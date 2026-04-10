# stories.md — project-guide (Python)

This document breaks the `project-guide` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Stories with code changes include a version number (e.g., v0.1.0). Stories with only documentation or polish changes omit the version number. The version follows semantic versioning and is bumped per story. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

---

## Phase I: Rename and Publish Package

Rename the package from `project-guides` to `project-guide` (singular). The goals are: reserve the PyPI name immediately with a minimal publish, then progressively clean up the codebase over subsequent stories. The old `project-guides` CLI entry point is kept alive through Story I.c to avoid breaking existing users mid-rename.

### Story I.a: v1.4.0 Reserve PyPI Name [Done]

Publish the package under the new name `project-guide` on PyPI. This is the minimal change needed to secure the name. The old `project-guides` CLI command continues to work — no regressions for existing users.

- [x] Update `pyproject.toml`
  - [x] Change `name` from `"project-guides"` to `"project-guide"`
  - [x] Add `project-guide = "project_guides.cli:main"` entry point alongside existing `project-guides`
  - [x] Bump version to `1.4.0`
  - [ ] Update description if needed
- [x] Update `project_guides/version.py` to `"1.4.0"`
- [x] Update `CHANGELOG.md` with v1.4.0 entry
- [x] Publish to PyPI via GitHub Actions
  - [x] Commit and push changes
  - [x] Create and publish a GitHub Release tagged `v1.4.0`
  - [x] Confirm the `Publish to PyPI` Actions workflow passes
- [x] Verify: `pip install project-guide` installs successfully
- [x] Verify: both `project-guide --help` and `project-guides --help` work

### Story I.b: v1.4.1 Rename Config File [Done]

Rename `.project-guides.yml` to `.project-guide.yml` everywhere: the template, all code references, and all documentation. Add a one-time migration so existing users' config files are renamed automatically with a printed notice.

- [x] Rename template file
  - [x] `project_guides/templates/.project-guides.yml.template` → `.project-guide.yml.template`
- [x] Update `config.py`
  - [x] Change the config filename constant from `.project-guides.yml` to `.project-guide.yml`
- [x] Update `cli.py`
  - [x] Add migration logic in the `main` group or a shared helper: if `.project-guides.yml` exists and `.project-guide.yml` does not, rename it and print: `"Renamed .project-guides.yml → .project-guide.yml"`
  - [x] Update all string references to the old config filename
- [x] Update `sync.py` references if any
- [x] Update `tests/` — all fixtures and assertions using the old filename
- [x] Update `README.md` and all guide docs referencing `.project-guides.yml`
- [x] Bump `version.py` and `pyproject.toml` to `1.4.1`
- [x] Update `CHANGELOG.md`
- [x] Verify: existing project with `.project-guides.yml` runs any command and gets renamed automatically
- [x] Verify: new `project-guide init` creates `.project-guide.yml`

### Story I.c: v1.5.0 Complete CLI Rename [In Progress]

Remove the old `project-guides` CLI entry point. Update all user-facing strings, documentation, and guide content to use `project-guide`. This is the breaking change — old users must reinstall.

- [x] Update `pyproject.toml`
  - [x] Remove `project-guides = "project_guides.cli:main"` entry point
  - [x] Bump version to `1.5.0`
- [x] Update `project_guides/version.py` to `"1.5.0"`
- [x] Update all CLI help strings in `cli.py` (e.g., `"Run project-guides init"` → `"Run project-guide init"`)
- [x] Update `README.md` — all command examples
- [x] Update all files under `project_guards/templates/guides/` that reference `project-guides`
  - [x] `project-guide.md` (How to Use section)
  - [x] Any other guide referencing the CLI command
- [x] Update `CHANGELOG.md`
- [x] Build and publish to PyPI
- [x] Verify: `project-guides --help` is no longer available after reinstall
- [x] Verify: `project-guide --help` works and shows correct command name

### Story I.d: v1.5.1 Rename Python Module Directory [In Progress]

Rename the Python package directory from `project_guides/` to `project_guide/` so the module name matches the package and CLI command. This is a purely internal refactor with no user-visible behavior change.

- [x] Rename directory: `project_guides/` → `project_guide/`
- [x] Update `pyproject.toml`
  - [x] `packages = ["project_guides"]` → `["project_guide"]`
  - [x] `project-guide = "project_guides.cli:main"` → `"project_guide.cli:main"`
- [x] Update all internal imports across `project_guide/*.py`
  - [x] `cli.py` — `from project_guides.xxx import`
  - [x] `sync.py` — `from project_guides.xxx import` and `importlib.resources.files("project_guides.templates...")` strings
  - [x] `config.py`, `exceptions.py`, `__init__.py`, `__main__.py`
- [x] Update all test imports: `from project_guides.xxx import` → `from project_guide.xxx import`
- [x] Update `.github/workflows/`
  - [x] `--cov=project_guides` → `--cov=project_guide` in `ci.yml`, `test.yml`, `publish.yml`
  - [x] `mypy project_guides/` → `mypy project_guide/` in `publish.yml`
