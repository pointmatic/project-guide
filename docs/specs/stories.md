# stories.md -- project-guide (python)

This document breaks the `project-guide` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Stories with code changes include a version number (e.g., v0.1.0). Stories with only documentation or polish changes omit the version number. The version follows semantic versioning and is bumped per story. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

For a high-level concept (why), see `concept.md`. For requirements and behavior (what), see `features.md`. For implementation details (how), see `tech-spec.md`. For project-specific must-know facts, see `project-essentials.md` (`plan_phase` appends new facts per phase).

---

## Phase N: Mode Naming, CLI Polish & Memory Integration (v2.4.0)

Clear the accumulated deferred backlog from Phases J–M in four clusters: (1) mode naming coherence — rename `code_velocity` → `code_direct` and `project_scaffold` → `scaffold_project`; (2) CLI polish — `_resolve_setting` helper, `--test-first` flag, `--no-input` for purge/update, `--quiet`, story detection in `status`; (3) advanced mode system — auto-detection from `files_exist`, interactive menu, per-project metadata overrides; (4) memory & knowledge — Pyve detection + bundled `project-essentials-pyve.md`, memory review in `scaffold_project`, memory reflection rule in `_header-common.md`. See `phase-n-mode-naming-cli-memory-plan.md` for full details.

**Implementation strategy:** Renames first (N.a–N.b, widespread cross-references), then CLI building blocks in dependency order (N.c `_resolve_setting` before N.d `--test-first`), then remaining CLI improvements (N.e–N.g, mutually independent), then advanced mode system (N.h–N.i), then memory & knowledge (N.j–N.l). Documentation pass last (N.m).

### Story N.a: v2.4.0 Rename code_velocity → code_direct [Done]

`code_velocity` does not pair naturally with `code_test_first`. `code_direct` more clearly describes the mode (direct coding, no mandatory TDD) and follows the same `code_<style>` naming convention.

- [x] Rename `project_guide/templates/project-guide/templates/modes/code-velocity-mode.md` → `code-direct-mode.md`
- [x] Update `project_guide/templates/project-guide/.metadata.yml`: mode key `code_velocity` → `code_direct`; `mode_template` path updated to `templates/modes/code-direct-mode.md`
- [x] Update all cross-references in mode templates: `default-mode.md`, `plan-stories-mode.md`, `plan-phase-mode.md`, `archive-stories-mode.md`, `_header-sequence.md` — any `code_velocity` occurrences
- [x] Update `docs/specs/project-essentials.md` line referencing "`code_velocity` mode" → `code_direct`
- [x] Update `README.md` mode table and any other `code_velocity` references
- [x] Update `docs/site/user-guide/modes.md` entry
- [x] Update `docs/specs/features.md` FR-1 modes table
- [x] Update any hardcoded `code_velocity` strings in test files
- [x] Run `pyve run project-guide update && pyve run project-guide mode code_direct` — verify `go.md` renders correctly
- [x] Verify: `test_every_mode_renders_successfully` passes with the renamed mode; `test_header_common_approval_gate_rule_renders_in_every_mode` still passes
- [x] Bump version to v2.4.0
- [x] Update CHANGELOG.md

### Story N.b: v2.4.1 Rename project_scaffold → scaffold_project [Done]

`project_scaffold` is the only mode that does not start with a verb. `scaffold_project` follows the `<verb>_<noun>` convention established by every other mode.

- [x] Rename `project_guide/templates/project-guide/templates/modes/project-scaffold-mode.md` → `scaffold-project-mode.md`
- [x] Update `.metadata.yml`: mode key `project_scaffold` → `scaffold_project`; `mode_template` path updated
- [x] Update all cross-references in mode templates: `default-mode.md`, `plan-stories-mode.md` (Story A.a scaffolding rule added in M.j references `project_scaffold` mode — update to `scaffold_project`)
- [x] Update `README.md`, `docs/site/user-guide/modes.md`, `docs/specs/features.md` (non-goals section and FR-1 modes table)
- [x] Update any hardcoded `project_scaffold` strings in test files
- [x] Run `pyve run project-guide update && pyve run project-guide mode scaffold_project` — verify renders correctly
- [x] Verify: `test_every_mode_renders_successfully` passes; parametrized approval-gate test passes
- [x] Bump version to v2.4.1
- [x] Update CHANGELOG.md

### Story N.c: v2.4.2 Config-File Fallback — _resolve_setting Helper [Done]

