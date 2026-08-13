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
│   ├── stories.py                      # stories.md parsing: [Done] detection, commit-message derivation
│   ├── actions.py                      # archive-stories + version-detection actions
│   ├── runtime.py                      # shared runtime helpers (skip-input, project-name detection)
│   ├── completion.py                   # shell-completion generation, post-processing, rc-file blocks
│   └── templates/
│       └── project-guide/              # Bundled template tree (copied on init)
│           ├── .metadata.yml
│           ├── README.md
│           ├── developer/              # Developer reference docs
│           └── templates/
│               ├── llm_entry_point.md  # Jinja2 entry point template (renders to go.md)
│               ├── modes/              # Mode templates + header partials
│               └── artifacts/          # Artifact structure templates
└── tests/                              # 901 tests across 15 files
    ├── test_cli.py                     # CLI command tests
    ├── test_sync.py                    # Sync logic tests
    ├── test_integration.py             # End-to-end workflow tests
    ├── test_render.py                  # Rendering pipeline tests
    ├── test_metadata.py                # Metadata parsing tests
    ├── test_config.py                  # Config round-trip tests
    ├── test_purge.py                   # Purge command tests
    ├── test_actions.py                 # archive-stories + version-detection actions
    ├── test_stories.py                 # stories.md parsing + commit-message derivation
    ├── test_cross_repo_contract.py     # Pyve-hosting cross-repo contract guards
    ├── test_runtime.py                 # Runtime helpers
    ├── test_archive_stories_mode.py    # archive_stories mode end-to-end
    └── test_completion.py              # completion generation, rc blocks, real-shell checks
```

---

## Filename Conventions

| Pattern | Purpose |
|---------|---------|
| `<mode-name>-mode.md` | Mode template (e.g., `code-direct-mode.md`, `scaffold-project-mode.md`) |
| `_*.md` | Jinja2 partials included by mode templates — `_header-*.md` (per-mode-kind headers) and `_phase-letters.md` (shared phase/story ID rules) |
| `.metadata.yml` | Hidden config/metadata files (dotfile prefix) |
| `*.bak.<timestamp>` | Backup files created by forced updates |
| `go.md` | Rendered entry point (unignored but untracked-by-default as of P.o / v2.8.0) |

---

## Key Component Design

### Module: `cli.py`

**Purpose**: All Click CLI commands.

**Commands:**

| Command | Description |
|---------|-------------|
| `init` | Copy template tree, render `go.md`, create config, update `.gitignore` |
| `mode [name]` | Switch mode and re-render `go.md`, or list available modes |
| `archive-stories` | Archive `stories.md` to `.archive/stories-vX.Y.Z.md` and re-render a fresh one |
| `status` | Grouped status: Mode, Guide, Files (with `--verbose`) |
| `update` | Hash-based sync with prompt/force/dry-run |
| `heal` | Silent-when-clean drift repair with create-missing semantics; fires automatically before every other command via the group-level auto-hook |
| `git-push [BRANCH_NAME]` | Wrap gitbetter's `git-push` with a commit message derived from the last `[Done]` story heading; shells out via `shutil.which` + `subprocess.run`, propagates child exit code |
| `git-commit [BRANCH_NAME]` | Identical interface/behavior to `git-push` (both share `_run_gitbetter_wrapper`), but invokes gitbetter's `git-commit` for a local commit instead of a push |
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
- `_run_gitbetter_wrapper(tool_name, branch_name, no_input, keep=False, amend=False)` — shared body of the `git-push` / `git-commit` commands (Story R.a); `tool_name` selects the gitbetter binary (`"git-push"` / `"git-commit"`) and drives every tool-naming message (not-on-PATH error, bundle-decline hint, out-of-sequence manual-resolution hint). `keep` / `amend` are Story R.q's gitbetter flag pass-throughs; `amend` short-circuits to `_run_amend` before any message derivation.
- `_get_committed_story_ids()` — parses `git log --pretty=%s` through `parse_committed_ids_from_subject` (Story P.u, which retired the single-regex form) and returns `(committed_ids, duplicates)`, the second mapping any ID seen in 2+ subjects to those subjects. Returns `(set(), {})` on `git`-not-found, non-git cwd, or empty history. Used by the gitbetter wrappers to decide which `[Done]` stories are uncommitted.
- `_resolve_spec_artifacts_path()` — best-effort resolver for the `spec_artifacts_path` metadata value used by the gitbetter wrappers to locate `stories.md`. Falls back to `docs/specs` when config / metadata are unavailable so the wrappers work in projects that haven't yet run `init`.
- `project_guide/stories.py:_read_done_stories()` / `derive_commit_message()` — pure helpers used by the gitbetter wrappers. `_read_done_stories` returns all `[Done]` headings as `StoryHeading(story_id, title)` tuples in file order; `derive_commit_message` produces the gitbetter-ready subject `"<id>: <transformed title>"` (backticks → single quotes, double quotes → single quotes, single quotes pass through, colon preserved).
- **Phase Q additions (named for navigation; the contracts live in `project-essentials.md`):** `_query_pyve_provision_status()` / `_warn_if_local_install_under_pyve()` / `_provision_pyve_hosting()` (Subphase Q-4 readiness-gated local-install warning); `_get_current_branch()` / `_presume_committed_on_branch()` (Q.u branch-aware squash-merge presumption for `git-push`); `_prompt_commit_out_of_sequence()` (Q.p single-story out-of-sequence opt-in) — all shared by both gitbetter wrappers. The git-log subject parser is `parse_committed_ids_from_subject()` in `stories.py` (P.u, superseding the single-regex form); `stories.py`'s `_STORY_RE` recognizes `#{3,5}` heading depths (Q.v).

