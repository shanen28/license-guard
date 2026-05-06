# LicenseGuard

LicenseGuard helps with two related problems:

1. **License compliance** — Given a `requirements.txt`, it finds what is **actually installed** in the current environment (including transitive dependencies), reads **license metadata** via `importlib.metadata`, **normalizes** common phrases toward SPDX-style strings, and **classifies** each package as APPROVED / RESTRICTED / DENIED / UNKNOWN using built-in rules or a **YAML/JSON policy file**.

2. **License drift (optional)** — With **`--check-latest`**, it calls PyPI’s public JSON API and compares your **installed** license metadata with the **latest** release, so you can spot risky license changes before upgrading.

By default the scan is **offline** (no network). PyPI mode is opt-in.

This is not legal advice—only an engineering aid.

## Requirements

- Python 3.9+
- Packages must be **installed** in the environment where you run LicenseGuard (it does not resolve versions from PyPI for the main scan).

## Installation

```bash
pip install licenseguard
```

From source (local checkout):

```bash
pip install .
```

Development editable install (includes pytest):

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## CLI

**Offline compliance scan:**

```bash
licenseguard scan requirements.txt
```

**Policy file:**

```bash
licenseguard scan requirements.txt --policy policy.yaml
```

**Compare with latest on PyPI** (network):

```bash
licenseguard scan requirements.txt --check-latest
```

**Cache PyPI snapshots** between runs (JSON file, merged after each `--check-latest` run):

```bash
licenseguard scan requirements.txt --check-latest --cache-file .licenseguard_cache.json
```

**Bypass PyPI cache** (always hit the network; do not read/write `--cache-file`):

```bash
licenseguard scan requirements.txt --check-latest --no-cache
```

Print version:

```bash
licenseguard --version
```

Other flags: `--fail-on`, `--json-only`, `--no-table`, `-o report.json`.

After the text table (when not using `--json-only` or `--no-table`), a short **Scan Summary** block is printed before the JSON.

**Unpinned direct dependencies** (anything other than a single `==` / `===` version without wildcards, or URLs/VCS lines) get a note merged into that row’s `reason` (multiple notes are joined with ` | `), including *Unpinned dependency — license may change on upgrade*.

### How OR and AND are interpreted

- **`OR`** — Alternatives. Example: `MIT OR GPL-3.0` is **acceptable** if **any** alternative satisfies your policy (e.g. built-in rules treat MIT as approved, so the whole expression can be APPROVED).
- **`AND`** — Cumulative. Example: `MIT AND GPL-3.0` must satisfy **all** tokens; a single denied/restricted token drives the branch.

Normalization preserves top-level **`OR`**; within each alternative, `AND`, commas, slashes, and semicolons are combined with **` AND `**.

### Policy file (YAML or JSON)

Per **alternative** (OR branch), **denied** is checked first, then **restricted**, then **approved**. If `approved` is non-empty, every token in that **AND-group** must match the allowlist. If `approved` is omitted, anything not denied or restricted is treated as approved.

### PyPI / drift fields (JSON, when `--check-latest`)

Each row may include: `version_installed`, `version_latest`, `license_installed`, `license_latest`, `license_changed` (true for **compatible**, **compatible_partial**, or **incompatible** drift), and **`change_type`**: `no_change`, `compatible` (latest tokens ⊆ installed), `compatible_partial` (sets overlap but neither is a subset—e.g. `MIT OR Apache` vs `MIT OR GPL`), `incompatible` (installed ⊆ latest but not equal, or disjoint), or `unknown` (lookup or metadata issues).

The table adds `latest_version` and `license_change` (`Y`/`N`/`-`); `change_type` stays in JSON to keep the table readable.

### Example JSON (excerpt)

```json
{
  "requirements_file": "/path/to/requirements.txt",
  "summary": {
    "approved": 12,
    "restricted": 1,
    "denied": 0,
    "unknown": 2,
    "total": 15,
    "worst_status": "RESTRICTED",
    "counts_by_status": {
      "APPROVED": 12,
      "RESTRICTED": 1,
      "DENIED": 0,
      "UNKNOWN": 2
    }
  },
  "rows": [
    {
      "direct": true,
      "installed": true,
      "license_detected": "MIT License",
      "license_spdx": "MIT",
      "package": "packaging",
      "reason": "matched pattern: MIT",
      "status": "APPROVED",
      "version": "24.0"
    }
  ],
  "warnings": []
}
```

With `"check_latest": true`, rows also include drift fields as described above.

### Exit codes

| Situation | Default | `--fail-on denied` | `--fail-on restricted` | `--fail-on unknown` |
|-----------|---------|-------------------|------------------------|---------------------|
| Non-zero | DENIED or RESTRICTED | DENIED | DENIED or RESTRICTED | Not all APPROVED |

## Python API

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

## CI/CD example

```yaml
- run: pip install -r requirements.txt .
- run: licenseguard scan requirements.txt --policy policy.yaml --fail-on restricted
```

## Modules

| Module | Role |
|--------|------|
| `licenseguard.resolver` | Parse requirements, walk installed dependencies |
| `licenseguard.license_detection` | Metadata + SPDX-oriented normalization (with light caching) |
| `licenseguard.license_tokens` | `tokenize_license_expression`, OR/AND splitting |
| `licenseguard.policy` | Policy file + classification |
| `licenseguard.scan` | Build the report dict |
| `licenseguard.pypi` | PyPI JSON + optional disk cache |
| `licenseguard.cli` | CLI |

No network access unless you use **`--check-latest`**.
