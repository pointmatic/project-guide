# features.md — project-guide (Python)

This document defines **what** the `project-guide` project does — requirements, inputs, outputs, behavior — without specifying **how** it is implemented. This is the source of truth for scope.

For a high-level concept (why), see `concept.md`. For implementation details (how), see `tech-spec.md`. For a breakdown of the implementation plan (step-by-step tasks), see `stories.md`.

---

## Project Goal

`project-guide` is a Python CLI tool that installs a mode-driven template system into software projects, providing structured LLM workflows for planning, coding, debugging, and documentation. Each mode renders a single entry-point document (`go.md`) that the LLM reads to begin collaborating with the developer.

### Core Requirements

1. **Mode-Driven Templates**: Define development workflows as modes, each with its own template, prerequisites, and completion criteria
2. **Dynamic Rendering**: Render a single entry-point document (`go.md`) from Jinja2 templates based on the active mode
3. **Project Initialization**: Install the full template system into any project with a single command
4. **File Synchronization**: Keep installed templates current with the latest package version using content-hash comparison
5. **Override Management**: Allow developers to lock specific files when they contain project-specific customizations
6. **Status Reporting**: Show mode, prerequisites, and file sync state at a glance

### Operational Requirements

1. **CLI Interface**: Intuitive commands for init, mode, status, update, override, purge
2. **Configuration**: Project-specific settings stored in `.project-guide.yml`
3. **Safety**: Never overwrite files without explicit consent; backups created on forced updates
4. **Transparency**: Compact status output with grouped sections; verbose mode for details
5. **Idempotency**: Running the same command multiple times produces the same result
6. **Shell Completion**: Tab completion for command names, flags, and mode names (bash, zsh, fish)

### Quality Requirements

1. **Reliability**: Never corrupt or lose project-specific file customizations
2. **Clarity**: Clear error messages with actionable guidance (e.g., "Run `project-guide update` to sync")
3. **Minimal Dependencies**: click, jinja2, pyyaml, packaging — no heavy frameworks
4. **Cross-Platform**: Works on macOS, Linux, and Windows
5. **Test Coverage**: Minimum 85% code coverage; parametrized test renders every mode

### Usability Requirements

1. **Primary Users**: Developers using LLM assistance for software projects
2. **Installation**: `pip install project-guide`
3. **Zero Config**: Works with sensible defaults; no configuration required for basic use
4. **Fast Autocomplete**: Short filenames (`go.md`, not `go-project-guide.md`) for IDE/LLM autocomplete

### Non-goals

1. **Not a project scaffolding tool** — manages workflow documentation, not project structure (though `scaffold_project` mode guides the LLM through scaffolding)
2. **Not a code generator** — provides structure for the LLM to follow; code is generated conversationally
3. **Not an LLM API client** — no API calls; the LLM reads rendered markdown documents
4. **Not language-specific** — default templates assume Python but modes are language-agnostic

---

## Inputs

### Command Line

**`project-guide init`**
- Optional: `--target-dir` (default: `docs/project-guide`)
- Optional: `--force` (overwrite existing files)
- Optional: `--no-input` (skip stdin; auto-enabled by `CI=1` or non-TTY)
- Optional: `--quiet` / `-q` (suppress per-file progress output)

**`project-guide mode [MODE_NAME]`**
- Optional: mode name to switch to
- No argument: list modes grouped by category with ✓/✗/→ markers; interactive numbered menu on TTY
- Optional: `--verbose` / `-v` (show unmet prerequisite file paths)
- Optional: `--no-input` (show listing only, skip interactive menu)

**`project-guide status`**
- Optional: `--verbose` / `-v` (show full per-file list and per-phase story breakdown)

**`project-guide update`**
- Optional: `--files` (specific files to update)
- Optional: `--dry-run` (show what would change without applying)
- Optional: `--force` (update even overridden/modified files, creates backups)
- Optional: `--no-input` (non-interactive; reserved for future prompts)
- Optional: `--quiet` / `-q` (suppress per-file progress output)

