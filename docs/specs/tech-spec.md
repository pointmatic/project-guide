# tech-spec.md — project-guide (Python)

This document defines **how** the `project-guide` project is built — architecture, module layout, dependencies, data models, API signatures, and cross-cutting concerns.

For requirements and behavior, see [`features.md`](features.md). For the implementation plan, see [`stories.md`](stories.md). For project-specific must-know facts (workflow rules, architecture quirks, hidden coupling), see [`project-essentials.md`](project-essentials.md) — `plan_tech_spec` populates it after this document is approved. For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

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
├── requirements-dev.txt                # Dev/test deps for the pyve test env
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
| `go.md` | Rendered entry point (unignored but untracked-by-default as of P.o / v2.8.0) |

---

## Key Component Design

### Module: `cli.py` (695 lines)

**Purpose**: All Click CLI commands.

**Commands:**

| Command | Description |
|---------|-------------|
| `init` | Copy template tree, render `go.md`, create config, update `.gitignore` |
| `mode [name]` | Switch mode and re-render `go.md`, or list available modes |
| `archive-stories` | Archive `stories.md` to `.archive/stories-vX.Y.Z.md` and re-render a fresh one |
| `bump-version <X.Y.Z>` | Update `pyproject.toml`, `<package>/version.py`, and seed a `CHANGELOG.md` heading |
| `status` | Grouped status: Mode, Guide, Files (with `--verbose`) |
| `update` | Hash-based sync with prompt/force/dry-run |
| `heal` | Silent-when-clean drift repair with create-missing semantics; fires automatically before every other command via the group-level auto-hook |
| `git-push [BRANCH_NAME]` | Wrap gitbetter's `git-push` with a commit message derived from the last `[Done]` story heading; shells out via `shutil.which` + `subprocess.run`, propagates child exit code |
| `override` | Lock a file from updates |
| `unoverride` | Remove a file lock |
| `overrides` | List all locked files |
| `purge` | Remove all project-guide files with confirmation |

**Key functions:**
- `_ensure_gitignore_entry(target_dir)` — writes the canonical `# project-guide` block: ignore everything under `target_dir` except `go.md` (negation-free explicit-list form as of P.l / v2.7.1, dynamically enumerated from the bundled template root). Idempotent. Recognized prior blocks (pre-P.d `.bak.*`-only form, v2.6.0 4-line form, v2.6.1/v2.7.0 3-line negation form, legacy `<target>/go.md` line) are rewritten cleanly to the v2.7.1 explicit-list form; foreign hand-customized content under a `# project-guide` header is left alone with a stderr warning. The recognized-line check is `_is_recognized_block_line(line, target_dir)` — accepts anything anchored at `/<target>/` plus the legacy negation entries.
- `_copy_template_tree(src, dest, force)` — recursive copy preserving structure
- `_migrate_config_if_needed()` — renames legacy `.project-guides.yml`
- `_apply_heal(config, config_path)` — apply pending template syncs and re-render `go.md`. Sets `PROJECT_GUIDE_HEALING=1` in `os.environ` before doing any writes so nested subprocess invocations don't re-enter the auto-hook.
- `_run_pre_invoke_hook()` — group-level auto-heal hook (Story P.b/c). Calls `should_skip_input()` to honor the `--no-input` contract via env / TTY signals; silent when no drift; prompts on drift in interactive mode; auto-yes + `Auto-healing N templates under --no-input.` stderr notice in skip-input mode.
- `HealGroup(click.Group)` — custom Click group whose overridden `main()` runs `_run_pre_invoke_hook()` before `super().main()`, so `--help` and `--version` (eager flags that would otherwise short-circuit during arg parsing) still trigger the hook.
- `_get_committed_story_ids()` — parses `git log --pretty=%s` and extracts story IDs from any subject line whose prefix matches `<id>: ` (regex `^([A-Z]\.[a-z]+):\s`). Returns an empty set on `git`-not-found, non-git cwd, or empty history. Used by the `git-push` wrapper to decide which `[Done]` stories are uncommitted.
- `_resolve_spec_artifacts_path()` — best-effort resolver for the `spec_artifacts_path` metadata value used by `git-push` to locate `stories.md`. Falls back to `docs/specs` when config / metadata are unavailable so the wrapper works in projects that haven't yet run `init`.
- `project_guide/stories.py:_read_done_stories()` / `derive_commit_message()` — pure helpers used by `git-push`. `_read_done_stories` returns all `[Done]` headings as `StoryHeading(story_id, title)` tuples in file order; `derive_commit_message` produces the gitbetter-ready subject `"<id>: <transformed title>"` (backticks → single quotes, double quotes → single quotes, single quotes pass through, colon preserved).

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

