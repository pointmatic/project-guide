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

### Story N.f: v2.4.5 --quiet / Output Suppression [Planned]

Add a `--quiet` / `-q` flag to suppress per-file progress chatter from `init`, `update`, and `purge`. Composes with `--no-input` for fully silent unattended runs.

- [ ] Add `--quiet` / `-q` boolean flag to `init`, `update`, and `purge` commands in `cli.py`
- [ ] Update `_copy_template_tree` to accept a `quiet: bool` parameter; suppress per-file progress lines when `True`
- [ ] Update `sync_files` callers in `cli.py` to pass `quiet` through to file-by-file output
- [ ] Errors, summaries (final counts), and explicit warnings are never suppressed regardless of `--quiet`
- [ ] `--quiet` and `--no-input` compose cleanly: `init --no-input --quiet` produces no stdout on success
- [ ] Tests in `tests/test_cli.py`:
  - [ ] `init --quiet` produces no per-file lines; summary count line still present
  - [ ] `update --quiet` suppresses per-file sync output
  - [ ] `purge --quiet --force` produces no prompts or progress lines
  - [ ] Error output is still emitted when `--quiet` is set (regression guard)
- [ ] Bump version to v2.4.5
- [ ] Update CHANGELOG.md

### Story N.g: v2.4.6 Story Detection in status [Planned]

`project-guide status` gains a **Stories** section showing backlog counts and the next unstarted story — giving the developer an at-a-glance view of progress without opening `stories.md`.

- [ ] Add `_read_stories_summary(spec_artifacts_path: str) -> StoriesSummary | None` helper (new `project_guide/stories.py` or inline in `cli.py`)
  - [ ] Reads `<spec_artifacts_path>/stories.md` via regex; returns `None` if absent or has no story headings
  - [ ] Counts: total stories, `[Done]`, `[In Progress]`, `[Planned]`
  - [ ] Identifies the first non-Done story for the "Next:" line
- [ ] Update `status` output to include a **Stories** section when data is available:
  ```
  Stories: 13 total — 0 done, 0 in progress, 13 planned
    Next: Story N.a: v2.4.0 Rename code_velocity → code_direct
  ```
- [ ] `--verbose` shows per-phase breakdown (phase letter, phase name, done/total count per phase)
- [ ] Section omitted entirely when `stories.md` is absent, empty, or post-archive (no story headings)
- [ ] Tests in `tests/test_cli.py`:
  - [ ] Status with populated stories.md shows correct counts
  - [ ] Status with all-Done stories shows `0 planned, 0 in progress`
  - [ ] Status with no stories.md omits the section
  - [ ] Status with empty post-archive stories.md omits the section
  - [ ] `--verbose` shows per-phase line
- [ ] Bump version to v2.4.6
- [ ] Update CHANGELOG.md

### Story N.h: v2.4.7 Mode Auto-Detection and Interactive Menu [Planned]

`project-guide mode` (no argument) becomes useful: it checks prerequisites and — on a TTY — offers a numbered selection menu instead of a plain list.

- [ ] Update the no-argument path of `mode` command to check each mode's `files_exist` list against the current working directory
  - [ ] Modes with all prerequisites met: marked `✓` (green)
  - [ ] Modes with unmet prerequisites: listed but dimmed; unmet files noted on `--verbose`
- [ ] Add interactive menu (TTY only, i.e. `not should_skip_input()`):
  - [ ] Modes grouped by category: Planning, Coding, Post-Release, Debugging, Documentation, Refactoring
  - [ ] Numbered selection prompt; on valid selection switch mode + re-render `go.md`
  - [ ] Invalid input → re-prompt (max 3 attempts then exit 1 with helpful message)
  - [ ] Under `--no-input` / non-TTY: skip menu, print the `✓`-annotated listing and exit 0
- [ ] Tests in `tests/test_cli.py`:
  - [ ] Mode with all `files_exist` files present → marked available in output
  - [ ] Mode with missing prerequisite → marked unavailable
  - [ ] Non-TTY `CliRunner` invocation → plain listing rendered, no interactive prompt
  - [ ] Selecting a valid number switches mode (integration test via `isolated_filesystem`)