### Module: `config.py`

**Purpose**: Configuration model and YAML I/O.

**Data classes:**
- `FileOverride` — reason, locked_version, last_updated
- `Config` — version, installed_version, target_dir, metadata_file, current_mode, test_first, pyve_version, pyve_installed, project_name, metadata_overrides, overrides

`project_name` is populated at `init` via a four-level resolution chain (CLI `--project-name` flag → `PROJECT_GUIDE_PROJECT_NAME` env var → `pyproject.toml` `[project].name` via `runtime._detect_project_name_from_pyproject()` → `Path.cwd().name`) and persists thereafter. It flows into `archive-stories` as the authoritative source for the fresh `stories.md` header, which is why that command can rebuild a header even when the archived `stories.md` had none to parse. `cli.py:archive_stories_cmd` prints a **drift warning** on stderr when `Path.cwd().name != config.project_name` but does not fail — a renamed directory is a plausible, recoverable state, not an error.

**Key behavior:**
- `Config.load()` / `Config.save()` — YAML round-trip
- Schema version guard: `Config.load()` compares `data['version']` against module-level `SCHEMA_VERSION` and raises `SchemaVersionError(direction="older"|"newer")` on mismatch. `SchemaVersionError` subclasses `ConfigError` so existing handlers still catch it. `cli.py:update` treats it specially: on `"older"` it directs the user at `init --force`; on `"newer"` it instructs them to upgrade the package. `cli.py:init` performs the actual `.project-guide.yml.bak.<timestamp>` backup when `--force` is used on an existing config — that is the single destructive-overwrite site, so the backup is idempotent (one per refresh) regardless of which entry point triggered it. **No migration registry exists, by design** — YAGNI until there is something to migrate; revisit when a genuinely breaking schema change arrives.
- Override management: `is_overridden()`, `add_override()`, `remove_override()`
- Pyve detection: `record_pyve_detection(detected_version)` — the sticky-true choke point for every automatic update (see the `Config` dataclass section)
- Defaults: `target_dir="docs/project-guide"`, `metadata_file=".metadata.yml"`, `current_mode="default"`, `test_first=False`, `pyve_version=None`, `pyve_installed=False`, `metadata_overrides={}`. `pyve_installed` is the one field whose *load* default differs from its dataclass default: an absent key reads as `pyve_version is not None`, preserving pre-R-2 behavior for existing configs

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

### Module: `sync.py`

