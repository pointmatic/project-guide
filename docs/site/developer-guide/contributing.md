# Contributing

Thank you for your interest in contributing to project-guide! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful and constructive in all interactions with the project and community.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check if the issue already exists in [GitHub Issues](https://github.com/pointmatic/project-guide/issues)
2. If not, create a new issue with:
   - Clear description of the problem or feature
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Your environment (OS, Python version, package version)

### Suggesting Improvements

For template improvements or new features:

1. Open a [GitHub Discussion](https://github.com/pointmatic/project-guide/discussions)
2. Describe your suggestion and use case
3. Discuss with maintainers before implementing

### Submitting Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/project-guide.git
   cd project-guide
   ```

2. **Create a branch**
   ```bash
   git switch -c feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   pyve run pip install -e .                       # main env: editable install
   pyve env init                               # create the dev testenv
   pyve env install -r requirements-dev.txt    # pytest, ruff, mypy
   ```

4. **Make your changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

5. **Run tests**
   ```bash
   pyve test
   ```

6. **Run linters**
   ```bash
   pyve env run ruff check project_guide tests
   pyve env run mypy project_guide
   ```

7. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

8. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

9. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Describe your changes

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Keep functions focused and small
- Write descriptive variable names

### Testing

- Write tests for new features
- Maintain or improve test coverage (minimum 85%, currently 90%)
- Run tests with `pyve test` (pytest lives in the dev testenv)
- Test edge cases and error conditions
- 596 tests across 12 test files

### Documentation

- Update docstrings for modified functions
- Update user documentation for user-facing changes
- Update CHANGELOG.md with your changes
- Keep documentation clear and concise

### Template Improvements

When improving templates:

1. **Test rendering**: Verify templates render correctly with `project-guide init` and mode selection
2. **Be specific**: Provide concrete steps, not vague instructions
3. **Include examples**: Show what good output looks like
4. **Consider edge cases**: Handle common variations
5. **Maintain consistency**: Follow existing template structure

## Project Structure

```
project-guide/
├── project_guide/              # Main package
│   ├── cli.py                  # CLI commands
│   ├── config.py               # Configuration handling
│   ├── metadata.py             # Metadata loading and validation
│   ├── render.py               # Jinja2 template rendering
│   ├── sync.py                 # File synchronization
│   ├── exceptions.py           # Custom exception classes
│   ├── version.py              # Version information
│   └── templates/              # Bundled templates
│       └── project-guide/      # Project guide templates
│           ├── .metadata.yml   # Mode and artifact definitions
│           ├── README.md       # Template README
│           ├── developer/      # Developer guide templates
│           └── templates/      # Jinja2 templates
│               ├── modes/      # Mode templates (*.md)
│               ├── artifacts/  # Artifact templates (*.md)
│               └── go.md       # Go template
├── tests/                      # Test suite (596 tests, 90% coverage)
│   ├── test_cli.py             # CLI command tests (~200)
│   ├── test_render.py          # Render tests, incl. per-mode (~170)
│   ├── test_actions.py         # Deterministic actions / archive (~53)
│   ├── test_runtime.py         # Runtime helpers (~52)
│   ├── test_stories.py         # Story parsing / git-push messages (~35)
│   ├── test_sync.py            # Sync logic tests (~25)
│   ├── test_config.py          # Configuration tests (~19)
│   ├── test_metadata.py        # Metadata tests (~18)
│   ├── test_archive_stories_mode.py  # archive_stories mode (~8)
│   ├── test_integration.py     # Integration tests (~6)
│   ├── test_purge.py           # Purge command tests (~5)
│   └── test_cross_repo_contract.py   # Pyve cross-repo contracts (~3)
├── docs/                       # Documentation
│   └── site/                   # MkDocs documentation
└── pyproject.toml              # Package configuration
```

### Dependencies

**Runtime:**

- click
- jinja2
- pyyaml
- packaging

**Development:**

- ruff
- mypy
- pytest-cov

## Testing Locally

### Run All Tests

```bash
pyve test
```

### Run Specific Tests

```bash
pyve test tests/test_cli.py
pyve test tests/test_cli.py::test_init_in_empty_directory
```

### Check Coverage

```bash
pyve test --cov=project_guide --cov-report=html
open htmlcov/index.html
```

### Run Linters

```bash
# Check code style
pyve env run ruff check project_guide tests

# Type checking
pyve env run mypy project_guide

# Format code
pyve env run ruff format project_guide tests
```

## Building Documentation

### Build MkDocs Site

```bash
mkdocs build
```

### Serve Locally

```bash
mkdocs serve
# Open http://127.0.0.1:8000
```

## Release Process

(For maintainers)

1. Update version in `project_guide/version.py`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create and push tag
5. GitHub Actions will build and publish to PyPI

## Getting Help

- [GitHub Discussions](https://github.com/pointmatic/project-guide/discussions) - Ask questions
- [GitHub Issues](https://github.com/pointmatic/project-guide/issues) - Report bugs
- [Documentation](https://pointmatic.github.io/project-guide/) - Read the docs

## License

By contributing, you agree that your contributions will be licensed under the Apache-2.0 License.
