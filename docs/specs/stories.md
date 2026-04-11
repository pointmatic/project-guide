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

### Story L.a: v2.2.0 Idempotent init Re-run [Done]

Change `project-guide init` to exit 0 silently when the project is already initialized, instead of the current `click.Abort()` on `.project-guide.yml` existing. This is the small, focused fix that actually unblocks the pyve post-hook integration — `--no-input` plumbing comes next in L.b.

- [x] Replace the abort-on-exists path in `project_guide/cli.py:init` (lines ~90-96)
  - [x] If `.project-guide.yml` exists and `--force` is not given: print `project-guide already initialized at <target_dir>/ (use --force to reinitialize).` to stdout and `return` (exit 0)
  - [x] If `.project-guide.yml` exists and `--force` is given: current overwrite behavior unchanged
  - [x] If `.project-guide.yml` does not exist: current behavior unchanged
  - [x] Decision rationale: idempotency check is based solely on `.project-guide.yml` presence. Partial-install state (config absent but target directory populated) falls through to the existing `_copy_template_tree` skip-with-warnings path — documented as out of scope in the phase plan
- [x] Update `tests/test_cli.py` init test that currently expects `click.Abort()` / exit 1 on re-init → change expectation to exit 0 with the "already initialized" message on stdout (renamed to `test_init_on_already_initialized_project_is_idempotent`)
- [x] Add new test: re-running `init` twice in a row produces exit 0 both times, and the second run does not modify any files (new `test_init_double_run_does_not_modify_files` — snapshots `st_mtime_ns` of `.project-guide.yml`, `.metadata.yml`, and two mode templates)
- [x] Add new test: `init --force` on an initialized project still overwrites (regression guard for the `--force` branch) — the existing `test_init_with_force_flag` already covers this; verified unchanged
- [x] Verify: `project-guide init && project-guide init` succeeds end-to-end in a `CliRunner.isolated_filesystem()` (covered by the two idempotency tests)

### Story L.b: v2.2.1 --no-input Flag, Trigger Helper, and Prompt Contract [Done]

Add the `--no-input` flag to `init`, land the shared `should_skip_input()` helper, and establish the missing-required-setting contract for any prompt that gets added to `init` in the future. Because `init` has no interactive prompts today, this story is plumbing + contract + regression-guard tests — no production prompt code exercises the contract yet, but the helper is the single idiom every future prompt must use.

- [x] Create `project_guide/runtime.py` with `should_skip_input(flag: bool = False) -> bool`
  - [x] Trigger priority (first match wins): explicit `flag` → `PROJECT_GUIDE_NO_INPUT` env var → `CI` env var → `sys.stdin.isatty() == False` → otherwise interactive
  - [x] Env-var truthiness: case-insensitive match against `{"1", "true", "yes", "on"}` (implemented as `_TRUTHY_ENV_VALUES` module-level frozenset)
  - [x] Safely handle the edge case where `sys.stdin` is `None` or closed (subprocess contexts): catch `AttributeError`/`ValueError` and treat as non-TTY (`_stdin_is_non_tty` helper)
- [x] Add `--no-input` click option to `init` in `project_guide/cli.py`
  - [x] Boolean flag, default `False`, no short form
  - [x] Help text: "Do not read from stdin; use defaults where sensible. Fail loudly if any prompt has no default. (Also auto-enabled by CI=1 or non-TTY stdin.)"
  - [x] Compute `skip_input = should_skip_input(no_input)` early in `init` — threads through for future prompt sites (marked `# noqa: F841` with a comment explaining this is plumbing for the first future prompt)
