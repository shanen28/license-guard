# Report Schema

The structure returned by `scan_requirements_file()` and emitted as JSON by the CLI. The CLI and the dashboard consume this identical shape.

---

## Top level

```json
{
  "requirements_file": "/abs/path/to/requirements.txt",
  "rows": [ ... ],
  "summary": { ... },
  "warnings": [ ... ],
  "check_latest": true
}
```

| Field | Type | Description |
|---|---|---|
| `requirements_file` | string | Absolute path to the scanned file |
| `rows` | array | One entry per resolved package |
| `summary` | object | Aggregate counts and worst status |
| `warnings` | array of strings | Non-fatal parse, resolution, and network issues |
| `check_latest` | boolean | Present **only** when drift mode is enabled |

---

## Row object

```json
{
  "package": "requests",
  "version": "2.32.3",
  "direct": true,
  "installed": true,
  "license_detected": "Apache 2.0",
  "license_spdx": "Apache-2.0",
  "status": "APPROVED",
  "reason": "Matched approved rule: Apache",
  "unknown_type": null
}
```

| Field | Type | Description |
|---|---|---|
| `package` | string | Canonical distribution name |
| `version` | string | Version installed in the environment |
| `direct` | boolean | `true` if listed in `requirements.txt` |
| `installed` | boolean | Always `true` in the current design |
| `license_detected` | string | Raw license string from package metadata |
| `license_spdx` | string | Normalized SPDX-style identifier |
| `status` | string | `APPROVED`, `RESTRICTED`, `DENIED`, or `UNKNOWN` |
| `reason` | string | Explanation of the classification |
| `unknown_type` | string or null | Set when `status` is `UNKNOWN` |

!!! note "Why both license fields"
    `license_detected` preserves exactly what the package claimed; `license_spdx` is what LicenseGuard made of it. Keeping both makes normalization auditable — you can always see the input to the decision.

### `status` values

| Value | Meaning |
|---|---|
| `APPROVED` | Permissive; no action needed |
| `RESTRICTED` | Usable with obligations; review required |
| `DENIED` | Not acceptable under the active policy |
| `UNKNOWN` | Could not be determined or recognized |

### `unknown_type` values

| Value | Meaning |
|---|---|
| `no_metadata` | No license information present in the package |
| `unrecognized` | Metadata present but normalization failed |
| `null` | Status is not `UNKNOWN` |

---

## Drift fields

Added to each row only when `check_latest` is enabled.

```json
{
  "version_installed": "2.1.0",
  "version_latest": "3.0.0",
  "license_installed": "MIT OR Apache-2.0",
  "license_latest": "MIT OR GPL-3.0",
  "license_changed": true,
  "change_type": "compatible_partial"
}
```

| Field | Type | Description |
|---|---|---|
| `version_installed` | string | Version in your environment |
| `version_latest` | string | Newest version on PyPI |
| `license_installed` | string | Normalized license of the installed version |
| `license_latest` | string | Normalized license of the latest version |
| `license_changed` | boolean | Whether the license changed at all |
| `change_type` | string | Classification of the change |

### `change_type` values

| Value | Meaning |
|---|---|
| `no_change` | Identical normalized token sets |
| `compatible` | Latest tokens are a subset of installed tokens |
| `compatible_partial` | Partial overlap between sets |
| `incompatible` | Disjoint sets, or broadening in a risky direction |
| `unknown` | Lookup or metadata problems prevented comparison |

`license_changed` is `true` for `compatible`, `compatible_partial`, and `incompatible`.

[:octicons-arrow-right-24: Interpreting these values](../drift/interpreting.md)

---

## Summary object

```json
{
  "approved": 42,
  "restricted": 3,
  "denied": 1,
  "unknown": 2,
  "total": 48,
  "worst_status": "DENIED",
  "counts_by_status": {
    "APPROVED": 42,
    "RESTRICTED": 3,
    "DENIED": 1,
    "UNKNOWN": 2
  }
}
```

| Field | Type | Description |
|---|---|---|
| `approved` | integer | Count of approved packages |
| `restricted` | integer | Count of restricted packages |
| `denied` | integer | Count of denied packages |
| `unknown` | integer | Count of unknown packages |
| `total` | integer | Total resolved packages |
| `worst_status` | string | Most severe status present |
| `counts_by_status` | object | The same counts, keyed by status name |

`worst_status` uses the severity ordering **DENIED → RESTRICTED → UNKNOWN → APPROVED**. It is the field CLI gating compares against `--fail-on`.

---

## Warnings

An array of human-readable strings. Common causes:

- a requirement line that could not be parsed into a package root
- a VCS or URL entry with no extractable package name
- a failed or timed-out PyPI lookup during drift analysis

Warnings never fail a scan. They are written to stderr in CLI mode and shown in the dashboard's warning banner.

!!! tip "Read warnings in CI"
    A scan that skipped half its input still reports success. Surfacing `warnings` in your pipeline output keeps silent gaps visible.

---

## Related

- [Python API](python-api.md) — consuming the report in code
- [CLI commands](../cli/commands.md) — producing the report
