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

## Future

### Code Mode Hierarchy [Deferred]

- `code_production` mode — blocked on further `code_*` abstraction work; revisit after N.d (`--test-first`) settles the mode-preference pattern.

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
