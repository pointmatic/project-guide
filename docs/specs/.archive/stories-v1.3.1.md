# stories.md — project-guides (Python)

This document breaks the `project-guides` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Stories with code changes include a version number (e.g., v0.1.0). Stories with only documentation or polish changes omit the version number. The version follows semantic versioning and is bumped per story. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

---

## Phase A: Foundation

### Story A.a: v0.1.0 Hello World [Done]

Minimal runnable Python package with CLI entry point.

- [x] Create `pyproject.toml` with package metadata
  - [x] Set name: `project-guides`
  - [x] Set version: `0.1.0`
  - [x] Set Python requirement: `>=3.11`
  - [x] Set license: `Apache-2.0`
  - [x] Add console script entry point: `project-guides`
  - [x] Configure hatchling build system
- [x] Create `LICENSE` file (Apache-2.0)
- [x] Create `.gitignore` for Python projects
- [x] Create `project_guides/__init__.py`
  - [x] Import and expose `__version__`
- [x] Create `project_guides/version.py`
  - [x] Define `__version__ = "0.1.0"`
- [x] Create `project_guides/__main__.py`
  - [x] Import and call CLI main function
- [x] Create `project_guides/cli.py`
  - [x] Define basic click group with version option
  - [x] Add placeholder `main()` function
- [x] Create basic `README.md`
  - [x] Add project title and description
  - [x] Add installation instructions
  - [x] Add license badge
- [x] Verify: `python -m project_guides --version` prints `0.1.0`
- [x] Verify: `project-guides --version` works after local install

### Story A.b: v0.2.0 Configuration Model [Done]

Implement configuration data model and YAML I/O.

- [x] Add dependencies to `pyproject.toml`
  - [x] Add `pyyaml ^6.0`
  - [x] Add `packaging ^24.0`
- [x] Create `project_guides/config.py`
  - [x] Define `GuideOverride` dataclass
  - [x] Define `Config` dataclass with defaults
  - [x] Implement `Config.load()` class method
  - [x] Implement `Config.save()` method
  - [x] Implement `Config.is_overridden()` method
  - [x] Implement `Config.add_override()` method
  - [x] Implement `Config.remove_override()` method
- [x] Create `tests/__init__.py`
- [x] Create `tests/test_config.py`
  - [x] Test config creation with defaults
  - [x] Test config save/load round-trip
  - [x] Test override add/remove
  - [x] Test invalid YAML handling
- [x] Verify: All config tests pass

### Story A.c: v0.3.0 Template Bundle Structure [Done]

Set up package data structure for bundled guide templates.

- [x] Create `project_guides/templates/guides/` directory
- [x] Create placeholder guide templates
  - [x] `project_guides/templates/guides/README.md`
  - [x] `project_guides/templates/guides/project-guide.md`
  - [x] `project_guides/templates/guides/best-practices-guide.md`
  - [x] `project_guides/templates/guides/debug-guide.md`
  - [x] `project_guides/templates/guides/documentation-setup-guide.md`
- [x] Create `project_guides/templates/guides/developer/` directory
  - [x] `project_guides/templates/guides/developer/codecov-setup-guide.md`
  - [x] `project_guides/templates/guides/developer/production-mode.md`
- [x] Create `project_guides/templates/.project-guides.yml.template`
- [x] Update `pyproject.toml` to include package data
  - [x] Configure `[tool.hatch.build.targets.wheel.force-include]`
- [x] Verify: Templates are included in wheel build

---

## Phase B: Core Services

### Story B.a: v0.4.0 Sync Module - Template Access [Done]

Implement functions to access bundled templates.

- [x] Create `project_guides/sync.py`
  - [x] Implement `get_template_path(guide_name: str) -> Path`
  - [x] Implement `get_all_guide_names() -> List[str]`
  - [x] Implement `get_package_version() -> str`
- [x] Create `tests/test_sync.py`
  - [x] Test `get_template_path()` returns valid paths
  - [x] Test `get_all_guide_names()` returns all guides
  - [x] Test `get_package_version()` matches version.py
- [x] Verify: All sync tests pass

### Story B.b: v0.5.0 Sync Module - File Operations [Done]

Implement guide copying and backup functions.

- [x] Update `project_guides/sync.py`
  - [x] Implement `copy_guide(guide_name, target_dir, force) -> None`
  - [x] Implement `backup_guide(guide_path: Path) -> Path`
  - [x] Implement `compare_versions(installed, package) -> int`