- [x] Bump `version.py` and `pyproject.toml` to `1.5.1`
- [x] Update `CHANGELOG.md`
- [x] Run full test suite — all 59 tests must pass
- [x] Verify: `pyve run project-guide status` works correctly after reinstall

### Story I.e: GitHub Repo Rename and PyPI Archive [Planned]

Admin tasks with no code changes. No version bump.

- [x] Rename GitHub repo from `project-guides` to `project-guide`
  - [x] Settings → Repository name → `project-guide`
  - [x] GitHub automatically redirects old URLs
- [x] Update all hardcoded GitHub URLs in the codebase and docs
  - [x] `README.md` badges and links
  - [x] `pyproject.toml` `[project.urls]` section
  - [x] Any guide files referencing the repo URL
- [x] Archive old `project-guides` PyPI package
  - [x] Publish a final `project-guides` release with updated README/description: "This package has moved to `project-guide`. Please update your dependencies."
  - [x] Go to PyPI → `project-guides` → Settings → Archive project
- [x] Update `mkdocs.yml` site URL if applicable
- [x] Verify: all links resolve correctly

### Story I.f: Update README, landing page, and descriptions [Done]
- [x] Update `docs/specs/descriptions.md` to reflect new package name and concepts (guides -> guide/prompts)
- [x] Update `README.md` based on `docs/specs/description.md`
- [x] Update landing page based on `docs/specs/description.md`
- [x] Add Codecov badge to `README.md` and set minimum coverage to 75%

### Story I.g: v1.5.2 Increase Test Coverage to 85% [In Progress]

Expand test coverage from 79% to 85%+ by filling gaps in `cli.py` (currently 72%, 84 missed statements). Focus on error paths, edge cases, and untested command flows. Raise the `--cov-fail-under` threshold to 85%.

**cli.py — config migration (lines 37–38):**
- [x] Test `_migrate_config_if_needed`: old `.project-guides.yml` exists, `.project-guide.yml` does not → renames and prints notice

**cli.py — `init` error paths (lines 79–84):**
- [x] Test `init` when a guide file already exists without `--force` (FileExistsError path — `⚠ Skipped` message)
- [x] Test `init` when `copy_guide` raises `SyncError` (e.g., permission denied) → exits with code 2

**cli.py — `status` edge cases (lines 115–117, 147–148, 157–161, 178):**
- [x] Test `status` with corrupt/invalid config file → `ConfigError`, exits with code 3
- [x] Test `status` with a missing guide file on disk → shows `✗ (missing)` and missing count
- [x] Test `status` with a locally modified guide (content differs from template) → shows `⚠ (modified)`
- [x] Test `status` summary includes missing count when guides are missing

**cli.py — `update` error paths (lines 198–203, 208–210, 220–226, 235–237):**
- [x] Test `update` with no config file → error message, exits with code 1
- [x] Test `update` with corrupt config → `ConfigError`, exits with code 3
- [x] Test `update --guides fake-guide.md` → error with available guides list, exits with code 1
- [x] Test `update` when `sync_guides` raises `SyncError` → exits with code 2

**cli.py — `update` modified-file prompts (lines 245–259, 269–282):**
- [x] Test `update` with locally modified file, user confirms → backup created, file updated, shows "Updated (approved by user)"
- [x] Test `update` with locally modified file, user declines → shows "Skipped (user declined)"
- [x] Test `update --dry-run` with locally modified file → shows "Modified (would prompt)" without changing files

**cli.py — `update` summary variations (lines 310–334):**
- [x] Test `update --dry-run` summary with missing files → shows "Would create"
- [x] Test `update` when all guides declined → "No guides updated (all modifications declined)"
- [x] Test `update` when all guides overridden (no `--force`) → "All guides are overridden. Use --force to update anyway."

**cli.py — `override`/`unoverride` missing config (lines 346–358, 387–399):**
- [x] Test `override` with no config file → error, exits with code 1
- [x] Test `override` with corrupt config → exits with code 3
- [x] Test `unoverride` with no config file → error, exits with code 1
- [x] Test `unoverride` with corrupt config → exits with code 3

**cli.py — `overrides` error path (lines 422–424):**
- [x] Test `overrides` with corrupt config → exits with code 3

**cli.py — `purge` edge cases (lines 478–491):**
- [x] Test `purge` when guides directory does not exist → shows "not found (skipped)"
- [x] Test `purge` when config file does not exist after dir removal → shows "not found (skipped)"

**Raise coverage threshold:**
- [x] Update `pyproject.toml`: change `--cov-fail-under=75` to `--cov-fail-under=85`
- [x] Verify: full test suite passes with 85%+ coverage
- [x] Bump `version.py` and `pyproject.toml` to `1.5.2`
- [x] Update `CHANGELOG.md`

**Codecov badge**
- [x] Add codecov badge to README.md

---

## Phase J: Mode-Driven Template System (v2.0.0)

Replace the static file-sync architecture with a dynamic, mode-driven template system using Jinja2. The LLM reads a single rendered `go-project-guide.md` that is regenerated each time the developer changes modes via `project-guide mode <name>`. See `phase-j-modes-plan.md` for full architectural details.

