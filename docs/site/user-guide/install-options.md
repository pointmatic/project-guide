# Installation

project-guide can be installed via pyve (recommended), pip, pipx, or from source.

## Requirements

- Python 3.11 or higher
- pyve, pip, or pipx package manager

project-guide depends on Jinja2 for its mode-driven templating system. This is installed automatically as a dependency.

## Install via pyve (recommended)

If you use [pyve](https://pointmatic.github.io/pyve/), let pyve install and manage Project-Guide globally for you:

```bash
pyve self install
```

`pyve self install` provisions project-guide in pyve's toolchain venv and creates a `~/.local/bin/project-guide` shim, so a single install on your `PATH` serves every project — no per-project `pip install` needed. project-guide keeps all per-project state in each project's `.project-guide.yml` and `docs/project-guide/` tree, so the shared install is never written to. When pyve is detected at `init` time, project-guide's onboarding, `status`, and `heal` output adapt to pyve-managed hosting.

## Install via pip

The simplest way to install project-guide is using pip:

```bash
pip install project-guide
```

This installs project-guide and its dependencies (including Jinja2) in your current Python environment.

## Install via pipx (recommended for standalone CLI use)

If you don't use pyve, pipx is the best way to get system-wide CLI access without affecting your project's dependencies:

```bash
pipx install project-guide
```

pipx installs the tool in an isolated environment while making the CLI command globally available.

If you don't have pipx installed:

```bash
# On macOS/Linux
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# On Windows
py -m pip install --user pipx
py -m pipx ensurepath
```

## Install from Source

To install the latest development version from GitHub:

```bash
git clone https://github.com/pointmatic/project-guide.git
cd project-guide
pip install -e .
```

For development with all optional dependencies:

```bash
pip install -e ".[dev,docs]"
```

## Verify Installation

After installation, verify that project-guide is available:

```bash
project-guide --version
```

You should see the version number displayed.

## Shell Completion (Optional)

Enable Tab completion for `project-guide` commands, flags, and mode names. Add the appropriate line to your shell's startup file.

### Bash

Add to `~/.bashrc`:

```bash
eval "$(_PROJECT_GUIDE_COMPLETE=bash_source project-guide)"
```

### Zsh

Add to `~/.zshrc`:

```bash
eval "$(_PROJECT_GUIDE_COMPLETE=zsh_source project-guide)"
```

### Fish

Add to `~/.config/fish/completions/project-guide.fish`:

```bash
_PROJECT_GUIDE_COMPLETE=fish_source project-guide | source
```

After updating your shell config, restart your shell (or `source` the file). Now you can:

- `project-guide <TAB>` — complete command names (`init`, `mode`, `status`, etc.)
- `project-guide mode <TAB>` — complete mode names (`default`, `plan_concept`, `code_direct`, etc.) — reads `.metadata.yml` from your current project
- `project-guide --<TAB>` — complete flags

Mode name completion is dynamic and reads the active project's `.metadata.yml`, so it works correctly even if you have custom modes.

## Next Steps

- [Getting Started](../getting-started.md) - Get started with your first project
- [Configuration](configuration.md) - Learn about configuration options
- [Commands](commands.md) - Explore all available commands