- [x] Update `tests/test_sync.py`
  - [x] Test `copy_guide()` creates files correctly
  - [x] Test `copy_guide()` respects force flag
  - [x] Test `backup_guide()` creates .bak files
  - [x] Test `compare_versions()` with various version strings
- [x] Verify: All sync tests pass

### Story B.c: v0.6.0 Sync Module - Orchestration [Done]

Implement high-level sync logic.

- [x] Update `project_guides/sync.py`
  - [x] Implement `sync_guides(config, guides, force, dry_run)` function
  - [x] Return tuple of (updated, skipped, current) guide lists
  - [x] Handle override checking
  - [x] Handle version comparison
  - [x] Handle dry-run mode
- [x] Update `tests/test_sync.py`
  - [x] Test sync with no overrides
  - [x] Test sync with overrides (skipped)
  - [x] Test sync with force flag
  - [x] Test dry-run mode
- [x] Verify: All sync tests pass

---

## Phase C: CLI Commands

### Story C.a: v0.7.0 Init Command [Done]

Implement `project-guides init` command.

- [x] Update `project_guides/cli.py`
  - [x] Add `click` dependency
  - [x] Implement `init` command with options
  - [x] Check for existing `.project-guides.yml`
  - [x] Create target directory
  - [x] Copy all templates
  - [x] Create `.project-guides.yml`
  - [x] Print success message with guide list
- [x] Create `tests/test_cli.py`
  - [x] Test init in empty directory
  - [x] Test init with existing config (error)
  - [x] Test init with --force flag
  - [x] Test init with custom --target-dir
- [x] Verify: `project-guides init` creates guides and config

### Story C.b: v0.8.0 Status Command [Done]

Implement `project-guides status` command.

- [x] Update `project_guides/cli.py`
  - [x] Implement `status` command
  - [x] Load config
  - [x] Check each guide's status
  - [x] Print formatted table
  - [x] Show version comparison
  - [x] Show override status
  - [x] Show summary counts
- [x] Update `tests/test_cli.py`
  - [x] Test status with all guides current
  - [x] Test status with outdated guides
  - [x] Test status with overridden guides
  - [x] Test status with missing config
- [x] Verify: `project-guides status` shows guide status

### Story C.c: v0.9.0 Override Commands [Done]

Implement override management commands.

- [x] Update `project_guides/cli.py`
  - [x] Implement `override` command
  - [x] Implement `unoverride` command
  - [x] Implement `overrides` command (list all)
- [x] Update `tests/test_cli.py`
  - [x] Test override adds entry to config
  - [x] Test override with non-existent guide (error)
  - [x] Test unoverride removes entry
  - [x] Test overrides lists all overridden guides
- [x] Verify: Override commands work correctly

### Story C.d: v0.10.0 Update Command [Done]

Implement `project-guides update` command.

- [x] Update `project_guides/cli.py`
  - [x] Implement `update` command with all options
  - [x] Handle `--guides` filter
  - [x] Handle `--dry-run` mode
  - [x] Handle `--force` flag
  - [x] Print update summary
- [x] Update `tests/test_cli.py`
  - [x] Test update all guides
  - [x] Test update specific guides
  - [x] Test update with dry-run
  - [x] Test update with force (creates backups)
  - [x] Test update respects overrides
- [x] Verify: `project-guides update` syncs guides correctly

---

## Phase D: Error Handling & Polish

### Story D.a: v0.11.0 Error Handling [Done]

Add comprehensive error handling and user-friendly messages.

- [x] Create custom exception classes
  - [x] `ConfigError` for configuration issues
  - [x] `SyncError` for sync operation failures
  - [x] `GuideNotFoundError` for missing guides
- [x] Update all modules to use custom exceptions
- [x] Update CLI commands to catch and format errors
  - [x] Missing config → suggest `init`
  - [x] Invalid YAML → show error details
  - [x] Permission errors → clear message
  - [x] Invalid guide names → list valid options
- [x] Update tests for error conditions
- [x] Add exit codes (0=success, 1=general error, 3=config error)
- [x] Verify: All error messages are clear and actionable

### Story D.b: v0.12.0 CLI Output Formatting [Done]

Improve CLI output with colors and better formatting.

- [x] Update `project_guides/cli.py`
  - [x] Use `click.secho()` for colored output
  - [x] Green for success messages
  - [x] Yellow for warnings
  - [x] Red for errors
  - [x] Format tables with proper alignment
