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

from project_guides.cli import main
from project_guides.config import Config


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


def test_init_in_empty_directory(runner, tmp_path):
    """Test init command in an empty directory."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])

        assert result.exit_code == 0
        assert "Initializing project-guides" in result.output
        assert "Successfully initialized" in result.output

        # Verify config file was created
        assert Path(".project-guides.yml").exists()

        # Verify guides were created
        assert Path("docs/guides/project-guide.md").exists()
        assert Path("docs/guides/debug-guide.md").exists()
        assert Path("docs/guides/developer/codecov-setup-guide.md").exists()


def test_init_with_existing_config_error(runner, tmp_path):
    """Test that init errors when config already exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # First init
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Second init without force should fail
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 1
        assert "already exists" in result.output


def test_init_with_force_flag(runner, tmp_path):
    """Test init with --force flag overwrites existing files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # First init
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Modify a guide
        guide_path = Path("docs/guides/project-guide.md")
        original_content = guide_path.read_text()
        guide_path.write_text("Modified content")

        # Second init with force
        result = runner.invoke(main, ['init', '--force'])
        assert result.exit_code == 0

        # Verify file was overwritten
        assert guide_path.read_text() == original_content


def test_init_with_custom_target_dir(runner, tmp_path):
    """Test init with custom --target-dir."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--target-dir', 'custom/path'])

        assert result.exit_code == 0
        assert Path("custom/path/project-guide.md").exists()

        # Verify config has correct target_dir
        config = Config.load(".project-guides.yml")
        assert config.target_dir == "custom/path"


def test_status_with_all_guides_current(runner, tmp_path):
    """Test status command when all guides are current."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Run status
        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "project-guides v1.0.0" in result.output
        assert "Guides status:" in result.output
        assert "All guides are up to date" in result.output


def test_status_with_outdated_guides(runner, tmp_path):
    """Test status command with outdated guides."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Modify config to simulate older version
        config = Config.load(".project-guides.yml")
        config.installed_version = "0.7.0"
        config.save(".project-guides.yml")

        # Run status
        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "update available" in result.output
        assert "Run 'project-guides update' to sync" in result.output


def test_status_with_overridden_guides(runner, tmp_path):
    """Test status command with overridden guides."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Add an override
        config = Config.load(".project-guides.yml")
        config.add_override("debug-guide.md", "Custom content", "0.8.0")
        config.save(".project-guides.yml")

        # Run status
        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "overridden" in result.output
        assert "Custom content" in result.output
        assert "1 guide overridden" in result.output


def test_status_with_missing_config(runner, tmp_path):
    """Test status command when config doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['status'])

        assert result.exit_code == 1
        assert "No .project-guides.yml found" in result.output
        assert "Run 'project-guides init' first" in result.output


def test_override_adds_entry_to_config(runner, tmp_path):
    """Test that override command adds entry to config."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Add override
        result = runner.invoke(main, ['override', 'debug-guide.md', 'Custom debugging workflow'])

        assert result.exit_code == 0
        assert "Marked debug-guide.md as overridden" in result.output
        assert "Custom debugging workflow" in result.output

        # Verify config was updated
        config = Config.load(".project-guides.yml")
        assert config.is_overridden("debug-guide.md")
        assert config.overrides["debug-guide.md"].reason == "Custom debugging workflow"


def test_override_with_nonexistent_guide_error(runner, tmp_path):
    """Test that override errors with non-existent guide."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Try to override non-existent guide
        result = runner.invoke(main, ['override', 'fake-guide.md', 'Some reason'])

        assert result.exit_code == 1
        assert "Guide 'fake-guide.md' not found" in result.output
        assert "Available guides:" in result.output