- [x] Add a module-level helper (or `click.ClickException` subclass) `_require_setting(name: str, cli_flag: str, env_var: str)` that raises with the message: `<name> is required when --no-input is active. Provide via --<cli_flag> or <env_var>.` and causes exit code 1. This is the landing spot for future prompt call sites.
- [x] Create `tests/test_runtime.py` (31 tests total):
  - [x] `should_skip_input(True)` returns `True` regardless of env/TTY
  - [x] `PROJECT_GUIDE_NO_INPUT=1` (and `true`, `YES`, `on`, etc.) returns `True`; empty/falsy/unset falls through (parametrized 8+6+1 cases)
  - [x] `CI=1` returns `True` when flag and `PROJECT_GUIDE_NO_INPUT` are not set (+ case-insensitive parametrized cases + falsy fall-through)
  - [x] Non-TTY stdin returns `True` when nothing else is set (monkeypatched `sys.stdin`)
  - [x] Priority order: flag beats env, env beats CI, CI beats TTY (3 dedicated priority tests)
  - [x] Safety: stdin `None` or closed returns `True` (non-TTY fallback) — both branches covered
  - [x] `_require_setting` contract tests (2 tests: exit code + exact message format)
- [x] Add to `tests/test_cli.py` (5 new tests):
  - [x] `init --no-input` on a fresh project → normal install, exit 0
  - [x] `init --no-input --force` on an initialized project → overwrite, exit 0
  - [x] `init` with `CI=1` env var (via `monkeypatch.setenv`) behaves the same as `--no-input` — specifically, it still exits 0 on re-run per L.a (idempotency + auto-detection compose cleanly)
  - [x] `init` with non-TTY stdin (via `runner.invoke(main, ['init'], input="")`) behaves the same as `--no-input`
  - [x] Regression guard for the FR-L4 contract: `test_require_setting_contract_exit_code_and_message` registers a throwaway `@click.command` that calls `_require_setting` and asserts exit 1 + exact message format. This is the guard that protects the contract the day someone adds a real prompt to `init`.
- [x] Verify: `CI=1 project-guide init` and `project-guide init --no-input` both work end-to-end on a fresh fixture project (covered by `test_init_with_ci_env_var_is_idempotent_on_rerun` and `test_init_with_no_input_flag_on_fresh_project`)

### Story L.c: v2.2.2 Phase L Documentation and CHANGELOG [Done]

- [x] Update `README.md` with a short "Unattended / CI use" subsection (nested under `### init`)
  - [x] Show all four trigger mechanisms with one example each: `--no-input`, `PROJECT_GUIDE_NO_INPUT=1`, `CI=1`, non-TTY (piped stdin)
  - [x] Note idempotent re-run: `project-guide init` on an initialized project is a no-op (dedicated "Idempotent re-run" paragraph)
  - [x] `--no-input` added to the `### init` options list
- [x] Update MkDocs command reference for `init` to document `--no-input` and the auto-detection behavior (`docs/site/user-guide/commands.md` — new "Idempotent Re-run" section + full "Unattended / CI Use" section with priority-order trigger table; `--no-input` added to options list and Examples block; cites `runtime.py` helpers for anyone adding a future prompt)
- [x] Update `docs/specs/project-guide-no-input-spec.md` status line from `Proposed (2026-04-10)` to `Implemented in v2.2.0–v2.2.1 (2026-04-11)` with one-sentence citations of Story L.a and Story L.b
- [x] Update `CHANGELOG.md` with Phase L entries (v2.2.0 and v2.2.1 already landed in prior stories; v2.2.2 doc-pass entry added here). The L.a and L.b CHANGELOG entries are already separated so pyve can cite the exact semantics it depends on.
- [x] Verify: `project-guide init --help` shows the new `--no-input` flag and correct help text (help text matches FR-L1/FR-L2 exactly — verified via the test_cli.py L.b test suite)
- [x] Verify: the rendered `default` mode (and any planning mode) is unchanged by this phase — Phase L touches only `cli.py`, `runtime.py`, and docs (230 tests pass unchanged; no template edits in this phase)

### Story L.d: v2.2.3 MkDocs commands.md Catch-up for archive-stories [Done]

Close a K.g carryover gap discovered during the L.c documentation pass: the MkDocs command reference at `docs/site/user-guide/commands.md` was not updated when the `archive-stories` CLI command shipped in v2.1.3 (Story K.d). The K.g docs pass updated the README's Command Reference, `modes.md`, `workflow.md`, and `default-mode.md`, but `commands.md` was not on that checklist and so still reflects the pre-v2.1.3 command surface. This story is a small, focused catch-up — scoped narrowly to the missing `archive-stories` content plus the stale count on the first line. It is deliberately *not* a general `commands.md` audit; any other drift in that file is out of scope and should be addressed in its own follow-up.

