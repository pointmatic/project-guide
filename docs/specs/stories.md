# stories.md — project-guide (Python)

This document breaks the `project-guide` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Stories with code changes include a version number (e.g., v0.1.0). Stories with only documentation or polish changes omit the version number. The version follows semantic versioning and is bumped per story. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

---

## Phase K: Release & Phase Lifecycle (v2.1.0)

Close the lifecycle gap so the next phase can start with a clean slate. Introduce `archive_stories` mode, codify the phase letter scheme and `## Future` section, teach `default` mode to suggest a next move when all stories are `[Done]`, and update `plan_phase` to continue phase letters across an archive boundary. See `phase-k-release-lifecycle-plan.md` for full details.

**Implementation strategy:** Spike first (K.a) with a throwaway script that exercises the full archive flow end-to-end — version derivation, file move, template re-render, `## Future` carry-over — before introducing the new `archive` action type or the productionized mode.

Out of scope (deferred to later phases): release/version-bump/tag automation (developer works across multiple git flows and prefers tool-agnostic), `code_production` mode and `code_*` abstraction, audit modes.

### Story K.a: v2.1.0 End-to-End Spike — archive_stories Flow [Done]

Wire the full archive pipeline end-to-end as a throwaway script in `scripts/`, before any productionized mode template, metadata entry, or new action type. Validates the critical path: detect latest version from a fixture `stories.md`, detect latest phase letter, move to `.archive/stories-vX.Y.Z.md`, re-render an empty `stories.md` with the carried-over `## Future` section.

- [x] Create `scripts/spike_archive_stories.py` (throwaway, not part of the package)
- [x] Implement latest-version detection by scanning `stories.md` for `v\d+\.\d+\.\d+` story headings
- [x] Implement latest-phase-letter detection by scanning `## Phase <Letter>:` headings
- [x] Implement `## Future` section extraction (everything from `## Future` to EOF)
- [x] Implement archive move: create `.archive/` if missing, move `stories.md` → `.archive/stories-vX.Y.Z.md`
- [x] Implement fresh `stories.md` re-render from the artifact template with the extracted `## Future` content re-injected
- [x] Run against a fixture `stories.md` (copy of pre-archive Phase J file) and verify round-trip
- [x] Verify: archived file matches original; new `stories.md` is empty body + carried `## Future`
- [x] Document spike findings in the story's commit message (decisions to carry into K.c/K.d)

### Story K.b: v2.1.1 Codify Phase Letter Scheme and Future Section [Done]

Move the phase letter rules into a shared include and codify the `## Future` section in the stories artifact template so both planning and post-archive flows reference one source.

- [x] Create `project_guide/templates/project-guide/templates/modes/_phase-letters.md` shared include
  - [x] Document phase letter scheme: `A`–`Z`, then `AA`, `AB`, …, `AZ`, `BA`, … (base-26, no zero)
  - [x] Document story sub-letter scheme: `A.a`–`A.z`, then `A.aa`, `A.ab`, …
  - [x] Note that letters continue across archive boundaries (read `.archive/` to find the latest)
- [x] Update `project_guide/templates/project-guide/templates/artifacts/stories.md` to include a `## Future` section after `{{ phases_and_stories }}`
  - [x] Add a brief inline note describing what belongs there (deferred stories, future phases, project-level out-of-scope items)
- [x] Update `project_guide/templates/project-guide/templates/modes/plan-stories-mode.md` to include `_phase-letters.md`
- [x] Update `project_guide/templates/project-guide/templates/modes/plan-phase-mode.md` to include `_phase-letters.md`
- [x] Verify: rendered `plan_stories` mode and `plan_phase` mode both contain the phase letter rules exactly once (story originally said `default`, corrected — `default` was a typo for `plan_stories`, which is where the rules belong)
- [x] Add tests for the updated `stories.md` artifact template (renders with empty and populated `## Future`)

### Story K.c: v2.1.2 Archive Action Type [Done]

Add a new `archive` action type to the metadata schema and action handler. Carries the version-derivation and move-and-recreate semantics validated in K.a.

