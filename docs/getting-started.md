---
layout: default
title: Getting Started
prev_url: /index.html
prev_title: Documentation Overview
next_url: /cli-reference.html
next_title: CLI Reference
---

# Getting Started

## Requirements

- Python 3.9+
- A virtual environment (recommended)
- Dependencies installed in the same environment where LicenseGuard runs
- A `requirements.txt` file with the dependencies you want to evaluate

## Install LicenseGuard

### From source (this repository)

```bash
pip install .
```

### Development install

```bash
pip install -e ".[dev]"
```

Development extras include test dependencies used by this repository.

## Verify environment

```bash
python --version
pip --version
licenseguard --version
```

If the `licenseguard` command is not found, activate the correct virtual environment and reinstall.

## Understand installed-only behavior

LicenseGuard intentionally scans only what is currently installed.  
If a package is listed in `requirements.txt` but not installed, it is skipped.

This design avoids mismatches between declared dependencies and runtime reality.

## First scan (CLI mode)

```bash
licenseguard scan requirements.txt --cli
```

This command:

1. Parses package names from `requirements.txt`
2. Resolves only installed packages (direct + transitive)
3. Detects and normalizes license metadata
4. Applies built-in or custom policy rules
5. Prints table + summary + JSON report

## First scan (Web dashboard mode)

```bash
licenseguard scan requirements.txt
```

This launches the local web UI. In current UX, scan execution is manual: click **Run scan**.

## Typical workflow

1. Install project dependencies
2. Run LicenseGuard scan
3. Review denied/restricted packages
4. Add or adjust a policy file
5. Enforce in CI with `--fail-on`
6. Store JSON artifacts for historical comparison

## Expected outputs

Every run returns:

- `rows`: package-level findings
- `summary`: status counts and worst status
- `warnings`: parse/resolution/network warnings

In `--check-latest` mode, row-level drift fields are added.

## Next steps

- Continue with [CLI Reference](cli-reference.md) for complete command options
- Continue with [Policy Guide](policy-guide.md) for policy design
- Continue with [CI/CD Integration](ci-cd.md) for pipeline setup

## Verify installation

```bash
licenseguard --version
```

Expected output includes the current version, such as `licenseguard 0.3.0`.
