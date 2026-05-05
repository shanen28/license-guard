---
layout: default
title: CI/CD Integration
prev_url: /architecture.html
prev_title: Architecture and Internals
next_url: /troubleshooting.html
next_title: Troubleshooting
---

# CI/CD Integration

Use LicenseGuard in pipelines to prevent risky dependencies from entering protected branches.

## Basic pipeline pattern

```yaml
- run: pip install -r requirements.txt .
- run: licenseguard scan requirements.txt --cli --policy policy.yaml --fail-on restricted
```

## Recommended steps

1. Install app dependencies and LicenseGuard in same environment
2. Run scan in CLI mode
3. Fail build based on selected threshold
4. Store JSON report as CI artifact

## Reference GitHub Actions workflow

```yaml
name: dependency-license-check
on:
  pull_request:
  push:
    branches: [main]

jobs:
  licenseguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt .
      - run: licenseguard scan requirements.txt --cli --json-only -o licenseguard-report.json --fail-on restricted
      - uses: actions/upload-artifact@v4
        with:
          name: licenseguard-report
          path: licenseguard-report.json
```

## JSON artifact example

```bash
licenseguard scan requirements.txt --cli --json-only -o artifacts/licenseguard-report.json
```

## Choosing failure threshold

- `denied` -> least strict
- `restricted` -> common governance baseline
- `unknown` -> strictest safety posture

## Caching in CI for drift mode

If using `--check-latest`, provide `--cache-file` and persist it between jobs to reduce API usage and improve speed.

## Pull request workflows

Suggested checks:

- Run scan on every PR
- Comment summary counts in PR checks
- Block merge on policy threshold violation

## Policy maintenance in CI

- Keep policy file in repository root (for discoverability)
- Require code-owner review for policy changes
- Add a scheduled workflow to run drift mode weekly
