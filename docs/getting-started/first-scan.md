# Your First Scan

This page walks through what happens when you run a scan and how to read the result.

---

## Run it

```bash
licenseguard scan requirements.txt --cli
```

---

## What the command does

1. **Parses direct roots** from `requirements.txt`, handling editable installs, egg fragments, and PEP 508 specifiers.
2. **Resolves the installed graph** by walking `requires_dist` breadth-first, following only packages present in the environment.
3. **Detects license metadata** for each resolved distribution.
4. **Normalizes** the raw license text into an SPDX-style identifier.
5. **Classifies** each package against the active policy.
6. **Enriches** rows with warnings such as unpinned direct dependencies.
7. **Aggregates** a summary and emits the report.

---

## Reading the output

### The table

Each row represents one resolved package:

| Column | Meaning |
|---|---|
| `package` | Canonical distribution name |
| `version` | Version installed in the current environment |
| `direct` | `true` if listed in `requirements.txt`, `false` if pulled in transitively |
| `license_detected` | Raw license string found in package metadata |
| `license_spdx` | Normalized SPDX-style identifier |
| `status` | `APPROVED`, `RESTRICTED`, `DENIED`, or `UNKNOWN` |
| `reason` | Why this status was assigned |

### The summary

```json
{
  "approved": 42,
  "restricted": 3,
  "denied": 1,
  "unknown": 2,
  "total": 48,
  "worst_status": "DENIED",
  "counts_by_status": { "...": "..." }
}
```

`worst_status` is the single most severe status present, using the ordering **DENIED → RESTRICTED → UNKNOWN → APPROVED**. It is the field to gate on programmatically.

### The warnings

Warnings never stop a scan. They report conditions worth knowing about:

- requirement lines that could not be parsed into a package root
- VCS or URL entries without extractable metadata
- network or metadata failures during drift lookups

---

## Triaging the result

!!! tip "Work in this order"
    1. **DENIED** — blocking. Replace the dependency or amend the policy deliberately.
    2. **RESTRICTED** — needs a human decision about obligations such as attribution or source disclosure.
    3. **UNKNOWN** — inspect `unknown_type` to see whether metadata was missing (`no_metadata`) or simply unrecognized (`unrecognized`).
    4. **APPROVED** — no action.

### Unpinned dependencies

Direct requirements that are not strictly pinned with `==` or `===` receive an extra note:

```text
Unpinned dependency — license may change on upgrade
```

This is a warning, not a status change. It flags packages whose license could shift the next time the environment is rebuilt.

---

## Why some packages are missing

LicenseGuard reports only what is installed. A package listed in `requirements.txt` but absent from the environment is skipped silently by design.

If your results look empty or short:

```bash
pip list
```

Confirm the expected packages are present and that you are in the right virtual environment.

[:octicons-arrow-right-24: Read more about installed-only resolution](../core-concepts/installed-only.md)

---

## Save the report

```bash
licenseguard scan requirements.txt --cli --json-only -o licenseguard-report.json
```

Persisting JSON gives you an audit trail and lets you diff results between builds.

---

## Next steps

- [Risk classification](../core-concepts/risk-classification.md) — how statuses are decided
- [Policy overview](../policy/overview.md) — override the built-in defaults
- [CI/CD integration](../ci-cd/integration.md) — turn this into a build gate
