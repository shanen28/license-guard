"""Tokenize SPDX-style license strings (OR = alternatives, AND = cumulative)."""

from __future__ import annotations

import re
from typing import FrozenSet, List, Optional, Tuple

_OR_SPLIT = re.compile(r"\s+OR\s+", re.IGNORECASE)
_AND_SPLIT = re.compile(
    r"\s+AND\s+|\s*;\s*|\s*,\s*|\s+/\s+",
    re.IGNORECASE,
)


def _norm_token(t: str) -> str:
    return " ".join(t.split()).strip().upper()


def split_or_alternatives(expr: str) -> List[List[str]]:
    """
    Split on top-level OR into alternatives; each alternative is AND-split into tokens.

    Empty or whitespace → [].
    """
    if not expr or not str(expr).strip():
        return []
    parts = [p.strip() for p in _OR_SPLIT.split(expr.strip()) if p.strip()]
    if not parts:
        return []
    branches: List[List[str]] = []
    for p in parts:
        tokens = [_norm_token(x) for x in _AND_SPLIT.split(p) if x.strip()]
        if tokens:
            branches.append(tokens)
    return branches if branches else [[_norm_token(expr.strip())]]


def tokenize_license_expression(spdx_string: str) -> FrozenSet[str]:
    """All distinct license tokens (normalized uppercase), flattened from every OR branch."""
    found: set = set()
    for branch in split_or_alternatives(spdx_string):
        for t in branch:
            if t:
                found.add(t)
    return frozenset(found)


def compute_license_drift(
    installed_spdx: str,
    latest_spdx: Optional[str],
    *,
    pypi_ok: bool,
) -> Tuple[bool, str]:
    """
    Returns ``(license_changed, change_type)`` where ``change_type`` is one of
    ``no_change``, ``compatible``, ``compatible_partial``, ``incompatible``, ``unknown``.

    ``license_changed`` is True for ``compatible``, ``compatible_partial``, or
    ``incompatible`` drift.
    """
    if not pypi_ok:
        return False, "unknown"

    inst_set = tokenize_license_expression(installed_spdx)
    if latest_spdx is None:
        return False, "unknown"

    lt = latest_spdx.strip()
    if not lt or lt.upper() == "UNKNOWN":
        return False, "unknown"

    latest_set = tokenize_license_expression(latest_spdx)
    if inst_set == latest_set:
        return False, "no_change"
    if not latest_set or not inst_set:
        return False, "unknown"
    if latest_set <= inst_set:
        return True, "compatible"
    if inst_set <= latest_set:
        return True, "incompatible"
    inter = inst_set & latest_set
    if inter:
        return True, "compatible_partial"
    return True, "incompatible"
