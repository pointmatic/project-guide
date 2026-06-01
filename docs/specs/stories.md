# stories.md -- project-guide (python)

This document breaks the `project-guide` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Put **`vX.Y.Z` in the story title only when that story ships the package version bump** for that release. Doc-only or polish stories **omit the version from the title** (they share the release with the preceding code story, or use your project’s doc-release policy). **One semver bump per owning story** — extra tasks on the *same* story share that bump; see `project-essentials.md`. Semantic versioning applies to the package. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

For a high-level concept (why), see [`concept.md`](concept.md). For requirements and behavior (what), see [`features.md`](features.md). For implementation details (how), see [`tech-spec.md`](tech-spec.md). For project-specific must-know facts, see [`project-essentials.md`](project-essentials.md) (`plan_phase` appends new facts per phase). For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

---

## Version Cadence

Standard semantic versioning, with these conventions:

- **Every story belongs to a phase.** Bugfix stories included. No orphan stories.
- **Per-story bumping** (when a story owns its own release):
  - Bugfix or trivial change → **patch** (`vX.Y.Z+1`)
  - Feature or improvement → **minor** (`vX.Y+1.0`)
  - Breaking change → **major** (`vX+1.0.0`). Post-1.0 only, and only via the `plan_production_phase` mode, which negotiates with the developer about whether the breakage is substantively user-facing or technically-but-trivially breaking (example: a log-format change is technically breaking, but if logs aren't a core consumer capability, the developer may judge it minor or even patch).
- **Phase-bundling option:** a phase can run unversioned during work and ship a single release/tag at end-of-phase. Stories within the phase carry no version in their title; the phase's last story owns the bump (magnitude determined by the highest-impact change in the bundle).
- **No out-of-order implementation.** Story order in this file is the order of execution. If work order needs to change, **reorganize/renumber here first** — don't skip ahead and create version-number gaps.
- **Pre-1.0:** standard semver applies; version starts at `v0.1.0` (Story A.a).
- **Post-1.0:** every phase must go through `plan_production_phase` (the lighter `plan_phase` is pre-1.0 only). Major bumps only happen through that mode's negotiation step.

This is the authoritative cadence rule. **Do not extrapolate the bump magnitude from `pyproject.toml`'s current version** — re-read this section whenever you're about to assign a version to a story.

---



## Phase Q: DX Improvements & Subphase Support

Open-ended developer-experience phase. Two distinguishing characteristics:

1. **First phase decomposed into subphases up front.** The subphase pattern itself is introduced by Subphase Q-1 (self-applying — the templates that document subphasing are first written using it). See [`phase-q-dx-subphases-plan.md`](phase-q-dx-subphases-plan.md) for the planning artifact.
2. **Ad-hoc subphases will accumulate as DX needs surface.** Only Subphase Q-1 is scoped today; Q-2, Q-3, … are placeholders, each to be drafted via its own future `plan_production_phase` session per the (Q-1-installed) Step 4a pattern.

**Story-ID continuation across subphases.** Story letters run monotonically across subphase boundaries — if Subphase Q-1 ends at `Q.c`, Subphase Q-2 starts at `Q.d`. Sub-letters reset only at the phase boundary, never at a subphase boundary.

**Multi-release exception.** Each subphase decides its own release shape (bundled per the Version Cadence phase-bundling option, extended per-subphase by the Q-1-installed pattern, or one-off versioned stories). Subphase Q-1 ships as one bundled release: **v2.11.0**.

## Subphase Q-1: Subphase Strategy & Pyve v2.8.0 Alignment

Bundled release at end-of-subphase as **v2.11.0** (minor, fully additive). Three stories, executed in document order; only `Q.c` carries the version in its title.

### Story Q.a: Subphase strategy pattern — template installation [Planned]

**Problem.** When a phase is too large to draft every story up front, the current `plan_phase` / `plan_production_phase` templates offer no idiomatic decomposition. Field experience drafting Pyve's Phase N (2026-06-01) surfaced the gap: the developer had to manually bootload subphase IDs (`N-1` form), heading level (`##`), monotonic story-letter continuation, multi-release exception, deferred-story breakdown, and the 3-level depth cap into every relevant LLM session. Pattern drift across sessions is guaranteed. The proposed pattern lives in [`docs/specs/subphase-strategy-for-large-phases.md`](subphase-strategy-for-large-phases.md).

**Behavior (post-story).** Four template edits land together so the pattern is self-consistent from the moment it appears:

- **`plan-production-phase-mode.md` Step 4a** — new "Subphase decomposition (optional)" step inserted between current Step 4 (Generate a phase plan document) and Step 5 (Breaking-change negotiation). Lists trigger heuristics, describes the Subphase-overview output, states that Subphase 1 is the only one with stories drafted up front, names re-entering `plan_production_phase` mid-phase as the canonical pattern (not a misuse), and explicitly allows skipping when the phase is small/medium.
- **`_phase-letters.md` new "Subphases" section** — between "Story sub-letters" and "Sub-numbered stories". Subphase IDs use arabic numerals with hyphen separator (`N-1`, `N-2`, …, `N-9`, `N-10`); subphase headings use `##`; story letters continue monotonically; story breakdown is per-subphase; the 3-level story-ID depth limit holds. Cross-reference back to `plan_production_phase` Step 4a.
- **`_header-common.md` scope-of-authority clarification** — one sentence appended to the existing "Scope of authority — structural changes to `stories.md`" rule: subphase headings (`## Subphase X-N:`) under an existing `## Phase X:` heading are structural sub-groupings, not new phases, and may be added by subsequent `plan_production_phase` invocations under the same phase's authority. Closes the loophole where an LLM drafting a Q-2 subphase mid-phase would otherwise read the rule as forbidding the new `##` heading.
- **`plan-phase-mode.md` pre-1.0 parenthetical** — one sentence in Step 4 noting that subphasing is available pre-1.0 too but rarely needed; default is to draft every story in one session; points at `plan_production_phase` Step 4a for the canonical pattern.

**Why these defaults.**

- **All four edits in one story.** The four files implement one coherent rule. Splitting them across stories would let half the rule land in a release without the other half, breaking self-consistency. The change request itself ([`subphase-strategy-for-large-phases.md`](subphase-strategy-for-large-phases.md)) treats them as one unit.
- **Step 4a placement (between current Step 4 and Step 5).** Subphase decomposition is a planning-shape decision; it must happen *after* the phase plan exists (Step 4) so the gap-analysis-row / breaking-change-count heuristics are computable, but *before* breaking-change negotiation (Step 5) and stories-file mutation (Step 7), so a decomposed phase's per-subphase release-target is in hand before the version-bump suggestion is made.
- **Subphase IDs use `N-1` hyphen form.** Three competing forms were considered: dotted (`N.1`), colon (`N:1`), hyphen (`N-1`). Dotted collides with sub-numbered stories (`N.m.1`); colon is parser-hostile in some markdown renderers. Hyphen is parser-safe across markdown, grep, and downstream tooling, and the visual distinction from story IDs (`N.a`) makes it unambiguous which axis the LLM is operating on.
- **`_header-common.md` clarification rather than rewrite.** The scope-of-authority rule is load-bearing for `code_direct` / `code_test_first` discipline (it's what stops mid-implementation LLMs from inventing new phases). The minimum edit that opens the subphase door without weakening the phase-creation gate is one clarifying sentence. A larger rewrite would create review surface area for diminishing rule clarity.

**Implementation:**
- [ ] Edit `project_guide/templates/project-guide/templates/modes/plan-production-phase-mode.md` — insert Step 4a between current Step 4 (Generate a phase plan document) and Step 5 (Breaking-change negotiation). Update Step 7 (Add a new phase section and stories to `stories.md`) with a sentence referencing the subphase layout when Step 4a opted in.
- [ ] Edit `project_guide/templates/project-guide/templates/modes/_phase-letters.md` — add new "Subphases (structural grouping within a phase)" section after "Story sub-letters" / before "Sub-numbered stories".
- [ ] Edit `project_guide/templates/project-guide/templates/modes/_header-common.md` — append one sentence to the "Scope of authority — structural changes to `stories.md`" rule clarifying that subphase headings under an existing `## Phase X:` are allowed under the same authority.
- [ ] Edit `project_guide/templates/project-guide/templates/modes/plan-phase-mode.md` — append one parenthetical sentence to Step 4 noting subphasing is available pre-1.0 but rarely needed; cross-reference `plan_production_phase` Step 4a.
- [ ] Run `pyve run project-guide update` to propagate template edits to `docs/project-guide/` (the dogfooded installed copy).
- [ ] Run `pyve test` — every mode template must still render without errors (parametrized regression guard in `tests/test_render.py`).
- [ ] Run `pyve testenv run ruff check project_guide/ tests/` — clean.
- [ ] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Programmatic enforcement of the subphase pattern.** No `project-guide subphase add Q-2` command — the pattern is LLM-readable template guidance. YAGNI until field use shows the rule alone is insufficient.
- **Retroactively re-decomposing archived phase plans.** No archived phase or its plan doc is being rewritten. Phase N (Pyve's worked example) stays as drafted in its own repo.
- **Cross-link to a future Pyve Phase N worked example** in the template body. Deferred until Pyve's Phase N artifacts ship and their paths are stable.
- **Tests for the template content.** Templates are rendered verbatim through Jinja; no logic to test. The existing render-pipeline regression guard already verifies file inclusion.
- **`plan-stories-mode.md` / `refactor-plan-mode.md` edits.** Per the change request's "Suggested template changes" section, neither template needs subphase awareness: `plan_stories` is for *initial* story planning of a project with no prior story plan; `refactor_plan` does not create phases.

---

### Story Q.b: Pyve v2.8.0 alignment — pyve-essentials.md refresh [Planned]

**Problem.** Project-guide's bundled `templates/artifacts/pyve-essentials.md` (auto-rendered into every consumer's `go.md` under `## Project Essentials > ### Pyve Essentials` via FR-13) references Pyve invocation patterns that pre-date Pyve v2.8.0:

- **Testenv path.** References `.pyve/testenv/venv/` (singular `testenv`). Pyve v2.8.0 (Pyve Story M.h) moved this to `.pyve/testenvs/<name>/{venv,conda}/` (plural, name-keyed); the default env name is `testenv`, so the v2.8.0 default path is `.pyve/testenvs/testenv/venv/`. Existing on-disk projects migrate transparently the first time `pyve update` / `pyve test` / `pyve testenv …` runs, so consumers won't break — but the documentation needs to land at the new shape so new users see the post-2.8 reality from day one.
- **Named test environments.** Pyve v2.8.0 introduced `[tool.pyve.testenvs]` in `pyproject.toml` (per-env backend `venv` / `micromamba` / `inherit`; source `requirements` / `extra` / `manifest`; lifecycle `lazy = true`). Not mentioned at all. The default single-`testenv` workflow remains identical; this is awareness, not a workflow rewrite.
- **Renamed commands.** Pyve v2.0 hard-removed `pyve doctor` and `pyve validate` in favor of `pyve check` (CI-safe 0/1/2 exit codes), and introduced `pyve update` as the non-destructive upgrade subcommand (replaced the removed `pyve init --update` flag). Both renames are inside Pyve's permanent Category-B legacy-flag-catches, so an LLM typing the old name gets a deprecation error rather than silent breakage — but the LLM-facing guidance should not be the source of that error.

Net effect: no consumer is broken (Pyve's migration shims protect them), but the LLM-facing guidance is stale. New project-guide users following the current rules will see Pyve deprecation noise and miss the modern declarative-config affordances.

**Behavior (post-story).** Surgical edits to the bundled artifact:

- Replace `.pyve/testenv/venv/` references with `.pyve/testenvs/testenv/venv/` (default env name). One-sentence note that Pyve v2.8.0 generalized to `.pyve/testenvs/<name>/{venv,conda}/` for declared named envs.
- Add a one-paragraph mention of `[tool.pyve.testenvs]` declarative config with a pointer at Pyve's `pointmatic.github.io/pyve/testing/#named-test-environments` for the full schema. **Do not duplicate Pyve's schema** — project-guide makes consumers aware the surface exists; Pyve owns the canonical detail.
- Replace `pyve doctor` / `pyve validate` references with `pyve check`.
- Add a brief mention of `pyve update` as the non-destructive refresh path (preserves env, refreshes managed files + project-guide scaffolding), distinct from `pyve init --force` (destructive rebuild).

The rest of the artifact (two-environment pattern, canonical invocation forms, `python` vs `python3`, `requirements-dev.txt` convention, editable-install / testenv guidance, LLM-internal vs. developer-facing invocation) is preserved unchanged — those rule shapes remain accurate against Pyve v2.8.0.

**Why this default.**

- **Surgical edits, not a rewrite.** The artifact's existing rule shapes are sound. The drift is in three specific places (path, command names, awareness of declarative config). A wholesale rewrite would create review surface area for content that doesn't need changing and would risk losing the careful LLM-vs-developer / `python`-vs-`python3` / editable-install nuance that took prior phases to land correctly.
- **Awareness of `[tool.pyve.testenvs]`, not schema duplication.** Project-guide's bundled artifact is read by every consumer's LLM, including consumers who haven't yet adopted named-testenvs. Forcing every LLM to learn Pyve's schema as a precondition to writing a single test would be a regression. The right shape is "this surface exists, here's where to learn more" — same pattern as the existing `pyve testenv init` / `pyve testenv install` brief mention.
- **Dogfood refresh as a conditional sub-task, not a separate story.** Per the auto-render flow (FR-13 in [features.md](features.md)), the `### Pyve Essentials` block in every `go.md` is sourced from the bundled artifact, *not* from per-project `project-essentials.md` content. So this project's `docs/specs/project-essentials.md` likely has nothing to refresh — the rules render through the same path everyone else uses. The story verifies that explicitly (FR-6 confirmation step) rather than assuming.
- **No on-disk path migration story.** Pyve handles the v2.7→v2.8 layout migration transparently the first time `pyve update` / `pyve test` / `pyve testenv …` runs in a pre-v2.8 project. Project-guide doesn't touch `.pyve/`; we just describe the post-migration shape. The user's actual disk state moves on Pyve's schedule.

**Implementation:**
- [ ] Edit `project_guide/templates/project-guide/templates/artifacts/pyve-essentials.md`:
  - [ ] Replace `.pyve/testenv/venv/` references with `.pyve/testenvs/testenv/venv/`; add one sentence noting the generalization to `.pyve/testenvs/<name>/{venv,conda}/` for declared named envs.
  - [ ] Add one paragraph on `[tool.pyve.testenvs]` declarative config with a pointer at `pointmatic.github.io/pyve/testing/#named-test-environments`.
  - [ ] Replace `pyve doctor` / `pyve validate` references with `pyve check`.
  - [ ] Add one sentence on `pyve update` as the non-destructive refresh path; distinguish from `pyve init --force` (destructive).
- [ ] Verify `docs/specs/project-essentials.md` for dogfood-specific Pyve entries needing the same refresh (FR-6 verification). If any exist outside the bundled-artifact auto-render block, apply the same edits. If none exist (expected), record the verification result in the implementation notes and skip the per-project edit.
- [ ] Run `pyve run project-guide update` to propagate the bundled-artifact edit to `docs/project-guide/templates/artifacts/pyve-essentials.md`; auto-render verifies the next `go.md` re-render picks it up.
- [ ] Spot-check the rendered `### Pyve Essentials` block in `docs/project-guide/go.md` after the update to confirm the edits landed in the auto-rendered output.
- [ ] Run `pyve test`.
- [ ] Run `pyve testenv run ruff check project_guide/ tests/`.
- [ ] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Full `[tool.pyve.testenvs]` schema documentation in `pyve-essentials.md`.** Project-guide does not duplicate Pyve's authoritative schema. One paragraph + link.
- **Conda-backed testenv recipes.** Awareness-only; recipe-grade content lives in Pyve's own `testing.md`.
- **Migration tooling for consumers on pre-v2.8 Pyve.** Pyve handles its own migration on first invocation; project-guide has no role in the path-layout transition.
- **CHANGELOG entry.** Bundled into Q.c's v2.11.0 release entry, not authored per-story.
- **`pyve check` integration into project-guide's own CI guidance.** No CI workflow edits in Q-1; current dogfood loop is `pyve test` + `pyve testenv run ruff check`, which remains accurate.

---

### Story Q.c: v2.11.0 Subphase Q-1 bundled release [Planned]

**Problem.** Subphase Q-1 ships as one bundled release per the subphase phase-bundling option installed in Story Q.a. Stories Q.a and Q.b run unversioned; Q.c is the release-marker story that bumps the package and authors the CHANGELOG entry covering both.

**Behavior (post-story).** Version bumped to **v2.11.0** across the three canonical sites (`project_guide/version.py`, `pyproject.toml`, new `CHANGELOG.md` entry). The CHANGELOG entry describes Subphase Q-1's two themes as one bundled release: the subphase pattern (Q.a) and the Pyve v2.8.0 alignment (Q.b).

**Why this default.**

- **v2.11.0 minor, not patch.** Subphase Q-1 introduces a new opt-in capability (the subphase pattern) to the `plan_production_phase` / `plan_phase` modes, which is a *feature* addition by the Version Cadence rule (`Feature or improvement → minor`). The pyve-essentials refresh on its own would be patch-grade, but the bundle is named by the highest-impact change.
- **One bump, last story.** The Version Cadence rule and the subphase phase-bundling proposal both land the bump on the closing story of the bundle. Q.c exists explicitly to mark that boundary — it's the only story in Q-1 with a version in its title.
- **CHANGELOG entry covers both Q.a and Q.b.** Bundled releases get one entry, not two. The entry's prose names both work units so future readers don't have to reconstruct the bundle's contents from commit history.

**Implementation:**
- [ ] Bump `project_guide/version.py` to `2.11.0`.
- [ ] Bump `pyproject.toml` to `2.11.0`.
- [ ] Add `## [2.11.0] - <date>` entry to `CHANGELOG.md` with two subsections (e.g., `### Added` for the subphase pattern; `### Changed` for the Pyve v2.8.0 alignment refresh). Concise prose; reference Q.a and Q.b by story ID; cross-reference [`phase-q-dx-subphases-plan.md`](phase-q-dx-subphases-plan.md) and [`subphase-strategy-for-large-phases.md`](subphase-strategy-for-large-phases.md).
- [ ] Run `pyve test`.
- [ ] Run `pyve testenv run ruff check project_guide/ tests/`.
- [ ] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Git tag / PyPI publish.** Per the *Approval gate discipline* rule in [project-essentials.md](project-essentials.md), the LLM does not initiate git operations or releases. The developer pushes the tag and triggers publish on their own schedule.
- **End-of-subphase mode switch / migration to a Q-2 planning session.** Q-2 entry is a separate developer-initiated decision; Q.c is just the release marker for Q-1.

---

## Future

### Audit Modes [Deferred]

Future modes: `audit_security`, `audit_architecture`, `audit_performance`, `audit_best_practices`, `audit_modularity`, `audit_patterns`.

### Project Lifecycle Automation [Deferred]

- Release helper / version-bump / tag automation — developer works across multiple git flows and prefers tool-agnostic; no timeline.
- Migration tooling for `docs/guides/` → `docs/project-guide/` — future `refactor` mode; low demand.

### Advanced Project Essentials [Deferred]

- `create_or_modify` action type — revisit if multiple artifacts develop the need; not yet justified.
- Validation/linting of `project-essentials.md` content — freeform by design; template convention is sufficient.
- Auto-detection of stale `project-essentials.md` — git-log based; deferred until there is demand.

### CLI Edge Cases [Deferred]

- `--interactive` flag to force interactive mode over non-TTY stdin — not needed; `stdin` can always be re-attached.
- Legacy broken-state detection for `init` (`.project-guide.yml` absent but target dir populated) — unusual edge case; falls through to existing skip-with-warnings path.

### Integrity & Validation [Deferred]

- `project-guide check` command — dedicated integrity/audit surface with nonzero exit on failure, suitable for CI and pre-commit hooks. Candidate rules: `project_name` in config vs. `cwd.name` vs. `pyproject.toml` `[project] name`; artifact headers (`# stories.md -- <name> (<lang>)`) vs. `config.project_name`/`config.programming_language`; `SCHEMA_VERSION` surfacing; `installed_version` vs. `__version__`; `.archive/stories-vX.Y.Z.md` filenames parse cleanly; metadata override keys reference existing modes; unrendered `{{ var }}` placeholders across written artifacts (broadens the N.s `render_fresh_stories_artifact` guard to every written artifact). `project-guide status` runs a cheap subset and prints a one-line footer (`⚠ N integrity issues — run 'project-guide check' for details`) without changing its exit code. Precedent: `django check`, `brew doctor`, `cargo check`. Defer until there is a concrete second integrity rule worth shipping (N.s covers the first drift source inline with a warning).

### Template & Rendering [Deferred]

- Support for literal `{{ var }}` strings in template output — use `{% raw %}...{% endraw %}` on a case-by-case basis; bridge with a general solution only if the pattern becomes common.
