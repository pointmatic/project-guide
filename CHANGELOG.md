# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.5] - 2026-04-10

### Added
- **Default mode "Suggesting the Next Step" section** (Story K.f) — `default-mode.md` now teaches the LLM to read `docs/specs/stories.md` (when present), check the status of every `### Story X.y: ... [<status>]` heading, and branch on three cases:
  - **All stories `[Done]`**: prompt the developer with both `archive_stories` (clean slate, archive then plan) and `plan_phase` (plan against history) as Option A and Option B, explaining the trade-off and including "Use this when:" guidance for each. Wait for the developer to choose before changing modes.
  - **At least one non-`[Done]`**: defer to the existing project lifecycle suggestions at the top of the mode (no behavior change).
  - **No `stories.md`**: direct the developer to `project-guide mode plan_concept` to begin the lifecycle.
- Detection happens at LLM read time (consistent with the v2 architecture — no Python-side check is added). The bundled mode template carries the prompt language for all three branches simultaneously.

### Tests
- No new tests; the existing parametrized `test_every_mode_renders_successfully` covers `default` and confirms the template still renders without errors. Manual verification via `runner.isolated_filesystem` confirms the rendered guide contains the all-Done section, both option labels, and the fresh-project hint.
- **193 tests pass** (unchanged from K.e).

## [2.1.4] - 2026-04-10

### Added
- **`plan_phase` mode handles post-archive empty `stories.md`** (Story K.e):
  - Step 1 of the mode template now distinguishes two `stories.md` shapes — "Populated" (one or more `## Phase <Letter>:` sections) vs "Empty (post-archive)" (header + `## Future` only). For the empty case, the template instructs the LLM to look in `docs/specs/.archive/` for `stories-vX.Y.Z.md` files, read the highest-version one, and use its highest phase letter as the basis for the next.
  - Step 5 explicitly describes the next-phase-letter algorithm (populated → successor of highest; empty + archive → successor of archived highest; neither → start at `A`) and tells the LLM to insert the new phase as the first phase when `stories.md` was empty.
  - Phase letters **continue across the archive boundary** — they do not reset.
- **`increment_phase_letter(letter)` helper** in `actions.py` — pure function returning the base-26-no-zero successor of a phase letter. Examples: `A→B`, `Z→AA`, `AZ→BA`, `ZZ→AAA`. Raises `ActionError` on invalid input (empty string, lowercase, non-letter characters).
- **`next_phase_letter(stories_text, archive_dir)` helper** in `actions.py` — implements the post-archive lookup algorithm in Python so future tooling can call it directly (e.g., a future `status` command or a Python-driven `plan_phase` action). The current `plan_phase` mode template describes the same algorithm in prose so the LLM can perform it directly without invoking Python (consistent with v2 architecture).
- **`_find_latest_archived_stories(archive_dir)` helper** — filters `.archive/` to files matching `stories-vX.Y.Z.md` (any stem starting with `stories`), ignoring unrelated archived artifacts like `phase-j-modes-plan.md` or `ux-problems-v2.0.10.md`. Returns the file with the highest semver version, or `None` if none exist.

### Tests
- 16 new tests in `tests/test_actions.py`:
  - **`extract_stories_header_context`** — 3 tests (double-hyphen, em-dash, missing → empty dict).
  - **`increment_phase_letter`** — 7 tests covering simple advance, `Z→AA` carry, two-letter advance, `ZZ→AAA` carry, three-letter advance, and three invalid-input cases.
  - **`next_phase_letter`** — 6 fixture tests covering: populated stories.md returns successor (and ignores `.archive/`), empty stories.md + Phase J archive → `K` (using the real `docs/specs/.archive/stories-v2.0.20.md` fixture), empty stories.md + missing `.archive/` → `A`, empty + empty `.archive/` → `A`, empty + `.archive/` containing only non-stories files → `A`, and empty + multiple archived stories versions picks the highest-version one.
- **193 tests pass** (up from 177).

### Notes
- The `next_phase_letter` Python helper duplicates an algorithm that the LLM can also perform from the rendered mode template. The duplication is deliberate: the v2 architecture prefers LLM-driven detection at read time, but having a Python implementation tested against the same fixture means future code (a `status` validator, a Python-driven plan_phase, or an end-to-end test of the full archive→plan_phase flow) can rely on the algorithm without re-implementing it. The tests assert both implementations stay in sync via the Phase J fixture.

## [2.1.3] - 2026-04-10

### Added
- **`archive_stories` mode** (Story K.d) — new sequence-style mode productionizes the archive pipeline from K.a/K.c:
  - New mode template `project_guide/templates/project-guide/templates/modes/archive-stories-mode.md` walks the LLM through reading the current `stories.md`, warning about any non-`[Done]` stories, showing the planned archive path, awaiting developer approval, running the archive command, and suggesting `plan_phase` as the next mode. Includes the `_phase-letters.md` shared include from K.b.
  - New `archive_stories` entry in `.metadata.yml` under the Post-Release section with `action: archive` on `stories.md`, `next_mode: plan_phase`, and a `files_exist: [stories.md]` prerequisite that surfaces a warning when the source is missing.
