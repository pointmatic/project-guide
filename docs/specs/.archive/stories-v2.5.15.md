# stories.md --  (python)

This document breaks the `project-guide` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Put **`vX.Y.Z` in the story title only when that story ships the package version bump** for that release. Doc-only or polish stories **omit the version from the title** (they share the release with the preceding code story, or use your project’s doc-release policy). **One semver bump per owning story** — extra tasks on the *same* story share that bump; see `project-essentials.md`. Semantic versioning applies to the package. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

For a high-level concept (why), see [`concept.md`](concept.md). For requirements and behavior (what), see [`features.md`](features.md). For implementation details (how), see [`tech-spec.md`](tech-spec.md). For project-specific must-know facts, see [`project-essentials.md`](project-essentials.md) (`plan_phase` appends new facts per phase). For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

---

## Phase O: UX improvements

Phase O improves how developers and **agents** (IDE assistants, embedders) interact with project-guide: clearer bundled workflow text in `go.md`, machine-friendly CLI output, and editor-native hints—without changing core mode semantics.

Completed work includes **O.a** (auto-rendered `pyve-essentials.md` in `go.md`), **O.b–c** (embedded **`--quiet`** contract and spec alignment; see `docs/specs/quiet-non-interactive-embedding.md` and `docs/specs/phase-o-pyve-quiet-embedding-plan.md`).

### Story O.a: v2.5.0 Rename project-essentials-pyve.md → pyve-essentials.md and Auto-Render in go.md [Done]

Today `project-essentials-pyve.md` is *merged once* into `docs/specs/project-essentials.md` at scaffold/plan-tech-spec time. Upstream improvements to the bundled pyve rules never reach existing projects — a real drift source. Rename to `pyve-essentials.md` (to signal it is a package-versioned bundled artifact, not a project-owned file) and render it directly in `go.md` behind the `pyve_installed` gate so every `project-guide mode <name>` invocation picks up the latest content automatically. **Released as v2.5.0** (package version and `CHANGELOG.md` section `[2.5.0]` — not tracked again as a separate checkbox below).

- [x] Rename `project_guide/templates/project-guide/templates/artifacts/project-essentials-pyve.md` → `pyve-essentials.md`
- [x] In `project_guide/render.py`:
  - [x] Add `_read_pyve_essentials(templates_subdir, pyve_installed)` helper — reads `templates/artifacts/pyve-essentials.md` from the *template tree* (not `spec_artifacts_path`); returns `""` when `pyve_installed=False` or file missing or whitespace-only
  - [x] Pass `pyve_essentials` into the Jinja context in `render_go_project_guide`
- [x] In `project_guide/templates/project-guide/templates/modes/_header-common.md`: add a `{% if pyve_essentials %}` block rendering the pyve content as a `### Pyve Essentials` subsection nested inside the existing `## Project Essentials` wrapper so `###` headings nest correctly
  - [x] Handle the case where `project_essentials` is empty but `pyve_essentials` is non-empty — the `## Project Essentials` wrapper must still render so the `###` subsection has a parent
- [x] Remove the "Merge Pyve Project Essentials" step from `scaffold-project-mode.md` (currently gated on `{% if pyve_installed %}`) — content is now auto-injected
  - [x] Renumber subsequent steps: collapse the `{% if pyve_installed %}9{% else %}8{% endif %}` conditionals back to unconditional numbering
