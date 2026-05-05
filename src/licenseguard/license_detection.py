"""Read license text from metadata and normalize toward SPDX-style identifiers."""

from __future__ import annotations

import re
from importlib import metadata
from typing import Dict, List, Optional, Tuple

# Long license blobs (e.g. full license text in metadata): try keyword → SPDX before full parse.
_LONG_LICENSE_CHAR_THRESHOLD = 200

_SUMMARY_CACHE: Dict[Tuple[str, str], str] = {}


def clear_license_detection_cache() -> None:
    _SUMMARY_CACHE.clear()


def _all_header_values(md, key: str) -> list:
    get_all = getattr(md, "get_all", None)
    if callable(get_all):
        values = get_all(key)
        return list(values) if values else []
    value = md.get(key)
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]


def _license_labels_from_classifiers(dist: metadata.Distribution) -> list:
    labels: list = []
    for c in _all_header_values(dist.metadata, "Classifier"):
        if not c.startswith("License :: "):
            continue
        parts = [p.strip() for p in c.split("::")]
        if len(parts) >= 2:
            labels.append(" :: ".join(parts[1:]).strip())
    return labels


def _normalized_license_field(md) -> str:
    raw = md.get("License")
    if not raw or not str(raw).strip():
        return ""
    if str(raw).strip().upper() == "UNKNOWN":
        return ""
    return " ".join(str(raw).split())


def _detect_license_summary_impl(dist: metadata.Distribution) -> str:
    md = dist.metadata

    lexpr = md.get("License-Expression")
    if lexpr and str(lexpr).strip():
        return str(lexpr).strip()

    from_field = _normalized_license_field(md)
    if from_field:
        return from_field

    from_classifiers = _license_labels_from_classifiers(dist)
    if from_classifiers:
        return "; ".join(from_classifiers)

    return ""


def detect_license_summary(dist: metadata.Distribution) -> str:
    """Raw license string from metadata (expression, License field, or classifiers)."""
    name = (dist.metadata.get("Name") or "").strip()
    ver = (dist.version or "").strip()
    key = (name, ver)
    if key in _SUMMARY_CACHE:
        return _SUMMARY_CACHE[key]
    val = _detect_license_summary_impl(dist)
    _SUMMARY_CACHE[key] = val
    return val


# (lowercase phrase, SPDX id). Longer phrases first for substring replacement order.
_PHRASE_TO_SPDX: Tuple[Tuple[str, str], ...] = (
    ("gnu lesser general public license v3", "LGPL-3.0"),
    ("gnu lesser general public license v2.1", "LGPL-2.1"),
    ("gnu lesser general public license", "LGPL-2.1"),
    ("gnu library general public license", "LGPL-2.1"),
    ("gnu general public license v3", "GPL-3.0"),
    ("gnu general public license v2", "GPL-2.0"),
    ("gnu affero general public license v3", "AGPL-3.0"),
    ("apache software license", "Apache-2.0"),
    ("apache license, version 2.0", "Apache-2.0"),
    ("apache license 2.0", "Apache-2.0"),
    ("apache 2.0", "Apache-2.0"),
    ("apache-2.0", "Apache-2.0"),
    ("apache-2", "Apache-2.0"),
    ("apache 2", "Apache-2.0"),
    ("the apache license, version 2.0", "Apache-2.0"),
    ("mit license", "MIT"),
    ("osi approved :: mit license", "MIT"),
    ("osi approved::mit license", "MIT"),
    ("new bsd license", "BSD-3-Clause"),
    ("modified bsd license", "BSD-3-Clause"),
    ("bsd 3-clause license", "BSD-3-Clause"),
    ("bsd 3-clause", "BSD-3-Clause"),
    ("three-clause bsd license", "BSD-3-Clause"),
    ("simplified bsd license", "BSD-2-Clause"),
    ("bsd 2-clause license", "BSD-2-Clause"),
    ("bsd 2-clause", "BSD-2-Clause"),
    ("two-clause bsd license", "BSD-2-Clause"),
    ("bsd license", "BSD-3-Clause"),
    ("isc license", "ISC"),
    ("mozilla public license 2.0", "MPL-2.0"),
    ("mozilla public license", "MPL-2.0"),
    ("python software foundation license", "PSF-2.0"),
    ("python software foundation", "PSF-2.0"),
    ("eclipse public license", "EPL-1.0"),
    ("common development and distribution license", "CDDL-1.0"),
    ("universal permissive license", "UPL-1.0"),
    ("zlib license", "Zlib"),
    ("boost software license", "BSL-1.0"),
    ("creative commons zero", "CC0-1.0"),
    ("cc0 1.0 universal", "CC0-1.0"),
    ("public domain", "Unlicense"),
    ("the unlicense", "Unlicense"),
    ("artistic license", "Artistic-2.0"),
    ("wtfpl", "WTFPL"),
)


