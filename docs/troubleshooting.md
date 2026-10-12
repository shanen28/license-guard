# Troubleshooting

---

## Command errors

??? failure "`error: command required`"
    You ran `licenseguard` without a subcommand.

    ```bash
    licenseguard scan requirements.txt --cli
    ```

??? failure "`error: file not found`"
    The requirements path is wrong or relative to a different directory. Use an absolute path when running from CI or another project directory.

??? failure "`error: policy file not found`"
    The `--policy` path does not resolve from the current working directory.

    ```bash
    licenseguard scan requirements.txt --cli --policy "$PWD/policy.yaml"
    ```

??? failure "`invalid policy file`"
    Usually one of:

    - the file is not valid YAML or JSON
    - a key's value is not a list
    - a list contains empty or non-string entries

    [:octicons-arrow-right-24: Policy file format](policy/policy-file.md)

??? failure "`licenseguard: command not found`"
    The console script is not on `PATH`, typically because a different environment is active.

    1. Activate the correct virtual environment.
    2. Reinstall: `pip install --force-reinstall licenseguard`
    3. Or invoke the module directly: `python -m licenseguard.cli --version`

---

## Empty or incomplete results

LicenseGuard reports only on **installed** packages. Empty results almost always mean the environment is not the one holding your dependencies.

```bash
# Confirm the expected packages are present
pip list

# Confirm which interpreter is active
python -c "import sys; print(sys.executable)"
```

Checklist:

- [ ] Dependencies installed in the **active** environment
- [ ] LicenseGuard installed in that **same** environment
- [ ] Package names in `requirements.txt` are parseable

!!! tip "In CI, install before scanning"
    ```bash
    pip install -r requirements.txt licenseguard
    licenseguard scan requirements.txt --cli
    ```

[:octicons-arrow-right-24: Why installed-only](core-concepts/installed-only.md)

---

## Too many UNKNOWN statuses

Some packages publish unusual or absent license metadata. Triage with `unknown_type`:

```bash
licenseguard scan requirements.txt --cli --json-only \
  | jq -r '.rows[] | select(.status == "UNKNOWN")
           | "\(.package): \(.unknown_type) — \(.license_detected // "none")"'
```

| `unknown_type` | What to do |
|---|---|
| `unrecognized` | Read `license_detected` and add that string to your policy |
| `no_metadata` | Check the package repository for a `LICENSE` file, then classify explicitly |

[:octicons-arrow-right-24: License detection](core-concepts/license-detection.md)

---

## Unparseable requirement warnings

A warning such as `could not parse package name` means a line could not be treated as a package root.

Common causes:

- VCS URLs without clear package metadata
- malformed requirement syntax
- unsupported line patterns

The scan continues for all valid lines. If a package you care about is missing from the report, check whether its requirement line produced a warning.

---

## Drift mode problems

`--check-latest` requires network access to PyPI.

| Symptom | Resolution |
|---|---|
| Intermittent failures | Usually transient DNS or network issues; retry |
| Slow scans | Add `--cache-file` to persist responses between runs |
| Many `unknown` change types | Inspect `warnings` for lookup failures |
| Fails in CI | Confirm the runner has outbound network access |

```bash
licenseguard scan requirements.txt \
  --cli --check-latest \
  --cache-file .licenseguard_cache.json
```

!!! note "Not for offline environments"
    If your build must be deterministic or runs air-gapped, leave drift mode off and run it as a separate scheduled job instead.

---

## Dashboard issues

??? failure "The browser does not open"
    1. Confirm the scan works in terminal mode: `licenseguard scan requirements.txt --cli`
    2. Check that the local port is available
    3. Verify `fastapi` and `uvicorn` are installed in the active environment

??? failure "The page loads but shows no results"
    The dashboard does not scan automatically — click **Run scan**. If the empty state persists, check the browser console and network tab for a failed `/scan` request.

??? failure "Download buttons are disabled"
    Downloads require a successful scan in the current session.

    1. Re-run the scan
    2. Check the error banner
    3. Confirm `/scan` returned successfully

??? failure "CLI flags appear to be ignored"
    `--json-only`, `--no-table`, `-o`, and `--fail-on` apply only in CLI mode. Add `--cli`:

    ```bash
    licenseguard scan requirements.txt --cli --fail-on restricted
    ```

---

## CI-specific issues

| Symptom | Likely cause |
|---|---|
| Scan passes but reports nothing | Dependencies not installed before scanning |
| Policy file not found | Relative path resolving from a different working directory |
| Build fails unexpectedly | Default threshold is `restricted`; set `--fail-on` explicitly |
| Report artifact missing on failure | Add `if: always()` to the upload step |

[:octicons-arrow-right-24: CI/CD integration](ci-cd/integration.md)

---

## Sanity checks

```bash
# Version
licenseguard --version

# Test suite (from a source checkout)
pytest -q

# Build and validate a distribution
python -m build
python -m twine check dist/*
```

---

## Reporting an issue

Open an issue at [github.com/shanen28/license-guard/issues](https://github.com/shanen28/license-guard/issues) including:

- the exact command you ran
- full stdout and stderr
- Python version and operating system
- a minimal `requirements.txt` that reproduces the problem

Redact anything proprietary from the report before attaching it.
