# Quickstart

Get a license report for your project in three commands.

---

## 1. Install dependencies and LicenseGuard together

```bash
pip install -r requirements.txt
pip install licenseguard
```

Both must live in the same environment — LicenseGuard reads installed package metadata.

---

## 2. Run a scan

=== "Terminal output"

    ```bash
    licenseguard scan requirements.txt --cli
    ```

    Prints a dependency table, a summary block, and the full JSON report.

=== "Web dashboard"

    ```bash
    licenseguard scan requirements.txt
    ```

    Launches a local dashboard and opens your browser. Click **Run scan** to begin.

!!! note "The dashboard is the default"
    Running `licenseguard scan` **without** `--cli` launches the web UI. CLI-only flags such as `--json-only`, `--no-table`, `-o`, and `--fail-on` are ignored with a warning unless `--cli` is also passed.

---

## 3. Enforce a policy

Create `policy.yaml`:

```yaml
approved:
  - MIT
  - BSD
  - Apache-2.0
  - ISC
restricted:
  - LGPL
  - MPL
denied:
  - GPL
  - AGPL
```

Then gate on it:

```bash
licenseguard scan requirements.txt --cli --policy policy.yaml --fail-on restricted
```

The command exits non-zero if any package resolves to `RESTRICTED` or `DENIED`, which is what makes it usable as a CI gate.

---

## What you get back

Every run produces three top-level pieces:

| Field | Contents |
|---|---|
| `rows` | One entry per resolved package, with license, status, and reason |
| `summary` | Status counts plus the aggregate `worst_status` |
| `warnings` | Non-fatal parse, resolution, or network issues |

With `--check-latest`, each row also gains drift fields comparing installed metadata against the newest PyPI release.

---

## Common first commands

```bash
# Save a report for audit history
licenseguard scan requirements.txt --cli --json-only -o licenseguard-report.json

# Check whether upgrades would change any license
licenseguard scan requirements.txt --cli --check-latest

# Strictest posture: fail unless everything is approved
licenseguard scan requirements.txt --cli --fail-on unknown
```

---

## Next steps

- [Your first scan](first-scan.md) — read the output field by field
- [CLI commands](../cli/commands.md) — every available option
- [Policy overview](../policy/overview.md) — design rules for your organization
