![project-guide](https://raw.githubusercontent.com/pointmatic/project-guide/main/docs/site/images/project-guide-header-readme.png)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/pointmatic/project-guide/workflows/Tests/badge.svg)](https://github.com/pointmatic/project-guide/actions)
[![PyPI](https://img.shields.io/pypi/v/project-guide.svg)](https://pypi.org/project/project-guide/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://pointmatic.github.io/project-guide/)
[![codecov](https://codecov.io/gh/pointmatic/project-guide/graph/badge.svg)](https://codecov.io/gh/pointmatic/project-guide)

A Python CLI tool that installs, swaps, and synchronizes battle-tested LLM workflow prompts across projects, supporting version tracking and project-specific overrides to keep documentation consistent while preserving customizations.

## Why project-guide?

The `go-project-guide` prompt provides the LLM with a structured workflow:
- Adapts for your current development mode (plan, code, debug, etc.) 
- Lets you stay in charge: guiding features, flow, and taste
- Handles the typing so you can stay focused on the big picture

### How It Works
- Install project-guide in any repository
- Initialize the Project-Guide system. 
- (optional) Set the project mode (plan, code, debug, etc.) 
- Tell your LLM to read the `go-project-guide.md` (in your IDE, or however you prefer).

### Human-in-the-Loop Development

This is "HITLoop" (human-in-the-loop) development: you direct, the LLM executes—It is not vibe-coding. Instead you are following the development closely and interactively guiding and improving the flow. The pace is "flaming agile"—an entire production-ready backend can be completed in 6-12 hours. 

### Customization and Updates

When you customize a prompt for your project, mark it as overridden so future package updates skip it. When you want the latest workflow improvements, run `project-guide update` to sync all non-overridden prompts. 

## Key Features
- 📚 **Battle-Tested Workflows** - Crafted workflow prompts from concept through production release in one place
- **Adaptive** — Switch project between plan, code, and debug modes to get the right instructions for each task
- 🔄 **Version Management** - Track and update all prompt docs in a project with a single command
- 🔒 **Custom Doc Lock** - Lock customized prompts to prevent update overwrites
- **Gentle Force Updates** — Automatic `.bak` files created if you `--force` update a custom prompt document
- 🎨 **CLI Interface** - Eight intuitive commands for all operations
- 🧪 **Well Tested** - 92% test coverage with 112 comprehensive tests
- ⚡ **Zero Configuration** - Works with sensible defaults out of the box
- 🌐 **Cross-Platform** - Runs on macOS, Linux, and Windows with Python 3.11+

## Installation

### Via pip

```bash
pip install project-guide
```

### Via pipx (recommended for CLI coding tools)

```bash
pipx install project-guide
```

## Quick Start

### 1. Initialize in your project

```bash
cd /path/to/your/project
project-guide init
```

This creates:
- `.project-guide.yml` - Configuration file
- `docs/project-guide/` - Mode templates, artifact templates, and metadata
- `docs/specs/go-project-guide.md` - Rendered LLM instructions (default mode)

### 2. Tell your LLM to read the guide

```
Read docs/specs/go-project-guide.md
```

The LLM follows the instructions, asks clarifying questions, and generates artifacts. Type `go` to advance through steps.

### 3. Switch modes as you progress

```bash
project-guide mode plan_concept      # Define problem & solution
project-guide mode plan_features     # Define requirements
project-guide mode plan_tech_spec    # Define architecture
project-guide mode plan_stories      # Break into stories
project-guide mode code_velocity     # Implement stories fast
project-guide mode debug             # Debug with test-first approach
```

Each mode regenerates `docs/specs/go-project-guide.md` with focused instructions for that workflow.

### 4. List available modes

```bash
project-guide mode
```

Output:
```
Current mode: plan_concept

Available modes:
  → default                   Getting started -- full project lifecycle overview
    plan_concept              Generate a high-level concept (problem and solution space)
    plan_features             Generate feature requirements (what the project does)
    plan_tech_spec            Generate a technical specification prompt (how it's built)
    plan_stories              Generate a user stories prompt
    code_velocity             Generate code with velocity
    code_test_first           Generate code with a test-first approach
    debug                     Debug code with a test-first approach
    ...
```

### 5. Update templates

```bash
pip install --upgrade project-guide
project-guide update
```

Overridden templates are skipped. Modified templates prompt for confirmation. Backups are always created before overwrites.

### 6. Customize a template (optional)

```bash
project-guide override templates/modes/debug-mode.md "Custom debugging for this project"
```

## Command Reference

### `init`

Initialize project-guide in the current directory.

```bash
project-guide init [OPTIONS]
```

**Options:**
- `--target-dir PATH` - Directory for templates (default: `docs/project-guide`)
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

### `mode`

Set or show the active development mode.

```bash
project-guide mode [MODE_NAME]
```

**Without argument:** Lists current mode and all available modes.

**With argument:** Switches to the specified mode and re-renders `go-project-guide.md`.

**Examples:**
```bash
# Show current mode and list all modes
project-guide mode

# Switch to velocity coding mode
project-guide mode code_velocity

# Switch to debugging mode
project-guide mode debug
```

### `status`

Show status of all installed templates and current mode.

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
version: "2.0"
installed_version: "2.0.7"
target_dir: "docs/project-guide"
current_mode: "code_velocity"
overrides:
  templates/modes/debug-mode.md:
    reason: "Custom debugging workflow for this project"
    locked_version: "2.0.0"
    last_updated: "2026-04-07"
```

**Fields:**
- `version` - Config file format version
- `installed_version` - Version of templates currently installed
- `target_dir` - Where templates are stored
- `current_mode` - Active development mode
- `overrides` - Map of customized templates with metadata

## Available Modes

### Planning Modes

| Mode | Command | Output |
|------|---------|--------|
| **Concept** | `project-guide mode plan_concept` | `docs/specs/concept.md` |
| **Features** | `project-guide mode plan_features` | `docs/specs/features.md` |
| **Tech Spec** | `project-guide mode plan_tech_spec` | `docs/specs/tech-spec.md` |
| **Stories** | `project-guide mode plan_stories` | `docs/specs/stories.md` |
| **Phase** | `project-guide mode plan_phase` | New phase added to stories |

### Coding Modes

| Mode | Command | Workflow |
|------|---------|----------|
| **Velocity** | `project-guide mode code_velocity` | Direct commits, fast iteration |
| **Test-First** | `project-guide mode code_test_first` | TDD red-green-refactor cycle |
| **Debug** | `project-guide mode debug` | Test-driven debugging |

### Documentation Modes

| Mode | Command | Output |
|------|---------|--------|
| **Branding** | `project-guide mode document_brand` | `docs/specs/brand-descriptions.md` |
| **Landing Page** | `project-guide mode document_landing` | GitHub Pages + MkDocs docs |

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