**Implementation strategy:** Spike first with `default` + `plan_concept` modes only, validating the full rendering pipeline end-to-end before adding remaining modes.

Foundation modes:
- `default`: Determine which mode to use (generated on init)
- `plan_concept`: Generate a high-level concept (problem and solution space)
- `plan_features`: Generate feature requirements
- `plan_tech_spec`: Generate a technical specification
- `plan_stories`: Generate user stories
- `plan_phase`: Generate a feature phase (mini-concept + features + tech details)
- `code_velocity`: Generate code with velocity
- `code_test_first`: Generate code with a test-first approach
- `debug`: Debug code with a test-first approach
- `document_brand`: Develop branding for the project
- `document_landing`: Generate a GitHub landing page and MkDocs documentation

Future modes (deferred): `code_production`, `audit_security`, `audit_architecture`, `audit_performance`, `audit_best_practices`, `audit_modularity`, `audit_patterns`, `refactor_plan`, `refactor_document`.

Migration: No automatic migration of old `docs/guides/` content. Users can apply a future `refactor` mode to migrate.

### Story J.a: v2.0.0 End-to-End Spike — Metadata, Rendering, and Mode Command [Done]

Wire the full stack end-to-end with two modes (`default`, `plan_concept`). This validates metadata parsing, Jinja2 rendering, the `mode` command, config schema v2.0, and the new directory structure. No remaining modes, no sync/update changes — just prove the critical path works.

- [x] Add `jinja2>=3.1` to runtime dependencies in `pyproject.toml`
- [x] Add `MetadataError` and `RenderError` to `exceptions.py`
- [x] Create `metadata.py`
  - [x] Load and validate `project-guide-metadata.yml`
  - [x] Resolve `common` block variables (two-pass: resolve `{{var}}` references in all fields against `common` values)
  - [x] Look up a mode by name, returning its `ModeDefinition` (template path, sequence/cycle, next_mode, artifacts, files_exist)
  - [x] List all available mode names
- [x] Create `render.py`
  - [x] Configure Jinja2 environment with the project's template directory as the loader path
  - [x] Render `go-project-guide.md` by: loading the entry point template, injecting the current mode's template via `{% include %}`, passing metadata variables as Jinja2 context
  - [x] Handle the `_header-sequence.md` / `_header-cycle.md` inclusion within mode templates
  - [x] Write rendered output to the target path
- [x] Update `config.py`
  - [x] Add `current_mode: str = "default"` to `Config` dataclass
  - [x] Bump config schema version to `"2.0"`
  - [x] Migrate v1.0 configs on load: add `current_mode: "default"` if missing
  - [x] Change default `target_dir` to `"docs/project-guide"` for new projects
- [x] Update `init` command in `cli.py`
  - [x] Create new directory structure: `docs/project-guide/templates/modes/`, `docs/project-guide/templates/artifacts/`
  - [x] Copy `project-guide-metadata.yml`, header partials, `default-mode.md`, and `plan-concept-mode.md` + its artifact template
  - [x] Render `go-project-guide.md` in `default` mode
  - [x] Create `.project-guide.yml` with `current_mode: "default"` and `target_dir: "docs/project-guide"`
  - [x] Add `go-project-guide.md` to `.gitignore` if not already present
- [x] Add `mode` command to `cli.py`
  - [x] `project-guide mode <name>`: validate mode name against metadata, update `current_mode` in config, render `go-project-guide.md`, print confirmation
  - [x] `project-guide mode` (no arg): print current mode and list available modes
  - [x] Error on invalid mode name with list of valid options
- [x] Convert template syntax: replace `{{template "path"}}` in mode templates with Jinja2 `{% include "path" %}`
- [x] Finalize `default-mode.md` and `plan-concept-mode.md` templates (already hand-drafted, adjust as needed during spike)
- [x] Write tests for `metadata.py`, `render.py`, `mode` command, updated `init`, and config v2.0 migration
- [x] Bump `version.py` and `pyproject.toml` to `2.0.0`
- [x] Update `CHANGELOG.md`
- [x] Verify: `project-guide init` creates new directory structure and renders `go-project-guide.md`
- [x] Verify: `project-guide mode plan_concept` switches mode and re-renders `go-project-guide.md` with plan_concept content
- [x] Verify: `project-guide mode` (no arg) lists available modes with current mode highlighted
- [x] Verify: rendered `go-project-guide.md` includes `_header-common.md` + `_header-sequence.md` + plan-concept steps
- [x] Verify: old v1.0 config loads without error (migration adds `current_mode: "default"`)
- [x] Verify: artifact templates (`templates/artifacts/concept.md`) are copied but NOT Jinja2-rendered

### Story J.b: v2.0.1 Update Status Command for Modes [Done]

Update `status` to reflect the mode system. Show current mode, mode description, and prerequisite file status.

- [x] Update `status` command in `cli.py`
  - [x] Display current mode name and description (from metadata)
  - [x] Display `go-project-guide.md` path
  - [x] Show prerequisite status for current mode (`files_exist` entries: present/missing)
  - [x] Continue to show guide sync status (version, overrides) for template files