- [x] Remove the "Pyve users" paragraph (the `{% if pyve_installed %}` block) from `plan-tech-spec-mode.md` step 6
- [x] Update `refactor-plan-mode.md` Step F.2 examples: clarify that pyve-specific rules live in the bundled `pyve-essentials.md` and should NOT be duplicated into `project-essentials.md`
- [x] Update `project_guide/templates/project-guide/templates/artifacts/project-essentials.md` comment block: mention `pyve-essentials.md` as a sibling bundled artifact that is auto-rendered (so users understand why pyve rules don't appear in their own file)
- [x] Update `docs/specs/features.md` FR-13: describe auto-render behavior, not one-shot merge
- [x] Update `docs/specs/tech-spec.md`: `render.py` behavior section, context variables table
- [x] Update `docs/specs/project-essentials.md` in this project (dogfooding): remove or shorten the "Workflow rules — pyve environment conventions" and "LLM-internal vs. developer-facing invocation" sections that will now auto-render from `pyve-essentials.md`; leave only project-specific notes that are not duplicated
- [x] Migration note in CHANGELOG: existing downstream projects may have pyve sections merged into their `project-essentials.md` from pre-v2.5.0 scaffold. Duplication is inert (content renders once from each source); users may optionally delete the merged-in pyve sections to defer to the bundled source of truth
- [x] Tests in `tests/test_render.py`:
  - [x] `render_go_project_guide` with `pyve_installed=True` → rendered `go.md` contains pyve-essentials content under a `### Pyve Essentials` subsection
  - [x] `render_go_project_guide` with `pyve_installed=False` → rendered `go.md` contains no pyve-essentials content (even if `pyve-essentials.md` exists in the template tree)
  - [x] Rendered `go.md` with both `project_essentials` and pyve content present has the `## Project Essentials` wrapper containing the `### Pyve Essentials` subsection
  - [x] Rendered `go.md` with empty `project_essentials` but `pyve_installed=True` still renders the `## Project Essentials` wrapper containing `### Pyve Essentials`
  - [x] No test or code references the old `project-essentials-pyve.md` filename
  - [x] Rename/update the existing pyve-artifact tests (currently `tests/test_render.py:1001-1152`) — adjust inclusion-gate test to assert auto-render rather than merge-instruction presence
  - [x] `test_every_mode_renders_successfully` still passes (parametrized)
  - [x] `scaffold_project` rendered output no longer contains "Merge Pyve Project Essentials"
  - [x] `plan_tech_spec` rendered output no longer contains "Pyve users:"
  - [x] `pyve-essentials.md` artifact contains no unrendered `{{ var }}` placeholders (update the existing guard test for the new name)

### Story O.b: v2.5.1 Embedded-invocation quiet contract ('init' / 'update' / 'purge') [Done]

**Goal:** Match `docs/specs/quiet-non-interactive-embedding.md`: with `--quiet`, **successful** runs produce **no stdout** (pyve/log aggregation friendly); **errors** and important **warnings** (e.g. overridden files, schema mismatch) remain visible; **exit codes** unchanged vs today.

- [x] **`init`**: When `quiet=True`, suppress informational stdout on success paths (`Initializing…`, `✓ Created`, render messages, file count line). Early exit when already initialized emits nothing when quiet. **`init --force` config backup notice → stderr** (`err=True`).
- [x] **`update`**: When `quiet=True`, suppress success-path stdout (dry-run banners/summaries, `✓ Re-rendered`, terminal summaries). Overridden-file notices → stderr. **`All files are overridden…`** when quiet → stderr only.
- [x] **`purge`**: When `quiet=True`, suppress final success banner; removal errors on stderr; **not found (skipped)** hints → stderr.
- [x] **CLI help**: `--quiet` strings describe success silence + stderr diagnostics; FR-9 documents **`--quiet` vs `--verbose`** (only `mode` has `--verbose` today).
- [x] **Tests** (`tests/test_cli.py`, `tests/test_purge.py`): quiet success asserts empty stdout; overridden notices on stderr; errors still emitted (`test_quiet_does_not_suppress_errors`).
- [x] **CHANGELOG** + version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → v2.5.1.
- [x] **Bundled `templates/artifacts/stories.md` + dogfood `docs/specs/project-essentials.md`:** clarify **Commit and version style** — a **`stories.md` title includes `vX.Y.Z` only when that story shipped the package bump**. **`go.md`** incorporates `project-essentials.md` automatically on the next **`project-guide mode <name>`** or **`project-guide update`** (dynamic rendering — `features.md` FR-1, FR-3 step 6, acceptance criterion #2); no hand-edit.

### Story O.c: Align specs with tightened `--quiet` contract [Done]

**Documentation only.** Spec updates shipped together with **O.b** in package **v2.5.1**; this checklist does **not** imply its own semver bump beyond that release.

- [x] **`docs/specs/features.md`**: FR-9 rewritten; Inputs bullets and acceptance criterion #8 updated.
- [x] **`docs/specs/tech-spec.md`**: CLI Design → **Machine-quiet commands** subsection.
- [x] **Cross-link**: `docs/specs/quiet-non-interactive-embedding.md` points at FR-9 / tech-spec and references **v2.5.1**.

### Story O.d: v2.5.2 Tighten cycle step 1 to mandate fresh Read of stories.md [Done]

**Problem:** In `code_direct` and `code_test_first`, step 1 says *"Read the story's checklist from `docs/specs/stories.md`"*. LLMs treat this as already-done because the file is in their context, so when the developer edits `stories.md` between cycles and says "go", the LLM works from a stale cache and silently overwrites or ignores the edits. Tighten the language so step 1 is unambiguous about re-fetching from disk on every cycle.

- [x] **`project_guide/templates/project-guide/templates/modes/code-direct-mode.md`** step 1 — extend the bullet to mandate a fresh `Read` tool call at the start of each cycle and explicitly call out that prior conversation context may be stale because the developer may have edited the file.
- [x] **`project_guide/templates/project-guide/templates/modes/code-test-first-mode.md`** step 1 — same tightening.
- [x] **Tests** in `tests/test_render.py`: add `test_code_direct_step_one_mandates_fresh_read` and `test_code_test_first_step_one_mandates_fresh_read` asserting the new "re-fetch from disk" / "may have edited" language renders into `go.md` for both modes.
- [x] **Re-render** dogfood `docs/project-guide/go.md` via `project-guide update` so this project picks up the change.
- [x] **CHANGELOG** + version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.2**.

### Story O.e: v2.5.3 Tighten debug-mode Step 5 as a named approval gate [Done]

**Problem:** In `debug_mode`, the 5-step Structured Debugging Workflow has a cognitive shape that lets an LLM mis-anchor "done" at Step 4. Step 4's output reads as terminus ("Working code with passing tests"); Step 5's output is the only one without a single nameable artifact ("updated documentation and comprehensive test coverage"); the Golden Rule mantra at the bottom reinforces a 3-beat rhythm (test → fix → verify) that excludes Step 5; and the Debugging Checklist (which *does* enumerate the Step 5 obligations including the `stories.md` write-up) lives several sections away after the case study and anti-patterns. Tighten the structure so Step 5 reads as a gate, not a wrap-up. **Out of scope:** the universal Approval Gate rule in `modes/_header-common.md` — other modes have differently-shaped cycles where "name the output artifact for every step" doesn't map cleanly.

- [x] **`debug-mode.md` Step 5** — rename heading to *"Step 5: Document the Fix in `stories.md` (Approval Gate)"*. Replace the bundled "Document and Prevent" actions with two explicitly separated artifacts: **(a) the story write-up** in `stories.md` (implementation tasks `[x]`'d, housekeeping tasks `[ ]`) — *the gate artifact*; **(b) prevention scan** ("look elsewhere in the codebase for similar bugs"). Output line: *"A story in `stories.md` matching the project format. Until this exists, the cycle is not complete."*
- [x] **`debug-mode.md` Step 4 Output** — change *"Working code with passing tests"* to *"Working code with passing tests — but the cycle is not complete; proceed to Step 5."*
- [x] **`debug-mode.md` cycle-steps section footer** — add a single line after Step 5: *"The approval gate is not reached until all five steps have produced their named output artifact. If you cannot name the Step 5 artifact, you are not at the gate."*
- [x] **`debug-mode.md` Debugging Checklist** — move from its current location (after the Case Study and "Common Debugging Scenarios") to immediately after Step 5. Add a one-line preamble: *"Before pausing for approval, run this checklist and confirm each item."*
- [x] **`debug-mode.md` Anti-Patterns** — add a new entry: *"❌ Declaring the fix complete after Step 4"*.
- [x] **`debug-mode.md` Golden Rule** (Summary section) — reframe to a four-beat: *"Write a failing test first. Fix the code second. Verify the test passes third. Document the fix in `stories.md` fourth."*
- [x] **Tests** in `tests/test_render.py`: add `test_debug_mode_step_five_is_named_approval_gate` covering (a) Step 5 heading contains "Approval Gate", (b) four-beat Golden Rule present, (c) Debugging Checklist appears between Step 5 and the Root Cause Analysis Framework (positional check), (d) the new anti-pattern entry text is present.
- [x] **Re-render** dogfood `docs/project-guide/go.md` via `project-guide update`.
- [x] **CHANGELOG** + version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.3**.

### Story O.f: v2.5.4 Tighten plan-features-mode to read concept.md before asking [Done]

**Problem:** In `plan_features` mode, the LLM treats the Prerequisites list as a checklist to interrogate the developer about, even when `concept.md` (the explicit upstream artifact) already supplies most of the answers. Observed pattern: the LLM enumerates "I need license preference, target audience, constraints, and concept.md" and asks the developer to confirm before reading the file. After the developer says "go", the LLM reads `concept.md` and immediately announces "I have enough context" — proving the questions were unnecessary. The mode template invites this by leading with a Prerequisites section worded as inputs to gather rather than facts usually already on disk, and by structuring Step 1 as "Gather information from the developer" without first mandating a read of the upstream document.

- [x] **`project_guide/templates/project-guide/templates/modes/plan-features-mode.md` Prerequisites** — reframe so `concept.md` is named as the primary source, and each prerequisite item is annotated with where it usually comes from (`concept.md` or `LICENSE`). Drop the "project idea" item from the numbered list (it is redundant with the lead-in sentence).
- [x] **`plan-features-mode.md` Steps** — insert a new Step 1 ("Read what already exists before asking anything") that mandates reading `docs/specs/concept.md` in full plus referenced sibling documents and any `LICENSE` file *before* presenting the developer with prerequisites or questions. Renumber the existing gather/generate/approve steps to 2/3/4. Step 2 must explicitly forbid enumerating prerequisites or asking for items `concept.md` already supplies, and require any genuinely-missing items be asked in a single consolidated round.
- [x] **`project_guide/templates/project-guide/templates/artifacts/stories.md` cross-reference paragraph** (lines 7–8) — extend the "see `concept.md` / `features.md` / `tech-spec.md` / `project-essentials.md`" sentence with a pointer to `docs/project-guide/go.md` for mode-tailored workflow instructions. Rationale: when an LLM is dropped into a session with `stories.md` open, the cross-reference paragraph is its map of related artifacts; without an explicit pointer to `go.md`, the LLM may proceed without picking up the cycle steps and approval-gate rules tailored to the current mode. Note: scope is the bundled artifact template only — downstream projects pick this up the next time `stories.md` is freshly rendered (`plan_stories` mode); the dogfood `docs/specs/stories.md` is project-owned and was not retroactively edited.
- [x] **Re-render** dogfood `docs/project-guide/go.md` via `project-guide update` and spot-check that the new Step 1 and Step 2 guidance render correctly in `plan_features` mode output. (No new render-output assertions in `tests/test_render.py` — the existing `test_every_mode_renders_successfully` and placeholder-guard tests already cover that the templating system works; per-phrase assertions on template body text are overkill.)
- [x] **CHANGELOG** + version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.4**.

---

### Story O.g: v2.5.5 Apply 'go.md' reminder across other artifacts [Done]

- [x] Apply 'go.md' reminder to `brand-description.md`, `concept.md`, `features.md`, and `tech-spec.md`.
- [x] **Convert backtick spec references to markdown local links** in the cross-reference paragraphs of every artifact template that lists sibling documents — `concept.md`, `features.md`, `tech-spec.md`, `stories.md`, `brand-descriptions.md` (each under `project_guide/templates/project-guide/templates/artifacts/`). Example: `` `concept.md` `` → `` [`concept.md`](concept.md) ``. Apply to every spec name in those paragraphs (`concept.md`, `features.md`, `tech-spec.md`, `stories.md`, `project-essentials.md`, `docs/project-guide/go.md`). Rationale: rendered downstream `docs/specs/*.md` files become click-navigable in IDEs and on GitHub. Out of scope: backtick references in *body* prose (only the cross-reference paragraph is touched here); mode templates under `templates/modes/` (those render into `go.md`, where relative links would resolve incorrectly). Note: this task is appended to a story already shipped as v2.5.5; the commit will be amended to the same version.
- [x] **Fix `plan-concept-mode.md` step 4 to reference the artifact template.** Step 4 read "Write the completed document to `docs/specs/concept.md`." with no pointer to `templates/artifacts/concept.md`, so the LLM synthesized `concept.md` from the variable list in steps 1–3 and dropped the static header (title, three-bullet section summary, sibling-doc cross-reference paragraph that lists `features.md` / `tech-spec.md` / `stories.md` / `project-essentials.md` / `go.md`). Observed in a fresh nbfoundry render. Aligned with the sibling pattern used by `plan-features-mode.md` step 3, `plan-tech-spec-mode.md` step 3, and `plan-stories-mode.md` step 2: "Generate `docs/specs/concept.md` using the artifact template at `templates/artifacts/concept.md`". Prevention scan: confirmed every other artifact-producing mode (`plan-features`, `plan-tech-spec`, `plan-stories`, `refactor-plan` create path, `plan-phase` project-essentials create path) already references its artifact template; `document-brand-mode.md`, `document-landing-mode.md`, and `plan-phase-mode.md`'s combined phase-plan doc inline their structure (no artifact template exists) and are an accepted variation.
- [x] Update CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.5**.

---

### Story O.h: v2.5.6 Make file-header conventions mandatory baseline content in 'project-essentials.md' [Done]

The artifact template at `templates/artifacts/project-essentials.md` includes a **File header conventions** section as starter content with `<YEAR>`, `<OWNER>`, `<LICENSE>` placeholders, but the four modes that own `project-essentials.md` lifecycle (`plan_tech_spec`, `plan_phase`, `refactor_plan`, `scaffold_project`) treated the entire file as conditional on developer-provided "must-know facts". A careful LLM running `plan_tech_spec` on a downstream project (observed: nbfoundry) asked the developer whether to include SPDX/copyright headers — silly, since copyright/license info is already in `concept.md` / `LICENSE` / `pyproject.toml` and headers are always required. This story reframes file headers as mandatory baseline content the LLM pre-fills automatically; the developer is asked only about *additional* project-specific facts.

- [x] **`plan-tech-spec-mode.md` steps 5–6**: reframe step 5 opener so the **File header conventions** section is mandatory baseline content the LLM pre-fills from `concept.md` / `LICENSE` / `pyproject.toml`; the developer is asked only about *additional* must-know facts. Replace the closing line ("If the developer says there are none, skip to step 7 — do not create an empty `project-essentials.md`") with "Even if the developer has no additional facts, still create `project-essentials.md` with the file header conventions section pre-filled." Drop the conditional opener of step 6 ("If the developer provides any facts, generate…") so creation is unconditional; require substituting `<YEAR>` / `<OWNER>` / `<LICENSE>` and removing the trailing TODO note.
- [x] **`plan-phase-mode.md` step 7 create branch** ("If it does NOT exist"): add the canonical pre-fill instruction — the **File header conventions** section is mandatory baseline content; pre-fill `<YEAR>` / `<OWNER>` / `<LICENSE>` from the project's `LICENSE` file and `pyproject.toml`; remove the trailing TODO note; do **not** ask the developer about headers (the question below is only about *additional* facts).
- [x] **`refactor-plan-mode.md` Step F.3 create path**: same pre-fill instruction as `plan_phase`. This is the highest-impact site since legacy projects being migrated to v2.x most often hit the create path.
- [x] **`scaffold-project-mode.md` step 8**: split into 8a ("Verify or create `project-essentials.md` with concrete file headers") + 8b (the existing memory-review behavior). Step 8a covers two cases — file missing (create from artifact template, substitute headers from steps 1–3) and file present with placeholders (substitute and remove TODO). If headers are already concrete, leave alone. Renamed step heading to "Project Essentials: Verify or Create, then Memory Review".
- [x] **`templates/artifacts/project-essentials.md` comment block**: replace "An empty file is acceptable — omit this file entirely…" paragraph with "This file is **always** created — the **File header conventions** section below is mandatory baseline content. Additional sections beyond file headers are optional…" Update the bulleted "File header conventions" item (line ~56–59) to say the LLM substitutes the placeholders during the four lifecycle modes and removes the trailing TODO note in the same pass — without asking the developer.
- [x] Update CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.6**.

---

### Story O.i: v2.5.7 Make artifact-template paths in 'go.md' project-root-relative [Done]

The mode templates instruct the LLM to "Generate `docs/specs/<artifact>.md` using the artifact template at `templates/artifacts/<artifact>.md`" — a relative path with no base. In the source repo it resolves from `project_guide/templates/project-guide/`; in a downstream project it resolves from `docs/project-guide/` (where `project-guide init` installs a copy of the entire template tree, including `docs/project-guide/templates/artifacts/*.md`). The LLM has no way to know either base directory and starts groping. A careful LLM running `plan_stories` on a downstream project (observed: nbfoundry) tried `find / -path '*/project_guide*/templates/...'` before the developer interrupted.

The fix is to **make the path explicit and project-root-relative** in the mode-step language: `docs/project-guide/templates/artifacts/<file>.md`. That path exists in every initialized project (created by `project-guide init` and refreshed by `project-guide update`), so the LLM can `Read` it directly with no discovery step. Pairing this with a one-time note in `_header-common.md` (or equivalent shared header) — "bundled artifact templates live at `docs/project-guide/templates/artifacts/` in this project" — anchors the LLM's mental model so it doesn't relapse on a future mode that omits the explicit path.

**Why not inline the content** (rejected alternative): we considered injecting the artifact template content into `go.md` at render time, mirroring the `pyve_essentials` pattern from O.a. Rejected because (a) artifact templates are several KB each and would bloat every `go.md` render even for modes that don't reference them; (b) a 50-byte path that the LLM `Read`s on demand is dramatically more memory-efficient than the bytes themselves; (c) the LLM doesn't actually need the template structure visible at every read of `go.md` — only when it's generating that specific artifact.

**Affected planning modes** (those whose Steps reference an artifact template by path):
- `plan_concept` → `templates/artifacts/concept.md`
- `plan_features` → `templates/artifacts/features.md`
- `plan_tech_spec` → `templates/artifacts/tech-spec.md` and `templates/artifacts/project-essentials.md` (step 6)
- `plan_stories` → `templates/artifacts/stories.md`
- `plan_phase` create branch → `templates/artifacts/project-essentials.md`
- `refactor_plan` Step F.3 create path → `templates/artifacts/project-essentials.md`
- `scaffold_project` step 8a create case → `templates/artifacts/project-essentials.md`
- `refactor_document` (sibling pattern) → `templates/artifacts/brand-descriptions.md`

**Tasks:**

- [x] **Mode templates** (`plan-concept-mode.md`, `plan-features-mode.md`, `plan-tech-spec-mode.md`, `plan-stories-mode.md`): rewrite each "Generate … using the artifact template at `templates/artifacts/<file>.md`" to "Generate … using the artifact template at `docs/project-guide/templates/artifacts/<file>.md`". Where present, also add a parenthetical: *"(installed by `project-guide init`; refreshed by `project-guide update`)"* — this answers the LLM's implicit "is this real?" question without prose bloat.
- [x] **`plan-phase-mode.md` step 7 create branch**, **`refactor-plan-mode.md` Step F.3 create path**, **`scaffold-project-mode.md` step 8a create case**: same path rewrite for the `project-essentials.md` reference.
- [x] **`refactor-document-mode.md`** (uses `brand-descriptions.md` artifact via the same pattern): same path rewrite.
- [x] **`_header-common.md`** (the shared header rendered in every mode's `go.md`): added an anchor sentence under the **Rules** block naming `docs/project-guide/templates/artifacts/` as the canonical install location and explicitly forbidding filesystem / `site-packages` / install-location searches. Loads with every mode so the rule is always-context. **Note:** the path is hardcoded with forward slashes (not `{{ target_dir }}/templates/artifacts/`) because `target_dir` carries OS-native separators and rendered as `docs\project-guide/templates/artifacts/` on Windows CI — mixed-separator output is confusing for the LLM and broke the anchor-detection test on Windows. Hardcoding matches the same convention used by the mode-template path rewrites in this story.
- [x] **`templates/artifacts/project-essentials.md`** (artifact comment block): added a project-guide-consumer hint under the **Architecture quirks** category naming the install location and listing the environment managers (pip, poetry, uv, conda, mamba, micromamba, pyve, pixi) that all stash `site-packages` differently — captures the "why the project-root-relative path is the only environment-agnostic answer" rationale for any future LLM that re-reads the artifact.
- [x] **Tests in `tests/test_render.py`** (27 new parametrized tests, +27 to total):
  - [x] `test_header_common_anchors_artifact_templates_install_location` — parametrized over every mode; asserts the rendered `go.md` contains `docs/project-guide/templates/artifacts/` and the explicit *"do not search the filesystem"* instruction.
  - [x] `test_mode_uses_project_root_relative_artifact_path` — parametrized over a `_MODE_ARTIFACT_REFERENCES` mapping (12 mode→file pairs spanning the 8 affected modes); asserts the explicit project-root-relative path appears, and that the count of bare `templates/artifacts/<file>.md` equals the count of explicit `docs/project-guide/templates/artifacts/<file>.md` (negative regression guard — every bare reference must be embedded inside the longer explicit path).
  - [x] `test_every_mode_renders_successfully` still passes (no regression).
- [x] No update needed to `docs/specs/features.md` or `docs/specs/tech-spec.md` — the install layout was already covered there; no new cross-reference required.
- [x] Update CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.7**.

**Out of scope:**
- Changing artifact template content (this story is purely about path clarity and mode-step language).
- Inline-rendering artifact templates into `go.md` (rejected alternative; see rationale above).
- Changing the install layout itself (`docs/project-guide/templates/artifacts/` is the canonical location set by `project-guide init` since v2.0; this story leans on that, doesn't change it).
- Path rewrites for non-planning modes (`code_direct`, `debug`, etc. — they don't reference artifact templates).

---

### Story O.j: v2.5.8 Update bundled docs to current pyve 'testenv' subcommand CLI shape [Done]

The bundled `pyve-essentials.md` artifact (auto-rendered into every downstream `go.md` under `## Project Essentials > ### Pyve Essentials` since v2.5.0) and the bundled developer doc `python-editable-install.md` quoted pyve commands in the **flag form** `pyve testenv --install -r requirements-dev.txt`. The current pyve CLI uses the **subcommand form** `pyve testenv install -r requirements-dev.txt` — `install` is one of four subcommands alongside `init`, `purge`, and `run` (per `pyve testenv --help`). The flag form is gone. Every downstream project that consumes `pyve-essentials.md` was being told the wrong command shape. `plan-tech-spec-mode.md`'s "Dev tool installation" example (used as a worked-example prompt during project-essentials capture) carried the same stale form.

- [x] **`templates/artifacts/pyve-essentials.md`**: replace all 3 occurrences of `pyve testenv --install -r requirements-dev.txt` with `pyve testenv install -r requirements-dev.txt` (lines 8, 30, 51).
- [x] **`developer/python-editable-install.md`**: replace all 3 occurrences (lines 82, 95, 125) — bundled developer doc shipped with the package via `init`.
- [x] **`templates/modes/plan-tech-spec-mode.md`** step 5 worked-example list: change `\`pyve testenv --install\`` → `\`pyve testenv install\`` so the prompt the developer sees during project-essentials capture matches the current CLI.
- [x] Source-tree scan (`grep -rn "testenv --install\|testenv --purge\|testenv --init\|testenv --run" project_guide/`) returned empty after edits — no other flag-form references remain. `.archive/*.md` files retain the stale form intentionally (historical record).
- [x] **`pyve testenv init` is required** before `pyve testenv install` or `pyve testenv run` — those subcommands do not auto-create `.pyve/testenv/venv/` (per [pyve `testenv` subcommand reference](https://pointmatic.github.io/pyve/usage/#testenv-subcommand)). Add the init step to the bundled docs:
  - **`templates/artifacts/pyve-essentials.md`**: added a new "Initialize the testenv (one-time)" bullet citing the upstream URL; updated "Install dev tools" bullet to reference the prior init step; added a sentence to the "If `pytest` fails" hint covering the env-doesn't-exist failure mode; updated `requirements-dev.txt` story-writing rule to say the reproducible setup is `pyve testenv init && pyve testenv install -r requirements-dev.txt` (two commands); added `pyve testenv init` to the testenv editable-install code block.
  - **`developer/python-editable-install.md`**: added `pyve testenv init` to both runnable code blocks (the testenv-only block and the preferred-pattern block); added a new "Common Mistakes" row covering `pyve testenv install/run` before `pyve testenv init`.
- [x] Update CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.8**.

**Out of scope:**
- Auditing other bundled commands (`pyve test`, `pyve run`, `pyve testenv run`) for CLI-shape drift — those still match the current help output as of writing.

---

### Story O.k: v2.5.9 Channel discipline (rich vs. logging) and install-output protection [Done]

Two related rules ship together as Rules-block hardening + tech-spec defaults:

1. **Channel discipline.** A common LLM failure mode: emitting an operational warning ("stage X took longer than expected") via `console.print(...)` because the message *feels* user-facing. Wrong channel — operational concerns are unfilterable downstream that way. The rule (`rich` is for users; `logging` is for operators; warnings/retries/fallbacks go to logs) is universal-Python, not project-specific. Bake it into the **tech-spec artifact's Cross-Cutting Concerns** section as static default content (similar to how File header conventions in project-essentials.md is mandatory baseline) so every project's generated `tech-spec.md` carries the rule, and `plan_stories` reads tech-spec → stories carry the discipline → code modes implement it correctly. Avoid the per-project Q&A pattern entirely (do **not** add this as a worked example to `plan-tech-spec-mode.md` step 5; that step is for project-specific gotchas).
2. **Install-output protection.** A second recurring LLM failure: editing files under `docs/project-guide/` to "fix" a discrepancy, then watching the edit get silently clobbered on the next `project-guide update` or `project-guide mode` invocation. Add a Rules-block bullet in `_header-common.md` (sibling to the O.i bundled-artifact-templates anchor) that names `docs/project-guide/` as install output, surfaces the `project-guide override` escape hatch, and presents three resolution paths the LLM should offer the developer rather than editing silently: override locally, file an issue/PR upstream at https://github.com/pointmatic/project-guide, or wait for guidance. The dogfooding-specific "edit source-of-truth template" path stays in **this repo's `docs/specs/project-essentials.md`** (where it already lived); only the universal moves go into `_header-common.md`.

- [x] **`developer/best-practices-guide.md`**: added a new **Logging and User Output** section between Error Handling and Open Source Sustainability. Captures the rich/logging discipline with rationale, anti-pattern (`console.print(...)` for warnings), and cross-language analogues (`chalk`/`pino` Node, `pterm`/`slog` Go, `console`/`tracing` Rust).
- [x] **`templates/artifacts/tech-spec.md`** Cross-Cutting Concerns section: added a static **Logging and User Output** subsection naming `rich`/`logging` (Python), `chalk`/`pino`, `pterm`/`slog`, `console`/`tracing` analogues, and the warnings-go-to-logs rule. Preserved `{{cross_cutting}}` placeholder under a new **Additional Cross-Cutting Concerns** subheading so project-specific cross-cutting concerns still get captured during plan-tech-spec mode's developer Q&A.
- [x] **`templates/modes/_header-common.md`** Rules block: added a new bullet (immediately after the O.i bundled-artifact-templates anchor) naming `docs/project-guide/` as install output, citing `project-guide override <file> "<reason>"` and `project-guide unoverride <file>` as the escape hatch, instructing the LLM to flag conflicts as substantive (not silently edit), and enumerating three universal resolution paths: (1) override and edit locally, (2) file an issue/PR at https://github.com/pointmatic/project-guide, (3) wait for developer guidance.
- [x] **`docs/specs/project-essentials.md`** dogfooding rule (this repo only): augmented the "Installed copy" bullet to mention the `project-guide override`/`unoverride` escape hatch alongside the existing "Never hand-edit" guidance, with a note that for dogfooding work the override path is rarely the right answer (the fix lives in the source-of-truth template).
- [x] Decision-record: in this story, do **not** add the rich/logging rule to `plan-tech-spec-mode.md` step 5 worked-examples (the project-essentials Q&A) — adding a universal rule to a project-specific Q&A is the per-project asking pattern we're trying to avoid. Tech-spec ownership is sufficient.
- [x] **Tests in `tests/test_render.py`** (16 new parametrized tests):
  - [x] `test_header_common_install_output_rule_renders_in_every_mode` — parametrized over every mode; pins four observable behaviors of the new rule: directory naming, override-command name, upstream URL, "do not edit silently" instruction.
  - [x] `test_tech_spec_artifact_has_logging_and_user_output_subsection` — reads the bundled artifact directly via `importlib.resources`; asserts the subsection header, both Python channels (`rich`, `logging`), at least one cross-language analogue (`chalk`, `pino`/`slog`), the operator-log rule for warnings, and that the original `{{cross_cutting}}` placeholder is preserved under a separate **Additional Cross-Cutting Concerns** subheading.
- [x] Update CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.9**.

**Out of scope:**
- Adding a re-read instruction in `code_direct` / `code_test_first` modes to re-load tech-spec.md when implementing logging/output stories. Trust the story-task → implementation propagation path for now (well-planned stories carry the discipline implicitly). Revisit if drift is observed in practice.
- Gating the install-output rule's path-to-resolve options with a Jinja conditional based on `project_name`. The dogfooding-specific source-of-truth path lives in this repo's `project-essentials.md` already; the shared header should carry only universal moves. Adding a `project_name`-based template branch for a single-repo carve-out is over-engineering.

---

### Story O.l: v2.5.10 Tighten plan_stories — assume approval, derive CI/CD, detect wrong mode [Done]

**Problem:** In `plan_stories` mode, the LLM exhibits three avoidable missteps that all stem from the current template wording:

1. **Asks the developer to confirm prerequisites are "approved"** — the Prerequisites section reads "Before writing stories, the following must be approved: concept.md, features.md, tech-spec.md", which the LLM treats as an instruction to interrogate the developer. The presence of those files (and the developer's choice to invoke `plan_stories`) already implies approval; the mode's natural pause-on-summary gate is the rejection path. Mirrors the pattern fixed for `plan_features` in O.f.
2. **Asks a CI/CD question whose answer is in `tech-spec.md`** — the standalone "Will this project need CI/CD automation?" prompt is presented even when `tech-spec.md` already specifies packaging/distribution and CI scope. The LLM should derive the answer from the spec and only escalate when the spec is genuinely silent. Two complementary fixes: capture a single explicit CI/CD summary fact during `plan_tech_spec` so it lands in the spec; teach `plan_stories` to read it.
3. **Cannot detect that it's the wrong mode** — `plan_stories` is for *initial* story planning. If `stories.md` already has substantive content beyond the template scaffold, or the codebase is already populated, or `git log` is deep, the developer has stumbled into the wrong mode and should be using `plan_phase` (optionally preceded by `refactor_plan` to formalize spec changes). The LLM has no guardrail and silently proceeds to overwrite or duplicate prior planning work.

**Tasks:**

- [x] **`templates/modes/plan-stories-mode.md` Prerequisites** — reframed to name `concept.md`, `features.md`, and `tech-spec.md` as inputs the LLM reads at the start of Step 2 (presence + developer's invocation imply approval). Dropped the "must be approved" phrasing. Replaced the standalone CI/CD-automation prompt with a one-liner pointing the LLM at `tech-spec.md`'s `## CI/CD Automation` section as the authoritative source, with permission to ask only if the spec is silent or genuinely ambiguous. To keep the test contract clean, the meta-instruction names "CI/CD-automation prompt" rather than quoting the previous verbatim question (the test pins absence of the verbatim phrase).
- [x] **`plan-stories-mode.md` Steps** — inserted new Step 1 "Verify this is the right mode" with three deterministic checks: existing `### Story` headings in `stories.md`, substantive source beyond Phase A scaffolding, and `git log --oneline | wc -l` deeper than ~10 commits. On trip, halt with a one-paragraph diagnosis and recommend `plan_phase` (optionally preceded by `refactor_plan`); do not proceed without explicit developer override. Renumbered existing steps to 2/3/4.
- [x] **`plan-stories-mode.md` Step 2 (formerly Step 1)** — extended the read instruction so the LLM extracts CI/CD scope from `tech-spec.md` to inform the Phase G decision and does not re-ask the developer when the spec answers the question. Step 3 now conditions Phase G inclusion on the spec's CI/CD section.
- [x] **`templates/modes/plan-tech-spec-mode.md` step 2** — added `ci_cd_automation` bullet to the technical-details list. One-line summary of CI/CD scope (lint/test on push, coverage reporting, automated registry publishing on tag); "None" is a valid opt-out. Captured once during plan-tech-spec Q&A — `plan_stories` reads this single fact.
- [x] **`templates/artifacts/tech-spec.md`** — added a dedicated top-level **`## CI/CD Automation`** section with `{{ci_cd_automation}}` placeholder, between Packaging and Distribution and end-of-document. A grep-able anchor `plan_stories` can deterministically locate independent of how packaging/distribution is structured.
- [x] **Tests in `tests/test_render.py`** (5 new tests):
  - [x] `test_plan_stories_mandates_wrong_mode_check` — asserts the rendered `plan_stories` `go.md` carries the "Verify this is the right mode" step name and mentions both `plan_phase` and `refactor_plan` plus at least one observable check (`### Story` headings).
  - [x] `test_plan_stories_does_not_ask_ci_cd_when_spec_present` — asserts the standalone "Will this project need CI/CD automation?" prompt no longer appears verbatim and that the replacement instruction names `tech-spec.md` as the source of truth.
  - [x] `test_plan_stories_drops_explicit_approval_ask` — asserts "must be approved" wording is gone from the rendered `plan_stories` `go.md` and the replacement framing names "imply approval".
  - [x] `test_plan_tech_spec_captures_ci_cd_automation_summary` — asserts the rendered `plan_tech_spec` `go.md` lists `ci_cd_automation` and names the destination ("CI/CD Automation") so the LLM knows where the fact lands.
  - [x] `test_tech_spec_artifact_has_ci_cd_automation_section` — reads the bundled artifact directly via `importlib.resources` and asserts both the section heading and the placeholder.
  - [x] All 138 prior render tests still pass (no regression); full suite is 430 passed.
- [x] **Re-rendered** dogfood `docs/project-guide/go.md` via `project-guide update`.
- [x] **Prevention scan** — confirmed the "must be approved" wording was unique to `plan-stories-mode.md` (no other mode template carried it; `plan_features` was already tightened in O.f). The wrong-mode-guardrail pattern is unique to `plan_stories` because it is the only "initial" planning mode that would conflict with prior story content; `plan_phase` and `refactor_plan` are by design used on existing projects. No follow-up tasks needed.
- [x] Updated CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.10**.
- [x] Verify: ran `pyve test` (430 passed), `pyve testenv run ruff check project_guide tests` (clean), and re-rendered `plan_stories` mode locally — wrong-mode check, CI/CD-from-spec instruction, and reframed prerequisites all present in the rendered `go.md`. End-to-end "scratch project with populated stories.md" verification deferred to first downstream encounter — pinning is via the unit tests above.

**Out of scope:**
- Auto-detecting the right mode and switching automatically. The guardrail halts and recommends; the developer initiates the mode change. Auto-switching is too magical for a workflow tool.
- Validating the *content* of `tech-spec.md`'s CI/CD section during `plan_stories`. The mode reads what's there; it does not lint the spec. Spec quality is a `plan_tech_spec` concern.
- Backfilling the new CI/CD summary into existing downstream `tech-spec.md` files. Downstream projects pick this up the next time they run `plan_tech_spec` or via a manual edit; this story does not ship a migration.

---

### Story O.m: v2.5.11 Tighten scaffold_project — read Story A.a first, treat generic defaults as fallbacks [Done]

**Problem:** `scaffold_project` mode template gives concrete defaults (version `0.1.0`, no build backend specified, generic README/CHANGELOG/.gitignore recipes) before mandating a read of the project-specific authoritative source — Story A.a in `docs/specs/stories.md` and `docs/specs/tech-spec.md`. The LLM treats the generic defaults as instructions and treats Story A.a as a checklist to mark off at the end. Observed downstream (datarefinery): the LLM picked setuptools without consulting A.a's hatchling prescription, set version to `0.1.0` against A.a's `0.0.1`, skipped `requirements-dev.txt` / `src/<package>/` skeleton / dev-tool configs / pyve init steps, then surfaced the delta at the mark-done step as "want to extend now or leave [Planned]?" — exactly the wrong shape. Same family of bug as Story O.f (`plan_features` reading `concept.md` before asking) and Story O.l (`plan_stories` deriving CI/CD from spec).

**Tasks:**

- [x] **`templates/modes/scaffold-project-mode.md`** — inserted new **Step 1: Read the project-specific spec** that mandates reading Story A.a in full plus `docs/specs/tech-spec.md` before any scaffolding work. Lists the project-specific fields A.a is authoritative for (build backend, version, deps, package layout, console scripts, dev tooling, etc.) and frames the subsequent steps as generic defaults that apply only when A.a is silent — on conflict, A.a wins. Renumbered existing 9 steps to 2–10.
- [x] **Step 4 (Package Manifest)** — reframed each concrete default as a fallback. Build backend explicit ("use what Story A.a prescribes; do not pick a default without checking"). Version "per Story A.a; default to `0.1.0` only if A.a is silent". Added explicit prompts for runtime deps, optional-dep extras, console scripts, entry-point groups, and dev-tool config (ruff/mypy/pytest) sourced from the spec. License / authors fields kept as the unconditional "generic fields that apply regardless" subgroup.
- [x] **Step 5 (README.md)** — added one-liner: if Story A.a or `tech-spec.md` prescribes additional sections beyond the generic ones, include them now rather than deferring.
- [x] **Step 6 (CHANGELOG.md)** — added one-liner: if Story A.a prescribes a seeded version entry (e.g., `## [0.0.1]`), include it.
- [x] **Step 7 (.gitignore)** — added one-liner: if Story A.a or `tech-spec.md` prescribes additional patterns (e.g., `data/`, secrets files), include them.
- [x] **Step 8 (renamed to "Verify Story A.a is Implemented and Mark Done")** — reframed preamble. By this point every A.a task should already be implemented; this step is a verification gate, not a "what's missing?" surfacing. If unmet tasks remain, loop back and implement them rather than mass-marking `[x]` or asking the developer to choose between options.
- [x] **Step 9 (Project Essentials)** — internal cross-reference updated: "steps 1–3 above" → "steps 2–4 above"; "from step 1" → "from step 2". Substep labels `8a`/`8b` renumbered to `9a`/`9b`.
- [x] **Tests in `tests/test_render.py`** (2 new tests):
  - [x] `test_scaffold_project_mandates_story_a_read_before_defaults` — pins the new Step 1 heading, "Story A.a" mention, "Story A.a wins" framing, "in full" instruction, and the no-default rule for build backend / version.
  - [x] `test_scaffold_project_step_numbers_renumbered` — pins absence of `**8a.` / `**8b.` / "steps 1–3 above", presence of `**9a.` / `**9b.` / "steps 2–4 above" / "from step 2, the copyright holder", and the final-step-is-10 anchor.
  - [x] All prior render tests still pass; full suite is **432 passed** (430 prior + 2 new).
- [x] **Re-rendered** dogfood `docs/project-guide/go.md` via `project-guide update`.
- [x] **Prevention scan** — `plan_phase` Phase A scaffolding section just runs `scaffold_project` (so it inherits this fix automatically); `refactor_plan` is for existing projects with manifests already in place (different shape — failure mode is "ignored an existing manifest", not "ignored A.a's prescription"). No other planning mode carries the "concrete default before reading project-specific source" pattern. No follow-up tasks needed.
- [x] Updated CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.11**.
- [x] Verify: ran `pyve test` (**432 passed**) and `pyve testenv run ruff check project_guide tests` (clean); re-rendered `scaffold_project` mode locally and confirmed the new Step 1 plus reframed defaults render correctly.

**Out of scope:**
- Hard-coding the LLM to fail loudly when Story A.a is missing entirely. Some projects may invoke `scaffold_project` before stories are planned (legitimate edge case for ad-hoc scaffolds); the new Step 1 already says "if no Story A.a exists, the steps below are the full spec." Failing loudly would block those flows.
- Auto-detecting build backend / version / deps from `pyproject.toml` if it pre-exists. Out of scope for this tightening — the failure mode is "LLM ignored A.a", not "LLM ignored an existing manifest". Address separately if observed.

---

### Story O.n: v2.5.12 Tighten code_direct / code_test_first cycles to announce the next story before implementing [Done]

**Problem:** The `code_direct` and `code_test_first` cycle templates conflate "read story" (Step 1) with "implement it" (Step 2): no explicit gate sits between them. After a mode switch the LLM reads `go.md`, says "the next step is to read `stories.md`...", and waits. When the developer says "go", the LLM silently picks a story (its best guess of what's next) and starts implementing — the developer has no chance to confirm or redirect *which specific story* is being worked on. Same family of bug as O.f / O.l / O.m: a missing read-and-announce-before-acting gate. The existing Step 9 ("Present" completed story) handles the *exit* gate cleanly; this story adds the symmetric *entry* gate so every "go" is precise.

**Tasks:**

- [x] **`templates/modes/code-direct-mode.md` Cycle Steps** — insert a new **Step 2: Identify and announce the intended next story** between the existing Read and Implement steps. The new step requires the LLM to state the story ID, title, and a one-line scope summary, then wait for "go" (or a redirect to a different story) before proceeding to implementation. Renumber Implement→3, Headers→4, Tests→5, Lint→6, Mark→7, Bump→8, CHANGELOG→9, Present→10, Wait→11.
- [x] **Step 11 (formerly Step 10) Wait** — extend the language so "go" re-enters the cycle at Step 1, triggering a fresh `stories.md` read and a *new* announce — never silent implementation of whatever the LLM assumed was next. This makes the cycle's two gates (announce-before-implement, present-before-next-cycle) symmetric.
- [x] **`templates/modes/code-test-first-mode.md` Cycle Steps** — same insertion. New Step 2 announces; existing TDD inner loop (red/green/refactor) becomes Step 3; subsequent steps renumber to 4–10. Step 10 (formerly 9) Wait extended with the same re-enter-at-Step-1 language.
- [x] **`code-direct-mode.md` Story Ordering section** — update the "If unclear which story is next, ask" bullet so it is explicit that asking is part of Step 2's announce, not a fallback the LLM may skip when it *thinks* it knows.
- [x] **Tests in `tests/test_render.py`** (4 new tests):
  - [x] `test_code_direct_step_two_announces_before_implementing` — asserts the rendered `code_direct` `go.md` contains a Step 2 named "Identify and announce" (or equivalent), names "story ID, title", and instructs the LLM to wait for "go" before implementing.
  - [x] `test_code_test_first_step_two_announces_before_implementing` — same shape for `code_test_first`.
  - [x] `test_code_direct_wait_step_re_enters_at_step_one` — asserts the final Wait step instructs "go" to re-enter the cycle at Step 1 with a fresh stories.md read.
  - [x] `test_code_test_first_wait_step_re_enters_at_step_one` — same for `code_test_first`.
  - [x] All prior render tests still pass.
- [x] **Re-render** dogfood `docs/project-guide/go.md` via `project-guide update`.
- [x] **Prevention scan** — `debug` mode's cycle entry condition is different (developer reports a specific bug; LLM debugs it; no "pick a story from a list" beat), so the announce-before-implement gate doesn't apply. `archive_stories` and `default` modes are sequence-shaped, not cycle-shaped. No other cycle modes carry this pattern.
- [x] Update CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.12**.
- [x] Verify: ran `pyve test` (full suite green) and `pyve testenv run ruff check project_guide tests` (clean); re-rendered both code modes locally and confirmed the new Step 2 announce gate plus the re-enter-at-Step-1 wait language render correctly.

**Out of scope:**
- Combining the cycle's two gates into one (pre-announcing the next story inside the previous cycle's Present step). Two separate gates are clearer for the post-mode-switch case and for cycles where the developer redirects to a different story than the LLM expected. One gate per concern.
- Adding the same announce gate to `debug` mode. The cycle entry there is "developer reports a bug"; the LLM doesn't pick a story off a list. If the symptom shows up there in practice, address separately.

---

### Story O.o: v2.5.13 Version-cadence rule (standard semver, phase-bundling, no out-of-order) [Done]

**Problem:** The bundled `templates/artifacts/stories.md` carries one terse line about versioning ("Put `vX.Y.Z` in the story title only when..."), which left a careful downstream LLM (datarefinery) extrapolating from `pyproject.toml`'s `version = "0.0.1"` placeholder and patch-bumping 48 stories before randomly switching to minor and then major. The rule was load-bearing but absent. This story documents the project-guide default cadence as static baseline content (parallel to file-header-conventions in `project-essentials.md` from O.h, channel-discipline in `tech-spec.md` from O.k, and CI/CD-summary in `tech-spec.md` from O.l) so every new project's `stories.md` carries it, and code modes read it deterministically rather than extrapolating.

**Cadence rule (the locked content):**
- **Every story belongs to a phase.** Bugfix stories included. No orphan stories.
- **Per-story bumping** (when a story owns its own release):
  - Bugfix or trivial change → **patch**
  - Feature or improvement → **minor**
  - Breaking change → **major** (post-1.0 only; only via `plan_production_phase` mode, which negotiates whether the breakage is substantively user-facing or technically-but-trivially breaking)
- **Bundling option:** a phase can run unversioned during work and ship a single release/tag at end-of-phase; bump magnitude is determined by the highest-impact change in the bundle.
- **No out-of-order implementation.** Story order in `stories.md` is the order of execution. If work order needs to change, reorganize/renumber here first — don't skip ahead and create version-number gaps.
- **Pre-1.0:** standard semver; version starts at `v0.1.0` (Story A.a).
- **Post-1.0:** every phase goes through `plan_production_phase` (the lighter `plan_phase` is pre-1.0 only).

**Plus:** a procedural rule that "Out of scope" sections in stories or phase plans must be **negotiated** with the developer at planning time, not silently committed.

**Tasks:**

- [x] **`templates/artifacts/stories.md`** — added a new top-level **`## Version Cadence`** section after the existing `vX.Y.Z`-in-title paragraph and before the first `---`. Static baseline content; forward-references `plan_production_phase` (Story O.p) without depending on it.
- [x] **`templates/modes/_header-cycle.md`** — added the **Version Cadence (quick reference)** section: four bump-magnitude bullets, phase-bundling option, anti-extrapolation closer pointing at `docs/specs/stories.md`'s authoritative section.
- [x] **`templates/modes/_header-cycle.md`** — added the **Out-of-scope items in stories** subsection: when announcing a story, briefly summarize any "Out of scope" items so the developer can opt some back into scope. They are a negotiation point, not a unilateral deferral.
- [x] **`templates/modes/plan-phase-mode.md` step 3** — extended the "Out of scope" bullet so the LLM walks through each Out-of-scope item with the developer before committing the phase plan. Primary site for the rule.
- [x] **`templates/modes/plan-stories-mode.md`** — added a Version-assignment cross-reference under Step 3 (most stories default to minor; bugfix=patch; major forward-deferred to `plan_production_phase`; A.a starts at v0.1.0). Updated Story Writing Rules' Version bullet to match.
- [x] **`templates/modes/code-direct-mode.md` Step 8 (Bump version)** — replaced the bare bullet with a one-liner cross-referencing the Version Cadence rule and forbidding extrapolation from `pyproject.toml`. Velocity Practices' "Version bump per story" bullet updated to match.
- [x] **`templates/modes/code-test-first-mode.md` Step 7 (Bump version)** — same cross-reference and anti-extrapolation language.
- [x] **`templates/modes/debug-mode.md`** Step 5 — added a one-line note that bug-fix stories take patch bumps per the Version Cadence rule (or run unversioned if the phase-bundling option is in play).
- [x] **Tests in `tests/test_render.py`** (10 new test cases — 5 test functions, 7 of them parametrized to give 10 total):
  - [x] `test_stories_artifact_has_version_cadence_section` — pins the section heading, all four bump-magnitude rules, phase-bundling, no-out-of-order, anti-extrapolation, v0.1.0 start, and `plan_production_phase` forward-reference.
  - [x] `test_header_cycle_carries_version_cadence_quick_reference` — parametrized over `code_direct`, `code_test_first`, `debug`; pins the quick-reference renders into every cycle-mode `go.md`.
  - [x] `test_header_cycle_carries_out_of_scope_negotiation_rule` — parametrized over the same three modes; pins the out-of-scope summary instruction.
  - [x] `test_plan_phase_mandates_out_of_scope_negotiation` — pins the "walk through each Out-of-scope item with the developer" + "negotiation, not a unilateral declaration" language.
  - [x] `test_code_modes_bump_step_references_cadence_rule` — parametrized over `code_direct`, `code_test_first`; pins the Bump-version step's cadence-rule reference and step-level anti-extrapolation language.
  - [x] All prior render tests still pass (no regression). Full suite **446 passed** (436 prior + 10 new).
- [x] **Fixed two pre-existing tests** (`tests/test_actions.py::test_perform_archive_happy_path` and `tests/test_archive_stories_mode.py::test_archive_stories_cli_happy_path`) whose archived-content-leak assertions used a bare-substring `"Story A.a" not in fresh` — the new Version Cadence section legitimately mentions `(Story A.a)` in prose, so the leak-check needed to pin on the heading form `### Story A.a` instead.
- [x] **Re-rendered** dogfood `docs/project-guide/go.md` via `project-guide update`.
- [x] **Prevention scan** — confirmed no other mode's "Bump version" or version-handling step extrapolates from `pyproject.toml`. The existing dogfood `project-essentials.md` "Version bumping" section is project-specific (keeps project-guide's own v2.x.y patch-per-story convention) — the new bundled cadence rule applies to *downstream* projects, not retroactively to this repo.
- [x] Updated CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.13**.
- [x] Verify: ran `pyve test` (446 passed) and `pyve testenv run ruff check project_guide tests` (clean); re-rendered `code_direct` / `code_test_first` / `debug` / `plan_phase` / `plan_stories` modes locally and confirmed the Version Cadence + out-of-scope-negotiation language renders correctly.

**Out of scope:**
- Implementing `plan_production_phase` mode itself — that's Story O.p. This story forward-references it but does not depend on it existing yet; the cadence rule's "post-1.0 major-via-`plan_production_phase`" language reads as forward guidance.
- Retroactively re-numbering this project's own dogfood `docs/specs/stories.md` to match the new cadence. Project-guide's own version history follows a different convention (patch-per-story v2.x.y) that is intentionally project-specific.
- Mode reordering / section renaming (`Planning` → `Project Planning`, `Post-Release` → `Release Planning`). That's Story O.q.

---

### Story O.p: v2.5.14 plan_production_phase mode + bump-version helper [Done]

**Problem:** Post-1.0 phases need production-level scrutiny *every time*, not just at the v1.0.0 threshold crossing. Standard `plan_phase` is the right regimen for pre-1.0 rapid iteration but too light once users depend on the package. This story introduces `plan_production_phase` mode — a copy of `plan_phase` plus production readiness prerequisites, an end-of-phase qualification checklist sourced from `developer/best-practices-guide.md`'s Velocity-vs-Production section, a breaking-change negotiation step (since "breaking" is often technically-but-trivially so — e.g., log-format changes when logs aren't a core consumer capability), and a deterministic version bump on developer green-light. Plus a CLI helper `project-guide bump-version <X.Y.Z>` parallel to `archive-stories` that does the mechanical write to `version.py` / `pyproject.toml` / `CHANGELOG.md`.

**Mandatory-vs-recommended:** post-1.0, `plan_production_phase` is **the only valid phase-planning mode**. `plan_phase` becomes pre-1.0-only.

**Tasks:**

- [x] **Audited the existing `plan-production-mode.md`** (renamed by the developer to `plan-production-phase-mode.md` prior to this story). Salvaged the Production Mode Transition Checklist content (branch protection, CONTRIBUTING.md, SECURITY.md, Dependabot, trusted publisher, PR-based workflow) and folded it into the new mode's Step 2 readiness checklist. Otherwise rewrote the file from scratch, deriving structure from `plan-phase-mode.md` and layering production-specific steps on top.
- [x] **`templates/modes/plan-production-phase-mode.md`** — full rewrite. Mode template includes:
  - Lead-in identifying it as the post-1.0 mandatory phase-planning mode (`plan_phase` is pre-1.0 only).
  - **Prerequisites section** naming required state: spec docs exist, package version at verge-of or past v1.0.0, CI green, previous phase shipped.
  - **Step 1**: Read existing specs (parallel to `plan_phase`).
  - **Step 2 (NEW)**: Walk the Production-readiness checklist with the developer — eight items sourced from `best-practices-guide.md`'s Velocity-vs-Production section. Mode does not proceed past unmet items without explicit developer override.
  - **Step 3**: Gather phase info (parallel to `plan_phase`) plus two production-specific prompts (`anticipated_breaking_changes`, `production_concerns`).
  - **Step 4**: Generate phase plan with explicit "Anticipated version bump target" line.
  - **Step 5 (NEW)**: Breaking-change negotiation. For each anticipated breaking change, walk the developer through "substantively breaks user expectations" vs. "technically-but-trivially breaking". Worked example: log-format change when logs aren't a core consumer capability. Mode suggests major-vs-minor per the negotiation; developer makes the final call.
  - **Step 6**: Present plan; **Step 7**: Add stories (unversioned during work, bundled release at end-of-phase per Version Cadence rule); **Step 8**: Present updated stories; **Step 9**: Append project-essentials new facts (parallel to `plan_phase`).
  - **Step 10**: Documents that end-of-phase release is via `project-guide bump-version <X.Y.Z>` (separate session).
- [x] **`project_guide/cli.py`** — added `bump_version` subcommand: `project-guide bump-version <X.Y.Z>` updates `pyproject.toml`'s `[project] version`, an auto-detected `__version__` source file (tries six candidate paths under `<package>/` and `src/<package>/`), and inserts a fresh `## [X.Y.Z] - YYYY-MM-DD` heading just below `## [Unreleased]` in `CHANGELOG.md`. Idempotent on re-run for the same version (date refreshed, body preserved). Validates semver format. Honors `--no-input` (missing positional → exit 2 with canonical error message) and `--quiet` (success-path stdout suppressed; errors and warnings remain on stderr). Three helper functions: `_bump_pyproject_version`, `_find_version_file`, `_bump_version_file`, `_bump_changelog`.
- [x] **`templates/modes/plan-phase-mode.md`** — inserted a new Step 1 ("Verify this is the right mode") that halts and recommends `plan_production_phase` if `pyproject.toml`'s version is `>= 1.0.0`. Renumbered subsequent steps to 2–8, updated internal cross-references ("from step 1" → "from step 2"; "see step 5" → "see step 6"). Updated Prerequisites prose to call out `plan_phase` as pre-1.0-only.
- [x] **`.metadata.yml`** — registered `plan_production_phase` mode entry (parallel structure to `plan_phase`); updated `plan_phase` description to call out it is pre-1.0-only.
- [x] **`project_guide/cli.py` `_MODE_CATEGORIES`** — registered `plan_production_phase` under "Post-Release" (will move to "Release Planning" in Story O.q).
- [x] **`developer/best-practices-guide.md`** — Velocity-vs-Production section gained a "How project-guide enforces the switch" paragraph cross-referencing `plan_production_phase` mode, `plan_phase`'s pre-1.0-only redirect, and `bump-version` as the end-of-phase release helper.
- [x] **Tests in `tests/test_render.py`** (5 new tests):
  - [x] `test_plan_production_phase_renders_successfully` — `project-guide mode plan_production_phase` produces a valid `go.md` with no unrendered Jinja placeholders.
  - [x] `test_plan_production_phase_carries_readiness_checklist` — pins all 7 load-bearing checklist items (branch protection, SECURITY.md, CONTRIBUTING.md, Dependabot, trusted publisher, mandatory CI).
  - [x] `test_plan_production_phase_breaking_change_negotiation` — pins the negotiation step name, the discretion principle ("substantively breaks user expectations" vs. "technically-but-trivially breaking"), and the log-format worked example.
  - [x] `test_plan_phase_redirects_post_1_0` — pins `plan_phase`'s new Step 1 language including `>= 1.0.0` threshold and `plan_production_phase` recommendation.
  - [x] `test_plan_production_phase_in_mode_listing` — `project-guide mode --no-input` output contains `plan_production_phase` (confirms metadata + `_MODE_CATEGORIES` registration).
- [x] **Tests in `tests/test_cli.py`** (6 new tests for `bump-version`):
  - [x] `test_bump_version_writes_three_files` — pins all three writes (pyproject.toml, version.py, CHANGELOG.md ordering: new section above older one).
  - [x] `test_bump_version_is_idempotent` — re-running with same version updates date, doesn't duplicate sections.
  - [x] `test_bump_version_rejects_invalid_semver` — non-semver argument fails with exit 2 and a clear message.
  - [x] `test_bump_version_no_input_contract` — `--no-input` without positional fails loud with exit 2; error message names the canonical fix.
  - [x] `test_bump_version_quiet_suppresses_success_stdout` — `--quiet` on a successful bump suppresses the success line.
  - [x] `test_bump_version_warns_when_no_version_file_found` — warns to stderr but pyproject + CHANGELOG still updated.
  - [x] All 446 prior tests still pass; full suite is **462 passed** (446 + 5 + 6 + 5 — the 5/6/5 split: 5 render, 6 CLI, plus 0 changes elsewhere).
- [x] **Re-rendered** dogfood `docs/project-guide/go.md` via `project-guide update`.
- [x] Updated CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.14**.

**Out of scope:**
- Auto-detecting whether the developer should run `plan_phase` or `plan_production_phase`. The version-comparison check in `plan_phase` halts and recommends; the developer initiates the mode change.
- Backfilling existing post-1.0 projects to use `plan_production_phase`. They opt in by switching modes; project-guide doesn't migrate them.

---

### Story O.q: v2.5.15 Mode reordering, section rename, and CLI help expansion [Done]

**Problem:** The `_MODE_CATEGORIES` and `_CATEGORY_ORDER` dicts in `cli.py` reflect an older organizational model. Three updates needed: (a) rename "Planning" → "Project Planning" (one-time-per-project work) and "Post-Release" → "Release Planning" (repeated work); (b) move `plan_phase` from Project Planning to Release Planning, register `plan_production_phase` (from O.p) under Release Planning; (c) reorder `_CATEGORY_ORDER` to match the lifecycle flow (Getting Started → Project Planning → Scaffold → Coding → Debugging → Documentation → Refactoring → Release Planning). Plus expand `mode` CLI help to enumerate the three invocation modes (positional / `--no-input` discovery / interactive menu) since the docstring is currently a single line.

**Tasks:**

- [x] **`project_guide/cli.py` `_MODE_CATEGORIES`** — renamed section labels: `"Planning"` → `"Project Planning"`, `"Post-Release"` → `"Release Planning"`. Moved `plan_phase` from Planning to Release Planning. Registered `plan_production_phase` under Release Planning. Added inline comments explaining each section's role.
- [x] **`project_guide/cli.py` `_CATEGORY_ORDER`** — reordered per lifecycle flow: `Getting Started → Project Planning → Scaffold → Coding → Debugging → Documentation → Refactoring → Release Planning → Other`.
- [x] **`project_guide/cli.py` `set_mode` docstring** — expanded from one line to a multi-paragraph block enumerating the three invocation paths (positional / `--no-input` / interactive menu) with worked-example syntax via Click `\b` blocks. Documents section ordering, per-mode markers (→ / ✓ / ✗), `--verbose` behavior, and `--no-input` auto-enable conditions (CI=1, non-TTY stdin).
- [x] **README mode list** — updated **Available Modes** section. Renamed "Planning Modes" → "Project Planning Modes" and "Post-Release Modes" → "Release Planning Modes". Added `plan_phase` (pre-1.0) and `plan_production_phase` (post-1.0 mandatory) under Release Planning Modes; removed `plan_phase` from Project Planning Modes. Added one-line role description above each section.
- [x] **`docs/specs/features.md`** FR-11 — updated section-grouping bullet to use new labels and ordering.
- [x] **`docs/specs/tech-spec.md`** — grep returned no matches for legacy labels; no update needed.
- [x] **Tests in `tests/test_cli.py`** (5 new tests):
  - [x] `test_mode_help_documents_three_invocation_paths` — pins all three worked-example syntaxes in `mode --help` output and the "interactive" keyword.
  - [x] `test_mode_listing_uses_renamed_sections` — pins presence of `Project Planning` and `Release Planning` headers; pins absence of legacy `Post-Release` standalone section heading.
  - [x] `test_mode_listing_section_order` — asserts ascending index order of all 8 section headings in the rendered listing.
  - [x] `test_plan_phase_in_release_planning_section` — confirms `plan_phase` appears after the Release Planning header.
  - [x] `test_plan_production_phase_registered_in_release_planning` — confirms `plan_production_phase` appears under Release Planning.
  - [x] All 462 prior tests still pass (substring-match assertions like `"Planning" in output` continue to hold against `Project Planning`); full suite is **467 passed**.
- [x] **Smoke test:** ran `project-guide init` + `project-guide mode --no-input` in a scratch directory; verified the rendered listing shows the lifecycle order (Getting Started → Project Planning → Scaffold → Coding → Debugging → Documentation → Refactoring → Release Planning) with `plan_phase` and `plan_production_phase` grouped under Release Planning alongside `archive_stories`.
- [x] Updated CHANGELOG and version bump: `project_guide/version.py`, `pyproject.toml`, `CHANGELOG.md` → **v2.5.15**.

**Out of scope:**
- Driving the section labels from a `section:` field in `.metadata.yml` (decentralizing what's currently centralized in `cli.py`). Possible future improvement; not needed for the rename + reorder fix.
- Renaming `plan_phase` itself. The mode keeps its name; only its section moves.

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
