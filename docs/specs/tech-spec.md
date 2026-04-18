# tech-spec.md — project-guide (Python)

This document defines **how** the `project-guide` project is built — architecture, module layout, dependencies, data models, API signatures, and cross-cutting concerns.

For requirements and behavior, see `features.md`. For the implementation plan, see `stories.md`.

---

## Runtime & Tooling

- **Language**: Python 3.11+
- **Package Manager**: pip
- **Build System**: Hatchling (via pyproject.toml)
- **Linter**: ruff (check + format)
- **Test Runner**: pytest + pytest-cov
- **Type Checker**: mypy
- **CLI Framework**: click
- **Template Engine**: Jinja2
- **Configuration**: PyYAML

---

## Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `click` | >=8.1 | CLI framework with command groups, options, and styled output |
| `jinja2` | >=3.1 | Template rendering for mode-driven entry point |
| `pyyaml` | >=6.0 | Parse and write `.project-guide.yml` and `.metadata.yml` |
| `packaging` | >=24.0 | Version parsing (used in config, not for sync freshness) |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.0 | Test runner |
| `pytest-cov` | >=4.0 | Coverage reporting (85% minimum) |
| `ruff` | >=0.1.0 | Linting and formatting |
| `mypy` | >=1.0 | Type checking |
| `types-PyYAML` | >=6.0 | Type stubs for PyYAML |

### System Dependencies

None — pure Python, no external binaries required.

---

## Package Structure

```
project-guide/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── requirements-dev.txt                # Dev/test deps for pyve testenv
├── .github/workflows/
│   ├── ci.yml                          # Lint + test on push
│   ├── test.yml                        # Multi-platform test matrix
│   ├── publish.yml                     # PyPI publish on release
│   └── deploy-docs.yml                 # MkDocs deployment
├── project_guide/
│   ├── __init__.py                     # Package exports
│   ├── __main__.py                     # python -m project_guide
│   ├── version.py                      # Single source of truth: __version__
│   ├── exceptions.py                   # Custom exception hierarchy
│   ├── config.py                       # Config dataclass + YAML I/O
│   ├── metadata.py                     # .metadata.yml parser + variable resolution
│   ├── render.py                       # Jinja2 rendering pipeline
│   ├── sync.py                         # File sync: hash comparison, copy, backup
│   ├── cli.py                          # Click CLI commands
│   └── templates/
│       └── project-guide/              # Bundled template tree (copied on init)
│           ├── .metadata.yml
│           ├── README.md
│           ├── developer/              # Developer reference docs
│           └── templates/
│               ├── go.md               # Jinja2 entry point template
│               ├── modes/              # Mode templates + header partials
│               └── artifacts/          # Artifact structure templates
└── tests/
    ├── test_cli.py                     # CLI command tests (~35K)
    ├── test_sync.py                    # Sync logic tests (~13K)
    ├── test_integration.py             # End-to-end workflow tests
    ├── test_render.py                  # Rendering pipeline tests
    ├── test_metadata.py                # Metadata parsing tests
    ├── test_config.py                  # Config round-trip tests
    └── test_purge.py                   # Purge command tests
```

---

## Filename Conventions

| Pattern | Purpose |
|---------|---------|
| `<mode-name>-mode.md` | Mode template (e.g., `code-direct-mode.md`, `scaffold-project-mode.md`) |
| `_header-*.md` | Jinja2 partials included by mode templates |
| `.metadata.yml` | Hidden config/metadata files (dotfile prefix) |
| `*.bak.<timestamp>` | Backup files created by forced updates |
| `go.md` | Rendered entry point (gitignored) |

---

## Key Component Design

### Module: `cli.py` (695 lines)

**Purpose**: All Click CLI commands.

**Commands:**

| Command | Description |
|---------|-------------|
| `init` | Copy template tree, render `go.md`, create config, update `.gitignore` |
| `mode [name]` | Switch mode and re-render `go.md`, or list available modes |
| `status` | Grouped status: Mode, Guide, Files (with `--verbose`) |
| `update` | Hash-based sync with prompt/force/dry-run |
| `override` | Lock a file from updates |
| `unoverride` | Remove a file lock |
| `overrides` | List all locked files |
| `purge` | Remove all project-guide files with confirmation |

**Key functions:**
- `_ensure_gitignore_entry(target_dir)` — adds `go.md` and `*.bak.*` patterns
- `_copy_template_tree(src, dest, force)` — recursive copy preserving structure
- `_migrate_config_if_needed()` — renames legacy `.project-guides.yml`

### Module: `config.py` (138 lines)

**Purpose**: Configuration model and YAML I/O.

**Data classes:**
- `FileOverride` — reason, locked_version, last_updated
- `Config` — version, installed_version, target_dir, metadata_file, current_mode, test_first, pyve_version, project_name, metadata_overrides, overrides

