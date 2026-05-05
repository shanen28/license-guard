---
layout: default
title: Documentation Overview
prev_url:
prev_title:
next_url: /getting-started.html
next_title: Getting Started
---

# LicenseGuard Documentation

LicenseGuard is a dependency license analysis tool for Python projects. It reads your `requirements.txt`, resolves only packages installed in the active environment, classifies license risk, and optionally compares installed metadata against latest PyPI releases.

This documentation is intentionally detailed so teams can use LicenseGuard for local development, CI enforcement, and governance workflows.

## Audience

This documentation is written for:

- Python developers integrating dependency compliance checks
- Platform and DevOps engineers building quality gates
- Security and legal-adjacent reviewers who need machine-readable reports

## Product summary

LicenseGuard provides:

- Installed-only dependency graph traversal
- Direct vs transitive dependency visibility
- License normalization into SPDX-like identifiers
- Policy-based classification (`APPROVED`, `RESTRICTED`, `DENIED`, `UNKNOWN`)
- Optional drift analysis against latest PyPI metadata
- CLI output, JSON report output, CSV export, and local dashboard UI

## Documentation map

- [Getting Started](getting-started.md)  
  Installation, first scan, and basic workflow.
- [CLI Reference](cli-reference.md)  
  Every option, behavior, and practical command examples.
- [Web Dashboard Guide](web-dashboard.md)  
  UI behavior, scan lifecycle, filtering, and downloads.
- [Policy Guide](policy-guide.md)  
  Policy file format, evaluation rules, and governance patterns.
- [PyPI Drift Analysis](pypi-drift.md)  
  How compare-latest mode works, fields, and operational guidance.
- [Python API Guide](python-api.md)  
  Programmatic usage and integration examples.
- [Architecture and Internals](architecture.md)  
  Module-level design and execution flow.
- [CI/CD Integration](ci-cd.md)  
  Pipeline integration strategies and gate patterns.
- [Troubleshooting](troubleshooting.md)  
  Common issues, diagnostics, and resolution steps.

## Version compatibility

This documentation targets LicenseGuard `0.3.0`.

## Read this first

If you are new to the project, start here:

1. [Getting Started](getting-started.md)
2. [CLI Reference](cli-reference.md)
3. [Policy Guide](policy-guide.md)

If you are integrating in CI:

1. [CLI Reference](cli-reference.md)
2. [CI/CD Integration](ci-cd.md)
3. [Troubleshooting](troubleshooting.md)

## GitHub Pages publishing

To publish docs from this repository:

1. Open repository **Settings -> Pages**
2. Source: **Deploy from a branch**
3. Branch: **main**
4. Folder: **/docs**
5. Save

GitHub Pages will publish these Markdown files automatically.
