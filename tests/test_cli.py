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
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from project_guide.cli import main
from project_guide.config import Config
from project_guide.exceptions import SyncError
from project_guide.version import __version__


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


def test_init_in_empty_directory(runner, tmp_path):
    """Test init command in an empty directory."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])

        assert result.exit_code == 0
        assert "Initializing project-guide" in result.output
        assert "Successfully initialized" in result.output

        # Verify config file was created
        assert Path(".project-guide.yml").exists()

        # Verify templates were created in new structure
        assert Path("docs/project-guide/go.md").exists()
        assert Path("docs/project-guide/.metadata.yml").exists()
        assert Path("docs/project-guide/templates/modes/plan-concept-mode.md").exists()
        assert Path("docs/project-guide/developer/codecov-setup-guide.md").exists()


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

        # Modify a template
        template_path = Path("docs/project-guide/templates/modes/plan-concept-mode.md")
        original_content = template_path.read_text(encoding="utf-8")
        template_path.write_text("Modified content")

        # Second init with force
        result = runner.invoke(main, ['init', '--force'])
        assert result.exit_code == 0

        # Verify file was overwritten
        assert template_path.read_text(encoding="utf-8") == original_content


def test_init_with_custom_target_dir(runner, tmp_path):
    """Test init with custom --target-dir."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--target-dir', 'custom/path'])

        assert result.exit_code == 0
        assert Path("custom/path/.metadata.yml").exists()

        # Verify config has correct target_dir
        config = Config.load(".project-guide.yml")
        assert config.target_dir == "custom/path"


def test_status_with_all_guides_current(runner, tmp_path):
    """Test status command when all guides are current."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Run status
        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert f"project-guide v{__version__}" in result.output
        # Mode section
        assert "Mode:" in result.output
        assert "default" in result.output
        assert "Run 'project-guide mode'" in result.output
        # Guide section
        assert "Guide:" in result.output
        assert "go.md" in result.output
        # Files section
        assert "current" in result.output


def test_status_with_files_needing_update(runner, tmp_path):
    """Test status when file content differs from template (hash mismatch)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Modify a file so its hash no longer matches the template
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("Modified content")

        # Run status
        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "need updating" in result.output
        assert "Run 'project-guide update' to sync" in result.output


def test_status_shows_mode_and_prerequisites(runner, tmp_path):
    """Test status shows current mode, description, and prerequisite status."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "Mode: default" in result.output
        assert "Getting started" in result.output
        assert "go.md" in result.output


def test_status_after_mode_change(runner, tmp_path):
    """Test status reflects the active mode after switching."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        runner.invoke(main, ['mode', 'code_velocity'])

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "Mode: code_velocity" in result.output
        assert "Generate code with velocity" in result.output


def test_status_v1_migration_notice(runner, tmp_path):
    """Test status shows migration notice for v1.x configs."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Simulate v1.x config
        config = Config.load(".project-guide.yml")
        config.version = "1.0"
        config.target_dir = "docs/guides"
        config.save(".project-guide.yml")

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "Migration notice" in result.output
        assert "docs/guides/ is deprecated" in result.output
        assert "refactor_plan" in result.output
        assert "refactor_document" in result.output


def test_status_no_migration_notice_for_v2(runner, tmp_path):
    """Test status does NOT show migration notice for v2.x configs."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "Migration notice" not in result.output


def test_refactor_modes_render(runner, tmp_path):
    """Test that refactor_plan and refactor_document modes render correctly."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        for name in ["refactor_plan", "refactor_document"]:
            result = runner.invoke(main, ['mode', name])
            assert result.exit_code == 0, f"{name} failed: {result.output}"
            assert f"Mode set: {name}" in result.output

            content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")
            assert "Restart the cycle" in content  # cycle header
            assert "Legacy Content" in content  # step 5

        # Verify distinct content
        runner.invoke(main, ['mode', 'refactor_plan'])
        plan = Path("docs/project-guide/go.md").read_text(encoding="utf-8")
        runner.invoke(main, ['mode', 'refactor_document'])
        doc = Path("docs/project-guide/go.md").read_text(encoding="utf-8")
        assert plan != doc
        assert "concept.md" in plan
        assert "descriptions.md" in doc


def test_mode_no_config(runner, tmp_path):
    """Test mode command with no config file."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['mode', 'plan_concept'])
        assert result.exit_code == 1
        assert "No .project-guide.yml found" in result.output


