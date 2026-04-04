# Installation

project-guide can be installed using pip, pipx, or from source.

## Requirements

- Python 3.11 or higher
- pip or pipx package manager

## Install via pip

The simplest way to install project-guide is using pip:

```bash
pip install project-guide
```

This installs project-guide in your current Python environment.

## Install via pipx (Recommended)

For system-wide CLI access without affecting your project's dependencies, use pipx:

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

## Next Steps

- [Quick Start Guide](quick-start.md) - Get started with your first project
- [Configuration](configuration.md) - Learn about configuration options
- [Commands](../user-guide/commands.md) - Explore all available commands
