# Web Dashboard Guide

LicenseGuard includes a local FastAPI dashboard launched by default when `--cli` is not provided.

## Start dashboard

```bash
licenseguard scan requirements.txt
```

The CLI opens a browser and starts a local server (typically `127.0.0.1:8000+`).

## Main UI areas

### Scan section

- **Run scan** button starts analysis
- **Download JSON** and **Download CSV** stay disabled until a successful scan
- Status line shows: scan duration and analyzed package count
- Hint text points users to CLI for advanced options

### Policy section

- In-memory policy inputs for approved/restricted/denied tokens
- `Apply policy` updates policy state for subsequent scans

### Results section

- Empty state shown before first scan
- Summary cards for Approved, Restricted, Denied, Unknown
- Interactive distribution chart (click bars to filter by status)
- Search and status filters
- Split tables for direct and transitive dependencies

## CSV and JSON downloads

- JSON endpoint: `/download`
- CSV endpoint: `/download/csv`
- CSV ordering mirrors UI: direct dependencies first, then transitive

## Manual scan behavior

Dashboard intentionally does not auto-run on load. Users click **Run scan** to begin.
