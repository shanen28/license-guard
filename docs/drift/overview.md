# Drift Analysis

A package's license can change between releases. Drift analysis compares what you have installed against the latest release on PyPI, so you learn about a license change **before** you upgrade.

---

## Enabling it

```bash
licenseguard scan requirements.txt --cli --check-latest
```

!!! warning "This enables network access"
    Drift analysis is the only feature that makes network calls. Without `--check-latest`, LicenseGuard is entirely offline. Do not enable it in air-gapped or deterministic no-network environments.

---

## What it does

For each resolved package:

1. Read the installed license metadata.
2. Query the PyPI JSON API for the latest release.
3. Normalize both into token sets.
4. Compare the sets and attach drift fields to the row.

If a lookup fails, the scan still succeeds. Affected packages are listed in `warnings`.

---

## Output fields

| Field | Description |
|---|---|
| `version_installed` | Version in your environment |
| `version_latest` | Newest version on PyPI |
| `license_installed` | Normalized license of the installed version |
| `license_latest` | Normalized license of the latest version |
| `license_changed` | Boolean — did the license change at all |
| `change_type` | Classification of the change |

---

## Change types

| Value | Meaning |
|---|---|
| `no_change` | Identical normalized token sets |
| `compatible` | Latest tokens are a subset of installed tokens |
| `compatible_partial` | Partial overlap between the sets |
| `incompatible` | Disjoint sets, or broadening in a risky direction |
| `unknown` | Lookup or metadata problems prevented comparison |

`license_changed` is `true` for `compatible`, `compatible_partial`, and `incompatible`.

---

## Why set comparison

Comparing token **sets** rather than strings produces a far more useful signal.

!!! example "Dual-licensed package changes one alternative"
    Installed: `MIT OR Apache-2.0`
    Latest: `MIT OR GPL-3.0`

    - **String comparison** would say "changed" — technically true, but it does not tell you whether you care.
    - **Set comparison** reports `compatible_partial`: `MIT` is still available to you, but one alternative became materially riskier.

    You can still take the MIT option, so this is not an emergency — but it is worth knowing.

[:octicons-arrow-right-24: How expressions are tokenized](../core-concepts/license-expressions.md)

---

## Caching

PyPI responses are cached in memory for the duration of a scan. An optional disk cache persists across runs:

```bash
licenseguard scan requirements.txt \
  --cli --check-latest \
  --cache-file .licenseguard_cache.json
```

The disk cache is a JSON file, merged across runs. Use `--no-cache` to force fresh lookups and skip cache writes.

!!! tip "Cache in CI"
    Persisting the cache file between pipeline runs reduces latency and API pressure substantially. Add it to your CI cache keyed on your requirements file, and add it to `.gitignore`.

---

## When to use it

**Good fits:**

- Planning a dependency upgrade
- Scheduled governance checks, weekly or daily
- Early warning for metadata changes across releases

**Poor fits:**

- Offline or air-gapped environments
- Builds requiring strict determinism
- Latency-sensitive pre-commit hooks

---

## Related

- [Interpreting drift results](interpreting.md) — what to do with each change type
- [Governance patterns](../policy/governance.md) — scheduling drift checks
