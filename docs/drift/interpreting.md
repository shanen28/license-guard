# Interpreting Drift Results

A drift finding is a prompt to look, not a verdict.

!!! warning "Metadata is not the license"
    Drift analysis compares **published metadata**, which is not the same as the legal terms. A metadata correction can look like a license change, and a genuine relicensing can appear as metadata noise. Always confirm against the package's changelog and `LICENSE` file before acting.

---

## Response by change type

=== "no_change"

    Nothing to do. Normalized token sets match.

=== "compatible"

    The latest release's licenses are a subset of what you already have. Generally safe, but confirm that the surviving license still satisfies your policy.

    **Action:** proceed with the upgrade; note the narrowing.

=== "compatible_partial"

    Partial overlap. At least one license you relied on is still available, but the set changed.

    **Action:** medium priority. Identify which alternative you depend on and confirm it survived.

=== "incompatible"

    Disjoint sets, or a change in a risky direction.

    **Action:** review before upgrading. Read the changelog, check the repository, and confirm the new terms against your policy.

=== "unknown"

    Comparison failed — a network error, missing metadata, or an unparseable expression.

    **Action:** check `warnings`. Often transient; re-run before investigating.

---

## A triage workflow

1. **Filter to changes.**

    ```bash
    licenseguard scan requirements.txt --cli --json-only --check-latest \
      | jq -r '.rows[] | select(.license_changed == true)
               | "\(.package): \(.license_installed) → \(.license_latest) [\(.change_type)]"'
    ```

2. **Sort by severity.** Handle `incompatible` first, then `compatible_partial`.

3. **Verify at the source.** Open the package's repository and read the changelog entry for the version in question. Metadata alone is not sufficient evidence.

4. **Decide and record.** Pin to the last acceptable version, replace the dependency, or accept the change — and write down which, and why.

5. **Update policy if needed.** If the new license is acceptable, add it to the policy explicitly rather than leaving it to be rediscovered later.

---

## False positives to expect

Several common situations produce a change signal without a real relicensing:

| Situation | What happened |
|---|---|
| Metadata modernization | A project moved from the `License` field to PEP 639 `License-Expression`, changing the string but not the terms |
| Classifier cleanup | Trove classifiers were corrected, added, or removed |
| Normalization difference | Free text in one release and a clean SPDX identifier in another |
| Dual-license clarification | Terms that were always dual were finally stated explicitly |

This is why `incompatible` is a review trigger rather than a build failure. A tool reading metadata cannot distinguish a correction from a change in terms.

---

## Scheduled checks

Per-pull-request scans catch licenses you introduce. They do not catch a license that changed in a dependency you already have. A scheduled run covers that:

```yaml
name: license-drift
on:
  schedule:
    - cron: "0 6 * * 1"   # Mondays, 06:00 UTC
  workflow_dispatch:

jobs:
  drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt licenseguard
      - run: |
          licenseguard scan requirements.txt \
            --cli --json-only --check-latest \
            --cache-file .licenseguard_cache.json \
            -o drift-report.json
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: drift-report
          path: drift-report.json
```

!!! tip "Route it to the right person"
    Send drift failures to whoever owns dependency upgrades, not to the author of whatever pull request happens to be open. Drift is about the existing tree, not about the change under review.

---

## What drift cannot tell you

- Whether a license change affects **your** distribution model
- Whether terms changed without metadata changing
- Anything about packages not published on PyPI
- The legal implications of any change

It narrows a large dependency tree down to the handful of packages worth a human look. That is the whole of its job.

---

## Related

- [Drift analysis](overview.md) — enabling and configuring
- [License expressions](../core-concepts/license-expressions.md) — how tokens are compared
- [Governance patterns](../policy/governance.md) — building review into a routine