def test_mode_list_available(runner, tmp_path):
    """Test mode command with no argument lists available modes."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        result = runner.invoke(main, ['mode'])
        assert result.exit_code == 0
        assert "Current mode:" in result.output
        assert "Available modes:" in result.output
        assert "plan_concept" in result.output
        assert "code_velocity" in result.output


def test_mode_invalid_name(runner, tmp_path):
    """Test mode command with invalid mode name."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        result = runner.invoke(main, ['mode', 'nonexistent'])
        assert result.exit_code == 1
        assert "Unknown mode" in result.output
        assert "Available modes:" in result.output


def test_mode_switch_updates_config(runner, tmp_path):
    """Test mode command updates current_mode in config."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        result = runner.invoke(main, ['mode', 'code_velocity'])
        assert result.exit_code == 0
        assert "Mode set: code_velocity" in result.output

        config = Config.load(".project-guide.yml")
        assert config.current_mode == "code_velocity"


def test_mode_renders_output(runner, tmp_path):
    """Test mode command renders go.md to target_dir."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        runner.invoke(main, ['mode', 'debug'])

        output = Path("docs/project-guide/go.md")
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "Debug Guide" in content


def test_status_with_overridden_guides(runner, tmp_path):
    """Test status command with overridden guides."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Add an override
        config = Config.load(".project-guide.yml")
        config.add_override("templates/modes/debug-mode.md", "Custom content", "0.8.0")
        config.save(".project-guide.yml")

        # Run status
        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "overridden" in result.output


def test_status_with_missing_config(runner, tmp_path):
    """Test status command when config doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['status'])

        assert result.exit_code == 1
        assert "No .project-guide.yml found" in result.output
        assert "Run 'project-guide init' first" in result.output


def test_override_adds_entry_to_config(runner, tmp_path):
    """Test that override command adds entry to config."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Add override
        result = runner.invoke(main, ['override', 'templates/modes/debug-mode.md', 'Custom debugging workflow'])

        assert result.exit_code == 0
        assert "Marked templates/modes/debug-mode.md as overridden" in result.output
        assert "Custom debugging workflow" in result.output

        # Verify config was updated
        config = Config.load(".project-guide.yml")
        assert config.is_overridden("templates/modes/debug-mode.md")
        assert config.overrides["templates/modes/debug-mode.md"].reason == "Custom debugging workflow"


def test_override_with_nonexistent_guide_error(runner, tmp_path):
    """Test that override errors with non-existent guide."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Try to override non-existent guide
        result = runner.invoke(main, ['override', 'fake-guide.md', 'Some reason'])

        assert result.exit_code == 1
        assert "File 'fake-guide.md' not found" in result.output
        assert "Available files:" in result.output


def test_unoverride_removes_entry(runner, tmp_path):
    """Test that unoverride command removes entry from config."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Add override
        runner.invoke(main, ['override', 'templates/modes/debug-mode.md', 'Custom content'])

        # Remove override
        result = runner.invoke(main, ['unoverride', 'templates/modes/debug-mode.md'])

        assert result.exit_code == 0
        assert "Removed override from templates/modes/debug-mode.md" in result.output

        # Verify config was updated
        config = Config.load(".project-guide.yml")
        assert not config.is_overridden("templates/modes/debug-mode.md")


def test_unoverride_not_overridden_error(runner, tmp_path):
    """Test that unoverride errors when guide is not overridden."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Try to unoverride a guide that's not overridden
        result = runner.invoke(main, ['unoverride', 'templates/modes/debug-mode.md'])

        assert result.exit_code == 1
        assert "is not overridden" in result.output


def test_overrides_lists_all_overridden_guides(runner, tmp_path):
    """Test that overrides command lists all overridden guides."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # Add multiple overrides
        runner.invoke(main, ['override', 'templates/modes/debug-mode.md', 'Custom debugging'])
        runner.invoke(main, ['override', 'templates/modes/plan-concept-mode.md', 'Project-specific'])

        # List overrides
        result = runner.invoke(main, ['overrides'])

        assert result.exit_code == 0
        assert "Overridden files:" in result.output
        assert "templates/modes/debug-mode.md" in result.output
        assert "Custom debugging" in result.output
        assert "templates/modes/plan-concept-mode.md" in result.output
        assert "Project-specific" in result.output
        assert "templates/modes/plan-concept-mode.md" in result.output
        assert "Project-specific" in result.output


def test_overrides_with_no_overrides(runner, tmp_path):
    """Test overrides command when no guides are overridden."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize project
        runner.invoke(main, ['init'])

        # List overrides
        result = runner.invoke(main, ['overrides'])

        assert result.exit_code == 0
        assert "No overridden files" in result.output


