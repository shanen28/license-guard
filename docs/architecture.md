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

## Resolution model

Resolver behavior is installed-only:

1. Parse direct roots from `requirements.txt`
2. Build installed distribution map from `importlib.metadata.distributions()`
3. BFS through `requires_dist` but only follow dependencies present in installed map
4. Skip missing dependencies silently

This keeps output aligned with the actual runtime environment.

## Scan pipeline

1. Load roots and resolve packages
2. Build row data from installed distributions
3. Classify status and reason via policy logic
4. Append unpinned direct-dependency warnings into row reason
5. Optionally enrich rows with PyPI drift fields
6. Build summary and return report

## Web architecture

The web app is a local FastAPI service with in-memory session state:

- Current requirements path
- Current policy config/path
- Drift flags and cache path
- Last scan result for download endpoints

Frontend is a single HTML page with vanilla JS and CSS embedded in `webapp.py`.