- [x] Extend `project_guide/metadata.py` to recognize `action: archive` on artifacts (shared `VALID_ARTIFACT_ACTIONS` constant lives in `project_guide/actions.py`; `metadata.py` imports it and validates any `action:` value against the set, tolerating artifacts without an `action:` field)
- [x] Implement archive action semantics: derive version from latest story in source file, move to `<dirname>/.archive/<basename>-vX.Y.Z.md`, re-render fresh artifact preserving `## Future` (new `project_guide/actions.py` module; `perform_archive` returns an `ArchiveResult` dataclass; best-effort rollback restores the source if the fresh re-render fails)
- [x] Add validation: `archive` action requires the source file to exist (runtime check in `perform_archive`; also validates the artifact template path so a broken install errors cleanly before mutating state)
- [x] Unit tests for version derivation (single story, multiple stories, no versioned stories) — 4 tests including a "prose mentions v99.99.99" negative case
- [x] Unit tests for phase letter derivation (single phase, multiple phases, post-Z letters) — 5 tests including `Z < AA < AB` and `ZZ < AAA`
- [x] Unit tests for `## Future` extraction and re-injection (present, absent, empty) — 3 extraction tests + 2 render-fresh tests covering default vs carried Future blocks
- [x] Unit tests for the archive action against a fixture `stories.md` — 6 tests: happy path, no-Future case, missing source, existing archive target, missing template, no-versions-in-source, plus a real-file round-trip against `.archive/stories-v2.0.20.md` (Phase J)
- [x] Verify: existing `create` and `modify` action types still work unchanged — 3 new metadata tests (valid archive, valid create/modify round-trip, missing action tolerated, unknown action rejected)

### Story K.d: v2.1.3 archive_stories Mode [Done]

Productionize the `archive_stories` mode using the `archive` action type and `_phase-letters.md` include from prior stories.

- [x] Create `project_guide/templates/project-guide/templates/modes/archive-stories-mode.md` (sequence-style, uses `_header-sequence.md` and `_phase-letters.md`)
- [x] Mode steps: read `stories.md`, warn if any non-`[Done]` stories, show planned archive path, await confirmation, perform archive, suggest `plan_phase`
- [x] Add `archive_stories` entry to `project_guide/templates/project-guide/.metadata.yml` under the `# Post-Release` section with `action: archive` on `stories.md`, `next_mode: plan_phase`, and `files_exist: [stories.md]` prerequisite
- [x] Integration test: render `archive_stories` mode, execute against a fixture, verify the archived file and the fresh `stories.md` (new `tests/test_archive_stories_mode.py` — 9 tests covering mode rendering, prereq warning, happy path, no-Future fallback, and 4 error paths)
- [x] Delete `scripts/spike_archive_stories.py` (now superseded); empty `scripts/` directory also removed
- [x] Verify: `project-guide mode archive_stories` + `project-guide archive-stories` works end-to-end on a clean test project
- [x] **Additional scope**: new `project-guide archive-stories` CLI command introduced to bridge the LLM-facing mode template and the deterministic `perform_archive` action. The mode template instructs the LLM to run this command after developer approval. Clean separation: template = conversational, CLI = transactional.
- [x] **Additional scope**: `render_fresh_stories_artifact` now uses a local `_LenientUndefined` so missing Jinja context variables render as `{{ name }}` placeholders instead of empty strings.
- [x] **Additional scope**: new `extract_stories_header_context(text)` parser in `actions.py` auto-extracts `project_name` and `programming_language` from the source stories.md first-line header (`# stories.md -- <name> (<lang>)`); `perform_archive` merges extracted values with the caller's context (caller wins) so the fresh re-render preserves the header.

### Story K.e: v2.1.4 plan_phase Post-Archive Support [Done]

Update `plan_phase` to handle an empty `stories.md` and continue phase letters from `.archive/` when present.