`project_name` is populated at `init` via a four-level resolution chain (CLI `--project-name` flag → `PROJECT_GUIDE_PROJECT_NAME` env var → `pyproject.toml` `[project].name` via `runtime._detect_project_name_from_pyproject()` → `Path.cwd().name`) and persists thereafter. It flows into `archive-stories` as the authoritative source for the fresh `stories.md` header.

**Key behavior:**
- `Config.load()` / `Config.save()` — YAML round-trip
- Schema version guard: `Config.load()` compares `data['version']` against module-level `SCHEMA_VERSION` and raises `SchemaVersionError(direction="older"|"newer")` on mismatch. `SchemaVersionError` subclasses `ConfigError` so existing handlers still catch it. `cli.py:update` treats it specially: on `"older"` it directs the user at `init --force`; on `"newer"` it instructs them to upgrade the package. `cli.py:init` performs the actual `.project-guide.yml.bak.<timestamp>` backup when `--force` is used on an existing config — that is the single destructive-overwrite site.
- Override management: `is_overridden()`, `add_override()`, `remove_override()`
- Defaults: `target_dir="docs/project-guide"`, `metadata_file=".metadata.yml"`, `current_mode="default"`, `test_first=False`, `pyve_version=None`, `metadata_overrides={}`

### Module: `metadata.py`

**Purpose**: Parse `.metadata.yml` with two-pass variable resolution.

**Data classes:**
- `ModeDefinition` — name, info, description, sequence_or_cycle, generation_type, mode_template, next_mode, artifacts, files_exist
- `Metadata` — common dict + list of ModeDefinition

**Key behavior:**
- `load_metadata(path)` — load YAML, resolve `{{var}}` placeholders in common block against themselves, then resolve all mode fields against common
- `Metadata.get_mode(name)` — lookup by name, raises `MetadataError` if not found
- `Metadata.list_mode_names()` — return all mode names
- `_apply_metadata_overrides(metadata, overrides)` — in-place patch of mode fields from `metadata_overrides` config dict; raises `MetadataError` on unknown mode name or non-patchable field; called at every `load_metadata()` call site

### Module: `render.py`

**Purpose**: Jinja2 rendering pipeline.

**Key function:**
- `render_go_project_guide(template_dir, mode, metadata, output_path, pyve_installed, pyve_version)` — configures Jinja2 environment with `templates/` as the loader path, resolves mode template path (strips prefix to get relative path within `modes/`), builds context from mode fields + metadata common vars + `target_dir` + `pyve_installed` + `pyve_version` + `project_essentials` + `pyve_essentials`, renders `go.md` template, writes output

**Helpers:**
- `_read_project_essentials(spec_artifacts_path)` — reads `docs/specs/project-essentials.md` (project-owned); returns `""` when missing, whitespace-only, or `spec_artifacts_path` is `None`. Empty string causes `_header-common.md` to omit the `## Project Essentials` wrapper.
- `_read_pyve_essentials(templates_subdir, pyve_installed)` — reads `templates/artifacts/pyve-essentials.md` from the bundled template tree (package-versioned, not project-owned); returns `""` when `pyve_installed=False`, file missing, or whitespace-only. When non-empty, `_header-common.md` renders it as a `### Pyve Essentials` subsection under `## Project Essentials`. This is auto-render, not a one-shot merge — improvements flow to every project on the next render.

**Jinja2 configuration:**
- Loader: `FileSystemLoader` on `templates/` subdirectory only
- `keep_trailing_newline=True`
- `_LenientUndefined` — undefined variables render as `{{ var_name }}` instead of erroring (preserves LLM instruction placeholders)

### Module: `sync.py` (250 lines)

**Purpose**: File synchronization using content-hash comparison.

**Key functions:**
- `get_all_file_names()` — discover tracked files via `rglob` patterns (`*.md`, `*.md.j2`, `*.yml`, `.*.yml`), returns deduplicated sorted list
- `file_matches_template(file_path, file_name)` — SHA-256 hash comparison between installed file and bundled template
- `copy_file(file_name, target_dir, force)` — copy from package to target
- `backup_file(file_path)` — create `.bak.<timestamp>` copy
- `apply_file_update(file_name, config, make_backup)` — backup + copy
- `sync_files(config, files, force, dry_run)` — main sync loop returning (updated, skipped, current, missing, modified) tuples

**Key design decision:** `sync_files` uses `file_matches_template()` as the sole freshness check. Version numbers are not used to determine whether a file needs updating. This means a package version bump that doesn't change a specific template won't flag that file as stale.

### Module: `exceptions.py` (52 lines)