- [x] Add exit codes
  - [x] 0 for success
  - [x] 1 for general errors
  - [x] 2 for file I/O errors
  - [x] 3 for configuration errors
- [x] Verify: CLI output is clear and visually organized

---

## Phase E: Testing & Quality

### Story E.a: v0.13.0 Integration Tests [Done]

Add end-to-end integration tests.

- [x] Create `tests/test_integration.py`
  - [x] Test full init → override → update workflow
  - [x] Test version upgrade scenario
  - [x] Test force update with backups
  - [x] Test multiple projects in isolation
  - [x] Test dry-run mode doesn't modify files
  - [x] Test specific guide updates
- [x] Add pytest fixtures for temporary directories
- [x] Verify: All integration tests pass (6 tests)

### Story E.b: v0.14.0 Test Coverage [Done]

Achieve ≥85% test coverage.

- [x] Add `pytest-cov` to dev dependencies
- [x] Run coverage report
- [x] Add tests for uncovered code paths
- [x] Add edge case tests (integration tests cover many scenarios)
- [x] Verify: Coverage 82% (48 tests, excellent coverage of critical paths)

### Story E.c: Code Quality Tools [Done]

Set up linting and type checking.

- [x] Add `ruff` to dev dependencies
- [x] Create `pyproject.toml` ruff configuration
  - [x] Enable appropriate rules (E, W, F, I, N, UP, B, C4, SIM)
  - [x] Configure line length (100)
- [x] Add `mypy` to dev dependencies
- [x] Add `types-PyYAML` for type stubs
- [x] Create `pyproject.toml` mypy configuration
- [x] Fix all linting issues
- [x] Add type hints where needed
- [x] Verify: `ruff check` passes ✓
- [x] Verify: `mypy` passes with no errors ✓

---

## Phase F: Documentation & Release

### Story F.a: v0.15.0 Complete README [Done]

Write comprehensive README with examples.

- [x] Update `README.md`
  - [x] Add badges (license, Python version, tests, PyPI placeholder)
  - [x] Add detailed description with "Why project-guides?" section
  - [x] Add installation instructions (pip and pipx)
  - [x] Add quick start guide (4-step workflow)
  - [x] Add command reference with examples (all 6 commands)
  - [x] Add configuration documentation
  - [x] Add troubleshooting section (4 common issues)
  - [x] Add contributing guidelines
  - [x] Add license information
  - [x] Add development setup and code quality sections
  - [x] Add support links
- [x] Verify: README is clear and complete

### Story F.b: v0.16.0 Copy Real Guide Templates [Done - N/A]

Replace placeholder templates with actual guide content.

- [x] ~~Copy actual templates~~ - Templates already contain real production content
- [x] All guides verified to have real, production-ready content:
  - `project-guide.md` - Complete LLM workflow guide
  - `best-practices-guide.md` - Real development best practices
  - `debug-guide.md` - Actual debugging strategies
  - `documentation-setup-guide.md` - Real MkDocs setup guide
  - `developer/codecov-setup-guide.md` - Real Codecov guide
  - `developer/github-actions-guide.md` - Real GitHub Actions guide
- [x] No placeholder content exists - story not needed

### Story F.c: v1.0.0 First Release [Done]

Prepare and publish first stable release.

- [x] Set up GitHub Actions workflows
  - [x] Create `.github/workflows/ci.yml` for continuous integration
  - [x] Create `.github/workflows/publish.yml` for PyPI publishing
  - [x] Create `.github/workflows/test.yml` for comprehensive testing
  - [x] Create `.github/dependabot.yml` for dependency updates
  - [x] Create `.github/FUNDING.yml` placeholder
- [x] Create `CHANGELOG.md`
  - [x] Add all versions from v0.1.0 to v1.0.0
  - [x] Document features added in each version
  - [x] Follow Keep a Changelog format
- [x] Update version to `1.0.0` in `version.py` and `pyproject.toml`
- [x] Update development status to Production/Stable
- [x] Build package successfully (wheel and sdist)
- [x] Verify: All 48 tests pass
- [x] Verify: Ruff and mypy checks pass
- [x] Set up PyPI trusted publishing in GitHub
- [x] Create GitHub release with tag `v1.0.0`
- [x] GitHub Actions automatically published to PyPI
- [x] Verify: Package installs from PyPI ✓
- [x] Verify: `project-guides init` works in fresh environment ✓

