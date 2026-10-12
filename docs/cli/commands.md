# CLI Commands

## Command structure

```bash
licenseguard scan <requirements_file> [options]
```

```bash
licenseguard --version
```

`--version` prints the installed version and exits.

---

## Output mode

!!! important "The dashboard is the default"
    `licenseguard scan requirements.txt` launches the **web dashboard**. Pass `--cli` for terminal output.

    CLI-only flags (`--json-only`, `--no-table`, `-o`, `--fail-on`) are ignored with a warning unless `--cli` is also present.

| Option | Effect |
|---|---|
| `--cli` | Print results in the terminal instead of launching the web UI |

---

## Core options

| Option | Argument | Description |
|---|---|---|
| `--cli` | — | Terminal output instead of the dashboard |
| `--policy` | `<path>` | Load a YAML or JSON policy file |
| `--json-only` | — | Emit only JSON on stdout; warnings still go to stderr |
| `--no-table` | — | Skip the human-readable table but still print JSON |
| `-o`, `--output-json` | `<path>` | Write the JSON report to a file |
| `--fail-on` | `denied` \| `restricted` \| `unknown` | Set the failure threshold |

---

## Drift options

These enable network access to PyPI. They are off by default.

| Option | Argument | Description |
|---|---|---|
| `--check-latest` | — | Compare installed license metadata against the latest PyPI release |
| `--cache-file` | `<path>` | Read and write a PyPI metadata cache |
| `--no-cache` | — | Bypass the cache and force fresh lookups |

!!! note "Offline by default"
    Without `--check-latest`, LicenseGuard makes no network calls at all. It reads only local package metadata.

[:octicons-arrow-right-24: Drift analysis guide](../drift/overview.md)

---

## Output modes compared

=== "Default (`--cli`)"

    Prints, in order:

    1. A fixed-width dependency table
    2. A summary block with status totals
    3. The full JSON payload

    Warnings are written to stderr.

=== "`--json-only`"

    - Emits only JSON on stdout
    - Keeps warnings on stderr for automation visibility
    - The right mode for machine parsing

=== "`--no-table`"

    - Skips the human-readable table
    - Still prints the JSON payload

---

## Exit behavior

By default the command exits non-zero when the worst status is `DENIED` or `RESTRICTED`.

| Flag | Fails when |
|---|---|
| `--fail-on denied` | Any package is DENIED |
| `--fail-on restricted` | Any package is DENIED or RESTRICTED |
| `--fail-on unknown` | Any package is not APPROVED |

This is what makes LicenseGuard usable as a CI gate.

[:octicons-arrow-right-24: Choosing a threshold](../ci-cd/gating.md)

---

## Input parsing notes

- Comments and blank lines in `requirements.txt` are ignored
- Editable installs (`-e`, `--editable`) and egg fragments are handled
- `-r` / `--requirement` includes are recognized but not recursed into for root discovery
- URL and VCS entries may not yield an extractable package name and will emit a warning
- Scanning continues for all parseable roots

---

## Report fields

### Top level

| Field | Description |
|---|---|
| `requirements_file` | Absolute path to the scanned file |
| `rows` | Package-level findings |
| `summary` | Status counts and worst status |
| `warnings` | Parse, resolution, and network warnings |
| `check_latest` | Present only when drift mode is enabled |

### Row level

| Field | Description |
|---|---|
| `package`, `version` | Canonical name and installed version |
| `direct` | `true` for requirements-file entries, `false` for transitive |
| `installed` | Always `true` in the current design |
| `license_detected` | Raw license string from metadata |
| `license_spdx` | Normalized identifier |
| `status` | APPROVED, RESTRICTED, DENIED, or UNKNOWN |
| `reason` | Explanation of the classification |
| `unknown_type` | `no_metadata` or `unrecognized`, when status is UNKNOWN |

### Drift fields

Present only with `--check-latest`:

`version_latest`, `license_latest`, `license_changed`, `change_type`

[:octicons-arrow-right-24: Full report schema](../api/report-schema.md)

---

## Related

- [Command examples](examples.md) — practical recipes
- [Web dashboard](../dashboard/overview.md) — the default mode
