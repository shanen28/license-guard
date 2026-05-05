"""Fetch project metadata from the PyPI JSON API (optional compare-latest mode)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from licenseguard.license_detection import normalize_license_to_spdx

_USER_AGENT = "licenseguard/0.3 (https://pypi.org/project/licenseguard/)"

_cache: Dict[str, Tuple[Optional[Dict[str, Any]], Optional[str]]] = {}


def clear_pypi_cache() -> None:
    _cache.clear()


def load_pypi_disk_cache(path: Optional[Path]) -> Dict[str, Dict[str, Any]]:
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_pypi_disk_cache(path: Optional[Path], data: Dict[str, Dict[str, Any]]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _synthetic_payload_from_disk(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal JSON shape so ``latest_version_and_spdx`` keeps working."""
    ver = entry.get("version_latest") or entry.get("version")
    lic = entry.get("license_spdx") or entry.get("license_raw") or ""
    return {"info": {"version": ver, "license": lic, "classifiers": entry.get("classifiers") or []}}


def fetch_pypi_metadata(
    project_name: str,
    *,
    timeout: float = 15.0,
    cache: Optional[Dict[str, Tuple[Optional[Dict[str, Any]], Optional[str]]]] = None,
    disk_read: Optional[Dict[str, Dict[str, Any]]] = None,
    disk_write: Optional[Dict[str, Dict[str, Any]]] = None,
    no_cache: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    GET https://pypi.org/pypi/{project}/json

    Resolution order: session ``cache`` → ``disk_read`` → HTTP. On successful HTTP,
    merge into ``disk_write`` when provided.

    With ``no_cache=True``, skip memory and disk cache (always HTTP; no cache writes).
    """
    key = project_name.strip().lower()
    store = cache if cache is not None else _cache
    if not no_cache:
        if key in store:
            return store[key]

        if disk_read and key in disk_read:
            data = _synthetic_payload_from_disk(disk_read[key])
            store[key] = (data, None)
            return store[key]

    quoted = urllib.parse.quote(project_name)
    url = f"https://pypi.org/pypi/{quoted}/json"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not isinstance(data, dict):
            if not no_cache:
                store[key] = (None, "invalid JSON response")
            return (None, "invalid JSON response")
        if not no_cache:
            store[key] = (data, None)
        if not no_cache and disk_write is not None:
            v, spdx = latest_version_and_spdx(data)
            disk_write[key] = {
                "version_latest": v,
                "license_spdx": spdx if spdx and spdx != "UNKNOWN" else spdx,
            }
            if spdx == "UNKNOWN" or not spdx:
                disk_write[key]["license_spdx"] = spdx or ""
        return (data, None)
    except urllib.error.HTTPError as e:
        err: Tuple[Optional[Dict[str, Any]], Optional[str]]
        if e.code == 404:
            err = (None, "not found on PyPI")
        else:
            err = (None, f"HTTP error {e.code}")
        if not no_cache:
            store[key] = err
        return err
    except urllib.error.URLError as e:
        err = (None, f"network error: {e.reason!s}")
        if not no_cache:
            store[key] = err
        return err
    except Exception as e:
        err = (None, f"error: {e}")
        if not no_cache:
            store[key] = err
        return err


def extract_latest_license_raw(info: Optional[Dict[str, Any]]) -> str:
    """Build a raw license string from PyPI ``info`` (similar priority to local metadata)."""
    if not info:
        return ""

    lexpr = info.get("license_expression") or info.get("License-Expression")
    if lexpr and str(lexpr).strip():
        return str(lexpr).strip()

    lic = info.get("license")
    if lic and str(lic).strip() and str(lic).strip().upper() != "UNKNOWN":
        return " ".join(str(lic).split())

    classifiers = info.get("classifiers") or []
    labels: list = []
    for c in classifiers:
        if isinstance(c, str) and c.startswith("License :: "):
            parts = [p.strip() for p in c.split("::")]
            if len(parts) >= 2:
                labels.append(" :: ".join(parts[1:]).strip())
    if labels:
        return "; ".join(labels)

    return ""


def latest_version_and_spdx(
    data: Optional[Dict[str, Any]],
) -> Tuple[Optional[str], Optional[str]]:
    if not data:
        return None, None
    info = data.get("info")
    if not isinstance(info, dict):
        return None, None

    ver = info.get("version")
    version_str = str(ver).strip() if ver else None
    if not version_str:
        version_str = None

    raw = extract_latest_license_raw(info)
    if raw.strip():
        return version_str, normalize_license_to_spdx(raw) or "UNKNOWN"
    if version_str is not None:
        return version_str, "UNKNOWN"
    return None, None
