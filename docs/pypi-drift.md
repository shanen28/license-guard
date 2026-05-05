---
layout: default
title: PyPI Drift Analysis
prev_url: /policy-guide.html
prev_title: Policy Guide
next_url: /python-api.html
next_title: Python API Guide
---

# PyPI Drift Analysis

Drift analysis is optional and enabled with `--check-latest`.

## What drift mode does

For each resolved package:

1. Read installed license metadata
2. Query PyPI for latest release metadata
3. Compare normalized license token sets
4. Add drift fields into each row

If a lookup fails, the scan still succeeds and warning entries describe affected packages.

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

`license_changed` is true for `compatible`, `compatible_partial`, and `incompatible`.

## When to use drift mode

Use drift mode when:

- You are planning dependency upgrades
- You want early warning for metadata changes across releases
- You run scheduled governance checks (daily/weekly)

Avoid drift mode in fully offline or deterministic no-network environments.

## Cache controls

```bash
licenseguard scan requirements.txt --cli --check-latest --cache-file .licenseguard_cache.json
```

Use `--no-cache` to force fresh lookups and skip cache writes.

## Interpreting results safely

- Treat `incompatible` as a review trigger, not an automatic legal conclusion
- Treat `compatible_partial` as medium risk requiring context
- Inspect `license_latest` and package changelogs before action
- Preserve reports for auditability and trend analysis

## Operational guidance

- Keep drift mode out of fully offline jobs
- Use cache in CI for speed and reduced API pressure
- Review `warnings` for transient network or package metadata problems
- Pair drift checks with a pinned lock/dependency update process
