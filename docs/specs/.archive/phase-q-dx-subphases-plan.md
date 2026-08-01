# phase-q-dx-subphases-plan.md — project-guide (Python)

Phase Q plan: **DX Improvements & Subphase Support.**

Phase Q is an open-ended developer-experience phase. Two characteristics distinguish it from prior phases:

1. **It is the first phase to be *decomposed into subphases* up front.** The subphase pattern itself is introduced by Subphase Q-1 (self-applying: the templates that document subphasing are first written using it).
2. **It will accumulate ad-hoc subphases as DX needs surface.** Only Subphase Q-1 is fully scoped today; Q-2, Q-3, … are placeholders that will each enter via their own future `plan_production_phase` session, per the Step 4a pattern.

The phase will mix release shapes: some subphases will ship as bundled releases (per the Version Cadence phase-bundling option, extended per-subphase by the proposed pattern); some may carry one-off versioned stories. Each subphase decides its own shape when its stories are drafted.

---

## Subphase Overview

### Subphase Q-1 — Subphase Strategy & Pyve v2.8.0 Alignment (this planning session)

**Scope.** Two coherent units of work, drafted as stories below:

1. Introduce the **subphase decomposition pattern** documented in [`docs/specs/subphase-strategy-for-large-phases.md`](subphase-strategy-for-large-phases.md). Template edits to `plan-production-phase-mode.md` (new Step 4a), `_phase-letters.md` (new "Subphases" section), `_header-common.md` (scope-of-authority sentence on subphase headings), and `plan-phase-mode.md` (pre-1.0 parenthetical pointing at Q-1's Step 4a).
2. **Pyve v2.8.0 alignment.** Refresh the bundled `templates/artifacts/pyve-essentials.md` (auto-rendered into every consumer's `go.md`) and this project's dogfooded `docs/specs/project-essentials.md` to reflect Pyve v2.8.0's named-test-environments layout (`.pyve/testenvs/<name>/{venv,conda}/`), the `[tool.pyve.testenvs]` declarative config, and the renamed commands (`pyve check` replacing `doctor`/`validate`; `pyve update` as the non-destructive refresh path).

**Release shape.** Bundled release at end-of-subphase as **v2.11.0** — minor bump, fully additive doc/template changes. The last story of Q-1 owns the bump (per the subphase phase-bundling option proposed in the change request).

### Subphase Q-2 — `plan_envs` mode (Pyve env-spec authoring surface)

**Scope.** Add a new sequence mode `plan_envs` that guides the developer through enumerating named environments (root + test envs), their backends, frameworks, packaging, and advisory fields. Authors `docs/specs/env-dependencies.md` from a bundled artifact template that vendors Pyve's `env-dependencies-template.md` at `spec_version: "3.0"`. Slotted into the canonical planning sequence as `plan_tech_spec → plan_envs → plan_stories`.

**Driver.** Pyve's transition from v2.8 (named test envs) to v3.0 (named-env + plugin architecture) raises env topology to a discrete planning concern worth its own mode. The cross-repo contract from Pyve's [N.ao spike](phase-q-wizard-env-contract.md) — closed-vocabulary trichotomy (known+implemented / known+advisory / unknown→error) and the vendored-template invariant — is the authoritative shape project-guide consumes.

**Release shape.** Bundled release at end-of-subphase as **v2.12.0** — minor (new feature: new mode + new artifact). Three stories (Q.d / Q.e / Q.f) executed in document order; only Q.f carries the version in its title.

**Full plan.** [`phase-q-subphase-2-plan-envs-plan.md`](phase-q-subphase-2-plan-envs-plan.md) — gap analysis, feature requirements, technical changes, breaking-change negotiation result, anticipated version bump target, out-of-scope walk, implementation strategy, acceptance criteria.

### Subphase Q-3 — Pyve-managed-hosting cross-repo contract

**Scope.** Pin four cross-repo contracts that let Pyve host project-guide as a globally-shimmed tool in its toolchain venv (Pyve Story N.aw), and add pyve-managed-hosting awareness to project-guide's user-facing surfaces (template install-advice, README, `status` footer, `heal` local-install drift warning).

**Driver.** Pyve's planned move from per-project `pip install project-guide` (into each project's Python env) to a single toolchain-venv install with a `~/.local/bin/project-guide` shim. Three of the four contracts already hold in code (install-location independence, `--version` stability, `.project-guide.yml` marker stability) — Q-3 pins them as tested contracts so Pyve can pin a minimum project-guide version. The fourth is genuinely new: branching template and CLI-output content on `pyve_installed` so the user sees pyve-managed-hosting guidance when pyve is the host, and a defensive `heal` warning when a legacy project-local install lingers.

**Release shape.** Bundled release at end-of-subphase as **v2.13.0** — minor (new behavior + new published contract surface). Three stories (Q.l / Q.m / Q.n) executed in document order; only Q.n carries the version in its title. (Letters Q.g–Q.k were taken by post-Q-2-release `code_direct` doc-fix tail stories; Q-3 picks up at the next monotonic letter Q.l.)

**Full plan.** [`phase-q-subphase-3-pyve-hosting-plan.md`](phase-q-subphase-3-pyve-hosting-plan.md) — gap analysis, feature requirements, technical changes, breaking-change negotiation result, anticipated version bump target, out-of-scope walk, implementation strategy, acceptance criteria.

### Subphase Q-4 and beyond — to be defined

Subphase Q-4+ remain intentionally undefined. **Story breakdown deferred to their own future `plan_production_phase` sessions** per the (Q-1-installed) Step 4a pattern. Each future subphase will be triggered by a concrete DX need: a pain point, a downstream consumer signal, an integration gap. Possible themes (non-binding, illustrative only):

- LLM workflow guidance refinements
- Mode-template ergonomic improvements
- Status / check / heal output polish beyond Q-3's scope
- Further external-tool integration patterns (e.g., the deferred `project-guide check` integrity command from `Future`)
- Dogfooded `env-dependencies.md` for project-guide itself (post-Q-2 follow-up if `plan_envs` field use surfaces template gaps)

When a Q-4+ theme crystallizes, the developer re-invokes `project-guide mode plan_production_phase` to scope that subphase. The Q-1-installed templates will guide the LLM to (a) recognize this is a mid-phase re-invocation, (b) add the new `## Subphase Q-N:` heading rather than a new `## Phase` heading, (c) continue story letters monotonically from where the prior subphase left off.

---

## Gap Analysis (Subphase Q-1 only)

### No idiomatic structure for large-phase decomposition

When a phase is genuinely too large to draft every story in one planning session, the current `plan_phase` / `plan_production_phase` templates offer no idiomatic decomposition. Field experience from Pyve Phase N (drafted 2026-06-01) surfaced the problem concretely:

- The developer manually instructed the LLM on subphase IDs (`N-1` form), heading level (`##`), monotonic story-letter continuation across subphase boundaries, multi-release exception, deferred-story breakdown, and 3-level story-ID depth cap. None of that is in the templates.
- Every future `plan_production_phase` invocation hitting a large phase would have to re-bootstrap the same conventions; pattern drift across sessions is guaranteed.
- The existing `_header-common.md` *Scope of authority* rule forbids creating new `## Phase` headings outside `plan_phase` / `plan_production_phase`. Without an articulated subphase concept, the LLM has no way to distinguish "internal structure to my phase" from "new phase" — natural fallback (jumping to the next phase letter for what is conceptually still the current phase) corrupts the phase-letter sequence.
- Large phases sometimes need multiple release tags (architectural cutover + post-release polish). The current "one phase = one bundled release" wording in `stories.md`'s Version Cadence section doesn't acknowledge this.

Full motivation and proposed template edits live in [`docs/specs/subphase-strategy-for-large-phases.md`](subphase-strategy-for-large-phases.md).

### Pyve integration drift after Pyve v2.8.0

Project-guide's bundled `templates/artifacts/pyve-essentials.md` (auto-rendered into every consumer's `go.md` under `## Project Essentials > ### Pyve Essentials` via FR-13) and this project's dogfooded `docs/specs/project-essentials.md` both reference Pyve invocation patterns that pre-date Pyve v2.8.0:

- **Testenv path.** Both files reference `.pyve/testenv/venv/` (singular `testenv`). Pyve v2.8.0 (Story M.h in Pyve's `stories.md`) moved this to `.pyve/testenvs/<name>/{venv,conda}/` (plural, name-keyed); the default env name is `testenv`, so the v2.8.0 default path is `.pyve/testenvs/testenv/venv/`. Existing projects migrate transparently on first `pyve update` or `pyve test`/`pyve testenv …` call, so the on-disk path will follow consumers automatically — but the documentation needs to land at the new shape so new consumers see the post-2.8 reality from day one.
- **Named test environments.** Pyve v2.8.0 introduced declarative `[tool.pyve.testenvs]` in `pyproject.toml`, supporting per-env backend (`venv` / `micromamba` / `inherit`), source (`requirements` / `extra` / `manifest`), and lifecycle (`lazy = true`). Neither file mentions this. The default-`testenv` workflow remains identical, so existing project-guide guidance still works — but recipes for projects with multiple test environments (matrix testing, conda-backed integration envs) are absent.
- **Renamed commands.** Pyve v2.0 (Story H.e.8a) hard-removed `pyve doctor` and `pyve validate` in favor of `pyve check` (CI-safe 0/1/2 exit codes). v2.0 (Story H.e.2) also introduced `pyve update` as the non-destructive upgrade subcommand, replacing the removed `pyve init --update` flag. project-guide's docs predate both renames; an LLM following the current guide might type a removed command and get the legacy-flag-catch error.

Net effect: no consumer is *broken* (Pyve's migration shims and stable command surface protect them), but the LLM-facing guidance is stale enough that new project-guide users following it will see deprecation noise and miss the modern declarative-config affordances.

---

## Feature Requirements (Subphase Q-1)

### Q-1-FR-1: Subphase pattern in `plan_production_phase`

A new **Step 4a (Subphase decomposition — optional)** inserted between current Step 4 and Step 5 of `templates/modes/plan-production-phase-mode.md`. The step:

1. Lists trigger heuristics (developer signal "this is huge"; gap-analysis rows > ~7; technical-changes layers > ~4; breaking changes > ~4; major bump + polish-shouldn't-block signal).
2. Describes the subphase-decomposition output: a "Subphase overview" section in the phase plan enumerating each `X-1`, `X-2`, … with a one-paragraph scope summary, deferred-story-breakdown marker for X-2+, multi-release exception line when applicable.
3. States that the initial session drafts stories only for Subphase 1.
4. States that re-entering `plan_production_phase` mid-phase to draft a later subphase's stories is the canonical pattern — not a misuse.
5. Explicitly allows skipping Step 4a when the phase is small/medium (existing single-block path stays default).

### Q-1-FR-2: Subphase ID and structure rules in `_phase-letters.md`

A new section after "Story sub-letters" / before "Sub-numbered stories" in `templates/modes/_phase-letters.md`:

- **Subphase IDs** use arabic numerals with a hyphen separator (`N-1`, `N-2`, …). The hyphen is the deliberate non-colliding separator vs. story IDs (`N.a`), sub-numbered stories (`N.m.1`), and phase letters (`AA`).
- **Subphase headings** use `##` (peer of `## Phase`, `## Future`).
- **Story letters continue monotonically** across subphase boundaries. Sub-letters reset only at the phase boundary.
- **Story breakdown is per-subphase**; subsequent subphases get their own future `plan_production_phase` sessions.
- **3-level story-ID depth limit holds.** `N.b.1` still allowed; `N.b.1.1` still forbidden. Subphase IDs do not consume a story-ID level.
- Cross-reference back to `plan_production_phase` Step 4a for the when-to-introduce-subphases policy.

### Q-1-FR-3: Scope-of-authority clarification in `_header-common.md`

The existing **Scope of authority — structural changes to `stories.md`** rule (`_header-common.md` line referencing "Phase creation … is the exclusive job of `plan_phase` (or `plan_production_phase` post-1.0)") gains one clarifying sentence: subphase headings (`## Subphase X-N:`) under an existing `## Phase X:` heading are structural sub-groupings, **not** new phases, and may be added by subsequent `plan_production_phase` invocations under the same phase's authority.

This closes the loophole where an LLM, drafting a Q-2 subphase mid-phase, would otherwise read the scope-of-authority rule as forbidding the new `##` heading.

### Q-1-FR-4: Pre-1.0 parenthetical in `plan-phase-mode.md`

One sentence appended to `plan-phase-mode.md` Step 4 (or equivalent location): subphasing is *available* in `plan_phase` for pre-1.0 phases, but pre-1.0 phases rarely reach the threshold; default is to draft every story in one session. Points at `plan_production_phase` Step 4a for the canonical pattern.

### Q-1-FR-5: `pyve-essentials.md` refresh for Pyve v2.8.0

Bundled artifact `project_guide/templates/project-guide/templates/artifacts/pyve-essentials.md` is updated to reflect Pyve v2.8.0:

- **Testenv path.** Replace `.pyve/testenv/venv/` references with `.pyve/testenvs/testenv/venv/` (default env name) and note that Pyve v2.8.0 generalized this to `.pyve/testenvs/<name>/{venv,conda}/` for declared named envs.
- **Named test environments (short).** One-paragraph mention of `[tool.pyve.testenvs]` declarative config, with a pointer at Pyve's `pointmatic.github.io/pyve/testing/#named-test-environments` for the full schema. Project-guide doesn't duplicate Pyve's schema; it just makes consumers aware the surface exists so they don't randomly invent their own test-env layout.
- **`pyve check` (replaces `pyve doctor` / `pyve validate`).** Where the current rules cite Pyve diagnostic commands, replace with `pyve check`.
- **`pyve update` mention.** Note that `pyve update` is the non-destructive refresh path (preserves env, refreshes managed files + project-guide scaffolding), distinct from `pyve init --force` (destructive rebuild).

Rule shapes (two-environment pattern, canonical invocation forms, `python` vs `python3`, `requirements-dev.txt` convention, editable-install/testenv guidance, LLM-internal vs. developer-facing invocation) are preserved unchanged — they remain accurate against Pyve v2.8.0. The edits are surgical, not a rewrite.

**Auto-render flow guarantee.** Because `pyve-essentials.md` is read by `render.py` at every `project-guide mode <name>` invocation and rendered into the consumer's `go.md` under `## Project Essentials > ### Pyve Essentials`, every consumer picks up the refreshed content on the next mode switch with no action required. No scaffold-time migration step.

### Q-1-FR-6: `project-essentials.md` (dogfood) Pyve invocation refresh

This project's own `docs/specs/project-essentials.md` § "Pyve Essentials" is rendered by the same auto-render path described in Q-1-FR-5 (see the `### Pyve Essentials` block in [`go.md`](../project-guide/go.md) at lines 211–272 of today's render — it's the bundled-artifact body, not a hand-authored project section). Reviewed for completeness; if Q-1-FR-5's edits to the bundled `pyve-essentials.md` are sufficient, no per-project edits are needed and Q-1-FR-6 collapses into a noop confirmation. If this project has dogfood-specific Pyve guidance outside the auto-rendered block, those entries get the same refresh as Q-1-FR-5. The story authoring Q-1-FR-6 explicitly verifies which case applies before deciding the scope.

---

## Technical Changes (Subphase Q-1)

- **Edits only to templates and documentation.** No `project_guide/` Python module changes, no new dependencies, no new CLI commands, no metadata schema changes.
- **Files touched (source of truth, not installed copies):**
  - `project_guide/templates/project-guide/templates/modes/plan-production-phase-mode.md`
  - `project_guide/templates/project-guide/templates/modes/_phase-letters.md`
  - `project_guide/templates/project-guide/templates/modes/_header-common.md`
  - `project_guide/templates/project-guide/templates/modes/plan-phase-mode.md`
  - `project_guide/templates/project-guide/templates/artifacts/pyve-essentials.md`
  - `docs/specs/project-essentials.md` (only if Q-1-FR-6 finds dogfood-specific entries needing refresh)
  - `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` — bumped once, at the end of Q-1's release story.
- **Installed-copy propagation.** Per the dogfooding rule, after editing source-of-truth templates the developer runs `pyve run project-guide update` to propagate to `docs/project-guide/`. The auto-heal hook (P.b/c) handles fresh clones transparently.
- **Test impact.** The parametrized render-mode test (`tests/test_render.py`) already covers every mode template's render path. Edits in Q-1 are content additions; no new test cases required, but the existing suite must still pass. The dogfood `pyve test` run is the verification gate.

---

## Production Concerns

**None for Subphase Q-1.** Pure template/doc work; no runtime code paths touched, no new I/O or network operations, no new external CLI dependencies, no schema migrations, no security surface. Future Q-N subphases will be re-evaluated at their own `plan_production_phase` sessions; this section gets revisited per-subphase.

---

## Anticipated Breaking Changes

**None for Subphase Q-1.**

- The **subphase pattern is opt-in.** Phases that don't subphase produce identical `stories.md` output to today. No existing phase plan, `stories.md`, or rendered `go.md` is invalidated. Parser-safe: subphase headings use `##` (which the rendered docs already handle); subphase IDs use a hyphen separator that doesn't collide with story IDs or phase letters; consumers grepping `## Phase` or `### Story X.y` continue to work unchanged.
- The **`pyve-essentials.md` refresh** is bundled-artifact content. Because `render.py` reads it on every mode switch, every consumer picks up the refreshed content automatically on their next `project-guide mode <name>` (or auto-heal hook fire). No scaffold-time migration step, no consumer-facing breaking surface.

Walked the change-request items in Step 5 (substantive vs. technically-but-trivially breaking) — every item came up "none." No version-bump escalation triggered.

---

## Anticipated Version Bump Target

**v2.11.0 — minor.** Fully additive (subphase pattern is opt-in; pyve-essentials refresh is bundled content with auto-render). Bundled release at end of Subphase Q-1; bumped exactly once on the last story.

---

## Out of Scope

Walked at the gate; deferred items:

- **PR-based workflow / branch protection / mandatory PR-gated CI.** Three production-readiness checklist items declined at the gate via explicit override. Re-flagged on the next `plan_production_phase` invocation.
- **Subphase Q-2, Q-3, …** All future Phase Q subphases are explicitly out of scope for this planning session. Each will be drafted via its own future `plan_production_phase` session per the Q-1-installed Step 4a pattern.
- **Programmatic enforcement of the subphase pattern.** No CLI command (e.g., a hypothetical `project-guide subphase add Q-2`) — the pattern is LLM-readable template guidance only. A future automation story may revisit if field use shows the rule alone isn't enough.
- **Migration tooling for existing phase plans.** No archive plans are being retroactively re-decomposed into subphases. Phase N (the Pyve worked example) stays as drafted in its own repo; no project-guide-side action.
- **`project-guide check` integrity command** (in `Future`). Already-deferred; not part of Q-1.
- **`pyve testenv` advanced-recipe documentation** in `pyve-essentials.md`. Q-1-FR-5 deliberately keeps the named-testenv mention to a one-paragraph pointer at Pyve's own docs. Project-guide does not duplicate Pyve's schema.
- **Cross-link from `pyve-essentials.md` to a future Pyve Phase N worked example.** Optional fourth Q-1 scope item discussed at the gate; deferred until Pyve N ships and the worked-example artifact paths are stable. Q-2+ candidate.

---

## Implementation Strategy

Three stories in Subphase Q-1, executed in document order:

1. **Q.a — Subphase strategy pattern template installation.** All four template edits (plan-production-phase, _phase-letters, _header-common, plan-phase) land together so the pattern is self-consistent from the moment it appears. Single coherent unit.
2. **Q.b — Pyve v2.8.0 alignment.** Refresh `pyve-essentials.md` (bundled artifact); confirm/refresh `docs/specs/project-essentials.md` (dogfood) if Q-1-FR-6 finds dogfood-specific entries. Single coherent unit (both files about the same Pyve v2.8.0 surface).
3. **Q.c — v2.11.0 Subphase Q-1 bundled release.** Bumps `project_guide/version.py`, `pyproject.toml`, adds `## [2.11.0]` CHANGELOG entry covering Q.a + Q.b. Closes Subphase Q-1.

Stories within Subphase Q-1 carry **no version in their title** until Q.c (the release story) — consistent with the proposed subphase phase-bundling option. Q.c's title carries `v2.11.0`.

---

## Acceptance Criteria (Subphase Q-1)

1. New `plan_production_phase` invocations on phases triggering the subphase heuristics generate a "Subphase overview" section in the phase plan and draft stories only for Subphase 1.
2. Subphase headings (`## Subphase X-N:`) and IDs (`N-1`, `N-2`, …) render cleanly through the existing Jinja2 pipeline; the parametrized render-mode test passes.
3. The auto-rendered `### Pyve Essentials` block in every `go.md` reflects Pyve v2.8.0's testenv path, mentions `[tool.pyve.testenvs]`, and cites `pyve check` / `pyve update` instead of the removed `pyve doctor` / `pyve validate` / `pyve init --update`.
4. This project's dogfooded `pyve test` and `pyve testenv run ruff check` both pass on the v2.11.0 commit.
5. CHANGELOG.md `## [2.11.0]` entry dated, describes the subphase pattern and Pyve v2.8.0 alignment as one bundled release.