**Why in Phase L and not a Phase K hotfix:** roll forward, not backward. The K.g commit (`0766528 v2.1.6 Phase K Documentation and CHANGELOG`) has shipped and Phase K is closed; adding retroactive tasks to a done phase would muddy the lifecycle boundary that Phase K's `archive_stories` mode was built to protect. Threading this through Phase L as L.d keeps the commit history monotonic and gives pyve a clean upstream version to cite (v2.2.3) if it ever needs to.

- [x] Update `docs/site/user-guide/commands.md` line 3: "eight commands" → "nine commands" (reflects the `archive-stories` command added in v2.1.3)
- [x] Update the "Command Overview" table in `docs/site/user-guide/commands.md` to add an `archive-stories` row. Inserted between `mode` and `status` to match the README's Command Reference ordering, since `archive-stories` is a post-release/lifecycle command that sits closer to `mode` than to the file-sync commands.
- [x] Add a new `## archive-stories` section to `docs/site/user-guide/commands.md`, placed after `## mode` and before `## status` to match the overview table ordering. Content adapted from the canonical README section at `README.md` `### archive-stories` — the README has the authoritative prose describing the 5-step archive pipeline, pre-check failure behavior, rollback-on-failure semantics, and the LLM-runs-after-developer-approval usage pattern. Wording preserved; lightly adapted for MkDocs heading structure (`### What It Does`, `### Failure Modes`, `### Usage` subsections).
- [x] The new section covers: command synopsis (`project-guide archive-stories`), what it does (the 5-step list), failure modes (pre-check failure leaves workspace untouched; rollback on re-render failure), and the "run by the LLM after the developer has approved the archive in `project-guide mode archive_stories`" usage note. Also calls out the conversational-vs-deterministic split between the mode template and the CLI command.
- [x] Verify: MkDocs renders `commands.md` without broken links or heading-level issues. Visual inspection confirms the new `##` section fits the existing heading hierarchy (consistent with the `## init`, `## mode`, `## status`, etc. pattern). No MkDocs build step was run — visual inspection sufficient per the story's fallback clause.
- [x] Verify: every command that `project-guide --help` lists is present in both the `commands.md` overview table and has its own `##` section. Enumerated against `pyve run python -m project_guide --help`: 9 commands (`archive-stories`, `init`, `mode`, `override`, `overrides`, `purge`, `status`, `unoverride`, `update`) — all 9 have both an overview table row and a dedicated `##` section after this story. No *other* commands drift was discovered.
- [x] Update `CHANGELOG.md` with a v2.2.3 entry under `### Fixed`. Entry explicitly cites K.g as the origin of the gap and L.c as the discovery point for provenance.
- [x] Update `docs/specs/stories.md`: mark L.d `[Done]` on completion

**Out of scope** (do not expand this story):
- Any other stale content in `commands.md` beyond the `archive-stories` gap (e.g., test-count drift, feature-count drift, outdated screenshots). Those are separate gaps and should be tracked separately if found.
- A general MkDocs-vs-README consistency audit across the rest of the `docs/site/user-guide/` tree. Legitimate future work, but not here.
- Changes to the `archive-stories` CLI command itself or the `archive_stories` mode — this story is documentation-only.
- Updates to `project_guide/templates/project-guide/templates/modes/default-mode.md` or any other template — this story does not touch rendered-output sources.

---

## Phase M: Project Essentials Integration (v2.3.0)

Establish `docs/specs/project-essentials.md` as a per-project artifact that captures must-know facts future LLMs need to avoid blunders (workflow rules, architecture quirks, hidden coupling, dogfooding/meta notes), then wire the three planning modes (`plan_tech_spec`, `refactor_plan`, `plan_phase`) to populate and maintain it over the project lifecycle. M.a ships the placeholder + render hook + dogfoods the artifact for this project; M.b generalizes M.a's regression guard into a project-wide post-render placeholder validator; M.c–M.e wire the planning modes; M.f is the documentation pass. See `phase-m-project-essentials-plan.md` for full details.

