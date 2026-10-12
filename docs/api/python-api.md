# Python API

LicenseGuard can be used programmatically for custom gating, reporting, and integration.

---

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

---

## Function signatures

### `load_policy_file`

```python
load_policy_file(path: Path) -> PolicyConfig
```

Loads a YAML or JSON policy file and returns a validated `PolicyConfig`. Raises on invalid structure.

### `scan_requirements_file`

```python
scan_requirements_file(
    requirements_path: Path,
    *,
    policy: PolicyConfig | None = None,
    check_latest: bool = False,
    pypi_cache_file: Path | None = None,
    pypi_no_cache: bool = False,
) -> dict[str, Any]
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `requirements_path` | `Path` | required | File to scan |
| `policy` | `PolicyConfig \| None` | `None` | Policy to apply; built-in rules when `None` |
| `check_latest` | `bool` | `False` | Enable PyPI drift analysis (network) |
| `pypi_cache_file` | `Path \| None` | `None` | Disk cache for PyPI responses |
| `pypi_no_cache` | `bool` | `False` | Bypass caching entirely |

---

## Minimal usage

```python
from pathlib import Path
from licenseguard import scan_requirements_file

result = scan_requirements_file(Path("requirements.txt"))

print(result["summary"]["worst_status"])
print(f"{result['summary']['total']} packages scanned")
```

---

## Programmatic gating

```python
from pathlib import Path
from licenseguard import scan_requirements_file

result = scan_requirements_file(Path("requirements.txt"))
worst = result["summary"]["worst_status"]

if worst in {"DENIED", "RESTRICTED"}:
    raise SystemExit(f"Dependency policy gate failed: {worst}")
```

### Custom rules beyond the built-in thresholds

The CLI gates on the single worst status. The API lets you express finer policy — for example, blocking restricted **direct** dependencies while tolerating restricted transitives:

```python
from pathlib import Path
from licenseguard import load_policy_file, scan_requirements_file

policy = load_policy_file(Path("policy.yaml"))
result = scan_requirements_file(Path("requirements.txt"), policy=policy)

blocking = [
    row for row in result["rows"]
    if row["status"] == "DENIED"
    or (row["status"] == "RESTRICTED" and row["direct"])
]

if blocking:
    for row in blocking:
        print(f"  {row['package']} {row['version']}: "
              f"{row['license_spdx']} ({row['status']})")
    raise SystemExit(f"{len(blocking)} blocking license findings")
```

---

## Drift analysis

```python
from pathlib import Path
from licenseguard import scan_requirements_file

result = scan_requirements_file(
    Path("requirements.txt"),
    check_latest=True,
    pypi_cache_file=Path(".licenseguard_cache.json"),
)

for row in result["rows"]:
    if row.get("license_changed"):
        print(f"{row['package']}: "
              f"{row['license_installed']} → {row['license_latest']} "
              f"[{row['change_type']}]")
```

!!! warning "Network calls"
    `check_latest=True` queries the PyPI API for every resolved package. Supply a cache file for repeated runs.

---

## Building custom exports

`result["rows"]` is plain serializable data, suitable for:

- internal dashboards
- security data-lake ingestion
- pull request summary comments
- compliance evidence artifacts

### Markdown summary for a PR comment

```python
from pathlib import Path
from licenseguard import scan_requirements_file

result = scan_requirements_file(Path("requirements.txt"))
summary = result["summary"]

lines = [
    "## Dependency License Report",
    "",
    f"**Worst status:** {summary['worst_status']}",
    "",
    "| Status | Count |",
    "|---|---|",
    f"| Approved | {summary['approved']} |",
    f"| Restricted | {summary['restricted']} |",
    f"| Denied | {summary['denied']} |",
    f"| Unknown | {summary['unknown']} |",
]

flagged = [r for r in result["rows"] if r["status"] in {"DENIED", "RESTRICTED"}]
if flagged:
    lines += ["", "### Findings", "", "| Package | Version | License | Status |", "|---|---|---|---|"]
    lines += [
        f"| `{r['package']}` | {r['version']} | {r['license_spdx']} | {r['status']} |"
        for r in flagged
    ]

print("\n".join(lines))
```

### CSV export

```python
import csv
from pathlib import Path
from licenseguard import scan_requirements_file

result = scan_requirements_file(Path("requirements.txt"))
fields = ["package", "version", "direct", "license_spdx", "status", "reason"]

with open("licenses.csv", "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    # Direct dependencies first, matching CLI and dashboard ordering.
    writer.writerows(sorted(result["rows"], key=lambda r: (not r["direct"], r["package"])))
```

---

## Handling warnings

```python
result = scan_requirements_file(Path("requirements.txt"))

for warning in result["warnings"]:
    print(f"warning: {warning}")
```

Warnings are non-fatal but worth surfacing — they indicate requirement lines that were skipped or metadata lookups that failed.

---

## Integration tips

- Gate on `summary.worst_status` for simple decisions, or iterate `rows` for nuanced rules.
- Persist the full report JSON for audit history and build-over-build comparison.
- Load the policy once at job startup for deterministic runs.
- Keep `check_latest` out of latency-sensitive paths.

---

## Related

- [Report schema](report-schema.md) — every field documented
- [Gating strategy](../ci-cd/gating.md) — threshold selection
