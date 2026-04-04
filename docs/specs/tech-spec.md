# tech-spec.md — project-guide (Python)

This document defines **how** the `project-guide` project is built — architecture, module layout, dependencies, data models, API signatures, and cross-cutting concerns.

For requirements and behavior, see `features.md`. For the implementation plan, see the stories document (to be created).

---

## Runtime & Tooling

- **Language**: Python 3.11+
- **Package Manager**: pip / uv
- **Build System**: Hatchling (via pyproject.toml)
- **Linter**: ruff (check + format)
- **Test Runner**: pytest
- **Type Checker**: mypy (optional, recommended)
- **CLI Framework**: click (or argparse for minimal dependencies)
- **Package Data**: Include guide templates via `package_data` in pyproject.toml

---

## Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `click` | ^8.1 | CLI framework with command groups and help text |
| `pyyaml` | ^6.0 | Parse and write `.project-guide.yml` configuration |
| `packaging` | ^24.0 | Version comparison and parsing |

**Alternative (minimal)**: Use only stdlib (`argparse` instead of `click`, manual YAML parsing) to reduce dependencies.

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ^8.0 | Test runner |
| `pytest-cov` | ^5.0 | Coverage reporting |
| `ruff` | ^0.6 | Linting and formatting |
| `mypy` | ^1.11 | Type checking |

### System Dependencies

None — pure Python, no external binaries required.

---

## Package Structure

```
project-guide/
├── pyproject.toml                    # Package metadata, dependencies, build config
├── README.md                         # Installation, usage, examples
├── LICENSE                           # Apache-2.0
├── .gitignore                        # Python, IDE, build artifacts
├── project_guides/
│   ├── __init__.py                   # Package version, public API
│   ├── __main__.py                   # Entry point for `python -m project_guides`
│   ├── cli.py                        # CLI command definitions (click commands)
│   ├── config.py                     # Configuration model and file I/O
│   ├── sync.py                       # Guide synchronization logic
│   ├── templates/                    # Bundled guide templates
│   │   ├── guides/
│   │   │   ├── README.md
│   │   │   ├── project-guide.md
│   │   │   ├── best-practices-guide.md
│   │   │   ├── debug-guide.md
│   │   │   ├── documentation-setup-guide.md
│   │   │   └── developer/
│   │   │       ├── codecov-setup-guide.md
│   │   │       └── production-mode.md
│   │   └── .project-guide.yml.template  # Default config template
│   └── version.py                    # Version constant
└── tests/
    ├── __init__.py
    ├── test_cli.py                   # CLI command tests
    ├── test_config.py                # Config parsing and writing tests
    ├── test_sync.py                  # Sync logic tests
    └── fixtures/                     # Test data (sample configs, guides)
```

---

## Key Component Design

### Module: `cli.py`

**Purpose**: Define CLI commands using click.

**Commands**:

```python
@click.group()
@click.version_option()
def main():
    """Manage LLM project guides across repositories."""
    pass

@main.command()
@click.option('--target-dir', default='docs/guides', help='Target directory for guides')
@click.option('--force', is_flag=True, help='Overwrite existing files')
def init(target_dir: str, force: bool):
    """Initialize guides in a new project."""
    # 1. Check if .project-guide.yml exists (error unless --force)
    # 2. Create target directory if needed
    # 3. Copy all templates from package data to target_dir
    # 4. Create .project-guide.yml with current version
    # 5. Print success message with list of installed guides

@main.command()
@click.option('--guides', multiple=True, help='Specific guides to update')
@click.option('--dry-run', is_flag=True, help='Show changes without applying')
@click.option('--force', is_flag=True, help='Update overridden guides (creates backups)')
@click.option('--interactive', is_flag=True, help='Prompt for each guide')
def update(guides: tuple[str, ...], dry_run: bool, force: bool, interactive: bool):
    """Update guides to latest version."""
    # 1. Load .project-guide.yml (error if missing)
    # 2. Get list of guides to update (all or --guides subset)
    # 3. For each guide:
    #    - Check if overridden (skip unless --force)
    #    - Check if current (skip if same version)
    #    - If --interactive, prompt user
    #    - If --dry-run, print what would change
    #    - Otherwise, copy template to target
    # 4. Update .project-guide.yml with new version
    # 5. Print summary

@main.command()
def status():
    """Show status of all guides."""
    # 1. Load .project-guide.yml (error if missing)
    # 2. Get package version
    # 3. For each guide:
    #    - Check if file exists
    #    - Check if overridden
    #    - Check if current version
    # 4. Print table with status

@main.command()
@click.option('--guide', required=True, help='Guide filename to override')
@click.option('--reason', required=True, help='Reason for override')
def override(guide: str, reason: str):
    """Mark a guide as overridden (won't be updated)."""
    # 1. Load .project-guide.yml (error if missing)
    # 2. Check if guide file exists (error if not)
    # 3. Add override entry with reason, current version, date
    # 4. Save .project-guide.yml
    # 5. Print success message

@main.command()
@click.option('--guide', required=True, help='Guide filename to unoverride')
def unoverride(guide: str):
    """Remove override from a guide (allow updates)."""
    # 1. Load .project-guide.yml (error if missing)
    # 2. Remove override entry
    # 3. Save .project-guide.yml
    # 4. Print success message

@main.command()
def overrides():
    """List all overridden guides."""
    # 1. Load .project-guide.yml (error if missing)
    # 2. Print table of overridden guides with reason, version, date
```