`init` writes a canonical **negation-free explicit-list** block under a `# project-guide` comment header (Story P.d → P.j → P.l). For the default install layout the block is:

```
# project-guide
/docs/project-guide/.metadata.yml
/docs/project-guide/README.md
/docs/project-guide/developer/
/docs/project-guide/templates/
/docs/project-guide/**/*.bak.*
```

The list is **dynamically generated** at write time by enumerating the bundled template root (`_get_package_template_dir()`) and emitting one anchored line per top-level child other than `go.md`. New top-level files or subdirectories added in future releases are picked up automatically — no manual writer update required.

**Why this shape:** every file under `target_dir` except `go.md` is bundled static data that `heal` (FR-14) repopulates on first invocation, so tracking the full template tree in the consumer repo would just add ~35 files of noise to `git status` and PR reviews. `go.md` itself **must remain non-gitignored** because IDE-integrated LLMs (Cursor, Claude Code, etc.) typically hide gitignored files from the LLM's view, and the LLM's instruction to `Read docs/project-guide/go.md` requires the file to be visible.

**Visibility vs. tracking (clarified in P.o / v2.8.0).** Two separate properties are at play:

- **Gitignore status** governs IDE-LLM visibility — the file must stay unignored for Cursor / Claude Code / VS Code-fork tooling to see it.
- **Tracking status** governs version-control churn and branch-switch safety — a tracked `go.md` appears in every mode-switch diff and (more dangerously) causes `git switch` aborts when a feature branch's tip has a different `go.md` than its base.

Pre-v2.8.0, `go.md` was tracked by historical accident. v2.8.0 (Story P.o) flips it to **untracked-but-unignored**: `heal` emits a stderr warning with a copyable `git rm --cached docs/project-guide/go.md && git commit` command when it detects `go.md` in the consumer's index; `init` emits a stderr note that fresh installs leave the file untracked. The gitignore block itself is unchanged from v2.7.1.

**Why untracked-by-default?** Field-evidence trigger: a consumer (pyve) pushed `update/project-guide-v2.7.1` as a feature branch, the PR merged on GitHub, and the post-merge `git switch main` aborted with `error: The following untracked working tree files would be overwritten by checkout: docs/project-guide/go.md` — pyve's main had `go.md` from an earlier `git add`, the feature-branch tip did not, and git refused the switch. Re-rendering `go.md` from `.project-guide.yml:mode` at heal-time doesn't help here because git aborts *before* any `project-guide` command runs. Collapsing to untracked-by-default removes the conflict entirely: git does not gate `switch` on untracked-unignored files.

**Why warn-don't-auto-fix.** `heal` warns when `go.md` is tracked but does not run `git rm --cached` itself. Project-guide writes its own files (templates, `.project-guide.yml`, the gitignore block) but does not edit the consumer's index or HEAD — same wrapper-initiates-git-ops constraint that bounded the P.k `git-push` wrapper. The consumer applies the one-line migration on their own schedule.

**Why explicit list instead of `**` + `!go.md`?** The cleaner negation form (used in v2.6.0–v2.7.0) is correct per the `.gitignore` spec, but several IDE-integrated tools (Cursor, parts of the VS Code fork ecosystem, certain LSP-based search backends) implement a subset of `.gitignore` semantics that does **not** honor re-include negation — they apply the broad `**` rule, hide `go.md` from @-mention search, and defeat the IDE-LLM-visibility constraint the policy is trying to enforce. P.l (v2.7.1) switched to the explicit-list form so no negation is required; tools with simplistic parsers handle anchored line-per-entry patterns reliably. Future maintainers: do **not** "simplify" back to `**` + `!` — the regression is invisible from git's perspective but breaks the IDE workflow that motivates tracking `go.md` in the first place.

**Why the trailing `<target>/**/*.bak.*` line?** Defensive coverage for backup files that `apply_file_update()` writes next to top-level synced files (e.g., `<target>/README.md.bak.<timestamp>`). Subdirectory backups are already covered by the per-directory entries; this catch-all is a simple recursive glob with no negation, so the IDEs handle it cleanly.