- [x] Update `project_guide/templates/project-guide/templates/modes/plan-phase-mode.md` to handle the empty-`stories.md` case explicitly (Step 1 now distinguishes "Populated" vs "Empty (post-archive)" shapes; Step 5 instructs the LLM to insert the new phase as the first phase if `stories.md` was empty)
- [x] Document the `.archive/` lookup: read `.archive/stories-vX.Y.Z.md` (latest by version) and parse the highest phase letter to determine the next letter (template prose plus a Python implementation: `next_phase_letter(stories_text, archive_dir)` in `actions.py` for future tooling use)
- [x] Reference `_phase-letters.md` for the letter rules rather than restating them (Step 5 prose says "see the Phase and Story ID Scheme below"; the include is rendered once at the end of the mode template)
- [x] Add a fixture test: empty `stories.md` + `.archive/stories-v2.0.20.md` containing Phase J → next phase letter is `K` (`test_next_phase_letter_empty_stories_with_phase_j_archive_returns_k`)
- [x] Add a fixture test: empty `stories.md` + no `.archive/` → next phase letter is `A` (`test_next_phase_letter_empty_stories_no_archive_returns_a`)
- [x] Verify: rendered `plan_phase` mode correctly references the include and the archive lookup (manually verified via `runner.isolated_filesystem` invocation: contains `## Phase and Story ID Scheme` exactly once, mentions `.archive/`, "Empty (post-archive)", and "continue across the archive boundary")
- [x] **Additional scope**: new `increment_phase_letter(letter)` helper in `actions.py` implements the base-26-no-zero successor algorithm (`A→B`, `Z→AA`, `ZZ→AAA`); tested with 7 cases including invalid inputs.
- [x] **Additional scope**: new `_find_latest_archived_stories(archive_dir)` helper filters `.archive/` to `stories-vX.Y.Z.md` files only, ignoring unrelated artifacts (`phase-j-modes-plan.md`, `ux-problems-v2.0.10.md`); tested with mixed-content archive directories.

### Story K.f: v2.1.5 Default Mode All-Stories-Done Suggestion [Done]

Teach `default` mode to detect when all stories are `[Done]` and prompt the developer to choose between `archive_stories` and `plan_phase`.

- [x] Update `project_guide/templates/project-guide/templates/modes/default-mode.md` with an "If all stories are [Done]" section (new top-level "Suggesting the Next Step" section with three branches: all-Done, at-least-one-non-Done, no-stories.md)
- [x] Detection performed by the LLM at read time (consistent with v2 architecture — no Python-side check)
- [x] Prompt suggests both `archive_stories` (clean slate first) and `plan_phase` (plan against history first), explaining the trade-off (Option A vs Option B with "Use this when:" guidance for each)
- [x] If at least one story is non-`[Done]`, the existing default lifecycle suggestions apply unchanged (the at-least-one-non-Done branch defers to the existing project lifecycle table at the top of the mode)
- [x] Verify by manually rendering `default` mode against (a) a fresh project (verified via `runner.isolated_filesystem` — rendered guide contains "fresh project" hint and the all-Done section), (b) an in-progress project (LLM-runtime branch — verified by reading the rendered template language), (c) a fully-`[Done]` project (LLM-runtime branch — verified by reading the rendered template language). All three scenarios are LLM-driven at read time per the v2 architecture; the rendered template contains the prompt language for all three branches simultaneously.

### Story K.g: v2.1.6 Phase K Documentation and CHANGELOG [Done]

- [x] Add `archive_stories` to the modes catalogue (sources identified: `docs/site/user-guide/modes.md` gets a new "Post-Release Modes" section with a full `archive_stories` reference entry; `docs/site/user-guide/workflow.md` gets a new Post-Release bullet in the Modes section and a new row in the "When to Switch Modes" table; `plan_phase` entry in `modes.md` updated to mention the two `stories.md` shapes — populated vs empty post-archive — and the archive-boundary lookup)
- [x] Update `project_guide/templates/project-guide/templates/modes/default-mode.md` "All Available Modes" table with the new mode under a new "Post-Release (sequence)" section
- [x] Update `CHANGELOG.md` with v2.1.0–v2.1.5 entries (already present from prior stories) and add a v2.1.6 entry for the K.g documentation pass
- [x] Update README if any user-facing wording references the lifecycle workflow:
  - Key Features: "15 modes" → "16 modes"; "Eight intuitive commands" → "Nine"; "91% test coverage with 131 comprehensive tests" → "Comprehensive test coverage across CLI, rendering, and action modules" (avoids future drift from hard-coded counts)
  - Quick Start mode list: added `archive_stories` and `project_scaffold` (the latter was already missing — fixed during this story)
  - Available Modes section: added a new "Post-Release Modes" table with `archive_stories`
  - Command Reference: new `archive-stories` CLI section describing the 5-step pipeline, pre-check failure behavior, rollback-on-failure semantics, and the LLM-runs-after-approval usage pattern
- [x] Verify: `project-guide --help` lists `archive-stories` as a top-level command; `project-guide mode` (when initialized) lists `archive_stories` in the mode catalogue; `project-guide archive-stories --help` works (all three verified via `click.testing.CliRunner`)

---

## Phase L: `project-guide init --no-input` Mode (v2.2.0)