> **Renumbering note:** This phase was originally drafted as Phase L on 2026-04-10. It was renumbered to Phase M on 2026-04-11 when a new Phase L (`project-guide init --no-input` mode) was inserted ahead of it. At the same time, stories M.a and M.b were moved out of Phase K (where they had been planned as K.h and K.i) and absorbed into this phase, because they are thematically part of the project-essentials integration rather than the K release-lifecycle work.

**Implementation strategy:** No spike — the integration boundary (the `project_essentials` render context variable) is validated by M.a's own tests. Ordering is load-bearing only within two pairs: M.a must ship before M.b (the validator generalizes M.a's regression guard), and M.a must ship before M.c/M.d/M.e (nothing to populate otherwise). M.c/M.d/M.e are mutually independent and can ship in any order; the listed order matches the project lifecycle (initial → refactor → per-phase).

Out of scope (deferred or already covered): a dedicated `refactor_essentials` mode (not needed; the three planning modes cover the lifecycle), a `create_or_modify` action type (mode templates handle existence-checking conversationally), validation/linting of `project-essentials.md` content (the artifact is freeform by design), support for literal `{{ var }}` strings as rendered output (documented as a known M.b limitation).

### Story M.a: v2.3.0 project-essentials.md Placeholder and Render Hook [Done]

Establish a per-project `project-essentials.md` artifact that gets injected into every rendered mode via `_header-common.md`. Empty/missing renders cleanly, content (when present) appears as a `## Project Essentials` section in every mode. This story lays the rails and dogfoods it for this project; M.c–M.e wire the planning modes to populate it. *(Originally planned as Phase K story K.h.)*

- [x] Create `project_guide/templates/project-guide/templates/artifacts/project-essentials.md`
  - [x] Empty body with a brief comment block describing what belongs there: workflow rules, architecture quirks, domain conventions, hidden coupling, dogfooding/meta notes
  - [x] Note that an empty file is acceptable
  - [x] **Additional scope**: template explicitly documents the no-top-level-heading convention — the wrapper in `_header-common.md` provides `## Project Essentials`, so file content should use `###` for subsections to avoid heading-level collision in rendered `go.md`
- [x] Update `project_guide/render.py` to read `<spec_artifacts_path>/project-essentials.md` if present (new `_read_project_essentials()` helper)
  - [x] Pass content as the `project_essentials` Jinja2 context variable
  - [x] Default to empty string when the file is missing or empty (no error) — also treats whitespace-only files as empty, and handles the unit-test case where `spec_artifacts_path` is absent from metadata.common
- [x] Update `project_guide/templates/project-guide/templates/modes/_header-common.md`
  - [x] After the **Rules** section and before the `# {{ mode_name }} mode` heading, render `{% if project_essentials %}## Project Essentials\n\n{{ project_essentials }}\n\n---\n{% endif %}` (section omitted entirely when empty)
- [x] Tests in `tests/test_render.py` (6 new tests under a Story M.a heading, with new `essentials_template_dir` and `essentials_metadata` fixtures):
  - [x] Rendered output contains `## Project Essentials` when fixture file is non-empty
  - [x] Rendered output omits the section when fixture file is empty (zero-length)
  - [x] Rendered output omits the section when fixture file is whitespace-only (additional edge case)
  - [x] Rendered output omits the section when fixture file is missing (no error)
  - [x] Rendered output omits the section when `spec_artifacts_path` is absent from metadata.common (the minimal-metadata unit-test path)
  - [x] **Regression guard** (temporary — removed by M.b once the general validator is in place): rendered output never contains the literal string `{{ project_essentials }}` in any of the above cases. Exercises all four file shapes inside a single test. Catches a future template edit that removes the `{% if %}` guard, since `_LenientUndefined.__str__` would otherwise render the placeholder verbatim. See `render.py:83-99`.
