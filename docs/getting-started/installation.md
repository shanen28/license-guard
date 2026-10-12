# Installation

## Requirements

| Requirement | Detail |
|---|---|
| Python | 3.9 or newer |
| Environment | A virtual environment is strongly recommended |
| Dependencies | Must be installed in the **same** environment where LicenseGuard runs |
| Input | A `requirements.txt` describing the dependencies to evaluate |

!!! important "Same-environment rule"
    LicenseGuard reports on **installed** packages. If it runs in a different environment than your project's dependencies, it will find nothing to report. See [Installed-Only Resolution](../core-concepts/installed-only.md).

---

## Install from PyPI

=== "pip"

    ```bash
    pip install licenseguard
    ```

=== "pipx (isolated CLI)"

    ```bash
    pipx install licenseguard
    ```

    !!! warning
        With `pipx`, LicenseGuard is isolated from your project environment and will not see your project's packages. Use `pip` inside your project venv instead.

=== "uv"

    ```bash
    uv pip install licenseguard
    ```

---

## Install from source

```bash
git clone https://github.com/shanen28/license-guard.git
cd license-guard
pip install .
```

### Development install

```bash
pip install -e ".[dev]"
```

Development extras add `pytest` and `httpx`, used by the repository's test suite.

---

## Recommended: a project virtual environment

=== "Linux / macOS"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install licenseguard
    ```

=== "Windows (PowerShell)"

    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    pip install licenseguard
    ```

This guarantees LicenseGuard and your dependencies share one environment.

---

## Dependencies

LicenseGuard installs a small runtime footprint:

| Package | Purpose |
|---|---|
| `packaging` | PEP 508 requirement parsing and name canonicalization |
| `PyYAML` | Policy file loading |
| `fastapi` | Local dashboard application |
| `uvicorn` | ASGI server for the dashboard |

---

## Verify the installation

```bash
licenseguard --version
```

Expected output resembles:

```text
licenseguard 0.3.1
```

Also confirm your interpreter and package manager:

```bash
python --version
pip --version
```

??? failure "`licenseguard: command not found`"
    The console script is installed into the environment's `Scripts/` (Windows) or `bin/` (POSIX) directory. If the command is missing:

    1. Confirm the correct virtual environment is activated.
    2. Reinstall with `pip install --force-reinstall licenseguard`.
    3. As a fallback, invoke the module directly:

    ```bash
    python -m licenseguard.cli --version
    ```

---

## Next steps

- [Quickstart](quickstart.md) — run a scan in under a minute
- [Your first scan](first-scan.md) — understand the output in detail