**`project-guide override FILE_NAME REASON`**
- Required: file name (template-relative path)
- Required: reason for override

**`project-guide unoverride FILE_NAME`**
- Required: file name

**`project-guide overrides`**
- No arguments

**`project-guide purge`**
- Optional: `--force` (skip confirmation prompt)
- Optional: `--no-input` (skip stdin; auto-enabled by `CI=1` or non-TTY)
- Optional: `--quiet` / `-q` (suppress per-file progress output)

### Configuration File

**`.project-guide.yml`** (created in project root):
```yaml
version: '2.0'
installed_version: 2.0.15
target_dir: docs/project-guide
metadata_file: .metadata.yml
current_mode: default
```

### Metadata File

**`.metadata.yml`** (inside target directory, hidden):
- Defines all modes, their templates, artifacts, prerequisites, and shared variables
- `common` block provides variable substitution across all mode definitions
- Installed by `init`, synced by `update`

---

## Outputs

### File Structure

**After `project-guide init`:**
```
project-root/
├── .project-guide.yml              # Configuration
├── .gitignore                      # Updated with .bak entries
└── docs/
    └── project-guide/
        ├── go.md                   # Rendered entry point (tracked in git)
        ├── .metadata.yml           # Mode definitions (hidden)
        ├── README.md               # Directory overview
        ├── developer/              # Developer reference docs
        │   ├── best-practices-guide.md
        │   ├── brand-descriptions-guide.md
        │   ├── codecov-setup-guide.md
        │   ├── debug-guide.md
        │   ├── landing-page-guide.md
        │   ├── production-github-guide.md
        │   └── project-guide.md
        └── templates/
            ├── llm_entry_point.md  # Jinja2 entry point template
            ├── modes/              # Mode templates + header partials
            │   ├── _header-common.md
            │   ├── _header-sequence.md
            │   ├── _header-cycle.md
            │   ├── default-mode.md
            │   ├── plan-concept-mode.md
            │   ├── plan-features-mode.md
            │   ├── plan-tech-spec-mode.md
            │   ├── plan-stories-mode.md
            │   ├── plan-phase-mode.md
            │   ├── scaffold-project-mode.md
            │   ├── code-velocity-mode.md
            │   ├── code-test-first-mode.md
            │   ├── debug-mode.md
            │   ├── document-brand-mode.md
            │   ├── document-landing-mode.md
            │   ├── refactor-plan-mode.md
            │   └── refactor-document-mode.md
            └── artifacts/          # Artifact templates (structure guides)
                ├── concept.md
                ├── features.md
                ├── tech-spec.md
                ├── stories.md
                └── brand-descriptions.md
```

### Console Output

**`project-guide status` (happy path):**
```
project-guide v2.0.15

Mode: default — Getting started -- full project lifecycle overview
  Run 'project-guide mode' to see available modes.

Guide: docs/project-guide/go.md
  Tell your LLM: Read docs/project-guide/go.md

Files: 33 current
```

**`project-guide status` (with problems):**
```
project-guide v2.0.15 (installed: v2.0.13)

Mode: code_direct — Generate code with velocity
  Prerequisites: all met
  Run 'project-guide mode' to see available modes.

Guide: docs/project-guide/go.md
  Tell your LLM: Read docs/project-guide/go.md

Files: 30 current, 2 need updating, 1 missing
  Run 'project-guide update' to sync.
```

---

## Functional Requirements

### FR-1: Mode-Driven Template Rendering

The system renders a single entry-point document (`go.md`) from Jinja2 templates based on the active mode.

**Behavior:**
1. Entry-point template (`templates/llm_entry_point.md`) includes `_header-common.md` and the active mode's template
2. Mode template includes the appropriate header partial (`_header-sequence.md` or `_header-cycle.md`)
3. Context variables from `.metadata.yml` common block are available in all templates
4. `target_dir` is passed as a Jinja2 context variable
5. Undefined variables render as placeholders (lenient mode), not errors