Make `project-guide init` safe to run unattended — from CI, scripts, or as a post-hook from `pyve init` — without hanging on stdin or failing on re-run. Introduce a `--no-input` flag, a shared `should_skip_input()` helper that also auto-detects `CI=1` / `PROJECT_GUIDE_NO_INPUT=1` / non-TTY stdin, and (the actual blocker for pyve integration) make re-running `init` on an already-initialized project a silent exit-0 no-op instead of the current `click.Abort()`. See `phase-l-no-input-init-plan.md` and the upstream spec `project-guide-no-input-spec.md` for full details.

**Implementation strategy:** No spike — the integration boundary (`sys.stdin.isatty()`, env vars, click options) is stdlib-level and the upstream spec already serves as the design validation. Stories are ordered by risk: L.a is the small behavioral fix that unblocks pyve today; L.b lands the `--no-input` surface and the future-proofing contract; L.c is the documentation pass.

Out of scope (deferred): `--no-input` for `purge`/`update` (not on the pyve integration path), a `--quiet` flag for output suppression (spec explicitly says `--no-input` affects stdin only), a `create_or_modify` action type, legacy broken-state detection where `.project-guide.yml` is absent but the target directory is populated.

### Story L.a: v2.2.0 Idempotent init Re-run [Planned]

Change `project-guide init` to exit 0 silently when the project is already initialized, instead of the current `click.Abort()` on `.project-guide.yml` existing. This is the small, focused fix that actually unblocks the pyve post-hook integration — `--no-input` plumbing comes next in L.b.

- [ ] Replace the abort-on-exists path in `project_guide/cli.py:init` (lines ~90-96)
  - [ ] If `.project-guide.yml` exists and `--force` is not given: print `project-guide already initialized at <target_dir>/ (use --force to reinitialize).` to stdout and `return` (exit 0)
  - [ ] If `.project-guide.yml` exists and `--force` is given: current overwrite behavior unchanged
  - [ ] If `.project-guide.yml` does not exist: current behavior unchanged
  - [ ] Decision rationale: idempotency check is based solely on `.project-guide.yml` presence. Partial-install state (config absent but target directory populated) falls through to the existing `_copy_template_tree` skip-with-warnings path — documented as out of scope in the phase plan
- [ ] Update `tests/test_cli.py` init test that currently expects `click.Abort()` / exit 1 on re-init → change expectation to exit 0 with the "already initialized" message on stdout
- [ ] Add new test: re-running `init` twice in a row produces exit 0 both times, and the second run does not modify any files (verify via `mtime` or file hash on a tracked template file)
- [ ] Add new test: `init --force` on an initialized project still overwrites (regression guard for the `--force` branch)
- [ ] Verify: `project-guide init && project-guide init` succeeds end-to-end in a `CliRunner.isolated_filesystem()`

### Story L.b: v2.2.1 --no-input Flag, Trigger Helper, and Prompt Contract [Planned]

Add the `--no-input` flag to `init`, land the shared `should_skip_input()` helper, and establish the missing-required-setting contract for any prompt that gets added to `init` in the future. Because `init` has no interactive prompts today, this story is plumbing + contract + regression-guard tests — no production prompt code exercises the contract yet, but the helper is the single idiom every future prompt must use.

- [ ] Create `project_guide/runtime.py` with `should_skip_input(flag: bool = False) -> bool`
  - [ ] Trigger priority (first match wins): explicit `flag` → `PROJECT_GUIDE_NO_INPUT` env var → `CI` env var → `sys.stdin.isatty() == False` → otherwise interactive
  - [ ] Env-var truthiness: case-insensitive match against `{"1", "true", "yes", "on"}`
  - [ ] Safely handle the edge case where `sys.stdin` is `None` or closed (subprocess contexts): catch `AttributeError`/`ValueError` and treat as non-TTY
- [ ] Add `--no-input` click option to `init` in `project_guide/cli.py`
  - [ ] Boolean flag, default `False`, no short form
  - [ ] Help text: "Do not read from stdin; use defaults where sensible. Fail loudly if any prompt has no default. (Also auto-enabled by CI=1 or non-TTY stdin.)"
  - [ ] Compute `skip_input = should_skip_input(no_input)` early in `init` — threads through for future prompt sites
