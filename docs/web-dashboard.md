---
layout: default
title: Web Dashboard Guide
prev_url: /cli-reference.html
prev_title: CLI Reference
next_url: /policy-guide.html
next_title: Policy Guide
---

# Web Dashboard Guide

LicenseGuard includes a local FastAPI dashboard launched by default when `--cli` is not provided.

## Start dashboard

```bash
licenseguard scan requirements.txt
```

The CLI opens a browser and starts a local server (typically `127.0.0.1:8000+`).

## Scan lifecycle

The dashboard is manual-run by design:

1. Page opens
2. Empty state is shown
3. User clicks **Run scan**
4. Loading overlay appears during request
5. Status line updates with duration and analyzed package count
6. Results panel is shown

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
- Lazy rendering for large sections with load-more controls

## CSV and JSON downloads

- JSON endpoint: `/download`
- CSV endpoint: `/download/csv`
- CSV ordering mirrors UI: direct dependencies first, then transitive

Download buttons are disabled until a successful scan populates session result state.

## Filtering and sorting behavior

- Search matches package name, license string, and status text
- Status filter narrows rows to a single classification
- Table sort headers toggle ascending and descending ordering
- Filters apply across direct and transitive tables

## Policy application flow

In-memory policy controls in the dashboard do not modify files on disk.

When **Apply policy** is clicked:

1. Tokens are split by commas
2. Policy payload is posted to `/policy`
3. Policy is retained in server state for subsequent scans
4. Next scan uses that in-memory policy unless overridden by query policy path

## Error and warning display

- Fatal issues are shown in the error banner
- Non-fatal warnings are shown in warning banner
- Download actions remain disabled after failed scans

## Manual scan behavior

Dashboard intentionally does not auto-run on load. Users click **Run scan** to begin.
