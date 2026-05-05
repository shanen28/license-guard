# CLI Reference

## Command structure

```bash
licenseguard scan <requirements_file> [options]
```

## Core options

- `--cli` - print results in terminal instead of launching web UI
- `--policy <path>` - use YAML/JSON policy file
- `--json-only` - print JSON only (warnings still go to stderr)
- `--no-table` - skip table output but still print JSON
- `-o, --output-json <path>` - save JSON report to file
- `--fail-on {denied|restricted|unknown}` - control failure threshold

## Drift options (optional network mode)

- `--check-latest` - compare installed license metadata with latest release on PyPI
- `--cache-file <path>` - read/write PyPI metadata cache
- `--no-cache` - bypass cache for fresh network lookups

## Exit behavior

Default non-zero exit happens when worst status is `DENIED` or `RESTRICTED`.

- `--fail-on denied` -> fail only if denied exists
- `--fail-on restricted` -> fail on denied or restricted
- `--fail-on unknown` -> fail unless all results are approved

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