Implement the documented resolution chain (CLI flag → env var → `.project-guide.yml` key → default) as a reusable helper in `runtime.py`. Required before N.d (`--test-first`) and any future prompt that has a settable default.

- [x] Add `_resolve_setting(name, cli_value, env_var, config_key, config, default)` to `project_guide/runtime.py`
  - [x] Resolution chain (first match wins): CLI value (if not `None`) → env var (truthy string via `_TRUTHY_ENV_VALUES` for bools; raw string for str settings) → config key (from loaded `Config` dict) → default
  - [x] Handles both `bool` and `str` return types; type is inferred from `default`
- [x] Tests in `tests/test_runtime.py` (new "Story N.c" section):
  - [x] CLI value wins over env, env wins over config, config wins over default (priority-order parametrized test)
  - [x] Full fallback chain: CLI=None, env unset, config key absent → default returned
  - [x] Bool resolution: truthy env values (`"1"`, `"true"`, `"yes"`, `"on"`) → `True`; falsy → `False`
  - [x] String resolution: env var returned as-is; config key returned as-is
  - [x] Contract test: function signature and return type are stable (guards against future signature drift)
- [x] Bump version to v2.4.2
- [x] Update CHANGELOG.md

### Story N.d: v2.4.3 --test-first Flag on init, minor concept template bugfix [Done]

Persist a project-level preference for test-driven coding so planning modes automatically suggest `code_test_first` instead of `code_direct`.

- [x] Add `test_first: bool = False` field to `Config` dataclass in `project_guide/config.py`
- [x] Update `Config.load()` / `Config.save()` for round-trip; add `test_config_test_first_round_trip` to `tests/test_config.py`
- [x] Add `--test-first` boolean flag to `init` in `cli.py`; resolve via `_resolve_setting` with env var `PROJECT_GUIDE_TEST_FIRST`; persist resolved value to config
- [x] Update `render.py` to pass `test_first: bool` as a Jinja2 context variable
- [x] Update `project_guide/templates/project-guide/.metadata.yml` `common` block: add `test_first: false` as a documented variable
- [x] Update mode templates that suggest a next coding step — use `{% if test_first %}code_test_first{% else %}code_direct{% endif %}`: `default-mode.md`, `plan-stories-mode.md`, `plan-phase-mode.md`
- [x] Tests in `tests/test_cli.py`:
  - [x] `init --test-first` → config `test_first: true`
  - [x] `init` without flag → config `test_first: false`
  - [x] `PROJECT_GUIDE_TEST_FIRST=1 init` → config `test_first: true`
- [x] Tests in `tests/test_render.py`:
  - [x] Rendered `default` mode with `test_first=True` contains `code_test_first` as next-mode suggestion
  - [x] Rendered `default` mode with `test_first=False` contains `code_direct`
- [x] Bug fix: add step 4 to `plan-concept-mode.md` — "Write the completed document to `docs/specs/concept.md`." (LLM was asking where to write the output because no step named the destination file)
- [x] Bump version to v2.4.3
- [x] Update CHANGELOG.md

### Story N.e: v2.4.4 --no-input for purge and update [Done]

Extend the Phase L `--no-input` contract to `purge` and `update`, completing the unattended-operation story across all commands that block on stdin.

- [x] Add `--no-input` flag to `purge`; wire to `should_skip_input()`; when active, skip `click.confirm()` and proceed
- [x] Add `--no-input` flag to `update`; wire to `should_skip_input()`; when active, skip modified-file prompts and apply safe default (skip modified files, no force-overwrite)
- [x] Auto-detect `CI=1`, `PROJECT_GUIDE_NO_INPUT=1`, non-TTY for both commands (consistent with Phase L contract)
- [x] Tests in `tests/test_cli.py`:
  - [x] `purge --no-input` skips confirmation, exits 0
  - [x] `purge` with `CI=1` also skips confirmation
  - [x] `update --no-input` skips modified-file prompts, applies safe defaults
  - [x] `update` with `PROJECT_GUIDE_NO_INPUT=1` also skips prompts
  - [x] Regression guard: `purge` without `--no-input` on TTY still prompts (existing behavior unchanged)
- [x] Bump version to v2.4.4
- [x] Update CHANGELOG.md

### Story N.f: v2.4.5 --quiet / Output Suppression [Done]

Add a `--quiet` / `-q` flag to suppress per-file progress chatter from `init`, `update`, and `purge`. Composes with `--no-input` for fully silent unattended runs.

