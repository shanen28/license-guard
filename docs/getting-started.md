# Getting Started

## Requirements

- Python 3.9+
- A virtual environment (recommended)
- Dependencies installed in the same environment where LicenseGuard runs

## Install LicenseGuard

### From source (this repository)

```bash
pip install .
```

### Development install

```bash
pip install -e ".[dev]"
```

## First scan

```bash
licenseguard scan requirements.txt --cli
```

This command:

1. Parses package names from `requirements.txt`
2. Resolves only installed packages (direct + transitive)
3. Detects and normalizes license metadata
4. Applies built-in or custom policy rules
5. Prints table + summary + JSON report

## Typical workflow

1. Install project dependencies
2. Run LicenseGuard scan
3. Review denied/restricted packages
4. Add or adjust a policy file
5. Enforce in CI with `--fail-on`

## Verify installation

```bash
licenseguard --version
```

Expected output includes the current version, such as `licenseguard 0.3.0`.