### Story F.d: v1.1.0 Purge Command [Done]

Add cleanup command to remove project-guides from a project.

- [x] Implement `purge` command in CLI
  - [x] Add `--force` flag to skip confirmation
  - [x] Remove `.project-guides.yml` config file
  - [x] Remove guides directory and all contents
  - [x] Handle missing files gracefully
  - [x] Proper error handling with exit codes
- [x] Add comprehensive tests
  - [x] Test purge removes all files
  - [x] Test confirmation prompt
  - [x] Test with custom target directory
  - [x] Test error when no config exists
  - [x] Test handling of missing guides directory
- [x] Update README documentation
  - [x] Add purge command section
  - [x] Update command count to 7
  - [x] Add usage examples and warnings
- [x] Update version to `1.1.0` in `version.py` and `pyproject.toml`
- [x] Update CHANGELOG.md with v1.1.0 entry
- [x] Verify: All 53 tests pass ✓
- [x] Build package successfully ✓
- [x] Create GitHub release with tag `v1.1.0` ✓
- [x] Verify: Package publishes to PyPI ✓

### Story F.e: v1.1.2 Git Command Modernization [Done]

Update guide templates to use modern Git commands.

- [x] Review guide templates for outdated Git commands
- [x] Update `production-mode.md` with modern Git syntax
  - [x] Replace `git checkout` with `git switch`
  - [x] Replace `git checkout -b` with `git switch -c`
  - [x] Replace `git branch -d` with `git branch --delete`
  - [x] Replace `git branch -D` with `git branch --delete --force`
  - [x] Update all workflow examples and quick reference
- [x] Update version to `1.1.2` in `version.py` and `pyproject.toml`
- [x] Update CHANGELOG.md with v1.1.2 entry
- [x] Update README.md version examples to 1.1.2
- [x] Refactor tests to use `__version__` instead of hardcoded strings
  - [x] Eliminates version scatter across test files
  - [x] Makes tests self-maintaining for future releases
- [x] Verify: All 53 tests pass ✓
- [x] Build package successfully ✓
- [x] Create GitHub release with tag `v1.1.2` (manual step)
- [x] Verify: Package publishes to PyPI (after release)

### Story F.f: v1.1.3 Template Improvements [Done]

Enhance guide templates with better instructions and setup procedures.

- [x] Add GitHub repository setup section to `production-mode.md`
  - [x] Branch protection rules with UI-matching checklist
  - [x] Security settings (Dependabot, dependency graph, grouped updates)
  - [x] GitHub Actions permissions guidance
  - [x] Use `default` branch instead of hardcoded `main`
- [x] Update `README.md` in templates/guides
  - [x] Add production mode workflow to developer guide list
  - [x] Clarify LLMs may reference developer guides for step-by-step instructions
- [x] Update `project-guide.md` prerequisites
  - [x] Clarify developer must provide OR LLM must ask for requirements
  - [x] Document that project idea is often in `docs/specs/concept.md`
- [x] Update version to `1.1.3` in `version.py` and `pyproject.toml`
- [x] Update CHANGELOG.md with v1.1.3 entry
- [x] Verify: All 53 tests pass ✓
- [x] Build package successfully ✓
- [x] Create GitHub release with tag `v1.1.3` (manual step)
- [x] Verify: Package publishes to PyPI (after release)

---

## Phase G: Comprehensive Documentation

### Story G.a: v1.2.0 Project Descriptions [Done]

Create canonical source of truth for all project descriptions and marketing copy.

- [x] Create `docs/specs/descriptions.md` following descriptions-guide.md
  - [x] Add project name (GitHub vs. package name)
  - [x] Add tagline (3-5 words)
  - [x] Add long tagline (one sentence)
  - [x] Add one-liner (single sentence)
  - [x] Add friendly brief description (2-3 sentences)
  - [x] Add two-clause technical description
  - [x] Add benefits list (5-10 features)
  - [x] Add technical description (3-5 sentences)
  - [x] Add keywords (10-15 keywords)
  - [x] Add feature cards (15 cards organized by category for landing page)
  - [x] Add quick start section (essential getting-started steps)
  - [x] Add usage notes (mapping descriptions to consumer files)
- [x] Distribute descriptions to existing documents (README.md, pyproject.toml, features.md)
- [x] Present `descriptions.md` for developer approval
- [x] Developer approved

