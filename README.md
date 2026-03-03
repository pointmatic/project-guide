# project-guides

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/pointmatic/project-guides/workflows/Tests/badge.svg)](https://github.com/pointmatic/project-guides/actions)
[![PyPI](https://img.shields.io/pypi/v/project-guides.svg)](https://pypi.org/project/project-guides/)

Manage LLM development workflow documentation across projects. `project-guides` provides centralized, versioned guide templates with project-specific override capabilities.

## Why project-guides?

When working with LLMs on software projects, consistent workflow documentation is critical. `project-guides` solves the problem of keeping development guides synchronized across multiple projects while allowing project-specific customizations.

**Key Features:**
- 📚 **Centralized Templates** - Maintain workflow guides in one place
- 🔄 **Version Management** - Track and update guides across projects
- ✏️ **Override Support** - Customize guides per project without losing sync
- 🔒 **Backup Protection** - Automatic backups when updating overridden guides
- 🎨 **CLI Interface** - Simple commands for all operations
- 🧪 **Well Tested** - 82% test coverage with 48 comprehensive tests

## Installation

### Via pip

```bash
pip install project-guides
```

### Via pipx (recommended for CLI tools)

```bash
pipx install project-guides
```

## Quick Start

### 1. Initialize guides in your project

```bash
cd /path/to/your/project
project-guides init
```

This creates:
- `.project-guides.yml` - Configuration file
- `docs/guides/` - Directory with guide templates

### 2. Check guide status

```bash
project-guides status
```

Output:
```
project-guides v0.15.0 (installed: v0.15.0)

Guides status:
  ✓ project-guide.md                         v0.15.0  (current)
  ✓ best-practices-guide.md                  v0.15.0  (current)
  ✓ debug-guide.md                           v0.15.0  (current)

All guides are up to date.
```

### 3. Customize a guide (optional)

```bash
project-guides override debug-guide.md "Custom debugging workflow for this project"
```

### 4. Update guides to latest version

```bash
project-guides update
```

Overridden guides are skipped by default. Use `--force` to update them (creates backups).

## Command Reference

### `init`

Initialize project-guides in the current directory.

```bash
project-guides init [OPTIONS]
```

**Options:**
- `--target-dir PATH` - Directory for guides (default: `docs/guides`)
- `--force` - Overwrite existing configuration

**Examples:**
```bash
# Initialize with default settings
project-guides init

# Use custom directory
project-guides init --target-dir documentation/workflows

# Force reinitialize
project-guides init --force
```

### `status`

Show status of all installed guides.

```bash
project-guides status
```

**Output includes:**
- Current package version
- Installed version in project
- Status of each guide (current, outdated, overridden, missing)
- Override reasons

### `update`

Update guides to the latest version.

```bash
project-guides update [OPTIONS]
```

**Options:**
- `--guides NAME` - Update specific guides only (repeatable)
- `--force` - Update even overridden guides (creates backups)
- `--dry-run` - Show what would change without applying

**Examples:**
```bash
# Update all guides (skips overridden)
project-guides update

# Update specific guides
project-guides update --guides project-guide.md --guides debug-guide.md

# Force update all (creates backups for overridden)
project-guides update --force

# Preview changes
project-guides update --dry-run
```

### `override`

Mark a guide as customized to prevent automatic updates.

```bash
project-guides override GUIDE_NAME REASON
```

**Arguments:**
- `GUIDE_NAME` - Name of the guide file
- `REASON` - Why this guide is customized

**Example:**
```bash
project-guides override debug-guide.md "Custom debugging workflow with project-specific tools"
```

### `unoverride`

Remove override status from a guide.

```bash
project-guides unoverride GUIDE_NAME
```

**Example:**
```bash
project-guides unoverride debug-guide.md
```

### `overrides`

List all overridden guides.

```bash
project-guides overrides
```

**Output:**
```
Overridden guides:

debug-guide.md
  Reason: Custom debugging workflow with project-specific tools
  Since: v0.12.0
  Last updated: 2026-03-03
```

## Configuration

The `.project-guides.yml` file stores project configuration:

```yaml
version: "1.0"
installed_version: "0.15.0"
target_dir: "docs/guides"
overrides:
  debug-guide.md:
    reason: "Custom debugging workflow"
    version: "0.12.0"
    last_updated: "2026-03-03"
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

**Problem:** Running commands outside a project-guides initialized directory.

**Solution:**
```bash
project-guides init
```

### "Guide already exists"

**Problem:** Trying to initialize when guides already exist.

**Solution:**
```bash
# Use --force to overwrite
project-guides init --force

# Or manually remove existing guides
rm -rf docs/guides .project-guides.yml
project-guides init
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
project-guides overrides

# Force update if needed
project-guides update --force
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/pointmatic/project-guides.git
cd project-guides

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=project_guides --cov-report=term-missing

# Run specific test file
pytest tests/test_cli.py -v
```

### Code Quality

```bash
# Linting
ruff check project_guides/ tests/

# Type checking
mypy project_guides/

# Format code
ruff format project_guides/ tests/
```

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
mypy project_guides/

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

## Support

- **Issues:** [GitHub Issues](https://github.com/pointmatic/project-guides/issues)
- **Discussions:** [GitHub Discussions](https://github.com/pointmatic/project-guides/discussions)
- **Documentation:** [Full Documentation](https://github.com/pointmatic/project-guides/tree/main/docs)

---

**Made with ❤️ for LLM-assisted development workflows**