- [x] Add `--quiet` / `-q` boolean flag to `init`, `update`, and `purge` commands in `cli.py`
- [x] Update `_copy_template_tree` to accept a `quiet: bool` parameter; suppress per-file progress lines when `True`
- [x] Update `sync_files` callers in `cli.py` to pass `quiet` through to file-by-file output
- [x] Errors, summaries (final counts), and explicit warnings are never suppressed regardless of `--quiet`
- [x] `--quiet` and `--no-input` compose cleanly: `init --no-input --quiet` produces no stdout on success
- [x] Tests in `tests/test_cli.py`:
  - [x] `init --quiet` produces no per-file lines; summary count line still present
  - [x] `update --quiet` suppresses per-file sync output
  - [x] `purge --quiet --force` produces no prompts or progress lines
  - [x] Error output is still emitted when `--quiet` is set (regression guard)
- [x] Bump version to v2.4.5
- [x] Update CHANGELOG.md

### Story N.g: v2.4.6 Story Detection in status [Done]

`project-guide status` gains a **Stories** section showing backlog counts and the next unstarted story — giving the developer an at-a-glance view of progress without opening `stories.md`.

- [x] Add `_read_stories_summary(spec_artifacts_path: str) -> StoriesSummary | None` helper (new `project_guide/stories.py` or inline in `cli.py`)
  - [x] Reads `<spec_artifacts_path>/stories.md` via regex; returns `None` if absent or has no story headings
  - [x] Counts: total stories, `[Done]`, `[In Progress]`, `[Planned]`
  - [x] Identifies the first non-Done story for the "Next:" line
- [x] Update `status` output to include a **Stories** section when data is available:
  ```
  Stories: 13 total — 0 done, 0 in progress, 13 planned
    Next: Story N.a: v2.4.0 Rename code_velocity → code_direct
  ```
- [x] `--verbose` shows per-phase breakdown (phase letter, phase name, done/total count per phase)
- [x] Section omitted entirely when `stories.md` is absent, empty, or post-archive (no story headings)
- [x] Tests in `tests/test_cli.py`:
  - [x] Status with populated stories.md shows correct counts
  - [x] Status with all-Done stories shows `0 planned, 0 in progress`
  - [x] Status with no stories.md omits the section
  - [x] Status with empty post-archive stories.md omits the section
  - [x] `--verbose` shows per-phase line
- [x] Bump version to v2.4.6
- [x] Update CHANGELOG.md

### Story N.h: v2.4.7 Mode Auto-Detection and Interactive Menu [Done]

`project-guide mode` (no argument) becomes useful: it checks prerequisites and — on a TTY — offers a numbered selection menu instead of a plain list.

- [x] Update the no-argument path of `mode` command to check each mode's `files_exist` list against the current working directory
  - [x] Modes with all prerequisites met: marked `✓` (green)
  - [x] Modes with unmet prerequisites: listed but dimmed; unmet files noted on `--verbose`
- [x] Add interactive menu (TTY only, i.e. `not should_skip_input()`):
  - [x] Modes grouped by category: Planning, Coding, Post-Release, Debugging, Documentation, Refactoring
  - [x] Numbered selection prompt; on valid selection switch mode + re-render `go.md`
  - [x] Invalid input → re-prompt (max 3 attempts then exit 1 with helpful message)
  - [x] Under `--no-input` / non-TTY: skip menu, print the `✓`-annotated listing and exit 0
- [x] Tests in `tests/test_cli.py`:
  - [x] Mode with all `files_exist` files present → marked available in output
  - [x] Mode with missing prerequisite → marked unavailable
  - [x] Non-TTY `CliRunner` invocation → plain listing rendered, no interactive prompt
  - [x] Selecting a valid number switches mode (integration test via `isolated_filesystem`)
- [x] Bump version to v2.4.7
- [x] Update CHANGELOG.md

### Story N.i: v2.4.8 Per-Project Metadata Overrides [Done]

Allow projects to patch specific mode fields in `.project-guide.yml` — e.g. change `next_mode`, override `files_exist` prerequisites — without editing the bundled `.metadata.yml`.

- [x] Add `metadata_overrides: dict[str, dict] = field(default_factory=dict)` to `Config` dataclass
- [x] Update `Config.load()` / `Config.save()` for round-trip; add round-trip test to `tests/test_config.py`
- [x] Add `_apply_metadata_overrides(metadata: Metadata, overrides: dict) -> None` in `project_guide/metadata.py`
  - [x] Supported fields: `next_mode`, `files_exist`, `info`, `description`
  - [x] Unknown mode name in overrides → `MetadataError`
  - [x] Unknown field in overrides → `MetadataError`
  - [x] Unmentioned fields on a mode are unchanged (partial patch semantics)