- [x] Update `test_cli.py` for updated `status` output
- [x] Bump `version.py` and `pyproject.toml` to `2.0.1`
- [x] Update `CHANGELOG.md`
- [x] Verify: `project-guide status` shows mode name, description, and prerequisite status

### Story J.c: v2.0.2 Update Sync/Update for New Directory Structure [Done]

Adapt the sync/override system to operate on the new template directory structure. After any update that touches mode templates or header partials, re-render `go-project-guide.md`.

- [x] Update guide discovery in `sync.py` (`get_all_guide_names()`) to scan `templates/modes/*.md`, `templates/artifacts/*.md`, `project-guide-metadata.yml`
  - [x] Remove old `guides/` directory references
- [x] Update `update` command: after syncing template files, re-render `go-project-guide.md` for the current mode
- [x] Override/unoverride work on template-relative paths (e.g., `override templates/modes/plan-concept-mode.md "Custom concept workflow"`)
- [x] Update `purge` to remove `docs/project-guide/` instead of `docs/guides/`
- [x] Write tests for updated sync discovery, update-then-render flow, and override on new paths
- [x] Bump `version.py` and `pyproject.toml` to `2.0.2`
- [x] Update `CHANGELOG.md`
- [x] Verify: `project-guide update` syncs new template files and re-renders `go-project-guide.md`
- [x] Verify: `project-guide override templates/modes/plan-concept-mode.md "reason"` works correctly

### Story J.d: v2.0.3 Add Planning Mode Templates [Done]

Add the remaining planning mode templates: `plan_features`, `plan_tech_spec`, `plan_stories`, `plan_phase`. Each must include the appropriate header partial and be self-contained.

- [x] Finalize `plan-features-mode.md` — migrate content from old `go-project-guide.md` Step 1 (Features Document)
- [x] Finalize `plan-tech-spec-mode.md` — migrate content from old Step 2 (Technical Specification)
- [x] Finalize `plan-stories-mode.md` — migrate content from old Step 3 (Stories Document)
- [x] Finalize `plan-phase-mode.md` — combined concept/features/tech-spec for adding a new phase to an existing project
- [x] Create artifact templates for each mode where applicable (`features.md`, `tech-spec.md`, `stories.md`)
- [x] Each mode template includes `{% include "_header-sequence.md" %}` with `next_mode` populated
- [x] Update `init` to copy all planning templates
- [x] Verify: `project-guide mode plan_features` renders correctly and includes next_mode prompt to `plan_tech_spec`
- [x] Verify: each planning mode's rendered output is self-contained for an LLM to follow
- [x] Bump `version.py` and `pyproject.toml` to `2.0.3`
- [x] Update `CHANGELOG.md`

### Story J.e: v2.0.4 Add Code and Debug Mode Templates [Done]

Add `code_velocity`, `code_test_first`, and `debug` mode templates. Migrate relevant content from old `go-project-guide.md` Step 4 and `best-practices-guide.md`.

- [x] Finalize `code-velocity-mode.md` — velocity coding workflow: commit to main, version-per-story, HITLoop cycle, checklist approach
- [x] Finalize `code-test-first-mode.md` — TDD workflow: failing test first, red-green-refactor
- [x] Finalize `debug-mode.md` — reproduce, isolate, failing test, fix, verify
- [x] Each mode template includes `{% include "_header-cycle.md" %}`
- [x] Migrate relevant best practices from `best-practices-guide.md` into the appropriate mode templates
- [x] Update `init` to copy code and debug templates
- [x] Verify: `project-guide mode code_velocity` renders correctly with cycle header
- [x] Verify: `project-guide mode debug` renders correctly
- [x] Bump `version.py` and `pyproject.toml` to `2.0.4`
- [x] Update `CHANGELOG.md`

### Story J.f: v2.0.5 Add Document Mode Templates [Done]

Add `document_brand` and `document_landing` mode templates.

- [x] Finalize `document-brand-mode.md` — adapted from old `descriptions-guide.md`, generate `docs/specs/brand-descriptions.md`
- [x] Finalize `document-landing-mode.md` — generate GitHub landing page (`docs/site/index.html`) and MkDocs documentation
- [x] Each mode template includes `{% include "_header-sequence.md" %}`
- [x] Create artifact templates where applicable
- [x] Update `init` to copy document templates
- [x] Verify: `project-guide mode document_brand` renders correctly
- [x] Verify: `project-guide mode document_landing` renders correctly
- [x] Bump `version.py` and `pyproject.toml` to `2.0.5`
- [x] Update `CHANGELOG.md`

### Story J.g: v2.0.6 Migrate Monolithic Entry Point Content [Done]

The old `go-project-guide.md` entry point template contains Steps 0-4 as a monolithic document. Now that all mode templates exist, reduce the entry point to a thin shell that includes `_header-common.md` and the active mode template. Move Step 0 (Project Setup) content into `_header-common.md` or `default-mode.md`.

