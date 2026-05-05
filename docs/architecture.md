---
layout: default
title: Architecture and Internals
prev_url: /python-api.html
prev_title: Python API Guide
next_url: /ci-cd.html
next_title: CI/CD Integration
---

# Architecture and Internals

LicenseGuard is organized into focused modules.

## Module map

- `licenseguard.resolver` - requirements parsing and installed dependency graph walk
- `licenseguard.license_detection` - extract and normalize license metadata
- `licenseguard.license_tokens` - OR/AND tokenization and drift comparisons
- `licenseguard.policy` - built-in and file-backed classification rules
- `licenseguard.scan` - orchestrates end-to-end scan and report assembly
- `licenseguard.pypi` - optional latest-release metadata retrieval + cache
- `licenseguard.webapp` - FastAPI app and embedded dashboard
- `licenseguard.cli` - command entrypoint and UX

## Design principles

- Prefer installed-runtime truth over declared intent
- Keep warning behavior explicit and non-blocking where possible
- Separate parsing, resolution, classification, and presentation concerns
- Keep the frontend framework-free for operational simplicity

## Resolution model

Resolver behavior is installed-only:

1. Parse direct roots from `requirements.txt`
2. Build installed distribution map from `importlib.metadata.distributions()`
3. BFS through `requires_dist` but only follow dependencies present in installed map
4. Skip missing dependencies silently

This keeps output aligned with the actual runtime environment.

## Why installed-only matters

Installed-only scanning avoids false positives from:

- stale or partially-applied `requirements.txt` files
- optional declarations not present in runtime
- unresolved transitive declarations from uninstalled packages

## Scan pipeline

1. Load roots and resolve packages
2. Build row data from installed distributions
3. Classify status and reason via policy logic
4. Append unpinned direct-dependency warnings into row reason
5. Optionally enrich rows with PyPI drift fields
6. Build summary and return report

## Data contracts

- Resolver returns `ResolvedPackage` records
- Scan converts records into serializable row dictionaries
- Summary is derived from status counts over current row set
- Web and CLI consume the same scan result shape

## Web architecture

The web app is a local FastAPI service with in-memory session state:

- Current requirements path
- Current policy config/path
- Drift flags and cache path
- Last scan result for download endpoints

Frontend is a single HTML page with vanilla JS and CSS embedded in `webapp.py`.

## Performance notes

- Distribution map lookup is cached in resolver
- UI uses lazy section rendering and paged row expansion
- Drift mode introduces network latency and optional disk cache behavior

## Extension points

Common enhancement paths:

- Add policy presets per organization
- Add SARIF or SPDX export formatters
- Add persistent report storage backend
- Add richer diffing between consecutive scans