- [x] Call `_apply_metadata_overrides` after `load_metadata()` in all paths that load metadata (render, mode-switch, status)
- [x] Tests in `tests/test_metadata.py`:
  - [x] Override `next_mode` → reflected in `ModeDefinition`
  - [x] Override `files_exist` → reflected in prerequisite check
  - [x] Unknown mode name → `MetadataError`
  - [x] Unknown field → `MetadataError`
  - [x] Empty overrides dict → no change (regression guard)
- [x] Bump version to v2.4.8
- [x] Update CHANGELOG.md

### Story N.j: v2.4.9 Pyve Detection and Bundled project-essentials-pyve.md [Done]

Auto-detect Pyve at `init` time and ship a bundled Pyve-focused project-essentials template so every Pyve project gets correct dev-environment rules without writing them from scratch.

- [x] Add `pyve_version: str | None = None` to `Config` dataclass; update load/save round-trip
- [x] In `init`, run `subprocess.run(['pyve', '--version'], capture_output=True, text=True, timeout=5)`
  - [x] On success (exit 0): extract version string from stdout; store in config as `pyve_version`
  - [x] On failure (`FileNotFoundError`, non-zero exit, or timeout): store `None`; detection failure is non-fatal
- [x] Update `render.py` to pass `pyve_installed: bool` and `pyve_version: str | None` as Jinja2 context variables
- [x] Create `project_guide/templates/project-guide/templates/artifacts/project-essentials-pyve.md`:
  - [x] Section: two-environment pattern (runtime `.venv/` vs dev testenv `.pyve/testenv/venv/`; canonical invocation forms `pyve run python`, `pyve test`, `pyve testenv run ruff/mypy`; "pytest not found → use `pyve test`" signal; "do not `pip install -e '.[dev]'` into the main venv" anti-pattern)
  - [x] Section: Python invocation rule — always use `python`, never `python3`; `python3` bypasses `asdf` version shims and may resolve to the wrong interpreter
  - [x] Section: `requirements-dev.txt` story-writing rule — any story introducing dev tooling (ruff, mypy, pytest, types-* stubs) must include a task to create/update `requirements-dev.txt` so `pyve testenv --install -r requirements-dev.txt` reproduces the dev env in one step
  - [x] No top-level `#` heading; `###` subsections (consistent with project-essentials convention)
- [x] Update `scaffold-project-mode.md` and `plan-tech-spec-mode.md` with a `{% if pyve_installed %}` branch: instruct LLM to read `project-essentials-pyve.md` and copy/merge its content into `docs/specs/project-essentials.md`
- [x] Tests:
  - [x] `init` with mocked `pyve --version` success → `pyve_version` set in config
  - [x] `init` with mocked `FileNotFoundError` → `pyve_version: null`, init exits 0
  - [x] Rendered `scaffold_project` with `pyve_installed=True` contains the pyve merge instruction
  - [x] Rendered `scaffold_project` with `pyve_installed=False` omits it
  - [x] `project-essentials-pyve.md` renders without unrendered placeholders (parametrized by `test_every_mode_renders_successfully` or a dedicated artifact-render test)
- [x] Bump version to v2.4.9
- [x] Update CHANGELOG.md

### Story N.k: v2.4.10 Memory Review in scaffold_project Mode [Done]

`scaffold_project` runs once per project setup — the natural moment to reconcile prior-session LLM memories with the project's permanent knowledge base in `project-essentials.md`.

- [x] Add a **Memory Review** step to `scaffold-project-mode.md` (penultimate step, before "Present for Approval"):
  - [x] Instruct LLM to read recorded memories from the project memory store (e.g., `.claude/projects/` files for Claude Code users)
  - [x] For each memory: evaluate whether it is project-specific and should live in `project-essentials.md` rather than (or in addition to) memory
  - [x] Present candidates to the developer: "I found N memories. These may belong in `project-essentials.md`: …"
  - [x] Await developer confirmation of which (if any) to copy/migrate
  - [x] Append confirmed items to `project-essentials.md` following the heading convention (`###` subsections, no top-level `#`)
  - [x] Escape hatch: if the memory store is empty or inaccessible, note this briefly and continue
- [x] Tests in `tests/test_render.py` (new "Story N.k" section):
  - [x] Rendered `scaffold_project` contains the Memory Review step
  - [x] Memory Review step appears before "Present for Approval"
  - [x] Escape hatch language ("empty or inaccessible") present
