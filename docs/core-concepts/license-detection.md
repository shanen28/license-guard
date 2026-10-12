# License Detection

Python packaging has no single authoritative license field. LicenseGuard reads several sources in priority order and normalizes whatever it finds.

---

## Metadata sources, in priority order

| Priority | Source | Notes |
|---|---|---|
| 1 | `License-Expression` | Modern PEP 639 field. Already an SPDX expression — used as-is. |
| 2 | `License` | Free-text field. Ranges from `MIT` to an entire license document. |
| 3 | `Classifier: License :: ...` | Trove classifiers. Mapped from their label text. |

The first source that yields usable content wins. If none do, the package is classified <span class="status-unknown">UNKNOWN</span> with `unknown_type: no_metadata`.

---

## Normalization

Raw metadata is messy. These all describe the same license:

```text
MIT
MIT License
The MIT License
MIT License (MIT)
License :: OSI Approved :: MIT License
```

LicenseGuard maps roughly forty phrase variations onto SPDX-style identifiers, covering the common families:

| Family | Normalized examples |
|---|---|
| Permissive | `MIT`, `ISC`, `BSD-2-Clause`, `BSD-3-Clause`, `Apache-2.0` |
| Weak copyleft | `LGPL-2.1`, `LGPL-3.0`, `MPL-2.0` |
| Strong copyleft | `GPL-2.0`, `GPL-3.0`, `AGPL-3.0` |
| Public-domain-like | `Unlicense`, `CC0-1.0` |
| Other | `PSF-2.0`, `Artistic-2.0`, `Zlib`, `BSL-1.0`, `WTFPL` |

Matching is case- and punctuation-tolerant, so `apache software license, version 2.0` and `Apache-2.0` converge on the same identifier.

---

## Handling full license text

Some packages place an entire license document in the `License` field. When the metadata exceeds roughly 200 characters, LicenseGuard switches to a keyword-based heuristic, scanning for distinctive phrases that identify the license family.

!!! warning "Best effort, not certainty"
    Guessing from a license blob is inherently approximate. When this path produces a result you intend to rely on, confirm it against the package's actual `LICENSE` file.

If the heuristic finds nothing recognizable, the package becomes <span class="status-unknown">UNKNOWN</span> with `unknown_type: unrecognized`.

---

## The two kinds of unknown

The `unknown_type` field distinguishes two very different situations:

| Value | Meaning | Typical remediation |
|---|---|---|
| `no_metadata` | No license information in the package at all | Check the project's repository; the package may be genuinely unlicensed |
| `unrecognized` | Metadata exists but normalization failed | Read `license_detected`, then add a policy rule for it |

An `unrecognized` result is usually quick to resolve — you can see the raw string and decide how to classify it. A `no_metadata` result is a genuine gap in the package's publishing.

---

## Output fields

Each row carries both the raw and normalized values:

```json
{
  "package": "requests",
  "version": "2.32.3",
  "license_detected": "Apache 2.0",
  "license_spdx": "Apache-2.0",
  "status": "APPROVED",
  "reason": "Matched approved rule: Apache"
}
```

Keeping `license_detected` alongside `license_spdx` means normalization is always auditable — you can see exactly what the package claimed and what LicenseGuard made of it.

---

## Improving coverage

If packages in your tree normalize poorly:

1. Read `license_detected` for the affected rows.
2. Add the raw string, or a prefix of it, to your [policy file](../policy/policy-file.md).
3. Policy rules match tokens directly, so an unnormalized string can still be classified explicitly.

---

## Related

- [Risk classification](risk-classification.md) — how a normalized license becomes a status
- [License expressions](license-expressions.md) — handling `OR` and `AND`