- [x] Slim down `go-project-guide.md` entry point template to: common header + mode inclusion only
- [x] Move Step 0 content (License, Copyright Headers, Badges, CHANGELOG) into `default-mode.md`
- [x] Distribute prerequisites from old default-mode.md into planning modes (concept, features, tech-spec)
- [x] Rewrite `default-mode.md` as full lifecycle overview for new users
- [x] Add `default` mode to `project-guide-metadata.yml`
- [x] Remove old static guide files that are now fully absorbed into mode templates (`best-practices-guide.md`)
- [x] Verify: all 11 modes render complete, self-contained output from the slimmed entry point
- [x] Verify: no content was lost in the migration
- [x] Bump `version.py` and `pyproject.toml` to `2.0.6`
- [x] Update `CHANGELOG.md`

### Story J.h: v2.0.7 Test Coverage and Documentation [Done]

Ensure test coverage remains at 85%+ after all Phase J changes. Update README and user-facing documentation to reflect the mode system.

- [x] Review test coverage for all new modules (`metadata.py`, `render.py`) and updated modules (`cli.py`, `config.py`, `sync.py`)
- [x] Add missing tests to maintain 85%+ coverage (112 tests, 92% coverage)
- [x] Update `README.md` with mode system usage examples (`project-guide mode plan_concept`, etc.)
- [x] Final pass: run full test suite, linting, type checking
- [x] Bump `version.py` and `pyproject.toml` to `2.0.7`
- [x] Update `CHANGELOG.md`

### Story J.i: v2.0.8 Project Setup Mode [Done]

Extract project scaffolding (LICENSE, headers, manifest, README, CHANGELOG, .gitignore) from `default-mode.md` into a dedicated `project_setup` sequence mode. Slim `default` to pure navigation.

- [x] Create `project-setup-mode.md` with step-by-step setup instructions and approval checklist
- [x] Add `project_setup` mode to `project-guide-metadata.yml` (between `default` and `plan_concept`)
- [x] Slim `default-mode.md` to project lifecycle overview with mode table -- no setup content
- [x] Update mode flow: `default` -> `project_setup` -> `plan_concept`
- [x] Verify: `project-guide mode project_setup` renders correctly with setup steps
- [x] Verify: `default` mode no longer contains setup instructions
- [x] Bump `version.py` and `pyproject.toml` to `2.0.8`
- [x] Update `CHANGELOG.md`

### Story J.j: v2.0.9 Artifact Refactoring Modes [Done]

Implement `refactor_plan` and `refactor_document` cycle modes for migrating existing documents into the v2.x artifact template format. Also add a v1.x → v2.x migration notice to the `status` command.

**Mode templates:**
- [x] Create `refactor-plan-mode.md` — cycle mode for refactoring planning artifacts (`concept.md`, `features.md`, `tech-spec.md`)
- [x] Create `refactor-document-mode.md` — cycle mode for refactoring documentation artifacts (`brand-descriptions.md`, landing page `index.html`, MkDocs files)
- [x] Each mode template includes `{% include "modes/_header-cycle.md" %}`
- [x] Add both modes to `project-guide-metadata.yml`

**Cycle steps (both modes follow this pattern for each document):**
1. Enumerate the documents to refactor
2. For each document:
   - [x] Move existing document to `<doc_name>_old.md`
   - [x] Read old document as the primary source of information
   - [x] If any necessary information is missing from the old document, ask the developer
   - [x] Generate new document using the appropriate artifact template format
   - [x] Append any leftover information to the end as a `## Legacy Content` section
   - [x] Present the completed document to the developer for approval; iterate as needed

**`refactor_plan` targets:**
- `docs/specs/concept.md` → artifact template format from `templates/artifacts/concept.md`
- `docs/specs/features.md` → artifact template format from `templates/artifacts/features.md`
- `docs/specs/tech-spec.md` → artifact template format from `templates/artifacts/tech-spec.md`

**`refactor_document` targets:**
- `docs/specs/descriptions.md` → `docs/specs/brand-descriptions.md` (artifact template format)
- `docs/site/index.html` → updated with `{{ web_root }}` structure from `document-landing-mode.md`
- MkDocs configuration and pages

**v1.x → v2.x migration notice in `status`:**
- [x] Detect v1.x config (`version: "1.0"` or `target_dir: "docs/guides"`) in the `status` command
- [x] Display migration notice:
  - `docs/guides/` directory is deprecated; new features target `docs/project-guide/` only
  - Run `project-guide init` to install the v2.x template system alongside existing guides
  - Use `refactor_plan` mode to migrate `concept.md`, `features.md`, `tech-spec.md` to the new artifact format
  - Use `refactor_document` mode to migrate `descriptions.md`, landing page, and MkDocs files

**Tests:**
- [x] Write tests for `refactor_plan` and `refactor_document` mode rendering
- [x] Write test for v1.x migration notice in `status` output
- [x] Bump `version.py` and `pyproject.toml` to `2.0.9`
- [x] Update `CHANGELOG.md`

### Story J.k: v2.0.10 Fix UX and Config Problems [Done]

Fix three UX/config issues identified in `docs/specs/ux-problems.md`. No backward compatibility needed — `purge` + `init` is the recovery path.

**Fix 1 — Default mode on init:**