def test_update_all_current(runner, tmp_path):
    """Test update when all files match templates (hash-based)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0
        assert "All files are up to date" in result.output


def test_update_specific_files(runner, tmp_path):
    """Test update command with specific modified files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Modify files so hash differs
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("Modified")
        Path("docs/project-guide/templates/modes/plan-concept-mode.md").write_text("Modified")

        # Update only specific files, approve prompts
        result = runner.invoke(main, ['update', '--files', 'templates/modes/debug-mode.md', '--files', 'templates/modes/plan-concept-mode.md'], input="y\ny\n")

        assert result.exit_code == 0
        assert "templates/modes/debug-mode.md" in result.output
        assert "templates/modes/plan-concept-mode.md" in result.output


def test_update_with_dry_run(runner, tmp_path):
    """Test update command with --dry-run flag."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Modify a file so hash differs
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("Modified")

        # Run dry-run update
        result = runner.invoke(main, ['update', '--dry-run'])

        assert result.exit_code == 0
        assert "Dry-run mode" in result.output
        assert "Modified" in result.output or "would prompt" in result.output.lower()
        assert "Run without --dry-run to apply changes" in result.output

        # Verify file was NOT changed (dry-run)
        assert Path("docs/project-guide/templates/modes/debug-mode.md").read_text() == "Modified"


def test_update_with_force_creates_backups(runner, tmp_path):
    """Test update command with --force flag creates backups for modified files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Modify a file so hash differs
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("Modified")

        # Update with force
        result = runner.invoke(main, ['update', '--force'])

        assert result.exit_code == 0
        assert "templates/modes/debug-mode.md" in result.output

        # Verify backup was created
        backup_files = list(Path("docs/project-guide/templates/modes").glob("debug-mode.md.bak.*"))
        assert len(backup_files) == 1


def test_update_respects_overrides(runner, tmp_path):
    """Test that update respects overridden files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Add override (file content still matches template, but is overridden)
        config = Config.load(".project-guide.yml")
        config.add_override("templates/modes/debug-mode.md", "Custom content", __version__)
        config.save(".project-guide.yml")

        # Update without force
        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0
        assert "Skipped (overridden):" in result.output
        assert "templates/modes/debug-mode.md" in result.output
        assert "Custom content" in result.output


# --- Story I.g: Coverage expansion tests ---


def test_migrate_config_renames_old_file(runner, tmp_path):
    """Test that _migrate_config_if_needed renames .project-guides.yml."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create old config file
        old_path = Path(".project-guides.yml")
        old_path.write_text("version: '1.0'\ninstalled_version: '1.0.0'\ntarget_dir: docs/project-guide\n")

        # Any CLI command triggers migration
        runner.invoke(main, ['status'])

        assert not old_path.exists()
        assert Path(".project-guide.yml").exists()


