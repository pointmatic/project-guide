![project-guide](https://raw.githubusercontent.com/pointmatic/project-guide/main/docs/site/images/project-guide-header-readme.png)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/pointmatic/project-guide/workflows/Tests/badge.svg)](https://github.com/pointmatic/project-guide/actions)
[![PyPI](https://img.shields.io/pypi/v/project-guide.svg)](https://pypi.org/project/project-guide/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://pointmatic.github.io/project-guide/)
[![codecov](https://codecov.io/gh/pointmatic/project-guide/graph/badge.svg)](https://codecov.io/gh/pointmatic/project-guide)

A Python-friendly CLI tool that installs, renders, and synchronizes battle-tested LLM workflow prompts across projects using mode-driven Jinja2 templates, with content-hash sync and project-specific overrides to keep documentation consistent while preserving customizations. Install globally with [pyve](https://pointmatic.github.io/pyve/) for pyve-aware onboarding.

## Why project-guide?

The `go.md` prompt provides the LLM with a structured workflow:
- Adapts for your current development mode (plan, code, debug, document, refactor)
- Lets you stay in charge: guiding features, flow, and taste
- Handles the typing so you can stay focused on the big picture

### How It Works
- Install project-guide in any repository (language-agnostic)
- Initialize the Project-Guide system
- (optional) Set the project mode (plan, code, debug, etc.)
- Tell your LLM to read `docs/project-guide/go.md` (in your IDE, or however you prefer)

### Human-in-the-Loop Development

This is "HITLoop" (human-in-the-loop) development: you direct, the LLM executes--it is not vibe-coding. Instead you are following the development closely and interactively guiding and improving the flow. The pace is "flaming agile"--an entire production-ready backend can be completed in 6-12 hours.

### Customization and Updates

When you customize a file for your project, mark it as overridden so future package updates skip it. When you want the latest workflow improvements, run `project-guide update` to sync all non-overridden files.

## Key Features
- **Battle-Tested Workflows** - Crafted workflow prompts from concept through production release in one place
- **Mode-Driven Templates** - 17 modes rendered via Jinja2 so `go.md` always matches your current task
- **Pyve Integration** - First-class [pyve](https://pointmatic.github.io/pyve/) support: install globally with `pyve self install` and get pyve-aware onboarding plus a `status` host footer and `heal` drift warnings when pyve manages the install
- **Content-Hash Sync** - SHA-256 hash comparison detects changes without relying on version numbers
- **Custom File Lock** - Lock customized files to prevent update overwrites
- **Gentle Force Updates** - Automatic `.bak` files created if you `--force` update a custom file
- **CLI Interface** - Intuitive commands for every step of the workflow (init, mode, status, update, heal, override, purge, …)
- **Auto-Heal** - Every command silently repairs the install if drift is detected; prompts only when there's actual work to do, so a fresh clone is one `project-guide <anything>` away from being usable
- **Shell Completion** - Tab completion for commands, flags, and mode names (bash, zsh, fish)
- **Well Tested** - Comprehensive test coverage across CLI, rendering, and action modules
- **Zero Configuration** - Works with sensible defaults out of the box
- **Cross-Platform** - Runs on macOS, Linux, and Windows with Python 3.11+

## Installation

### Via pyve (recommended)

If you use [pyve](https://pointmatic.github.io/pyve/), let pyve install project-guide globally for you — `pyve self install` provisions project-guide in pyve's toolchain venv and creates a `~/.local/bin/project-guide` shim. Otherwise, install with `pip` (or `pipx`) per the sections below.

```bash
pyve self install
```

**Why a single global install?** Under pyve hosting, one project-guide install on `PATH` serves every project you work on, rather than a separate `pip install` per project. project-guide is built for this: all per-project state lives in your project's `.project-guide.yml` and `docs/project-guide/` tree — nothing is written back to the shared install. When pyve is detected at `init` time, project-guide adapts: the rendered `go.md` onboarding, `project-guide status`, and `project-guide heal` all reflect pyve-managed hosting (and `heal` warns if a stray project-local install would shadow the global one).

### Via pip

```bash
pip install project-guide
```

### Via pipx (recommended for CLI coding tools)

```bash
pipx install project-guide
```

### Dependencies

click, jinja2, pyyaml, packaging

### Shell Completion (Optional)

Enable Tab completion for commands, flags, and mode names. Add to your shell startup file:

```bash
# bash (~/.bashrc)
eval "$(_PROJECT_GUIDE_COMPLETE=bash_source project-guide)"

# zsh (~/.zshrc)
eval "$(_PROJECT_GUIDE_COMPLETE=zsh_source project-guide)"
```

See [Installation Options](https://pointmatic.github.io/project-guide/user-guide/install-options/#shell-completion-optional) for fish and full details.

## Quick Start

### 1. Initialize in your project

```bash
cd /path/to/your/project
project-guide init
```

This creates:
- `.project-guide.yml` - Configuration file (tracked)
- `docs/project-guide/go.md` - Rendered LLM instructions (**unignored but intentionally untracked** as of v2.8.0 — must be visible to IDE-integrated LLMs, but kept out of git so branch switches don't trip on it)
- `docs/project-guide/` - Mode templates, artifact templates, and metadata (gitignored bundled data)

Everything under `docs/project-guide/` is gitignored **except** `go.md` (which the LLM reads). The gitignored template tree is bundled static data — `project-guide heal` repopulates it on first invocation in a fresh clone, and the auto-hook makes that healing run silently before any other command.

**Upgrading from v2.6.x – v2.7.x?** Earlier project-guide versions left `go.md` tracked by historical accident. v2.8.0 flips the policy to untracked-by-default to eliminate branch-switch and merge friction. If `heal` warns that `go.md` is tracked, run once on your default branch:

```bash
git rm --cached docs/project-guide/go.md && git commit -m "untrack go.md per project-guide v2.8.0"
```

The file stays visible to your IDE LLM (the gitignore block hasn't changed), but it stops appearing in diffs and stops blocking `git switch`.

### 2. Tell your LLM to read the guide

```
Read docs/project-guide/go.md
```

The LLM follows the instructions, asks clarifying questions, and generates artifacts. Type `go` to advance through steps.

### 3. Switch modes as you progress

```bash
project-guide mode plan_concept      # Define problem & solution
project-guide mode plan_features     # Define requirements
project-guide mode plan_tech_spec    # Define architecture
project-guide mode plan_envs         # FROZEN (pending Pyve work) — skip; do not use
project-guide mode plan_stories      # Break into stories
project-guide mode plan_phase        # Add a new phase to stories (pre-1.0)
project-guide mode plan_production_phase # Add a new phase to stories (post-1.0, with readiness checklist)
project-guide mode scaffold_project  # Scaffold license, manifest, README, CHANGELOG
project-guide mode code_direct       # Implement stories fast
project-guide mode code_test_first   # TDD red-green-refactor
project-guide mode debug             # Debug with test-first approach
project-guide mode archive_stories   # Archive completed stories.md before next phase
project-guide mode document_brand    # Brand descriptions
project-guide mode document_landing  # GitHub Pages + MkDocs docs
project-guide mode refactor_plan     # Plan a refactor
project-guide mode refactor_document # Document a refactor
```

Each mode re-renders `docs/project-guide/go.md` with focused instructions for that workflow.

### 4. List available modes

```bash
project-guide mode
```

Modes are displayed in category groups with availability markers:
- `→` — current mode (cyan background highlight)
- `✓` — all prerequisites met (green)
- `✗` — unmet prerequisites (yellow, dimmed)

On a real terminal, a numbered selection menu is shown so you can switch by entering a number. Under `--no-input`, `CI=1`, or piped input, only the listing is shown.

```
Current mode: code_direct

  Planning
  ✓  2  plan_concept               Generate a high-level concept
  ✓  3  plan_features              Generate feature requirements
  ...

  Coding
  →  6  code_direct                Generate code directly, test after
  ✓  7  code_test_first            Generate code with a test-first approach
  ...

Select mode [1-17, Enter to cancel]:
```

### 5. Update files

```bash
pip install --upgrade project-guide   # pyve users: pyve upgrades project-guide for you
project-guide update
```

Overridden files are skipped. Modified files prompt for confirmation. Backups are always created before overwrites.

### 6. Customize a file (optional)

```bash
project-guide override templates/modes/debug-mode.md "Custom debugging for this project"
```

## Command Reference

### `init`

Initialize project-guide in the current directory. Safe to run unattended — re-running on an already-initialized project is a silent exit-0 no-op, and the `--no-input` flag (plus auto-detection) ensures CI runners and post-hooks never hang on stdin.

```bash
project-guide init [OPTIONS]
```

**Options:**
- `--target-dir PATH` - Directory for templates (default: `docs/project-guide`)
- `--force` - Overwrite existing configuration
- `--no-input` - Do not read from stdin; use defaults where sensible. Fail loudly if any prompt has no default. (Also auto-enabled by `CI=1` or non-TTY stdin.)

**Examples:**
```bash
# Initialize with default settings
project-guide init

# Use custom directory
project-guide init --target-dir documentation/workflows

# Force reinitialize
project-guide init --force
```

#### Unattended / CI use

`project-guide init` is safe to invoke from any unattended context (CI runners, `pyve` post-hooks, subprocess pipelines, shell scripts). Four independent triggers all enable skip-input mode, in priority order — the first match wins:

```bash
# 1. Explicit flag
project-guide init --no-input

# 2. PROJECT_GUIDE_NO_INPUT env var (truthy: 1, true, yes, on — case-insensitive)
PROJECT_GUIDE_NO_INPUT=1 project-guide init

# 3. CI env var (auto-detected on most CI runners)
CI=1 project-guide init

# 4. Non-TTY stdin (piped input, subprocess, closed stdin)
echo "" | project-guide init
```

**Idempotent re-run:** Running `project-guide init` a second time on a project that is already initialized is a silent exit-0 no-op (with an informational message). Use `--force` to re-run the full install and overwrite existing files. This makes the command safe to call unconditionally from automated flows.

### `mode`

Set or show the active development mode.

```bash
project-guide mode [MODE_NAME]
```

**Without argument:** Lists all modes grouped by category with ✓/✗/→ markers. Shows an interactive selection menu on TTY.

**With argument:** Switches to the specified mode and re-renders `go.md`.

**Options:**
- `--verbose` / `-v` — Show unmet prerequisite file paths beneath each `✗` entry
- `--no-input` — Show listing only; skip interactive menu

**Examples:**
```bash
# Show grouped listing (+ interactive menu on TTY)
project-guide mode

# Show listing with prerequisite details
project-guide mode --verbose

# Switch to direct coding mode
project-guide mode code_direct

# Switch to debugging mode
project-guide mode debug
```

### `archive-stories`

Archive `docs/specs/stories.md` and re-render a fresh one for the next phase. Wraps the deterministic `archive` action declared on the `archive_stories` mode.

```bash
project-guide archive-stories
```

This command:

1. Reads the latest version from the highest `### Story X.y: vN.N.N` heading in `stories.md`.
2. Detects the highest `## Phase <Letter>:` heading (informational only).
3. Extracts the `## Future` section verbatim if present.
4. Moves `stories.md` to `<spec_artifacts_path>/.archive/stories-vX.Y.Z.md`.
5. Re-renders a fresh empty `stories.md` from the bundled artifact template, carrying the `## Future` section over.

If any pre-check fails (no versioned stories, archive target already exists, source file missing) the command errors and leaves the workspace untouched. If the re-render fails after the move, the source is rolled back from `.archive/`.

This command is intended to be run by the LLM after the developer has approved the archive in `project-guide mode archive_stories`.

### `bump-version`

Bump the package version across all three canonical sites in one step. Use it at end-of-phase when shipping a bundled release.

```bash
project-guide bump-version [VERSION]
```

**Argument:**
- `VERSION` - the `X.Y.Z` version to write

**Writes:**
- `pyproject.toml` `[project] version`
- the package `__version__` source (auto-detected: `<package>/version.py`, `_version.py`, `__init__.py`, and `src/` variants)
- a new `## [VERSION] - YYYY-MM-DD` entry in `CHANGELOG.md`, inserted directly below `## [Unreleased]` (idempotent — re-running refreshes the date and preserves the body)

**Options:**
- `--no-input` - Skip prompts; fail loudly if a default is missing (also auto-enabled by `CI=1` or non-TTY stdin)
- `--quiet` - Suppress success-path stdout; errors and warnings still print to stderr

The version magnitude (patch / minor / major) is a decision made per the Version Cadence rule in `docs/specs/stories.md`; this command performs only the mechanical write.

### `status`

Show status of all installed files and current mode. Output is compact and grouped into Mode, Guide, and Files sections with color.

```bash
project-guide status [OPTIONS]
```

**Options:**
- `--verbose` / `-v` - Show detailed file-level information

**Output includes:**
- Current package version and installed version
- Active mode with prerequisites status
- Status of the rendered guide
- File counts (current, need updating, missing, overridden)
- Stories section: total/done/in-progress/planned counts + next story (when `stories.md` exists)
- A `Managed by pyve vX.Y.Z` footer when pyve was present at `init` time (install pyve before running `project-guide init` for it to appear)
- Per-file detail and per-phase story breakdown (verbose mode)

### `update`

Update files to the latest version. Uses SHA-256 content hash comparison to detect changes.

```bash
project-guide update [OPTIONS]
```

**Options:**
- `--files NAME` - Update specific files only (repeatable)
- `--force` - Update even overridden files (creates backups)
- `--dry-run` - Show what would change without applying
- `--no-input` - Non-interactive mode (reserved for future prompts)
- `--quiet` / `-q` - Suppress per-file progress output

**Examples:**
```bash
# Update all files (skips overridden)
project-guide update

# Update specific files
project-guide update --files templates/modes/debug-mode.md

# Force update all (creates backups for overridden)
project-guide update --force

# Preview changes
project-guide update --dry-run
```

### `heal`

Repair the install: create missing template files and refresh stale ones to match the bundled package. Silent when there's nothing to do; prompts to apply when drift is detected.

```bash
project-guide heal [OPTIONS]
```

**Options:**
- `--no-input` - Auto-yes the `[Y/n]` prompt and emit a one-line stderr notice when writes occur (also auto-enabled by `CI=1`, `PROJECT_GUIDE_NO_INPUT=1`, or non-TTY stdin)

**When to use it:**
- After cloning a repo that has `project-guide init`'d output but the template tree is gitignored — heal repopulates it.
- After accidentally editing or deleting a bundled template file and wanting to restore the canonical version.
- Whenever you're not sure whether the install is up-to-date with the package version.

**Auto-hook:** every `project-guide` invocation (including `--help` and `--version`) calls heal first via a group-level hook, so the fresh-clone case usually resolves itself silently the first time you run *any* command. The hook is silent in the steady state and prompts only when there's actual drift.

**Tracked-`go.md` warning (v2.8.0+):** if `docs/project-guide/go.md` is in your git index, `heal` emits a stderr warning with a copyable migration command. The current policy is untracked-by-default — `go.md` stays visible to IDE LLMs (because it's unignored) but is kept out of the index so branch switches don't trip on it. The warning is non-fatal; the consumer applies the migration on their own schedule.

**Local-install warning under pyve hosting (v2.13.0+):** when pyve is detected and a project-local install of project-guide (under a `site-packages` directory inside your project, e.g. `.venv/`) would shadow pyve's global install, `heal` emits a stderr warning with a copyable `pip uninstall project-guide` command. Like the `go.md` warning it is non-fatal and never auto-removes anything — you decide when to clean up. An editable source checkout is deliberately not flagged.

**Examples:**
```bash
# Interactive: prompts on drift
project-guide heal

# Unattended (CI, scripts, embedding callers)
project-guide heal --no-input
```

### `git-push`

Wrap [gitbetter](https://github.com/pointmatic/gitbetter)'s `git-push` with a commit message auto-derived from the most-recently-completed-and-not-yet-committed story in `docs/specs/stories.md`. Optional: requires gitbetter on PATH.

```bash
project-guide git-push [BRANCH_NAME]
```

**Arguments:**
- `BRANCH_NAME` (optional) - Passed through to gitbetter for branch-aware push flows (e.g. switching to a feature branch and offering cleanup after merge)

**Heading-to-message transformation:**
```
### Story G.a: v1.2.3 New command `foo` with "Hello" [Done]
                                ↓
       G.a: v1.2.3 New command 'foo' with 'Hello'
```
Backticks and double quotes become single quotes; single quotes pass through; the colon after the story ID is preserved (it's the anchor for the already-committed check).

**Hard errors (exit 1):**
- No `[Done]` story in `stories.md`
- The last `[Done]` story is already committed — the wrapper does not second-guess; resolve manually with raw `git-push`
- Multiple `[Done]` stories are uncommitted — commit them one at a time with explicit messages via raw `git-push`
- `git-push` not on PATH — install gitbetter: `brew install pointmatic/tap/gitbetter`

**Examples:**
```bash
# Most common: ready to commit the just-completed story to the current branch
project-guide git-push

# Feature-branch push (gitbetter switches to the branch first, offers cleanup after merge)
project-guide git-push feature/heal-command
```

**Optional dependency.** gitbetter is not required for any other `project-guide` command. Install it only if you want this wrapper:
```bash
brew install pointmatic/tap/gitbetter
```

### `override`

Mark a file as customized to prevent automatic updates.

```bash
project-guide override FILE_NAME REASON
```

**Arguments:**
- `FILE_NAME` - Name of the file (positional)
- `REASON` - Why this file is customized (positional)

**Example:**
```bash
project-guide override templates/modes/debug-mode.md "Custom debugging workflow with project-specific tools"
```

### `unoverride`

Remove override status from a file.

```bash
project-guide unoverride FILE_NAME
```

**Arguments:**
- `FILE_NAME` - Name of the file (positional)

**Example:**
```bash
project-guide unoverride templates/modes/debug-mode.md
```

### `overrides`

List all overridden files.

```bash
project-guide overrides
```

**Output:**
```
Overridden files:

templates/modes/debug-mode.md
  Reason: Custom debugging workflow with project-specific tools
  Since: v2.0.0
  Last updated: 2026-03-03
```

### `purge`

Remove all project-guide files from the current project.

```bash
project-guide purge [OPTIONS]
```

**Options:**
- `--force` - Skip confirmation prompt
- `--no-input` - Skip confirmation (also auto-enabled by `CI=1` or non-TTY stdin)
- `--quiet` / `-q` - Suppress per-file progress output

**Examples:**
```bash
# Purge with confirmation prompt
project-guide purge

# Purge without confirmation
project-guide purge --force

# Unattended purge (CI / non-interactive)
project-guide purge --no-input --force
```

**What gets removed:**
- `.project-guide.yml` configuration file
- Target directory (e.g., `docs/project-guide/`) and all contents

**Warning:** This action cannot be undone. Use with caution.

## Configuration

The `.project-guide.yml` file stores project configuration:

```yaml
version: "2.0"
installed_version: "2.17.0"
target_dir: "docs/project-guide"
metadata_file: ".metadata.yml"
current_mode: "code_direct"
test_first: false
pyve_version: "1.2.3"          # null if pyve not installed

overrides:
  templates/modes/debug-mode.md:
    reason: "Custom debugging workflow for this project"
    locked_version: "2.0.0"
    last_updated: "2026-04-07"

metadata_overrides:             # optional — per-project mode field patches
  plan_stories:
    next_mode: scaffold_project
```

**Fields:**
- `version` - Config file format version
- `installed_version` - Version of files currently installed
- `target_dir` - Where templates are stored
- `metadata_file` - Hidden metadata file inside target dir (default: `.metadata.yml`)
- `current_mode` - Active development mode
- `test_first` - Default coding approach (`false` = `code_direct`, `true` = `code_test_first`)
- `pyve_version` - Detected pyve version at init time; `null` if pyve not installed
- `overrides` - Map of file-level update locks with reason and timestamp
- `metadata_overrides` - Per-project patches for individual mode fields (`next_mode`, `files_exist`, `info`, `description`)

## Available Modes

### Project Planning Modes

One-time-per-project work — the spec documents that establish the project before any code lands. (The **Environments** step is currently **frozen** — see the note below the table.)

| Mode | Command | Output |
|------|---------|--------|
| **Concept** | `project-guide mode plan_concept` | `docs/specs/concept.md` |
| **Features** | `project-guide mode plan_features` | `docs/specs/features.md` |
| **Tech Spec** | `project-guide mode plan_tech_spec` | `docs/specs/tech-spec.md` + `docs/specs/project-essentials.md` (initial population) |
| **Environments** *(frozen)* | `project-guide mode plan_envs` | `docs/specs/env-dependencies.md` |
| **Stories** | `project-guide mode plan_stories` | `docs/specs/stories.md` |

> **`plan_envs` is frozen** pending upstream Pyve work and should not be used. The recommended flow goes straight from **Tech Spec** to **Stories**; the mode stays listed so it can be restored once Pyve unblocks it.

### Coding Modes

| Mode | Command | Workflow |
|------|---------|----------|
| **Direct** | `project-guide mode code_direct` | Direct commits, fast iteration |
| **Test-First** | `project-guide mode code_test_first` | TDD red-green-refactor cycle |
| **Debug** | `project-guide mode debug` | Test-driven debugging |

### Documentation Modes

| Mode | Command | Output |
|------|---------|--------|
| **Branding** | `project-guide mode document_brand` | `docs/specs/brand-descriptions.md` |
| **Landing Page** | `project-guide mode document_landing` | GitHub Pages + MkDocs docs |

### Release Planning Modes

Repeated per release — phase planning (pre-1.0 vs. post-1.0), end-of-phase archive.

| Mode | Command | Purpose |
|------|---------|---------|
| **Phase** | `project-guide mode plan_phase` | Pre-1.0 phase planning. New phase added to `stories.md` + append to `project-essentials.md` |
| **Production Phase** | `project-guide mode plan_production_phase` | Post-1.0 mandatory phase planning. Adds production-readiness checklist + breaking-change negotiation + explicit version-bump target |
| **Archive Stories** | `project-guide mode archive_stories` | Move completed `stories.md` to `.archive/` and re-render an empty one for the next phase |

### Refactoring Modes

| Mode | Command | Workflow |
|------|---------|----------|
| **Plan** | `project-guide mode refactor_plan` | Update `concept`/`features`/`tech-spec` for new capabilities or legacy migration; terminal step refreshes `project-essentials.md` (creates it for legacy projects) |
| **Document** | `project-guide mode refactor_document` | Update README, brand descriptions, landing page, and MkDocs config |

## Troubleshooting

### "Configuration file not found"

**Problem:** Running commands outside a project-guide initialized directory.

**Solution:**
```bash
project-guide init
```

### "File already exists"

**Problem:** Trying to initialize when files already exist.

**Solution:**
```bash
# Use --force to overwrite
project-guide init --force

# Or manually remove existing files
rm -rf docs/project-guide .project-guide.yml
project-guide init
```

### "Permission denied"

**Problem:** Insufficient permissions to write files.

**Solution:**
```bash
# Check directory permissions
ls -la docs/

# Fix permissions if needed
chmod -R u+w docs/
```

### Updates not appearing

**Problem:** Files show as current but you expect updates.

**Solution:**
```bash
# Check if file is overridden
project-guide overrides

# Force update if needed
project-guide update --force
```

## Development

Quick reference. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full
guide (PR process, release process, code-style commands, coverage
expectations).

### Setup

```bash
git clone https://github.com/pointmatic/project-guide.git
cd project-guide

# Main environment: editable install.
pyve run pip install -e .

# Dev testenv: pytest, ruff, mypy.
pyve env init
pyve env install -r requirements-dev.txt
```

### Running Tests

```bash
pyve test                                      # all tests
pyve test tests/test_cli.py                    # one file
pyve test --cov=project_guide --cov-report=term-missing
```

### Code Quality

```bash
pyve env run ruff check project_guide tests
pyve env run ruff format project_guide tests
pyve env run mypy project_guide
```

### Documentation Development

The project uses MkDocs with Material theme for documentation.

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Preview documentation locally (with live reload)
mkdocs serve
# Open http://127.0.0.1:8000

# Build documentation
mkdocs build

# Build with strict mode (fails on warnings)
mkdocs build --strict
```

**Directory Structure:**
- `docs/site/` - Documentation source files (markdown)
- `site/` - Built documentation (generated, gitignored)
- `mkdocs.yml` - MkDocs configuration
- `.github/workflows/deploy-docs.yml` - Automated deployment to GitHub Pages

## Contributing

Contributions are welcome! See [`CONTRIBUTING.md`](CONTRIBUTING.md) for
the full PR process. Quick summary:

1. **Fork** and branch off `main`.
2. **Test** locally: `pyve test` and `pyve env run ruff check project_guide tests` must pass.
3. **PR** against `pointmatic/project-guide:main` with a description that explains the *why*.
4. **CI** must be green; a maintainer will review.

For non-trivial changes, scope the work via a story in
`docs/specs/stories.md` before opening the PR — see `CONTRIBUTING.md` for
the recommended workflow.

## Security

To report a vulnerability, **do not file a public GitHub issue**. Use
[GitHub Security Advisories](https://github.com/pointmatic/project-guide/security/advisories/new)
for a private report — see [`SECURITY.md`](SECURITY.md) for the supported-
versions policy, response expectations, and the threat model.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

```
Copyright (c) 2026 Pointmatic

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## Documentation

Full documentation is available at [pointmatic.github.io/project-guide](https://pointmatic.github.io/project-guide/)

- [Getting Started](https://pointmatic.github.io/project-guide/getting-started/installation/) - Installation and quick start
- [User Guide](https://pointmatic.github.io/project-guide/user-guide/commands/) - Commands, workflows, and override management
- [Developer Guide](https://pointmatic.github.io/project-guide/developer-guide/contributing/) - Contributing and development setup

## Support

- **Issues:** [GitHub Issues](https://github.com/pointmatic/project-guide/issues)
- **Discussions:** [GitHub Discussions](https://github.com/pointmatic/project-guide/discussions)
- **Documentation:** [GitHub Pages](https://pointmatic.github.io/project-guide/)

---

**Made for LLM-assisted development workflows**