`init` hardcodes `current_mode="plan_concept"` and renders in `plan_concept` mode. It should use `default`.

- [x] Update `cli.py` `init`: change `current_mode="plan_concept"` to `"default"` and render in `default` mode
- [x] Update affected tests

**Fix 2 — Remove template paths from `files_exist`:**

`files_exist` entries include `{{mode_templates_path}}/...` which resolves to a repo-internal path that never exists in an installed project. Template presence is infrastructure, not a user prerequisite — if a template is missing, the render will fail with a clear Jinja2 error.

- [x] Remove all `{{mode_templates_path}}` entries from `files_exist` in the metadata file, keeping only `{{spec_artifacts_path}}` entries (user-created content)
- [x] Add actionable error guidance: when a Jinja2 render fails due to a missing template, prompt the developer to run `project-guide status` and `project-guide update`
- [x] Add a parametrized test that iterates every mode in the metadata and asserts the render pipeline succeeds — proves a fresh install works and catches regressions when modes are added
- [x] Update affected tests

**Fix 3 — Rename metadata file to `.metadata.yml` and add to config:**

`project-guide-metadata.yml` is redundant (already inside `project-guide/`) and is infrastructure, not user content. Rename to `.metadata.yml` (hidden, minimal). Store the filename in `.project-guide.yml` so the CLI never hardcodes it.

- [x] Add `metadata_file: str = ".metadata.yml"` to `Config` dataclass in `config.py`
- [x] Update `cli.py`: replace all 4 hardcoded `"project-guide-metadata.yml"` with `Path(config.target_dir) / config.metadata_file`; in `init`, set `metadata_file=".metadata.yml"` when creating the config
- [x] Rename template file: `project_guide/templates/project-guide/project-guide-metadata.yml` → `project_guide/templates/project-guide/.metadata.yml`
- [x] Update `metadata.py`: docstrings referencing the old filename
- [x] Update `sync.py` `get_all_guide_names()`: `rglob("*.yml")` does not match dotfiles — add `".*.yml"` pattern or explicitly include `.metadata.yml`
- [x] Update all test references (`test_metadata.py`, `test_cli.py`, `test_integration.py`)
- [x] Update `CHANGELOG.md`

**Wrap-up:**
- [x] Bump `version.py` and `pyproject.toml` to `2.0.10`
- [x] Run full test suite — 129 tests pass, 92% coverage
- [x] Verify: `project-guide init` creates `.metadata.yml` and starts in `default` mode
- [x] Verify: `.project-guide.yml` contains `metadata_file: .metadata.yml`
- [x] Verify: `project-guide mode plan_phase` shows only spec artifact prerequisites, no template paths
- [x] Verify: `project-guide update` syncs `.metadata.yml` correctly

### Story J.l: v2.0.11 Move Rendered Guide to project-guide Directory [Done]

The rendered `go-project-guide.md` is mode instructions, not a spec artifact. It currently lives in `docs/specs/` because the Jinja2 template source has the same name in `docs/project-guide/`. Fix this by moving the template source into `docs/project-guide/templates/` and rendering the output to `docs/project-guide/go-project-guide.md`.

**Move template source:**
- [x] Move `project_guide/templates/project-guide/go-project-guide.md` → `project_guide/templates/project-guide/templates/go-project-guide.md`
- [x] Update `render.py`: Jinja2 loader simplified to search only `templates/` subdirectory
- [x] Update `cli.py` `init`: render output to `docs/project-guide/go-project-guide.md` instead of `docs/specs/go-project-guide.md`

**Update render output path:**
- [x] All CLI commands (`init`, `mode`, `update`, `status`) now render to `target_dir / go-project-guide.md`
- [x] `target_dir` added as a Jinja2 context variable for templates

**Gitignore and cleanup:**
- [x] `_ensure_gitignore_entry()` now receives `target_dir` — entry is `docs/project-guide/go-project-guide.md`
- [x] `_header-common.md` updated to `Read {{ target_dir }}/go-project-guide.md`

**Tests and wrap-up:**
- [x] Updated `test_cli.py`, `test_render.py`, `test_sync.py` — all output path assertions and fixtures
- [x] Bump `version.py` and `pyproject.toml` to `2.0.11`
- [x] Update `CHANGELOG.md`
- [x] Run full test suite — 129 tests pass, 92% coverage
- [x] Verify: `project-guide init` renders `docs/project-guide/go-project-guide.md`
- [x] Verify: `project-guide mode code_velocity` re-renders in the correct location
- [x] Verify: developer instruction is `Read docs/project-guide/go-project-guide.md`

### Story J.m: v2.0.12 Improve Status Command UX and Rename Guides to Files [Done]

The `status` command outputs 40+ lines dominated by a per-file sync list. On the happy path (everything current), this is noise. Also, "guides" no longer describes what the sync system tracks — rename to "files" throughout.

**Status UX:**
- [x] Refactor `status` command: compact summary by default, per-file list only on problems
- [x] Show `target_dir` in status header
- [x] Show hint: `Run 'project-guide mode' to see available modes.`
- [x] Add `--verbose` / `-v` flag to force full per-file list