- [x] Bump version to v2.4.10
- [x] Update CHANGELOG.md

### Story N.l: v2.4.11 Memory Reflection Instruction in _header-common.md [Done]

Teach every mode to pause before recording a new memory and ask: does this belong in `project-essentials.md` instead?

- [x] Add rule #7 to the **Rules** block in `project_guide/templates/project-guide/templates/modes/_header-common.md`:
  - [x] Text (exact): "Before recording a new memory, reflect: is this fact project-specific (belongs in `docs/specs/project-essentials.md`) or cross-project (belongs in LLM memory)? Could it belong in both? If project-specific, add it to `project-essentials.md` instead of or in addition to memory."
- [x] Tests in `tests/test_render.py` (new "Story N.l" section):
  - [x] `test_header_common_memory_reflection_rule_renders_in_every_mode` — parametrized over all mode names via `_get_all_mode_names()`; asserts the pinned substring `"Before recording a new memory, reflect"` appears inside the **Rules** block (positional assertion, consistent with the M.g approval-gate test pattern)
- [x] Verify: `test_every_mode_renders_successfully` still passes (no template regressions)
- [x] Bump version to v2.4.11
- [x] Update CHANGELOG.md

### Story N.m: v2.4.12 Phase N Documentation and CHANGELOG [Done]

- [x] Update `docs/specs/features.md`:
  - [x] FR-1 modes table: added `archive_stories`; mode count correct
  - [x] New FRs for N behaviors (FR-8 through FR-13): `--no-input`, `--quiet`, story detection, mode listing, metadata overrides, pyve detection
  - [x] `.project-guide.yml` schema block: add `test_first`, `pyve_version`, `metadata_overrides`
- [x] Update `docs/specs/tech-spec.md`:
  - [x] Filename conventions table (updated mode template examples)
  - [x] `Config` dataclass fields
  - [x] `metadata.py` and `render.py` behavior sections
- [x] Update `README.md`: mode listing output; command options (new flags); config schema
- [x] Update `docs/site/user-guide/modes.md`: marker legend and interactive menu description
- [x] Update `docs/site/user-guide/commands.md`: new flags for update/purge; status Stories section; mode menu behavior
- [x] Update `CHANGELOG.md` with v2.4.12 entry for this documentation pass
- [x] Verify: all tests pass, ruff clean, `pyve run project-guide update` re-renders `go.md` cleanly
- [x] Bump version to v2.4.12

### Story N.n: v2.4.13 Copyright and SPDX License Header, improve editable install documentation [Done]

#### File Headers
- [x] Using the project-essentials.md feature, instruct the LLM to use consistent headers for generated files
  - [x] Copyright notice format
  - [x] SPDX license headers
  - [x] Descriptive comment header file (such as PEP 257 docstrings for Python files)
  - [x] Provide a header example for reference 

#### Editable Python Module and Test Environment Dependency Installation
LLMs can easily get confused about how to install editable Python modules in different environments. There only needs to be one editable install in the main environment. Pyve makes it easy to separate the test environment tools installation from the main environment. When the Pyve environment is purged and reinitialized, the test environment remains intact. 

It is possible to install an editable module in both the main and test environments in Pyve. 

Project venv (ad hoc use, REPL, scripts):
```bash
pyve run pip install -e .
```

Testenv (so pytest can import the module):
```bash
pyve testenv run pip install -e .
pyve testenv --install -r requirements-dev.txt
```

A cleaner approach is to install it in the main environment, not in the test environment, then ensure that the test environment can import it by using pytest's `pythonpath` configuration in `pyproject.toml`.

Place in pytest.ini or pyproject.toml `[tool.pytest.ini_options]`:
```
pythonpath = ["."]   # or ["src"] for src layout
```

This avoids maintaining two editable installs with potentially diverging dependency resolution. The tradeoff: pythonpath works for import discovery but not for console scripts or entry points — if your tests invoke CLI entry points, you still need the editable install in the testenv.

Rule of thumb: use pythonpath for library projects, editable install in testenv for projects with CLI entry points that tests exercise.

- [x] Given this information above, improve the LLM instructions. 
- [x] Draft a developer guide for using Pyve with editable installs `/project_guide/templates/project-guide/developer/python-editable-install.md`. 
- [x] Update `CHANGELOG.md` with v2.4.13 entry for this documentation pass
- [x] Verify: all tests pass, ruff clean, `pyve run project-guide update` re-renders `go.md` cleanly
- [x] Bump version to v2.4.13

