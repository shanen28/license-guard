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

## Return object

`scan_requirements_file(...)` returns a dictionary with:

- `requirements_file` - absolute path
- `rows` - list of package-level findings
- `warnings` - parse/resolution/network warnings
- `summary` - aggregate counts and worst status
- `check_latest` - present only when drift mode is enabled

## Row highlights

- `package`, `version`
- `direct` (bool)
- `installed` (always true in current design)
- `license_detected`, `license_spdx`
- `status`, `reason`, `unknown_type`
- drift fields (only when `check_latest=True`)

## Integration tips

- Parse `summary.worst_status` for gating decisions
- Persist JSON for audit/comparison history
- Keep policy loading close to job startup for deterministic runs
