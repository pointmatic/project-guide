# Configuration

project-guide uses a simple YAML configuration file to store project-specific settings.

## Configuration File

The `.project-guide.yml` file is created automatically when you run `project-guide init`. It's stored in your project root.

### Default Configuration

```yaml
version: "2.0"
installed_version: "2.17.0"
target_dir: "docs/project-guide"
metadata_file: ".metadata.yml"
current_mode: "code_direct"
test_first: false
pyve_version: "2.6.2"        # null if pyve is not installed
overrides: {}
```

## Configuration Fields

### `version`

The configuration file format version. Currently `"2.0"`.

### `installed_version`

The version of the project-guide package that was used to install or last update the files. Used alongside content hashing to determine which files need updating.

### `target_dir`

The directory where project-guide files are installed. Defaults to `docs/project-guide`.

You can customize this:

```yaml
target_dir: "documentation/workflows"
```

### `metadata_file`

The name of the metadata file used to track file state. Defaults to `.metadata.yml`.

### `current_mode`

Tracks the active development mode. Changed via the `project-guide mode` command. project-guide includes 17 modes to match different development workflows.

### `test_first`

The default coding approach. `false` (the default) starts coding in `code_direct` mode; `true` prefers `code_test_first` (test-driven development). Set at `init` via the `--test-first` flag.

### `pyve_version`

The version of [pyve](https://pointmatic.github.io/pyve/) detected at `init` time, or `null` if pyve was not installed. When set, project-guide adapts to pyve-managed hosting — the rendered `go.md` onboarding, the `project-guide status` footer, and the `project-guide heal` local-install check all read this cached value (pyve is not re-detected on every command). If you install pyve after running `init`, re-run `project-guide init --force` to refresh the detection.

### `overrides`

A mapping of template paths to override metadata. Managed automatically by the `override` and `unoverride` commands.

Example:

```yaml
overrides:
  templates/modes/debug-mode.md:
    reason: "Custom debugging workflow for our project"
    locked_version: "2.0.10"
    last_updated: "2026-03-15"
```

Override fields:

- `reason` -- Why the override was created
- `locked_version` -- The package version when the override was set
- `last_updated` -- When the override was last modified

### `metadata_overrides`

An optional mapping for per-project patches to individual mode fields, without editing the bundled `.metadata.yml`. Only `next_mode`, `files_exist`, `info`, and `description` are patchable; unmentioned fields are left unchanged.

```yaml
metadata_overrides:
  plan_stories:
    next_mode: scaffold_project
```

## Zero Configuration

project-guide works out of the box with sensible defaults. You don't need to create or modify the configuration file manually unless you want to customize behavior.

## Custom Target Directory

To use a custom target directory, specify it during initialization:

```bash
project-guide init --target-dir custom/path
```

Or modify the configuration file:

```yaml
target_dir: "custom/path"
```

All commands will respect this setting.

## Shell Completion

project-guide supports Tab completion for commands, flags, and mode names in bash, zsh, and fish. Completion is opt-in — add a one-line `eval` to your shell startup file.

**Bash** (`~/.bashrc`):
```bash
eval "$(_PROJECT_GUIDE_COMPLETE=bash_source project-guide)"
```

**Zsh** (`~/.zshrc`):
```bash
eval "$(_PROJECT_GUIDE_COMPLETE=zsh_source project-guide)"
```

**Fish** (`~/.config/fish/completions/project-guide.fish`):
```bash
_PROJECT_GUIDE_COMPLETE=fish_source project-guide | source
```

After updating your shell config, restart your shell (or `source` the file). Then:

- `project-guide <TAB>` completes command names (`init`, `mode`, `status`, etc.)
- `project-guide mode <TAB>` completes mode names from the active project's `.metadata.yml` (dynamic — works with any custom modes)
- `project-guide --<TAB>` completes flags

See [Installation Options](install-options.md#shell-completion-optional) for more details.

## Content Hash Sync

project-guide uses content hashing (not version numbers) to track file state. This enables smart updates that:

- Detect exactly which files have changed upstream
- Only update non-overridden files
- Show which files are current, outdated, or overridden
- Preserve your customizations

## Manual Configuration

While not recommended, you can manually edit `.project-guide.yml` if needed. The file uses standard YAML syntax.

!!! warning
    Manual edits should be done carefully. Invalid YAML will cause commands to fail.

## Next Steps

- [Commands Reference](../user-guide/commands.md) - Learn all available commands
- [Override Management](../user-guide/overrides.md) - Understand the override system
- [Workflow Guide](../user-guide/workflow.md) - See configuration in action
