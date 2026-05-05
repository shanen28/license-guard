# LicenseGuard Documentation

Welcome to the LicenseGuard documentation. This guide covers CLI usage, web dashboard behavior, policy design, PyPI drift analysis, Python API usage, architecture, CI integration, and troubleshooting.

## What LicenseGuard does

LicenseGuard scans dependencies from a `requirements.txt` and analyzes only packages that are currently installed in your environment.

It provides:

- License compliance status per package (`APPROVED`, `RESTRICTED`, `DENIED`, `UNKNOWN`)
- Direct vs transitive dependency visibility
- Optional PyPI "latest version" drift analysis
- JSON, CSV, and terminal-friendly outputs
- A local web dashboard for interactive filtering and reporting

## Documentation map

- [Getting Started](getting-started.md)
- [CLI Reference](cli-reference.md)
- [Web Dashboard Guide](web-dashboard.md)
- [Policy Guide](policy-guide.md)
- [PyPI Drift Analysis](pypi-drift.md)
- [Python API Guide](python-api.md)
- [Architecture and Internals](architecture.md)
- [CI/CD Integration](ci-cd.md)
- [Troubleshooting](troubleshooting.md)

## Version

This documentation targets LicenseGuard `0.3.0`.

## Publish on GitHub Pages

1. Open repository **Settings -> Pages**
2. Source: **Deploy from a branch**
3. Branch: **main**
4. Folder: **/docs**
5. Save

GitHub will publish these Markdown pages automatically.
