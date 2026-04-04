# Commands Reference

project-guide provides seven intuitive commands for managing LLM workflow guides across your projects.

## Command Overview

| Command | Purpose |
|---------|---------|
| `init` | Install guides into a new project |
| `status` | Show which guides are current, outdated, or overridden |
| `update` | Update non-overridden guides to latest versions |
| `override` | Mark a guide as overridden to prevent updates |
| `unoverride` | Remove override status from a guide |
| `overrides` | List all overridden guides |
| `purge` | Remove all guides and configuration |

## init

Install workflow guides into your project.

```bash
project-guide init [OPTIONS]
```

### Options

- `--guides-dir PATH` - Custom directory for guides (default: `docs/guides`)
- `--force` - Overwrite existing guides and configuration

### Examples

```bash
# Initialize with default settings
project-guide init

# Use custom guides directory
project-guide init --guides-dir documentation/workflows

# Force reinstall (overwrites existing files)
project-guide init --force
```

### What It Does

1. Creates the guides directory if it doesn't exist
2. Copies all bundled guides to the directory
3. Creates `.project-guide.yml` configuration file
4. Records the package version for each guide

## status

Display the status of all guides in your project.

```bash
project-guide status
```

### Output

Shows each guide with:
- **Current** ✓ - Guide is up to date
- **Outdated** ⚠ - Newer version available
- **Overridden** 🔒 - Guide is locked (won't be updated)
- **Missing** ✗ - Guide not found in guides directory

### Example Output

```
Guide Status:
  project-guide.md         ✓ Current (v1.1.3)
  best-practices-guide.md  ⚠ Outdated (v1.1.0 → v1.1.3)
  debug-guide.md           🔒 Overridden (v1.1.0)
  documentation-setup-guide.md  ✓ Current (v1.1.3)
```

## update

Update all non-overridden guides to the latest versions.

```bash
project-guide update [OPTIONS]
```

### Options

- `--force` - Update even overridden guides (creates `.bak` backups)

### Examples

```bash
# Update non-overridden guides
project-guide update

# Force update all guides (including overridden)
project-guide update --force
```

### What It Does

1. Checks each guide's version against the package version
2. Updates outdated guides that are not overridden
3. Skips overridden guides (unless `--force` is used)
4. Creates `.bak` backups when updating overridden guides with `--force`
5. Updates package version in configuration

## override

Mark a guide as overridden to prevent automatic updates.

```bash
project-guide override <guide-name> [OPTIONS]
```

### Options

- `--reason TEXT` - Optional reason for the override

### Examples

```bash
# Mark guide as overridden
project-guide override project-guide.md

# With reason
project-guide override project-guide.md --reason "Customized for our team workflow"
```

### What It Does

1. Records the guide as overridden in `.project-guide.yml`
2. Stores the current version
3. Optionally stores the reason
4. Future `update` commands will skip this guide

## unoverride

Remove override status from a guide, allowing it to be updated again.

```bash
project-guide unoverride <guide-name>
```

### Examples

```bash
# Remove override status
project-guide unoverride project-guide.md
```

### What It Does

1. Removes the guide from the overrides list in `.project-guide.yml`
2. The guide can now be updated with `project-guide update`

## overrides

List all currently overridden guides.

```bash
project-guide overrides
```

### Example Output

```
Overridden Guides:
  project-guide.md (v1.1.0)
    Reason: Customized for our team workflow
  
  debug-guide.md (v1.1.2)
    Reason: Added project-specific debugging steps
```

## purge

Remove all guides and configuration from the project.

```bash
project-guide purge [OPTIONS]
```

### Options

- `--force` - Skip confirmation prompt

### Examples

```bash
# Purge with confirmation
project-guide purge

# Purge without confirmation
project-guide purge --force
```

### What It Does

1. Prompts for confirmation (unless `--force` is used)
2. Removes the entire guides directory
3. Deletes `.project-guide.yml` configuration file

!!! warning
    This operation cannot be undone. Use with caution.

## Global Options

All commands support these global options:

- `--help` - Show help message
- `--version` - Show package version

## Exit Codes

- `0` - Success
- `1` - Error (invalid arguments, file not found, etc.)

## Next Steps

- [Workflow Guide](workflow.md) - See commands in action
- [Override Management](overrides.md) - Learn override best practices
- [Configuration](../getting-started/configuration.md) - Understand configuration options