- **`project-guide archive-stories` CLI command** — new subcommand that wraps `project_guide.actions.perform_archive`. Loads the project's `.project-guide.yml`, looks up the `archive_stories` mode, finds its archive artifact, resolves the bundled `stories.md` template (always uses the package-bundled copy, not the project's installed templates, so the re-render is not affected by any local template edits), and invokes `perform_archive` with the merged metadata context. Prints a summary: archived path, version, last phase letter, and whether a Future section was carried.
- **`extract_stories_header_context(text)` helper** in `actions.py` — parses the stories.md first-line header (`# stories.md -- <project-name> (<programming-language>)`) into a context dict. `perform_archive` merges extracted values with the caller's context (caller wins) so the fresh re-render preserves the header even when the caller doesn't supply `project_name`/`programming_language` explicitly.

### Changed
- **`render_fresh_stories_artifact` uses lenient undefined rendering.** Missing Jinja context variables now render as `{{ name }}` placeholders instead of empty strings, preventing header corruption like `# stories.md --  (Python)` when a project's metadata doesn't include `project_name`. Implemented via a local `_LenientUndefined` class in `actions.py` (mirrors `render.py._LenientUndefined`; kept local to avoid an import cycle).

### Removed
- **`scripts/spike_archive_stories.py`** — the K.a throwaway script is now superseded by `project_guide.actions.perform_archive` + `project-guide archive-stories`. The empty `scripts/` directory was removed as well.

### Tests
- New `tests/test_archive_stories_mode.py` — 9 end-to-end integration tests using `click.testing.CliRunner`:
  - **Mode template rendering**: `mode archive_stories` renders a go.md containing the mode-specific content, the `project-guide archive-stories` command, the phase-letters include, and the `plan_phase` next-mode suggestion.
  - **Prerequisite warning**: missing `stories.md` surfaces the "Prerequisites not yet met" warning.
  - **Happy path**: `archive-stories` moves the source to `.archive/stories-v1.0.0.md`, preserves the source byte-for-byte, re-renders a fresh `stories.md` with carried Future section and preserved `demo-project` header.
  - **No-Future fallback**: source without a Future section falls back to the template default (HTML-comment explainer present).
  - **Error paths**: missing config, missing source, pre-existing archive target (idempotency guard), no versioned story headings. Each error path verifies the source is left untouched.
- **177 tests pass** (up from 168 after K.c refactor).

### Notes
- The mode template is LLM-conversational (read/warn/show/approve), but the actual mutation is Python-deterministic (`project-guide archive-stories` shelling to `perform_archive`). This keeps the file-mutation logic testable and transactional while the decision-making stays in the LLM conversation.

## [2.1.2] - 2026-04-10

### Added
- **`archive` artifact action type** (Story K.c) — new `project_guide/actions.py` module implements the deterministic archive pipeline:
  - `detect_latest_version(text)` — scans `### Story X.y: vN.N.N` headings and returns the numerically highest version (not lexical).
  - `detect_latest_phase_letter(text)` — scans `## Phase <Letter>:` headings using base-26-no-zero ordering (`A` < `Z` < `AA` < `ZZ` < `AAA`).
  - `extract_future_section(text)` — returns the `## Future` block verbatim to EOF, or `""` if absent.
  - `render_fresh_stories_artifact(template, context, future)` — re-renders the bundled `stories.md` artifact template with an empty body, substituting the template's default `## Future` block with a carried section when provided.
  - `perform_archive(source, template, context)` — end-to-end runtime: moves `source` to `<dirname>/.archive/<stem>-vX.Y.Z<suffix>`, re-renders a fresh source with Future preserved, best-effort rollback on failure. Returns `ArchiveResult(archived_to, source_rewritten, version, phase_letter, future_carried)`.
- **`ActionType` StrEnum** and **`Artifact` dataclass** in `project_guide/actions.py`. `ActionType.CREATE`/`MODIFY`/`ARCHIVE` are the canonical action values; `StrEnum` means `ActionType.ARCHIVE == "archive"` is `True`, so YAML round-trips as bare strings. `Artifact` is a typed, validated representation of a mode's artifact entry (`file | webpage | framework` + `action`).
- **`ActionError` exception** in `project_guide/exceptions.py` for archive action failures at runtime.

### Changed
- **BREAKING: `ModeDefinition.artifacts` is now `list[Artifact]`, not `list[dict]`.** Every mode's `artifacts:` list is parsed into typed `Artifact` dataclass instances during metadata load. Consumers must use attribute access (`artifact.file`, `artifact.action`) instead of dict access (`artifact["file"]`). No CLI/runtime code in this package consumed the old dict shape, so this is only visible to tests and any future external integrations. Pre-release (Phase K) acceptable churn.
- **`metadata.py` validates artifact action values at load time** — any `action:` field on an artifact must be one of `ActionType.{CREATE,MODIFY,ARCHIVE}`. Artifacts without an `action:` field continue to be tolerated (legacy form). Typos like `action: arhive` now fail at metadata load time with a helpful error message listing valid values.

