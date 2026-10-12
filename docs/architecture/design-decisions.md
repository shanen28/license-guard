# Design Decisions

The reasoning behind LicenseGuard's less obvious choices, and what each one costs.

---

## Installed-only resolution

**Decision:** resolve the dependency graph from `importlib.metadata`, not from a lockfile or PyPI metadata.

**Why:** most scanners report on an *intended* dependency set. That set routinely diverges from reality — stale requirements entries, unselected extras, platform-gated dependencies, transitives of packages never installed. Reading the installed environment reports on what actually ships.

**Cost:** the environment must be complete before scanning. A partially installed environment yields a partial report, and LicenseGuard cannot evaluate a package you have not installed. In CI this means dependency installation is a hard prerequisite, not an optimization.

**Mitigation:** [drift analysis](../drift/overview.md) covers the "what would happen if I upgraded" case without requiring installation.

---

## Severity ordering places UNKNOWN above APPROVED

**Decision:** order statuses `DENIED > RESTRICTED > UNKNOWN > APPROVED`.

**Why:** an unidentifiable license is less dangerous than a known-incompatible one, but more dangerous than a known-permissive one. Slotting UNKNOWN between RESTRICTED and APPROVED lets `--fail-on unknown` express "everything must be positively identified" as a distinct, stricter posture than "nothing may be restricted."

**Cost:** the ordering is not intuitive at first glance — one might expect unknowns to be either the most or least severe. It is documented precisely because it is a judgment call.

---

## OR/AND set semantics rather than string matching

**Decision:** tokenize license expressions into sets and evaluate OR branches independently.

**Why:** substring matching on a compound expression produces wrong answers. `MIT OR GPL-3.0` contains the substring `GPL`, so a naive matcher denies a package that is freely available under MIT. Evaluating branches as genuine alternatives fixes this.

The same tokenization makes drift comparison meaningful: `MIT OR Apache-2.0` → `MIT OR GPL-3.0` is `compatible_partial`, not an undifferentiated "changed."

**Cost:** more complex than string equality, and it adds a normalization dependency — two expressions must normalize consistently to compare correctly.

[:octicons-arrow-right-24: Expression evaluation](../core-concepts/license-expressions.md)

---

## Framework-free frontend

**Decision:** the dashboard is one HTML string in `webapp.py` with vanilla JavaScript and a canvas-drawn chart.

**Why:** LicenseGuard is a locally launched, single-user tool. A framework would add a build step, a bundler, a `node_modules` tree, and a packaging problem — in exchange for conveniences that a page with one table and one chart does not need. Keeping it inline means `pip install licenseguard` is the entire setup.

**Cost:** the UI code is harder to maintain than a component tree would be, and a large embedded string is awkward to edit. The tradeoff holds only while the dashboard stays simple; a substantially richer UI would justify revisiting it.

---

## The dashboard is the default mode

**Decision:** `licenseguard scan` launches the web UI; `--cli` opts into terminal output.

**Why:** the dashboard is the better experience for the exploratory first use — filtering, sorting, and the distribution chart beat a wall of text when you are trying to understand an unfamiliar dependency tree.

**Cost:** it surprises users who expect a CLI tool to behave like one, and it makes the automation path the longer one to type. CLI-only flags are ignored with a warning when `--cli` is absent, which is a usability patch over the underlying tension.

!!! note "A defensible choice, not an obvious one"
    Reasonable people disagree here. The alternative — terminal by default, `--web` to opt in — would favor the automation case over the exploration case.

---

## Manual scan trigger in the dashboard

**Decision:** the dashboard does not scan on page load.

**Why:** opening a page should not trigger work. Explicit invocation keeps behavior predictable, especially once drift mode is enabled and a scan means network calls.

**Cost:** an extra click, and an empty state that occasionally reads as a bug.

---

## Offline by default

**Decision:** no network calls unless `--check-latest` is passed.

**Why:** compliance tooling runs in restricted environments. A scanner that silently reaches the network is unusable in air-gapped CI and unpredictable when PyPI is slow. Making network access opt-in keeps the default path deterministic and fast.

**Cost:** drift detection — arguably the most differentiated feature — is off unless you know to enable it.

---

## Warnings are non-blocking

**Decision:** unparseable requirement lines and failed drift lookups emit warnings; the scan continues.

**Why:** real requirements files contain VCS URLs, local paths, and unusual syntax. Aborting on the first unparseable line would make the tool unusable on exactly the complex projects that most need it.

**Cost:** warnings can be overlooked, and a scan that silently skipped half its input still reports success. The `warnings` array exists to be read, including in CI.

---

## Version kept in sync manually

**Decision:** the version appears in both `pyproject.toml` and `licenseguard/__init__.py`, with comments in both pointing at the other.

**Why:** avoids a build-time dependency on dynamic version resolution for a project this small.

**Cost:** it can drift. A single-sourced version via `importlib.metadata` would remove the hazard, and is a reasonable future change.

---

## Related

- [Architecture overview](overview.md) — module structure and data flow
- [Installed-only resolution](../core-concepts/installed-only.md)
- [Contributing](../contributing.md)
