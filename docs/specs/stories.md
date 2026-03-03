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

### Story D.b: v0.12.0 CLI Output Formatting [Planned]

Improve CLI output with colors and better formatting.

- [ ] Update `project_guides/cli.py`
  - [ ] Use `click.secho()` for colored output
  - [ ] Green for success messages
  - [ ] Yellow for warnings
  - [ ] Red for errors
  - [ ] Format tables with proper alignment
- [ ] Add exit codes
  - [ ] 0 for success
  - [ ] 1 for general errors
  - [ ] 2 for file I/O errors
  - [ ] 3 for configuration errors
- [ ] Verify: CLI output is clear and visually organized

---

## Phase E: Testing & Quality

### Story E.a: v0.13.0 Integration Tests [Planned]

Add end-to-end integration tests.

- [ ] Create `tests/test_integration.py`
  - [ ] Test full init → override → update workflow
  - [ ] Test version upgrade scenario
  - [ ] Test force update with backups
  - [ ] Test multiple projects in isolation
- [ ] Add pytest fixtures for temporary directories
- [ ] Verify: All integration tests pass

### Story E.b: v0.14.0 Test Coverage [Planned]

Achieve ≥85% test coverage.

- [ ] Add `pytest-cov` to dev dependencies
- [ ] Run coverage report
- [ ] Add tests for uncovered code paths
- [ ] Add edge case tests
  - [ ] Empty directories
  - [ ] Corrupted YAML files
  - [ ] Concurrent operations
- [ ] Verify: Coverage ≥85%

### Story E.c: Code Quality Tools [Planned]

Set up linting and type checking.

- [ ] Add `ruff` to dev dependencies
- [ ] Create `pyproject.toml` ruff configuration
  - [ ] Enable appropriate rules
  - [ ] Configure line length
- [ ] Add `mypy` to dev dependencies
- [ ] Create `pyproject.toml` mypy configuration
- [ ] Fix all linting issues
- [ ] Add type hints to all functions
- [ ] Verify: `ruff check` passes
- [ ] Verify: `mypy` passes with no errors

---

## Phase F: Documentation & Release

### Story F.a: v0.15.0 Complete README [Planned]

Write comprehensive README with examples.

- [ ] Update `README.md`
  - [ ] Add badges (license, PyPI version placeholder)
  - [ ] Add detailed description
  - [ ] Add installation instructions (pip and pipx)
  - [ ] Add quick start guide
  - [ ] Add command reference with examples
  - [ ] Add configuration documentation
  - [ ] Add troubleshooting section
  - [ ] Add contributing guidelines
  - [ ] Add license information
- [ ] Verify: README is clear and complete

### Story F.b: v0.16.0 Copy Real Guide Templates [Planned]

Replace placeholder templates with actual guide content.

- [ ] Copy actual `project-guide.md` to templates
- [ ] Copy actual `best-practices-guide.md` to templates
- [ ] Copy actual `debug-guide.md` to templates
- [ ] Copy actual `documentation-setup-guide.md` to templates
- [ ] Copy actual developer guides to templates
- [ ] Update templates README with guide descriptions
- [ ] Verify: All templates have real content

### Story F.c: v1.0.0 First Release [Planned]

Prepare and publish first stable release.

- [ ] Create `CHANGELOG.md`
  - [ ] Add all versions from v0.1.0 to v1.0.0
  - [ ] Document features added in each version
- [ ] Update version to `1.0.0` in `version.py`
- [ ] Build package: `python -m build`
- [ ] Test installation from wheel
- [ ] Create git tag: `v1.0.0`
- [ ] Publish to PyPI: `python -m twine upload dist/*`
- [ ] Verify: Package installs from PyPI
- [ ] Verify: All commands work in fresh environment

---

## Summary

**Total Stories**: 19 (16 with version numbers, 3 without)
**Final Version**: v1.0.0
**Estimated Phases**: 6 (A-F)

**Phase Breakdown**:
- **Phase A (Foundation)**: 3 stories — Basic package structure, config model, template bundle
- **Phase B (Core Services)**: 3 stories — Sync module implementation
- **Phase C (CLI Commands)**: 4 stories — All CLI commands
- **Phase D (Error Handling)**: 2 stories — Error handling and output polish
- **Phase E (Testing & Quality)**: 3 stories — Integration tests, coverage, linting
- **Phase F (Documentation & Release)**: 4 stories — README, real templates, first release
