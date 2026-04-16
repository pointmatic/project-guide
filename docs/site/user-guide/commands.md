# Commands Reference

project-guide provides nine commands for managing LLM workflow files across your projects.

## Command Overview

| Command | Purpose |
|---------|---------|
| `init` | Install files into a new project |
| `mode` | Switch workflow mode or list available modes |
| `archive-stories` | Archive `stories.md` and re-render a fresh one for the next phase |
| `status` | Show file status grouped by category |
| `update` | Update non-overridden files to latest versions |
| `override` | Mark a file as overridden to prevent updates |
| `unoverride` | Remove override status from a file |
| `overrides` | List all overridden files |
| `purge` | Remove all files and configuration |

## init

Install workflow files into your project and render the initial `go.md` entry point. Safe to run unattended — re-running on an already-initialized project is a silent exit-0 no-op, and the `--no-input` flag (plus auto-detection) ensures CI runners and post-hooks never hang on stdin.

```bash
project-guide init [OPTIONS]
```

### Options

- `--target-dir PATH` - Custom directory for files (default: `docs/project-guide`)
- `--force` - Overwrite existing files and configuration
- `--no-input` - Do not read from stdin; use defaults where sensible. Fail loudly if any prompt has no default. (Also auto-enabled by `CI=1` or non-TTY stdin.)

### Examples

```bash
# Initialize with default settings
project-guide init

# Use custom target directory
project-guide init --target-dir documentation/workflows

# Force reinstall (overwrites existing files)
project-guide init --force

# Unattended / CI
project-guide init --no-input
PROJECT_GUIDE_NO_INPUT=1 project-guide init
CI=1 project-guide init
echo "" | project-guide init   # non-TTY stdin
```

### What It Does

1. Creates the `docs/project-guide/` directory if it doesn't exist
2. Copies all bundled templates to the directory
3. Creates `.project-guide.yml` configuration file
4. Renders `go.md` from templates based on the active mode
5. Records the content hash for each file

### Idempotent Re-run

Running `project-guide init` a second time on a project that is already initialized is a silent exit-0 no-op — the command prints `project-guide already initialized at <target_dir>/ (use --force to reinitialize).` and returns. This makes the command safe to call unconditionally from automated flows (CI, `pyve` post-hooks, shell scripts).

Use `--force` to re-run the full install and overwrite existing files.

### Unattended / CI Use

`project-guide init` reads no stdin when any of the following are true — the first match wins:

| Priority | Trigger                            | Notes                                                                                        |
|---------:|------------------------------------|----------------------------------------------------------------------------------------------|
|        1 | `--no-input` flag                  | Explicit opt-in.                                                                             |
|        2 | `PROJECT_GUIDE_NO_INPUT` env var   | Truthy values (case-insensitive): `1`, `true`, `yes`, `on`.                                  |
|        3 | `CI` env var                       | Same truthy-value rules. Auto-detected on most CI runners (GitHub Actions, GitLab CI, etc.). |
|        4 | Non-TTY stdin                      | Piped input, subprocess, closed stdin, or `sys.stdin is None`.                               |

When any trigger fires, `init` uses defaults for every setting that has one. If a future prompt has no default under `--no-input`, the command fails loudly with an exit code of 1 rather than hanging on stdin.

This plumbing (the `should_skip_input()` helper and the `_require_setting()` contract in `project_guide/runtime.py`) was added in v2.2.1 so that any future interactive prompt added to `init` automatically inherits the unattended-mode contract.

## mode

Switch the active workflow mode or list available modes.

```bash
project-guide mode [MODE_NAME]
```

### Options

- `--verbose`, `-v` - Show unmet prerequisite file paths beneath each `✗` entry
- `--no-input` - Show listing only; skip interactive selection menu

### Examples

```bash
# List all available modes (+ interactive menu on TTY)
project-guide mode

# List with prerequisite details
project-guide mode --verbose

# Listing only, no interactive menu
project-guide mode --no-input

# Switch to a specific mode
project-guide mode plan_concept
project-guide mode code_direct
project-guide mode debug
```

### What It Does

1. When called with no argument, lists all 15 modes grouped by category with ✓/✗/→ markers
2. On a real TTY (unless `--no-input`/`CI=1`/non-TTY stdin), shows an interactive numbered menu
3. When called with a mode name, switches the active mode
4. Re-renders `go.md` to reflect the new mode's workflow
5. Updates `.project-guide.yml` with the active mode

## archive-stories

Archive `docs/specs/stories.md` and re-render a fresh one for the next phase. Wraps the deterministic `archive` action declared on the `archive_stories` mode (shipped in v2.1.3).

```bash
project-guide archive-stories
```

### What It Does

1. Reads the latest version from the highest `### Story X.y: vN.N.N` heading in `stories.md`.
2. Detects the highest `## Phase <Letter>:` heading (informational only).
3. Extracts the `## Future` section verbatim if present.
4. Moves `stories.md` to `<spec_artifacts_path>/.archive/stories-vX.Y.Z.md`.
5. Re-renders a fresh empty `stories.md` from the bundled artifact template, carrying the `## Future` section over.

### Failure Modes

