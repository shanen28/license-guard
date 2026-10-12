# Web Dashboard

LicenseGuard ships with a local FastAPI dashboard, launched by default when `--cli` is not provided.

---

## Starting it

```bash
licenseguard scan requirements.txt
```

The CLI starts a local server (typically on `127.0.0.1:8000` or the next free port) and opens your browser.

!!! note "Local only"
    The dashboard binds to localhost and holds all state in memory for the lifetime of the process. It is a single-user development tool, not a hosted service. Nothing is persisted to disk unless you download a report.

---

## Scan lifecycle

The dashboard does **not** scan on load. Scanning is a deliberate action:

1. The page opens in an empty state.
2. You click **Run scan**.
3. A loading overlay appears while the request runs.
4. The status line reports scan duration and package count.
5. The results panel renders.

This keeps the tool predictable — opening the page never triggers work you did not ask for.

---

## Interface sections

### Scan

| Control | Behavior |
|---|---|
| **Run scan** | Starts the analysis |
| **Download JSON** | Disabled until a successful scan |
| **Download CSV** | Disabled until a successful scan |
| Status line | Scan duration and number of packages analyzed |

### Policy

In-memory policy inputs for approved, restricted, and denied tokens. **Apply policy** stores the lists in server session state for subsequent scans.

!!! warning "Dashboard policies are not saved"
    The in-memory policy applies only to the running session and never writes to disk. For anything durable or shared, use a [policy file](../policy/policy-file.md).

### Results

- Summary cards for each of the four statuses
- An interactive distribution chart — click a bar to filter by that status
- Search and status filters
- Separate tables for direct and transitive dependencies
- Lazy rendering with load-more controls for large trees

---

## Architecture

The frontend is a single HTML page with vanilla JavaScript and CSS embedded directly in `webapp.py`. There is no React, no build step, and no bundler.

That is a deliberate tradeoff: for a locally launched single-user tool, a framework would add packaging complexity and a build toolchain without improving the experience. The chart is drawn on a `<canvas>` element; theming uses CSS custom properties; dark mode preference persists in `localStorage`.

[:octicons-arrow-right-24: Architecture and design decisions](../architecture/design-decisions.md)

---

## Endpoints

| Endpoint | Purpose |
|---|---|
| `/` | Dashboard page |
| `/scan` | Run a scan, return the report |
| `/policy` | Set the in-memory policy |
| `/download` | JSON report download |
| `/download/csv` | CSV report download |

CSV ordering mirrors the UI: direct dependencies first, then transitive.

---

## Session state

The server holds, in memory:

- the current requirements path
- the current policy configuration or path
- drift flags and cache path
- the most recent scan result, used by the download endpoints

Downloads are disabled until that result exists, which is why they stay greyed out after a failed scan.

---

## Related

- [Using the dashboard](usage.md) — filtering, sorting, and exports in detail
- [CLI commands](../cli/commands.md) — the terminal alternative
