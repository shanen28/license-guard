# Using the Dashboard

Detailed behavior of filtering, sorting, policy application, and exports.

---

## Filtering and search

| Control | Behavior |
|---|---|
| **Search** | Matches package name, license string, and status text |
| **Status filter** | Narrows rows to a single classification |
| **Chart bars** | Clicking a bar filters the tables to that status |

Filters apply across both the direct and transitive tables simultaneously, so a search reflects the whole dependency tree rather than one section.

---

## Sorting

Table column headers toggle between ascending and descending order. Sorting applies within each section — direct and transitive remain grouped rather than interleaving.

---

## The distribution chart

A canvas-drawn bar chart showing counts per status. Bars are interactive: clicking one applies the corresponding status filter, and clicking again clears it.

This is the fastest route from "one denied package exists" to seeing which package it is.

---

## Large dependency trees

For projects with many packages, the dashboard renders lazily:

- Sections render on expansion rather than on page load
- Rows paginate in batches of 100
- A **load more** control extends the visible set

This keeps the page responsive on trees with several hundred resolved packages.

---

## Applying a policy

When you click **Apply policy**:

1. Each input is split on commas into tokens.
2. The payload is posted to `/policy`.
3. The policy is retained in server session state.
4. The next scan uses it, unless overridden by a policy path.

```text
approved:   MIT, BSD, Apache-2.0, ISC
restricted: LGPL, MPL
denied:     GPL, AGPL
```

!!! tip "Use the dashboard to draft, a file to enforce"
    The in-memory editor is a fast way to try rule combinations and see the effect immediately. Once the lists look right, copy them into a [policy file](../policy/policy-file.md) so they are version-controlled and usable in CI.

---

## Exports

| Format | Endpoint | Notes |
|---|---|---|
| JSON | `/download` | The full report, identical to CLI output |
| CSV | `/download/csv` | Flattened rows; direct dependencies first |

Both buttons stay disabled until a scan succeeds in the current session.

CSV suits spreadsheet review and sharing with non-technical reviewers. JSON suits tooling, diffing, and audit storage.

---

## Errors and warnings

| Display | Meaning |
|---|---|
| Error banner | A fatal problem — the scan did not complete |
| Warning banner | Non-fatal issues such as unparseable requirement lines |

Download actions remain disabled after a failed scan, since there is no result to export.

---

## Troubleshooting

??? failure "The browser does not open"
    Confirm the scan works in terminal mode first:

    ```bash
    licenseguard scan requirements.txt --cli
    ```

    Then check that the local port is free and that `fastapi` and `uvicorn` are installed in the active environment.

??? failure "The page loads but shows nothing"
    The dashboard does not scan automatically. Click **Run scan**. If the empty state persists, check the browser console and network tab for a failed `/scan` request.

??? failure "Download buttons stay disabled"
    Downloads require a successful scan in the current session. Re-run the scan, check the error banner, and confirm the `/scan` request returned successfully.

[:octicons-arrow-right-24: Full troubleshooting guide](../troubleshooting.md)

---

## When to use the CLI instead

The dashboard is for exploration and triage. Use the CLI when you need:

- a policy file rather than in-memory rules
- drift analysis (`--check-latest`)
- exit-code gating (`--fail-on`)
- scripted or scheduled execution

[:octicons-arrow-right-24: CLI reference](../cli/commands.md)
