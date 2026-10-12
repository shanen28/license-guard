# Command Examples

Practical recipes for common tasks.

---

## Basic scans

=== "Terminal"

    ```bash
    licenseguard scan requirements.txt --cli
    ```

=== "Dashboard"

    ```bash
    licenseguard scan requirements.txt
    ```

=== "Version check"

    ```bash
    licenseguard --version
    ```

---

## Automation

### JSON only, for parsing

```bash
licenseguard scan requirements.txt --cli --json-only
```

### Pipe into `jq`

```bash
licenseguard scan requirements.txt --cli --json-only \
  | jq '.summary'
```

### List every denied package

```bash
licenseguard scan requirements.txt --cli --json-only \
  | jq -r '.rows[] | select(.status == "DENIED") | "\(.package) \(.version) — \(.license_spdx)"'
```

### Count packages by status

```bash
licenseguard scan requirements.txt --cli --json-only \
  | jq -r '.rows | group_by(.status)[] | "\(.[0].status): \(length)"'
```

### Find packages with no license metadata

```bash
licenseguard scan requirements.txt --cli --json-only \
  | jq -r '.rows[] | select(.unknown_type == "no_metadata") | .package'
```

---

## Policy enforcement

### Apply a policy file

```bash
licenseguard scan requirements.txt --cli --policy policy.yaml
```

### Gate on restricted or worse

```bash
licenseguard scan requirements.txt --cli --policy policy.yaml --fail-on restricted
```

### Strictest gate

```bash
licenseguard scan requirements.txt --cli --fail-on unknown
```

---

## Saving reports

### Write to a file

```bash
licenseguard scan requirements.txt --cli -o licenseguard-report.json
```

### Date-stamped audit trail

```bash
licenseguard scan requirements.txt \
  --cli --json-only \
  -o "reports/licenseguard-$(date +%F).json"
```

### Quiet mode for CI logs

```bash
licenseguard scan requirements.txt \
  --cli --no-table \
  -o report.json \
  --fail-on restricted
```

---

## Drift analysis

### Check for license changes in newer releases

```bash
licenseguard scan requirements.txt --cli --check-latest
```

### With a persistent cache

```bash
licenseguard scan requirements.txt \
  --cli --check-latest \
  --cache-file .licenseguard_cache.json
```

### Force fresh lookups

```bash
licenseguard scan requirements.txt --cli --check-latest --no-cache
```

### Show only packages whose license changed

```bash
licenseguard scan requirements.txt --cli --json-only --check-latest \
  | jq -r '.rows[] | select(.license_changed == true) | "\(.package): \(.license_spdx) → \(.license_latest) [\(.change_type)]"'
```

---

## CI snippets

=== "GitHub Actions"

    ```yaml
    - run: pip install -r requirements.txt licenseguard
    - run: |
        licenseguard scan requirements.txt \
          --cli --json-only \
          --policy policy.yaml \
          --fail-on restricted \
          -o licenseguard-report.json
    - uses: actions/upload-artifact@v4
      if: always()
      with:
        name: licenseguard-report
        path: licenseguard-report.json
    ```

=== "GitLab CI"

    ```yaml
    license-check:
      image: python:3.12
      script:
        - pip install -r requirements.txt licenseguard
        - licenseguard scan requirements.txt --cli --json-only --policy policy.yaml --fail-on restricted -o report.json
      artifacts:
        when: always
        paths:
          - report.json
    ```

=== "Pre-commit hook"

    ```yaml
    - repo: local
      hooks:
        - id: licenseguard
          name: Dependency license check
          entry: licenseguard scan requirements.txt --cli --no-table --fail-on denied
          language: system
          pass_filenames: false
    ```

[:octicons-arrow-right-24: Full CI/CD guide](../ci-cd/integration.md)

---

## Troubleshooting commands

```bash
# Confirm installation
licenseguard --version

# Confirm the environment has your dependencies
pip list

# Run the test suite from a source checkout
pytest -q

# Validate a built distribution before upload
python -m build
python -m twine check dist/*
```

[:octicons-arrow-right-24: Troubleshooting guide](../troubleshooting.md)
