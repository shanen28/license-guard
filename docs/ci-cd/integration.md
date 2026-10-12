# CI/CD Integration

Use LicenseGuard in a pipeline to stop risky dependencies before they reach a protected branch.

---

## The essential pattern

```bash
pip install -r requirements.txt licenseguard
licenseguard scan requirements.txt --cli --policy policy.yaml --fail-on restricted
```

!!! important "Install dependencies first"
    LicenseGuard reports on **installed** packages. If your dependencies are not installed in the same environment, the scan will find nothing and pass vacuously.

    Always install `requirements.txt` before scanning.

---

## Recommended steps

1. Install application dependencies and LicenseGuard into the same environment.
2. Run the scan in `--cli` mode.
3. Fail the build according to your threshold.
4. Upload the JSON report as a build artifact.

---

## GitHub Actions

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
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt licenseguard

      - name: Scan dependency licenses
        run: |
          licenseguard scan requirements.txt \
            --cli --json-only \
            --policy policy.yaml \
            --fail-on restricted \
            -o licenseguard-report.json

      - name: Upload report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: licenseguard-report
          path: licenseguard-report.json
```

!!! tip "`if: always()` matters"
    Without it, the artifact upload is skipped when the scan fails — which is exactly when you most want the report.

---

## GitLab CI

```yaml
license-check:
  image: python:3.12
  stage: test
  script:
    - pip install -r requirements.txt licenseguard
    - |
      licenseguard scan requirements.txt \
        --cli --json-only \
        --policy policy.yaml \
        --fail-on restricted \
        -o licenseguard-report.json
  artifacts:
    when: always
    paths:
      - licenseguard-report.json
    expire_in: 90 days
```

---

## Azure Pipelines

```yaml
steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: "3.12"

  - script: pip install -r requirements.txt licenseguard
    displayName: Install dependencies

  - script: |
      licenseguard scan requirements.txt \
        --cli --json-only \
        --policy policy.yaml \
        --fail-on restricted \
        -o $(Build.ArtifactStagingDirectory)/licenseguard-report.json
    displayName: Scan dependency licenses

  - task: PublishBuildArtifacts@1
    condition: always()
    inputs:
      pathToPublish: $(Build.ArtifactStagingDirectory)
      artifactName: licenseguard-report
```

---

## Pre-commit hook

A fast local gate catching the worst cases before they are committed:

```yaml
repos:
  - repo: local
    hooks:
      - id: licenseguard
        name: Dependency license check
        entry: licenseguard scan requirements.txt --cli --no-table --fail-on denied
        language: system
        pass_filenames: false
```

Keep the local threshold at `denied` and the CI threshold stricter. A pre-commit hook that blocks frequently gets disabled.

---

## Caching for drift mode

If you run `--check-latest` in CI, persist the cache file between runs:

```yaml
- uses: actions/cache@v4
  with:
    path: .licenseguard_cache.json
    key: licenseguard-${{ hashFiles('requirements.txt') }}
```

This cuts latency and reduces load on the PyPI API.

Add `.licenseguard_cache.json` to `.gitignore`.

---

## Policy maintenance in CI

- Keep `policy.yaml` in the repository root for discoverability.
- Require code-owner review for policy changes, so a failing gate cannot be quietly edited away.
- Add a scheduled workflow that runs drift mode weekly.

[:octicons-arrow-right-24: Governance patterns](../policy/governance.md)

---

## Pull request workflow

Suggested configuration:

- Run the scan on every pull request
- Make it a required status check for merge
- Upload the report so reviewers can inspect findings
- Keep a separate scheduled drift job off the PR path

---

## Related

- [Gating strategy](gating.md) — choosing the right threshold
- [Command examples](../cli/examples.md) — more snippets
- [Python API](../api/python-api.md) — custom gating logic
