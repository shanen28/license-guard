# Governance Patterns

A policy file is only useful if it stays accurate. These are patterns for keeping it that way.

---

## Treat policy as code

The policy file governs what your organization is allowed to ship. Give it the same controls as the code it protects.

- **Version-control it** alongside the project
- **Require review** for changes — a code-owner rule on `policy.yaml` is a reasonable minimum
- **Record rationale** in the commit message, not just the diff
- **Never edit it to make a build pass** without that review

!!! warning "The failure mode to avoid"
    A denied package blocks a release. Under time pressure, someone moves it to `approved` and merges. The gate now passes and nobody revisits it.

    Requiring review on the policy file is what prevents this from becoming routine.

---

## Start strict, loosen deliberately

Begin with an explicit `approved` allowlist. Everything unlisted surfaces as <span class="status-unknown">UNKNOWN</span>, which is noisy at first but shows you exactly what your dependency tree actually contains.

Then add entries deliberately, each with a reason. The alternative — starting permissive and denying as problems appear — means you never learn what is already in the tree.

---

## Choosing a CI threshold

| Threshold | Fails on | Use when |
|---|---|---|
| `--fail-on denied` | DENIED only | Adopting the tool; minimizing disruption |
| `--fail-on restricted` | DENIED, RESTRICTED | Common governance baseline |
| `--fail-on unknown` | Anything not APPROVED | High-assurance; everything must be identified |

A practical adoption path: start at `denied`, resolve the backlog, move to `restricted`, and reserve `unknown` for projects where complete license provenance is a requirement.

[:octicons-arrow-right-24: Gating strategy in detail](../ci-cd/gating.md)

---

## Review cadence

The package landscape changes. Licenses change. A policy written once and never revisited slowly stops describing reality.

| Cadence | Activity |
|---|---|
| **Per pull request** | Automated scan with the current gate |
| **Weekly** | Scheduled [drift check](../drift/overview.md) against latest PyPI releases |
| **Quarterly** | Human review of the policy itself — are the lists still right? |
| **On legal change** | Re-review when distribution model or jurisdiction changes |

---

## Triaging the restricted queue

`RESTRICTED` means "a human must decide," which only works if someone actually decides. Give the queue an owner and a rhythm.

For each restricted package, record:

1. Why the dependency is needed
2. What obligations the license imposes
3. Whether those obligations are satisfied by how you ship
4. Who approved the decision, and when

Storing that record next to the policy file turns a recurring debate into a one-time decision.

---

## Keep evidence

Persist the JSON report from every CI run:

```bash
licenseguard scan requirements.txt \
  --cli --json-only \
  -o "reports/licenseguard-$(date +%F).json"
```

This gives you:

- **Auditability** — what the tree looked like at any past release
- **Trend analysis** — whether unknowns are growing
- **Change attribution** — which commit introduced a new license

Upload it as a CI artifact so it survives the build.

[:octicons-arrow-right-24: Artifact storage in CI](../ci-cd/integration.md)

---

## Scheduled drift checks

Per-PR scans catch what you add. They do not catch a license that changed in a package you already depend on. A scheduled drift run covers that gap:

```yaml
on:
  schedule:
    - cron: "0 6 * * 1"   # Mondays, 06:00 UTC
```

```bash
licenseguard scan requirements.txt \
  --cli --check-latest \
  --cache-file .licenseguard_cache.json
```

Route failures to whoever owns dependency upgrades rather than to the author of an unrelated pull request.

---

## Pin your direct dependencies

LicenseGuard flags unpinned direct dependencies with a note on the row. The flag exists because an unpinned requirement can resolve to a different version — and a different license — on the next build.

Pinning with `==` makes your license report reproducible. Combine it with a managed upgrade process so pins stay current.

---

## Related

- [Policy file format](policy-file.md) — the schema
- [Gating strategy](../ci-cd/gating.md) — threshold selection
- [Drift analysis](../drift/overview.md) — catching changes in existing dependencies