### Tests
- New `tests/test_actions.py` — 30 tests covering: ActionType enum and StrEnum behavior, Artifact dataclass parsing (file/webpage/framework targets, missing action, unknown action, non-mapping input), version/phase/future detection (including negative cases and base-26 ordering), fresh-render behavior, and a real-file round-trip against `.archive/stories-v2.0.20.md` (the Phase J archive).
- Updated tests in `tests/test_metadata.py` — 4 new tests verifying `action: archive` parses to `ActionType.ARCHIVE`, `action: create`/`modify` still parse, missing `action:` yields `artifact.action is None`, and unknown actions raise `MetadataError`. Existing tests updated to use attribute access on `Artifact`.
- **168 tests pass** (up from 133).

### Notes
- This story adds the action **type** only. Wiring the action into a CLI-invocable `archive_stories` mode (new mode template, metadata entry, and the mode command routing it to `perform_archive`) is the next story, K.d.
- The `ActionType`/`Artifact` refactor replaced an earlier in-progress design using bare string constants (`ACTION_CREATE`, `ACTION_MODIFY`, `ACTION_ARCHIVE`, `VALID_ARTIFACT_ACTIONS` frozenset) after a mid-story decision to prioritize code clarity over backward compatibility. No releases shipped with the string-constant form.

## [2.1.1] - 2026-04-10

### Added
- **Phase and Story ID Scheme shared include** (Story K.b) — new template `project_guide/templates/project-guide/templates/modes/_phase-letters.md` documents the base-26-no-zero phase letter scheme (`A`–`Z`, `AA`–`ZZ`, `AAA`–…), the matching story sub-letter scheme, and the rule that letters continue across `archive_stories` boundaries by consulting `docs/specs/.archive/`. The include is now rendered once inside both `plan_stories` and `plan_phase` so the rules live in one place.
- **`## Future` section in the stories artifact template** — `project_guide/templates/project-guide/templates/artifacts/stories.md` now renders a `## Future` section after `{{phases_and_stories}}` with an inline note describing what belongs there (deferred stories, future phases, project-level out-of-scope items). This gives `archive_stories` a canonical place to preserve the "carry-over" section across archive cycles.
- **Tests**: two new tests in `tests/test_render.py` verify the artifact template renders a `## Future` section when `phases_and_stories` is empty and when it is populated (with the Future section appearing after the phases content). 133 tests pass.

## [2.1.0] - 2026-04-10

### Added
- **Spike: archive_stories pipeline** (Story K.a) — throwaway script `scripts/spike_archive_stories.py` exercises the full archive flow end-to-end (latest-version detection, latest-phase-letter detection, `## Future` extraction, archive move, fresh `stories.md` re-render). Validates the critical path before the productionized `archive_stories` mode lands in K.c/K.d. Verified round-trip against a copy of `.archive/stories-v2.0.20.md` (Phase J file): archived file byte-matches the original, fresh `stories.md` contains the carried `## Future` section. Will be deleted in K.d once superseded.

## [2.0.20] - 2026-04-10

### Changed
- **Renamed Jinja2 template source** `templates/go.md` → `templates/llm_entry_point.md`. The rendered output is still `go.md` (unchanged). This eliminates confusion when @-mentioning files in an LLM chat — there's now only one `go.md` (the rendered entry point the LLM reads).