**Modes (15 total):**

| Mode | Type | Description |
|-|-|-|
| `default` | sequence | Project lifecycle overview for new users |
| `scaffold_project` | sequence | Scaffold LICENSE, headers, manifest, README, CHANGELOG |
| `plan_concept` | sequence | Define problem and solution space |
| `plan_features` | sequence | Define feature requirements |
| `plan_tech_spec` | sequence | Define technical specification |
| `plan_stories` | sequence | Break down into implementation stories |
| `plan_phase` | sequence | Add a new feature phase to an existing project |
| `archive_stories` | sequence | Archive completed stories.md and start fresh for next phase |
| `code_direct` | cycle | Fast coding workflow with commit-per-story |
| `code_test_first` | cycle | Test-driven development workflow |
| `debug` | cycle | Reproduce, isolate, fix, verify workflow |
| `document_brand` | sequence | Define brand descriptions and messaging |
| `document_landing` | sequence | Generate landing page and MkDocs docs |
| `refactor_plan` | cycle | Update planning artifacts for new features or migration |
| `refactor_document` | cycle | Update documentation artifacts for new features or migration |

### FR-2: Project Initialization

`project-guide init` installs the complete template system into a project.

**Behavior:**
1. Copy template tree from package to target directory (default: `docs/project-guide`)
2. Render `go.md` in `default` mode
3. Create `.project-guide.yml` with current version, target directory, metadata file path, and `default` mode
4. Add `*.bak.*` entries to `.gitignore` under a `# project-guide` comment (the rendered `go.md` is tracked in git so the LLM can read it)
5. Report number of files installed

**Edge Cases:**
- `.project-guide.yml` exists → error unless `--force`
- Files already exist → skip without `--force`, overwrite with `--force`

### FR-3: File Synchronization (Hash-Based)

`project-guide update` syncs installed files to the latest package templates using content-hash comparison.

**Behavior:**
1. For each tracked file, compare SHA-256 hash of installed file vs bundled template
2. Hash matches → current (no action)
3. Hash differs and not overridden → prompt user to backup and overwrite
4. File missing → create it
5. File overridden → skip (unless `--force`)
6. After updating template files, re-render `go.md` for the current mode
7. Update `installed_version` in config

**Key design decision:** Version numbers do not determine freshness. A package version bump that doesn't change a specific template will not flag that file as needing an update.

**Edge Cases:**
- `--dry-run` → show changes without applying
- `--force` → backup and overwrite modified/overridden files without prompting
- `--files` → sync only specific files

### FR-4: Override Management

`project-guide override` locks a file from updates.

**Behavior:**
1. Verify file exists in tracked file list
2. Record override in `.project-guide.yml` with reason, locked version, and date
3. `update` skips overridden files unless `--force`

`project-guide unoverride` removes the lock.

`project-guide overrides` lists all overridden files with reasons.

### FR-5: Status Reporting

`project-guide status` shows a compact, grouped summary.

**Sections:**
1. **Header**: package version; installed version shown only when it differs
2. **Mode**: current mode name and description; prerequisites when applicable; hint to list modes
3. **Guide**: rendered entry-point path; onboarding hint
4. **Files**: summary counts (current, need updating, missing, overridden); `--verbose` for per-file list; hint to update when needed
5. **Stories** (when `stories.md` exists and contains stories): total/done/in-progress/planned counts; next unstarted story; `--verbose` adds per-phase breakdown

**Styling:** Bold labels, cyan highlights for mode name and guide path, color-coded file counts (green/yellow/red), dim action prompts.

### FR-6: Purge

`project-guide purge` removes all project-guide files.

**Behavior:**
1. Show what will be removed (config file and target directory)
2. Confirm unless `--force`
3. Remove target directory and config file

### FR-8: Non-Interactive / CI Mode

`--no-input`, `CI=1`, `PROJECT_GUIDE_NO_INPUT=1`, and non-TTY stdin all suppress interactive prompts on `init`, `update`, and `purge`. The first matching trigger wins (priority order: explicit flag → env var → CI env → non-TTY).

