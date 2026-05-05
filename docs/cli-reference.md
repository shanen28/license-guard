---
layout: default
title: CLI Reference
prev_url: /getting-started.html
prev_title: Getting Started
next_url: /web-dashboard.html
next_title: Web Dashboard Guide
---

# CLI Reference

## Command structure

```bash
licenseguard scan <requirements_file> [options]
```

## Global command

```bash
licenseguard --version
```

Prints the installed LicenseGuard version and exits.

## Core options

- `--cli` - print results in terminal instead of launching web UI
- `--policy <path>` - use YAML/JSON policy file
- `--json-only` - print JSON only (warnings still go to stderr)
- `--no-table` - skip table output but still print JSON
- `-o, --output-json <path>` - save JSON report to file
- `--fail-on {denied|restricted|unknown}` - control failure threshold

## Output modes

### Default CLI output (`--cli`)

By default, CLI mode prints:

1. A fixed-width dependency table
2. A summary block with status totals
3. Full JSON payload

Warnings are written to stderr.

### `--json-only`

- Emits only JSON to stdout
- Keeps warnings in stderr for automation visibility
- Best mode for machine parsing

### `--no-table`

- Skips human-readable table
- Still prints JSON payload

## Drift options (optional network mode)

- `--check-latest` - compare installed license metadata with latest release on PyPI
- `--cache-file <path>` - read/write PyPI metadata cache
- `--no-cache` - bypass cache for fresh network lookups

Use drift mode only when network access is available and you want upgrade-risk signals.

## Exit behavior

Default non-zero exit happens when worst status is `DENIED` or `RESTRICTED`.

- `--fail-on denied` -> fail only if denied exists
- `--fail-on restricted` -> fail on denied or restricted
- `--fail-on unknown` -> fail unless all results are approved

## Input parsing notes

- `requirements.txt` comments and blank lines are ignored
- Includes from `-r`/`--requirement` are not followed by the resolver parser
- URLs/VCS entries may be unparseable for root extraction and can emit warnings
- Package scanning still proceeds for all parseable roots

## Key JSON fields

Top-level:

- `requirements_file`
- `rows`
- `summary`
- `warnings`
- `check_latest` (present only when enabled)

Row-level:

- `package`, `version`, `direct`, `installed`
- `license_detected`, `license_spdx`, `status`, `reason`, `unknown_type`
- drift fields when enabled: `version_latest`, `license_latest`, `license_changed`, `change_type`

## Examples

### Basic scan

```bash
licenseguard scan requirements.txt --cli
```

### JSON-only for automation

```bash
licenseguard scan requirements.txt --cli --json-only
```

### Policy enforcement

```bash
licenseguard scan requirements.txt --cli --policy policy.yaml --fail-on restricted
```

### Save report

```bash
licenseguard scan requirements.txt --cli -o licenseguard-report.json
```

### Drift analysis

```bash
licenseguard scan requirements.txt --cli --check-latest --cache-file .licenseguard_cache.json
```

### Strict gate in CI

```bash
licenseguard scan requirements.txt --cli --json-only --fail-on unknown
```

### Save JSON for audit trail

```bash
licenseguard scan requirements.txt --cli --json-only -o reports/licenseguard-$(date +%F).json
```