- [ ] Bump version to v2.4.7
- [ ] Update CHANGELOG.md

### Story N.i: v2.4.8 Per-Project Metadata Overrides [Planned]

Allow projects to patch specific mode fields in `.project-guide.yml` — e.g. change `next_mode`, override `files_exist` prerequisites — without editing the bundled `.metadata.yml`.

- [ ] Add `metadata_overrides: dict[str, dict] = field(default_factory=dict)` to `Config` dataclass
- [ ] Update `Config.load()` / `Config.save()` for round-trip; add round-trip test to `tests/test_config.py`
- [ ] Add `_apply_metadata_overrides(metadata: Metadata, overrides: dict) -> None` in `project_guide/metadata.py`
  - [ ] Supported fields: `next_mode`, `files_exist`, `info`, `description`
  - [ ] Unknown mode name in overrides → `MetadataError`
  - [ ] Unknown field in overrides → `MetadataError`
  - [ ] Unmentioned fields on a mode are unchanged (partial patch semantics)
- [ ] Call `_apply_metadata_overrides` after `load_metadata()` in all paths that load metadata (render, mode-switch, status)
- [ ] Tests in `tests/test_metadata.py`:
  - [ ] Override `next_mode` → reflected in `ModeDefinition`
  - [ ] Override `files_exist` → reflected in prerequisite check
  - [ ] Unknown mode name → `MetadataError`
  - [ ] Unknown field → `MetadataError`
  - [ ] Empty overrides dict → no change (regression guard)
- [ ] Bump version to v2.4.8
- [ ] Update CHANGELOG.md

### Story N.j: v2.4.9 Pyve Detection and Bundled project-essentials-pyve.md [Planned]

Auto-detect Pyve at `init` time and ship a bundled Pyve-focused project-essentials template so every Pyve project gets correct dev-environment rules without writing them from scratch.

- [ ] Add `pyve_version: str | None = None` to `Config` dataclass; update load/save round-trip
- [ ] In `init`, run `subprocess.run(['pyve', '--version'], capture_output=True, text=True, timeout=5)`
  - [ ] On success (exit 0): extract version string from stdout; store in config as `pyve_version`
  - [ ] On failure (`FileNotFoundError`, non-zero exit, or timeout): store `None`; detection failure is non-fatal
- [ ] Update `render.py` to pass `pyve_installed: bool` and `pyve_version: str | None` as Jinja2 context variables
- [ ] Create `project_guide/templates/project-guide/templates/artifacts/project-essentials-pyve.md`:
  - [ ] Section: two-environment pattern (runtime `.venv/` vs dev testenv `.pyve/testenv/venv/`; canonical invocation forms `pyve run python`, `pyve test`, `pyve testenv run ruff/mypy`; "pytest not found → use `pyve test`" signal; "do not `pip install -e '.[dev]'` into the main venv" anti-pattern)
  - [ ] Section: `requirements-dev.txt` story-writing rule — any story introducing dev tooling (ruff, mypy, pytest, types-* stubs) must include a task to create/update `requirements-dev.txt` so `pyve testenv --install -r requirements-dev.txt` reproduces the dev env in one step
  - [ ] No top-level `#` heading; `###` subsections (consistent with project-essentials convention)
- [ ] Update `scaffold-project-mode.md` and `plan-tech-spec-mode.md` with a `{% if pyve_installed %}` branch: instruct LLM to read `project-essentials-pyve.md` and copy/merge its content into `docs/specs/project-essentials.md`
- [ ] Tests:
  - [ ] `init` with mocked `pyve --version` success → `pyve_version` set in config
  - [ ] `init` with mocked `FileNotFoundError` → `pyve_version: null`, init exits 0
  - [ ] Rendered `scaffold_project` with `pyve_installed=True` contains the pyve merge instruction
  - [ ] Rendered `scaffold_project` with `pyve_installed=False` omits it
  - [ ] `project-essentials-pyve.md` renders without unrendered placeholders (parametrized by `test_every_mode_renders_successfully` or a dedicated artifact-render test)
