# Copyright (c) 2026 Pointmatic
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path

import pytest
from click.testing import CliRunner

from project_guide.cli import main


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_purge_removes_all_files(runner, tmp_path):
    """Test that purge removes config and guides directory."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Verify files exist
        assert Path(".project-guide.yml").exists()
        assert Path("docs/guides").exists()

        # Purge with --force to skip confirmation
        result = runner.invoke(main, ['purge', '--force'])
        assert result.exit_code == 0
        # Handle both Unix (/) and Windows (\) path separators
        assert ("✓ Removed docs/guides/" in result.output or "✓ Removed docs\\guides/" in result.output)
        assert "✓ Removed .project-guide.yml" in result.output
        assert "project-guide has been purged" in result.output

        # Verify files are gone
        assert not Path(".project-guide.yml").exists()
        assert not Path("docs/guides").exists()


def test_purge_with_confirmation_prompt(runner, tmp_path):
    """Test that purge prompts for confirmation without --force."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Purge without --force, answer 'n' to abort
        result = runner.invoke(main, ['purge'], input='n\n')
        assert result.exit_code == 1
        assert "Are you sure you want to purge project-guide?" in result.output

        # Files should still exist
        assert Path(".project-guide.yml").exists()
        assert Path("docs/guides").exists()

        # Purge without --force, answer 'y' to confirm
        result = runner.invoke(main, ['purge'], input='y\n')
        assert result.exit_code == 0

        # Files should be gone
        assert not Path(".project-guide.yml").exists()
        assert not Path("docs/guides").exists()


def test_purge_with_custom_target_dir(runner, tmp_path):
    """Test purge with custom target directory."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize with custom directory
        result = runner.invoke(main, ['init', '--target-dir', 'custom/guides'])
        assert result.exit_code == 0

        # Verify files exist
        assert Path(".project-guide.yml").exists()
        assert Path("custom/guides").exists()

        # Purge
        result = runner.invoke(main, ['purge', '--force'])
        assert result.exit_code == 0
        # Handle both Unix (/) and Windows (\) path separators
        assert ("✓ Removed custom/guides/" in result.output or "✓ Removed custom\\guides/" in result.output)

        # Verify files are gone
        assert not Path(".project-guide.yml").exists()
        assert not Path("custom/guides").exists()


def test_purge_without_config_errors(runner, tmp_path):
    """Test that purge errors when no config exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Try to purge without initializing
        result = runner.invoke(main, ['purge', '--force'])
        assert result.exit_code == 3
        assert "Configuration file not found" in result.output


def test_purge_handles_missing_guides_dir(runner, tmp_path):
    """Test purge when guides directory is already deleted."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Manually delete guides directory
        import shutil
        shutil.rmtree("docs/guides")

        # Purge should still work
        result = runner.invoke(main, ['purge', '--force'])
        assert result.exit_code == 0
        # Handle both Unix (/) and Windows (\) path separators
        assert ("docs/guides/ not found (skipped)" in result.output or "docs\\guides/ not found (skipped)" in result.output)
        assert "✓ Removed .project-guide.yml" in result.output

        # Config should be gone
        assert not Path(".project-guide.yml").exists()