### Story N.o: v2.4.14 Autopublish PyPI packages on tag push [Done]

- [x] Update GitHub Actions workflow to build and publish PyPI packages when a tag is pushed
- [x] Update `CHANGELOG.md` with v2.4.14 entry for this automation
- [x] Verify: workflow runs correctly, packages are published to PyPI
- [x] Bump version to v2.4.14

### Story N.p: v2.4.15 Schema Version Mismatch Protection [Done]

Add a schema-version guard to `.project-guide.yml` so breaking config changes fail loudly with a recoverable exit path. Defers a migration framework until a concrete breaking change forces the issue; `update` auto-backs up the stale config and points the developer at `init --force` for a clean refresh, with manual merge from the backup.

- [x] Add `SCHEMA_VERSION = "2.0"` module-level constant in `project_guide/config.py`
- [x] In `Config.load()`, compare `data.get('version', "2.0")` to `SCHEMA_VERSION`:
  - [x] Match → proceed as today
  - [x] Older known → raise `SchemaVersionError` with "older schema" message
  - [x] Newer unknown → raise `SchemaVersionError` with "newer schema; upgrade project-guide" message
- [x] Add `SchemaVersionError(ConfigError)` subclass in `project_guide/exceptions.py` so command handlers can distinguish schema mismatch from other config errors
- [x] In `cli.py:update`, catch `SchemaVersionError`:
  - [x] On the "older" path: copy `.project-guide.yml` → `.project-guide.yml.bak.<timestamp>` (reuse `sync.backup_file` or equivalent)
  - [x] Print: `Schema mismatch. Config backed up to <path>. Run 'project-guide init --force' to refresh, then manually merge customizations from the backup.`
  - [x] On the "newer" path: do NOT back up; print upgrade-the-package message
  - [x] Exit 1 in both cases
- [x] Other commands that call `Config.load()` (`mode`, `status`, `override`, `unoverride`, `overrides`, `purge`) let `SchemaVersionError` propagate with a short message pointing user to run `project-guide update` for auto-backup
- [x] In `cli.py:update`, broaden the re-render guard so `go.md` is re-rendered if it is missing, even when no template files changed this run (currently guarded only by `if template_files:`). Rationale: `go.md` is rendered output, not a tracked file, so deleting it leaves `update` as a silent no-op. Add regression test in `tests/test_cli.py` (new "Story N.p" section): delete `go.md`, run `update` with no template changes, assert `go.md` exists afterward
- [x] Tests in `tests/test_config.py` (new "Story N.p" section):
  - [x] Matching version loads normally
  - [x] Older schema → `SchemaVersionError` with "older" wording
  - [x] Newer schema → `SchemaVersionError` with "newer" wording
  - [x] Absent `version` field defaults to `"2.0"` and loads normally (regression guard)
- [x] Tests in `tests/test_cli.py` (new "Story N.p" section):
  - [x] `update` with older schema creates timestamped backup, exits 1, message references `init --force`
  - [x] `update` with newer schema does NOT create a backup; exits 1 with upgrade-package message
  - [x] `status` / `mode` with older schema → clean error message pointing at `update`, exits 1
- [x] Document the policy in `docs/specs/project-essentials.md` under a new `### Config schema versioning` subsection: bump `SCHEMA_VERSION` only for rename / remove / retype / semantic changes; additive-with-default does not bump. Note: "When a real breaking change arrives, revisit adding a migration registry."
- [x] Update `docs/specs/tech-spec.md` Config section: note the schema-version check and the `SchemaVersionError` class
- [x] Update `CHANGELOG.md` with v2.4.15 entry
- [x] Bump version to v2.4.15
- [x] Verify: all tests pass, ruff clean, `pyve run project-guide update` re-renders `go.md` cleanly

### Story N.q: v2.4.16 Move '.project-guide.yml' Backup to 'init --force' [Done]

Relocate the `.project-guide.yml` backup from `update`'s `SchemaVersionError("older")` handler (added in N.p) into `init --force`, where the actual destructive overwrite happens. The N.p design backed up upstream of the recovery command, which has two flaws: (1) re-running `update` against an unresolved older schema spams a new identical `.bak.<timestamp>` on every invocation, and (2) running `init --force` directly — the actual data-loss path — produces no backup at all. Putting the backup at the overwrite site makes it idempotent (one backup per destructive refresh) and covers all entry points, not just the schema-mismatch recovery flow.