def _normalize_one_segment(segment: str) -> str:
    sl = segment.strip().lower()
    if not sl:
        return segment.strip()

    for phrase, spdx in _PHRASE_TO_SPDX:
        if sl == phrase:
            return spdx

    for phrase, spdx in _PHRASE_TO_SPDX:
        if phrase in sl:
            return spdx

    # Already SPDX-like (alphanumeric, dots, hyphens, plus)
    compact = segment.strip()
    if re.fullmatch(r"[\w.+\-]+(\s+(AND|OR)\s+[\w.+\-]+)*", compact, re.IGNORECASE):
        return re.sub(r"\s+", " ", compact)

    return segment.strip()


def _guess_spdx_from_license_blob(text: str) -> Optional[str]:
    """Map common keywords in long license prose to a single SPDX id (best-effort)."""
    u = text.upper()
    if re.search(r"\bGNU\s+AFFERO\s+GENERAL\s+PUBLIC\s+LICENSE\b", u) or "AGPL-3" in u:
        return "AGPL-3.0"
    if re.search(r"\bGNU\s+LESSER\s+GENERAL\s+PUBLIC\s+LICENSE\b", u) or re.search(
        r"\bLGPL\b", u
    ):
        return "LGPL-3.0"
    if re.search(r"\bGNU\s+GENERAL\s+PUBLIC\s+LICENSE\b", u):
        if re.search(r"\bVERSION\s+2\b", u) or " V2" in u or re.search(r"\bGPL-2\b", u):
            return "GPL-2.0"
        return "GPL-3.0"
    if re.search(r"\bGPL-3\b", u):
        return "GPL-3.0"
    if re.search(r"\bGPL-2\b", u):
        return "GPL-2.0"
    if "APACHE" in u:
        return "Apache-2.0"
    if re.search(r"\bBSD\b", u):
        return "BSD-3-Clause"
    if re.search(r"\bMIT\b", u):
        return "MIT"
    return None


def normalize_license_to_spdx(raw: str) -> str:
    """
    Map common license phrases to SPDX ids. Top-level ``OR`` stays ``OR``; within each
    alternative, ``AND`` / comma / slash / semicolon combine with `` AND ``.
    """
    if not raw or not raw.strip():
        return ""

    compact = " ".join(raw.split())
    if len(compact) > _LONG_LICENSE_CHAR_THRESHOLD:
        guessed = _guess_spdx_from_license_blob(compact)
        if guessed:
            return guessed
        return ""

    or_segments = [p.strip() for p in re.split(r"\s+OR\s+", compact, flags=re.I) if p.strip()]
    if not or_segments:
        return _normalize_one_segment(compact)

    out_or: List[str] = []
    for seg in or_segments:
        chunks = re.split(r"\s*;\s*|\s*,\s*|\s+/\s+|\s+AND\s+", seg, flags=re.I)
        seen = set()
        unique: List[str] = []
        for c in chunks:
            c = c.strip()
            if not c:
                continue
            n = _normalize_one_segment(c)
            k = n.lower()
            if k not in seen:
                seen.add(k)
                unique.append(n)
        if unique:
            out_or.append(" AND ".join(unique))
    return " OR ".join(out_or)