- [ ] Add a module-level helper (or `click.ClickException` subclass) `_require_setting(name: str, cli_flag: str, env_var: str)` that raises with the message: `<name> is required when --no-input is active. Provide via --<cli_flag> or <env_var>.` and causes exit code 1. This is the landing spot for future prompt call sites.
- [ ] Create `tests/test_runtime.py`:
  - [ ] `should_skip_input(True)` returns `True` regardless of env/TTY
  - [ ] `PROJECT_GUIDE_NO_INPUT=1` (and `true`, `YES`, `on`) returns `True`; empty/unset returns fall-through behavior
  - [ ] `CI=1` returns `True` when flag and `PROJECT_GUIDE_NO_INPUT` are not set
  - [ ] Non-TTY stdin returns `True` when nothing else is set (monkeypatch `sys.stdin.isatty`)
  - [ ] Priority order: flag beats env, env beats CI, CI beats TTY
  - [ ] Safety: stdin `None` or closed returns `True` (non-TTY fallback)
- [ ] Add to `tests/test_cli.py`:
  - [ ] `init --no-input` on a fresh project → normal install, exit 0
  - [ ] `init --no-input --force` on an initialized project → overwrite, exit 0
  - [ ] `init` with `CI=1` env var (via `monkeypatch.setenv`) behaves the same as `--no-input` — specifically, it still exits 0 on re-run per L.a (idempotency + auto-detection compose cleanly)
  - [ ] `init` with non-TTY stdin (via `CliRunner(input=...)`) behaves the same as `--no-input`
  - [ ] Regression guard for the FR-L4 contract: a unit test that injects a dummy prompt through `_require_setting` verifies the exit-1 path and the exact error message format. This is the guard that protects the contract the day someone adds a real prompt to `init`.
- [ ] Verify: `CI=1 project-guide init` and `project-guide init --no-input` both work end-to-end on a fresh fixture project

### Story L.c: v2.2.2 Phase L Documentation and CHANGELOG [Planned]

- [ ] Update `README.md` with a short "Unattended / CI use" subsection
  - [ ] Show all four trigger mechanisms with one example each: `--no-input`, `PROJECT_GUIDE_NO_INPUT=1`, `CI=1`, non-TTY (piped stdin)
  - [ ] Note idempotent re-run: `project-guide init` on an initialized project is a no-op
- [ ] Update MkDocs command reference for `init` to document `--no-input` and the auto-detection behavior
- [ ] Update `docs/specs/project-guide-no-input-spec.md` status line from `Proposed (2026-04-10)` to `Implemented in v2.2.0–v2.2.1`
- [ ] Update `CHANGELOG.md` with two bullets (separated so pyve can cite the exact semantics it depends on):
  - [ ] v2.2.0: `init` is now idempotent — re-running on an initialized project is a silent exit-0 no-op
  - [ ] v2.2.1: New `--no-input` flag on `init` with env-var (`PROJECT_GUIDE_NO_INPUT`, `CI`) and non-TTY auto-detection
- [ ] Verify: `project-guide init --help` shows the new `--no-input` flag and correct help text
- [ ] Verify: the rendered `default` mode (and any planning mode) is unchanged by this phase — Phase L touches only `cli.py`, `runtime.py`, and docs

---

## Phase M: Project Essentials Integration (v2.3.0)

Establish `docs/specs/project-essentials.md` as a per-project artifact that captures must-know facts future LLMs need to avoid blunders (workflow rules, architecture quirks, hidden coupling, dogfooding/meta notes), then wire the three planning modes (`plan_tech_spec`, `refactor_plan`, `plan_phase`) to populate and maintain it over the project lifecycle. M.a ships the placeholder + render hook + dogfoods the artifact for this project; M.b generalizes M.a's regression guard into a project-wide post-render placeholder validator; M.c–M.e wire the planning modes; M.f is the documentation pass. See `phase-m-project-essentials-plan.md` for full details.

> **Renumbering note:** This phase was originally drafted as Phase L on 2026-04-10. It was renumbered to Phase M on 2026-04-11 when a new Phase L (`project-guide init --no-input` mode) was inserted ahead of it. At the same time, stories M.a and M.b were moved out of Phase K (where they had been planned as K.h and K.i) and absorbed into this phase, because they are thematically part of the project-essentials integration rather than the K release-lifecycle work.

**Implementation strategy:** No spike — the integration boundary (the `project_essentials` render context variable) is validated by M.a's own tests. Ordering is load-bearing only within two pairs: M.a must ship before M.b (the validator generalizes M.a's regression guard), and M.a must ship before M.c/M.d/M.e (nothing to populate otherwise). M.c/M.d/M.e are mutually independent and can ship in any order; the listed order matches the project lifecycle (initial → refactor → per-phase).