**Rename "guides" → "files":**
- [x] `exceptions.py`: `GuideNotFoundError` → `ProjectFileNotFoundError`
- [x] `sync.py`: `get_all_guide_names` → `get_all_file_names`, `copy_guide` → `copy_file`, `backup_guide` → `backup_file`, `apply_guide_update` → `apply_file_update`, `sync_guides` → `sync_files`
- [x] `config.py`: `GuideOverride` → `FileOverride`, `guide_name` → `file_name` parameters
- [x] `cli.py`: `--guides` → `--files` flag, all user-facing strings ("Guide" → "File", "guides" → "files")
- [x] All test files updated

**Wrap-up:**
- [x] Bump `version.py` and `pyproject.toml` to `2.0.12`
- [x] Update `CHANGELOG.md`
- [x] Run full test suite — all tests pass at 85%+ coverage

### Story J.n: v2.0.13 Status UX, Hash-Based Sync, and Rename go.md [Done]

Three related improvements: redesign `status` output with grouped sections, replace version-based sync logic with content hash comparison, and rename `go-project-guide.md` → `go.md`.

**Redesign `status` output — grouped sections with contextual actions:**

```
project-guide v2.0.13 (installed: v2.0.12)

Mode: default — Getting started -- full project lifecycle overview
  Prerequisites: all met
  Run 'project-guide mode' to see available modes.

Guide: docs/project-guide/go.md

Files: 3 current, 28 need updating, 2 missing
  Run 'project-guide update' to sync.
```

- [x] Group output into three sections: Mode, Guide, Files — each with its own contextual action prompt
- [x] Omit `Prerequisites` line when the mode has none
- [x] Show `(installed: vX.X.X)` only when it differs from package version
- [x] Files section is always a summary count; `--verbose` for per-file list
- [x] Action prompts only when relevant (`update` prompt only when files need syncing)
- [x] Update affected tests

**Hash-based sync — replace version comparison with content hash:**

The current logic assumes all files are stale when the package version differs from `installed_version`. In reality, most files don't change between versions. Use the existing `file_matches_template()` hash comparison as the sole source of truth for file freshness.

- [x] Update `status` command: always use `file_matches_template()` to determine file state, remove version-first branching
- [x] Update `sync_files()`: same — hash check determines whether a file needs updating, not version comparison
- [x] `installed_version` remains as a global "last time update ran" data point, shown in the header, not per-file
- [x] Remove per-file version display from `--verbose` output (the version was the global `installed_version` repeated — not meaningful per-file)
- [x] Update affected tests

**Rename `go-project-guide.md` → `go.md`:**

The file lives in `docs/project-guide/` — the directory provides context. The shorter name is easier to type and autocomplete (`@go<tab>`).

- [x] Rename template source: `templates/go-project-guide.md` → `templates/go.md`
- [x] Update `render.py`: `get_template("go.md")`
- [x] Update `cli.py`: all references to `go-project-guide.md` → `go.md` (init, mode, update, status, gitignore)
- [x] Update `_header-common.md`: developer instruction path
- [x] Update all test references
- [x] Update `CHANGELOG.md`

**Wrap-up:**
- [x] Bump `version.py` and `pyproject.toml` to `2.0.13`
- [x] Run full test suite — 129 tests pass, 91% coverage
- [x] Verify: `project-guide init` renders `docs/project-guide/go.md`
- [x] Verify: `project-guide status` shows grouped output with hash-based file state
- [x] Verify: version upgrade with no template changes shows `Files: 33 current`

### Story J.o: v2.0.14 Adjust status output colors []

- [x] Adjust status output colors for interest and readability
- [x] Bump version to 2.0.14

### Story J.p: v2.0.15 Add missing prompt to 'Tell LLM to read go.md' [Done]

- [x] Add prompt to 'Tell your LLM: Read docs/project-guide/go-project-guide.md'
- [x] Bump version to 2.0.15

### Story J.q: v2.0.16 Refactor Planning Docs and Documentation [Done]

- [x] Clarify `refactor_*` modes and their purpose in `.metadata.yml`
- [x] Update `refactor-plan-mode.md` and `refactor-document-mode.md`
- [x] Update concept (`docs/specs/concept.md`)
- [x] Update features (`docs/specs/features.md`)
- [x] Update tech-spec (`docs/specs/tech-spec.md`)
- [x] Update README (`README.md`)
- [x] Update index.html page (`docs/site/index.html`)
- [x] Update MkDocs pages (`docs/site/*.md`)
- [x] Update CHANGELOG (`CHANGELOG.md`)
- [x] Bump version to 2.0.16

### Story J.r: Restructure MkDocs Site Navigation [Done]

No version bump — documentation-only changes.

The Getting Started section had three pages (installation, quick-start, configuration) that overlapped with each other and with the landing page Quick Start section. Restructured to eliminate duplication.

**File moves:**
- [x] `docs/site/getting-started/quick-start.md` → `docs/site/getting-started.md` (top-level, content unchanged)
- [x] `docs/site/getting-started/installation.md` → `docs/site/user-guide/install-options.md`
- [x] `docs/site/getting-started/configuration.md` → `docs/site/user-guide/configuration.md`
- [x] Removed empty `docs/site/getting-started/` directory