**Purpose**: File synchronization using content-hash comparison.

**Key functions:**
- `get_all_file_names()` — discover tracked files via `rglob` patterns (`*.md`, `*.md.j2`, `*.yml`, `.*.yml`), returns deduplicated sorted list
- `file_matches_template(file_path, file_name)` — SHA-256 hash comparison between installed file and bundled template
- `copy_file(file_name, target_dir, force)` — copy from package to target
- `backup_file(file_path)` — create `.bak.<timestamp>` copy
- `apply_file_update(file_name, config, make_backup)` — backup + copy
- `sync_files(config, files, force, dry_run)` — main sync loop returning (updated, skipped, current, missing, modified) tuples

**Key design decision:** `sync_files` uses `file_matches_template()` as the sole freshness check. Version numbers are not used to determine whether a file needs updating. This means a package version bump that doesn't change a specific template won't flag that file as stale.

### Module: `exceptions.py`

**Exception hierarchy:**
```
ProjectGuidesError (base)
├── ConfigError
│   └── SchemaVersionError
├── SyncError
├── ProjectFileNotFoundError
├── MetadataError
├── RenderError
├── ActionError
└── CompletionError
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
    version: str = "2.0"                 # config schema version (SCHEMA_VERSION)
    installed_version: str = ""
    target_dir: str = "docs/project-guide"
    metadata_file: str = ".metadata.yml"
    current_mode: str = "default"
    test_first: bool = False
    pyve_version: str | None = None      # bare "3.2.2"; legacy raw line still reads
    pyve_installed: bool = False         # the render gate — not derived from the above
    project_name: str = ""
    metadata_overrides: dict[str, dict] = field(default_factory=dict)
    overrides: dict[str, FileOverride] = field(default_factory=dict)
```

**`pyve_installed` is deliberately not derived from `pyve_version`** (Subphase R-2). The two answer different questions — "should the Pyve guidance render?" versus "which pyve was seen?" — and deriving the first from the second is what turned a single failed `pyve --version` probe into the permanent loss of ~80 lines of guardrail from every rendered `go.md`. A config written before the field existed defaults it to `pyve_version is not None`, so upgrading changes no project's behavior; a key that *is* present always wins, which is how a hand-edited opt-out survives a load.

**Sticky-true helper.** Every *automatic* detection result flows through one method:

```python
def record_pyve_detection(self, detected_version: str | None) -> bool:
    """Fold a detection result in. Returns whether anything changed."""
```

It may set `pyve_installed` to `True` and never to `False`: a failed probe returns `False` (nothing changed) and leaves both fields alone, because detection fails for reasons unrelated to whether pyve is present — an un-rehashed `PATH`, a slow first run, a sandbox. The boolean return lets callers skip a pointless config write, and is what `update` reads to decide whether a re-render is owed. `init` is the one site that bypasses the helper: it may record a miss as `False`, having no prior observation to overwrite.

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

`completion install` / `uninstall` accept `--quiet` (host tools such as pyve shell out to them during provisioning); foreign-block warnings still reach stderr. `completion show` accepts **neither** `--quiet` (its stdout *is* the payload) **nor** `--no-input` (it never prompts). `completion status` accepts neither for the same reasons, and signals through its exit code: 0 absent-or-current, 1 stale/partial/damaged, 2 I/O error.

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

### Shell Completion Installation (Subphase R-1)

`completion.py` owns generation, post-processing, and the on-disk artifacts. The design is driven by one finding: **Click's generated callback resolves the bare command name through `PATH` at completion time**, long after the rc block ran. Baking an absolute path into the rc block fixes only the generation call. So project-guide post-processes Click's output rather than emitting it verbatim.

**Post-processing** (`postprocess_script`) — two line-local rewrites per shell, never a blanket substitution of the command name (`#compdef project-guide`, `compdef … project-guide`, and `complete -F … project-guide` all register against the name the user *types*):