- [x] Populate `docs/specs/project-essentials.md` for this project with current must-know facts:
  - [x] Dogfooding rule: edit templates under `project_guide/templates/project-guide/`, never `docs/project-guide/` (the installed copy); `docs/project-guide/go.md` is dynamically re-rendered by `mode`
  - [x] Workflow rule: pyve two-environment pattern — runtime (`pyve run python ...`), tests (`pyve test`), dev tools (`pyve testenv run ruff/mypy ...`), never `pip install -e ".[dev]"` into the main venv
  - [x] **Additional scope**: v2 mode-driven Jinja2 templating architecture note, Phase K release-lifecycle split (`archive_stories` mode vs `archive-stories` CLI), phase letter continuity across archive boundaries, Phase L `--no-input` contract (`should_skip_input()` + `_require_setting()` pinned by the contract test), and commit/version style conventions
- [x] Verify by running `project-guide mode default` (and `project-guide mode code_velocity`) and inspecting `docs/project-guide/go.md` for the rendered Project Essentials section — section appears between the `**Rules**` block and the mode heading in both modes; `###` subsection nesting renders correctly
- [x] Note: do **not** add `project-essentials.md` as a tracked artifact in any mode's `.metadata.yml` entry yet — that wiring is M.c–M.e's responsibility

### Story M.b: v2.3.1 Render Output Validation — Fail on Unrendered Placeholders [Done]

Generalize the M.a `{{ project_essentials }}` regression guard into a project-wide safeguard. After every render, scan the output for any remaining `{{ identifier }}` Jinja-style placeholders. If any are found, raise `RenderError` with the placeholder names. This catches missed intents (a context variable that should have been set), typos (`{{ project_essentialss }}`), and removed `{% if %}` guards across **all** templates, not just `_header-common.md`. The current `_LenientUndefined` class (`render.py:83-99`) outputs `{{ var_name }}` for undefined variables — this story turns that observation into a hard error gate. Lenient mode itself stays unchanged because its placeholder output is what makes the validator's job possible. *(Originally planned as Phase K story K.i.)*

- [x] Add a post-render validation function in `project_guide/render.py` (new `_validate_no_unrendered_placeholders` helper)
  - [x] Regex: `\{\{\s*([a-zA-Z_]\w*)\s*\}\}` (matches `{{var}}`, `{{ var }}`, `{{  var  }}`) — module-level `_UNRENDERED_PLACEHOLDER_RE` with an extensive docstring explaining what it deliberately does NOT match (attribute access, filters, expressions, statement blocks)
  - [x] Scan the rendered string after Jinja produces output, before writing the file
  - [x] If matches found, raise `RenderError` with the deduplicated list of placeholder names (first-occurrence order preserved) and a hint message: "Hint: check (1) render.py context variables and (2) template variable spellings."
- [x] Call the validator inside `render_go_project_guide` after `template.render(...)` but before `output_path.write_text(...)` — a failing validation leaves the filesystem untouched
- [x] Tests in `tests/test_render.py` (7 new tests under a "Story M.b" heading):
  - [x] Rendering a template with a single undefined variable raises `RenderError` citing the name
  - [x] Error message lists all distinct offenders (3 vars → 3 names in the message)
  - [x] Error message deduplicates repeated offenders (a name repeated 3× appears exactly once) and preserves first-occurrence order
  - [x] Error message contains both "render.py context variables" and "template variable spellings" fix hints
  - [x] Output file is NOT written when the validator raises (pre/post `exists()` assertions)
  - [x] Rendering with all variables defined succeeds (happy path using the standard `template_dir` fixture)
  - [x] Validator does not raise on templates with no Jinja variables at all (empty-match edge case)
  - [x] **Also updated**: the existing `test_render_undefined_vars_are_preserved` test was renamed to `test_render_undefined_vars_raise_render_error` and its assertions inverted — the v2.3.1 contract is that undefined variables RAISE (the validator catches them) rather than PASS THROUGH (the old M.a lenient-undefined contract)
