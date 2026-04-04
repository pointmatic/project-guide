# Testing Guide

Comprehensive guide to testing project-guide.

## Test Suite Overview

project-guide has 82% test coverage with 59 comprehensive tests covering:
- CLI commands
- Configuration handling
- Guide synchronization
- Integration scenarios

## Running Tests

### All Tests

```bash
pytest
```

### With Coverage

```bash
pytest --cov=project_guide --cov-report=term-missing
```

### HTML Coverage Report

```bash
pytest --cov=project_guide --cov-report=html
open htmlcov/index.html
```

### Specific Test Files

```bash
pytest tests/test_cli.py
pytest tests/test_config.py
pytest tests/test_sync.py
pytest tests/test_integration.py
```

### Specific Tests

```bash
pytest tests/test_cli.py::test_init_command
pytest tests/test_cli.py::TestInitCommand::test_creates_guides_directory
```

### By Pattern

```bash
pytest -k "init"
pytest -k "override"
```

## Test Structure

### Unit Tests

Test individual functions and classes in isolation.

**Example**: `tests/test_config.py`

```python
def test_config_loads_from_file(tmp_path):
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text("""
version: "1.0"
package_version: "1.1.3"
guides_dir: "docs/guides"
overrides: {}
""")
    
    config = Config.load(tmp_path)
    assert config.package_version == "1.1.3"
```

### Integration Tests

Test multiple components working together.

**Example**: `tests/test_integration.py`

```python
def test_full_workflow(tmp_path):
    # Init
    result = runner.invoke(cli, ["init"], cwd=tmp_path)
    assert result.exit_code == 0
    
    # Override
    result = runner.invoke(cli, ["override", "project-guide.md"], cwd=tmp_path)
    assert result.exit_code == 0
    
    # Update (should skip overridden)
    result = runner.invoke(cli, ["update"], cwd=tmp_path)
    assert "Skipped" in result.output
```

### CLI Tests

Test command-line interface using Click's test runner.

**Example**: `tests/test_cli.py`

```python
from click.testing import CliRunner
from project_guide.cli import cli

def test_init_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "Initialized" in result.output
```

## Writing Tests

### Test Function Naming

```python
# Good
def test_init_creates_guides_directory():
    ...

def test_override_marks_guide_as_overridden():
    ...

# Bad
def test1():
    ...

def test_stuff():
    ...
```

### Using Fixtures

```python
import pytest
from pathlib import Path

@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary project directory."""
    guides_dir = tmp_path / "docs" / "guides"
    guides_dir.mkdir(parents=True)
    return tmp_path

def test_with_fixture(project_dir):
    assert (project_dir / "docs" / "guides").exists()
```

### Parametrized Tests

```python
@pytest.mark.parametrize("guide_name", [
    "project-guide.md",
    "best-practices-guide.md",
    "debug-guide.md",
])
def test_guide_exists(guide_name):
    from project_guide.templates import GUIDES_DIR
    assert (GUIDES_DIR / guide_name).exists()
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
def test_init_creates_files(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], cwd=tmp_path)
    
    assert (tmp_path / "docs" / "guides").exists()
    assert (tmp_path / ".project-guide.yml").exists()
    assert (tmp_path / "docs" / "guides" / "project-guide.md").exists()
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

@pytest.fixture
def initialized_project(tmp_path, runner):
    """Project with guides initialized."""
    runner.invoke(cli, ["init"], cwd=tmp_path)
    return tmp_path
```

### Using Fixtures

```python
def test_status_command(initialized_project, runner):
    result = runner.invoke(cli, ["status"], cwd=initialized_project)
    assert result.exit_code == 0
    assert "Current" in result.output
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

- **Overall**: 82%
- **CLI**: 85%
- **Config**: 90%
- **Sync**: 80%

### Coverage Targets

- Maintain minimum 80% overall coverage
- New code should have 90%+ coverage
- Critical paths should have 100% coverage

### Checking Coverage

```bash
# Terminal report
pytest --cov=project_guide --cov-report=term-missing

# HTML report
pytest --cov=project_guide --cov-report=html
open htmlcov/index.html
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
    pytest --cov=project_guide --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Best Practices

### 1. Test Behavior, Not Implementation

```python
# Good - tests behavior
def test_init_creates_guides():
    result = runner.invoke(cli, ["init"])
    assert (project_dir / "docs" / "guides").exists()

# Bad - tests implementation details
def test_init_calls_create_directory():
    with patch("project_guide.sync.create_directory") as mock:
        runner.invoke(cli, ["init"])
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
def test_init(tmp_path):
    runner.invoke(cli, ["init"], cwd=tmp_path)
    assert (tmp_path / ".project-guide.yml").exists()

# Bad - modifies actual filesystem
def test_init():
    runner.invoke(cli, ["init"])
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
def test_something(tmp_path):
    result = runner.invoke(cli, ["init"], cwd=tmp_path)
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
pytest --pdb

# Drop into pdb on first failure
pytest -x --pdb
```

## Next Steps

- [Development Setup](development.md) - Set up development environment
- [Contributing](contributing.md) - Contribution guidelines
