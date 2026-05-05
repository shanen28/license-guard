# PyPI Drift Analysis

Drift analysis is optional and enabled with `--check-latest`.

## What drift mode does

For each resolved package:

1. Read installed license metadata
2. Query PyPI for latest release metadata
3. Compare normalized license token sets
4. Add drift fields into each row

## Drift fields in output

- `version_installed`
- `version_latest`
- `license_installed`
- `license_latest`
- `license_changed` (boolean)
- `change_type`

## `change_type` values

- `no_change` - same normalized token set
- `compatible` - latest tokens are subset of installed tokens
- `compatible_partial` - partial overlap
- `incompatible` - disjoint or broadening in risky direction
- `unknown` - lookup/metadata issues prevented comparison

## Cache controls

```bash
licenseguard scan requirements.txt --cli --check-latest --cache-file .licenseguard_cache.json
```

Use `--no-cache` to force fresh lookups and skip cache writes.

## Operational guidance

- Keep drift mode out of fully offline jobs
- Use cache in CI for speed and reduced API pressure
- Review `warnings` for transient network or package metadata problems
