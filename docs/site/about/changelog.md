# Changelog

All notable changes to project-guides are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.1] - 2026-03-25

### Added
- **Prompt before overwriting user-modified guides**
  - `update` command prompts `Overwrite <guide>? [y/N]` for each locally modified file
  - User can accept or decline per-file; declined files are reported as "Skipped (user declined)"
  - `--force` flag skips the prompt, creates a `.bak` backup, and overwrites automatically
  - `--dry-run` reports modified files with a note they would be prompted

### Changed
- `sync_guides()` returns 5-tuple `(updated, skipped, current, missing, modified)` — modified files deferred to CLI for prompting
- `update` output shows "Updated (backed up):" label when `--force` is used
- Test suite expanded to 59 tests

## [1.3.0] - 2026-03-25

### Added
- **Content-based change detection** in `update` and `status` commands
  - New `file_matches_template()` function uses SHA-256 hash to compare file content with templates
  - Detects user modifications even when version numbers match
  - `status` command shows "(modified)" for files with user edits
- **Missing file detection** in `update` command
  - Missing files are now properly detected and reported separately with cyan "+" indicator
  - Missing files are always created, even if version numbers match

### Fixed
- `update` command incorrectly reported "all guides are up to date" when files were missing
- `update` command didn't detect user modifications to guide files

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

## Earlier Versions

For the complete changelog including all pre-1.0 versions, see the [CHANGELOG.md](https://github.com/pointmatic/project-guides/blob/main/CHANGELOG.md) file in the repository.

### Version History

- **0.15.0** - Comprehensive README and documentation
- **0.14.0** - Code quality tools (ruff, mypy)
- **0.13.0** - Integration tests
- **0.12.0** - Colored CLI output
- **0.11.0** - Custom exception classes
- **0.10.0** - `overrides` command
- **0.9.0** - `override` and `unoverride` commands
- **0.8.0** - `update` command
- **0.7.0** - `status` command
- **0.6.0** - Sync orchestration
- **0.5.0** - Backup and version comparison
- **0.4.0** - Template copying
- **0.3.0** - Template bundling
- **0.2.0** - Configuration model
- **0.1.0** - Initial release

## Links

- [GitHub Releases](https://github.com/pointmatic/project-guides/releases)
- [PyPI Release History](https://pypi.org/project/project-guides/#history)
- [Full Changelog](https://github.com/pointmatic/project-guides/blob/main/CHANGELOG.md)

[Unreleased]: https://github.com/pointmatic/project-guides/compare/v1.3.1...HEAD
[1.3.1]: https://github.com/pointmatic/project-guides/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/pointmatic/project-guides/compare/v1.1.3...v1.3.0
[1.1.3]: https://github.com/pointmatic/project-guides/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/pointmatic/project-guides/compare/v1.1.0...v1.1.2
[1.1.0]: https://github.com/pointmatic/project-guides/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/pointmatic/project-guides/compare/v0.15.0...v1.0.0
