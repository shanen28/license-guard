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

## Classification behavior

LicenseGuard normalizes detected license text, then classifies using:

1. Provided policy file (if any), or in-memory web policy
2. Built-in fallback pattern rules

### OR and AND semantics

- `OR` means alternatives (`MIT OR GPL-3.0`)
- `AND` means cumulative requirements (`MIT AND GPL-3.0`)

Per OR branch, denied/restricted checks are evaluated before approved.

## Unknown reasons

`UNKNOWN` rows include `reason` and may include `unknown_type`:

- `no_metadata` -> license not found in package metadata
- `unrecognized` -> metadata exists but normalization failed

## Best practices

- Keep approved rules explicit for stricter control
- Review restricted licenses case-by-case
- Treat unknown licenses as an escalation point
- Keep policy under version control and review via PRs