**Existing-block detection:** `_ensure_gitignore_entry()` is idempotent. The recognized-line predicate `_is_recognized_block_line(line, target_dir)` accepts any line starting with `/<target>/` (the v2.7.1+ anchor) plus the legacy negation-form lines (`<target>/**`, `!<target>/go.md`, `<target>/**/*.bak.*`, `<target>/go.md`). A block whose every non-empty line satisfies the predicate is rewritten cleanly to the current canonical form; any line that fails the predicate marks the block as hand-customized — the writer leaves it untouched and emits a stderr warning. A `.gitignore` with no `# project-guide` header gets the canonical block appended (separated by a blank line).

**Migration:** `project-guide init --force` rewrites prior blocks (pre-P.d `.bak.*`-only, v2.6.0 4-line, v2.6.1/v2.7.0 3-line) to the v2.7.1 explicit-list form in place. `git rm --cached` remains the manual cleanup for files already tracked under the old policy.

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

### Machine-quiet commands (`init`, `update`, `purge`)

When **`--quiet` / `-q`** is set and the command **succeeds**, **`stdout` stays empty** so wrappers (pyve, CI logs) are not polluted. Diagnostics use **`stderr`**: Click handlers pass **`err=True`** for errors, render/update warnings, overridden-file notices, config-backup notices on **`init --force`**, and optional purge skip hints.

Commands whose UX remains interactive (`mode`, `status`, etc.) do not accept `--quiet` unless extended explicitly later.

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

### External CLI Dependencies (Story P.k pattern)

`git-push` is the first `project-guide` subcommand that **depends on an external CLI being on PATH** (gitbetter's `git-push` binary). Future workflow-integration commands (potential `git-tag`, `git-rebase`, etc.) should follow the same pattern:

1. **Discover** via `shutil.which(name)`. If `None`, exit 1 with stderr that names the missing tool and the canonical install command. Never silently fall back to a degraded behavior.
2. **Invoke** via `subprocess.run(argv, check=False)` with **no captured output** so the external tool inherits the parent's stdin/stdout/stderr (interactive flows like prompts and progress reporting must reach the developer unaltered).
3. **Propagate** the child's exit code with `sys.exit(result.returncode)`. The wrapper's own exit semantics are a passthrough — the external tool's reject/recovery semantics are the source of truth, not the wrapper's.
4. **Tests** mock both `shutil.which` (to control discovery) and `subprocess.run` (to control the child's behavior and capture argv). See `tests/test_cli.py::test_git_push_*` for the reference test shape.

This deliberately keeps each wrapper a thin convenience layer rather than a parallel implementation. The tested invariants are: discovery error message, argv shape (including positional passthrough), and exit-code propagation. Nothing else.

### Auto-Heal Group Hook (Phase P)

Every `project-guide` invocation runs the heal drift-detection + prompt path before dispatching the requested subcommand. This is implemented as a custom `HealGroup(click.Group)` whose overridden `main()` calls `_run_pre_invoke_hook()` before delegating to `super().main()`. Running before `super().main()` is deliberate: it places the hook **ahead of `make_context` / arg parsing**, which is what makes the hook fire even for `--help` and `--version` (eager flags that would otherwise short-circuit before any subcommand or group body runs).

**Recursion guard.** `_apply_heal()` sets `PROJECT_GUIDE_HEALING=1` in `os.environ` before any write. The hook reads this env var first and returns silently when set, so a `project-guide` subprocess spawned by another `project-guide` invocation does not re-enter and re-prompt.

**Skip conditions:** the hook returns silently when `PROJECT_GUIDE_HEALING=1` is set, when `.project-guide.yml` is absent, when the config fails to load (schema mismatch, parse error), or when `sync_files()` raises `SyncError`. In all these cases the original subcommand is responsible for surfacing whatever guidance is appropriate; the hook does not duplicate it.

**Decline does not block.** When the user answers `n` to the prompt, the hook returns and the original subcommand still runs. Refusing the heal is the user's choice; it is not an error condition.

**Skip-input contract.** The hook calls `should_skip_input()` (no flag, since the hook runs before per-subcommand args are parsed) so it honors `PROJECT_GUIDE_NO_INPUT`, `CI=1`, and non-TTY stdin. Under skip-input mode the prompt is replaced with the `Auto-healing N templates under --no-input.` stderr notice and auto-yes — see FR-8.

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
