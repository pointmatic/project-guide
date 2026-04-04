![project-guide](https://raw.githubusercontent.com/pointmatic/project-guide/main/docs/site/images/project-guide-header-readme.png)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/pointmatic/project-guide/workflows/Tests/badge.svg)](https://github.com/pointmatic/project-guide/actions)
[![PyPI](https://img.shields.io/pypi/v/project-guide.svg)](https://pypi.org/project/project-guide/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://pointmatic.github.io/project-guide/)

A Python CLI tool that installs and synchronizes battle-tested LLM workflow guides across projects, supporting version tracking and project-specific overrides to keep documentation consistent while preserving customizations.

## Why project-guide?

Install project-guide in any repository with `pip install project-guide`, run `project-guide init`, then tell your LLM to "Read `docs/guides/project-guide.md` and start." The guide walks the LLM through planning documents, breaking work into stories, and implementing each story step-by-step. You just say "proceed" after each step. The developer stays in charge—guiding features, flow, and taste—while the LLM handles the typing.

This is "HITLoop" (human-in-the-loop) development: the developer directs, the LLM executes. The pace is "flaming agile"—an entire production-ready backend can be completed in 6-12 hours.

**Key Features:**
- 📚 **Battle-Tested Workflows** - Crafted guides from concept through production release
- 🔄 **Version Management** - Track and update guides across projects automatically
- ✏️ **Project-Specific Overrides** - Lock customized guides to prevent overwrites
- 🔒 **Automatic Backups** - Preserve customizations when forcing updates
- 🎨 **CLI Interface** - Seven intuitive commands for all operations
- 🧪 **Well Tested** - 82% test coverage with 59 comprehensive tests
- ⚡ **Zero Configuration** - Works with sensible defaults out of the box
- 🌐 **Cross-Platform** - Runs on macOS, Linux, and Windows with Python 3.11+

## Installation

### Via pip

```bash
pip install project-guide
```

### Via pipx (recommended for CLI tools)

```bash
pipx install project-guide
```

## Quick Start

### 1. Initialize guides in your project

```bash
cd /path/to/your/project
project-guide init
```

This creates:
- `.project-guide.yml` - Configuration file
- `docs/guides/` - Directory with guide templates

### 2. Check guide status

```bash
project-guide status
```

Output:
```
project-guide v1.5.1 (installed: v1.2.7)

Guides status:
  ⚠ README.md                                v1.2.7  (update available)
  ⚠ best-practices-guide.md                  v1.2.7  (update available)
  ⚠ debug-guide.md                           v1.2.7  (update available)
  ⚠ descriptions-guide.md                    v1.2.7  (update available)
  ⚠ developer/codecov-setup-guide.md         v1.2.7  (update available)
  ⚠ developer/production-mode.md             v1.2.7  (update available)
  ⚠ documentation-setup-guide.md             v1.2.7  (update available)
  ⚠ project-guide.md                         v1.2.7  (update available)

8 updates available
```

### 3. Update guides to latest version

```bash
project-guide update
```

Overridden guides are skipped by default. Modified guides prompt "Backup and overwrite?" — a `.bak` file is always created before any overwrite. Use `--force` to skip the prompt and overwrite all modified guides automatically (backups still created).

Output:
```
Updated:
  ✓ README.md
  ✓ best-practices-guide.md
  ✓ debug-guide.md
  ✓ descriptions-guide.md
  ✓ developer/codecov-setup-guide.md
  ✓ developer/production-mode.md
  ✓ documentation-setup-guide.md
  ✓ project-guide.md

✓ Successfully updated 8 guides.
```

### 4. Customize a guide (optional)

```bash
project-guide override debug-guide.md "Custom debugging workflow for this project"
```

## Command Reference

### `init`

Initialize project-guide in the current directory.

```bash
project-guide init [OPTIONS]
```

**Options:**
- `--target-dir PATH` - Directory for guides (default: `docs/guides`)
- `--force` - Overwrite existing configuration

**Examples:**
```bash
# Initialize with default settings
project-guide init

# Use custom directory
project-guide init --target-dir documentation/workflows

# Force reinitialize
project-guide init --force
```

### `status`

Show status of all installed guides.

```bash
project-guide status
```

**Output includes:**
- Current package version
- Installed version in project
- Status of each guide (current, outdated, overridden, missing)
- Override reasons

### `update`

Update guides to the latest version.

```bash
project-guide update [OPTIONS]
```

**Options:**
- `--guides NAME` - Update specific guides only (repeatable)
- `--force` - Update even overridden guides (creates backups)
- `--dry-run` - Show what would change without applying

**Examples:**
```bash
# Update all guides (skips overridden)
project-guide update

# Update specific guides
project-guide update --guides project-guide.md --guides debug-guide.md

# Force update all (creates backups for overridden)
project-guide update --force

# Preview changes
project-guide update --dry-run
```

### `override`

Mark a guide as customized to prevent automatic updates.

```bash
project-guide override GUIDE_NAME REASON
```

**Arguments:**
- `GUIDE_NAME` - Name of the guide file
- `REASON` - Why this guide is customized

**Example:**
```bash
project-guide override debug-guide.md "Custom debugging workflow with project-specific tools"
```

### `unoverride`

Remove override status from a guide.

```bash
project-guide unoverride GUIDE_NAME
```

**Example:**
```bash
project-guide unoverride debug-guide.md
```

### `overrides`

List all overridden guides.

```bash
project-guide overrides
```

**Output:**
```
Overridden guides:

debug-guide.md
  Reason: Custom debugging workflow with project-specific tools
  Since: v0.12.0
  Last updated: 2026-03-03
```

### `purge`

Remove all project-guide files from the current project.

```bash
project-guide purge [OPTIONS]
```

**Options:**
- `--force` - Skip confirmation prompt

**Examples:**
```bash
# Purge with confirmation prompt
project-guide purge

# Purge without confirmation
project-guide purge --force
```

**What gets removed:**
- `.project-guide.yml` configuration file
- Guides directory (e.g., `docs/guides/`) and all contents

**Warning:** This action cannot be undone. Use with caution.

## Configuration

The `.project-guide.yml` file stores project configuration:

```yaml
version: "1.0"
installed_version: "1.1.2"
target_dir: "docs/guides"
overrides:
  debug-guide.md:
    reason: "Custom debugging workflow with project-specific tools"
    locked_version: "1.0.0"
    last_updated: "2026-03-09"
```

**Fields:**
- `version` - Config file format version
- `installed_version` - Version of guides currently installed
- `target_dir` - Where guides are stored
- `overrides` - Map of customized guides with metadata

## Available Guides

### Core Guides

- **`project-guide.md`** - Complete workflow for starting new projects with LLMs
- **`best-practices-guide.md`** - Development best practices and lessons learned
- **`debug-guide.md`** - Debugging strategies and troubleshooting workflows

### Documentation Guides

- **`documentation-setup-guide.md`** - Setting up MkDocs documentation
- **`README.md`** - README template and guidelines

### Developer Guides

- **`developer/codecov-setup-guide.md`** - Code coverage with Codecov
- **`developer/github-actions-guide.md`** - CI/CD with GitHub Actions

## Troubleshooting

### "Configuration file not found"

**Problem:** Running commands outside a project-guide initialized directory.

**Solution:**
```bash
project-guide init
```

### "Guide already exists"

**Problem:** Trying to initialize when guides already exist.

**Solution:**
```bash
# Use --force to overwrite
project-guide init --force

# Or manually remove existing guides
rm -rf docs/guides .project-guide.yml
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

**Problem:** Guides show as current but you expect updates.

**Solution:**
```bash
# Check if guide is overridden
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
git checkout -b feature/your-feature-name

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

📚 **Full documentation is available at [pointmatic.github.io/project-guide](https://pointmatic.github.io/project-guide/)**

- [Getting Started](https://pointmatic.github.io/project-guide/getting-started/installation/) - Installation and quick start
- [User Guide](https://pointmatic.github.io/project-guide/user-guide/commands/) - Commands, workflows, and override management
- [Developer Guide](https://pointmatic.github.io/project-guide/developer-guide/contributing/) - Contributing and development setup
- [Workflow Guides](docs/guides/) - Bundled LLM workflow guides in your project

## Support

- **Issues:** [GitHub Issues](https://github.com/pointmatic/project-guide/issues)
- **Discussions:** [GitHub Discussions](https://github.com/pointmatic/project-guide/discussions)
- **Documentation:** [GitHub Pages](https://pointmatic.github.io/project-guide/)

---

**Made with ❤️ for LLM-assisted development workflows**