If any pre-check fails (no versioned stories in the source, archive target already exists, source file missing) the command errors and leaves the workspace untouched. If the re-render fails after the move, the source is rolled back from `.archive/`.

### Usage

This command is intended to be run by the LLM after the developer has approved the archive in `project-guide mode archive_stories`. The conversational-vs-deterministic split is deliberate: the mode template walks the developer through the decision; the CLI command performs the transaction.

## status

Display the status of all files in your project, grouped by category.

```bash
project-guide status [OPTIONS]
```

### Options

- `--verbose`, `-v` - Show detailed output per file and per-phase story breakdown

### Output

Shows grouped sections:

- **Mode** - Active mode name, description, and prerequisites status
- **Guide** - The rendered `go.md` entry point path
- **Files** - Summary counts (current / need updating / missing / overridden); per-file list in verbose mode
- **Stories** - Total/done/in-progress/planned counts and next unstarted story (when `stories.md` exists and contains stories); per-phase breakdown in verbose mode

Each file shows one of:

- **Current** - File content matches the latest template
- **Changed** - Content hash differs from the latest template
- **Overridden** - File is locked and won't be updated
- **Missing** - File not found in the target directory

### Example Output

```
project-guide v2.4.12

Mode: code_direct — Generate code directly, test after
  Prerequisites: all met
  Run 'project-guide mode' to see available modes.

Guide: docs/project-guide/go.md
  Tell your LLM: Read docs/project-guide/go.md

Files: 33 current

Stories: 12 total (8 done, 1 in progress, 3 planned)
  Next: N.m — Phase N Documentation and CHANGELOG
```

## update

Update all non-overridden files to the latest versions.

```bash
project-guide update [OPTIONS]
```

### Options

- `--files FILE [FILE ...]` - Update only specific files
- `--dry-run` - Show what would be updated without making changes
- `--force` - Update even overridden files (creates `.bak` backups)
- `--no-input` - Non-interactive mode (reserved for future prompts)
- `--quiet`, `-q` - Suppress per-file progress output

### Examples

```bash
# Update all non-overridden files
project-guide update

# Preview what would change
project-guide update --dry-run

# Update specific files only
project-guide update --files templates/modes/debug-mode.md developer/setup.md

# Force update all files (including overridden)
project-guide update --force
```

### What It Does

1. Compares each file's content hash against the latest template hash
2. Updates files whose content has changed and are not overridden
3. Skips overridden files (unless `--force` is used)
4. Creates `.bak.<timestamp>` backups when updating overridden files with `--force`
5. Re-renders `go.md` if the active mode's template changed
6. Updates content hashes in configuration

## override

Mark a file as overridden to prevent automatic updates.

```bash
project-guide override <FILE_NAME> <REASON>
```

Both arguments are positional. File paths are template-relative.

### Examples

```bash
# Override a mode template
project-guide override templates/modes/debug-mode.md "Added team-specific debugging steps"

# Override a developer file
project-guide override developer/setup.md "Customized for our internal toolchain"
```

### What It Does

1. Records the file as overridden in `.project-guide.yml`
2. Stores the current content hash as `locked_version`
3. Stores the reason and `last_updated` timestamp
4. Future `update` commands will skip this file

## unoverride

Remove override status from a file, allowing it to be updated again.

```bash
project-guide unoverride <FILE_NAME>
```

The file path is positional and template-relative.

### Examples

```bash
# Remove override status
project-guide unoverride templates/modes/debug-mode.md
```

### What It Does

1. Removes the file from the overrides list in `.project-guide.yml`
2. The file can now be updated with `project-guide update`

## overrides

List all currently overridden files.

```bash
project-guide overrides
```

### Example Output

```
Overridden Files:
  templates/modes/debug-mode.md
    Reason: Added team-specific debugging steps
    Locked: 2026-03-15

  developer/setup.md
    Reason: Customized for our internal toolchain
    Locked: 2026-04-01
```

## purge

Remove all files and configuration from the project.

```bash
project-guide purge [OPTIONS]
```

### Options

- `--force` - Skip confirmation prompt (intent: "I am sure")
- `--no-input` - Skip confirmation (also auto-enabled by `CI=1` or non-TTY stdin)
- `--quiet`, `-q` - Suppress per-file progress output

### Examples

```bash
# Purge with confirmation
project-guide purge

# Purge without confirmation
project-guide purge --force

# Unattended purge (CI / non-interactive)
project-guide purge --no-input --force
```

### What It Does

1. Prompts for confirmation (unless `--force`, `--no-input`, `CI=1`, or non-TTY stdin)
2. Removes the entire `docs/project-guide/` directory
3. Deletes `.project-guide.yml` configuration file

!!! warning
    This operation cannot be undone. Use with caution.

## Global Options

All commands support these global options:

- `--help` - Show help message
- `--version` - Show package version

## Exit Codes

- `0` - Success
- `1` - General error (invalid arguments, unexpected failure, etc.)
- `2` - File I/O error (permission denied, disk full, etc.)
- `3` - Configuration error (missing or invalid `.project-guide.yml`)

## Next Steps

- [Workflow Guide](workflow.md) - See commands in action
- [Override Management](overrides.md) - Learn override best practices
- [Configuration](configuration.md) - Understand configuration options