- [x] In `cli.py:init`, when `config_path.exists() and force` (before constructing the new `Config`): copy `.project-guide.yml` → `.project-guide.yml.bak.<timestamp>`
  - [x] Use `shutil.copy2` (preserves mtime) and `datetime.now().strftime("%Y%m%d%H%M%S")` for the timestamp, matching the existing N.p convention
  - [x] Print the backup path at the end of init output: `Previous config backed up to <path>. Delete once you've verified the new config.`
  - [x] Gate strictly on `config_path.exists()` — `init --force` with no prior config creates no backup (nothing to lose)
- [x] In `cli.py:update`, remove the backup call from the `SchemaVersionError("older")` handler
  - [x] New message: `Schema mismatch: <err>. Run 'project-guide init --force' to refresh (your existing .project-guide.yml will be backed up).`
  - [x] Still exits 1; `"newer"` path is unchanged (already had no backup)
  - [x] Remove the now-unused `from datetime import datetime` inline import if it is not used elsewhere in the function
- [x] Update `tests/test_cli.py` "Story N.p" section — flip the existing assertions:
  - [x] `update` with older schema: no backup created; stderr references `init --force`; exit 1 (previously: backup created)
  - [x] Re-run `update` with older schema multiple times: still no backup created (regression guard for the backup-spam bug)
- [x] Tests in `tests/test_cli.py` (new "Story N.q" section):
  - [x] `init --force` on existing project: creates timestamped backup; end-of-output references the backup path; new config is written
  - [x] `init` (no `--force`) on fresh project: no backup (nothing to back up); normal init
  - [x] `init --force` on a nonexistent config: no backup; normal init (gated on `config_path.exists()`)
  - [x] End-to-end: `update` with older schema → no backup; then `init --force` → backup created; contents of backup match the pre-refresh config
- [x] Update `docs/specs/tech-spec.md` — relocate the backup-step description from the `update` flow to the `init --force` flow
- [x] Update `docs/specs/project-essentials.md` `### Config schema versioning` subsection — update the description of the recovery flow to match the new location of the backup
- [x] Update `CHANGELOG.md` with v2.4.16 entry (note: corrects the N.p design; no schema bump required)
- [x] Bump version to v2.4.16 in `project_guide/version.py` and `pyproject.toml`
- [x] Verify: all tests pass, ruff clean

### Story N.r: v2.4.17 LLM vs Developer Invocation Rule in Pyve Essentials [Done]

Teach the LLM to keep `pyve run` out of user-facing command suggestions. The wrapper is only needed because the LLM's Bash-tool shell does not auto-activate `.venv/`; the developer's shell typically does. Without this rule, the LLM generalizes from a successful `pyve run <cmd>` execution and echoes the wrapped form back to the developer in "next, run:" prompts — overriding the bare form that mode templates already use. Observed in the wild in `archive_stories` (LLM suggested `pyve run project-guide mode plan_phase` instead of `project-guide mode plan_phase`).

- [x] Add a new `### LLM-internal vs. developer-facing invocation` subsection to `project_guide/templates/project-guide/templates/artifacts/project-essentials-pyve.md`, placed immediately after the existing "Runtime code / Tests / Dev tools / Install dev tools" bullet list (before the `### Python invocation rule` subsection)
  - [x] State the rule: `pyve run` is for the LLM's own Bash-tool invocations; developer-facing suggestions use the bare form verbatim from the mode template
  - [x] Include ✅/❌ examples using `project-guide mode plan_phase`
  - [x] Include a **Why:** line referencing the Bash-tool shell vs. the developer's (typically pyve/direnv-activated) shell
  - [x] Include a **How to apply:** line: "Never prepend environment wrappers (`pyve run`, `poetry run`, `uv run`, etc.) to commands you quote from a mode template."
- [x] Run `pyve run project-guide update` to propagate the edited template into `docs/project-guide/` for this project (dogfooding)
- [x] Verify: rendered `docs/project-guide/go.md` contains the new subsection under `## Project Essentials`
- [x] Tests in `tests/test_render.py` (new "Story N.r" section):
  - [x] When pyve is detected, rendered `go.md` for any mode contains the new subsection heading (e.g., substring `"LLM-internal vs. developer-facing invocation"`)
  - [x] The subsection is absent when pyve is not detected (regression guard for the existing `project-essentials-pyve.md` inclusion gate)
- [x] Update `CHANGELOG.md` with v2.4.17 entry
- [x] Bump version to v2.4.17 in `project_guide/version.py` and `pyproject.toml`
- [x] Verify: all tests pass, ruff clean