def test_init_skips_existing_guide_without_force(runner, tmp_path):
    """Test init skips guides that already exist without --force."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Pre-create the target directory and one template
        Path("docs/project-guide/templates/modes").mkdir(parents=True)
        Path("docs/project-guide/templates/modes/plan-concept-mode.md").write_text("My custom content")

        result = runner.invoke(main, ['init'])

        assert result.exit_code == 0
        assert "Skipped" in result.output
        # The pre-existing file should not be overwritten
        assert Path("docs/project-guide/templates/modes/plan-concept-mode.md").read_text() == "My custom content"


def test_init_sync_error_exits_with_code_2(runner, tmp_path):
    """Test init exits with code 2 when template copy fails."""
    with runner.isolated_filesystem(temp_dir=tmp_path), \
            patch("project_guide.cli._copy_template_tree", side_effect=OSError("Permission denied")):
        result = runner.invoke(main, ['init'])

        assert result.exit_code == 2
        assert "Permission denied" in result.output


def test_status_with_corrupt_config(runner, tmp_path):
    """Test status with corrupt config file exits with code 3."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".project-guide.yml").write_text("not: valid: yaml: [[[")

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 3


def test_status_with_missing_guide_file(runner, tmp_path):
    """Test status shows missing indicator when guide file is deleted."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Delete a guide file
        Path("docs/project-guide/templates/modes/debug-mode.md").unlink()

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "missing" in result.output
        assert "file" in result.output.lower()


def test_status_with_modified_file(runner, tmp_path):
    """Test status shows needs-updating indicator when file content differs."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Modify a file
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("User-modified content")

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "need updating" in result.output


def test_update_with_missing_config(runner, tmp_path):
    """Test update with no config file exits with code 1."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['update'])

        assert result.exit_code == 1
        assert "No .project-guide.yml found" in result.output


def test_update_with_corrupt_config(runner, tmp_path):
    """Test update with corrupt config exits with code 3."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".project-guide.yml").write_text("not: valid: yaml: [[[")

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 3


def test_update_with_invalid_file_name(runner, tmp_path):
    """Test update with non-existent file name exits with code 1."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['update', '--files', 'fake-guide.md'])

        assert result.exit_code == 1
        assert "File 'fake-guide.md' not found" in result.output
        assert "Available files:" in result.output


def test_update_sync_error_exits_with_code_2(runner, tmp_path):
    """Test update exits with code 2 when sync_files raises SyncError."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        with patch("project_guide.cli.sync_files", side_effect=SyncError("Disk full")):
            result = runner.invoke(main, ['update'])

            assert result.exit_code == 2
            assert "Disk full" in result.output


def test_update_modified_file_user_approves(runner, tmp_path):
    """Test update with modified file when user confirms backup and overwrite."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Modify a guide so it's detected as modified
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("User-modified content")

        # User says yes to the prompt
        result = runner.invoke(main, ['update'], input="y\n")

        assert result.exit_code == 0
        assert "Updated (approved by user)" in result.output
        assert "templates/modes/debug-mode.md" in result.output


def test_update_modified_file_user_declines(runner, tmp_path):
    """Test update with modified file when user declines."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Modify a guide
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("User-modified content")

        # User says no to the prompt
        result = runner.invoke(main, ['update'], input="n\n")

        assert result.exit_code == 0
        assert "Skipped (user declined)" in result.output


def test_update_dry_run_with_modified_file(runner, tmp_path):
    """Test update --dry-run shows modified files without changing them."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("User-modified content")
        original = Path("docs/project-guide/templates/modes/debug-mode.md").read_text(encoding="utf-8")

        result = runner.invoke(main, ['update', '--dry-run'])

        assert result.exit_code == 0
        assert "would prompt" in result.output.lower()
        # File should not have changed
        assert Path("docs/project-guide/templates/modes/debug-mode.md").read_text(encoding="utf-8") == original


def test_update_dry_run_with_missing_files(runner, tmp_path):
    """Test update --dry-run shows missing files as 'Would create'."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Delete a file so it's detected as missing
        Path("docs/project-guide/templates/modes/debug-mode.md").unlink()

        result = runner.invoke(main, ['update', '--dry-run'])

        assert result.exit_code == 0
        assert "Would create" in result.output


def test_update_all_declined_message(runner, tmp_path):
    """Test update message when all modified guides are declined."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Modify all guides so they all appear as modified
        guides_dir = Path("docs/project-guide")
        for guide in guides_dir.rglob("*.md"):
            guide.write_text("Modified content")

        # Decline all prompts (enough for all modified guides)
        result = runner.invoke(main, ['update'], input=("n\n" * 50))

        assert result.exit_code == 0
        assert "No files updated" in result.output or "declined" in result.output


def test_update_all_overridden_message(runner, tmp_path):
    """Test update message when all guides are overridden."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        config = Config.load(".project-guide.yml")
        from project_guide.sync import get_all_file_names
        for guide in get_all_file_names():
            config.add_override(guide, "Custom", "0.9.0")
        config.save(".project-guide.yml")

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0
        assert "overridden" in result.output.lower()


def test_update_rerenders_after_template_change(runner, tmp_path):
    """Test that update re-renders go.md after template files are updated."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Modify a template so hash differs, then force update
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("Modified")

        result = runner.invoke(main, ['update', '--force'])

        assert result.exit_code == 0
        assert "Re-rendered go.md" in result.output


def test_override_on_template_relative_path(runner, tmp_path):
    """Test that override works with template-relative paths."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['override', 'templates/modes/plan-concept-mode.md', 'Custom concept workflow'])

        assert result.exit_code == 0
        assert "Marked templates/modes/plan-concept-mode.md as overridden" in result.output

        config = Config.load(".project-guide.yml")
        assert config.is_overridden("templates/modes/plan-concept-mode.md")

        # Unoverride should also work
        result = runner.invoke(main, ['unoverride', 'templates/modes/plan-concept-mode.md'])
        assert result.exit_code == 0

        config = Config.load(".project-guide.yml")
        assert not config.is_overridden("templates/modes/plan-concept-mode.md")


def test_update_skips_overridden_file(runner, tmp_path):
    """Test that update skips overridden files without --force."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Override a file
        config = Config.load(".project-guide.yml")
        config.add_override("templates/modes/debug-mode.md", "Custom debug", __version__)
        config.save(".project-guide.yml")

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0
        assert "Skipped (overridden)" in result.output
        assert "templates/modes/debug-mode.md" in result.output


def test_override_with_missing_config(runner, tmp_path):
    """Test override with no config file exits with code 1."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['override', 'templates/modes/debug-mode.md', 'reason'])

        assert result.exit_code == 1
        assert "No .project-guide.yml found" in result.output


def test_override_with_corrupt_config(runner, tmp_path):
    """Test override with corrupt config exits with code 3."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".project-guide.yml").write_text("not: valid: yaml: [[[")

        result = runner.invoke(main, ['override', 'templates/modes/debug-mode.md', 'reason'])

        assert result.exit_code == 3


def test_unoverride_with_missing_config(runner, tmp_path):
    """Test unoverride with no config file exits with code 1."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['unoverride', 'templates/modes/debug-mode.md'])

        assert result.exit_code == 1
        assert "No .project-guide.yml found" in result.output


def test_unoverride_with_corrupt_config(runner, tmp_path):
    """Test unoverride with corrupt config exits with code 3."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".project-guide.yml").write_text("not: valid: yaml: [[[")

        result = runner.invoke(main, ['unoverride', 'templates/modes/debug-mode.md'])

        assert result.exit_code == 3


def test_overrides_with_corrupt_config(runner, tmp_path):
    """Test overrides command with corrupt config exits with code 3."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".project-guide.yml").write_text("not: valid: yaml: [[[")

        result = runner.invoke(main, ['overrides'])

        assert result.exit_code == 3


def test_purge_missing_guides_directory(runner, tmp_path):
    """Test purge when guides directory does not exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Remove guides directory before purge
        import shutil
        shutil.rmtree("docs/project-guide")

        result = runner.invoke(main, ['purge', '--force'])

        assert result.exit_code == 0
        assert "not found (skipped)" in result.output
        assert not Path(".project-guide.yml").exists()


def test_update_modified_file_apply_sync_error(runner, tmp_path):
    """Test update when apply_file_update raises SyncError during user-approved update."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("User-modified content")

        with patch("project_guide.cli.apply_file_update", side_effect=SyncError("Write failed")):
            result = runner.invoke(main, ['update'], input="y\n")

            assert result.exit_code == 0
            assert "Error updating" in result.output


def test_update_dry_run_no_changes(runner, tmp_path):
    """Test update --dry-run when all guides are current shows no updates needed."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['update', '--dry-run'])

        assert result.exit_code == 0
        assert "No updates needed" in result.output


def test_update_with_missing_file_creates_it(runner, tmp_path):
    """Test update creates missing files and reports them."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Delete a file so it's detected as missing
        Path("docs/project-guide/templates/modes/debug-mode.md").unlink()

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0
        assert "Created" in result.output or "created" in result.output
        assert Path("docs/project-guide/templates/modes/debug-mode.md").exists()


def test_purge_with_corrupt_config(runner, tmp_path):
    """Test purge with corrupt config exits with code 3."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".project-guide.yml").write_text("not: valid: yaml: [[[")

        result = runner.invoke(main, ['purge', '--force'])

        assert result.exit_code == 3


def test_purge_with_confirmation_prompt(runner, tmp_path):
    """Test purge without --force asks for confirmation."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # User confirms
        result = runner.invoke(main, ['purge'], input="y\n")

        assert result.exit_code == 0
        assert "purged" in result.output.lower()
        assert not Path(".project-guide.yml").exists()


def test_purge_missing_config_after_dir_removal(runner, tmp_path):
    """Test purge when config file is already gone."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['purge', '--force'])

        assert result.exit_code == 0
        assert not Path(".project-guide.yml").exists()
        assert not Path("docs/project-guide").exists()