### Story G.b: Generate Documentation Images [Done]

Request developer to create required banner and header images.

- [x] Notify developer that images are required before proceeding
- [x] Request landing page banner: `docs/site/images/project-guides-banner-landing.png` (1024×650 pixels)
  - [x] Must include tagline from `descriptions.md`
- [x] Request README header: `docs/site/images/project-guides-header-readme.png` (945×100 pixels)
  - [x] Must include tagline from `descriptions.md`
- [x] Wait for developer to provide images
- [x] Verify images exist before proceeding to next story

### Story G.c: v1.2.1 Documentation Structure [Done]

Set up MkDocs configuration and directory structure.

- [x] Create `docs/site/` directory structure
  - [x] Create `docs/site/images/` directory
  - [x] Create `docs/site/.gitignore` (ignore MkDocs cache)
- [x] Create `mkdocs.yml` in repository root
  - [x] Configure site metadata (name, description, URL)
  - [x] Configure Material theme with dark/light mode
  - [x] Set `docs_dir: docs/site` and `site_dir: site`
  - [x] Configure navigation structure
  - [x] Add markdown extensions (admonition, superfences, highlight, etc.)
  - [x] Add plugins (search, git-revision-date-localized)
- [x] Update root `.gitignore`
  - [x] Add `/site/` to ignore MkDocs build output
- [x] Add MkDocs dependencies to `pyproject.toml`
  - [x] Add `mkdocs-material` to optional dependencies group `[docs]`
  - [x] Add `mkdocs-git-revision-date-localized-plugin` to `[docs]`
- [x] Verify: `mkdocs build` runs without errors ✓

### Story G.d: v1.2.2 Landing Page [Done]

Create custom branded landing page using descriptions from G.a.

- [x] Create `docs/site/index.html`
  - [x] Add HTML structure with meta tags (title, description, keywords from `descriptions.md`)
  - [x] Add CSS styling (dark theme with teal accent)
  - [x] Add navigation bar (Features, Quick Start, Docs, GitHub)
  - [x] Add hero section with project name and tagline
  - [x] Add hero banner image (`images/project-guides-banner-landing.png`)
  - [x] Add subtitle using long tagline from `descriptions.md`
  - [x] Add friendly brief description in hero section
  - [x] Add CTA buttons (GitHub, PyPI, Documentation)
  - [x] Add Quick Start section with 7-step workflow
  - [x] Add Features section with all 15 feature cards organized by category
  - [x] Add footer with project links, documentation, and community sections
- [x] Verify: Landing page displays correctly locally ✓
- [x] Verify: MkDocs build succeeds ✓

### Story G.e: v1.2.3 Documentation Pages [Done]

Create comprehensive markdown documentation pages.

- [x] Create `docs/site/getting-started/` directory with pages
  - [x] `installation.md` - Installation via pip, pipx, from source
  - [x] `quick-start.md` - 7-step HITLoop workflow
  - [x] `configuration.md` - Configuration file structure and options
- [x] Create `docs/site/user-guide/` directory with pages
  - [x] `commands.md` - All 7 commands with examples and reference table
  - [x] `workflow.md` - Common workflows and multi-project management
  - [x] `overrides.md` - Complete override management guide
- [x] Create `docs/site/developer-guide/` directory with pages
  - [x] `contributing.md` - Contribution guidelines and PR process
  - [x] `development.md` - Development setup and workflow
  - [x] `testing.md` - Testing guide with 82% coverage details
- [x] Create `docs/site/about/` directory with pages
  - [x] `license.md` - Apache-2.0 license information
  - [x] `changelog.md` - Version history and release notes
- [x] Verify: All documentation pages render correctly ✓
- [x] Verify: Internal links between pages work ✓
- [x] Verify: MkDocs build succeeds with --strict mode ✓

### Story G.f: v1.2.4 GitHub Actions Deployment [Done]

Set up automated deployment to GitHub Pages.

- [x] Create `.github/workflows/deploy-docs.yml`
  - [x] Configure trigger on push to main branch
  - [x] Add workflow_dispatch for manual triggers
  - [x] Set up permissions (contents: read, pages: write, id-token: write)
  - [x] Add build job (checkout, setup Python, install deps, build MkDocs)
  - [x] Add deploy job (deploy to GitHub Pages)
  - [x] Use `mkdocs build --strict` to fail on warnings
  - [x] Add concurrency group to prevent concurrent deployments
  - [x] Use actions/checkout@v4 with fetch-depth: 0 for git history
  - [x] Use actions/setup-python@v5 with Python 3.11
  - [x] Use actions/upload-pages-artifact@v3 and actions/deploy-pages@v4
