# Testing Guide

Comprehensive guide to testing project-guide.

## Test Suite Overview

project-guide has 90% test coverage with 596 tests across 12 test files covering:

- CLI commands
- Deterministic actions (archive) and the `archive_stories` mode
- Configuration handling
- File synchronization
- Jinja2 template rendering
- Metadata loading and validation
- Runtime helpers (skip-input contract, project-name detection)
- Story parsing and `git-push` message derivation
- Cross-repo contracts (Pyve hosting)
- Integration scenarios
- Purge command

## Running Tests

This project is pyve-managed: pytest lives in the dev testenv, so run tests with `pyve test` (not bare `pytest`). `pyve test` forwards any arguments straight to pytest.

### All Tests

```bash
pyve test
```

### With Coverage

```bash
pyve test --cov=project_guide --cov-report=term-missing
```

### HTML Coverage Report

```bash
pyve test --cov=project_guide --cov-report=html
open htmlcov/index.html
```

### Specific Test Files

```bash
pyve test tests/test_cli.py
pyve test tests/test_render.py
pyve test tests/test_config.py
pyve test tests/test_cross_repo_contract.py
```

### Specific Tests

```bash
pyve test tests/test_cli.py::test_init_in_empty_directory
```

### By Pattern

```bash
pyve test -k "init"
pyve test -k "render"
```

## Test Structure

### Test Files

| File | Tests | Description |
|------|-------|-------------|
| `test_cli.py` | ~200 | CLI command tests using CliRunner |
| `test_render.py` | ~170 | Jinja2 template rendering (incl. parametrized per-mode) |
| `test_actions.py` | ~53 | Deterministic actions (archive) |
| `test_runtime.py` | ~52 | Runtime helpers (skip-input, project-name detection) |
| `test_stories.py` | ~35 | Story parsing and `git-push` message derivation |
| `test_sync.py` | ~25 | File synchronization logic |
| `test_config.py` | ~19 | Configuration handling |
| `test_metadata.py` | ~18 | Metadata loading and validation |
| `test_archive_stories_mode.py` | ~8 | `archive_stories` mode behavior |
| `test_integration.py` | ~6 | End-to-end integration scenarios |
| `test_purge.py` | ~5 | Purge command |
| `test_cross_repo_contract.py` | ~3 | Cross-repo contracts (Pyve hosting) |

### Unit Tests

Test individual functions and classes in isolation.

**Example**: `tests/test_config.py`

```python
def test_config_loads_from_file(tmp_path):
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text("""
version: "2.0"
installed_version: "2.13.0"
""")

    config = Config.load(str(config_file))
    assert config.installed_version == "2.13.0"
```

### Integration Tests

Test multiple components working together.

**Example**: `tests/test_integration.py`

```python
def test_full_workflow():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Init
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0

        # Status
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
```

### CLI Tests

Test command-line interface using Click's test runner.

**Example**: `tests/test_cli.py`

```python
from click.testing import CliRunner
from project_guide.cli import main

def test_init_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
```

### Render Tests

Test Jinja2 template rendering, including parametrized tests that render every mode defined in `.metadata.yml`.

**Example**: `tests/test_render.py`

```python
@pytest.mark.parametrize("mode", get_all_modes_from_metadata())
def test_render_mode(mode):
    """Verify every mode in .metadata.yml renders without error."""
    result = render_template(mode=mode)
    assert result is not None
```

## Writing Tests

### Test Function Naming

```python
# Good
def test_init_creates_project_guide_directory():
    ...

def test_render_mode_produces_valid_output():
    ...

# Bad
def test1():
    ...

def test_stuff():
    ...
```

### Using CliRunner.isolated_filesystem()

CLI tests should use `isolated_filesystem()` to avoid polluting the real filesystem:

```python
def test_init_creates_files():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
        assert Path(".project-guide.yml").exists()
```

### Using Fixtures