**Exception hierarchy:**
```
ProjectGuidesError (base)
├── ConfigError
│   └── SchemaVersionError
├── SyncError
├── ProjectFileNotFoundError
├── MetadataError
└── RenderError
```

---

## Data Models

### Config (`FileOverride`)

```python
@dataclass
class FileOverride:
    reason: str
    locked_version: str
    last_updated: date
```

### Config (`Config`)

```python
@dataclass
class Config:
    version: str = "2.0"
    installed_version: str = ""
    target_dir: str = "docs/project-guide"
    metadata_file: str = ".metadata.yml"
    current_mode: str = "default"
    test_first: bool = False
    pyve_version: str | None = None
    metadata_overrides: dict[str, dict] = field(default_factory=dict)
    overrides: dict[str, FileOverride] = field(default_factory=dict)
```

### Metadata (`ModeDefinition`)

```python
@dataclass
class ModeDefinition:
    name: str
    info: str
    description: str
    sequence_or_cycle: str
    generation_type: str = "document"
    mode_template: str = ""
    next_mode: str | None = None
    artifacts: list[dict] = field(default_factory=list)
    files_exist: list[str] = field(default_factory=list)
```

---

## Configuration

### Precedence

1. Command-line flags (highest priority)
2. `.project-guide.yml` in project root
3. `.metadata.yml` in target directory
4. Package defaults (lowest priority)

### `.gitignore` Management

`init` adds under a `# project-guide` comment:
```
docs/project-guide/go.md
docs/project-guide/**/*.bak.*
```

---

## CLI Design

### Entry Point

```toml
[project.scripts]
project-guide = "project_guide.cli:main"
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (missing config, invalid arguments, abort) |
| 2 | File I/O error (permission denied, render failure) |
| 3 | Configuration error (invalid YAML, schema mismatch) |

### Output Styling

- **Bold**: section labels (`Mode:`, `Guide:`, `Files:`)
- **Cyan**: mode name, guide path
- **Green**: success markers, current counts
- **Yellow**: warnings, overridden counts, needs-updating counts
- **Red**: errors, missing counts
- **Dim**: action prompts, hints

---

## Cross-Cutting Concerns

### Error Handling

Fail fast with actionable messages:
- Missing config → "Run 'project-guide init' first."
- Render failure → "Run 'project-guide status' to check for missing files." + "Run 'project-guide update' to restore missing templates."
- Invalid file name → list available files

### File Safety

1. `init` without `--force` → skip existing files
2. `update` without `--force` → prompt for each modified file
3. `update --force` → create `.bak.<timestamp>` backups before overwriting
4. `purge` → confirm unless `--force`
5. Overridden files → skip during update unless `--force`

### Legacy Migration

- `.project-guides.yml` → `.project-guide.yml` (automatic rename on any CLI command)
- v1.x config detection → migration notice in `status` output

---

## Performance Implementation

All operations are file-based on small files (<100KB each). No performance concerns.

- SHA-256 hashing: effectively instant on template-sized files
- Jinja2 rendering: milliseconds
- File discovery: `rglob` on a small directory tree

---

## Testing Strategy

### Test Structure

| File | Focus | Tests |
|------|-------|-------|
| `test_cli.py` | All CLI commands, error paths, output assertions | ~60 |
| `test_sync.py` | Hash comparison, copy, backup, sync logic | ~22 |
| `test_integration.py` | End-to-end workflows | ~6 |
| `test_render.py` | Jinja2 rendering, parametrized mode test | ~20 |
| `test_metadata.py` | YAML parsing, variable resolution | ~9 |
| `test_config.py` | Config round-trip, overrides | ~7 |
| `test_purge.py` | Purge command edge cases | ~5 |

**Total: 129 tests, ~91% coverage**

### Key Test Patterns

- `CliRunner.isolated_filesystem()` for all CLI tests
- `tmp_path` fixture for sync/config unit tests
- `@pytest.mark.parametrize` over all mode names for render regression
- `unittest.mock.patch` for error injection (SyncError, permission denied)
- Windows `encoding="utf-8"` on all `read_text()` calls reading template content

### CI/CD

- **ci.yml**: ruff check + pytest on push
- **test.yml**: Multi-platform matrix (macOS, Linux, Windows) × Python 3.11-3.14
- **publish.yml**: Build + publish to PyPI on GitHub Release
- **deploy-docs.yml**: MkDocs deployment to GitHub Pages

---

## Packaging and Distribution

### PyPI

- **Package name**: `project-guide`
- **License**: Apache-2.0
- **Python requires**: `>=3.11`
- **Build backend**: Hatchling

### Package Data

Templates are included automatically — Hatchling includes all non-Python files under `packages = ["project_guide"]`.

### Console Script

```toml
[project.scripts]
project-guide = "project_guide.cli:main"
```

### Installation

```bash
pip install project-guide
```