**Error Handling**:
- Missing `.project-guide.yml` → suggest running `init` first
- File permission errors → clear error message
- Invalid YAML → parse error with line number
- Invalid guide name → list valid guide names

---

### Module: `config.py`

**Purpose**: Configuration model and file I/O.

**Data Model**:

```python
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Optional

@dataclass
class GuideOverride:
    """Represents an overridden guide."""
    reason: str
    locked_version: str
    last_updated: date

@dataclass
class Config:
    """Project configuration for project-guide."""
    version: str = "1.0"  # Config schema version
    installed_version: str = ""  # Package version when last synced
    target_dir: str = "docs/guides"
    overrides: Dict[str, GuideOverride] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str = ".project-guide.yml") -> "Config":
        """Load configuration from YAML file."""
        # Read YAML, parse into Config object
        # Handle missing file, invalid YAML, schema errors
        pass

    def save(self, path: str = ".project-guide.yml") -> None:
        """Save configuration to YAML file."""
        # Convert Config to dict, write as YAML
        pass

    def is_overridden(self, guide_name: str) -> bool:
        """Check if a guide is overridden."""
        return guide_name in self.overrides

    def add_override(self, guide_name: str, reason: str, version: str) -> None:
        """Add or update an override."""
        self.overrides[guide_name] = GuideOverride(
            reason=reason,
            locked_version=version,
            last_updated=date.today()
        )

    def remove_override(self, guide_name: str) -> None:
        """Remove an override."""
        self.overrides.pop(guide_name, None)
```

**Functions**:

```python
def load_config(path: str = ".project-guide.yml") -> Config:
    """Load configuration from file."""
    # Wrapper around Config.load() with error handling

def save_config(config: Config, path: str = ".project-guide.yml") -> None:
    """Save configuration to file."""
    # Wrapper around config.save() with error handling
```

---

### Module: `sync.py`

**Purpose**: Guide synchronization logic.

**Functions**:

```python
from pathlib import Path
from typing import List, Tuple

def get_template_path(guide_name: str) -> Path:
    """Get path to bundled template for a guide."""
    # Use importlib.resources or pkg_resources to access package data
    # Return Path to template file
    pass

def get_all_guide_names() -> List[str]:
    """Get list of all available guide names."""
    # List files in templates/guides/ directory
    # Return list of filenames
    pass

def copy_guide(guide_name: str, target_dir: Path, force: bool = False) -> None:
    """Copy a guide template to target directory."""
    # Get template path
    # Check if target file exists (error unless force=True)
    # Copy template to target_dir/guide_name
    pass

def backup_guide(guide_path: Path) -> Path:
    """Create a backup of a guide file."""
    # Copy guide_path to guide_path.bak
    # Return backup path
    pass

def compare_versions(installed: str, package: str) -> int:
    """Compare two version strings."""
    # Use packaging.version.parse()
    # Return -1 if installed < package, 0 if equal, 1 if installed > package
    pass

def get_package_version() -> str:
    """Get current package version."""
    # Read from project_guides.__version__
    pass

def sync_guides(
    config: Config,
    guides: List[str] | None = None,
    force: bool = False,
    dry_run: bool = False
) -> Tuple[List[str], List[str], List[str]]:
    """
    Sync guides to latest version.
    
    Returns:
        (updated, skipped, current) - lists of guide names
    """
    # If guides is None, sync all guides
    # For each guide:
    #   - Check if overridden (skip unless force=True)
    #   - Check if current version (skip if same)
    #   - If dry_run, add to updated list but don't copy
    #   - Otherwise, copy template
    # Return lists of updated, skipped, current guides
    pass
```

---

### Module: `version.py`

**Purpose**: Single source of truth for package version.

```python
__version__ = "0.1.0"
```

**Note**: This is imported in `__init__.py` and used throughout the package.

---

### Module: `__init__.py`

**Purpose**: Package initialization and public API.

```python
from project_guides.version import __version__

__all__ = ["__version__"]
```

---

### Module: `__main__.py`

**Purpose**: Entry point for `python -m project_guides`.

```python
from project_guides.cli import main

if __name__ == "__main__":
    main()
```

---

## Data Models

### Configuration Schema (`.project-guide.yml`)

```yaml
version: "1.0"                    # String, config schema version
installed_version: "0.2.1"        # String, package version
target_dir: "docs/guides"         # String, relative path

overrides:                        # Dict[str, GuideOverride]
  debug_guide.md:                 # Guide filename as key
    reason: "Custom case study"   # String, why overridden
    locked_version: "0.2.0"       # String, package version when locked
    last_updated: "2026-03-03"    # String, ISO 8601 date
```

**Validation**:
- `version` must be "1.0"
- `installed_version` must be valid semver
- `target_dir` must be relative path (no absolute paths)
- `overrides` keys must be valid guide filenames
- `locked_version` must be valid semver
- `last_updated` must be ISO 8601 date (YYYY-MM-DD)