| Shell | Rewrites |
|---|---|
| zsh | replace the `(( ! $+commands[…] ))` `PATH` guard with `[[ -x <bin> ]] \|\| return 1`; substitute `<bin>` for the bare name in the callback |
| bash | substitute `<bin>` for `$1` in the callback; **insert** `[[ -x <bin> ]] \|\| return 1` above it — bash ships no guard, and without one a stale `--bin` prints `env: …: No such file or directory` on every TAB |

Applied **only when `--bin` resolves to an absolute path**: the baked guard is a filesystem test, so a bare-name fallback would test a file relative to `$PWD`. On that fallback Click's script is emitted verbatim.

`apply_bash_compat` is separate and applies **regardless** of `--bin`, because it fixes a defect in Click's template rather than in binary resolution: `complete -o nosort -F …` is bash ≥ 4.4, and on bash 3.2 the whole line fails so *nothing* registers. The line is rewritten to `complete -o nosort … 2>/dev/null || complete …`, keeping Click's ordering on modern bash and registering on 3.2.

**No Click version pin.** Each substitution must match **exactly once** or `CompletionError` is raised naming the failed pattern. Click's templates were byte-stable across 8.1.8 → 8.4.x; a future template change becomes a loud failure at generation time rather than a silently-unmodified script.

**Two install routes.** One generator serves both — Click's `zsh_eval_context[-1] == loadautofunc` branch picks the right registration path — so the routes differ only in where the bytes land:

- **bash** — the script is written **inline** into the sentinel block. Nothing is executed at shell startup (no subprocess per shell), and a stale install cannot print.
- **zsh** — the script goes to an `fpath` autoload file named `_project-guide` (default `$XDG_DATA_HOME/project-guide/zsh-completions`, `--dir` to override), and the rc block only wires it up.

**The zsh bootstrap** (`build_zsh_bootstrap`) satisfies three requirements the obvious two-liner misses:

```zsh
if [[ -r <dir>/_project-guide ]]; then
  fpath=(<dir> $fpath)
  if (( $+functions[compdef] )); then
    autoload -Uz _project-guide && compdef _project-guide project-guide
  else
    autoload -Uz compinit && compinit -i
  fi 2>/dev/null
fi
```

1. The outer `[[ -r ]]` keeps a half-uninstalled state inert — a `compdef` registered against a deleted file defers its failure to TAB time.
2. The `else` branch covers `compinit` never having run (the original field defect).
3. The `if` branch covers `compinit` having **already** run — the common case, since the block lands at the end of `~/.zshrc` after oh-my-zsh. `fpath` entries added after `compinit` are never scanned; measured against `$_comps`, which stays unset. Re-running `compinit` was rejected as expensive and as overriding a configuration the user chose.

**rc-file block machinery.** Blocks are bracketed by an exact sentinel pair (`# >>> project-guide completion >>>` / `# <<< project-guide completion <<<`) and carry a version stamp. `install_block` replaces an existing block **where it sits** rather than moving it to the tail; `remove_block` reclaims the blank separator it inserted, but only when that blank is genuinely adjacent slack, so `install` → `uninstall` round-trips byte-for-byte. Every content-changing write is preceded by a `.bak.<timestamp>` copy.

**Ours-vs-foreign** mirrors `_ensure_gitignore_entry()`: content project-guide did not write is reported, never edited. The **one sanctioned exception** is pyve's legacy block, bounded twice — by pyve's exact header (`PYVE_SENTINEL_START`; the *closing* sentinel is byte-identical to ours, so the blocks are told apart by header alone) and by `_is_pyve_generated`, which requires every body line to be plausibly pyve's output. A hand-edited pyve block is foreign again. Adoption replaces in place because pyve inserts its block **above** SDKMan's must-be-last marker; appending ours at the tail would move the wiring past it.

**Inspection** (`inspect_shell` → `ShellStatus`) reports `absent` / `installed` / `stale` / `partial` / `damaged`. Staleness uses `os.access(bin, os.X_OK)` — the *same* predicate the installed script bakes in, so `status` and the shell cannot disagree. For zsh the autoload directory is read out of the installed `fpath` line rather than assumed, since the shell obeys the rc file. `_warn_if_completion_stale` consumes this from the pre-invoke hook and warns (never repairs) on stale and partial.

