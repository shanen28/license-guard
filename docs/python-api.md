---
layout: default
title: Python API Guide
prev_url: /pypi-drift.html
prev_title: PyPI Drift Analysis
next_url: /architecture.html
next_title: Architecture and Internals
---

# Python API Guide

LicenseGuard can be used programmatically.

## Public API

```python
from pathlib import Path

from licenseguard import load_policy_file, scan_requirements_file

policy = load_policy_file(Path("policy.yaml"))
result = scan_requirements_file(
    Path("requirements.txt"),
    policy=policy,
    check_latest=False,
    pypi_cache_file=None,
    pypi_no_cache=False,
)
```

## Function signatures

- `load_policy_file(path: Path) -> PolicyConfig`
- `scan_requirements_file(requirements_path: Path, *, policy=None, check_latest=False, pypi_cache_file=None, pypi_no_cache=False) -> Dict[str, Any]`

## Return object

`scan_requirements_file(...)` returns a dictionary with:

- `requirements_file` - absolute path
- `rows` - list of package-level findings
- `warnings` - parse/resolution/network warnings
- `summary` - aggregate counts and worst status
- `check_latest` - present only when drift mode is enabled

## Summary object details

`summary` includes:

- `approved`
- `restricted`
- `denied`
- `unknown`
- `total`
- `worst_status`
- `counts_by_status`

## Row highlights

- `package`, `version`
- `direct` (bool)
- `installed` (always true in current design)
- `license_detected`, `license_spdx`
- `status`, `reason`, `unknown_type`
- drift fields (only when `check_latest=True`)

## Programmatic gating example

```python
from pathlib import Path
from licenseguard.scan import scan_requirements_file

result = scan_requirements_file(Path("requirements.txt"))
worst = result["summary"]["worst_status"]
if worst in {"DENIED", "RESTRICTED"}:
    raise SystemExit(f"Dependency policy gate failed: {worst}")
```

## Generating custom exports

You can transform `result["rows"]` into:

- Internal dashboards
- Security data lake ingestion
- Pull request summary comments
- Compliance evidence artifacts

## Integration tips

- Parse `summary.worst_status` for gating decisions
- Persist JSON for audit/comparison history
- Keep policy loading close to job startup for deterministic runs
