# phase-q-subphase-2-plan-envs-plan.md — project-guide (Python)

Subphase Q-2 plan: **`plan_envs` mode — Pyve env-spec authoring surface.**

Subphase Q-2 of [Phase Q (DX Improvements & Subphase Support)](phase-q-dx-subphases-plan.md). Adds a new sequence mode `plan_envs` that guides the developer through enumerating, scoping, and documenting the named environments a Pyve-managed repo needs (root + test envs, with closed-vocabulary attributes). The mode authors `docs/specs/env-dependencies.md` from a bundled artifact template that vendors Pyve's `spec_version: "3.0"` closed vocabulary.

Companion inputs digested for this planning session:
- [`phase-q-wizard-env-contract.md`](phase-q-wizard-env-contract.md) — the cross-repo contract from Pyve. Pyve owns the env-spec schema, version, and closed vocabulary; project-guide consumes and never invents values.
- [`phase-q-plan-envs-mode-roughdraft.md`](phase-q-plan-envs-mode-roughdraft.md) — Pyve-perspective rough draft of the mode instructions. Adapted into project-guide's sequence-mode shape during Story Q.d.
- [`phase-q-plan-envs-mode-env-dependences-artifact-roughdraft.md`](phase-q-plan-envs-mode-env-dependences-artifact-roughdraft.md) — Pyve-perspective rough draft of the artifact template. Adapted into project-guide's artifact-template format during Story Q.d.

---

## Gap Analysis (Subphase Q-2)

### No mode for env planning