### Host-supplied facts (the `--bin` / `--pyve-version` / `--project-name` pattern)

Three flags across two subphases are the same idea, and reading them as one prevents each new instance from being re-litigated:

> When a host tool knows a fact about the environment **with certainty** and project-guide can only *guess* at it, accept the fact as an input. project-guide keeps the decision; the host supplies the input.

| Flag | Env var | The fact | What project-guide would otherwise do |
|---|---|---|---|
| `--bin` (R.c) | — | which binary the completion callback should invoke | resolve `argv[0]`, then guess via `PATH` |
| `--pyve-version` (R.k) | `PYVE_VERSION` | which pyve is running project-guide | shell out to `pyve --version` |
| `--project-name` (N.s) | `PROJECT_GUIDE_PROJECT_NAME` | what the project is called | read `pyproject.toml`, then fall back to the directory name |

Shared properties, each of which is load-bearing rather than incidental:

1. **Last-resort detection, evaluated lazily.** The chain is always *flag → env var → detection*, and the detection link is only reached when the earlier ones are empty. For `--pyve-version` this is the difference between one subprocess and none, which is why the resolution is hand-written rather than routed through `_resolve_setting` (whose `default` argument is evaluated eagerly).
2. **Blank means "not supplied", not "the empty value".** A host interpolating an unset shell variable yields `""`; treating that as an answer would record a useless value *and* skip the detection that would have found the real one.
3. **Supplied values are not validated.** These fields record an observation, not a constraint. Refusing a value the host asserts about *itself* would be project-guide second-guessing the only component that knows for certain — and the validation would inevitably lag the host's own format changes. **Normalizing is not validating** (R.n): `--pyve-version "pyve version 3.2.2"` is stored as `3.2.2` so the field has one shape regardless of who wrote it, but nothing is rejected and nothing raises — a value with no recognizable version token is stored exactly as given.
4. **project-guide still owns the consequence.** `--bin` does not decide whether to post-process (absoluteness does); `--pyve-version` does not decide whether the guidance renders (`pyve_installed` does). The host supplies a fact, never a decision.

**Where the pattern deliberately stops.** `--pyve-version` is `init`-only. Later changes are handled by re-detection at the `update` / `mode` refresh sites, not by asking the host to re-assert the fact on every invocation. And `--project-name` is *not* elevated to other commands: identity is a stable fact deliberately changed, environment is a fact that changes on its own, and symmetric flags would imply a symmetry that does not exist.

### External CLI Dependencies (Story P.k pattern)