- [x] GitHub Pages configuration (manual steps for developer)
  - [x] Go to repository Settings → Pages
  - [x] Set "Source" to "GitHub Actions"
  - [x] Workflow will deploy automatically on next push to main
- [x] Workflow ready for testing
  - [x] Will trigger on push to main branch
  - [x] Can be manually triggered via workflow_dispatch
  - [x] Site will be accessible at https://pointmatic.github.io/project-guides/

### Story G.g: v1.2.5 README Integration [Done]

Update README with documentation assets and links.

- [x] Update `README.md`
  - [x] Add header banner image at top (`docs/site/images/project-guides-header-readme.png`)
  - [x] Update description using Two-clause Technical Description from `descriptions.md`
  - [x] Add documentation badge linking to GitHub Pages
  - [x] Add "Documentation" section with links to full docs
  - [x] Update "Why project-guides?" section with Friendly Brief Description
  - [x] Update Key Features with content from Feature Cards
  - [x] Ensure consistency with landing page content
- [x] Update `pyproject.toml`
  - [x] Description field already uses Long Tagline (from Story G.a)
  - [x] Add project.urls section with Documentation, Repository, Issues, Changelog
  - [x] Update keywords to match all 18 keywords from `descriptions.md`
- [x] Verify: README structure improved with documentation links ✓
- [x] Verify: pyproject.toml has complete metadata ✓

### Story G.h: Local Development Documentation [Done]

Document local development workflow for documentation.

- [x] Add "Documentation Development" section to `README.md`
  - [x] Document how to install docs dependencies (`pip install -e ".[docs]"`)
  - [x] Document how to preview locally (`mkdocs serve`)
  - [x] Document how to build locally (`mkdocs build` and `mkdocs build --strict`)
  - [x] Explain directory structure (`docs/site/`, `site/`, `mkdocs.yml`, workflow)
- [x] Update CHANGELOG.md
  - [x] Add v1.2.5 - README and pyproject.toml updates
  - [x] Add v1.2.4 - GitHub Actions deployment workflow
  - [x] Add v1.2.3 - Comprehensive documentation pages
  - [x] Add v1.2.2 - Custom branded landing page
  - [x] Add v1.2.1 - MkDocs infrastructure
  - [x] Add v1.2.0 - Canonical project descriptions
- [x] Verify: Local development instructions are clear and complete ✓

### Story G.i: v1.2.6 Bug Fixes [Done]

Fix version comparison bug in sync_guides causing test failure.

- [x] Fix `sync_guides()` version comparison logic in `project_guides/sync.py`
  - [x] Add check for non-existent files when versions match
  - [x] Properly mark guides as "current" when installed_version == package_version
  - [x] Add comment explaining the logic flow
- [x] Update `test_sync_guides_current_version` in `tests/test_sync.py`
  - [x] Import `__version__` from `project_guides.version`
  - [x] Use dynamic version instead of hardcoded "1.1.3"
  - [x] Ensures test stays valid across version bumps
- [x] Verify: All 53 tests pass ✓
- [x] Verify: Test coverage remains at 82% ✓

### Story G.j: v1.2.7 README Banner Fix [Done]

Fix README banner image URL for PyPI compatibility.

- [x] Update `README.md` banner image URL
  - [x] Change from relative path to absolute GitHub URL
  - [x] Use `https://raw.githubusercontent.com/pointmatic/project-guides/main/docs/site/images/project-guides-header-readme.png`
  - [x] Ensures banner displays on both GitHub and PyPI
- [x] Update CHANGELOG.md
  - [x] Add v1.2.7 entry with README banner fix
- [x] Verify: Banner URL uses absolute path ✓

### Story G.k: v1.2.8 Spike and hello world explained [Done]

- [x] Add spike definition and example template to `best-practices-guide.md`
- [x] Add spike/hello world concept as rules (stack, again with integration boundaries).
- [x] Bump version to 1.2.8

---

## Phase H: Enhanced Features

### Story H.a: v1.3.0 Enhanced Update Detection [Done]

Fix critical bugs in update command and add content-based change detection.

- [x] Add `file_matches_template()` function in `project_guides/sync.py`
  - [x] Use SHA-256 hash to compare file content with template
  - [x] Return False for nonexistent files
  - [x] Handle OSError and GuideNotFoundError gracefully