Project-guide's planning sequence today (`plan_concept` → `plan_features` → `plan_tech_spec` → `plan_stories`) covers problem space, behavior, architecture, and implementation breakdown, but leaves **environment topology** unaddressed. For a Pyve v2.8+ project (let alone Pyve v3.0's named-env + plugin architecture), the question "how many environments does this repo need, with what backends, frameworks, and packaging?" is a discrete planning decision worth its own mode. Currently the developer either bootloads the decision into `plan_tech_spec` (overloading that mode's architecture focus), drops it on `plan_stories` (decisions emerge mid-implementation), or omits it entirely (drift between live `pyve.toml` and intended topology accumulates silently).

### `env-dependencies.md` has no template home

Pyve's [N.ao spike](phase-q-wizard-env-contract.md) introduced `docs/specs/env-dependencies.md` as the authored point-in-time env-spec artifact (peer of `features.md` / `tech-spec.md`). Project-guide has no bundled template for it, no mode that authors it, no metadata wiring that names it. Without those three pieces, every consumer hand-rolls the artifact (drift across projects) or skips it (drift between intent and `pyve.toml`).

### Spec-version tracking has no codified pattern

Per the contract, **the bundled `env-dependencies.md` template is a vendored copy of Pyve's `env-dependencies-template.md` at a pinned `spec_version`** (today: `"3.0"`). When Pyve bumps the template (new vocabulary value, §4 shape change), project-guide must do a refresh story — the same pattern Subphase Q-1 used for `pyve-essentials.md`'s Pyve v2.8.0 alignment. This refresh-story protocol is new to project-guide and needs to be documented as an invariant in `project-essentials.md` so future LLMs don't try to invent values or "improve" the template independent of Pyve's release cadence.

### Spec-doc drift around mode count and naming

Audit during Q-2 planning surfaced pre-existing drift in `concept.md` and `features.md`:

- `concept.md` Scope claims "15 modes" but lists 14 modes + a future `code_production`. The list uses retired names: `project_scaffold` (current: `scaffold_project`), `code_velocity` (current: `code_direct`).
- `features.md` FR-1 modes table lists 15 rows but **omits `plan_production_phase`** — the mode being used to author this very planning session. Actual `.metadata.yml` mode count is 16 (15 table rows + `plan_production_phase`).
- Post-Q-2 the count becomes **17** (adding `plan_envs`).

Drift is small but cumulative; folding the cleanup into Q.e's spec-sync story keeps Q-2 self-consistent (the new mode lands in already-correct surrounding documentation).

---

## Feature Requirements (Subphase Q-2)

### Q-2-FR-1: `plan_envs` mode template

A new sequence-mode template at `project_guide/templates/project-guide/templates/modes/plan-envs-mode.md`, adapted from the Pyve-perspective rough draft. Follows the existing `plan_concept` / `plan_features` / `plan_tech_spec` shape:

- **Header**: includes `_header-sequence.md` partial (standard sequence-mode wrapper).
- **Mode description**: one-paragraph statement of purpose — guide the developer through enumerating named environments (root + test envs), their purposes, backends, languages, frameworks, packaging, and advisory fields; output is `docs/specs/env-dependencies.md`.
- **Prerequisites**: `docs/specs/features.md` and `docs/specs/tech-spec.md` must exist. The mode infers env requirements from those specs plus the codebase.
- **Steps** (2-phase per the rough draft):
  1. Read existing specs (`features.md`, `tech-spec.md`, optionally `README.md`, `CONTRIBUTING.md`, CI/CD workflows, container manifests). Skim the codebase for env-shape signals (test directories, build artifacts, language mix).
  2. Determine env topology: how many environments, their purposes, backends, frameworks. Apply the closed-vocabulary trichotomy — known+implemented, known+advisory (no-op), or hard error. Never invent vocabulary values.
  3. Generate `docs/specs/env-dependencies.md` from the bundled template at `templates/artifacts/env-dependencies.md`. Fill every `<placeholder>`, resolve every `<!-- HOW TO FILL -->` comment, omit the template's How-To section from the rendered output.
  4. Present for developer approval; iterate until approved.
  5. End-of-mode hint: switch to `plan_stories` for implementation breakdown.
- **Closed-vocabulary discipline note**: an explicit reminder that backend / language / framework / packaging / app_type values come from the bundled template's §2 glossary (vendored from Pyve at `spec_version: "3.0"`); a value outside the closed set is a spec violation, not a creative choice. If a needed mechanism is missing from the vocabulary entirely, file a Pyve change-request per the artifact's §8 — do not invent a value.

### Q-2-FR-2: `env-dependencies.md` bundled artifact template

A new artifact template at `project_guide/templates/project-guide/templates/artifacts/env-dependencies.md`, adapted from the rough draft. Section structure (§0 How-To through §9 Change Log) is preserved; project-guide-specific adjustments:

- **`spec_version: "3.0"`** hard-coded at the §4.0 machine-readable YAML block. Bumps to this value are governed by the **vendored-template invariant** documented in Story Q.e's `project-essentials.md` append (new fact).
- **§0 How To Use This Template** stays in the bundled artifact (instructional guidance) but is omitted from the rendered output (per the mode's Step 3 — "omit the template's How-To section from the rendered output"). This matches the existing `concept.md` / `features.md` / `tech-spec.md` pattern.
- **Pyve-internal path references removed**: the rough draft says "copy this file to `pyve-environment-dependencies-repo_<repo_name>.md`" and references Pyve-internal docs. Project-guide replaces those with the canonical `docs/specs/env-dependencies.md` filename and project-guide-style cross-references (links to `concept.md`, `features.md`, `tech-spec.md`, etc., as the other artifacts do).
- **Cross-reference to `go.md`** added per the project-guide artifact convention — "For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see `docs/project-guide/go.md`."
- **Closed vocabulary tables** (§2's `app_type` / `packaging` / `frameworks` / `languages` / backend categories) are preserved verbatim from the rough draft at `spec_version: "3.0"`. These are the load-bearing content of the vendored template; rewording them risks drift from Pyve's authoritative vocabulary.
- **Header comment** added at the top of the file: `<!-- Vendored from Pyve env-dependencies-template.md at spec_version "3.0". Closed vocabulary is Pyve-owned; project-guide refreshes via a dedicated story when Pyve bumps. See docs/specs/project-essentials.md → "Pyve env-spec vendored-template contract" for the protocol. -->`

### Q-2-FR-3: `.metadata.yml` mode wiring

Add a new `plan_envs` mode definition to `project_guide/templates/project-guide/.metadata.yml`. Slotted between `plan_tech_spec` and `plan_stories`. Confirmed sequence change: `plan_tech_spec.next_mode` flips from `plan_stories` to `plan_envs`; `plan_envs.next_mode` is `plan_stories`.

```yaml
- name: plan_envs
  info: Define named environments and their dependencies
  description: Guide the developer through enumerating named environments (root + test envs), backends, frameworks, packaging, and advisory fields. Authors docs/specs/env-dependencies.md from the vendored Pyve env-spec template at spec_version "3.0".
  sequence_or_cycle: sequence
  generation_type: document
  mode_template: modes/plan-envs-mode.md
  next_mode: plan_stories
  artifacts:
    - file: docs/specs/env-dependencies.md
      action: create
  files_exist:
    - docs/specs/features.md
    - docs/specs/tech-spec.md
```

Mode-listing category: **Project Planning** (the existing category for `plan_concept` / `plan_features` / `plan_tech_spec` / `plan_stories` / `plan_phase` / `plan_production_phase`). Listing position controlled by mode order in `.metadata.yml`; `plan_envs` is inserted immediately after `plan_tech_spec`.

### Q-2-FR-4: Spec doc sync (`concept.md`, `features.md`)

Add the new mode to the project's own spec documents:

- **`features.md` FR-1 modes table**: add `plan_envs` row (sequence). Add `plan_production_phase` row (drift catch-up). Refresh count "**15 total**" → "**17 total**".
- **`concept.md` Scope statement**: update mode list to current names (`scaffold_project`, `code_direct`), add `plan_envs` and `plan_production_phase`, refresh count. Future `code_production` line preserved as-is.
- **`tech-spec.md`**: no direct mode enumeration; auto-render flow remains correct. Cross-reference updates only if any link rot is discovered during the edit.

### Q-2-FR-5: `project-essentials.md` — Pyve env-spec vendored-template contract

New section appended to `docs/specs/project-essentials.md` documenting the cross-repo invariant:

- **Vendored template, Pyve-owned vocabulary.** The bundled `env-dependencies.md` artifact is a vendored copy of Pyve's `env-dependencies-template.md` at a pinned `spec_version` (currently `"3.0"`). Pyve owns the closed vocabulary (`backend` / `languages` / `frameworks` / `packaging` / `app_type`) and the §4 schema; project-guide consumes.
- **Trichotomy contract.** Every value at every axis is exactly one of: **known + implemented** (Pyve materializes), **known + advisory** (Pyve records + surfaces, never materializes — the no-op class), **unknown** (spec violation → hard error). Project-guide's `plan_envs` mode emits only spec_version-conformant values — no inventing.
- **Refresh-story protocol.** When Pyve publishes a new template version (new vocabulary value, §4 shape change, or `spec_version` bump), project-guide does a dedicated refresh story — same shape as Subphase Q-1's `pyve-essentials.md` v2.8.0 alignment story (Q.b). The refresh story re-vendors the template, bumps the `spec_version` reference, and CHANGELOG-entries the alignment.
- **Authoritative source pointer**: Pyve's `docs/specs/project-guide-requests/env-dependencies-template.md` (in the Pyve repo) is the upstream.
- **Cross-reference**: the existing `### Pyve Essentials` section in `project-essentials.md` is about Pyve *invocation* (workflow / commands); the new section is about Pyve *env-spec vocabulary* (data contract). They are complementary, not overlapping.

---

## Technical Changes (Subphase Q-2)

- **Edits only to templates, metadata, and spec documentation.** No `project_guide/` Python module changes; no new dependencies; no new CLI commands; no `.project-guide.yml` schema changes; no `SCHEMA_VERSION` bump.
- **Files touched** (source of truth, not installed copies):
  - **Created**: `project_guide/templates/project-guide/templates/modes/plan-envs-mode.md`
  - **Created**: `project_guide/templates/project-guide/templates/artifacts/env-dependencies.md`
  - **Edited**: `project_guide/templates/project-guide/.metadata.yml` (add `plan_envs` block; flip `plan_tech_spec.next_mode`)
  - **Edited**: `docs/specs/concept.md` (Scope mode list + count)
  - **Edited**: `docs/specs/features.md` (FR-1 modes table + count)
  - **Edited**: `docs/specs/project-essentials.md` (new section on Pyve env-spec vendored-template contract)
  - **Bumped**: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` — once, at the end of Q-2's release story (Q.f).
- **Installed-copy propagation.** After editing the source-of-truth templates and metadata, the developer runs `pyve run project-guide update` to propagate to `docs/project-guide/`. The auto-heal hook (P.b/c) handles fresh clones.
- **Test impact.** The parametrized render-mode test (`tests/test_render.py`) iterates every mode in `.metadata.yml`. Adding `plan_envs` is picked up automatically; no new test cases authored, but the existing suite must still pass on the v2.12.0 commit. Same for any `_metadata` test that asserts mode count — likely a one-line constant bump if such an assertion exists.

---

## Production Concerns

**None for Subphase Q-2.** Pure template / metadata / doc work; no runtime code paths touched, no new external CLI dependencies, no `.project-guide.yml` schema changes, no I/O or network operations. Same posture as Q-1 (Subphase Q-2 confirmed at the gate to have no security / performance / reliability concerns).

---

## Anticipated Breaking Changes

Walked at Step 5 — one item, judged technically-but-trivially breaking:

### Sequence change: `plan_tech_spec.next_mode` flips from `plan_stories` to `plan_envs`

Project-guide's `project-guide mode <name>` command and the `_header-sequence.md` "next mode" hint use the `next_mode` field from `.metadata.yml`. Today, a developer completing `plan_tech_spec` sees `project-guide mode plan_stories` recommended. Post-Q-2, they see `project-guide mode plan_envs` recommended.

**Is it substantively breaking?** No.
- **No existing project is mid-flight in that exact transition.** Existing consumers have either passed `plan_tech_spec` already (their `current_mode` is `plan_stories` or downstream, unaffected), or have not yet reached it (they get the new recommendation cleanly).
- **The recommendation is advisory, not mandatory.** A developer can always override with the explicit mode name: `project-guide mode plan_stories` continues to work unchanged.
- **The mode is opt-in.** A consumer who doesn't want env planning runs `plan_stories` directly. The new `plan_envs` mode never executes without an explicit invocation.

**Judgment: technically-but-trivially breaking — non-breaking for semver purposes.** Minor bump suffices.

No other items.

---

## Anticipated Version Bump Target

**v2.12.0 — minor.** New feature (new sequence mode + new artifact template). Bundled release at end of Subphase Q-2; bumped exactly once on the last story (Q.f).

Subphase Q-2 ships its own release, per the multi-release-subphase pattern proposed in Q-1's subphase strategy. Subphase Q-1 = v2.11.0; Subphase Q-2 = v2.12.0.

---

## Out of Scope

Walked at the gate; deferred items:

- **Pyve-side F4/F5/F6 work.** `pyve env sync`, the `.project-guide.yml` contract-guard test, the closed-vocabulary trichotomy in `pyve_toml_helper.py` — all live in the Pyve repo. Project-guide's deliverable is the spec-authoring surface; Pyve consumes.
- **Dynamic `spec_version` discovery.** The bundled template hard-codes `"3.0"`. Pyve-source-of-truth lookups, version negotiation, or runtime template fetching are explicitly out. Bumps come via a refresh story (the Q-1 / Q.b shape).
- **Validating `env-dependencies.md` at `project-guide` time.** No `project-guide check env-dependencies` integrity command. The trichotomy validation is Pyve's F6 responsibility; project-guide's role is to author conformant output via LLM-driven `plan_envs` discipline + the bundled-template vocabulary.
- **Pyve env-spec parser / linter inside project-guide.** Per above — no parsing or schema validation in project-guide. The artifact is human-and-LLM authored; Pyve is the consumer that validates.
- **Backfilling `env-dependencies.md` into archived projects or this dogfooded repo.** Authoring this project's own `env-dependencies.md` (i.e., running `plan_envs` against project-guide itself) is a separate story, not part of Q-2's template-installation scope. May land in Q-3 if dogfooding surfaces template gaps.
- **`plan_envs` cycle variant.** No cycle-mode counterpart (`refactor_envs` etc.) — env decisions are point-in-time decisions captured per Pyve's spec_version, not a continuous-refinement loop. Reopen via a re-run of `plan_envs` (idempotent regeneration per the rough draft's design).
- **Subphase Q-3 and beyond.** Each future Q-N subphase is drafted in its own future `plan_production_phase` session per the (Q-1-installed) Step 4a pattern.
- **Mode-listing category reorganization.** `plan_envs` lands in the existing "Project Planning" category alongside `plan_concept` / `plan_features` / `plan_tech_spec` / `plan_stories` / `plan_phase` / `plan_production_phase`. No category split, no rename — the new mode fits the existing bucket cleanly.

---

## Implementation Strategy

Three stories in Subphase Q-2, executed in document order:

1. **Q.d — `plan_envs` mode authoring (template + artifact + metadata wiring).** All three files land together so the mode is functional end-to-end on first commit. Adapts both rough drafts into project-guide's canonical shapes; wires the metadata sequence.
2. **Q.e — Spec doc sync (concept.md + features.md + project-essentials.md).** Adds the new mode to spec listings, refreshes counts, cleans up pre-existing mode-name drift (`project_scaffold` → `scaffold_project`, `code_velocity` → `code_direct`, missing `plan_production_phase` row), and lands the Pyve env-spec vendored-template invariant in `project-essentials.md`.
3. **Q.f — v2.12.0 Subphase Q-2 bundled release.** Bumps `project_guide/version.py`, `pyproject.toml`, adds `## [2.12.0]` CHANGELOG entry covering Q.d + Q.e. Closes Subphase Q-2.

Stories within Subphase Q-2 carry **no version in their title** until Q.f (the release story), consistent with the subphase phase-bundling option.

**Story-letter continuity** across the Q-1 → Q-2 boundary per the (Q-1-installed) `_phase-letters.md` Subphases rule: Q-1 ends at `Q.c`, Q-2 starts at `Q.d`. No reset.

**Dependency on Q-1.** Q.a's template installation (subphase pattern in `_phase-letters.md`, `plan-production-phase-mode.md` Step 4a, `_header-common.md`, `plan-phase-mode.md`) must ship before Q-2's stories are *worked on*. Q-2's planning happens now (this session); Q-2's implementation waits for Q-1's v2.11.0 release. Trying to implement Q.d before Q.a ships would produce a `stories.md` whose Q-2 subphase structure conflicts with templates that don't yet recognize subphases.

---

## Acceptance Criteria (Subphase Q-2)

1. `project-guide mode plan_envs` renders without errors; the rendered `go.md` contains the expected steps, prerequisites, and closed-vocabulary discipline note.
2. `project-guide mode` listing shows `plan_envs` in the "Project Planning" category immediately after `plan_tech_spec` and before `plan_stories`.
3. A `plan_tech_spec`-completing developer sees `plan_envs` recommended as `next_mode` (verifiable via the rendered `go.md` next-step section).
4. The bundled `env-dependencies.md` template at `project_guide/templates/project-guide/templates/artifacts/env-dependencies.md` reflects `spec_version: "3.0"` and carries the closed-vocabulary tables verbatim from the rough draft.
5. `concept.md` and `features.md` accurately reflect 17 modes including `plan_envs` and `plan_production_phase`, and use current mode names (`scaffold_project`, `code_direct`).
6. `project-essentials.md` carries a new section documenting the Pyve env-spec vendored-template contract (trichotomy, refresh-story protocol, authoritative-source pointer).
7. `pyve test` and `pyve testenv run ruff check project_guide/ tests/` both pass on the v2.12.0 commit.
8. `CHANGELOG.md` `## [2.12.0]` entry dated, describes the `plan_envs` mode introduction and spec-doc sync as one bundled release.