Out of scope (deferred or already covered): a dedicated `refactor_essentials` mode (not needed; the three planning modes cover the lifecycle), a `create_or_modify` action type (mode templates handle existence-checking conversationally), validation/linting of `project-essentials.md` content (the artifact is freeform by design), support for literal `{{ var }}` strings as rendered output (documented as a known M.b limitation).

### Story M.a: v2.3.0 project-essentials.md Placeholder and Render Hook [Planned]

Establish a per-project `project-essentials.md` artifact that gets injected into every rendered mode via `_header-common.md`. Empty/missing renders cleanly, content (when present) appears as a `## Project Essentials` section in every mode. This story lays the rails and dogfoods it for this project; M.c–M.e wire the planning modes to populate it. *(Originally planned as Phase K story K.h.)*

- [ ] Create `project_guide/templates/project-guide/templates/artifacts/project-essentials.md`
  - [ ] Empty body with a brief comment block describing what belongs there: workflow rules, architecture quirks, domain conventions, hidden coupling, dogfooding/meta notes
  - [ ] Note that an empty file is acceptable
- [ ] Update `project_guide/render.py` to read `<spec_artifacts_path>/project-essentials.md` if present
  - [ ] Pass content as the `project_essentials` Jinja2 context variable
  - [ ] Default to empty string when the file is missing or empty (no error)
- [ ] Update `project_guide/templates/project-guide/templates/modes/_header-common.md`
  - [ ] After the **Rules** section and before the `# {{ mode_name }} mode` heading, render `{% if project_essentials %}## Project Essentials\n\n{{ project_essentials }}\n\n---\n{% endif %}` (or equivalent — section omitted entirely when empty)
- [ ] Tests in `tests/test_render.py`:
  - [ ] Rendered output contains `## Project Essentials` when fixture file is non-empty
  - [ ] Rendered output omits the section when fixture file is empty
  - [ ] Rendered output omits the section when fixture file is missing (no error)
  - [ ] **Regression guard** (temporary — removed by M.b once the general validator is in place): rendered output never contains the literal string `{{ project_essentials }}` in any of the above cases. This catches a future template edit that removes the `{% if %}` guard, since `_LenientUndefined.__str__` would otherwise render the placeholder verbatim. See `render.py:83-99`.
- [ ] Populate `docs/specs/project-essentials.md` for this project with current must-know facts:
  - [ ] Dogfooding rule: edit templates under `project_guide/templates/project-guide/`, never `docs/project-guide/` (the installed copy)
  - [ ] Workflow rule: pyve has **two** environments — main `.venv/` (runtime only) and `.pyve/testenv/venv/` (dev tools: pytest, ruff, mypy). Canonical commands:
    - Runtime code: `pyve run python ...`, `pyve run project-guide ...`
    - Tests: `pyve test [pytest args]` (NOT `pyve run pytest` — pytest is not in the main venv)
    - Lint / type-check: `.pyve/testenv/venv/bin/ruff check ...`, `.pyve/testenv/venv/bin/mypy ...`
    - Install dev tools: `pyve testenv --install -r requirements-dev.txt` (NEVER `pip install -e ".[dev]"` into the main venv — that pollutes runtime deps)
  - [ ] `docs/project-guide/go.md` is dynamically re-rendered by the `mode` command — never hand-edit
  - [ ] (Add others if any surface during the story)
- [ ] Verify by running `project-guide mode default` (or any mode) and inspecting `docs/project-guide/go.md` for the rendered Project Essentials section
- [ ] Note: do **not** add `project-essentials.md` as a tracked artifact in any mode's `.metadata.yml` entry yet — that wiring is M.c–M.e's responsibility

### Story M.b: v2.3.1 Render Output Validation — Fail on Unrendered Placeholders [Planned]

Generalize the M.a `{{ project_essentials }}` regression guard into a project-wide safeguard. After every render, scan the output for any remaining `{{ identifier }}` Jinja-style placeholders. If any are found, raise `RenderError` with the placeholder names. This catches missed intents (a context variable that should have been set), typos (`{{ project_essentialss }}`), and removed `{% if %}` guards across **all** templates, not just `_header-common.md`. The current `_LenientUndefined` class (`render.py:83-99`) outputs `{{ var_name }}` for undefined variables — this story turns that observation into a hard error gate. Lenient mode itself stays unchanged because its placeholder output is what makes the validator's job possible. *(Originally planned as Phase K story K.i.)*