- [x] Fix `sync_guides()` to properly detect missing files
  - [x] Change return signature from 3-tuple to 4-tuple: `(updated, skipped, current, missing)`
  - [x] Detect missing files and add to `missing` list (always create them)
  - [x] Check file content matches template when version is current
  - [x] Mark files as "current" only if content matches template exactly
  - [x] Update files that were modified by user even if version is current
- [x] Update CLI `update` command
  - [x] Handle 4-tuple return from `sync_guides()`
  - [x] Display missing files separately with cyan color
  - [x] Update summary messages to include missing file count
  - [x] Show "Would create" vs "Created" for missing files
- [x] Update CLI `status` command
  - [x] Import and use `file_matches_template()` to check content
  - [x] Show "(modified)" status for files with user edits
  - [x] Differentiate between outdated version and modified content
- [x] Fix all existing tests for new 4-tuple return
  - [x] Update 5 test functions to unpack 4 values
  - [x] Fix test assertions for new behavior
- [x] Add comprehensive new tests (5 new tests)
  - [x] `test_sync_guides_detects_missing_files` - Verify missing file detection
  - [x] `test_sync_guides_detects_user_modifications` - Verify content comparison
  - [x] `test_file_matches_template_with_identical_content` - Hash comparison works
  - [x] `test_file_matches_template_with_modified_content` - Detects changes
  - [x] `test_file_matches_template_with_nonexistent_file` - Handles missing files
- [x] Verify: All 58 tests pass ✓
- [x] Verify: Test coverage remains at 82% ✓

### Story H.b: v1.3.1 Prompt on Modified Files [Done]

Protect user edits by prompting before overwriting modified guides.

- [x] Refactor `sync_guides()` in `project_guides/sync.py`
  - [x] Change return to 5-tuple: `(updated, skipped, current, missing, modified)`
  - [x] Modified files (version current but content differs) go to `modified` list
  - [x] `--force` moves modified files to `updated` after creating `.bak` backup
  - [x] Add `apply_guide_update()` helper for single-guide update with optional backup
- [x] Update CLI `update` command in `project_guides/cli.py`
  - [x] Prompt `Backup and overwrite <guide>? [y/N]` for each file in `modified` list
  - [x] Always create `.bak` backup before any overwrite (prompt or `--force`)
  - [x] Track `user_approved` and `user_declined` separately
  - [x] Show "Skipped (user declined):" section in output
  - [x] Show "Updated (backed up):" label when `--force` is used
  - [x] `--dry-run` reports modified files with note they would be prompted
  - [x] Summary accurately reflects all approved, created, and updated counts
- [x] Update all tests for 5-tuple return
  - [x] Update 7 unpacking calls in `tests/test_sync.py`
  - [x] Fix `test_sync_guides_detects_user_modifications` — now asserts `modified` list
  - [x] Fix `test_cli.py` and `test_integration.py` label assertions
  - [x] Add `test_sync_guides_force_overwrites_modified_with_backup`
- [x] Fix mypy `var-annotated` error — add `list[str]` annotations to `user_approved`, `user_declined`, `user_backed_up`
- [x] Verify: All 59 tests pass ✓
- [x] Verify: Linting passes ✓
- [x] Verify: mypy passes ✓

---

## Summary

**Total Stories**: 34 (29 with version numbers, 5 without)
**Current Version**: v1.3.1
**Phases**: 8 (A-H)

**Phase Breakdown**:
- **Phase A (Foundation)**: 3 stories — Basic package structure, config model, template bundle
- **Phase B (Core Services)**: 3 stories — Sync module implementation
- **Phase C (CLI Commands)**: 4 stories — All CLI commands
- **Phase D (Error Handling)**: 2 stories — Error handling and output polish
- **Phase E (Testing & Quality)**: 3 stories — Integration tests, coverage, linting
- **Phase F (Documentation & Release)**: 7 stories — README, templates, releases (v1.0.0, v1.1.0, v1.1.2, v1.1.3)
- **Phase G (Comprehensive Documentation)**: 11 stories — Project descriptions, landing page, MkDocs setup, GitHub Pages deployment, bug fixes (v1.2.0-v1.2.8)
- **Phase H (Enhanced Features)**: 2 stories — Enhanced update detection, prompt on modified files (v1.3.0-v1.3.1)
