# Configuration

project-guide uses a simple YAML configuration file to store project-specific settings.

## Configuration File

The `.project-guide.yml` file is created automatically when you run `project-guide init`. It's stored in your project root.

### Default Configuration

```yaml
version: "2.0"
installed_version: "2.20.0"
target_dir: "docs/project-guide"
metadata_file: ".metadata.yml"
current_mode: "code_direct"
test_first: false
pyve_version: "3.2.2"        # bare version; null if pyve was never detected
pyve_installed: true         # renders the Pyve guidance into go.md
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

The version of [pyve](https://pointmatic.github.io/pyve/) that project-guide has seen, stored bare (`3.2.2`), or `null` if pyve was never detected. project-guide adapts to pyve-managed hosting from this cached value — the rendered `go.md` onboarding, the `project-guide status` footer, and the `project-guide heal` local-install check all read it rather than re-running `pyve --version` on every command.

At `init` the value is resolved from the first available of: the `--pyve-version` flag → the `PYVE_VERSION` environment variable → a `pyve --version` probe. A tool that installs project-guide on your behalf and already knows pyve's version can pass it directly, which skips the probe:

```bash
project-guide init --pyve-version 3.2.2
```

If detection misses, `init` says so on stderr rather than failing — pyve simply may not have been on `PATH` at that moment.

### `pyve_installed`

Whether the Pyve guidance section is rendered into `go.md`. It is a field in its own right, not a reading of `pyve_version`: the guidance is the part of the guide that tells your LLM to use `pyve test` rather than `pyve run pytest`, and one unlucky probe should not be able to remove it permanently.

**If you install pyve after running `init`,** run `project-guide update` or switch modes (`project-guide mode <name>`) — both re-detect and restore the guidance. You do not need `init --force`.

Detection only ever turns this **on**. A later failed probe leaves it alone, so a rehashing `PATH` or a slow first run cannot strip the guidance back out. To opt out of the section deliberately, set it to `false` by hand — though note that a subsequent successful detection turns it back on, so the opt-out holds only while pyve is genuinely unavailable.

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

project-guide supports Tab completion for commands, flags, and mode names in **bash and zsh** (fish is not yet supported). Completion is opt-in, and project-guide installs it for you:

```bash
project-guide completion install
```

Restart your shell (or `source` the rc file it names). Then:

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
