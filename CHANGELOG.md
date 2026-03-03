# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/pointmatic/project-guides/compare/v1.0.0...HEAD
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
