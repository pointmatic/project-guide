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
from project_guide.config import Config


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


def test_full_init_override_update_workflow(runner, tmp_path):
    """Test complete workflow: init → override → modify → update."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Step 1: Initialize project
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        assert Path(".project-guide.yml").exists()
        assert Path("docs/project-guide/.metadata.yml").exists()

        # Step 2: Override a file
        result = runner.invoke(main, ['override', 'templates/modes/debug-mode.md', 'Custom debugging workflow'])
        assert result.exit_code == 0

        config = Config.load(".project-guide.yml")
        assert config.is_overridden("templates/modes/debug-mode.md")

        # Step 3: Check status
        result = runner.invoke(main, ['status'])
        assert result.exit_code == 0
        assert "overridden" in result.output

        # Step 4: Modify a non-overridden file to trigger update
        Path("docs/project-guide/templates/modes/plan-concept-mode.md").write_text("Modified")

        # Step 5: Update (should skip overridden file, prompt for modified)
        result = runner.invoke(main, ['update'], input="y\n")
        assert result.exit_code == 0
        assert "templates/modes/plan-concept-mode.md" in result.output

        # Step 6: Modify the overridden file and force update
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("Custom")

        result = runner.invoke(main, ['update', '--force'])
        assert result.exit_code == 0

        # Verify backup was created for modified overridden file
        backup_files = list(Path("docs/project-guide/templates/modes").glob("debug-mode.md.bak.*"))
        assert len(backup_files) >= 1

        # Step 7: Unoverride
        result = runner.invoke(main, ['unoverride', 'templates/modes/debug-mode.md'])
        assert result.exit_code == 0

        config = Config.load(".project-guide.yml")
        assert not config.is_overridden("templates/modes/debug-mode.md")


def test_hash_based_status(runner, tmp_path):
    """Test that status uses content hash, not version, to determine file state."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Set installed_version to something old — files should still be current
        config = Config.load(".project-guide.yml")
        config.installed_version = "0.1.0"
        config.save(".project-guide.yml")

        result = runner.invoke(main, ['status'])
        assert result.exit_code == 0
        assert "current" in result.output
        # Should NOT show "need updating" since content hasn't changed
        assert "need updating" not in result.output


def test_force_update_creates_backups(runner, tmp_path):
    """Test that force update creates backups for modified files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Override and modify files
        runner.invoke(main, ['override', 'templates/modes/debug-mode.md', 'Custom debug'])
        runner.invoke(main, ['override', 'templates/modes/plan-concept-mode.md', 'Custom project'])
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("Custom debug")
        Path("docs/project-guide/templates/modes/plan-concept-mode.md").write_text("Custom project")

        # Force update
        result = runner.invoke(main, ['update', '--force'])
        assert result.exit_code == 0

        # Verify backups were created for modified overridden files
        debug_backups = list(Path("docs/project-guide/templates/modes").glob("debug-mode.md.bak.*"))
        project_backups = list(Path("docs/project-guide/templates/modes").glob("plan-concept-mode.md.bak.*"))

        assert len(debug_backups) >= 1
        assert len(project_backups) >= 1


def test_multiple_projects_in_isolation(runner, tmp_path):
    """Test that multiple projects can coexist independently."""
    import os

    # Project 1
    project1 = tmp_path / "project1"
    project1.mkdir()

    original_dir = os.getcwd()
    try:
        os.chdir(project1)

        result = runner.invoke(main, ['init', '--target-dir', 'guides'])
        assert result.exit_code == 0

        runner.invoke(main, ['override', 'templates/modes/debug-mode.md', 'Project 1 custom'])

        config1 = Config.load(".project-guide.yml")
        assert config1.target_dir == "guides"
        assert config1.is_overridden("templates/modes/debug-mode.md")

        # Project 2
        project2 = tmp_path / "project2"
        project2.mkdir()
        os.chdir(project2)

        result = runner.invoke(main, ['init', '--target-dir', 'documentation'])
        assert result.exit_code == 0

        runner.invoke(main, ['override', 'templates/modes/plan-concept-mode.md', 'Project 2 custom'])

        config2 = Config.load(".project-guide.yml")
        assert config2.target_dir == "documentation"
        assert config2.is_overridden("templates/modes/plan-concept-mode.md")
        assert not config2.is_overridden("templates/modes/debug-mode.md")

        # Verify projects are independent
        config1_check = Config.load(str(project1 / ".project-guide.yml"))
        assert config1_check.is_overridden("templates/modes/debug-mode.md")
        assert not config1_check.is_overridden("templates/modes/plan-concept-mode.md")

        config2_check = Config.load(str(project2 / ".project-guide.yml"))
        assert config2_check.is_overridden("templates/modes/plan-concept-mode.md")
        assert not config2_check.is_overridden("templates/modes/debug-mode.md")
    finally:
        os.chdir(original_dir)


def test_dry_run_doesnt_modify_files(runner, tmp_path):
    """Test that dry-run mode doesn't actually modify files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Modify a file
        file_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        file_path.write_text("MODIFIED CONTENT", encoding="utf-8")

        # Dry-run update
        result = runner.invoke(main, ['update', '--dry-run'])
        assert result.exit_code == 0
        assert "Modified" in result.output or "would prompt" in result.output.lower()
        assert "Run without --dry-run to apply changes" in result.output

        # Verify file wasn't modified
        assert file_path.read_text(encoding="utf-8") == "MODIFIED CONTENT"


def test_specific_file_update(runner, tmp_path):
    """Test updating only specific files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Modify specific files
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("Modified")
        Path("docs/project-guide/templates/modes/plan-concept-mode.md").write_text("Modified")

        # Update only specific files, approve prompts
        result = runner.invoke(main, ['update', '--files', 'templates/modes/debug-mode.md', '--files', 'templates/modes/plan-concept-mode.md'], input="y\ny\n")
        assert result.exit_code == 0
        assert "templates/modes/debug-mode.md" in result.output
        assert "templates/modes/plan-concept-mode.md" in result.output
