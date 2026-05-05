# Troubleshooting

## `error: command required`

You ran `licenseguard` without subcommand. Use:

```bash
licenseguard scan requirements.txt --cli
```

## `error: file not found`

Check the requirements path is correct and relative to your current directory.

## Empty results

LicenseGuard only reports installed packages. If rows are empty:

- Ensure dependencies are installed in the active environment
- Confirm package names in `requirements.txt` are parseable

## Too many `UNKNOWN` statuses

- Some packages have missing or unusual license metadata
- Add policy rules where possible
- Use result `reason` and `unknown_type` to triage

## Drift mode failures or warnings

`--check-latest` needs network access to PyPI.

- Retry for transient DNS/network issues
- Use `--cache-file` for stability
- Inspect `warnings` in output

## Web UI not opening

- Use `--cli` to confirm scan works first
- Check local port availability
- Verify FastAPI/Uvicorn are installed

## Download buttons disabled

Downloads become enabled only after a successful scan in the current session.

## Common sanity checks

```bash
licenseguard --version
pytest -q
python -m build
python -m twine check dist/*
```
