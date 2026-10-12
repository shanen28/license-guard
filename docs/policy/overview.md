# Policy Overview

A policy defines which licenses your organization accepts, accepts conditionally, or refuses.

---

## Two modes of classification

| Mode | When it applies | Behavior |
|---|---|---|
| **Built-in rules** | No `--policy` supplied | Substring pattern matching over common license families |
| **File policy** | `--policy path` supplied | Your explicit lists replace the built-in rules entirely |
| **In-memory policy** | Set in the web dashboard | Applies to subsequent scans in that session only |

!!! tip "Prefer an explicit policy in production"
    Built-in rules are a reasonable default for exploration. For anything you gate a build on, define a policy file: it is explicit, reviewable, and version-controlled.

---

## Minimal policy

```yaml
approved:
  - MIT
  - BSD
  - Apache-2.0
restricted:
  - LGPL
  - MPL
denied:
  - GPL
  - AGPL
```

Apply it:

```bash
licenseguard scan requirements.txt --cli --policy policy.yaml
```

All three keys are optional, but each value must be a list of non-empty strings.

[:octicons-arrow-right-24: Full file format reference](policy-file.md)

---

## How rules are evaluated

For each license token:

1. Check **denied** rules — match ends evaluation.
2. Check **restricted** rules.
3. Check **approved** rules.
4. No match → <span class="status-unknown">UNKNOWN</span>.

Denied-first ordering means the most severe applicable rule always wins.

For compound expressions, this evaluation runs per OR branch, with the least severe branch determining the final status. See [License expressions](../core-concepts/license-expressions.md).

---

## Matching behavior

Rules match a token **exactly** or as a **family prefix**:

```yaml
denied:
  - GPL        # matches GPL, GPL-2.0, GPL-3.0 — but not LGPL-3.0
approved:
  - Apache-2.0 # matches only Apache-2.0
```

Use a bare family name to cover a lineage; use a full identifier when the version matters.

---

## Designing your lists

=== "Approved"

    The licenses you can use without review. Keep this list explicit rather than permissive — an allowlist produces predictable outcomes and makes new licenses visible instead of silently accepted.

    Typical: `MIT`, `BSD-2-Clause`, `BSD-3-Clause`, `Apache-2.0`, `ISC`, `PSF-2.0`

=== "Restricted"

    Licenses you can use but that carry obligations — attribution, source disclosure for modifications, patent terms. These should trigger a human decision, not a build failure by default.

    Typical: `LGPL`, `MPL`, `EPL`, `CDDL`

=== "Denied"

    Licenses incompatible with how you ship. For most commercial, closed-source products this means strong copyleft.

    Typical: `GPL`, `AGPL`, `SSPL`, plus `Proprietary` and `Commercial` for non-redistributable packages

=== "Unknown"

    Not a list you write — it is what remains. Treat a growing unknown count as a signal that your policy needs new entries, not as background noise.

---

## A starting policy

```yaml
# policy.yaml — adjust to your organization's legal guidance
approved:
  - MIT
  - BSD
  - BSD-2-Clause
  - BSD-3-Clause
  - Apache-2.0
  - ISC
  - PSF-2.0
  - Python Software Foundation
  - Unlicense
  - CC0-1.0

restricted:
  - LGPL
  - MPL
  - EPL
  - CDDL
  - MS-PL
  - OSL

denied:
  - GPL
  - AGPL
  - SSPL
  - Proprietary
  - Commercial
  - No Redistribution
```

!!! warning "This is a template, not legal guidance"
    License acceptability depends on how you distribute your software, whether you modify dependencies, and your jurisdiction. Have your actual policy reviewed by someone qualified to make that call.

---

## Related

- [Policy file format](policy-file.md) — schema, JSON equivalent, validation
- [Governance patterns](governance.md) — reviewing and maintaining policy over time
- [Risk classification](../core-concepts/risk-classification.md) — the built-in defaults
