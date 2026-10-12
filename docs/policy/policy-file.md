# Policy File Format

Policies are plain YAML or JSON. The format is intentionally small.

---

## Schema

| Key | Type | Required | Meaning |
|---|---|---|---|
| `approved` | list of strings | No | Licenses accepted without review |
| `restricted` | list of strings | No | Licenses requiring review |
| `denied` | list of strings | No | Licenses not accepted |

All keys are optional. Each present key must be a list of non-empty strings. Any token matching no rule becomes <span class="status-unknown">UNKNOWN</span>.

---

## YAML

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

## JSON

```json
{
  "approved": ["MIT", "BSD", "Apache-2.0"],
  "restricted": ["LGPL", "MPL"],
  "denied": ["GPL", "AGPL"]
}
```

Both are equivalent. Format is detected from the file contents, so either extension works.

---

## Loading a policy

=== "CLI"

    ```bash
    licenseguard scan requirements.txt --cli --policy policy.yaml
    ```

=== "Python"

    ```python
    from pathlib import Path
    from licenseguard import load_policy_file, scan_requirements_file

    policy = load_policy_file(Path("policy.yaml"))
    result = scan_requirements_file(Path("requirements.txt"), policy=policy)
    ```

=== "Dashboard"

    Enter comma-separated tokens in the Policy section and click **Apply policy**. This sets an in-memory policy for subsequent scans in that session — it does not write to disk.

---

## Validation

A policy file is rejected if:

- the file is not valid YAML or JSON
- a key's value is not a list
- a list contains empty strings or non-string values

```text
error: invalid policy file
```

??? failure "Common validation mistakes"

    **A string instead of a list**

    ```yaml
    approved: MIT          # wrong — must be a list
    approved:
      - MIT                # correct
    ```

    **An empty entry**

    ```yaml
    denied:
      - GPL
      -                    # wrong — empty value
    ```

    **Non-string values**

    ```yaml
    approved:
      - MIT
      - 2.0                # wrong — parsed as a number
      - "2.0"              # correct if you really mean the string
    ```

---

## Matching rules

Tokens match exactly, or as a family prefix where the token begins with `RULE-`.

| Rule | Matches | Does not match |
|---|---|---|
| `MIT` | `MIT` | `MIT-0` is matched (prefix `MIT-`) |
| `GPL` | `GPL`, `GPL-2.0`, `GPL-3.0` | `LGPL-3.0`, `AGPL-3.0` |
| `BSD` | `BSD`, `BSD-3-Clause` | `0BSD` |
| `Apache-2.0` | `Apache-2.0` | `Apache-1.1` |

!!! note "LGPL and AGPL are separate families"
    Because matching is anchored at the start of the token, a `GPL` rule does **not** catch `LGPL-3.0` or `AGPL-3.0`. List those explicitly if you intend to cover them:

    ```yaml
    denied:
      - GPL
      - AGPL
    restricted:
      - LGPL
    ```

---

## Matching unnormalized licenses

Policy rules match the normalized token, but if normalization failed you can still classify a package by its raw string. Read `license_detected` from an `unrecognized` row and add a rule for it:

```yaml
approved:
  - Some Unusual License 1.0
```

This gives you an escape hatch for packages whose metadata LicenseGuard cannot interpret.

---

## Where to keep the file

Keep `policy.yaml` in the repository root. It is discoverable there, it version-controls alongside the code it governs, and CI can reference it by a stable relative path.

```bash
licenseguard scan requirements.txt --cli --policy policy.yaml --fail-on restricted
```

!!! tip "Use absolute paths in CI"
    When a pipeline runs from a different working directory, a relative policy path will not resolve. Use `$GITHUB_WORKSPACE/policy.yaml` or the equivalent for your CI system.

---

## Related

- [Policy overview](overview.md) — designing your lists
- [Governance patterns](governance.md) — maintaining the policy over time