def test_unoverride_removes_entry(runner, tmp_path):
    """Test that unoverride command removes entry from config."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Add override
        runner.invoke(main, ['override', 'debug-guide.md', 'Custom content'])

        # Remove override
        result = runner.invoke(main, ['unoverride', 'debug-guide.md'])

        assert result.exit_code == 0
        assert "Removed override from debug-guide.md" in result.output

        # Verify config was updated
        config = Config.load(".project-guides.yml")
        assert not config.is_overridden("debug-guide.md")


def test_unoverride_not_overridden_error(runner, tmp_path):
    """Test that unoverride errors when guide is not overridden."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Try to unoverride a guide that's not overridden
        result = runner.invoke(main, ['unoverride', 'debug-guide.md'])

        assert result.exit_code == 1
        assert "is not overridden" in result.output


def test_overrides_lists_all_overridden_guides(runner, tmp_path):
    """Test that overrides command lists all overridden guides."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Add multiple overrides
        runner.invoke(main, ['override', 'debug-guide.md', 'Custom debugging'])
        runner.invoke(main, ['override', 'project-guide.md', 'Project-specific'])

        # List overrides
        result = runner.invoke(main, ['overrides'])

        assert result.exit_code == 0
        assert "Overridden guides (2)" in result.output
        assert "debug-guide.md" in result.output
        assert "Custom debugging" in result.output
        assert "project-guide.md" in result.output
        assert "Project-specific" in result.output


def test_overrides_with_no_overrides(runner, tmp_path):
    """Test overrides command when no guides are overridden."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # List overrides
        result = runner.invoke(main, ['overrides'])

        assert result.exit_code == 0
        assert "No overridden guides" in result.output


def test_update_all_guides(runner, tmp_path):
    """Test update command updates all guides."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Modify config to simulate older version
        config = Config.load(".project-guides.yml")
        config.installed_version = "0.9.0"
        config.save(".project-guides.yml")

        # Run update
        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0
        assert "Updated:" in result.output
        assert "guide" in result.output.lower()

        # Verify config was updated
        config = Config.load(".project-guides.yml")
        assert config.installed_version == "1.0.0"


def test_update_specific_guides(runner, tmp_path):
    """Test update command with specific guides."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Modify config to simulate older version
        config = Config.load(".project-guides.yml")
        config.installed_version = "0.9.0"
        config.save(".project-guides.yml")

        # Update only specific guides
        result = runner.invoke(main, ['update', '--guides', 'debug-guide.md', '--guides', 'project-guide.md'])

        assert result.exit_code == 0
        assert "debug-guide.md" in result.output
        assert "project-guide.md" in result.output


def test_update_with_dry_run(runner, tmp_path):
    """Test update command with --dry-run flag."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Modify config to simulate older version
        config = Config.load(".project-guides.yml")
        config.installed_version = "0.9.0"
        config.save(".project-guides.yml")

        # Run dry-run update
        result = runner.invoke(main, ['update', '--dry-run'])

        assert result.exit_code == 0
        assert "Dry-run mode" in result.output
        assert "Would update" in result.output
        assert "Run without --dry-run to apply changes" in result.output

        # Verify config was NOT updated
        config = Config.load(".project-guides.yml")
        assert config.installed_version == "0.9.0"


def test_update_with_force_creates_backups(runner, tmp_path):
    """Test update command with --force flag creates backups."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Add override
        config = Config.load(".project-guides.yml")
        config.add_override("debug-guide.md", "Custom content", "0.10.0")
        config.installed_version = "0.9.0"
        config.save(".project-guides.yml")

        # Update with force
        result = runner.invoke(main, ['update', '--force'])

        assert result.exit_code == 0
        assert "Updated:" in result.output
        assert "debug-guide.md" in result.output

        # Verify backup was created
        backup_files = list(Path("docs/guides").glob("debug-guide.md.bak.*"))
        assert len(backup_files) == 1


def test_update_respects_overrides(runner, tmp_path):
    """Test that update respects overridden guides."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Add override
        config = Config.load(".project-guides.yml")
        config.add_override("debug-guide.md", "Custom content", "0.10.0")
        config.installed_version = "0.9.0"
        config.save(".project-guides.yml")

        # Update without force
        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0
        assert "Skipped (overridden):" in result.output
        assert "debug-guide.md" in result.output
        assert "Custom content" in result.output