```python
import pytest
from pathlib import Path

@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary project directory."""
    return tmp_path

def test_with_fixture(project_dir):
    assert project_dir.exists()
```

### Parametrized Tests

```python
@pytest.mark.parametrize("mode", [
    "greenfield",
    "existing",
    "maintenance",
])
def test_mode_renders(mode):
    result = render_template(mode=mode)
    assert result is not None
```

### Testing Exceptions

```python
import pytest

def test_invalid_config_raises_error():
    with pytest.raises(ValueError, match="Invalid configuration"):
        Config.load(Path("/nonexistent"))
```

### Testing File Operations

```python
def test_init_creates_files():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
        assert Path(".project-guide.yml").exists()
        assert Path("project-guide").exists()
```

## Windows Encoding

When reading template content in tests, always specify UTF-8 encoding to avoid Windows encoding issues:

```python
# Good
content = path.read_text(encoding="utf-8")

# Bad - may fail on Windows
content = path.read_text()
```

## Test Fixtures

### Common Fixtures

```python
@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()

@pytest.fixture
def project_dir(tmp_path):
    """Temporary project directory."""
    return tmp_path
```

### Using Fixtures

```python
def test_status_command(runner):
    with runner.isolated_filesystem():
        runner.invoke(main, ["init"])
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
```

## Mocking

### Mocking File System

```python
from unittest.mock import patch, MagicMock

def test_with_mock_filesystem():
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True
        # Test code
```

### Mocking External Calls

```python
def test_with_mock_subprocess():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Test code
```

## Coverage Goals

### Current Coverage

- **Overall**: 90%
- **Minimum threshold**: 85% (enforced)

### Coverage Targets

- Maintain minimum 85% overall coverage (enforced in CI)
- New code should have 90%+ coverage
- Critical paths should have 100% coverage

### Checking Coverage

```bash
# Terminal report
pyve test --cov=project_guide --cov-report=term-missing

# HTML report
pyve test --cov=project_guide --cov-report=html
open htmlcov/index.html

# Fail if coverage drops below threshold
pyve test --cov=project_guide --cov-fail-under=85
```

## Continuous Integration

Tests run automatically on:
- Every push to main
- Every pull request
- Manual workflow dispatch

### GitHub Actions Workflow

```yaml
- name: Run tests
  run: |
    pytest --cov=project_guide --cov-report=xml --cov-fail-under=85

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Best Practices

### 1. Test Behavior, Not Implementation

```python
# Good - tests behavior
def test_init_creates_project_guide():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["init"])
        assert Path("project-guide").exists()

# Bad - tests implementation details
def test_init_calls_create_directory():
    with patch("project_guide.sync.create_directory") as mock:
        runner.invoke(main, ["init"])
        mock.assert_called_once()
```

### 2. Use Descriptive Assertions

```python
# Good
assert result.exit_code == 0, f"Command failed: {result.output}"
assert "Success" in result.output

# Bad
assert result.exit_code == 0
assert True
```

### 3. Keep Tests Isolated

```python
# Good - uses isolated filesystem
def test_init():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["init"])
        assert Path(".project-guide.yml").exists()

# Bad - modifies actual filesystem
def test_init():
    runner.invoke(main, ["init"])
    # Pollutes actual directory
```

### 4. Test Edge Cases

```python
def test_init_with_existing_directory():
    # Test when directory already exists
    ...

def test_init_with_no_permissions():
    # Test when lacking write permissions
    ...

def test_init_with_invalid_path():
    # Test with invalid path
    ...
```

## Debugging Tests

### Print Debugging

```python
def test_something():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["init"])
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        assert result.exit_code == 0
```

### Using pdb

```python
def test_something():
    import pdb; pdb.set_trace()
    # Test code
```

### Pytest Debugging

```bash
# Drop into pdb on failure
pyve test --pdb

# Drop into pdb on first failure
pyve test -x --pdb
```

## Next Steps

- [Development Setup](development.md) - Set up development environment
- [Contributing](contributing.md) - Contribution guidelines
