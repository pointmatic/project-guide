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

### Story Q.a: Subphase strategy pattern — template installation [Done]

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
- [x] Edit `project_guide/templates/project-guide/templates/modes/plan-production-phase-mode.md` — insert Step 4a between current Step 4 (Generate a phase plan document) and Step 5 (Breaking-change negotiation). Update Step 7 (Add a new phase section and stories to `stories.md`) with a sentence referencing the subphase layout when Step 4a opted in.
- [x] Edit `project_guide/templates/project-guide/templates/modes/_phase-letters.md` — add new "Subphases (structural grouping within a phase)" section after "Story sub-letters" / before "Sub-numbered stories".
- [x] Edit `project_guide/templates/project-guide/templates/modes/_header-common.md` — append one sentence to the "Scope of authority — structural changes to `stories.md`" rule clarifying that subphase headings under an existing `## Phase X:` are allowed under the same authority.
- [x] Edit `project_guide/templates/project-guide/templates/modes/plan-phase-mode.md` — append one parenthetical sentence to Step 4 noting subphasing is available pre-1.0 but rarely needed; cross-reference `plan_production_phase` Step 4a.
- [x] Run `pyve run project-guide update` to propagate template edits to `docs/project-guide/` (the dogfooded installed copy).
- [x] Run `pyve test` — every mode template must still render without errors (parametrized regression guard in `tests/test_render.py`).
- [x] Run `pyve testenv run ruff check project_guide/ tests/` — clean.
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Programmatic enforcement of the subphase pattern.** No `project-guide subphase add Q-2` command — the pattern is LLM-readable template guidance. YAGNI until field use shows the rule alone is insufficient.
- **Retroactively re-decomposing archived phase plans.** No archived phase or its plan doc is being rewritten. Phase N (Pyve's worked example) stays as drafted in its own repo.
- **Cross-link to a future Pyve Phase N worked example** in the template body. Deferred until Pyve's Phase N artifacts ship and their paths are stable.
- **Tests for the template content.** Templates are rendered verbatim through Jinja; no logic to test. The existing render-pipeline regression guard already verifies file inclusion.
- **`plan-stories-mode.md` / `refactor-plan-mode.md` edits.** Per the change request's "Suggested template changes" section, neither template needs subphase awareness: `plan_stories` is for *initial* story planning of a project with no prior story plan; `refactor_plan` does not create phases.

---

### Story Q.b: Pyve v2.8.0 alignment — pyve-essentials.md refresh [Done]

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
- [x] Edit `project_guide/templates/project-guide/templates/artifacts/pyve-essentials.md`:
  - [x] Replace `.pyve/testenv/venv/` references with `.pyve/testenvs/testenv/venv/`; add one sentence noting the generalization to `.pyve/testenvs/<name>/{venv,conda}/` for declared named envs.
  - [x] Add one paragraph on `[tool.pyve.testenvs]` declarative config with a pointer at `pointmatic.github.io/pyve/testing/#named-test-environments`.
  - [x] Replace `pyve doctor` / `pyve validate` references with `pyve check`. *(Verification: neither term was present in the artifact pre-edit; the new `pyve update` vs. `pyve init --force` section now cites `pyve check` as the diagnostic command and explicitly names the v2.0 removal of `pyve doctor` / `pyve validate` so an LLM reading this file no longer learns the dead names.)*
  - [x] Add one sentence on `pyve update` as the non-destructive refresh path; distinguish from `pyve init --force` (destructive).
- [x] Verify `docs/specs/project-essentials.md` for dogfood-specific Pyve entries needing the same refresh (FR-6 verification). *(Result: no `.pyve/testenv` paths, no `pyve doctor` / `pyve validate` / `pyve init --update` references. The line-3 note explicitly defers Pyve workflow rules to the auto-rendered artifact; the remaining Pyve mentions are passing references that do not encode invocation patterns. No per-project edit needed.)*
- [x] Run `pyve run project-guide update` to propagate the bundled-artifact edit to `docs/project-guide/templates/artifacts/pyve-essentials.md`; auto-render verifies the next `go.md` re-render picks it up.
- [x] Spot-check the rendered `### Pyve Essentials` block in `docs/project-guide/go.md` after the update to confirm the edits landed in the auto-rendered output.
- [x] Run `pyve test`.
- [x] Run `pyve testenv run ruff check project_guide/ tests/`.
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Full `[tool.pyve.testenvs]` schema documentation in `pyve-essentials.md`.** Project-guide does not duplicate Pyve's authoritative schema. One paragraph + link.
- **Conda-backed testenv recipes.** Awareness-only; recipe-grade content lives in Pyve's own `testing.md`.
- **Migration tooling for consumers on pre-v2.8 Pyve.** Pyve handles its own migration on first invocation; project-guide has no role in the path-layout transition.
- **CHANGELOG entry.** Bundled into Q.c's v2.11.0 release entry, not authored per-story.
- **`pyve check` integration into project-guide's own CI guidance.** No CI workflow edits in Q-1; current dogfood loop is `pyve test` + `pyve testenv run ruff check`, which remains accurate.

---

### Story Q.c: v2.11.0 Subphase Q-1 bundled release [Done]

**Problem.** Subphase Q-1 ships as one bundled release per the subphase phase-bundling option installed in Story Q.a. Stories Q.a and Q.b run unversioned; Q.c is the release-marker story that bumps the package and authors the CHANGELOG entry covering both.

**Behavior (post-story).** Version bumped to **v2.11.0** across the three canonical sites (`project_guide/version.py`, `pyproject.toml`, new `CHANGELOG.md` entry). The CHANGELOG entry describes Subphase Q-1's two themes as one bundled release: the subphase pattern (Q.a) and the Pyve v2.8.0 alignment (Q.b).

**Why this default.**

- **v2.11.0 minor, not patch.** Subphase Q-1 introduces a new opt-in capability (the subphase pattern) to the `plan_production_phase` / `plan_phase` modes, which is a *feature* addition by the Version Cadence rule (`Feature or improvement → minor`). The pyve-essentials refresh on its own would be patch-grade, but the bundle is named by the highest-impact change.
- **One bump, last story.** The Version Cadence rule and the subphase phase-bundling proposal both land the bump on the closing story of the bundle. Q.c exists explicitly to mark that boundary — it's the only story in Q-1 with a version in its title.
- **CHANGELOG entry covers both Q.a and Q.b.** Bundled releases get one entry, not two. The entry's prose names both work units so future readers don't have to reconstruct the bundle's contents from commit history.

**Implementation:**
- [x] Bump `project_guide/version.py` to `2.11.0`.
- [x] Bump `pyproject.toml` to `2.11.0`.
- [x] Add `## [2.11.0] - <date>` entry to `CHANGELOG.md` with two subsections (e.g., `### Added` for the subphase pattern; `### Changed` for the Pyve v2.8.0 alignment refresh). Concise prose; reference Q.a and Q.b by story ID; cross-reference [`phase-q-dx-subphases-plan.md`](phase-q-dx-subphases-plan.md) and [`subphase-strategy-for-large-phases.md`](subphase-strategy-for-large-phases.md).
- [x] Run `pyve test`.
- [x] Run `pyve testenv run ruff check project_guide/ tests/`.
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Git tag / PyPI publish.** Per the *Approval gate discipline* rule in [project-essentials.md](project-essentials.md), the LLM does not initiate git operations or releases. The developer pushes the tag and triggers publish on their own schedule.
- **End-of-subphase mode switch / migration to a Q-2 planning session.** Q-2 entry is a separate developer-initiated decision; Q.c is just the release marker for Q-1.

---

## Subphase Q-2: `plan_envs` mode (Pyve env-spec authoring surface)

Adds a new sequence mode `plan_envs` that guides the developer through enumerating named environments (root + test envs), their backends, frameworks, packaging, and advisory fields. Authors `docs/specs/env-dependencies.md` from a bundled artifact template that vendors Pyve's `env-dependencies-template.md` at `spec_version: "3.0"`. Slotted into the canonical planning sequence as `plan_tech_spec → plan_envs → plan_stories`.

Driver: Pyve's v2.8 → v3.0 transition raises env topology to a discrete planning concern; the cross-repo contract from Pyve's N.ao spike (closed-vocabulary trichotomy, vendored-template invariant) is the authoritative shape consumed here. See [`phase-q-wizard-env-contract.md`](phase-q-wizard-env-contract.md) for the contract and [`phase-q-subphase-2-plan-envs-plan.md`](phase-q-subphase-2-plan-envs-plan.md) for the full Q-2 plan.

Bundled release at end-of-subphase as **v2.12.0** (minor — new feature). Three stories, executed in document order; only `Q.f` carries the version in its title. **Dependency:** Q.a's subphase-pattern templates must ship (v2.11.0) before Q.d–Q.f are *worked on* — Q-2's planning happens now; Q-2's implementation waits for v2.11.0.

### Story Q.d: `plan_envs` mode authoring — template, artifact, metadata wiring [Done]

**Problem.** Project-guide's planning sequence today (`plan_concept` → `plan_features` → `plan_tech_spec` → `plan_stories`) leaves environment topology unaddressed. For a Pyve-managed repo — let alone a Pyve v3.0 named-env + plugin-architecture repo — the question "how many environments, with what backends, frameworks, and packaging?" is a discrete planning decision that today gets bootloaded into `plan_tech_spec` (overloading its architecture focus), dropped on `plan_stories` (decisions emerge mid-implementation), or omitted entirely (silent drift between intent and `pyve.toml`). Pyve's N.ao spike introduced `docs/specs/env-dependencies.md` as the point-in-time env-spec artifact (peer of `features.md` / `tech-spec.md`); project-guide has no bundled template, no mode that authors it, no metadata wiring that names it.

**Behavior (post-story).** Three files land together — the mode is non-functional without all three. Two are new files; one is an edit.

- **New: `project_guide/templates/project-guide/templates/modes/plan-envs-mode.md`.** Sequence-mode template adapted from [`phase-q-plan-envs-mode-roughdraft.md`](phase-q-plan-envs-mode-roughdraft.md). Follows the existing `plan_concept` / `plan_features` / `plan_tech_spec` shape: includes `_header-sequence.md`; states purpose; lists prerequisites (`features.md`, `tech-spec.md`); enumerates steps (read specs → determine env topology with closed-vocabulary discipline → generate `env-dependencies.md` from bundled template → present for approval → iterate → next-mode hint `plan_stories`); ends with the closed-vocabulary discipline note (values come from the bundled template's §2 glossary; unknown value is a spec violation, not a creative choice; missing mechanism is a Pyve change-request per §8, not an invention).
- **New: `project_guide/templates/project-guide/templates/artifacts/env-dependencies.md`.** Artifact template adapted from [`phase-q-plan-envs-mode-env-dependences-artifact-roughdraft.md`](phase-q-plan-envs-mode-env-dependences-artifact-roughdraft.md). Section structure (§0 through §9) preserved; Pyve-internal path references removed (rough draft's `pyve-environment-dependencies-repo_<repo_name>.md` filename collapses to canonical `docs/specs/env-dependencies.md`); cross-references rewritten in project-guide artifact style (links to `concept.md` / `features.md` / `tech-spec.md` / `go.md`); §4.0 YAML block hard-codes `spec_version: "3.0"`; closed-vocabulary tables preserved verbatim from the rough draft. Header comment cites the vendored-template invariant: `<!-- Vendored from Pyve env-dependencies-template.md at spec_version "3.0". Closed vocabulary is Pyve-owned; project-guide refreshes via a dedicated story when Pyve bumps. See docs/specs/project-essentials.md → "Pyve env-spec vendored-template contract" for the protocol. -->`
- **Edited: `project_guide/templates/project-guide/.metadata.yml`.** Adds `plan_envs` mode definition (name, info, description, `sequence_or_cycle: sequence`, `generation_type: document`, `mode_template: modes/plan-envs-mode.md`, `next_mode: plan_stories`, artifacts: `docs/specs/env-dependencies.md` action `create`, `files_exist: [features.md, tech-spec.md]`). Position in the file: immediately after `plan_tech_spec`, before `plan_stories`. Flips `plan_tech_spec.next_mode` from `plan_stories` to `plan_envs`.

**Why these defaults.**

- **Three files in one story.** The mode is non-functional with any of the three missing: metadata-only wiring with no template → render error; template-only with no metadata → mode not listed and not selectable; mode + metadata with no artifact template → Step 3 of the mode has nothing to generate from. Splitting across stories would land a half-installed mode in an interim release.
- **Vendored-template approach over schema parsing.** Project-guide does not parse the closed vocabulary or validate `env-dependencies.md` shape at render time. The bundled template carries the vocabulary verbatim as instructional content; LLM discipline (per the closed-vocabulary note in the mode template) is what keeps `plan_envs` output conformant. Schema validation is Pyve's F6 responsibility — happens at `pyve env sync` time, not at `project-guide plan_envs` time.
- **`spec_version: "3.0"` hard-coded.** No runtime version negotiation, no dynamic lookup of Pyve's current vocabulary. Bumps to the value come via a dedicated refresh story (the Q.b / Q-1 pattern). This keeps project-guide's coupling to Pyve at *release-pinned*, not *runtime-linked* — the same shape as `pyve-essentials.md`'s vendoring.
- **`files_exist: [features.md, tech-spec.md]`.** The mode infers env requirements from these specs plus the codebase. Listing them as prerequisites makes the `project-guide mode` listing surface them as unmet (`✗`) when absent, preventing the LLM from running `plan_envs` against an underspecified project.
- **`next_mode: plan_stories`.** Env decisions inform story scoping (which stories run in which env). The natural next step after env topology is implementation breakdown.
- **Slotted in the canonical sequence (not listing-only).** Per gate confirmation: `plan_tech_spec → plan_envs → plan_stories` is the new sequence. Existing projects already past `plan_tech_spec` are unaffected; new projects pick up the env-planning step cleanly. The sequence change is technically-but-trivially breaking (advisory recommendation only; explicit-mode-name invocation continues to work unchanged).
- **No `_header-cycle.md` consideration.** `plan_envs` is a sequence mode, not a cycle. Env decisions are point-in-time per Pyve's `spec_version`, not a continuous refinement loop. Re-running `plan_envs` regenerates the doc idempotently (per the rough draft's design).

**Implementation:**
- [x] Author `project_guide/templates/project-guide/templates/modes/plan-envs-mode.md` per the shape above. Adapt steps from [`phase-q-plan-envs-mode-roughdraft.md`](phase-q-plan-envs-mode-roughdraft.md) into project-guide's sequence-mode pattern (parallel to `plan-tech-spec-mode.md`).
- [x] Author `project_guide/templates/project-guide/templates/artifacts/env-dependencies.md`. Adapt from [`phase-q-plan-envs-mode-env-dependences-artifact-roughdraft.md`](phase-q-plan-envs-mode-env-dependences-artifact-roughdraft.md). Preserve §0–§9 structure, closed-vocabulary tables verbatim. Remove Pyve-internal path references. Add the vendored-template header comment. Hard-code `spec_version: "3.0"` at §4.0.
- [x] Edit `project_guide/templates/project-guide/.metadata.yml`: add `plan_envs` block between `plan_tech_spec` and `plan_stories`; flip `plan_tech_spec.next_mode` from `plan_stories` to `plan_envs`; confirm `plan_envs.next_mode: plan_stories`.
- [x] Run `pyve run project-guide update` to propagate template + metadata edits to `docs/project-guide/` (the dogfooded installed copy).
- [x] Run `pyve run project-guide mode plan_envs` to verify the new mode renders without errors. Inspect the rendered `go.md` for: correct step sequence, prerequisite list, closed-vocabulary discipline note, next-mode hint pointing at `plan_stories`.
- [x] Run `pyve run project-guide mode` (no arg) to verify listing shows `plan_envs` in the "Project Planning" category between `plan_tech_spec` and `plan_stories`.
- [x] Run `pyve test` — the parametrized render-mode test must still pass (it iterates `.metadata.yml`; the new mode is picked up automatically).
- [x] Run `pyve testenv run ruff check project_guide/ tests/`.
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Pyve-side env-sync / schema validation.** Pyve's F4 (`pyve env sync`), F5 (contract-guard test), and F6 (closed-vocabulary trichotomy in `pyve_toml_helper.py`) all live in the Pyve repo. Project-guide is the authoring surface; Pyve is the consumer.
- **Dynamic `spec_version` discovery.** No runtime template fetching, no version negotiation. Bumps via refresh stories.
- **Validating the artifact's content at `project-guide` time.** No `project-guide check env-dependencies` integrity command. LLM discipline + Pyve's downstream validation is the loop.
- **Backfilling `env-dependencies.md` for this dogfooded project.** Running `plan_envs` against project-guide itself is a separate concern; may land in Q-3 if Q-2 field use surfaces template gaps.
- **`refactor_envs` cycle counterpart.** Env decisions are point-in-time per Pyve's `spec_version`, not a continuous-refinement loop. Re-run `plan_envs` if a redo is needed.
- **Spec doc sync (`concept.md`, `features.md`, `project-essentials.md`).** Bundled into Q.e.
- **Version bump / CHANGELOG entry.** Bundled into Q.f.

---

### Story Q.e: Spec doc sync — `concept.md`, `features.md`, `project-essentials.md` [Done]

**Problem.** Q.d adds the `plan_envs` mode but leaves the project's own spec documents stale. Three drift surfaces need to be addressed in one coherent edit:

1. **`features.md` FR-1 modes table** lists 15 rows but is missing `plan_production_phase` (the very mode being used to plan this subphase). Post-Q-2, the count becomes 17 (existing 15 table rows + `plan_production_phase` + `plan_envs`).
2. **`concept.md` Scope** claims "15 modes" and lists 14 modes + a future `code_production`. The list uses retired names: `project_scaffold` (current: `scaffold_project`), `code_velocity` (current: `code_direct`). Drift accumulated across phases; Q-2 is the natural moment to clean it because we're touching the mode list anyway.
3. **`project-essentials.md` lacks the Pyve env-spec vendored-template invariant.** Q.d ships a bundled template whose vocabulary is Pyve-owned; without an explicit invariant recorded in `project-essentials.md`, future LLMs are likely to "improve" the template independently, invent vocabulary values, or fail to recognize a Pyve template bump as a refresh-story trigger.

**Behavior (post-story).** Three surgical edits.

- **`features.md` FR-1 modes table edit.** Add a `plan_production_phase` row (sequence; "Plan a production-grade phase post-1.0 with readiness checklist and breaking-change negotiation"). Add a `plan_envs` row (sequence; "Define named environments and their dependencies"). Refresh table-header count from "**15 total**" → "**17 total**" (or equivalent wording — confirm exact phrasing during edit).
- **`concept.md` Scope statement edit.** Refresh mode list to current names: `scaffold_project` (not `project_scaffold`), `code_direct` (not `code_velocity`). Add `plan_envs` and `plan_production_phase` to the list. Refresh count "15 modes" → "17 modes" (preserving the "future `code_production`" mention, since that mode is still future). Same edit hygiene applied to any other count references in `concept.md` that flag during the edit.
- **`project-essentials.md` new section.** Append after the existing `### Pyve Essentials` section a new section titled `### Pyve env-spec vendored-template contract`. Content per [`phase-q-subphase-2-plan-envs-plan.md`](phase-q-subphase-2-plan-envs-plan.md) § Q-2-FR-5:
  - Vendored template, Pyve-owned vocabulary.
  - Trichotomy contract (known+implemented / known+advisory / unknown→error).
  - Refresh-story protocol (same shape as Q.b's `pyve-essentials.md` v2.8.0 alignment).
  - Authoritative source pointer (Pyve's `docs/specs/project-guide-requests/env-dependencies-template.md`).
  - Cross-reference: existing `### Pyve Essentials` is about Pyve *invocation*; new section is about Pyve *env-spec vocabulary*. Complementary, not overlapping.

**Why these defaults.**

- **Drift cleanup folded into the same story, not spun off.** Per gate confirmation: refreshing `concept.md`'s old mode names while we're already adding `plan_envs` to its list is one cognitive unit, one commit, no risk of partial coverage. Spinning a separate story would leave Q.e narrowly scoped to "add new mode" while a parallel story handled "rename old modes" — two PRs to review, two commit boundaries for related edits.
- **`project-essentials.md` invariant lands here, not in Q.d.** Q.d's surface is "the mode works." Q.e's surface is "future LLMs reading the specs understand the cross-repo contract." Different cognitive layers; different review focus.
- **New section, not edit of existing `### Pyve Essentials`.** The existing section is auto-rendered from `pyve-essentials.md` (FR-13) — editing it inline would create drift between the dogfooded `project-essentials.md` and the bundled artifact. The new section is project-guide-specific architectural invariant content, never auto-rendered, hand-authored.
- **17, not 16.** Count refresh acknowledges both additions (`plan_envs` from Q.d, `plan_production_phase` from prior drift).

**Implementation:**
- [x] Edit `docs/specs/features.md` FR-1 modes table: add `plan_production_phase` row, add `plan_envs` row, refresh count to 17.
- [x] Edit `docs/specs/concept.md` Scope: refresh mode names (`project_scaffold` → `scaffold_project`, `code_velocity` → `code_direct`), add `plan_envs` and `plan_production_phase`, refresh count "15 modes" → "17 modes". Preserve "future `code_production`" mention.
- [x] Append new `### Pyve env-spec vendored-template contract` section to `docs/specs/project-essentials.md` after the existing `### Pyve Essentials` section. Content per the Q-2-FR-5 outline above. *(Note: `### Pyve Essentials` is auto-rendered into `go.md` from the bundled artifact, not present in `project-essentials.md` itself, so the new section was appended at the end of the file; the cross-reference still resolves correctly in the rendered `go.md`.)*
- [x] Run `pyve run project-guide update` to re-render `go.md` (the new `project-essentials.md` section flows into rendered output via the auto-render path). *(`update` refreshes static files; `go.md`'s `## Project Essentials` injection is re-rendered by `project-guide mode`, which was re-run to refresh the file.)*
- [x] Spot-check the rendered `### Pyve env-spec vendored-template contract` block in `docs/project-guide/go.md`.
- [x] Run `pyve test`.
- [x] Run `pyve testenv run ruff check project_guide/ tests/`.
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Renaming any `.metadata.yml` mode keys.** No `project_scaffold` → `scaffold_project` rename anywhere in the metadata or template tree — that ship sailed in earlier phases; the current canonical names are already in place. Q.e is fixing stale `concept.md` references to retired names, not initiating any rename.
- **`tech-spec.md` mode enumeration refresh.** `tech-spec.md` doesn't enumerate modes individually; the auto-render flow remains correct. Spot-checks during the edit may surface link rot worth a one-line fix, but a full sweep is out of scope.
- **Audit of all spec docs for cross-document inconsistency.** Q.e fixes drift identified during Q-2 planning. A broader audit (every spec doc, every count, every cross-reference) is a separate concern that may land in a future Q-N subphase.
- **CHANGELOG entry / version bump.** Bundled into Q.f.

---

### Story Q.e.1: Planning-artifact drift sweep — `concept.md`, `features.md`, `tech-spec.md` [Done]

**Problem.** Q.e fixed the headline mode-list drift in `concept.md` and `features.md` but a follow-on audit (requested at the Q.e gate) surfaced further drift in the **planning artifacts** that must be current before the v2.12.0 release. These are `refactor_plan`-class documents (concept / features / tech-spec); the drift is mechanical (stale counts, retired names, an out-of-date gitignore description, an incomplete CLI command list) and right-sized for a sweep story rather than a `refactor_plan` mode switch.

**Behavior (post-story).** Every planning-artifact reference to mode counts, mode names, the CLI command set, and the gitignore block shape is accurate against the current `.metadata.yml` (17 real modes + future `code_production`) and current behavior.

- **`concept.md` Scope (line ~48–49).** CLI command list refreshed to include the commands shipped since it was last touched (`heal`, `git-push`, `archive-stories`, `completion`, plus existing `init`/`mode`/`status`/`update`/`override`/`unoverride`/`overrides`/`purge`). Mode list completed to include `archive_stories` (currently omitted); count reconciled so the stated number matches the listed items.
- **`features.md` FR-1 acceptance (line ~533).** "All 15 modes render without errors" → "All 17 modes render without errors" (or count-agnostic wording).
- **`features.md` FR-2 gitignore (line ~251).** "(3 lines: ...)" description updated to the **negation-free explicit-list form** (v2.7.1 / P.l), matching the FR-14 detail later in the same file and `tech-spec.md` § gitignore.
- **`tech-spec.md`.** Spot-check confirmed largely current (gitignore / heal / git-push content already reflects the latest behavior). Fix any count or command-list drift discovered during the edit; a full restructure is out of scope.

**Why this default.**

- **Sweep story, not `refactor_plan` mode.** The drift is find-and-align mechanical work, not a feature-driven rewrite or legacy migration (the cases `refactor_plan` exists for). A mode switch mid-release is heavier than the work warrants.
- **Split from Q.e.2 along the artifact-class boundary.** Planning artifacts (this story) vs. published documentation artifacts (Q.e.2) are reviewed with different focus and map to the `refactor_plan` / `refactor_document` division. Two clean commit boundaries beat one mega-diff spanning both.
- **`concept.md` count reconciliation.** Q.e deliberately left `archive_stories` off `concept.md`'s list (scope-bounded to the two new modes). This story closes that gap so the count and the enumerated items agree.

**Implementation:**
- [x] Edit `docs/specs/concept.md` Scope: refresh the CLI command list to the current subcommand set (added `heal`, `archive-stories`, `bump-version`, `git-push`); add `archive_stories` to the mode list; reconcile the stated mode count with the listed items (17 real modes now match; `code_production` reworded as a future addition outside the count).
- [x] Edit `docs/specs/features.md`: FR-1 acceptance "15 modes" → "17 modes"; FR-2 gitignore "(3 lines: ...)" → negation-free explicit-list description consistent with FR-14 / `tech-spec.md`.
- [x] Spot-check `docs/specs/tech-spec.md` for mode-count / CLI-command / gitignore drift; fix any found (no restructure). *(Result: clean — no mode-count or subcommand-enumeration drift, no retired names, gitignore content already in explicit-list form, no artifact-pipeline list needing `env-dependencies.md`. No edits needed.)*
- [x] Run `pyve run project-guide update` and re-render `go.md`. *(N/A: Q.e.1 touches only `docs/specs/{concept,features}.md` — project artifacts, not bundled templates or `project-essentials.md` — so nothing flows through `update` or the go.md `## Project Essentials` injection. Skipped as inapplicable.)*
- [x] Run `pyve test`.
- [x] Run `pyve testenv run ruff check project_guide/ tests/`.
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Documentation artifacts (`README.md`, `docs/site/`).** Owned by Q.e.2.
- **Archived stories under `docs/specs/.archive/`.** Frozen historical records — never edited; their retired-name references (`code_velocity`, `project_scaffold`) are correct in their historical context.
- **Substantive content rewrites.** This is drift alignment, not a `refactor_plan`-grade restructure.
- **CHANGELOG entry / version bump.** Bundled into Q.f.

---

### Story Q.e.2: Documentation-artifact drift sweep — `README.md` + `docs/site` MkDocs [Done]

**Problem.** The published documentation set — `README.md` and the MkDocs site under `docs/site/` — still advertises stale mode counts, uses the retired `code_velocity` name, and (in the detailed `modes.md` reference) is missing entries for `plan_envs` and `plan_production_phase`. These are `refactor_document`-class artifacts; the drift must be current before the v2.12.0 release so external readers see accurate information. The work is mechanical alignment plus two new mode-reference entries — right-sized for a sweep story rather than a `refactor_document` mode switch.

**Behavior (post-story).** Every published-documentation reference to mode counts and mode names is accurate, and the detailed mode reference documents all current modes.

- **Counts → 17.** `README.md` ("15 modes"), `docs/site/index.html` ("15 modes"), `docs/site/user-guide/workflow.md` ("16 modes"), `configuration.md` ("15 modes"), `commands.md` ("15 modes") all refreshed (prefer count-agnostic wording where it reads naturally, else the accurate number).
- **Retired name → `code_direct`.** `docs/site/getting-started.md`, `docs/site/user-guide/install-options.md`, `docs/site/user-guide/configuration.md` (the `current_mode:` example) updated from `code_velocity`.
- **`docs/site/user-guide/modes.md` new entries.** Add a `plan_envs` entry under Planning Modes (between `plan_tech_spec` and `plan_stories`) and a `plan_production_phase` entry; update the New-Project flow diagram to include `plan_envs` in the `plan_tech_spec → plan_envs → plan_stories` sequence. Verify the mode count/grouping line is consistent.
- **`docs/site/user-guide/commands.md`.** Ensure the mode-listing description and any enumerated mode examples include the new modes (or remain count-agnostic).

**Why this default.**

- **Sweep story, not `refactor_document` mode.** Same rationale as Q.e.1: mechanical alignment + two reference entries, not a feature-driven documentation rewrite. A mode switch right before release is over-provisioned.
- **`modes.md` carries real content, not just find-replace.** The two missing mode entries are genuine additions; bundling them with the count/name fixes keeps the whole published mode story consistent in one pass.
- **Split from Q.e.1.** Published-doc review (audience: external users) is a different focus from spec-doc review (audience: future LLMs/maintainers). Separate commit boundaries.

**Implementation:**
- [x] Refresh mode counts in `README.md`, `docs/site/index.html` (three occurrences), `docs/site/user-guide/workflow.md` (was "16"), `docs/site/user-guide/configuration.md`, `docs/site/user-guide/commands.md` to 17.
- [x] Replace retired `code_velocity` with `code_direct` in `docs/site/getting-started.md`, `docs/site/user-guide/install-options.md`, `docs/site/user-guide/configuration.md`.
- [x] Add `plan_envs` and `plan_production_phase` entries to `docs/site/user-guide/modes.md`; update the New-Project flow diagram to include `plan_envs`; update the planning-sequence intro and flip `plan_tech_spec`'s Next field to `plan_envs`.
- [x] Verify `docs/site/user-guide/commands.md` mode coverage references the new modes (or is count-agnostic). *(Count-agnostic; the listing description needed only the count refresh.)*
- [x] Grep the full `docs/site/` tree and `README.md` for any remaining `code_velocity` / `project_scaffold` / stale mode-count strings; fix stragglers. *(Caught two extra "15 development modes" in `index.html` body copy beyond the line-484 hit.)*
- [x] Run `pyve test`.
- [x] Run `pyve testenv run ruff check project_guide/ tests/`.
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Planning artifacts (`concept.md`, `features.md`, `tech-spec.md`).** Owned by Q.e.1.
- **Archived stories under `docs/specs/.archive/`.** Frozen historical records.
- **MkDocs build/deploy or theme changes.** Content alignment only; no `mkdocs.yml` structure or CI workflow changes.
- **Landing-page redesign or brand-copy rewrite.** `brand-descriptions.md` and `index.html` prose beyond the stale count are untouched.
- **CHANGELOG entry / version bump.** Bundled into Q.f.

---

### Story Q.f: v2.12.0 Subphase Q-2 bundled release [Done]

**Problem.** Subphase Q-2 ships as one bundled release per the subphase phase-bundling option installed in Q.a. Stories Q.d, Q.e, Q.e.1, and Q.e.2 run unversioned; Q.f is the release-marker story that bumps the package and authors the CHANGELOG entry covering them all.

**Behavior (post-story).** Version bumped to **v2.12.0** across the three canonical sites (`project_guide/version.py`, `pyproject.toml`, new `CHANGELOG.md` entry). The CHANGELOG entry describes Subphase Q-2's themes as one bundled release: the `plan_envs` mode introduction (Q.d), the spec-doc sync (Q.e), and the full documentation drift sweep across planning artifacts and the published MkDocs site (Q.e.1, Q.e.2).

**Why this default.**

- **v2.12.0 minor, not patch.** New mode + new artifact template + new architectural invariant (Pyve env-spec vendored-template contract) are *feature additions* by the Version Cadence rule (`Feature or improvement → minor`).
- **Distinct release from Q-1's v2.11.0.** Per the subphase phase-bundling pattern installed in Q.a, each subphase decides its own release shape; Q-1 and Q-2 ship as separate minor bumps because each is a discrete shippable bundle. Subphase Q-1 = v2.11.0; Subphase Q-2 = v2.12.0.
- **One bump, last story.** Same convention as Q.c — Q.f is the only Q-2 story with a version in its title; Q.d and Q.e run unversioned during the subphase.
- **CHANGELOG entry covers Q.d, Q.e, Q.e.1, and Q.e.2.** Bundled releases get one entry. The entry's prose names the work units and cross-references [`phase-q-subphase-2-plan-envs-plan.md`](phase-q-subphase-2-plan-envs-plan.md) and [`phase-q-wizard-env-contract.md`](phase-q-wizard-env-contract.md) so future readers can reconstruct the cross-repo context.

**Implementation:**
- [x] Bump `project_guide/version.py` to `2.12.0`.
- [x] Bump `pyproject.toml` to `2.12.0`.
- [x] Add `## [2.12.0] - 2026-06-05` entry to `CHANGELOG.md` with `### Added` (the `plan_envs` mode + `env-dependencies.md` artifact template + the Pyve env-spec vendored-template contract) and `### Changed` (planning-artifact spec sync + documentation drift sweep) subsections. References Q.d, Q.e, Q.e.1, Q.e.2 by story ID; cross-references [`phase-q-subphase-2-plan-envs-plan.md`](phase-q-subphase-2-plan-envs-plan.md) and [`phase-q-wizard-env-contract.md`](phase-q-wizard-env-contract.md).
- [x] Run `pyve test`.
- [x] Run `pyve testenv run ruff check project_guide/ tests/`.
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Git tag / PyPI publish.** Per the *Approval gate discipline* rule in [project-essentials.md](project-essentials.md), the LLM does not initiate git operations or releases. The developer pushes the tag and triggers publish on their own schedule.
- **End-of-subphase migration to a Q-3 planning session.** Q-3 entry is a separate developer-initiated decision; Q.f is just the release marker for Q-2.

---

### Story Q.g: README mode-listing completeness fix (post-v2.12.0 doc follow-up) [Done]

**Problem.** The Q.e.2 documentation sweep refreshed `README.md`'s mode *count* to 17 and added the new `plan_envs` / `plan_production_phase` entries to the MkDocs `docs/site/user-guide/modes.md` reference — but it never updated `README.md`'s own two mode catalogs. The result, shipped in v2.12.0, is an internal inconsistency: the README advertises "17 modes" while its listings enumerate only 14. Q.e.2's straggler grep searched for retired names and stale counts, not for *absent* mode entries, so the omissions slipped through. This is a **doc-only** fix with no behavior change and (per developer direction) **no version bump** — it rides into the repo as a standalone documentation correction.

**Behavior (post-story).** Every current mode is represented in `README.md`'s listings, consistent with the stated count of 17 and with the `.metadata.yml` mode set.

- **Quick Start §3 "Switch modes as you progress" block.** Add `plan_envs` (between `plan_tech_spec` and `plan_stories`) and `plan_production_phase` (adjacent to `plan_phase`) command lines, each with a one-line comment matching the block's style. (`default` is intentionally omitted from this "switch as you progress" block, as it was before.)
- **"Available Modes" → Project Planning table.** Add a `plan_envs` row (`docs/specs/env-dependencies.md`); update the section preamble "the **four** spec documents" → "**five**" to account for `env-dependencies.md`. (`plan_production_phase` is already present in the Release Planning table, so only `plan_envs` is missing from the catalogs.)
- **Interactive-menu example.** `Select mode [1-15, …]` → `[1-17, …]`.

**Why this default.**

- **New tail story (`Q.g`), not a reopened/renumbered Q.e.3.** Subphase Q-2 already shipped (v2.12.0, Q.f) and is committed. Inserting a sub-numbered `Q.e.3` would place it in document order *before* the committed Q.f, producing exactly the out-of-sequence state `project-guide git-push` flags. A new monotonic letter appended at the tail is the correct shape for genuinely post-release work, and no `[Planned]` stories sit ahead of it.
- **Appended under Subphase Q-2, no new subphase heading.** `code_direct` may append stories under an existing `## Subphase` heading but may not create new subphase/phase headings (that is `plan_production_phase`'s job). This fix is Q-2-deliverable cleanup, so it belongs under Q-2; a Q-3 subphase is not warranted for a one-file doc correction.
- **No version bump.** Doc-only, no behavior change, per developer direction. The README correction simply travels with the repo; the next release that bumps for code reasons will already include it.

**Implementation:**
- [x] Edit `README.md` Quick Start §3 switch block: add `plan_envs` and `plan_production_phase` command lines in position with style-matching comments.
- [x] Edit `README.md` "Available Modes" → Project Planning: add the `plan_envs` row; change the preamble "four spec documents" → "five".
- [x] Edit `README.md` interactive-menu example: `[1-15, …]` → `[1-17, …]`.
- [x] Grep `README.md` to confirm all 17 `.metadata.yml` modes appear at least once in the listings (allowing the intentional `default` omission from the switch block). *(All 17 present; `plan_phase` correctly distinct from `plan_production_phase`.)*
- [x] Run `pyve test` and `pyve testenv run ruff check project_guide/ tests/` (hygiene; no code change expected to affect them). *(586 passed; ruff clean.)*
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Re-auditing `docs/site/` for the same gap.** The MkDocs `modes.md` reference already received the new entries in Q.e.2; this story is the README-only follow-up. A fresh full-site completeness audit is a separate concern.
- **Version bump / CHANGELOG entry.** None — doc-only, no behavior change, per developer direction.
- **`default` in the Quick Start switch block.** Intentionally omitted, consistent with the block's existing shape.

---

### Story Q.h: Fix self-referential "Read Documentation" button on the landing page [Done]

**Problem.** The "Read Documentation" CTA button on the MkDocs landing page (`docs/site/index.html`) is broken: its `href` points at the site root `https://pointmatic.github.io/project-guide/`. The MkDocs nav declares `Home: index.html` (`mkdocs.yml`), so the site root **is** the landing page itself — clicking "Read Documentation" reloads the landing page instead of entering the docs. Every other "go to docs" link on the page targets `.../getting-started/` (the nav "Docs" link and the footer "Getting Started" link), so the CTA is the lone self-referential outlier. Doc-only fix on a static asset; no behavior change and **no version bump**.

**Behavior (post-story).** The CTA button navigates into the actual documentation at `https://pointmatic.github.io/project-guide/getting-started/`, consistent with the nav "Docs" link and the footer "Getting Started" link. Its label is also changed from "Read Documentation" to **"Get Started"** (per developer direction) — clearer call-to-action that matches the `getting-started/` destination.

**Why this default.**

- **Target `getting-started/`, not a bare docs root.** There is no separate docs index distinct from this landing page (`Home: index.html` maps the root to it), so the first real documentation page is `getting-started/`. Matching the two existing working links keeps all three "enter the docs" affordances pointing at the same place.
- **New tail story (`Q.h`), no version bump.** Same rationale as Q.g — Subphase Q-2 has shipped and is committed; this is a genuinely post-release doc fix appended at the tail under the existing subphase heading. Static-asset bug fix with no package behavior change carries no version, per the established doc-fix convention.
- **`code_direct`, not `debug`.** The root cause is immediately evident from the markup (self-referential `href`); no reproduce/isolate exploration is needed, so the `debug` cycle is not warranted.

**Implementation:**
- [x] Edit `docs/site/index.html`: change the CTA button `href` from `https://pointmatic.github.io/project-guide/` to `https://pointmatic.github.io/project-guide/getting-started/`, and relabel it from "Read Documentation" to "Get Started".
- [x] Grep `docs/site/index.html` to confirm no remaining bare-site-root links masquerading as docs links (the GitHub / PyPI CTAs are correct as-is).
- [x] Run `pyve test` and `pyve testenv run ruff check project_guide/ tests/` (hygiene; no code change expected to affect them).
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Broader landing-page link audit / redesign.** Only the one broken CTA is in scope; the nav, footer, and other CTAs are correct.
- **`mkdocs.yml` nav restructure** (e.g., adding a distinct docs landing page separate from `index.html`). The fix targets the existing `getting-started/` entry point; rethinking the home/docs split is a separate concern.
- **Version bump / CHANGELOG entry.** None — doc-only static-asset fix, no behavior change.

---

### Story Q.i: Fix vertical misalignment of the filled CTA button on the landing page [Done]

**Problem.** On the landing page (`docs/site/index.html`), the filled "View on GitHub" button's label sits ~2px higher than the two outlined buttons ("Install from PyPI", "Get Started") — visibly off-center in the CTA row. Root cause is a box-model mismatch: `.btn-secondary` carries a `2px solid` border while `.btn-primary` has none. With `box-sizing: border-box` but no explicit `height`, the border still adds to the outer box, so the outlined buttons are 4px taller. The `.cta-buttons` flex row has no `align-items` set (defaults to `stretch`), so the shorter filled button is stretched to match — but its single line of label text isn't re-centered, leaving it near the top of the taller box. Doc-only CSS fix on the static landing page; no behavior change and **no version bump**.

**Behavior (post-story).** All three CTA buttons have identical box height and vertically-centered labels.

- Add `border: 2px solid transparent;` to `.btn-primary` so the filled button's box matches `.btn-secondary`'s bordered box exactly (4px taller box, transparent so no visible outline), eliminating the height/centering discrepancy.

**Why this default.**

- **Transparent border over `align-items: center`.** Adding a transparent border makes the actual box heights equal — the robust fix — rather than only re-centering labels within unequal boxes. It also keeps the hover `transform: translateY(-2px)` lift consistent across all buttons. (`align-items: center` would mask the symptom but leave the boxes different heights.)
- **`.btn-primary` only, not the `.btn` base.** `.btn-secondary` already declares its own `2px solid var(--accent)` border; adding a transparent border to the base `.btn` would be overridden there anyway, so the minimal, clearest change is on `.btn-primary`.
- **New tail story (`Q.i`), no version bump.** Same convention as Q.g / Q.h — post-release static-asset doc fix appended under the existing subphase heading; no package behavior change, so no version.

**Implementation:**
- [x] Edit `docs/site/index.html`: add `border: 2px solid transparent;` to the `.btn-primary` rule.
- [x] Confirm the three CTA buttons now share identical box height (markup review: `.btn-primary` now carries a 2px transparent border matching `.btn-secondary`'s 2px solid border).
- [x] Run `pyve test` and `pyve testenv run ruff check project_guide/ tests/`. *(586 passed; ruff clean.)*
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Broader CSS / responsive audit of the landing page.** Only the CTA-row alignment is in scope.
- **Switching the flex row to `align-items: center`.** The transparent-border fix is preferred; revisit only if a future layout change needs it.
- **Version bump / CHANGELOG entry.** None — doc-only CSS fix, no behavior change.

---

### Story Q.j: Left-justify the hero headline and description in a width-matched container [Done]

**Problem.** On the landing page (`docs/site/index.html`), the hero headline and the multi-paragraph description under the banner are centered (`.hero { text-align: center }`). Centered body copy across several lines is hard to read — each line starts at a different left edge, so the eye loses the return point. The developer wants the headline and description wrapped in a container, left-justified, with the container width matching the Quick Start section's card area (`.quick-start-grid` is `max-width: 900px`) so the hero text block visually aligns with the content below it. Doc-only CSS/markup change on the static landing page; no behavior change and **no version bump**.

**Behavior (post-story).** The hero headline (`<h1>`) and the `.hero-description` paragraphs are wrapped in a new `.hero-content` container that is `max-width: 900px`, horizontally centered in the hero, and **left-aligned**. The description fills that container width (no longer capped at 800px and centered), so its left edge lines up with the headline. The 900px width matches `.quick-start-grid`'s `max-width`, so the hero text column aligns with the Quick Start cards below.

- **Banner image** stays full container width (unchanged).
- **CTA buttons** stay centered (unchanged) — the request covers the headline and text, not the button row.

**Why these defaults.**

- **`max-width: 900px` to match the cards.** `.quick-start-grid` caps at 900px; reusing that value makes the hero text column and the Quick Start card area share the same content width, which is what "match the width of the cards" asks for.
- **Wrap only `<h1>` + `.hero-description` in `.hero-content`.** Keeping the banner and CTA row outside the new container preserves their existing full-width / centered treatment, so the change is scoped to exactly the text the developer flagged.
- **Drop `.hero-description`'s `max-width: 800px` / `margin: … auto`.** Inside a left-aligned 900px container, the old `800px` + `auto` margins would re-center the paragraph and break the flush-left alignment with the headline; switching to `margin: 2rem 0` and full width keeps the left edges aligned.
- **New tail story (`Q.j`), no version bump.** Same convention as Q.g–Q.i — post-release static-asset doc fix appended under the existing subphase heading; no package behavior change, so no version.

**Implementation:**
- [x] Add a `.hero-content` CSS rule: `max-width: 900px; margin: 0 auto; text-align: left;` (comment notes 900px matches `.quick-start-grid`).
- [x] Update `.hero-description`: removed the `max-width: 800px` cap and changed `margin: 2rem auto` → `margin: 2rem 0` so it fills the container and left-aligns.
- [x] Wrap the hero `<h1>` and `<div class="hero-description">` in `<div class="hero-content"> … </div>` in the markup. *(Banner and CTA row left outside the wrapper, unchanged.)*
- [x] Run `pyve test` and `pyve testenv run ruff check project_guide/ tests/`. *(586 passed; ruff clean.)*
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Moving or restyling the CTA button row.** It stays centered as-is.
- **Banner image changes.** Stays full container width.
- **Broader hero/typography redesign or responsive-breakpoint rework** beyond what the container + left-justify requires.
- **Version bump / CHANGELOG entry.** None — doc-only CSS fix, no behavior change.

---

### Story Q.k: Style inline prose links so visited links stay readable in dark mode [Done]

**Problem.** The inline "Pyve" link in the hero description (`docs/site/index.html`) has no link styling, so it falls back to the browser's default anchor colors — unvisited blue and, critically, **visited purple**. On the dark background (`--bg-dark` / `--bg-darker`) the visited-purple is nearly unreadable. Unlike the nav, footer, and `.btn` links (which all have explicit color rules), inline prose links inside `.hero-description` were never styled. Doc-only CSS fix on the static landing page; no behavior change and **no version bump**.

**Behavior (post-story).** Inline links inside `.hero-description` render in the **same color as the surrounding text** (`color: inherit`, so they match the bold secondary-text prose) with an **underline** to signal they are links, and shift to the accent teal on hover (consistent with the nav/footer link affordance). Because the rule sets `color` on the anchor with no separate `:visited` override, the unreadable default visited-purple no longer appears.

**Why these defaults.**

- **`color: inherit` + underline, per developer direction.** The developer asked for "same color as text, underline shows it is a link." `color: inherit` makes the link match whatever prose it sits in (here the bold secondary text), and the underline carries the link affordance. This also neutralizes the `:visited` state, which is the actual bug.
- **`:hover` → accent.** A teal hover matches every other link on the page (nav, footer) and gives an interactive cue without making the resting state a hard-to-read color.
- **Scoped to `.hero-description a`.** That is the only inline-prose link on the page today. Keeping the selector scoped avoids disturbing the nav / footer / `.btn` links, which already have intentional styling. Future prose link locations can adopt the same rule if needed.
- **New tail story (`Q.k`), no version bump.** Same convention as Q.g–Q.j — post-release static-asset doc fix appended under the existing subphase heading; no package behavior change, so no version.

**Implementation:**
- [x] Add `.hero-description a { color: inherit; text-decoration: underline; }` and `.hero-description a:hover { color: var(--accent); }` to the stylesheet.
- [x] Confirm the visited-link state no longer uses the browser-default purple (no separate `:visited` rule remains in effect; `color` applies to all link states).
- [x] Run `pyve test` and `pyve testenv run ruff check project_guide/ tests/` (hygiene; no code change expected to affect them).
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Styling nav / footer / `.btn` links.** Already intentionally styled; untouched.
- **A global prose-link rule beyond `.hero-description`.** No other inline-prose links exist on the page today; revisit if links are added to feature cards or other prose.
- **Version bump / CHANGELOG entry.** None — doc-only CSS fix, no behavior change.

---

## Subphase Q-3: Pyve-managed-hosting cross-repo contract

Pins four cross-repo contracts that let Pyve host project-guide as a globally-shimmed tool in its toolchain venv, and adds pyve-managed-hosting awareness to project-guide's user-facing surfaces. Driver: Pyve's planned move from per-project `pip install project-guide` to a single toolchain-venv install with a `~/.local/bin/project-guide` shim (Pyve Story N.aw). See [`phase-q-pyve-toolchain-hosting.md`](phase-q-pyve-toolchain-hosting.md) for the contract and [`phase-q-subphase-3-pyve-hosting-plan.md`](phase-q-subphase-3-pyve-hosting-plan.md) for the full Q-3 plan.

Three of the four contracts already hold in code (install-location independence, `--version` stability, `.project-guide.yml` marker stability) — Q.l pins them as tested contracts. The fourth is genuinely new: branching template and CLI-output content on `pyve_installed` (Q.m), with a defensive `project-guide heal` warning when a legacy project-local install lingers (also Q.m, mirroring the P.o `go.md`-tracked warning pattern).

Bundled release at end-of-subphase as **v2.13.0** (minor — new behavior + new published contract surface). Three stories executed in document order; only `Q.n` carries the version in its title. **Story-letter continuity:** Q-2 closed at `Q.f` (v2.12.0), then `Q.g`–`Q.k` landed as post-release `code_direct` doc-fix tail stories under Q-2. Q-3 picks up at `Q.l` per the monotonic-continuation rule in `_phase-letters.md`. **No upstream dependency** — Q-1 (v2.11.0) and Q-2 (v2.12.0) have both shipped; Q-3 implementation can begin immediately after approval.

### Story Q.l: Cross-repo contract pinning — tests + documentation [Done]

**Problem.** Three of the four cross-repo contracts in [`phase-q-pyve-toolchain-hosting.md`](phase-q-pyve-toolchain-hosting.md) already hold in code but are not pinned by tests or published as documented contracts. Code-grounding audit confirms:

- **Install-location independence.** `Path.cwd()` is used uniformly across [cli.py:209](../../project_guide/cli.py), [cli.py:794–796](../../project_guide/cli.py), [cli.py:1035](../../project_guide/cli.py), [runtime.py:142](../../project_guide/runtime.py). Nothing reads from the package install location for per-project state.
- **`--version` surface.** Wired at [cli.py:89](../../project_guide/cli.py) via Click's `@click.version_option(version=__version__)`. Standard Click format (`"project-guide, version X.Y.Z"`) — pinnable.
- **`.project-guide.yml` marker.** Filename hard-coded in `Config.load()` / `Config.save()`; written at project root; carries `installed_version` and `target_dir` plus other Schema-2.0 fields.

Pyve Story N.aw will pin a minimum project-guide version once Q-3 ships; tests pinning the contract surface are what make that pin meaningful. Without tests + documented contracts, the three behaviors could drift in a future story without anyone noticing the cross-repo breakage until Pyve's CI flags it.

**Behavior (post-story).** Three test surfaces + two documentation surfaces.

- **Test: install-location independence.** `CliRunner().isolated_filesystem()` invokes `project-guide init` from a temp cwd; asserts `(tmp / ".project-guide.yml").exists()` and `(tmp / "docs/project-guide/go.md").exists()`; asserts no writes to the package install location. Same shape for `update` and `mode`.
- **Test: `--version` output format.** Invokes `project-guide --version`, asserts output matches `r"project-guide, version \d+\.\d+\.\d+\n?"`. The regex *is* the cross-repo contract Pyve pins against; changing the format requires a coordinated breaking change.
- **Test: `.project-guide.yml` marker shape.** After `init`, asserts the file is named exactly `.project-guide.yml` (no rename, no extension drift) at project root; `yaml.safe_load()` of its contents yields a dict containing **at minimum** `version` (schema), `installed_version`, `target_dir`, `current_mode`. Asserted-field set is the cross-repo subset — additional fields (`pyve_version`, `metadata_overrides`, …) may exist; their absence is not a contract violation.
- **Doc: `features.md` Cross-Repo Contracts section.** New subsection enumerating the four contracts with their guarding tests (or "implementation only — no test" for Q.m's awareness case).
- **Doc: `project-essentials.md` Pyve cross-repo contracts section.** Appended after the (Q-2-installed) "Pyve env-spec vendored-template contract" section. Documents the four contracts as architectural invariants. Two new Q-3 invariants beyond features.md: **(a) any rename of `.project-guide.yml` or removal of the contract fields is a coordinated breaking change** requiring a paired Pyve story; **(b) pyve detection is cached in `.project-guide.yml`'s `pyve_version` field at init time and not re-run at every CLI invocation** — `status`, help, template branches, and the heal defensive guard read the cached value, keeping commands cheap and predictable.

**Why these defaults.**

- **Q.l lands before Q.m.** Q.l pins already-correct behavior; Q.m adds new pyve-aware behavior. Pinning the foundation first means Q.m's new code can lean on the documented contract surface (e.g., Q.m's status footer reads `config.pyve_version`, which Q.l's marker-shape test pins as a stable field).
- **Three tests, three contracts.** Each contract maps to exactly one test; no test asserts multiple contracts. Keeps failure attribution unambiguous.
- **Regex over exact-string match for `--version`.** The exact-string approach (assert `output == "project-guide, version 2.13.0\n"`) would force every version bump to update the test. The regex pins the *shape* — what Pyve actually depends on — and tolerates the version number.
- **Required-field subset, not full schema, for `.project-guide.yml`.** Pyve pins against `installed_version` + `target_dir` (per the contract doc). Asserting the full Schema-2.0 field set would over-couple the test to internal evolution.
- **Two documentation homes, not one.** `features.md` documents the contract as a functional surface (what's promised); `project-essentials.md` documents it as an architectural invariant (what future LLMs must respect). Different reader audiences; both edits are small.

**Implementation:**
- [x] Author the three contract-pinning tests in a new `tests/test_cross_repo_contract.py`. *(One test per contract: install-location independence, `--version` format, `.project-guide.yml` marker shape.)*
- [x] Append "Cross-Repo Contracts" section to `docs/specs/features.md` enumerating all four contracts (the three pinned here + the pyve-managed-hosting awareness implemented in Q.m, documented in Q.l for completeness).
- [x] Append new "Pyve cross-repo contracts" section to `docs/specs/project-essentials.md` after the existing "Pyve env-spec vendored-template contract" section. Include invariants (a) and (b).
- [x] Run `pyve run project-guide update` to re-render `go.md` (the project-essentials.md addition flows through auto-render).
- [x] Spot-check the rendered new section in `docs/project-guide/go.md`.
- [x] Run `pyve test` — all new tests pass; existing suite remains green (589 passed, +3).
- [x] Run `pyve testenv run ruff check project_guide/ tests/`. *(Clean.)*
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Implementation note — `--version` test shape.** The `--version` contract is pinned in two robust pieces rather than a single literal-string match. Click 8.3's `version_option` memoizes the program name in a closure `nonlocal` on the *first* `--version` call in the process, so whichever test runs `--version` first pins the prog token for the whole session (`test_cli.py` does, as `"main"`) — CliRunner's `prog_name` cannot reliably read back `project-guide` in-process, and the testenv ships no console script for a subprocess check. The test therefore pins (a) the version-number **format** via `--version` (the part Pyve parses) and (b) the **program name** via the `pyproject.toml` `[project.scripts]` entry point (`project-guide = "project_guide.cli:main"`), which is the real source of the shipped binary's name. Together these pin the full `project-guide, version X.Y.Z` contract without depending on Click internals.

**Out of scope:**
- **Pyve-side minimum-version pin.** Pyve Story N.aw will pin `project-guide ≥ vX.Y.Z` after Q-3 ships; that edit lives in the Pyve repo.
- **Schema test of `.project-guide.yml`'s full field set.** Q.l asserts the cross-repo subset only; full-schema testing is `tests/test_config.py`'s job (existing round-trip tests cover it).
- **Test pinning Click's exit codes.** Already covered by existing CLI tests; no new assertion needed for Q.l.
- **CLI/template changes.** Bundled into Q.m.
- **Version bump / CHANGELOG entry.** Bundled into Q.n.

---

### Story Q.m: Pyve-managed-hosting awareness — templates, README, status footer, heal warning [Done]

**Problem.** `pyve_installed` is detected at `init` time ([cli.py:251–262](../../project_guide/cli.py)) and cached in `.project-guide.yml`, but its only consumer is `render.py:_read_pyve_essentials()` (auto-renders `pyve-essentials.md` into `go.md`). The flag is **not** consumed by:

- Onboarding install advice in the rendered `go.md` ([`_header-common.md`:6](../../project_guide/templates/project-guide/templates/modes/_header-common.md) says "After installing project-guide (`pip install project-guide`)..." unconditionally).
- The developer-reference page ([`developer/project-guide.md`:7](../../project_guide/templates/project-guide/developer/project-guide.md) — same shape, plus a pre-existing `project-guides` typo).
- The top-level [`README.md`](../../README.md) install section.
- `project-guide status` output (no footer naming the host).
- `project-guide heal` drift checks (no detection of a local-install footgun when pyve is the canonical host).

Under Pyve's toolchain-venv hosting (Pyve Story N.aw), `pip install project-guide` is wrong advice for users with pyve installed — the user runs `pyve self install` and pyve manages the install path. If a user adopts pyve-managed hosting *after* having previously run `pip install project-guide` into a project-local venv, both installs coexist; `which project-guide` resolves to whichever is first on `PATH`, and behavior diverges silently with version drift.

**Behavior (post-story).** Five surfaces gain pyve-awareness; all five are gated on the already-cached `pyve_installed` detection.

- **`_header-common.md`** branches the onboarding line on `pyve_installed`:
  - True: `"Pyve manages project-guide for you. From your project root, run `project-guide init` to scaffold the docs, then instruct your LLM as follows..."`
  - False: existing pip-install advice preserved.
- **`developer/project-guide.md`** branches the same way. Also fixes the existing `project-guides` typo inline.
- **`README.md`** gains a "Installation via pyve (recommended)" section above the existing pip-install section. One short paragraph: "If you use [pyve](https://pointmatic.github.io/pyve/), let pyve install project-guide globally for you — `pyve self install` provisions project-guide in pyve's toolchain venv and creates a `~/.local/bin/project-guide` shim. Otherwise, `pip install project-guide` per the section below." Standalone pip-install advice preserved.
- **`project-guide status` footer.** When `config.pyve_version is not None`, append a dim one-line footer: `"Managed by pyve v<version> (detected at init time)."` Matches the existing dim "Run 'project-guide update' to sync" hint convention. **No runtime re-detection** — reads cached config per Q.l's invariant (b).
- **`project-guide heal` defensive local-install warning.** When `config.pyve_version is not None` AND the running project-guide's `importlib.metadata.distribution("project-guide")` install location resolves to a descendant of `Path.cwd()` (e.g., under `<cwd>/.venv/`, `<cwd>/.pyve/envs/<name>/`) → emit stderr warning:
  ```
  ⚠ Local project-guide install detected at <path>.
    Pyve is configured to manage project-guide globally.
    Remove the local install with: pip uninstall project-guide
  ```
  Heal's auto-hook (P.b/c) carries the warning to every `project-guide` invocation including `--help` / `--version` until the user resolves it. **Silent-when-clean preserved** — heal stays silent on this axis when no local install is detected. **No auto-uninstall** — same wrapper-initiates-side-effects discipline as P.k / P.o.

**Why these defaults.**

- **`heal`, not `status`, for the local-install warning.** Mirrors the P.o `go.md`-tracked warning pattern exactly — `heal` detects a state requiring a user-initiated `pip`/`git` operation, emits a warning, never auto-fixes. Two advantages over a status-only surface: (i) per-invocation visibility via the auto-hook (the user sees it until they resolve it, not just when they remember to run `status`); (ii) precedent symmetry (heal already warns about another `pip`/`git`-resolvable state, namely tracked `go.md`; adding the local-install warning to the same surface keeps heal's job coherent).
- **`status` footer stays separate from `heal` warning.** Different signals at different lifecycle points: status footer is informational (one-time read-out of cached host state when the user deliberately checks); heal warning is defensive (per-invocation diagnostic of a drift state requiring user action). They surface different things; both stay.
- **Cached pyve detection, no runtime re-run.** Status reads `config.pyve_version`; heal's local-install check reads `config.pyve_version`. Neither re-invokes `pyve --version` per call. Trade-off: a user who installs pyve *after* `project-guide init` won't see the awareness until they re-run `init --force` (or a future `project-guide refresh-detection` surface — YAGNI today). Trade-off recorded in Q.l's `project-essentials.md` invariant (b).
- **Template branches via existing `pyve_installed` Jinja variable.** `render.py` already threads `pyve_installed` to the Jinja context. The branches use the existing variable — no new render-pipeline plumbing.
- **Typo fix folded into Q.m, not spun off.** `project-guides` → `project-guide` in `developer/project-guide.md` is a one-character drift fix in the same file we're already touching. Spinning it off would be churn.
- **README "recommended" framing, not "deprecated" framing.** The pip-install path is the canonical fallback for standalone users with no pyve. Calling it "deprecated" would alarm those users unnecessarily; "via pyve (recommended)" + "Otherwise, pip install" reads cleanly.

**Implementation:**
- [x] Edit `project_guide/templates/project-guide/templates/modes/_header-common.md` — Jinja-branch the onboarding line on `pyve_installed` (this template is rendered into `go.md`, so the `{% if %}` works).
- [x] Edit `project_guide/templates/project-guide/developer/project-guide.md` — host-agnostic install line + `project-guides`→`project-guide` typo fix. *(Adaptation: this `developer/` file is copied verbatim by `sync.py`, **not** Jinja-rendered, so a runtime branch is impossible — instead the line now names both install paths (pyve `pyve self install` / `pip install project-guide`). Also corrected the stale `docs/guides/project-guide.md` → `docs/project-guide/go.md` read target in the same sentence.)*
- [x] Edit `README.md` — add "Via pyve (recommended)" section above the existing pip-install section.
- [x] Edit `project_guide/cli.py` `status` command — append the pyve-detected footer when `config.pyve_version is not None`. *(Footer uses `_pyve_version_token()` to extract the bare version from the raw `pyve --version` string so it reads `Managed by pyve v2.6.2 …` rather than doubling the `pyve` prefix.)*
- [x] Edit `project_guide/cli.py` heal/auto-hook detection — add `_warn_if_local_install_under_pyve()`, wired into both `_run_pre_invoke_hook` and the `heal` command (beside `_warn_if_go_md_tracked`), following the P.o pattern. *(Refinement: detection requires the running package to be under cwd **and** inside a `site-packages` segment, so an editable source checkout — project-guide's own dogfood repo — is not flagged as a removable local install.)*
- [x] Add tests: `test_render.py` covers the `_header-common.md` branch for `pyve_installed=True`/`False`; `test_cli.py` covers the status footer (present/absent) and the heal local-install warning (fires for a site-packages install under pyve; silent for an editable checkout; silent when pyve absent).
- [x] Run `pyve run project-guide update` to propagate template edits to `docs/project-guide/`.
- [x] Spot-check rendered `go.md` for both branches. *(Render tests verify both deterministically; this repo's `go.md` — pyve detected — shows the pyve-managed branch with no raw Jinja leakage.)*
- [x] Run `pyve test` — 596 passed (+7).
- [x] Run `pyve testenv run ruff check project_guide/ tests/` — clean.
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Runtime pyve re-detection.** Status and heal both read cached `config.pyve_version`. A `project-guide refresh-detection` subcommand is YAGNI until field use surfaces the cache-staleness footgun.
- **Auto-`pip uninstall`.** Heal warns; user removes. Same discipline as P.k git-push and P.o `go.md` tracking.
- **Help-text expansion.** No `project-guide --help` text changes. Onboarding is surfaced via rendered `go.md` (template branches) and README. Help text stays terse.
- **Detection of conflicting pyve-managed installs across multiple toolchain venvs.** Pyve owns the toolchain-venv path policy; project-guide trusts it.
- **`docs/specs/cross-repo-contracts.md` as a dedicated file.** Contracts live in `features.md` (functional) and `project-essentials.md` (invariant) per Q.l's design.
- **Version bump / CHANGELOG entry.** Bundled into Q.n.

---

### Story Q.n: v2.13.0 Subphase Q-3 bundled release [Done]

**Problem.** Subphase Q-3 ships as one bundled release per the subphase phase-bundling option installed in Q.a. Stories Q.l and Q.m run unversioned; Q.n is the release-marker story that bumps the package and authors the CHANGELOG entry covering both.

**Behavior (post-story).** Version bumped to **v2.13.0** across the three canonical sites (`project_guide/version.py`, `pyproject.toml`, new `CHANGELOG.md` entry). The CHANGELOG entry describes Subphase Q-3's two themes as one bundled release: the cross-repo contract pinning (Q.l) and the pyve-managed-hosting awareness (Q.m).

**Why this default.**

- **v2.13.0 minor, not patch.** Pyve-managed-hosting awareness is new behavior (template branches + status footer + heal local-install warning); newly-published cross-repo contracts are a feature surface pyve pins against. Both are *feature additions* by the Version Cadence rule (`Feature or improvement → minor`).
- **Distinct release from Q-1's v2.11.0 and Q-2's v2.12.0.** Per the subphase phase-bundling pattern installed in Q.a, each subphase decides its own release shape; Q-3 ships as a separate minor bump because it's a discrete shippable bundle.
- **One bump, last story.** Same convention as Q.c / Q.f — Q.n is the only Q-3 story with a version in its title.
- **CHANGELOG entry covers both Q.l and Q.m** and cross-references [`phase-q-subphase-3-pyve-hosting-plan.md`](phase-q-subphase-3-pyve-hosting-plan.md) and [`phase-q-pyve-toolchain-hosting.md`](phase-q-pyve-toolchain-hosting.md) so future readers can reconstruct the cross-repo context (Pyve Story N.aw is the consuming-side counterpart).

**Implementation:**
- [x] Bump `project_guide/version.py` to `2.13.0`.
- [x] Bump `pyproject.toml` to `2.13.0`.
- [x] Add `## [2.13.0] - 2026-06-05` entry to `CHANGELOG.md` with `### Added` (cross-repo contract tests + docs, pyve-managed-hosting awareness, defensive local-install warning) and `### Changed` (the `developer/project-guide.md` host-agnostic/typo/path fix) subsections. References Q.l and Q.m; cross-references the Q-3 plan and the cross-repo contract doc.
- [x] Run `pyve test` — 596 passed.
- [x] Run `pyve testenv run ruff check project_guide/ tests/` — clean.
- [x] Flip story status `[Planned]` → `[Done]` and check off tasks.

**Out of scope:**
- **Git tag / PyPI publish.** Per the *Approval gate discipline* rule in [project-essentials.md](project-essentials.md), the LLM does not initiate git operations or releases. The developer pushes the tag and triggers publish on their own schedule.
- **End-of-subphase migration to a Q-4 planning session.** Q-4 entry is a separate developer-initiated decision; Q.n is just the release marker for Q-3.

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