`git-push` is the first `project-guide` subcommand that **depends on an external CLI being on PATH** (gitbetter's `git-push` binary); `git-commit` (Story R.a) is the second — same gitbetter toolchain, same shape, sharing `_run_gitbetter_wrapper` with only the binary name differing. Future workflow-integration commands (potential `git-tag`, `git-rebase`, etc.) should follow the same pattern:

1. **Discover** via `shutil.which(name)`. If `None`, exit 1 with stderr that names the missing tool and the canonical install command. Never silently fall back to a degraded behavior.
2. **Invoke** via `subprocess.run(argv, check=False)` with **no captured output** so the external tool inherits the parent's stdin/stdout/stderr (interactive flows like prompts and progress reporting must reach the developer unaltered).
3. **Propagate** the child's exit code with `sys.exit(result.returncode)`. The wrapper's own exit semantics are a passthrough — the external tool's reject/recovery semantics are the source of truth, not the wrapper's.
4. **Tests** mock both `shutil.which` (to control discovery) and `subprocess.run` (to control the child's behavior and capture argv). See `tests/test_cli.py::test_git_push_*` and `test_git_commit_*` for the reference test shape.

This deliberately keeps each wrapper a thin convenience layer rather than a parallel implementation. The tested invariants are: discovery error message, argv shape (including positional passthrough), and exit-code propagation. Nothing else.

**The wrapper-value principle** (Subphase R-3) is the test every proposed wrapper feature is measured against:

> The wrapper earns its place by *integration* — reading `stories.md` and `git log` so the developer copies and pastes less. A feature that reads neither does not belong in it; use the bare `gitbetter` command.

This is why `--keep` is a straight pass-through with no project-guide semantics, why `--amend` preserves the previous subject instead of accepting `-m`, and why the staging guard (which needs `stories.md`) is in scope while a general working-tree guard is not.

#### Commit-message derivation

**Single story.** `<id>: <title>`. The colon after the ID is preserved — it is the anchor the already-committed check searches for in `git log --pretty=%s`. Backticks and double quotes in the title become single quotes; single quotes pass through (invocation is `shell=False`, so there is no shell-quoting concern).

**Bundled subject** (`derive_bundle_commit_message`, 2+ uncommitted `[Done]` stories). Per-story tokens joined with `", "`, each `<id>` or `<id>: <version>`; titles joined with `" + "` after the title boundary:

| Case | Shape |
|---|---|
| All versionless | `H.a, H.b, H.c: title1 + title2 + title3` |
| All versioned | `H.j: v0.10.0, H.k: v0.11.0 title1 + title2` (the last token's `: <ver>` doubles as the title boundary) |
| Mixed | `H.a, H.b: v1.2.3, H.c: title1 + title2 + title3` |

The colon rule: a colon precedes a *version* or a *title*, never two bare IDs. The assembled message is trimmed and internal whitespace runs collapse to one space. Title sanitization matches the single-story rules.

**Permissive read, strict emit.** `parse_committed_ids_from_subject` (`stories.py`) recognizes single-ID subjects (bare and the legacy `Story <id>:` form), legacy bundled subjects with no colons, and every canonical form the wrapper emits — while emission produces only the canonical shapes above. The asymmetry is deliberate: historical hand-typed commits must stay recognizable without becoming templates for new ones. The parser inspects **only the ID-prefix shape**; title text is never matched, so a title containing `+` cannot confuse it.

#### Candidate selection

**Header filter.** A `[Done]` story whose body (between its `### Story` heading and the next `### Story` / `## Phase` / `## Future` / EOF) contains **zero** `- [ ]` *and* `- [x]` items is a decorative group-overview header for a sub-numbered cluster, and is filtered out of uncommitted-detection — it has no work to commit. The rule is forgiving on purpose: zero items *of any kind*, not "zero checked items", so a `[Done]` story with all-unchecked items is still a real story (unchecked items are a developer-discipline concern, not a header signal). Scoped to the wrappers — `_read_done_stories` sets `StoryHeading.is_header`, but other consumers such as `status` still count headers in their totals.

**Out-of-sequence partition.** After the header filter, the `[Done]` list in document order must be a clean **committed prefix → uncommitted suffix**. Any uncommitted story whose index precedes the last committed story's index is out-of-sequence. Phase boundaries are not respected; the partition operates on the flat list.

**Squash-merge presumption** (`_presume_committed_on_branch`, and the pure `_presumed_squash_merged_prefix` it shares with the `--amend` guard). Squash merges rewrite commit subjects into PR titles, so earlier `[Done]` stories may not parse from the log at hand even though they shipped. Two heuristics: with an **anchor** (≥1 story parses), presume every story before it merged and run the normal flow on the tail; with **no anchor** and 2+ uncommitted, offer `Commit just the last one? [Y/n]`.

**Destination-aware gate** (Story R.p). Whether the presumption applies is decided by *where the work is going*, not where the developer is standing: a supplied `branch_name` selects it from any checkout. Naming the current branch is not branch work (an ordinary push keeps the strict discipline), and an undeterminable branch stays strict — the mechanism needs a branch to scan and a name to quote. Announcements name the branch **scanned** (the current one); the destination has no log yet.

**`--amend` is a short-circuit, not an inversion** (Story R.q). The wrapper's normal contract is *already-committed → exit 0*; under `--amend` already-committed is the **precondition**, so left alone the wrapper would exit before invoking gitbetter. The temptation is to invert that check and thread a new branch through the derivation flow — the wrong shape, because `--amend` decides no message. It short-circuits instead: refuse under `--no-input` (it force-pushes with `--force-with-lease`, and a history-shape decision is not a CI default), read `git log -1 --pretty=%s` and pass it back verbatim, refuse while a `[Done]` story is uncommitted (gitbetter runs `git add -A` first, so that work would land in the previous commit under the previous message), then invoke. The guard reads the same presumed committed-set as the flow, or it would refuse on every squash-merged feature branch.

The full outcome table — every branch/state combination with its exit code, prompt, and default — is behavior, and lives in [`features.md`](features.md) FR-15.

### Auto-Heal Group Hook (Phase P)

Every `project-guide` invocation runs the heal drift-detection + prompt path before dispatching the requested subcommand. This is implemented as a custom `HealGroup(click.Group)` whose overridden `main()` calls `_run_pre_invoke_hook()` before delegating to `super().main()`. Running before `super().main()` is deliberate: it places the hook **ahead of `make_context` / arg parsing**, which is what makes the hook fire even for `--help` and `--version` (eager flags that would otherwise short-circuit before any subcommand or group body runs).

**Recursion guard.** `_apply_heal()` sets `PROJECT_GUIDE_HEALING=1` in `os.environ` before any write. The hook reads this env var first and returns silently when set, so a `project-guide` subprocess spawned by another `project-guide` invocation does not re-enter and re-prompt.

**Skip conditions:** the hook returns silently when `PROJECT_GUIDE_HEALING=1` is set, when `.project-guide.yml` is absent, when the config fails to load (schema mismatch, parse error), or when `sync_files()` raises `SyncError`. In all these cases the original subcommand is responsible for surfacing whatever guidance is appropriate; the hook does not duplicate it.

**Decline does not block.** When the user answers `n` to the prompt, the hook returns and the original subcommand still runs. Refusing the heal is the user's choice; it is not an error condition.

**Skip-input contract.** The hook calls `should_skip_input()` (no flag, since the hook runs before per-subcommand args are parsed) so it honors `PROJECT_GUIDE_NO_INPUT`, `CI=1`, and non-TTY stdin. Under skip-input mode the prompt is replaced with the `Auto-healing N templates under --no-input.` stderr notice and auto-yes — see FR-8.

**The rule for any new prompt** (added v2.2.1). Every interactive prompt added to a CLI command **must** decide whether to read stdin via `should_skip_input()` (`runtime.py`), and must use `_require_setting()` to fail loudly when a required setting has no default under `--no-input`. The exact failure message and exit code are pinned by `tests/test_cli.py::test_require_setting_contract_exit_code_and_message` — **do not reword that message casually**; downstream tooling (pyve) may cite it. `init` has no prompts today, but the plumbing (`skip_input = should_skip_input(no_input)`) is already in place; the unused local is intentional and carries a `# noqa: F841`.

---

## Performance Implementation

All operations are file-based on small files (<100KB each). No performance concerns.

- SHA-256 hashing: effectively instant on template-sized files
- Jinja2 rendering: milliseconds
- File discovery: `rglob` on a small directory tree

---

## Testing Strategy

### Test Structure

| File | Focus |
|------|-------|
| `test_cli.py` | All CLI commands, error paths, output assertions |
| `test_sync.py` | Hash comparison, copy, backup, sync logic |
| `test_integration.py` | End-to-end workflows |
| `test_render.py` | Jinja2 rendering, parametrized all-modes render |
| `test_metadata.py` | YAML parsing, variable resolution |
| `test_config.py` | Config round-trip, overrides |
| `test_purge.py` | Purge command edge cases |
| `test_actions.py` | archive-stories + version-detection actions |
| `test_stories.py` | stories.md parsing, `is_header`, commit-message derivation |
| `test_cross_repo_contract.py` | Pyve-hosting cross-repo contract guards |
| `test_runtime.py` | Runtime helpers (skip-input, project-name detection) |
| `test_archive_stories_mode.py` | `archive_stories` mode end-to-end |

**Total: 901 tests across 15 files, ≥85% coverage (currently ~91%).**

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