### Story N.s: v2.4.18 project_name in Config + Silent-Placeholder Guard [Done]

Fix the archive_stories bug where a fresh `stories.md` is written with literal `{{ project_name }}` / `{{ programming_language }}` placeholders. Root cause: `perform_archive` relies on a strict regex parse of the old `stories.md` header to recover these values, has no fallback, and `render_fresh_stories_artifact` doesn't detect unrendered placeholders before writing. Fix: add `project_name` as a per-project Config field (populated at `init` via a resolution chain), pass it into the archive context, and add a post-render placeholder validator so silent drops become loud failures. Scope is deliberately narrow — broader integrity checks (header-vs-config drift, schema age, bundled-template drift) go to the deferred `project-guide check` command in the Future section.

- [x] Add `project_name: str = ""` field to `Config` dataclass in `project_guide/config.py`
- [x] Update `Config.load()` / `Config.save()` for round-trip; add `test_config_project_name_round_trip` to `tests/test_config.py`
- [x] Add `--project-name` option to `init` in `cli.py`; resolve via `_resolve_setting` (from N.c) with env var `PROJECT_GUIDE_PROJECT_NAME`; fallback chain: CLI flag → env → `pyproject.toml` `[project] name` → `Path.cwd().name`
  - [x] Extract the `pyproject.toml` lookup into a small helper in `runtime.py` (`_detect_project_name_from_pyproject()`) so the logic is unit-testable and non-Python projects can be extended later
  - [x] Persist the resolved value into `.project-guide.yml`
- [x] Update `cli.py:archive_stories_cmd` to merge `config.project_name` into the context passed to `perform_archive` (override `metadata.common`): `context = {**dict(metadata.common), "project_name": config.project_name}`
- [x] Add a one-line drift warning in `cli.py:archive_stories_cmd` (not a failure): if `Path.cwd().name != config.project_name`, print `⚠ cwd name '<cwd>' differs from config project_name '<name>' — archive will use the config value` to stderr. Exit 0.
- [x] Add post-render placeholder validator to `render_fresh_stories_artifact` in `project_guide/actions.py`:
  - [x] Reuse the `_UNRENDERED_PLACEHOLDER_RE` pattern from `render.py` (import it, or extract to a shared module — `runtime.py` is the natural home)
  - [x] After rendering, scan for unrendered `{{ name }}` placeholders; if any found, raise `ActionError` listing the undefined variable names and the file being written
  - [x] This is the root-cause guard: any future code path that forgets to populate a template variable fails loudly instead of silently corrupting the output
- [x] Tests in `tests/test_config.py` (new "Story N.s" section):
  - [x] `project_name` round-trips through `save`/`load`
  - [x] Absent field defaults to `""` (regression guard, additive-with-default policy)
- [x] Tests in `tests/test_cli.py` (new "Story N.s" section):
  - [x] `init --project-name explicit-name` → config `project_name: explicit-name`
  - [x] `PROJECT_GUIDE_PROJECT_NAME=env-name init` (no flag) → config `project_name: env-name`
  - [x] `init` in a dir containing a minimal `pyproject.toml` with `[project] name = "from-pyproject"` → config `project_name: from-pyproject`
  - [x] `init` with no flag, no env, no pyproject.toml → config `project_name` equals `Path.cwd().name`
  - [x] `archive-stories` with no header in `stories.md` and `config.project_name="demo"` → fresh `stories.md` contains `demo`, no literal `{{` placeholders
  - [x] `archive-stories` where `Path.cwd().name` differs from `config.project_name` → warning printed to stderr; command still exits 0
- [x] Tests in `tests/test_actions.py` (new "Story N.s" section):
  - [x] `render_fresh_stories_artifact` raises `ActionError` when context is missing `project_name` (undefined variable → lenient placeholder → validator catches it)
  - [x] Error message names the offending variable(s) and the template being rendered
  - [x] Successful render with all variables populated still passes validation (regression guard)
- [x] Update `docs/specs/tech-spec.md` Config section: document the new `project_name` field and the `init` resolution chain
- [x] Update `docs/specs/project-essentials.md` — add the resolution chain to the existing `### Config schema versioning` section or a new subsection
- [x] Update `CHANGELOG.md` with v2.4.18 entry
- [x] Bump version to v2.4.18 in `project_guide/version.py` and `pyproject.toml`
- [x] Verify: all tests pass, ruff clean, `pyve run project-guide update` re-renders `go.md` cleanly

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
