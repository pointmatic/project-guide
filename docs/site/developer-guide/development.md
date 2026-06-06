# Development Setup

Guide for setting up a development environment for project-guide.

## Prerequisites

- Python 3.11 or higher
- Git
- [pyve](https://pointmatic.github.io/pyve/) — this project is pyve-managed; pyve provisions the environments

## Clone the Repository

```bash
git clone https://github.com/pointmatic/project-guide.git
cd project-guide
```

## Set Up the Environment

project-guide uses pyve's two-environment model: a main runtime env plus a separate dev testenv. pytest, ruff, and mypy live in the **testenv**, not the main venv.

```bash
# Main environment: editable install
pyve run pip install -e .

# Dev testenv: pytest, ruff, mypy
pyve testenv init
pyve testenv install -r requirements-dev.txt
```

## Verify Installation

```bash
# Check package is installed
project-guide --version

# Run tests
pyve test

# Check linting
pyve testenv run ruff check project_guide tests

# Check types
pyve testenv run mypy project_guide
```

## Development Workflow

### 1. Create a Branch

```bash
git switch -c feature/your-feature-name
```

### 2. Make Changes

Edit files in `project_guide/` or `tests/`

### 3. Run Tests

```bash
# Run all tests
pyve test

# Run with coverage
pyve test --cov=project_guide

# Run specific test file
pyve test tests/test_cli.py

# Run specific test
pyve test tests/test_cli.py::test_init_in_empty_directory
```

### 4. Check Code Quality

```bash
# Lint code
pyve testenv run ruff check project_guide tests

# Format code
pyve testenv run ruff format project_guide tests

# Type check
pyve testenv run mypy project_guide
```

### 5. Update Documentation

If you changed user-facing functionality:

```bash
# Edit documentation
vim docs/site/user-guide/commands.md

# Build and preview
mkdocs serve
# Open http://127.0.0.1:8000
```

### 6. Commit Changes

```bash
git add .
git commit -m "Add feature: description"
```

## Project Structure

### Main Package

```
project_guide/
├── __init__.py               # Package initialization
├── __main__.py               # CLI entry point
├── cli.py                    # CLI commands implementation
├── config.py                 # Configuration model
├── metadata.py               # Metadata loading and validation
├── render.py                 # Jinja2 template rendering
├── sync.py                   # File synchronization logic
├── exceptions.py             # Custom exception classes
├── version.py                # Version information
└── templates/                # Bundled templates
    └── project-guide/        # Project guide templates
        ├── .metadata.yml     # Mode and artifact definitions
        ├── README.md         # Template README
        ├── developer/        # Developer guide templates
        └── templates/        # Jinja2 templates
            ├── modes/        # Mode templates (*.md)
            ├── artifacts/    # Artifact templates (*.md)
            └── go.md         # Go template
```

### Tests

```
tests/
├── __init__.py
├── test_cli.py                       # CLI command tests (~200)
├── test_render.py                    # Render tests, incl. per-mode (~170)
├── test_actions.py                   # Deterministic actions / archive (~53)
├── test_runtime.py                   # Runtime helpers (~52)
├── test_stories.py                   # Story parsing / git-push messages (~35)
├── test_sync.py                      # Sync logic tests (~25)
├── test_config.py                    # Configuration tests (~19)
├── test_metadata.py                  # Metadata tests (~18)
├── test_archive_stories_mode.py      # archive_stories mode (~8)
├── test_integration.py               # Integration tests (~6)
├── test_purge.py                     # Purge command tests (~5)
└── test_cross_repo_contract.py       # Pyve cross-repo contracts (~3)
```

### Documentation

```
docs/
└── site/                     # MkDocs documentation
    ├── getting-started.md
    ├── user-guide/
    ├── developer-guide/
    └── about/
```

## Running Tests

### Basic Test Run

```bash
pyve test
```

### With Coverage Report

```bash
pyve test --cov=project_guide --cov-report=html
open htmlcov/index.html
```

### Verbose Output

```bash
pyve test -v
```

### Stop on First Failure

```bash
pyve test -x
```

### Run Specific Tests

```bash
# By file
pyve test tests/test_cli.py

# By test name
pyve test tests/test_cli.py::test_init_in_empty_directory

# By pattern
pyve test -k "test_init"
```

## Code Quality Tools

### Ruff (Linter and Formatter)

```bash
# Check for issues
pyve testenv run ruff check project_guide tests

# Fix auto-fixable issues
pyve testenv run ruff check --fix project_guide tests

# Format code
pyve testenv run ruff format project_guide tests
```

### Mypy (Type Checker)

```bash
# Type check
pyve testenv run mypy project_guide

# Strict mode
pyve testenv run mypy --strict project_guide
```

## Building Documentation

### Local Development

```bash
# Serve with live reload
mkdocs serve

# Open http://127.0.0.1:8000
```

### Build Static Site

```bash
# Build to site/ directory
mkdocs build

# Build with strict mode (fail on warnings)
mkdocs build --strict
```

## Debugging

### Using pdb

Add breakpoint in code:

```python
import pdb; pdb.set_trace()
```

Run tests:

```bash
pyve test tests/test_cli.py::test_init_in_empty_directory
```

### Using pytest debugging

```bash
# Drop into pdb on failure
pyve test --pdb

# Drop into pdb on first failure
pyve test -x --pdb
```

### Verbose CLI Output

```bash
# Run CLI with Python for better error messages
python -m project_guide init
```

## Common Tasks

### Add a New Command

1. Add command function in `project_guide/cli.py`
2. Add tests in `tests/test_cli.py`
3. Update documentation in `docs/site/user-guide/commands.md`
4. Run tests and linters

### Add a New Mode

1. Create a mode template in `project_guide/templates/project-guide/templates/modes/`
2. Add the mode to `.metadata.yml` in `project_guide/templates/project-guide/`
3. Test rendering with `project-guide init` and select the new mode
4. Verify the parametrized test in `test_render.py` picks up the new mode
5. Document changes in `CHANGELOG.md`

### Update a Template

1. Edit the template in `project_guide/templates/project-guide/templates/`
2. Test with `project-guide init` followed by mode selection to verify rendering
3. Update version in `project_guide/version.py` if needed
4. Document changes in `CHANGELOG.md`

### Add a New Artifact

1. Create an artifact template in `project_guide/templates/project-guide/templates/artifacts/`
2. Add the artifact to `.metadata.yml`
3. Add tests for the new artifact
4. Update documentation

## Troubleshooting

### Import Errors

Ensure the package is installed in editable mode in the main env:

```bash
pyve run pip install -e .
```

### Test Failures

Refresh the dev testenv dependencies:

```bash
pyve testenv install -r requirements-dev.txt
```

### Type Check Errors

Ignore specific errors if needed:

```python
# type: ignore[error-code]
```

## Next Steps

- [Contributing Guide](contributing.md) - Contribution guidelines
- [Testing Guide](testing.md) - Detailed testing information
