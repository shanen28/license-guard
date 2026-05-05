"""Load policy from file or built-in rules; classify normalized license text."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, FrozenSet, Iterable, List, Optional, Tuple

from licenseguard.license_tokens import split_or_alternatives


class LicenseStatus(str, Enum):
    APPROVED = "APPROVED"
    RESTRICTED = "RESTRICTED"
    DENIED = "DENIED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PolicyConfig:
    approved: FrozenSet[str]
    restricted: FrozenSet[str]
    denied: FrozenSet[str]


_DENIED_OTHER = (
    "COMMERCIAL",
    "PROPRIETARY",
    "NO REDISTRIBUTION",
)

_RESTRICTED_BUILTIN = (
    "LGPL",
    "LESSER GENERAL PUBLIC",
    "MPL",
    "MOZILLA PUBLIC LICENSE",
    "EPL",
    "ECLIPSE PUBLIC LICENSE",
    "CPL",
    "COMMON PUBLIC LICENSE",
    "CDDL",
    "COMMON DEVELOPMENT AND DISTRIBUTION",
    "MS-PL",
    "MICROSOFT PUBLIC LICENSE",
    "OSL",
    "OPEN SOFTWARE LICENSE",
)

_APPROVED_BUILTIN = (
    "MIT",
    "BSD",
    "APACHE",
    "ISC",
    "PYTHON SOFTWARE FOUNDATION",
    "PSF",
    "UNLICENSE",
    "CC0",
    "PUBLIC DOMAIN",
    "ARTISTIC",
    "ZLIB",
    "BOOST",
    "BSL",
    "WTFPL",
)


_SEVERITY = {
    LicenseStatus.DENIED: 0,
    LicenseStatus.RESTRICTED: 1,
    LicenseStatus.UNKNOWN: 2,
    LicenseStatus.APPROVED: 3,
}


def worst_status(statuses: Iterable[LicenseStatus]) -> LicenseStatus:
    items = list(statuses)
    if not items:
        return LicenseStatus.UNKNOWN
    return min(items, key=lambda s: _SEVERITY.get(s, 99))


def _first_hit(text_upper: str, needles: Tuple[str, ...]) -> Optional[str]:
    for needle in needles:
        if needle in text_upper:
            return needle
    return None


def _classify_one_token_builtin(t: str) -> Tuple[LicenseStatus, str]:
    """Classify a single SPDX-like token (already uppercased)."""
    if "AGPL" in t:
        return LicenseStatus.DENIED, "matched pattern: AGPL"
    if "LGPL" in t:
        return LicenseStatus.RESTRICTED, "matched pattern: LGPL"
    if "GPL" in t or "GNU GENERAL PUBLIC LICENSE" in t:
        return LicenseStatus.DENIED, "matched pattern: GPL"

    hit = _first_hit(t, _DENIED_OTHER)
    if hit:
        return LicenseStatus.DENIED, f"matched pattern: {hit}"

    hit = _first_hit(t, _RESTRICTED_BUILTIN)
    if hit:
        return LicenseStatus.RESTRICTED, f"matched pattern: {hit}"

    hit = _first_hit(t, _APPROVED_BUILTIN)
    if hit:
        return LicenseStatus.APPROVED, f"matched pattern: {hit}"

    return LicenseStatus.UNKNOWN, "no policy match for detected text"


def _classify_and_group_builtin(tokens: List[str]) -> Tuple[LicenseStatus, str]:
    """AND semantics: most restrictive token wins."""
    if not tokens:
        return LicenseStatus.UNKNOWN, "License not found in metadata"
    pairs = [_classify_one_token_builtin(t) for t in tokens]
    w = worst_status(s for s, _ in pairs)
    for s, r in pairs:
        if s == w:
            return s, r
    return LicenseStatus.UNKNOWN, "no policy match for detected text"


def _or_combine_best(statuses: List[LicenseStatus]) -> LicenseStatus:
    """OR semantics: pick the best (most permissive) outcome across alternatives."""
    if not statuses:
        return LicenseStatus.UNKNOWN
    if LicenseStatus.APPROVED in statuses:
        return LicenseStatus.APPROVED
    if LicenseStatus.UNKNOWN in statuses:
        return LicenseStatus.UNKNOWN
    if LicenseStatus.RESTRICTED in statuses:
        return LicenseStatus.RESTRICTED
    return LicenseStatus.DENIED


def _classify_builtin_expression(expr: str) -> Tuple[LicenseStatus, str]:
    branches = split_or_alternatives(expr)
    if not branches:
        return LicenseStatus.UNKNOWN, "License not found in metadata"
    branch_results: List[Tuple[LicenseStatus, str]] = [
        _classify_and_group_builtin(b) for b in branches
    ]
    overall = _or_combine_best([s for s, _ in branch_results])
    for s, r in branch_results:
        if s == overall:
            return s, r
    return branch_results[0]


def _norm_token(s: str) -> str:
    return s.strip().upper()


def _policy_lists(data: Any) -> Tuple[List[str], List[str], List[str]]:
    if not isinstance(data, dict):
        raise ValueError("policy file must contain a JSON object or YAML mapping")

    def get_list(key: str) -> List[str]:
        v = data.get(key)
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError(f"policy key {key!r} must be a list")
        out: List[str] = []
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"policy list {key!r} must contain non-empty strings")
            out.append(item.strip())
        return out

    return get_list("approved"), get_list("restricted"), get_list("denied")


def policy_from_mapping(data: Any) -> PolicyConfig:
    """Build a policy from a mapping (same shape as YAML/JSON policy files)."""
    approved, restricted, denied = _policy_lists(data)
    return PolicyConfig(
        approved=frozenset(_norm_token(x) for x in approved),
        restricted=frozenset(_norm_token(x) for x in restricted),
        denied=frozenset(_norm_token(x) for x in denied),
    )


def load_policy_file(path: Path) -> PolicyConfig:
    """Load policy from a .json, .yaml, or .yml file."""
    raw_text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".json":
        data = json.loads(raw_text)
    elif suffix in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(raw_text)
        if data is None:
            data = {}
    else:
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            import yaml

            data = yaml.safe_load(raw_text)
            if data is None:
                data = {}

    return policy_from_mapping(data)


def _token_matches_rule(token_upper: str, rule_upper: str) -> bool:
    if token_upper == rule_upper:
        return True
    if token_upper.startswith(rule_upper + "-"):
        return True
    return False


def _token_matches_any_rule(token_upper: str, rules: FrozenSet[str]) -> Optional[str]:
    for rule in rules:
        if _token_matches_rule(token_upper, rule):
            return rule
    return None


def _classify_and_group_file(tokens: List[str], policy: PolicyConfig) -> Tuple[LicenseStatus, str]:
    if not tokens:
        return LicenseStatus.UNKNOWN, "License not found in metadata"

    upper_tokens = [_norm_token(t) for t in tokens if t.strip()]

    for tok in upper_tokens:
        hit = _token_matches_any_rule(tok, policy.denied)
        if hit:
            return LicenseStatus.DENIED, f"policy denied: {hit} (token {tok})"

    for tok in upper_tokens:
        hit = _token_matches_any_rule(tok, policy.restricted)
        if hit:
            return LicenseStatus.RESTRICTED, f"policy restricted: {hit} (token {tok})"

    if policy.approved:
        unmatched = [tok for tok in upper_tokens if not _token_matches_any_rule(tok, policy.approved)]
        if unmatched:
            return LicenseStatus.UNKNOWN, f"token not in approved list: {', '.join(unmatched)}"
        return LicenseStatus.APPROVED, "policy approved"

    return LicenseStatus.APPROVED, "policy: not denied or restricted"


def _classify_file_expression(expr: str, policy: PolicyConfig) -> Tuple[LicenseStatus, str]:
    branches = split_or_alternatives(expr)
    if not branches:
        return LicenseStatus.UNKNOWN, "License not found in metadata"
    branch_results = [_classify_and_group_file(b, policy) for b in branches]
    overall = _or_combine_best([s for s, _ in branch_results])
    for s, r in branch_results:
        if s == overall:
            return s, r
    return branch_results[0]


def classify_license(
    normalized_spdx: str,
    policy: Optional[PolicyConfig] = None,
) -> Tuple[LicenseStatus, str]:
    """
    Classify using optional file policy (lists of SPDX-like ids) or built-in substring rules.
    ``normalized_spdx`` should be the output of ``normalize_license_to_spdx``.
    Top-level OR is treated as alternatives (any acceptable branch satisfies the expression).
    """
    if not normalized_spdx or not normalized_spdx.strip():
        return LicenseStatus.UNKNOWN, "License not found in metadata"

    expr = normalized_spdx.strip()
    if policy is not None:
        return _classify_file_expression(expr, policy)
    return _classify_builtin_expression(expr)


def should_fail_scan(worst: LicenseStatus, fail_on: Optional[str]) -> bool:
    if fail_on is None:
        return worst in (LicenseStatus.DENIED, LicenseStatus.RESTRICTED)
    if fail_on == "denied":
        return worst == LicenseStatus.DENIED
    if fail_on == "restricted":
        return worst in (LicenseStatus.DENIED, LicenseStatus.RESTRICTED)
    if fail_on == "unknown":
        return worst != LicenseStatus.APPROVED
    return False
