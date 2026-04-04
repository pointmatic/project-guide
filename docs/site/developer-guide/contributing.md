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

For guide improvements or new features:

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
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   pip install -e ".[dev,docs]"
   ```

4. **Make your changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

5. **Run tests**
   ```bash
   pytest
   ```

6. **Run linters**
   ```bash
   ruff check .
   mypy project_guide
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
- Maintain or improve test coverage
- Use pytest for testing
- Test edge cases and error conditions

### Documentation

- Update docstrings for modified functions
- Update user documentation for user-facing changes
- Update CHANGELOG.md with your changes
- Keep documentation clear and concise

### Guide Improvements

When improving workflow guides:

1. **Test with LLMs**: Verify guides work with actual LLMs
2. **Be specific**: Provide concrete steps, not vague instructions
3. **Include examples**: Show what good output looks like
4. **Consider edge cases**: Handle common variations
5. **Maintain consistency**: Follow existing guide structure

## Project Structure

```
project-guide/
├── project_guide/          # Main package
│   ├── templates/          # Bundled guide templates
│   │   └── guides/         # Workflow guides
│   ├── cli.py             # CLI commands
│   ├── config.py          # Configuration handling
│   ├── sync.py            # Guide synchronization
│   └── version.py         # Version information
├── tests/                  # Test suite
├── docs/                   # Documentation
│   ├── guides/            # Developer guides
│   ├── site/              # MkDocs documentation
│   └── specs/             # Specifications
└── pyproject.toml         # Package configuration
```

## Testing Locally

### Run All Tests

```bash
pytest
```

### Run Specific Tests

```bash
pytest tests/test_cli.py
pytest tests/test_cli.py::test_init_command
```

### Check Coverage

```bash
pytest --cov=project_guide --cov-report=html
open htmlcov/index.html
```

### Run Linters

```bash
# Check code style
ruff check .

# Type checking
mypy project_guide

# Format code
ruff format .
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
