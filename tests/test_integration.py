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


def test_full_init_override_update_workflow(runner, tmp_path):
    """Test complete workflow: init → override → update."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Step 1: Initialize project
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        assert Path(".project-guides.yml").exists()
        assert Path("docs/guides/project-guide.md").exists()

        # Step 2: Override a guide
        result = runner.invoke(main, ['override', 'debug-guide.md', 'Custom debugging workflow'])
        assert result.exit_code == 0

        config = Config.load(".project-guides.yml")
        assert config.is_overridden("debug-guide.md")

        # Step 3: Check status
        result = runner.invoke(main, ['status'])
        assert result.exit_code == 0
        assert "overridden" in result.output
        assert "Custom debugging workflow" in result.output

        # Step 4: Simulate version upgrade by modifying config
        config.installed_version = "0.12.0"
        config.save(".project-guides.yml")

        # Step 5: Update (should skip overridden guide, update others)
        result = runner.invoke(main, ['update'])
        assert result.exit_code == 0
        assert "Skipped (overridden)" in result.output or "Updated:" in result.output
        assert "debug-guide.md" in result.output

        # Step 6: Force update (should create backup and update overridden guide)
        # Reset version again to trigger update
        config = Config.load(".project-guides.yml")
        config.installed_version = "0.12.0"
        config.save(".project-guides.yml")

        result = runner.invoke(main, ['update', '--force'])
        assert result.exit_code == 0
        assert "Updated:" in result.output or "Already current:" in result.output

        # Verify backup was created
        backup_files = list(Path("docs/guides").glob("debug-guide.md.bak.*"))
        assert len(backup_files) >= 1

        # Step 7: Unoverride
        result = runner.invoke(main, ['unoverride', 'debug-guide.md'])
        assert result.exit_code == 0

        config = Config.load(".project-guides.yml")
        assert not config.is_overridden("debug-guide.md")


def test_version_upgrade_scenario(runner, tmp_path):
    """Test upgrading from old version to new version."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize with current version
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Simulate old version
        config = Config.load(".project-guides.yml")
        config.installed_version = "0.10.0"
        config.save(".project-guides.yml")

        # Check status - should show updates available
        result = runner.invoke(main, ['status'])
        assert result.exit_code == 0
        assert "update available" in result.output

        # Update to latest
        result = runner.invoke(main, ['update'])
        assert result.exit_code == 0
        assert "Updated:" in result.output

        # Verify version was updated
        config = Config.load(".project-guides.yml")
        assert config.installed_version == "1.0.0"

        # Status should now show all current
        result = runner.invoke(main, ['status'])
        assert result.exit_code == 0
        assert "All guides are up to date" in result.output


def test_force_update_creates_backups(runner, tmp_path):
    """Test that force update creates backups for all guides."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Override multiple guides
        runner.invoke(main, ['override', 'debug-guide.md', 'Custom debug'])
        runner.invoke(main, ['override', 'project-guide.md', 'Custom project'])

        # Modify installed version
        config = Config.load(".project-guides.yml")
        config.installed_version = "0.12.0"
        config.save(".project-guides.yml")

        # Force update
        result = runner.invoke(main, ['update', '--force'])
        assert result.exit_code == 0

        # Verify backups were created for overridden guides
        debug_backups = list(Path("docs/guides").glob("debug-guide.md.bak.*"))
        project_backups = list(Path("docs/guides").glob("project-guide.md.bak.*"))

        assert len(debug_backups) >= 1
        assert len(project_backups) >= 1


def test_multiple_projects_in_isolation(runner, tmp_path):
    """Test that multiple projects can coexist independently."""
    import os

    # Project 1
    project1 = tmp_path / "project1"
    project1.mkdir()

    # Change to project1 directory
    original_dir = os.getcwd()
    try:
        os.chdir(project1)

        result = runner.invoke(main, ['init', '--target-dir', 'guides'])
        assert result.exit_code == 0

        runner.invoke(main, ['override', 'debug-guide.md', 'Project 1 custom'])

        config1 = Config.load(".project-guides.yml")
        assert config1.target_dir == "guides"
        assert config1.is_overridden("debug-guide.md")

        # Project 2
        project2 = tmp_path / "project2"
        project2.mkdir()
        os.chdir(project2)

        result = runner.invoke(main, ['init', '--target-dir', 'documentation'])
        assert result.exit_code == 0

        runner.invoke(main, ['override', 'project-guide.md', 'Project 2 custom'])

        config2 = Config.load(".project-guides.yml")
        assert config2.target_dir == "documentation"
        assert config2.is_overridden("project-guide.md")
        assert not config2.is_overridden("debug-guide.md")

        # Verify projects are independent by checking files directly
        config1_check = Config.load(str(project1 / ".project-guides.yml"))
        assert config1_check.is_overridden("debug-guide.md")
        assert not config1_check.is_overridden("project-guide.md")

        config2_check = Config.load(str(project2 / ".project-guides.yml"))
        assert config2_check.is_overridden("project-guide.md")
        assert not config2_check.is_overridden("debug-guide.md")
    finally:
        os.chdir(original_dir)


def test_dry_run_doesnt_modify_files(runner, tmp_path):
    """Test that dry-run mode doesn't actually modify files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Modify a guide file
        guide_path = Path("docs/guides/debug-guide.md")
        guide_path.read_text()
        guide_path.write_text("MODIFIED CONTENT")

        # Simulate old version
        config = Config.load(".project-guides.yml")
        config.installed_version = "0.10.0"
        config.save(".project-guides.yml")

        # Dry-run update
        result = runner.invoke(main, ['update', '--dry-run'])
        assert result.exit_code == 0
        assert "Would update" in result.output
        assert "Run without --dry-run to apply changes" in result.output

        # Verify file wasn't modified
        assert guide_path.read_text() == "MODIFIED CONTENT"

        # Verify config wasn't updated
        config_check = Config.load(".project-guides.yml")
        assert config_check.installed_version == "0.10.0"


def test_specific_guide_update(runner, tmp_path):
    """Test updating only specific guides."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Simulate old version
        config = Config.load(".project-guides.yml")
        config.installed_version = "0.10.0"
        config.save(".project-guides.yml")

        # Update only specific guides
        result = runner.invoke(main, ['update', '--guides', 'debug-guide.md', '--guides', 'project-guide.md'])
        assert result.exit_code == 0
        assert "debug-guide.md" in result.output
        assert "project-guide.md" in result.output

        # Verify config was updated
        config = Config.load(".project-guides.yml")
        assert config.installed_version == "1.0.0"