**Behavior:**
- `purge`: skips the "Are you sure?" confirmation prompt when any trigger fires. Combines with `--force` (the latter signals intent; the former signals environment).
- `update`: flag is present for future-prompt parity; `update` currently has no interactive prompts.
- `init`: flag is present; no prompts exist today but the plumbing is in place.

### FR-9: Quiet Mode

`--quiet` / `-q` on `init`, `update`, and `purge` suppresses per-file progress lines. Errors, final count summaries, and explicit warnings (e.g., overridden-file notices) are always shown regardless of `--quiet`. Composes cleanly with `--no-input` for fully silent unattended runs.

### FR-10: Story Detection in Status

`project-guide status` parses `<spec_artifacts_path>/stories.md` and adds a **Stories** section showing total/done/in-progress/planned counts and the next unstarted story. Section is omitted when the file is absent or contains no story headings (e.g., post-archive). `--verbose` adds a per-phase breakdown.

### FR-11: Mode Listing with Availability Markers and Interactive Menu

`project-guide mode` (no argument) displays a grouped, annotated mode listing:

- Modes are grouped by category (Getting Started, Planning, Coding, Post-Release, Scaffold, Documentation, Debugging, Refactoring) with ordered category headers.
- Each mode is annotated: `→` (current, cyan background highlight), `✓` (all prerequisites met, green), `✗` (unmet prerequisites, yellow, dimmed name).
- `--verbose` / `-v` shows the unmet prerequisite file paths beneath each `✗` entry.
- On a real TTY (unless `--no-input`, `CI=1`, or non-TTY stdin), a numbered selection menu is shown after the listing, allowing the developer to switch mode by entering a number. Empty input cancels. Up to 3 attempts before exit 1.

### FR-12: Per-Project Metadata Overrides

`metadata_overrides` in `.project-guide.yml` allows per-project patching of individual mode fields without editing the bundled `.metadata.yml`. Only these fields are patchable: `next_mode`, `files_exist`, `info`, `description`. Partial patch semantics — unmentioned fields are unchanged. Unknown mode names or fields raise `MetadataError`. Overrides are applied at every `load_metadata()` call site.

### FR-13: Pyve Detection and Bundled project-essentials-pyve.md

`project-guide init` detects whether `pyve` is installed by running `pyve --version`. On success, the version string is stored as `pyve_version` in `.project-guide.yml`; on failure (`FileNotFoundError`, non-zero exit, timeout), `null` is stored. Detection failure is non-fatal.

The `pyve_installed` boolean (derived from `pyve_version`) is passed as a Jinja2 context variable at every render call site. When true:
- `scaffold-project-mode.md` gains a "Merge Pyve Project Essentials" step that copies `templates/artifacts/project-essentials-pyve.md` into `docs/specs/project-essentials.md`.
- `plan-tech-spec-mode.md` instructs the LLM to merge pyve-specific rules when creating `project-essentials.md`.

The bundled `templates/artifacts/project-essentials-pyve.md` artifact covers: two-environment pattern, canonical invocation forms, `python` vs `python3` asdf-shim rule, and `requirements-dev.txt` story-writing convention.

### FR-7: Shell Completion

Tab completion for `project-guide` commands, flags, and mode names in bash, zsh, and fish.

**Behavior:**
1. **Static completion** (commands and flags) is provided automatically by Click for any user who enables shell completion via the standard `_PROJECT_GUIDE_COMPLETE=<shell>_source` environment variable
2. **Dynamic mode name completion**: `project-guide mode <TAB>` reads the active project's `.metadata.yml` and returns matching mode names; works with custom modes
3. Completion callbacks never crash the user's shell — any error returns an empty list silently

**Setup:**
- bash: `eval "$(_PROJECT_GUIDE_COMPLETE=bash_source project-guide)"` in `~/.bashrc`
- zsh: `eval "$(_PROJECT_GUIDE_COMPLETE=zsh_source project-guide)"` in `~/.zshrc`
- fish: `_PROJECT_GUIDE_COMPLETE=fish_source project-guide | source` in `~/.config/fish/completions/project-guide.fish`