### Added
- **Shell completion for `project-guide mode <TAB>`** — dynamically completes mode names from the active project's `.metadata.yml`. Click's built-in shell completion handles command names and flags automatically.
- Setup instructions for bash, zsh, and fish in [Installation Options](https://pointmatic.github.io/project-guide/user-guide/install-options/).

## [2.0.19] - 2026-04-10

### Changed
- **`update` no longer prompts for modified files** — files whose content differs from the bundled template are now auto-backed-up (`.bak.<timestamp>`) and overwritten without asking. The previous prompt was misleading because hash-based sync can't distinguish "user modified the file" from "the bundled template changed in this version" — both look identical.
- Use `project-guide override <file> <reason>` to lock files that should not be touched by `update`.
- Removed "Modified files detected" / "Skipped (user declined)" / "Updated (approved by user)" output sections.

### Removed
- `sync_files()` no longer returns a `modified` list — its 5-tuple is now a 4-tuple `(updated, skipped, current, missing)`. Files that previously went into `modified` now go into `updated` (with backups).
- `apply_file_update` is no longer used in `cli.py` (still exported from `sync.py` for internal use)

## [2.0.18] - 2026-04-10

### Fixed
- **`go.md` is no longer gitignored** — agentic LLMs that respect gitignore patterns couldn't read the rendered entry point, breaking the entire workflow. The file is now tracked in git, which also gives mode switches a useful git history footprint.
- **Mode heading bug** — planning mode templates rendered `# concept.md — {{ project_name }}` (with the literal Jinja2 placeholder, since `project_name` was never defined). Replaced with a single mode heading in `_header-common.md` that uses actual metadata: `# {{ mode_name }} mode ({{ sequence_or_cycle }})` followed by a `> {{ mode_info }}` blockquote.

### Changed
- `_ensure_gitignore_entry()` no longer adds `go.md` to `.gitignore` (only `*.bak.*` patterns remain)
- All 14 mode templates stripped of their individual H1 headings in favor of the centralized mode heading from `_header-common.md`

## [2.0.17] - 2026-04-09

### Changed
- **Renamed `project_setup` mode to `project_scaffold`** — "setup" was too generic; "scaffold" matches the mode's actual purpose (creating project files) and industry conventions. Breaking change for anyone using `project-guide mode project_setup`.
- Renamed template file: `project-setup-mode.md` → `project-scaffold-mode.md`
- Slimmed down `docs/site/user-guide/workflow.md` from 376 lines to ~85 lines, removing duplication with getting-started, commands, and overrides pages

### Added
- `docs/site/user-guide/modes.md` — comprehensive reference for all 15 modes with type, prerequisites, artifacts, and Mode Flow diagram
- "When to Switch Modes" table and "The HITLoop Cycle" section in workflow guide

## [2.0.13] - 2026-04-09

### Changed
- `status` command redesigned with grouped sections: Mode (with prerequisites), Guide, Files — each with contextual action prompts
- File sync now uses content hash comparison instead of version comparison — a version bump no longer marks unchanged files as stale
- `(installed: vX.X.X)` only shown in status when it differs from package version
- Prerequisites line omitted when the mode has none
- Renamed `go-project-guide.md` → `go.md` — shorter, easier to autocomplete

### Removed
- Version-based file freshness check — `compare_versions` no longer used by `status` or `sync_files`

## [2.0.12] - 2026-04-08

### Changed
- `status` command redesigned: compact summary by default, per-file list only when problems exist
- Status header now shows `Target:` directory, mode on one line with description
- Added `--verbose` / `-v` flag to force full per-file list
- Status footer shows `Run 'project-guide mode' to see available modes.`
- Renamed "guides" to "files" throughout: the sync system tracks files, not guides
  - `--guides` CLI flag → `--files`
  - `GuideNotFoundError` → `ProjectFileNotFoundError`
  - `GuideOverride` → `FileOverride`
  - sync.py: `get_all_guide_names` → `get_all_file_names`, `copy_guide` → `copy_file`, `backup_guide` → `backup_file`, `apply_guide_update` → `apply_file_update`, `sync_guides` → `sync_files`
  - All user-facing strings updated

## [2.0.11] - 2026-04-08

### Changed
- Rendered `go-project-guide.md` now outputs to `docs/project-guide/` instead of `docs/specs/` — it's mode instructions, not a spec artifact
- Entry point template moved from `project-guide/go-project-guide.md` to `project-guide/templates/go-project-guide.md`
- Jinja2 loader simplified to search only the `templates/` subdirectory
- Developer instruction in `_header-common.md` updated to `Read docs/project-guide/go-project-guide.md`
- `.gitignore` entry updated to `docs/project-guide/go-project-guide.md`
- `target_dir` now available as a Jinja2 context variable in templates

## [2.0.10] - 2026-04-08

### Fixed
- `init` now starts in `default` mode instead of `plan_concept`
- `files_exist` prerequisites no longer include template paths that resolve to repo-internal locations; only user-created spec artifacts are checked

### Changed
- Renamed metadata file from `project-guide-metadata.yml` to `.metadata.yml` (hidden, shorter — already scoped by `project-guide/` directory)
- Added `metadata_file` field to `.project-guide.yml` config — CLI reads the metadata filename from config instead of hardcoding it
- Render errors now show actionable guidance: run `project-guide status` and `project-guide update`
- `sync.py` guide discovery now includes dotfiles (`.*.yml` pattern)

### Added
- Parametrized test that renders every mode from the bundled metadata — proves a fresh install works and catches regressions

## [2.0.9] - 2026-04-07

### Added
- New `refactor_plan` cycle mode — migrate planning artifacts (concept, features, tech-spec) to v2.x artifact template format
- New `refactor_document` cycle mode — migrate documentation artifacts (descriptions, landing page, MkDocs) to v2.x format
- v1.x → v2.x migration notice in `status` command when config version is "1.0" or target_dir is "docs/guides"

## [2.0.8] - 2026-04-07

### Added
- New `project_setup` mode -- one-time project scaffolding (LICENSE, copyright headers, package manifest, README with badges, CHANGELOG, .gitignore)
- `project-setup-mode.md` template with step-by-step setup instructions and approval checklist

### Changed
- `default-mode.md` slimmed to pure navigation -- project lifecycle overview with mode table, no setup instructions
- Mode flow updated: `default` -> `project_setup` -> `plan_concept` -> ... -> `code_velocity`
- `project_setup` added to `project-guide-metadata.yml` between `default` and `plan_concept`

## [2.0.7] - 2026-04-07

### Added
- 5 new tests for `mode` command (no config, list modes, invalid name, config update, render output)
- `mode` command added to README Command Reference

### Changed
- README updated for v2.0: new Quick Start with mode workflow, Available Modes table, updated config example, corrected test stats (112 tests, 92% coverage)
- Test coverage increased from 90% to 92% (112 tests, up from 107)

## [2.0.6] - 2026-04-07

### Changed
- `default-mode.md` rewritten as a full project lifecycle overview (setup, planning, implementation) with links to specific modes -- serves as a friendly starting point for new users
- Distributed prerequisites from old default mode into appropriate planning modes:
  - Project idea -> `plan-concept-mode.md`
  - License preference, target audience, constraints -> `plan-features-mode.md`
  - Language/runtime, preferred frameworks -> `plan-tech-spec-mode.md`
- Added `default` mode to `project-guide-metadata.yml`

### Removed
- `best-practices-guide.md` -- content absorbed into `code-velocity-mode.md` and `code-test-first-mode.md`

## [2.0.5] - 2026-04-07

### Added
- Brand descriptions artifact template (`templates/artifacts/brand-descriptions.md`)

### Fixed
- Renamed `brand-mode.md` to `document-brand-mode.md` and `document-mode.md` to `document-landing-mode.md` to match metadata definitions
- Added missing `mode_template` field to `document_landing` mode in metadata
- Escaped GitHub Actions `${{ }}` syntax in `document-landing-mode.md` to prevent Jinja2 conflict
- Converted `{info}` / `{description}` placeholders in brand mode to Jinja2 `{{ mode_info }}` / `{{ mode_description }}`

## [2.0.4] - 2026-04-07

### Added
- Complete `code-velocity-mode.md` -- velocity coding workflow with cycle steps, practices, and mode switching guidance
- Complete `code-test-first-mode.md` -- TDD workflow with red-green-refactor cycle, test writing guidelines, and test hierarchy
- `debug-mode.md` already complete from prior work (retained as-is)
- All cycle mode templates include `{% include "modes/_header-cycle.md" %}`

## [2.0.3] - 2026-04-07

### Added
- Complete planning mode templates: `plan-features-mode.md`, `plan-tech-spec-mode.md`, `plan-stories-mode.md`, `plan-phase-mode.md`
- Artifact templates: `features.md`, `tech-spec.md`, `stories.md`
- All mode templates now include appropriate header partials (`_header-sequence.md` or `_header-cycle.md`)

### Fixed
- Entry point template renamed to `go-project-guide.md.j2` to prevent rendered output from overwriting the Jinja2 source template
- Explicit `encoding="utf-8"` in Jinja2 `FileSystemLoader` and `write_text()` to fix Windows cp1252 corruption of em-dash characters

### Changed
- Monolithic Steps 0-4 content removed from `go-project-guide.md.j2` — entry point is now a thin shell (header + mode include)

## [2.0.2] - 2026-04-07

### Changed
- `update` command re-renders `go-project-guide.md` after syncing template files that affect the rendered output
- Override/unoverride work on template-relative paths (e.g., `templates/modes/plan-concept-mode.md`)
- Guide discovery in `sync.py` fully scans new directory structure (old `guides/` references removed)

## [2.0.1] - 2026-04-07

### Changed
- `status` command now shows current mode name, description, guide path, and prerequisite status before guide sync details
- Windows cross-platform fix: guide names in `sync.py` always use forward slashes via `as_posix()`

## [2.0.0] - 2026-04-07

### Added
- **Mode-driven template system** — `project-guide mode <name>` sets the active development mode and renders `go-project-guide.md` via Jinja2
- New `mode` CLI command: set mode with argument, list available modes without argument
- New module `metadata.py` — parses `project-guide-metadata.yml`, resolves `{{var}}` placeholders, provides mode lookup
- New module `render.py` — Jinja2 template rendering pipeline for `go-project-guide.md`
- New runtime dependency: `jinja2>=3.1`
- New exception types: `MetadataError`, `RenderError`
- `go-project-guide.md` automatically added to `.gitignore` on init (it is a rendered artifact)
- 11 foundation mode templates: `default`, `plan_concept`, `plan_features`, `plan_tech_spec`, `plan_stories`, `plan_phase`, `code_velocity`, `code_test_first`, `debug`, `document_brand`, `document_landing`
- Artifact templates directory (`templates/artifacts/`) for LLM output formatting
- Header partials (`_header-common.md`, `_header-sequence.md`, `_header-cycle.md`) included via Jinja2

### Changed
- **Breaking:** Default target directory changed from `docs/guides/` to `docs/project-guide/`
- **Breaking:** Config schema version bumped to `2.0` with new `current_mode` field
- `init` now copies the full template tree (modes, artifacts, metadata, developer guides) and renders `go-project-guide.md`
- Template discovery in `sync.py` updated for new directory structure
- Old static guide files (`project-guide.md`, `debug-guide.md`, `documentation-setup-guide.md`) replaced by mode templates
- Config migration: v1.0 configs load with `current_mode: "default"` added automatically
- Test suite expanded to 102 tests (up from 87), coverage at 87%

## [1.5.2] - 2026-04-05

### Added
- 28 new CLI tests covering error paths, edge cases, and user prompts (87 total, up from 59)
- Codecov badge added to README.md

### Changed
- Test coverage increased from 79% to 94% (cli.py: 72% → 97%)
- Minimum coverage threshold raised from 75% to 85% (`--cov-fail-under`)

## [1.5.1] - 2026-04-04

### Changed
- **Renamed Python module directory from `project_guides/` to `project_guide/`**
  - All internal imports updated to `project_guide.*`
  - `importlib.resources` package paths updated to `project_guide.templates.*`
  - All test imports updated
  - GitHub Actions workflows updated (`--cov=project_guide`, `mypy project_guide/`, `ruff check project_guide/`)
  - `pyproject.toml` entry point updated to `project_guide.cli:main`

## [1.5.0] - 2026-04-03

### Changed
- **Removed `project-guides` CLI entry point** — only `project-guide` is now installed
  - Existing users must reinstall: `pip install project-guide`
- Updated all user-facing CLI messages to reference `project-guide`
- Updated guide template to reference `pip install project-guide` and `project-guide init`

### Breaking Change
- The `project-guides` command is no longer installed. Replace all uses with `project-guide`.

## [1.4.1] - 2026-04-03

### Changed
- **Renamed config file from `.project-guides.yml` to `.project-guide.yml`**
  - All CLI commands now read and write `.project-guide.yml`
  - Automatic one-time migration: if `.project-guides.yml` exists and `.project-guide.yml` does not, the file is renamed on next command run with a printed notice
  - Template updated to `.project-guide.yml.template`

## [1.4.0] - 2026-04-03

### Added
- **Reserved `project-guide` package name on PyPI**
  - Added `project-guide` as a second CLI entry point (maps to the same `project_guides.cli:main`)
  - Both `project-guides` and `project-guide` commands work identically
  - Existing users are unaffected; new users should install `project-guide`
  - The old `project-guides` entry point will be removed in v1.5.0

## [1.3.1] - 2026-03-25

### Added
- **Prompt before overwriting user-modified guides**
  - `update` command now prompts `Overwrite <guide>? [y/N]` for each modified file
  - User can accept or decline per-file — declined files are reported as skipped
  - `--force` flag skips the prompt, creates a `.bak` backup, and overwrites automatically
  - `--dry-run` shows modified files with a note that they would be prompted

### Changed
- `sync_guides()` now returns 5-tuple `(updated, skipped, current, missing, modified)`
  - `modified`: files with user edits detected but not yet acted on (caller decides)
  - `--force` moves modified files directly to `updated` list after creating backup
- `update` output now shows "Updated (backed up):" label when `--force` is used
- Test suite expanded to 59 tests with `test_sync_guides_force_overwrites_modified_with_backup`

## [1.3.0] - 2026-03-25

### Added
- **Content-based change detection** in `update` command
  - New `file_matches_template()` function uses SHA-256 hash to compare file content with templates
  - Detects user modifications even when version numbers match
  - `status` command now shows "(modified)" for files with user edits
- **Missing file detection** in `update` command
  - Missing files are now properly detected and reported separately
  - `update` command displays missing files in cyan with "+" indicator
  - Missing files are always created, even if version numbers match

### Fixed
- **Critical bug**: `update` command incorrectly reported "all guides are up to date" when files were missing
- **Critical bug**: `update` command didn't detect user modifications to guide files
- `sync_guides()` now returns 4-tuple `(updated, skipped, current, missing)` instead of 3-tuple

### Changed
- Enhanced `status` command output to differentiate between:
  - Outdated version: "(update available)"
  - User modifications: "(modified)"
  - Missing files: "(missing)"
- Test suite expanded from 53 to 58 tests with 5 new comprehensive tests

## [1.2.7] - 2026-03-10

### Fixed
- **README banner image URL**
  - Changed from relative path to absolute GitHub URL for PyPI compatibility
  - Banner now displays correctly on https://pypi.org/project/project-guides/

## [1.2.6] - 2026-03-10

### Fixed
- **Version comparison bug in sync_guides**
  - Fixed logic to properly mark guides as "current" when installed_version matches package_version
  - Added check for non-existent files when versions match
  - Updated test to use dynamic version import instead of hardcoded value

## [1.2.5] - 2026-03-10

### Changed
- **Updated README.md** with comprehensive documentation integration
  - Added header banner image
  - Updated description with Two-clause Technical Description
  - Added Documentation badge linking to GitHub Pages
  - Added dedicated Documentation section with links to full docs
  - Updated "Why project-guides?" with Friendly Brief Description and HITLoop explanation
  - Updated Key Features with content from Feature Cards
- **Updated pyproject.toml** metadata
  - Added project.urls section (Homepage, Documentation, Repository, Issues, Changelog)
  - Expanded keywords to 18 items matching descriptions.md

## [1.2.4] - 2026-03-10

### Added
- **GitHub Actions workflow** for automated documentation deployment
  - `.github/workflows/deploy-docs.yml` for deploying to GitHub Pages
  - Triggers on push to main branch and manual workflow_dispatch
  - Builds with strict mode to fail on warnings
  - Deploys to https://pointmatic.github.io/project-guides/

## [1.2.3] - 2026-03-10

### Added
- **Comprehensive documentation pages** in `docs/site/`
  - Getting Started: installation.md, quick-start.md, configuration.md
  - User Guide: commands.md, workflow.md, overrides.md
  - Developer Guide: contributing.md, development.md, testing.md
  - About: license.md, changelog.md
- All pages include cross-references and internal links
- Documentation verified with `mkdocs build --strict`

## [1.2.2] - 2026-03-10

### Added
- **Custom branded landing page** at `docs/site/index.html`
  - Dark theme with teal accent colors
  - Hero section with tagline and banner image
  - Friendly Brief Description explaining HITLoop workflow
  - Quick Start section with 7-step workflow
  - 15 Feature Cards organized into 3 categories (Core, Operational, Philosophy)
  - Responsive design with navigation and footer

## [1.2.1] - 2026-03-10

### Added
- **MkDocs documentation infrastructure**
  - `mkdocs.yml` configuration with Material theme
  - Dark/light mode toggle with teal accent
  - Navigation structure for all documentation sections
  - Markdown extensions (admonition, superfences, highlight, etc.)
  - Plugins: search, git-revision-date-localized
  - `docs/site/.gitignore` for MkDocs cache
  - Updated root `.gitignore` to ignore `/site/` build output
  - Added `[docs]` optional dependency group in pyproject.toml

## [1.2.0] - 2026-03-10

### Added
- **Canonical project descriptions** in `docs/specs/descriptions.md`
  - Project name, taglines (short and long), one-liner
  - Friendly Brief Description explaining HITLoop workflow
  - Two-clause Technical Description
  - Benefits list (10 items)
  - Technical Description (3 paragraphs)
  - Keywords (18 items including HITLoop)
  - Quick Start section (7 essential steps)
  - Feature Cards (15 cards in 3 categories)
  - Usage Notes mapping descriptions to consumer files

### Changed
- **Updated README.md** with canonical descriptions
  - Line 8: Two-clause Technical Description
  - Line 12: Friendly Brief Description (first sentence)
- **Updated pyproject.toml**
  - Description field: Long Tagline
- **Updated docs/specs/features.md**
  - Line 11: Two-clause Technical Description
- **Enhanced project-guide.md template**
  - Added "How to Use This Guide" section
  - Clarified "proceed" language for step-by-step workflow

## [1.1.3] - 2026-03-09

### Added
- **GitHub repository setup section** in `production-mode.md` guide
  - Branch protection rules with UI-matching checklist format
  - Security settings: Dependency graph, Dependabot alerts, security updates, grouped updates
  - GitHub Actions permissions guidance (Read-only by default)
  - Uses `default` branch for flexibility (works with `main` or `master`)

### Changed
- **Updated `project-guide.md` prerequisites**
  - Clarified developer must provide OR LLM must ask for requirements
  - Documented that project idea is often in `docs/specs/concept.md`
- **Updated `templates/guides/README.md`**
  - Added production mode workflow to developer guide list
  - Clarified LLMs may reference developer guides for step-by-step instructions

## [1.1.2] - 2026-03-09

### Changed
- **Modernized Git commands** in `production-mode.md` guide template
  - Updated `git checkout` to `git switch` for switching branches
  - Updated `git checkout -b` to `git switch -c` for creating branches
  - Updated `git branch -d` to `git branch --delete` for clarity
  - Updated `git branch -D` to `git branch --delete --force` for explicit force deletion
  - All workflow examples, quick references, and troubleshooting sections updated
- **Refactored test suite** to eliminate version number scatter
  - Tests now use `__version__` import instead of hardcoded version strings
  - Makes tests self-maintaining across version bumps
  - Only `version.py` needs updating for future releases

## [1.1.0] - 2026-03-03

### Added
- **`purge` command** to remove all project-guides files from a project
  - `--force` flag to skip confirmation prompt
  - Removes `.project-guides.yml` and guides directory
  - Handles missing files gracefully
  - Comprehensive error handling
- 5 new tests for purge command (total: 53 tests)

### Changed
- Updated README with purge command documentation
- Command count increased from 6 to 7

## [1.0.0] - 2026-03-03

### Added
- First stable release! 🎉
- Production-ready with 48 tests and 82% coverage
- Complete documentation and guides
- GitHub Actions CI/CD workflows
- Automated PyPI publishing on release

### Changed
- Development status updated to Production/Stable
- All features complete and tested

## [0.15.0] - 2026-03-03

### Added
- Comprehensive README with badges, installation instructions, and full command reference
- Quick start guide with 4-step workflow
- Troubleshooting section with common issues and solutions
- Contributing guidelines and development setup instructions
- Support links for issues, discussions, and documentation

### Changed
- Enhanced documentation throughout

## [0.14.0] - 2026-03-03

### Added
- Code quality tools: ruff linter and mypy type checker
- Comprehensive linting rules (E, W, F, I, N, UP, B, C4, SIM)
- Type hints throughout codebase
- `types-PyYAML` for type stubs
- GitHub Actions workflows (ci.yml, publish.yml, test.yml)
- Dependabot configuration for automated dependency updates
- GitHub Sponsors funding configuration placeholder
- Open Source Sustainability section in best-practices-guide.md

### Changed
- All code passes ruff and mypy checks with zero errors
- Line length configured to 100 characters

## [0.13.0] - 2026-03-03

### Added
- Integration tests for end-to-end workflows
- Test for full init → override → update workflow
- Test for version upgrade scenarios
- Test for force update with backups
- Test for multiple projects in isolation
- Test for dry-run mode
- Test for specific guide updates

### Changed
- Test coverage increased to 82% (48 tests total)

## [0.12.0] - 2026-03-03

### Added
- Colored CLI output using `click.secho()`
- Explicit exit codes for different error types:
  - 0 for success
  - 1 for general errors
  - 2 for file I/O errors
  - 3 for configuration errors
- Formatted tables with proper alignment in status output

### Changed
- All CLI commands now use colored output for better UX
- Error messages are more visually distinct

## [0.11.0] - 2026-03-03

### Added
- Custom exception classes for structured error handling:
  - `ProjectGuidesError` - Base exception
  - `ConfigError` - Configuration-related errors
  - `SyncError` - Sync operation failures
  - `GuideNotFoundError` - Missing guide templates
- Helpful error messages with actionable suggestions
- Error handling for missing config files
- Error handling for invalid YAML
- Error handling for permission errors
- Error handling for invalid guide names

### Changed
- All modules updated to use custom exceptions
- CLI commands catch and format errors appropriately

## [0.10.0] - 2026-03-03

### Added
- `overrides` command to list all overridden guides
- Display override reason, version, and last updated date

## [0.9.0] - 2026-03-03

### Added
- `override` command to mark guides as customized
- `unoverride` command to remove override status
- Override tracking in configuration with reason and metadata

### Changed
- Update command now skips overridden guides by default
- Force flag creates backups when updating overridden guides

## [0.8.0] - 2026-03-03

### Added
- `update` command to sync guides to latest version
- `--guides` flag to update specific guides only
- `--force` flag to update even overridden guides (with backups)
- `--dry-run` flag to preview changes without applying

## [0.7.0] - 2026-03-03

### Added
- `status` command to show guide installation status
- Display current vs. installed version
- Show which guides are current, outdated, or overridden
- Color-coded status indicators

## [0.6.0] - 2026-03-03

### Added
- `sync_guides()` orchestration function
- Override checking during sync
- Version comparison logic
- Dry-run mode support
- Force update with automatic backups

### Changed
- Sync module now handles complex update scenarios

## [0.5.0] - 2026-03-03

### Added
- `backup_guide()` function with timestamp-based naming
- `compare_versions()` function using `packaging.version`
- Version comparison for update detection

## [0.4.0] - 2026-03-03

### Added
- `copy_guide()` function to copy templates to target directory
- Force flag to overwrite existing files
- Subdirectory support for developer guides
- Permission error handling

## [0.3.0] - 2026-03-03

### Added
- Template bundling as package data
- `get_template_path()` function using `importlib.resources`
- `get_all_guide_names()` function to list available guides
- Support for developer subdirectory guides

## [0.2.0] - 2026-03-03

### Added
- Configuration model with dataclasses
- `Config.load()` and `Config.save()` methods
- YAML serialization/deserialization
- Override tracking in configuration
- `GuideOverride` dataclass for metadata

## [0.1.0] - 2026-03-03

### Added
- Initial package structure with Hatchling
- Basic CLI framework with Click
- `init` command to initialize project guides
- `--target-dir` and `--force` flags
- Apache 2.0 license
- Core guide templates:
  - project-guide.md
  - best-practices-guide.md
  - debug-guide.md
  - documentation-setup-guide.md
  - developer/codecov-setup-guide.md
  - developer/github-actions-guide.md

[Unreleased]: https://github.com/pointmatic/project-guides/compare/v1.5.1...HEAD
[1.5.1]: https://github.com/pointmatic/project-guides/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/pointmatic/project-guides/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/pointmatic/project-guides/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/pointmatic/project-guides/compare/v1.3.1...v1.4.0
[1.3.1]: https://github.com/pointmatic/project-guides/compare/v1.3.0...v1.3.1
[1.1.3]: https://github.com/pointmatic/project-guides/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/pointmatic/project-guides/compare/v1.1.0...v1.1.2
[1.1.0]: https://github.com/pointmatic/project-guides/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/pointmatic/project-guides/compare/v0.15.0...v1.0.0
[0.15.0]: https://github.com/pointmatic/project-guides/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/pointmatic/project-guides/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/pointmatic/project-guides/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/pointmatic/project-guides/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/pointmatic/project-guides/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/pointmatic/project-guides/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/pointmatic/project-guides/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/pointmatic/project-guides/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/pointmatic/project-guides/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/pointmatic/project-guides/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/pointmatic/project-guides/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/pointmatic/project-guides/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/pointmatic/project-guides/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pointmatic/project-guides/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pointmatic/project-guides/releases/tag/v0.1.0
