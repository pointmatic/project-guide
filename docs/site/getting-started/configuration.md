# Configuration

project-guide uses a simple YAML configuration file to store project-specific settings.

## Configuration File

The `.project-guide.yml` file is created automatically when you run `project-guide init`. It's stored in your project root.

### Default Configuration

```yaml
version: "1.0"
package_version: "1.1.3"
guides_dir: "docs/guides"
overrides: {}
```

## Configuration Fields

### `version`

The configuration file format version. Currently `"1.0"`.

### `package_version`

The version of the project-guide package that was used to install or last update the guides. This is used to track which guides are outdated.

### `guides_dir`

The directory where guides are installed. Defaults to `docs/guides`.

You can customize this:

```yaml
guides_dir: "documentation/workflows"
```

### `overrides`

A mapping of guide names to override metadata. Managed automatically by the `override` and `unoverride` commands.

Example:

```yaml
overrides:
  project-guide.md:
    version: "1.1.0"
    reason: "Customized for our specific workflow"
```

## Zero Configuration

project-guide works out of the box with sensible defaults. You don't need to create or modify the configuration file manually unless you want to customize behavior.

## Custom Guides Directory

To use a custom guides directory, specify it during initialization:

```bash
project-guide init --guides-dir custom/path
```

Or modify the configuration file:

```yaml
guides_dir: "custom/path"
```

All commands will respect this setting.

## Version Tracking

project-guide automatically tracks:
- Which package version installed each guide
- Which guides have been overridden
- The version at which a guide was overridden

This enables smart updates that:
- Only update non-overridden guides
- Show which guides are outdated
- Preserve your customizations

## Manual Configuration

While not recommended, you can manually edit `.project-guide.yml` if needed. The file uses standard YAML syntax.

!!! warning
    Manual edits should be done carefully. Invalid YAML will cause commands to fail.

## Next Steps

- [Commands Reference](../user-guide/commands.md) - Learn all available commands
- [Override Management](../user-guide/overrides.md) - Understand the override system
- [Workflow Guide](../user-guide/workflow.md) - See configuration in action