---

## Configuration

### `.project-guide.yml` Schema

```yaml
version: '2.0'                      # Config schema version
installed_version: '2.0.15'         # Package version when last synced
target_dir: 'docs/project-guide'    # Where templates are installed
metadata_file: '.metadata.yml'      # Metadata filename (within target_dir)
current_mode: 'default'             # Active mode
test_first: false                   # Default coding approach (false = code_direct, true = code_test_first)
pyve_version: '1.2.3'               # Detected pyve version at init time; null if not installed

overrides:                           # Optional — file-level update locks
  <file_name>:
    reason: <string>
    locked_version: <version>
    last_updated: <date>

metadata_overrides:                  # Optional — per-project mode field patches
  <mode_name>:
    next_mode: <string>             # Override next mode in sequence
    files_exist: [<path>, ...]      # Override prerequisite file list
    info: <string>                  # Override one-line description
    description: <string>           # Override detailed description
```

### `.metadata.yml` Schema

```yaml
common:                              # Shared variables for {{var}} substitution
  spec_artifacts_path: 'docs/specs'
  programming_language: python
  # ... additional variables

modes:
  - name: <mode_name>
    info: <one-line description>
    description: <detailed description>
    sequence_or_cycle: sequence|cycle
    generation_type: document|code
    mode_template: <path to Jinja2 template>
    next_mode: <optional next mode name>
    artifacts:                       # Optional: files this mode generates
      - file: <path>
        action: create|modify
    files_exist:                     # Optional: prerequisite files
      - <path>
```

---

## Testing Requirements

### Unit Tests
- Metadata loading, variable resolution, mode lookup
- Jinja2 rendering with mode templates and header partials
- Config save/load round-trip, override management
- File sync: hash comparison, copy, backup
- Template path resolution and file discovery

### Integration Tests
- Full init → override → update workflow
- Hash-based status (version mismatch with matching content shows "current")
- Force update with backups
- Multi-project isolation
- Dry-run mode

### Parametrized Tests
- Every mode in `.metadata.yml` must render without errors (regression guard for new modes)

**Minimum Coverage**: 85% code coverage (currently ~91%)

---

## Security and Compliance Notes

1. **File Safety**: Never overwrite files without explicit consent (`--force` or user approval)
2. **Backup Creation**: `.bak` backups with timestamps created before any forced overwrite
3. **No Secrets**: Package contains only documentation templates, no sensitive data
4. **No Network**: Operates entirely offline after installation

---

## Performance Expectations

1. **File I/O**: All operations are file-based; performance is not a concern
2. **Hash Comparison**: SHA-256 hash of small files (<100KB each) is effectively instant
3. **Rendering**: Jinja2 template rendering completes in milliseconds

---

## Acceptance Criteria

1. `project-guide init` creates the full template tree and renders `go.md` in `default` mode; detects pyve and stores `pyve_version`
2. `project-guide mode <name>` switches mode and re-renders `go.md`
3. `project-guide mode` (no argument) shows grouped listing with ✓/✗/→ markers; interactive menu on TTY
4. `project-guide status` shows compact grouped output with hash-based file state and Stories section
5. `project-guide update` syncs files using content-hash comparison, not version numbers
6. `project-guide override/unoverride` manages file locks correctly
7. `project-guide purge` cleanly removes all project-guide files; respects `--no-input` / `CI=1`
8. `--no-input` and `--quiet` flags work on `init`, `update`, and `purge`
9. `metadata_overrides` in `.project-guide.yml` patches mode fields without editing bundled metadata
10. All 15 modes render without errors (parametrized test)
11. Shell completion (Tab) works for commands, flags, and mode names in bash/zsh/fish after one-line setup
12. Works on macOS, Linux, and Windows
13. Test coverage is ≥85%
14. Package is published to PyPI as `project-guide`
