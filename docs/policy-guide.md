---
layout: default
title: Policy Guide
prev_url: /web-dashboard.html
prev_title: Web Dashboard Guide
next_url: /pypi-drift.html
next_title: PyPI Drift Analysis
---

# Policy Guide

Policies can be supplied as YAML or JSON.

## Policy shape

```yaml
approved:
  - MIT
  - BSD
  - Apache-2.0
restricted:
  - LGPL
  - MPL
denied:
  - GPL
  - AGPL
```

All keys are optional, but each value must be a list of non-empty strings.

## JSON equivalent

```json
{
  "approved": ["MIT", "BSD", "Apache-2.0"],
  "restricted": ["LGPL", "MPL"],
  "denied": ["GPL", "AGPL"]
}
```

## Classification behavior

LicenseGuard normalizes detected license text, then classifies using:

1. Provided policy file (if any), or in-memory web policy
2. Built-in fallback pattern rules

### OR and AND semantics

- `OR` means alternatives (`MIT OR GPL-3.0`)
- `AND` means cumulative requirements (`MIT AND GPL-3.0`)

Per OR branch, denied/restricted checks are evaluated before approved.

## Practical policy outcomes

Example expression: `MIT OR GPL-3.0`

- If `MIT` is approved, the branch can be approved even if GPL is denied
- If no branch passes policy checks, status becomes restricted/denied/unknown based on branch evaluation

Example expression: `MIT AND GPL-3.0`

- Both tokens must pass in that branch
- A denied token makes the branch denied

## Built-in fallback logic

Without a file policy, built-in pattern matching is used.

- Common permissive families map to approved
- Restrictive families map to restricted
- GPL/AGPL/proprietary patterns map to denied
- Unmatched strings remain unknown

## Policy design recommendations

- Start strict with explicit `approved` allowlist for predictable outcomes
- Keep `restricted` for licenses requiring manual review
- Keep `denied` focused on licenses your organization cannot accept
- Version-control policy files and require review for changes
- Revisit policy quarterly as package landscape changes

## Unknown reasons

`UNKNOWN` rows include `reason` and may include `unknown_type`:

- `no_metadata` -> license not found in package metadata
- `unrecognized` -> metadata exists but normalization failed

## Best practices

- Keep approved rules explicit for stricter control
- Review restricted licenses case-by-case
- Treat unknown licenses as an escalation point
- Keep policy under version control and review via PRs
- Use `--fail-on unknown` in high-assurance repositories