**Navigation updates:**
- [x] `mkdocs.yml`: Getting Started is now a single top-level page; Install Options and Configuration moved under User Guide
- [x] `index.html`: Docs nav link updated to `/getting-started/`
- [x] Updated cross-references in 6 files (getting-started.md, install-options.md, commands.md, workflow.md, overrides.md, development.md)

**Other fixes:**
- [x] `git checkout -b` → `git switch -c` in README.md, contributing.md, development.md
- [x] Fixed `.gitignore` entries: removed stale `go-project-guide.md` paths, added `docs/project-guide/go.md` and `docs/project-guide/**/*.bak.*` under `# project-guide` comment
- [x] Added `Tell your LLM: Read docs/project-guide/go.md` prompt to `status` Guide section

### Story J.s: v2.0.17 Modes Doc, Rename project_setup to project_scaffold, Slim Workflow Doc [Done]

User-facing changes that warrant a version bump.

**Add Modes documentation page:**
- [x] Create `docs/site/user-guide/modes.md` documenting all 15 modes with type, prerequisites, artifacts, next mode, description, and command
- [x] Add Mode Flow diagram showing the typical project lifecycle
- [x] Add Modes page to `mkdocs.yml` nav between Commands and Workflow

**Rename `project_setup` → `project_scaffold`:**

The "setup" name was too generic — could mean install dependencies, configure environment, set up CI, etc. The mode specifically scaffolds project files (LICENSE, headers, manifest, README, CHANGELOG, .gitignore), so "scaffold" is more accurate and matches industry conventions.

- [x] Rename template file: `project-setup-mode.md` → `project-scaffold-mode.md`
- [x] Update `.metadata.yml`: `name: project_scaffold`, template path, comment header (`# Scaffold`), description
- [x] Update `next_mode: project_scaffold` in `plan_stories` mode
- [x] Update `default-mode.md`: lifecycle table row, "Scaffold (sequence)" section
- [x] Update `project-scaffold-mode.md`: heading "Project Scaffold Mode", description, fix `next_mode` reference (was hardcoded `plan_concept`, now uses `{{ next_mode }}`)
- [x] Update `docs/site/user-guide/modes.md`: section heading, mode entry, command, mode flow diagram
- [x] Update `docs/specs/concept.md`: 15 modes list
- [x] Update `docs/specs/features.md`: file structure listing, modes table
- [x] Historical references in `CHANGELOG.md` and `stories.md` Story J.i left as-is (describe past work with old name)

**Slim down `workflow.md`:**

The workflow guide was 376 lines and mostly duplicated content from `getting-started.md`, `commands.md`, and `overrides.md`. Reduced to ~85 lines focused on the workflow itself.

- [x] Removed Initial Setup section (duplicates getting-started.md)
- [x] Removed Common Workflows section (duplicates commands and overrides)
- [x] Removed Multi-Project Management section
- [x] Removed Override Management section (duplicates overrides.md)
- [x] Removed Best Practices section (generic, not workflow-specific)
- [x] Removed Troubleshooting section (duplicates other pages)
- [x] Added "The HITLoop Cycle" section (propose → review → approve → execute rhythm)
- [x] Added "When to Switch Modes" table
- [x] Added "Customization and Updates" paragraph linking to overrides.md
- [x] Updated "Next Steps" to link to canonical pages

**Wrap-up:**
- [x] Bump `version.py` and `pyproject.toml` to `2.0.17`
- [x] Update `CHANGELOG.md`
- [x] Run full test suite — 129 tests pass (parametrized mode test confirms `project_scaffold` renders)

---

## Future

### Future Story: Code Production Mode [Deferred]

Implement the `code_production` mode...TBD

### Future Story: Archive Stories Mode [Deferred]

Future mode (deferred): `archive_stories`

Move the `docs/specs/stories.md` file to `docs/specs/.archive/stories.md-vx.x.x.md` where `vx.x.x` is the most recent version set by a story.

Then `plan_phase` mode can create a new `docs/specs/stories.md` file. This requires a minor tweak to the metadata since there is a `file_exists` requirement for the stories file and a `modify` action on that file (as well as some logic changes if we add a `create_or_modify` action type).

### Future Story: Audit Modes [Deferred]

Future modes (deferred): `audit_security`, `audit_architecture`, `audit_performance`, `audit_best_practices`, `audit_modularity`, `audit_patterns`

### Out of Scope for Phase J

- Mode auto-detection from `files_exist` prerequisites (future advanced feature)
- Interactive mode menu (deferred — direct `mode <name>` argument is sufficient for v2.0.0)
- LLM API calls for artifact generation (future — currently the LLM fills in variables conversationally)
- Per-project metadata overrides in `.project-guide.yml` (future — metadata.yml is the single source for now)
- Migration tooling for `docs/guides/` → `docs/project-guide/` (future `refactor` mode)
- Story detection in `status` command (nice-to-have, can be added in a follow-up phase)
- Future modes: `code_production`, `audit_*`, `refactor_*`