- [x] Remove the now-redundant `{{ project_essentials }}` regression-guard assertion added in M.a (the generalized validator subsumes it). Left a brief comment in the test file at the former location explaining that the M.b validator covers this case and would raise far more loudly than a single dedicated test.
- [x] Audit existing mode templates and `_header-common.md` to confirm none rely on undefined variables silently passing through. **No fixes needed** — manual grep enumerated 10 mode templates using bare `{{ var }}` placeholders, and every one is backed by either a `render.py` context variable (`mode_name`, `mode_info`, `mode_description`, `sequence_or_cycle`, `next_mode`, `target_dir`, `project_essentials`) or a `metadata.common` entry (`test_invocation`, `spec_artifacts_path`, `web_root`). No mode template `{% include %}`s an artifact template, so artifact placeholders never enter the mode render path. The empirical proof is the `test_every_mode_renders_successfully` parametrized test — all 14 modes continue to pass unchanged after the validator ships.
- [x] Verify: running `project-guide mode default` and `project-guide mode plan_concept` still produces valid `go.md` output with no errors (both ran successfully; `go.md` was grepped for unrendered placeholders → zero matches)
- [x] Document the limitation in a code comment: templates that legitimately want to emit literal `{{ var }}` strings (e.g., documentation of Jinja syntax) will trigger false positives. Not currently a problem; bridge if/when needed (likely via `{% raw %}`). Documented inline in the `_UNRENDERED_PLACEHOLDER_RE` docstring.

### Story M.c: v2.3.2 plan_tech_spec Populates project-essentials.md [Done]

After the tech-spec is approved, prompt the developer to capture any project-specific must-know facts and write them to `docs/specs/project-essentials.md`.