---

## CLI Design

### Entry Point

**Package**: `project-guide`
**Command**: `project-guide` (registered in `pyproject.toml` as console script)

### Command Structure

```
project-guide
├── init          Initialize guides in a new project
├── update        Update guides to latest version
├── status        Show status of all guides
├── override      Mark a guide as overridden
├── unoverride    Remove override from a guide
└── overrides     List all overridden guides
```

### Help Text

```bash
$ project-guide --help
Usage: project-guide [OPTIONS] COMMAND [ARGS]...

  Manage LLM project guides across repositories.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  init        Initialize guides in a new project
  update      Update guides to latest version
  status      Show status of all guides
  override    Mark a guide as overridden
  unoverride  Remove override from a guide
  overrides   List all overridden guides
```

### Exit Codes

- `0` — Success
- `1` — General error (missing config, invalid arguments)
- `2` — File I/O error (permission denied, file not found)
- `3` — Configuration error (invalid YAML, schema mismatch)

---

## Cross-Cutting Concerns

### Error Handling

**Strategy**: Fail fast with clear error messages.

**Error Types**:
1. **Missing Configuration** → "No .project-guide.yml found. Run 'project-guide init' first."
2. **Invalid YAML** → "Failed to parse .project-guide.yml: <error> at line <N>"
3. **File Not Found** → "Guide not found: <guide_name>. Available guides: <list>"
4. **Permission Denied** → "Cannot write to <path>: Permission denied"
5. **Invalid Version** → "Invalid version string: <version>"

**Implementation**:
- Use custom exception classes (`ConfigError`, `SyncError`)
- Catch exceptions in CLI commands, print friendly messages
- Exit with appropriate exit codes

### Logging

**Strategy**: Minimal logging, focus on user-facing output.

**Levels**:
- **INFO**: Progress messages (e.g., "Installing project_guide.md...")
- **WARNING**: Non-fatal issues (e.g., "Guide already up to date")
- **ERROR**: Fatal errors (e.g., "Failed to write config file")

**Implementation**:
- Use `click.echo()` for normal output
- Use `click.secho()` with colors for status (green=success, yellow=warning, red=error)
- No debug logging in production (keep it simple)

### File Safety

**Strategy**: Never overwrite files without explicit consent.

**Rules**:
1. `init` without `--force` → error if `.project-guide.yml` exists
2. `update` without `--force` → skip overridden guides
3. `update --force` → create `.bak` backups before overwriting
4. Always validate paths to prevent directory traversal

**Implementation**:
- Check file existence before writing
- Use `shutil.copy2()` to preserve metadata
- Create backups with timestamp suffix (e.g., `debug_guide.md.bak.20260303`)

### Version Comparison

**Strategy**: Use `packaging.version.parse()` for semver comparison.

**Logic**:
```python
from packaging.version import parse

def is_outdated(installed: str, package: str) -> bool:
    return parse(installed) < parse(package)
```

---

## Testing Strategy

### Unit Tests

**Coverage**:
- `config.py`: Config loading, saving, override management
- `sync.py`: Template copying, version comparison, sync logic
- `cli.py`: Command argument parsing (mock file I/O)

**Approach**:
- Use `pytest` fixtures for temporary directories
- Mock file I/O for CLI tests
- Test error conditions (missing files, invalid YAML)

### Integration Tests

**Coverage**:
- Full `init` workflow: create config, copy templates
- Full `update` workflow: sync guides, respect overrides
- Override workflow: add, list, remove overrides

**Approach**:
- Use `tmp_path` fixture for isolated test directories
- Create real files and configs
- Verify file contents and config state

### Acceptance Tests

**Coverage**:
- Install guides in new project
- Update guides after version bump
- Override a guide and verify it's not updated
- Remove override and verify guide updates

**Approach**:
- End-to-end tests using `subprocess` to run CLI
- Verify console output and file state

---

## Packaging and Distribution

### PyPI Metadata

**Package Name**: `project-guide`
**Description**: "Manage LLM development workflow documentation across projects"
**Keywords**: `llm`, `documentation`, `workflow`, `guides`, `templates`
**License**: Apache-2.0
**Python Requires**: `>=3.11`

### Package Data

Include guide templates in distribution:

```toml
[tool.hatch.build.targets.wheel]
packages = ["project_guides"]

[tool.hatch.build.targets.wheel.force-include]
"project_guides/templates" = "project_guides/templates"
```

### Console Script

```toml
[project.scripts]
project-guide = "project_guides.cli:main"
```

### Installation Methods

**Via pip**:
```bash
pip install project-guide
```

**Via pipx** (recommended for system-wide CLI):
```bash
pipx install project-guide
```

---

## Summary

**Architecture**: Simple CLI tool with file-based operations
**Dependencies**: Minimal (click, pyyaml, packaging)
**Data Model**: YAML configuration with override tracking
**CLI**: 6 commands for init, update, status, override management
**Testing**: Unit, integration, and acceptance tests with ≥85% coverage
**Distribution**: PyPI package with bundled templates