- [ ] Bump version to v2.4.9
- [ ] Update CHANGELOG.md

### Story N.k: v2.4.10 Memory Review in scaffold_project Mode [Planned]

`scaffold_project` runs once per project setup — the natural moment to reconcile prior-session LLM memories with the project's permanent knowledge base in `project-essentials.md`.

- [ ] Add a **Memory Review** step to `scaffold-project-mode.md` (penultimate step, before "Present for Approval"):
  - [ ] Instruct LLM to read recorded memories from the project memory store (e.g., `.claude/projects/` files for Claude Code users)
  - [ ] For each memory: evaluate whether it is project-specific and should live in `project-essentials.md` rather than (or in addition to) memory
  - [ ] Present candidates to the developer: "I found N memories. These may belong in `project-essentials.md`: …"
  - [ ] Await developer confirmation of which (if any) to copy/migrate
  - [ ] Append confirmed items to `project-essentials.md` following the heading convention (`###` subsections, no top-level `#`)
  - [ ] Escape hatch: if the memory store is empty or inaccessible, note this briefly and continue
- [ ] Tests in `tests/test_render.py` (new "Story N.k" section):
  - [ ] Rendered `scaffold_project` contains the Memory Review step
  - [ ] Memory Review step appears before "Present for Approval"
  - [ ] Escape hatch language ("empty or inaccessible") present
- [ ] Bump version to v2.4.10
- [ ] Update CHANGELOG.md

### Story N.l: v2.4.11 Memory Reflection Instruction in _header-common.md [Planned]

Teach every mode to pause before recording a new memory and ask: does this belong in `project-essentials.md` instead?

- [ ] Add rule #7 to the **Rules** block in `project_guide/templates/project-guide/templates/modes/_header-common.md`:
  - [ ] Text (exact): "Before recording a new memory, reflect: is this fact project-specific (belongs in `docs/specs/project-essentials.md`) or cross-project (belongs in LLM memory)? Could it belong in both? If project-specific, add it to `project-essentials.md` instead of or in addition to memory."
- [ ] Tests in `tests/test_render.py` (new "Story N.l" section):
  - [ ] `test_header_common_memory_reflection_rule_renders_in_every_mode` — parametrized over all mode names via `_get_all_mode_names()`; asserts the pinned substring `"Before recording a new memory, reflect"` appears inside the **Rules** block (positional assertion, consistent with the M.g approval-gate test pattern)
- [ ] Verify: `test_every_mode_renders_successfully` still passes (no template regressions)
- [ ] Bump version to v2.4.11
- [ ] Update CHANGELOG.md

### Story N.m: v2.4.12 Phase N Documentation and CHANGELOG [Planned]

- [ ] Update `docs/specs/features.md`:
  - [ ] FR-1 modes table: `code_direct` (was `code_velocity`), `scaffold_project` (was `project_scaffold`); mode count
  - [ ] New FRs for N3–N9 (or update existing FRs to reflect new flags and behaviors)
  - [ ] `.project-guide.yml` schema block: add `test_first`, `pyve_version`, `metadata_overrides`
- [ ] Update `docs/specs/tech-spec.md`:
  - [ ] Filename conventions table (renamed mode templates)
  - [ ] `Config` dataclass fields
  - [ ] `cli.py` and `metadata.py` behavior sections
- [ ] Update `README.md`: mode table (renames); command reference (new flags); config schema
- [ ] Update `docs/site/user-guide/modes.md`: renamed mode entries (`code_direct`, `scaffold_project`)
- [ ] Update `docs/site/user-guide/commands.md`: new flags for init/update/purge; status Stories section; mode menu behavior
- [ ] Update `CHANGELOG.md` with v2.4.0–v2.4.11 entries (already landed per-story) and a v2.4.12 entry for this documentation pass
- [ ] Verify: all tests pass, ruff clean, `pyve run project-guide update` re-renders `go.md` cleanly
- [ ] Bump version to v2.4.12

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

### Template & Rendering [Deferred]

- Support for literal `{{ var }}` strings in template output — use `{% raw %}...{% endraw %}` on a case-by-case basis; bridge with a general solution only if the pattern becomes common.