- [x] Update `project_guide/templates/project-guide/templates/modes/plan-tech-spec-mode.md` to add a final step after tech-spec approval (new steps 5, 6, 7 inserted after the previous step 4 "approve" gate)
- [x] Step asks the developer for project-essentials content with **concrete worked examples** in the prompt (not just abstract categories — the LLM should put these specific scenarios in front of the developer to jog their memory):
  - [x] **Workflow rules — tool wrappers and environment conventions.** All four worked examples present (Python invocation, dev tool installation, test invocation, "legitimate alternatives should be intentional choices" principle).
  - [x] **Architecture quirks** — present as a top-level category with the source-of-truth vs installed-copy example.
  - [x] **Domain conventions** — present with money-in-cents / UTC timestamps / string-IDs examples.
  - [x] **Hidden coupling** — present with mirror-file / auto-generated code / regenerated-looks-hand-edited examples.
  - [x] **Dogfooding / meta notes** — present as an additional fifth category (not in the story's original list, but the M.a dogfooding work made it obvious this belongs here).
  - [x] **Skip if there are none — empty is fine** — implemented as an explicit "skip to step 7" escape hatch in the template, with the note that empty files are acceptable when maintaining an existing one but should NOT be created on fresh projects.
- [x] Generate `docs/specs/project-essentials.md` from the artifact template only if the developer provides facts (step 6); otherwise skip entirely (step 5's escape hatch). **Design refinement from the story text**: the story said "leave the file empty (or skip creation entirely)" — we chose skip-creation, not empty file, because the latter would leave a dormant file in `docs/specs/` that looks like an oversight. The M.a render hook's "whitespace-only = omit section" branch handles maintenance of an existing empty file, but initial creation of an empty file is intentionally avoided.
- [x] Step 6 also reminds the LLM to follow the heading convention (no top-level `#`; `###` for subsections) to prevent heading-level collision with the wrapper injected by `_header-common.md`.
- [x] Add `project-essentials.md` to `plan_tech_spec`'s `artifacts` list in `project_guide/templates/project-guide/.metadata.yml` with `action: create`
- [x] Tests for the rendered mode template containing the new prompt (2 new tests under a "Story M.c" heading in `tests/test_render.py`):
  - [x] `test_plan_tech_spec_mode_prompts_for_project_essentials` — end-to-end render via `CliRunner.isolated_filesystem() + init + mode plan_tech_spec`. Asserts: capture step present and post-approval; at least one concrete worked example visible (`pyve run python` or `poetry run python`); two category names (`Workflow rules`, `Architecture quirks`); the "skip if none" escape hatch; the artifact template path reference; and the heading convention reminder.
  - [x] `test_plan_tech_spec_metadata_declares_project_essentials_artifact` — loads bundled metadata, gets the `plan_tech_spec` mode, asserts both artifacts are declared and the `project-essentials.md` artifact uses `ActionType.CREATE`. This is the wiring checkpoint that M.d/M.e will deliberately diverge from (they use `modify`).
- [x] Verify: running `project-guide mode plan_tech_spec` end-to-end on a fixture project includes the essentials prompt — confirmed via the end-to-end test above and by running `pyve run project-guide update && pyve run project-guide mode plan_tech_spec` in this repo. The rendered `go.md` contains the capture step at its expected position (step 5) AND the M.a-injected `## Project Essentials` section at the top, proving the two layers compose correctly.

### Story M.d: v2.3.3 refactor_plan Refreshes project-essentials.md [Done]

When `refactor_plan` updates the concept/features/tech-spec, give the developer a chance to refresh `project-essentials.md` for any architecture or workflow changes that affect must-know facts.

- [x] Update `project_guide/templates/project-guide/templates/modes/refactor-plan-mode.md` to add a cycle step (or extend Step 1) for revisiting project-essentials — **design choice: terminal step, not cycle step**. New "Final Step: Revisit Project Essentials" section appended after Step 8, runs **once** per refactor session (not per-document). Rationale: the main cycle processes three documents one at a time, but most facts a refactor introduces are cross-document (new tool wrapper, new dev-tool isolation, etc.) — asking once at the end gives the developer the full refactor context. Documented in the CHANGELOG's "Design choice" note.
- [x] Prompt should ask whether the refactor changed any facts the LLM must know, with **concrete worked examples** (not just "tool wrapper, renamed module, changed conventions"):
  - [x] *Switched or added an environment manager* — present with a fully-rendered "*Example:*" sentence ("We switched from `poetry` to `pyve`...") so the LLM can put concrete language in front of the developer.
  - [x] *Split runtime from dev environment* — present with the `pip install -e '.[dev]'` anti-pattern explicitly called out.
  - [x] *Renamed module or moved source-of-truth* — present with the template-source-move example from this project's own history.
  - [x] *Changed domain conventions* — present with the float → cents example.
  - [x] *New auto-generated or hidden-coupling files* — present with the `go.md` re-render example.
  - [x] **Principle**: "if the refactor introduced a fork-in-the-road where the wrong choice still 'works,' that's a project-essential" — rendered verbatim as the closing principle of Step F.2.
- [x] Mode template handles the case where `project-essentials.md` does not yet exist (legacy project): Step F.1 branches to the "create path"; Step F.3 generates a new file from the artifact template. Legacy projects are explicitly flagged as the highest-value case ("they are the highest-value case for project-essentials capture, because none of their conventions have been written down").
- [x] Mode template handles the case where it exists: Step F.1 branches to the "modify path"; Step F.3 reads → integrates → writes with explicit preserve/update/add semantics.
- [x] Add `project-essentials.md` to `refactor_plan`'s `artifacts` list in `.metadata.yml` with `action: modify` (previously this mode had no artifacts list at all — a new list was added with just this one entry).
- [x] Tests for the rendered mode template (2 new tests under a "Story M.d" heading in `tests/test_render.py`):
  - [x] `test_refactor_plan_mode_prompts_for_project_essentials_revisit` — end-to-end render. Asserts: terminal section present; runs once (not per-document); create and modify branches both visible; legacy-project framing explicit; at least one concrete worked example with environment-manager naming; artifact template path referenced; heading convention reminder; "skip if none" escape hatch; fork-in-the-road principle visible.
  - [x] `test_refactor_plan_metadata_declares_project_essentials_modify_artifact` — loads bundled metadata, asserts exactly one `project-essentials.md` artifact with `ActionType.MODIFY`. The "exactly one" check guards against copy-paste duplicates.
- [x] Verify: rendered `refactor_plan` mode includes the revisit step — confirmed via the end-to-end test above and by running `pyve run project-guide update && pyve run project-guide mode refactor_plan` in this repo. All four sub-steps (F.1 through F.4) render at the expected terminal position; the M.a-injected `## Project Essentials` section also appears at the top, proving composition works for cycle-type modes as well.

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

