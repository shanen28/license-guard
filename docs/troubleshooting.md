---
layout: default
title: Troubleshooting
prev_url: /ci-cd.html
prev_title: CI/CD Integration
next_url: /index.html
next_title: Documentation Overview
---

# Troubleshooting

## `error: command required`

You ran `licenseguard` without subcommand. Use:

```bash
licenseguard scan requirements.txt --cli
```

## `error: file not found`

Check the requirements path is correct and relative to your current directory.

## `error: policy file not found`

The `--policy` path does not exist in the current working directory context.

Use absolute paths when running from CI or from a different project directory.

## `invalid policy file`

This usually means:

- file syntax is invalid YAML/JSON
- keys are wrong type (must be lists)
- list entries are empty or non-string values

## Empty results

LicenseGuard only reports installed packages. If rows are empty:

- Ensure dependencies are installed in the active environment
- Confirm package names in `requirements.txt` are parseable

If needed, run:

```bash
pip list
```

to confirm the expected packages are present.

## Too many `UNKNOWN` statuses

- Some packages have missing or unusual license metadata
- Add policy rules where possible
- Use result `reason` and `unknown_type` to triage

## Unparseable requirement warnings

Warnings like `could not parse package name` indicate lines that cannot be treated as package roots.

Common causes:

- VCS URLs without clear package metadata
- malformed requirement syntax
- unsupported line patterns

The scan continues for valid lines.

## Drift mode failures or warnings

`--check-latest` needs network access to PyPI.

- Retry for transient DNS/network issues
- Use `--cache-file` for stability
- Inspect `warnings` in output

## Web UI not opening

- Use `--cli` to confirm scan works first
- Check local port availability
- Verify FastAPI/Uvicorn are installed

## Web UI loads but no results visible

- Click **Run scan** (manual-run behavior)
- Confirm empty state disappears after successful scan
- Check browser console/network tab for frontend request failures

## Download buttons disabled

Downloads become enabled only after a successful scan in the current session.

If disabled unexpectedly:

1. Re-run scan
2. Check error banner
3. Confirm `/scan` request succeeded

## Common sanity checks

```bash
licenseguard --version
pytest -q
python -m build
python -m twine check dist/*
```

## When to open an issue

Open a repository issue with:

- exact command run
- full stderr/stdout output
- Python version
- operating system
- minimal reproducible `requirements.txt`
