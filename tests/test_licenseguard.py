"""Focused tests for policy, tokenization, and drift classification."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

from licenseguard.license_tokens import (
    compute_license_drift,
    split_or_alternatives,
    tokenize_license_expression,
)
from licenseguard.policy import LicenseStatus, classify_license, load_policy_file


def test_split_or_alternatives_and_vs_or() -> None:
    assert split_or_alternatives("MIT OR GPL-3.0") == [["MIT"], ["GPL-3.0"]]
    assert split_or_alternatives("MIT AND Apache-2.0") == [["MIT", "APACHE-2.0"]]


def test_tokenize_license_expression_flattens() -> None:
    toks = tokenize_license_expression("MIT OR Apache-2.0")
    assert toks == frozenset({"MIT", "APACHE-2.0"})


def test_builtin_or_any_approved_branch() -> None:
    status, _ = classify_license("MIT OR GPL-3.0", None)
    assert status == LicenseStatus.APPROVED


def test_builtin_and_requires_all_tokens() -> None:
    status, _ = classify_license("MIT AND GPL-3.0", None)
    assert status == LicenseStatus.DENIED


def test_file_policy_or_respects_allowlist(tmp_path: Path) -> None:
    pol_path = tmp_path / "pol.yaml"
    pol_path.write_text("approved:\n  - MIT\n", encoding="utf-8")
    pol = load_policy_file(pol_path)
    status, _ = classify_license("MIT OR GPL-3.0", pol)
    assert status == LicenseStatus.APPROVED


def test_unknown_empty_license() -> None:
    status, reason = classify_license("", None)
    assert status == LicenseStatus.UNKNOWN
    assert "License not found in metadata" in reason


def test_compute_license_drift_compatible_subset() -> None:
    chg, ctype = compute_license_drift(
        "MIT OR Apache-2.0",
        "Apache-2.0",
        pypi_ok=True,
    )
    assert ctype == "compatible"
    assert chg is True


def test_compute_license_drift_compatible_partial_overlap() -> None:
    chg, ctype = compute_license_drift(
        "MIT OR Apache-2.0",
        "MIT OR GPL-3.0",
        pypi_ok=True,
    )
    assert ctype == "compatible_partial"
    assert chg is True


def test_compute_license_drift_no_change() -> None:
    chg, ctype = compute_license_drift("MIT", "MIT", pypi_ok=True)
    assert ctype == "no_change"
    assert chg is False


def test_compute_license_drift_pypi_failed() -> None:
    chg, ctype = compute_license_drift("MIT", "MIT", pypi_ok=False)
    assert ctype == "unknown"
    assert chg is False


def test_unpinned_appends_to_row_reason(tmp_path: Path) -> None:
    from licenseguard.scan import scan_requirements_file

    req = tmp_path / "requirements.txt"
    req.write_text("packaging>=1.0\n", encoding="utf-8")
    result = scan_requirements_file(req)
    row = next(r for r in result["rows"] if r["package"] == "packaging")
    assert "Unpinned dependency" in row["reason"]


def test_strict_pin_no_unpinned_note(tmp_path: Path) -> None:
    from licenseguard.scan import scan_requirements_file

    ver = metadata.version("packaging")
    req = tmp_path / "requirements.txt"
    req.write_text(f"packaging=={ver}\n", encoding="utf-8")
    result = scan_requirements_file(req)
    row = next(r for r in result["rows"] if r["package"] == "packaging")
    assert "Unpinned dependency" not in row["reason"]


def test_summary_counts_in_scan(tmp_path: Path) -> None:
    from licenseguard.scan import scan_requirements_file

    req = tmp_path / "requirements.txt"
    req.write_text("nonexistent-pkg-xyz-12345\n", encoding="utf-8")
    result = scan_requirements_file(req)
    s = result["summary"]
    assert "approved" in s and "counts_by_status" in s
    assert result["rows"] == []
    assert s["total"] == 0


def test_normalize_long_license_blob_mit() -> None:
    from licenseguard.license_detection import normalize_license_to_spdx

    filler = "Lorem ipsum dolor sit amet. " * 12
    blob = filler + "This software is under the MIT License for testing."
    assert len(blob) > 200
    assert normalize_license_to_spdx(blob) == "MIT"


def test_unknown_requirement_root_yields_no_rows(tmp_path: Path) -> None:
    from licenseguard.scan import scan_requirements_file

    req = tmp_path / "requirements.txt"
    req.write_text("nonexistent-pkg-xyz-12345\n", encoding="utf-8")
    result = scan_requirements_file(req)
    assert result["rows"] == []


def test_scan_row_is_installed_direct_dependency(tmp_path: Path) -> None:
    from licenseguard.scan import scan_requirements_file

    req = tmp_path / "requirements.txt"
    req.write_text("packaging\n", encoding="utf-8")
    result = scan_requirements_file(req)
    row = next(r for r in result["rows"] if r["package"] == "packaging")
    assert row["direct"] is True
    assert row["installed"] is True
    assert "optional" not in row
