# Gating Strategy

Choosing what should fail a build, and when to tighten it.

---

## The three thresholds

| Flag | Fails on | Strictness |
|---|---|---|
| `--fail-on denied` | DENIED | Least strict |
| `--fail-on restricted` | DENIED, RESTRICTED | Common baseline |
| `--fail-on unknown` | Anything not APPROVED | Strictest |

Without `--fail-on`, the default is to fail when the worst status is `DENIED` or `RESTRICTED` — equivalent to `--fail-on restricted`.

---

## How the decision is made

The scan computes `summary.worst_status` using the severity ordering:

```text
DENIED  >  RESTRICTED  >  UNKNOWN  >  APPROVED
```

The threshold is compared against that single value. One denied package in a tree of five hundred fails the build.

---

## A staged adoption path

Turning on the strictest gate in an existing project usually produces a wall of failures that gets the check disabled. Adopt in stages.

=== "Stage 1 — Observe"

    Run without gating. Collect reports, understand what is actually in the tree.

    ```bash
    licenseguard scan requirements.txt --cli --json-only -o report.json || true
    ```

=== "Stage 2 — Block the worst"

    Gate on denied only. This should be a small, actionable set.

    ```bash
    licenseguard scan requirements.txt --cli --policy policy.yaml --fail-on denied
    ```

=== "Stage 3 — Baseline"

    Once the denied backlog is clear, require review of restricted licenses.

    ```bash
    licenseguard scan requirements.txt --cli --policy policy.yaml --fail-on restricted
    ```

=== "Stage 4 — Full provenance"

    Every package must be positively identified and approved. Appropriate for regulated or high-assurance projects.

    ```bash
    licenseguard scan requirements.txt --cli --policy policy.yaml --fail-on unknown
    ```

---

## Different gates in different places

A single threshold everywhere is rarely right. Match strictness to the cost of interruption.

| Context | Suggested threshold | Rationale |
|---|---|---|
| Pre-commit hook | `denied` | Fast feedback; must not block routine work |
| Pull request | `restricted` | The main governance gate |
| Release branch | `unknown` | Nothing unidentified ships |
| Scheduled drift | Report only | Alert the owner; do not break unrelated builds |

---

## Handling the unknown queue

`--fail-on unknown` is only sustainable if unknowns are actually driven to zero. Each one resolves in a predictable way:

1. Read `license_detected` and `unknown_type` for the row.
2. If `unrecognized`, add the raw string to your policy — it is a known license that simply did not normalize.
3. If `no_metadata`, check the package's repository for a `LICENSE` file and classify explicitly.
4. If the package genuinely has no license, treat that as a finding: unlicensed code carries no grant of rights.

[:octicons-arrow-right-24: Policy file format](../policy/policy-file.md)

---

## Custom gating logic

The built-in thresholds gate on the single worst status. For more nuanced rules — tolerating restricted transitives while blocking restricted directs, for instance — use the Python API:

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
        print(f"{row['package']} {row['version']}: {row['license_spdx']} ({row['status']})")
    raise SystemExit(1)
```

[:octicons-arrow-right-24: Python API reference](../api/python-api.md)

---

## Anti-patterns

!!! danger "Avoid these"
    - **Editing the policy to make a build pass** without review. Require code-owner approval on `policy.yaml`.
    - **Appending `|| true`** to silence a gate. If the gate is too strict, lower the threshold deliberately instead.
    - **Gating on drift results.** Metadata changes produce false positives; drift belongs in a scheduled report, not a blocking check.
    - **Scanning without installing.** An empty environment passes every threshold and tells you nothing.

---

## Related

- [CI/CD integration](integration.md) — pipeline configuration
- [Governance patterns](../policy/governance.md) — sustaining the process
