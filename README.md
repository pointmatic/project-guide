![project-guide](https://raw.githubusercontent.com/pointmatic/project-guide/main/docs/site/images/project-guide-header-readme.png)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/pointmatic/project-guide/workflows/Tests/badge.svg)](https://github.com/pointmatic/project-guide/actions)
[![PyPI](https://img.shields.io/pypi/v/project-guide.svg)](https://pypi.org/project/project-guide/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://pointmatic.github.io/project-guide/)
[![codecov](https://codecov.io/gh/pointmatic/project-guide/graph/badge.svg)](https://codecov.io/gh/pointmatic/project-guide)

A Python CLI tool that installs, renders, and synchronizes battle-tested LLM workflow prompts across projects using mode-driven Jinja2 templates, with content-hash sync and project-specific overrides to keep documentation consistent while preserving customizations.

## Why project-guide?

The `go.md` prompt provides the LLM with a structured workflow:
- Adapts for your current development mode (plan, code, debug, document, refactor)
- Lets you stay in charge: guiding features, flow, and taste
- Handles the typing so you can stay focused on the big picture

### How It Works
- Install project-guide in any repository
- Initialize the Project-Guide system
- (optional) Set the project mode (plan, code, debug, etc.)
- Tell your LLM to read `docs/project-guide/go.md` (in your IDE, or however you prefer)

### Human-in-the-Loop Development

This is "HITLoop" (human-in-the-loop) development: you direct, the LLM executes--it is not vibe-coding. Instead you are following the development closely and interactively guiding and improving the flow. The pace is "flaming agile"--an entire production-ready backend can be completed in 6-12 hours.

### Customization and Updates

When you customize a file for your project, mark it as overridden so future package updates skip it. When you want the latest workflow improvements, run `project-guide update` to sync all non-overridden files.

## Key Features
- **Battle-Tested Workflows** - Crafted workflow prompts from concept through production release in one place
- **Mode-Driven Templates** - 15 modes rendered via Jinja2 so `go.md` always matches your current task
- **Content-Hash Sync** - SHA-256 hash comparison detects changes without relying on version numbers
- **Custom File Lock** - Lock customized files to prevent update overwrites
- **Gentle Force Updates** - Automatic `.bak` files created if you `--force` update a custom file
- **CLI Interface** - Nine intuitive commands for all operations
- **Shell Completion** - Tab completion for commands, flags, and mode names (bash, zsh, fish)
- **Well Tested** - Comprehensive test coverage across CLI, rendering, and action modules
- **Zero Configuration** - Works with sensible defaults out of the box
- **Cross-Platform** - Runs on macOS, Linux, and Windows with Python 3.11+

## Installation

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
- `.project-guide.yml` - Configuration file
- `docs/project-guide/` - Mode templates, artifact templates, and metadata
- `docs/project-guide/go.md` - Rendered LLM instructions (default mode)

The rendered `go.md` and `.bak.*` backup files are gitignored.

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
project-guide mode plan_stories      # Break into stories
project-guide mode plan_phase        # Add a new phase to stories
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

Select mode [1-15, Enter to cancel]:
```

### 5. Update files

```bash
pip install --upgrade project-guide
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
installed_version: "2.4.12"
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

### Planning Modes

| Mode | Command | Output |
|------|---------|--------|
| **Concept** | `project-guide mode plan_concept` | `docs/specs/concept.md` |
| **Features** | `project-guide mode plan_features` | `docs/specs/features.md` |
| **Tech Spec** | `project-guide mode plan_tech_spec` | `docs/specs/tech-spec.md` + `docs/specs/project-essentials.md` (initial population) |
| **Stories** | `project-guide mode plan_stories` | `docs/specs/stories.md` |
| **Phase** | `project-guide mode plan_phase` | New phase added to `stories.md` + append to `project-essentials.md` |

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

### Post-Release Modes

| Mode | Command | Purpose |
|------|---------|---------|
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

### Setup

```bash
# Clone repository
git clone https://github.com/pointmatic/project-guide.git
cd project-guide

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=project_guide --cov-report=term-missing

# Run specific test file
pytest tests/test_cli.py -v
```

### Code Quality

```bash
# Linting
ruff check project_guide/ tests/

# Type checking
mypy project_guide/

# Format code
ruff format project_guide/ tests/
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

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Write tests** for new functionality
3. **Ensure all tests pass** and maintain coverage above 80%
4. **Run linting and type checks** before submitting
5. **Write clear commit messages** referencing issues when applicable
6. **Submit a pull request** with a description of changes

### Development Workflow

```bash
# Create feature branch
git switch -c feature/your-feature-name

# Make changes and test
pytest tests/
ruff check .
mypy project_guide/

# Commit and push
git commit -m "Add feature: description"
git push origin feature/your-feature-name
```

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
