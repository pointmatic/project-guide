# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
