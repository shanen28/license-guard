# Contributing

---

## Development setup

```bash
git clone https://github.com/shanen28/license-guard.git
cd license-guard

python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```

Development extras add `pytest` and `httpx`.

!!! tip "Always use a virtual environment"
    LicenseGuard depends on `fastapi` and `uvicorn` with version constraints that can conflict with other globally installed tooling. An isolated environment avoids disturbing the rest of your system.

---

## Running tests

```bash
pytest -q
```

The suite covers three layers:

| File | Scope |
|---|---|
| `tests/test_licenseguard.py` | Resolution, detection, normalization, policy, tokens |
| `tests/test_cli.py` | Argument handling, output modes, exit codes |
| `tests/test_webapp.py` | Endpoints, scan lifecycle, downloads |

Run a single file or test while iterating:

```bash
pytest tests/test_licenseguard.py -v
pytest -k "normalize" -v
```

---

## Project layout

```text
license-guard/
├── src/licenseguard/
│   ├── cli.py                 # Command entry point
│   ├── resolver.py            # Requirements parsing, graph traversal
│   ├── license_detection.py   # Metadata extraction and normalization
│   ├── license_tokens.py      # OR/AND tokenization, drift comparison
│   ├── policy.py              # Classification rules
│   ├── scan.py                # Orchestration
│   ├── pypi.py                # PyPI client and caching
│   └── webapp.py              # FastAPI app and dashboard
├── tests/
├── docs/
└── mkdocs.yml
```

[:octicons-arrow-right-24: Architecture overview](architecture/overview.md)

---

## Working on the documentation

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

The site builds at `http://127.0.0.1:8000` with live reload.

Before opening a pull request, confirm a strict build passes — this is what CI runs:

```bash
mkdocs build --strict
```

`--strict` turns warnings, including broken internal links, into errors.

### Adding a page

1. Create the Markdown file under `docs/`.
2. Add it to the `nav` block in `mkdocs.yml`.
3. Run `mkdocs build --strict` to verify links resolve.

Documentation deploys automatically to GitHub Pages when changes to `docs/`, `mkdocs.yml`, or `requirements-docs.txt` land on `main`.

---

## Code conventions

- Type hints throughout; `from __future__ import annotations` at module top
- `dataclasses` for structured records
- Module-level separation — parsing, resolution, classification, and presentation stay independent
- Comments explain **why**, not what

---

## Adding license mappings

Normalization lives in `license_detection.py`. To add a mapping:

1. Add the phrase-to-SPDX entry to the lookup table.
2. Add a test case in `tests/test_licenseguard.py`.
3. Verify existing normalization tests still pass.

Prefer adding a precise mapping over broadening an existing pattern — substring rules that are too permissive cause misclassification elsewhere.

---

## Adding policy rules

Built-in rules live in `policy.py`. Keep in mind:

- Denied rules are evaluated before restricted, which are evaluated before approved.
- Matching is prefix-anchored, so `GPL` does not match `LGPL-3.0`.
- Any change to built-in defaults alters behavior for every user who has not supplied a policy file — add a test demonstrating the intended classification.

---

## Pull requests

Before submitting:

- [ ] `pytest -q` passes
- [ ] `mkdocs build --strict` passes, if docs changed
- [ ] New behavior has test coverage
- [ ] Documentation updated alongside the code
- [ ] Commit messages explain the reasoning, not just the change

---

## Releasing

Releases publish automatically from a version tag. Version numbers live in
**two** places and must match the tag, or the workflow fails before uploading:

- `pyproject.toml` → `[project].version`
- `src/licenseguard/__init__.py` → `__version__`

```bash
# 1. Bump the version in both files, then commit
git commit -am "Release 0.3.2"
git push

# 2. Tag and push the tag
git tag v0.3.2
git push origin v0.3.2
```

Pushing the tag triggers `.github/workflows/publish.yml`, which verifies the
tag against both version strings, runs the test suite, builds the sdist and
wheel, validates them with `twine check`, and publishes to PyPI.

!!! danger "PyPI versions are permanent"
    A version number can never be reused on PyPI, even after deleting a
    release. Never move or re-push a release tag — cut a new version instead.

### Trusted Publishing

Uploads use [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/),
so no API token is stored in the repository. PyPI mints a short-lived
credential for the workflow run via OIDC.

This requires a one-time setup on PyPI under the project's
**Publishing** settings:

| Field | Value |
|---|---|
| Owner | `shanen28` |
| Repository | `license-guard` |
| Workflow | `publish.yml` |
| Environment | `pypi` |

### Building locally

To inspect artifacts without publishing:

```bash
python -m build
python -m twine check dist/*
```

---

## Reporting bugs

Open an issue at [github.com/shanen28/license-guard/issues](https://github.com/shanen28/license-guard/issues) with the exact command, full output, Python version, OS, and a minimal reproducing `requirements.txt`.

---

## License

LicenseGuard is MIT licensed. Contributions are accepted under the same terms.
