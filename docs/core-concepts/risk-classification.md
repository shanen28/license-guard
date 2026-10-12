# Risk Classification

Every resolved package receives exactly one of four statuses.

---

## The four statuses

| Status | Meaning |
|---|---|
| <span class="status-approved">APPROVED</span> | Permissive terms; no action required |
| <span class="status-restricted">RESTRICTED</span> | Usable, but carries obligations that need review |
| <span class="status-denied">DENIED</span> | Not acceptable under the active policy |
| <span class="status-unknown">UNKNOWN</span> | License could not be determined or recognized |

---

## Severity ordering

For aggregation, the statuses are ordered by severity:

```text
DENIED  >  RESTRICTED  >  UNKNOWN  >  APPROVED
```

The summary's `worst_status` is the most severe status present across all rows. This ordering also governs conflict resolution within a single license expression.

!!! note "Why UNKNOWN outranks APPROVED"
    An unidentifiable license is a smaller risk than a known-incompatible one, but a larger risk than a known-permissive one. Placing it between RESTRICTED and APPROVED lets `--fail-on unknown` express "everything must be positively identified and approved" without conflating unknowns with outright denials.

---

## Built-in default rules

When no policy file is supplied, LicenseGuard applies substring pattern rules:

=== "Approved"

    ```text
    MIT, BSD, Apache, ISC, PSF, Python Software Foundation,
    Unlicense, CC0, Public Domain, Artistic, Zlib,
    Boost, BSL, WTFPL
    ```

=== "Restricted"

    ```text
    LGPL, MPL, EPL, CPL, CDDL, MS-PL, OSL
    ```

=== "Denied"

    ```text
    GPL, AGPL, Commercial, Proprietary, No Redistribution
    ```

=== "Unknown"

    ```text
    Anything matching none of the above
    ```

!!! warning "GPL matching is deliberately broad"
    The `GPL` pattern is checked for denial before `LGPL` is checked for restriction, and matching is substring-based. The evaluation order ensures `LGPL-3.0` is correctly classified as RESTRICTED rather than swept up by the GPL rule — but if you depend on this distinction, define it explicitly in a policy file rather than relying on built-in ordering.

---

## Evaluation order

Within any given license token, rules are checked in this sequence:

1. **Denied** rules
2. **Restricted** rules
3. **Approved** rules
4. Fall through to **UNKNOWN**

Denied-first means the most severe applicable rule wins, which is the safe default for a compliance tool.

---

## Policy files override everything

Supplying `--policy` replaces the built-in rules entirely. Your approved, restricted, and denied lists become the only rules applied.

```bash
licenseguard scan requirements.txt --cli --policy policy.yaml
```

This is the recommended production configuration: explicit rules produce predictable, reviewable outcomes, and the policy file itself becomes a version-controlled artifact.

[:octicons-arrow-right-24: Policy file format](../policy/policy-file.md)

---

## Family prefix matching

Policy rules match either exactly or as a family prefix. A rule of `GPL` matches the token `GPL-3.0`, because the token begins with `GPL-`.

| Rule | Matches | Does not match |
|---|---|---|
| `GPL` | `GPL`, `GPL-2.0`, `GPL-3.0` | `LGPL-3.0` |
| `BSD` | `BSD`, `BSD-2-Clause`, `BSD-3-Clause` | `0BSD` |
| `Apache-2.0` | `Apache-2.0` | `Apache-1.1` |

Write broad family rules when you want to cover a whole license lineage, and exact rules when version matters.

---

## The reason field

Every row explains its own classification:

```json
{
  "status": "DENIED",
  "reason": "Matched denied rule: GPL"
}
```

Reasons also carry non-blocking advisories, most commonly the unpinned-dependency note:

```json
{
  "status": "APPROVED",
  "reason": "Matched approved rule: MIT; Unpinned dependency — license may change on upgrade"
}
```

An unpinned direct dependency is any requirement not fixed with `==` or `===`. It does not change the status — it flags that the status could change the next time the environment is built.

---

## Related

- [License expressions](license-expressions.md) — compound `OR` / `AND` licenses
- [Policy overview](../policy/overview.md) — writing your own rules
- [Gating strategy](../ci-cd/gating.md) — choosing a CI threshold