- [ ] Add a post-render validation function in `project_guide/render.py`
  - [ ] Regex: `\{\{\s*[a-zA-Z_]\w*\s*\}\}` (matches `{{var}}`, `{{ var }}`, `{{  var  }}`)
  - [ ] Scan the rendered string after Jinja produces output, before writing the file
  - [ ] If matches found, raise `RenderError` with the list of placeholder names and a hint message: "Check (1) render.py context variables and (2) template variable spellings"
- [ ] Call the validator inside `render_go_project_guide` after `template.render(...)` but before `output_path.write_text(...)`
- [ ] Tests in `tests/test_render.py`:
  - [ ] Rendering a template that references an undefined variable raises `RenderError`
  - [ ] Error message includes the offending placeholder name
  - [ ] Rendering with all variables defined succeeds (existing parametrized mode test should still pass)
  - [ ] Validator does not raise on templates with no Jinja variables at all
- [ ] Remove the now-redundant `{{ project_essentials }}` regression-guard assertion added in M.a (the generalized validator subsumes it). Leave a brief comment in the test file noting the validator covers this case.
- [ ] Audit existing mode templates and `_header-common.md` to confirm none rely on undefined variables silently passing through. Fix any that do.
- [ ] Verify: running `project-guide mode default` and `project-guide mode plan_concept` still produces valid `go.md` output with no errors
- [ ] Document the limitation in a code comment: templates that legitimately want to emit literal `{{ var }}` strings (e.g., documentation of Jinja syntax) will trigger false positives. Not currently a problem; bridge if/when needed.

### Story M.c: v2.3.2 plan_tech_spec Populates project-essentials.md [Planned]

After the tech-spec is approved, prompt the developer to capture any project-specific must-know facts and write them to `docs/specs/project-essentials.md`.

- [ ] Update `project_guide/templates/project-guide/templates/modes/plan-tech-spec-mode.md` to add a final step after tech-spec approval
- [ ] Step asks the developer for project-essentials content with **concrete worked examples** in the prompt (not just abstract categories — the LLM should put these specific scenarios in front of the developer to jog their memory):
  - **Workflow rules — tool wrappers and environment conventions.** A common source of "random walks" by LLMs: multiple invocation forms all *work*, but only one is canonical. Capture which form to use so the LLM doesn't pick whatever happens to succeed first:
    - *Python invocation*: wrapper command (e.g., `pyve run python ...`, `poetry run python ...`, `hatch run python ...`, `uv run python ...`) vs `python -m ...` vs `.venv/bin/python ...`. All may execute, but only one matches the project's setup.
    - *Dev tool installation*: dedicated dev/test environment (e.g., `pyve testenv --install`, `poetry install --with dev`, `uv sync --extra dev`) vs `pip install -e ".[dev]"` into the main venv. Different isolation guarantees — the latter pollutes the runtime venv.
    - *Test invocation*: project-specific runner (e.g., `pyve test`, `poetry run pytest`, `make test`) vs bare `pytest`. Bare `pytest` may fail because the tool isn't in the active venv — that's a signal to use the wrapper, not to `pip install pytest`.
    - **Principle:** legitimate alternatives exist, but they should be intentional choices, not a random walk to whatever works.
  - **Architecture quirks** (e.g., source-of-truth vs generated/installed file locations — edit the source, not the copy; build outputs that get regenerated)
  - **Domain conventions** (e.g., money stored in cents, all timestamps UTC, IDs are strings not ints)
  - **Hidden coupling** (e.g., files that mirror each other, auto-generated code, regenerated outputs that look hand-edited)
  - **Skip if there are none — empty is fine**
- [ ] Generate `docs/specs/project-essentials.md` from the artifact template only if the developer provides facts; otherwise leave the file empty (or skip creation entirely)
- [ ] Add `project-essentials.md` to `plan_tech_spec`'s `artifacts` list in `project_guide/templates/project-guide/.metadata.yml` with `action: create`
- [ ] Tests for the rendered mode template containing the new prompt
- [ ] Verify: running `project-guide mode plan_tech_spec` end-to-end on a fixture project includes the essentials prompt

### Story M.d: v2.3.3 refactor_plan Refreshes project-essentials.md [Planned]

When `refactor_plan` updates the concept/features/tech-spec, give the developer a chance to refresh `project-essentials.md` for any architecture or workflow changes that affect must-know facts.

