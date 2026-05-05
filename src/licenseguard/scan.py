"""Orchestrate resolver + license detection + policy into a scan report."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from licenseguard.license_detection import detect_license_summary, normalize_license_to_spdx
from licenseguard.license_tokens import compute_license_drift
from licenseguard.policy import LicenseStatus, PolicyConfig, classify_license, worst_status
from licenseguard.pypi import (
    fetch_pypi_metadata,
    latest_version_and_spdx,
    load_pypi_disk_cache,
    save_pypi_disk_cache,
)
from licenseguard.resolver import (
    ResolvedPackage,
    installed_distribution_map,
    load_requirement_roots,
    resolved_packages_for_roots,
    unpinned_direct_package_names,
)

_UNPINNED_REASON_SUFFIX = "Unpinned dependency — license may change on upgrade"
_REASON_SPLIT = re.compile(r"\s*\|\s*|\s*;\s*")


def _join_reason_parts(parts: List[str]) -> str:
    seen: Set[str] = set()
    out: List[str] = []
    for p in parts:
        p = (p or "").strip()
        if not p or p in seen:
            continue
        seen.add(p)
        out.append(p)
    return " | ".join(out)


def _unknown_type(status: str, reason: str) -> Optional[str]:
    if status != LicenseStatus.UNKNOWN.value:
        return None
    full = (reason or "").strip()
    r0 = full.split("|")[0].strip()
    if r0 == "License not found in metadata":
        return "no_metadata"
    if "could not be normalized" in full:
        return "unrecognized"
    return None


def _reason_parts_from_string(s: str) -> List[str]:
    if not (s or "").strip():
        return []
    seen: Set[str] = set()
    out: List[str] = []
    for piece in _REASON_SPLIT.split(s):
        p = piece.strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


@dataclass
class ScanRow:
    package: str
    version: str
    direct: bool
    installed: bool
    license_detected: str
    license_spdx: str
    status: str
    reason: str
    unknown_type: Optional[str]


def _row_installed(
    pkg_name: str,
    version: str,
    direct: bool,
    dist: metadata.Distribution | None,
    policy: Optional[PolicyConfig],
) -> ScanRow:
    raw = detect_license_summary(dist) if dist is not None else ""
    spdx = normalize_license_to_spdx(raw)

    if not (raw or "").strip():
        st = LicenseStatus.UNKNOWN.value
        reason = "License not found in metadata"
        return ScanRow(
            package=pkg_name,
            version=version,
            direct=direct,
            installed=True,
            license_detected=raw,
            license_spdx=spdx,
            status=st,
            reason=reason,
            unknown_type=_unknown_type(st, reason),
        )

    status, policy_reason = classify_license(spdx, policy)
    if status == LicenseStatus.UNKNOWN:
        if not (spdx or "").strip() or policy_reason == "License not found in metadata":
            reason = "License could not be normalized (non-SPDX or complex expression)"
        else:
            reason = policy_reason
    else:
        reason = _join_reason_parts(_reason_parts_from_string(policy_reason))

    st_val = status.value
    return ScanRow(
        package=pkg_name,
        version=version,
        direct=direct,
        installed=True,
        license_detected=raw,
        license_spdx=spdx,
        status=st_val,
        reason=reason,
        unknown_type=_unknown_type(st_val, reason),
    )


def _build_rows(
    dists_by_name: Dict[str, metadata.Distribution],
    packages: List[ResolvedPackage],
    policy: Optional[PolicyConfig],
) -> List[ScanRow]:
    rows: List[ScanRow] = []
    for pkg in sorted(packages, key=lambda p: p.name):
        dist = dists_by_name.get(pkg.name)
        rows.append(_row_installed(pkg.name, pkg.version, pkg.direct, dist, policy))
    return rows


def _status_counts(rows: List[ScanRow]) -> Dict[str, int]:
    counts = {s.value: 0 for s in LicenseStatus}
    for r in rows:
        counts[r.status] = counts.get(r.status, 0) + 1
    return counts


def _build_summary(rows: List[ScanRow]) -> Dict[str, Any]:
    counts = _status_counts(rows)
    return {
        "approved": counts["APPROVED"],
        "restricted": counts["RESTRICTED"],
        "denied": counts["DENIED"],
        "unknown": counts["UNKNOWN"],
        "total": len(rows),
        "worst_status": worst_status(LicenseStatus(r.status) for r in rows).value,
        "counts_by_status": counts,
    }


def _append_unpinned_reasons(row_dicts: List[Dict[str, Any]], unpinned: Set[str]) -> None:
    for row in row_dicts:
        if not row.get("direct") or row["package"] not in unpinned:
            continue
        parts = _reason_parts_from_string(row.get("reason") or "")
        if _UNPINNED_REASON_SUFFIX not in parts:
            parts.append(_UNPINNED_REASON_SUFFIX)
        row["reason"] = _join_reason_parts(parts)


def _enrich_rows_with_pypi(
    row_dicts: List[Dict[str, Any]],
    warnings: List[str],
    *,
    disk_read: Dict[str, Dict[str, Any]],
    disk_write: Optional[Dict[str, Dict[str, Any]]],
    no_cache: bool,
) -> None:
    session: Dict[str, Any] = {}
    warned_packages: set = set()

    for row in row_dicts:
        pkg = row["package"]
        key = pkg.lower()
        data, err = fetch_pypi_metadata(
            pkg,
            cache=session,
            disk_read=disk_read,
            disk_write=disk_write,
            no_cache=no_cache,
        )

        lic_installed = row.get("license_spdx") or ""

        if err:
            if key not in warned_packages:
                warnings.append(f"[PyPI] lookup failed for package {pkg}: {err}")
                warned_packages.add(key)
            row["version_installed"] = row["version"]
            row["version_latest"] = None
            row["license_installed"] = lic_installed
            row["license_latest"] = None
            row["license_changed"] = False
            row["change_type"] = "unknown"
            continue

        v_latest, lic_latest = latest_version_and_spdx(data)
        row["version_installed"] = row["version"]
        row["version_latest"] = v_latest
        row["license_installed"] = lic_installed
        row["license_latest"] = lic_latest
        chg, ctype = compute_license_drift(lic_installed, lic_latest, pypi_ok=True)
        row["license_changed"] = chg
        row["change_type"] = ctype


def scan_requirements_file(
    requirements_path: Path,
    *,
    policy: Optional[PolicyConfig] = None,
    check_latest: bool = False,
    pypi_cache_file: Optional[Path] = None,
    pypi_no_cache: bool = False,
) -> Dict[str, Any]:
    roots, parse_warnings = load_requirement_roots(requirements_path)
    packages, resolve_warnings = resolved_packages_for_roots(roots)
    dists_by_name = installed_distribution_map()
    rows = _build_rows(dists_by_name, packages, policy)
    row_dicts = [asdict(r) for r in rows]
    _append_unpinned_reasons(row_dicts, unpinned_direct_package_names(requirements_path))
    for row in row_dicts:
        row["unknown_type"] = _unknown_type(row.get("status") or "", row.get("reason") or "")
    extra_warnings: List[str] = []

    disk_read: Dict[str, Dict[str, Any]] = {}
    disk_write: Optional[Dict[str, Dict[str, Any]]] = None
    if check_latest and not pypi_no_cache:
        disk_read = load_pypi_disk_cache(pypi_cache_file) if pypi_cache_file else {}
        disk_write = {}

    if check_latest:
        _enrich_rows_with_pypi(
            row_dicts,
            extra_warnings,
            disk_read=disk_read,
            disk_write=disk_write,
            no_cache=pypi_no_cache,
        )
        if pypi_cache_file is not None and not pypi_no_cache and disk_write is not None:
            merged = {**disk_read, **disk_write}
            save_pypi_disk_cache(pypi_cache_file, merged)

    result: Dict[str, Any] = {
        "requirements_file": str(requirements_path.resolve()),
        "rows": row_dicts,
        "warnings": parse_warnings + resolve_warnings + extra_warnings,
        "summary": _build_summary(rows),
    }
    if check_latest:
        result["check_latest"] = True
    return result