- [ ] Update `project_guide/templates/project-guide/templates/modes/refactor-plan-mode.md` to add a cycle step (or extend Step 1) for revisiting project-essentials
- [ ] Prompt should ask whether the refactor changed any facts the LLM must know, with **concrete worked examples** (not just "tool wrapper, renamed module, changed conventions"):
  - *Switched or added an environment manager* (e.g., adopted `pyve`, `uv`, `poetry`, `hatch` — capture the canonical Python invocation and dev-tool install commands)
  - *Split runtime from dev environment* (e.g., dev tools moved out of main venv into a dedicated testenv — capture which commands target which env, and explicitly note the **anti-pattern** to avoid like `pip install -e ".[dev]"` into the runtime venv)
  - *Renamed module or moved source-of-truth* (e.g., template source moved from `docs/` to `project_guide/templates/` — capture so the LLM doesn't edit the installed copy)
  - *Changed domain conventions* (e.g., money representation changed from float to cents)
  - *New auto-generated or hidden-coupling files* (e.g., a new build step regenerates a file that looks hand-edited)
  - **Principle**: if the refactor introduced a fork-in-the-road where the wrong choice still "works," that's a project-essential.
- [ ] Mode template handles the case where `project-essentials.md` does not yet exist (legacy project): create from artifact template, then populate. Legacy projects are the most likely to need a first-time capture of these conventions, so the prompt should be especially explicit in that branch.
- [ ] Mode template handles the case where it exists: read, modify, write
- [ ] Add `project-essentials.md` to `refactor_plan`'s `artifacts` list in `.metadata.yml` with `action: modify`
- [ ] Tests for the rendered mode template
- [ ] Verify: rendered `refactor_plan` mode includes the revisit step

### Story M.e: v2.3.4 plan_phase Appends to project-essentials.md [Planned]

When `plan_phase` plans a new phase, prompt the developer to append any new must-know facts the phase introduces.

- [ ] Update `project_guide/templates/project-guide/templates/modes/plan-phase-mode.md` to add a step after phase approval
- [ ] Prompt: "Does this phase introduce any new must-know facts that should be added to project-essentials.md? (e.g., new architecture, new workflow rule, new gotcha)"
- [ ] Append (do not overwrite) to `project-essentials.md` if the developer provides facts
- [ ] Mode template handles the create case for legacy projects (file does not yet exist)
- [ ] Add `project-essentials.md` to `plan_phase`'s `artifacts` list in `.metadata.yml` with `action: modify`
- [ ] Tests for the rendered mode template
- [ ] Verify: rendered `plan_phase` mode includes the append prompt

### Story M.f: v2.3.5 Phase M Documentation and CHANGELOG [Planned]

- [ ] Add `project-essentials.md` to the artifacts catalogue (wherever artifacts are listed in `project_guide/templates/project-guide/`)
- [ ] Cross-reference `project-essentials.md` from `concept.md`, `features.md`, and/or `tech-spec.md` artifact templates if appropriate (a one-line "see also")
- [ ] Update `CHANGELOG.md` with v2.3.0–v2.3.4 entries
- [ ] Update README if any user-facing wording references the new artifact
- [ ] Verify by running each of the three updated planning modes against a fresh fixture project

---

## Future

### Change "code_velocity" to "code_direct" [Deferred]

"velocity" isn't the right word and doesn't pair well with "code_test_first". The "direct" mode should be the default mode for coding.

### Test First flag [Deferred]

Add a `--test-first` flag to the `init` command that causes coding to prefer `code_test_first` whenever `code_direct` would have been chosen as a next step. This involves abstracting out the `code_*` mode and paves the way for a future `code_production` mode.

### Code Production Mode [Deferred]

Implement the `code_production` mode...TBD

### Audit Modes [Deferred]

Future modes (deferred): `audit_security`, `audit_architecture`, `audit_performance`, `audit_best_practices`, `audit_modularity`, `audit_patterns`

### Out of Scope for Phase J

- Mode auto-detection from `files_exist` prerequisites (future advanced feature)
- Interactive mode menu (deferred — direct `mode <name>` argument is sufficient for v2.0.0)
- LLM API calls for artifact generation (future — currently the LLM fills in variables conversationally)
- Per-project metadata overrides in `.project-guide.yml` (future — metadata.yml is the single source for now)
- Migration tooling for `docs/guides/` → `docs/project-guide/` (future `refactor` mode)
- Story detection in `status` command (nice-to-have, can be added in a follow-up phase)
- Future modes: `code_production`, `audit_*`, `refactor_*`

