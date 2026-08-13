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

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import click
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


def test_init_on_already_initialized_project_is_idempotent(runner, tmp_path):
    """Re-running init without --force is a silent exit-0 no-op.

    Idempotent re-run (v2.2.0) — supports unattended/CI use and the pyve
    post-hook integration path. Previously raised click.Abort() / exit 1.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # First init
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Second init without force should exit 0 with an informational message
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        assert "already initialized" in result.output


def test_init_double_run_does_not_modify_files(runner, tmp_path):
    """Second init run does not touch any tracked template files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # First init
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Snapshot mtimes of a representative set of files the installer writes
        tracked = [
            Path(".project-guide.yml"),
            Path("docs/project-guide/.metadata.yml"),
            Path("docs/project-guide/templates/modes/plan-concept-mode.md"),
            Path("docs/project-guide/templates/modes/default-mode.md"),
        ]
        before = {p: p.stat().st_mtime_ns for p in tracked}

        # Second init — idempotent no-op
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Verify no tracked file was rewritten
        after = {p: p.stat().st_mtime_ns for p in tracked}
        assert before == after


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


# --- Story L.b: --no-input flag, auto-detection, and the _require_setting
#     contract. See project_guide/runtime.py for the trigger priority.


def test_init_with_no_input_flag_on_fresh_project(runner, tmp_path, monkeypatch):
    """--no-input on a fresh project → normal install, exit 0."""
    # Clear any ambient env that would make this test non-discriminating
    monkeypatch.delenv("PROJECT_GUIDE_NO_INPUT", raising=False)
    monkeypatch.delenv("CI", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--no-input'])
        assert result.exit_code == 0
        assert "Initializing project-guide" in result.output
        assert "Successfully initialized" in result.output
        assert Path(".project-guide.yml").exists()
        assert Path("docs/project-guide/go.md").exists()


def test_init_with_no_input_and_force_on_initialized_project(runner, tmp_path, monkeypatch):
    """--no-input --force on an initialized project → overwrite, exit 0."""
    monkeypatch.delenv("PROJECT_GUIDE_NO_INPUT", raising=False)
    monkeypatch.delenv("CI", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # First init
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Modify a template, then re-init with --no-input --force
        template_path = Path("docs/project-guide/templates/modes/plan-concept-mode.md")
        original_content = template_path.read_text(encoding="utf-8")
        template_path.write_text("Modified content")

        result = runner.invoke(main, ['init', '--no-input', '--force'])
        assert result.exit_code == 0
        assert template_path.read_text(encoding="utf-8") == original_content


def test_init_with_ci_env_var_is_idempotent_on_rerun(runner, tmp_path, monkeypatch):
    """CI=1 composes cleanly with L.a idempotency: re-run still exits 0.

    This is the regression test for the compose: auto-detection (L.b) +
    idempotent re-run (L.a) must both apply on the second call. Any regression
    that re-introduces `click.Abort()` on re-init would fail here in CI.
    """
    monkeypatch.setenv("CI", "1")
    monkeypatch.delenv("PROJECT_GUIDE_NO_INPUT", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # First init under CI=1 — plain `init`, no explicit flag
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        # Second init under CI=1 — must still exit 0 per L.a
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        assert "already initialized" in result.output


def test_init_with_non_tty_stdin_behaves_like_no_input(runner, tmp_path, monkeypatch):
    """Non-TTY stdin (CliRunner with input=...) behaves like --no-input.

    CliRunner's ``input`` parameter produces a non-TTY stdin; the runtime
    module's TTY-fallback branch treats that as skip-input. End-to-end this
    means piped stdin never hangs on a prompt.
    """
    monkeypatch.delenv("PROJECT_GUIDE_NO_INPUT", raising=False)
    monkeypatch.delenv("CI", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Feed empty stdin — CliRunner makes this a non-TTY file-like object
        result = runner.invoke(main, ['init'], input="")
        assert result.exit_code == 0
        assert Path(".project-guide.yml").exists()


def test_require_setting_contract_exit_code_and_message(runner):
    """FR-L4 regression guard: exercise _require_setting via a dummy command.

    Today no production prompt site calls _require_setting, so this test
    registers a throwaway click command at import time and invokes it through
    CliRunner. The day someone adds a real prompt to init, this contract test
    remains the source of truth for the exact error message format.
    """
    from project_guide.runtime import _require_setting

    @click.command()
    def _dummy():
        _require_setting("project name", "project-name", "PROJECT_GUIDE_PROJECT_NAME")

    result = runner.invoke(_dummy, [])
    assert result.exit_code == 1
    assert (
        "project name is required when --no-input is active. "
        "Provide via --project-name or PROJECT_GUIDE_PROJECT_NAME."
    ) in result.output


# --- Story N.d ---------------------------------------------------------------


def test_init_test_first_flag_persists(runner, tmp_path):
    """init --test-first → config test_first: true."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--test-first'])
        assert result.exit_code == 0
        config = Config.load(".project-guide.yml")
        assert config.test_first is True


def test_init_without_test_first_flag_defaults_false(runner, tmp_path):
    """init without --test-first → config test_first: false."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        config = Config.load(".project-guide.yml")
        assert config.test_first is False


def test_init_test_first_env_var(runner, tmp_path, monkeypatch):
    """PROJECT_GUIDE_TEST_FIRST=1 init → config test_first: true."""
    monkeypatch.setenv("PROJECT_GUIDE_TEST_FIRST", "1")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        config = Config.load(".project-guide.yml")
        assert config.test_first is True


# --- End Story N.d -----------------------------------------------------------


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
        runner.invoke(main, ['mode', 'code_direct'])

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "Mode: code_direct" in result.output
        assert "Generate code directly, test after" in result.output


def test_status_v1_migration_notice(runner, tmp_path):
    """Test status shows migration notice for legacy docs/guides target_dir.

    Note: the version-based leg of this notice is now preempted by
    SchemaVersionError at Config.load (Story N.p). The target_dir leg
    remains for configs whose layout was never migrated.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Simulate a legacy layout still pointing at docs/guides.
        config = Config.load(".project-guide.yml")
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
        assert "plan_concept" in result.output
        assert "code_direct" in result.output
        # Modes are now grouped by category
        assert "Planning" in result.output
        assert "Coding" in result.output


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
        result = runner.invoke(main, ['mode', 'code_direct'])
        assert result.exit_code == 0
        assert "Mode set: code_direct" in result.output

        config = Config.load(".project-guide.yml")
        assert config.current_mode == "code_direct"


def test_mode_renders_output(runner, tmp_path):
    """Test mode command renders go.md to target_dir."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        runner.invoke(main, ['mode', 'debug'])

        output = Path("docs/project-guide/go.md")
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "debug mode" in content


def test_mode_shell_completion_returns_all_modes(runner, tmp_path):
    """Test shell completion returns all mode names when incomplete is empty."""
    from project_guide.cli import _complete_mode_names

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        result = _complete_mode_names(None, None, '')

        assert "default" in result
        assert "plan_concept" in result
        assert "code_direct" in result
        assert "debug" in result
        assert "refactor_plan" in result


def test_mode_shell_completion_filters_by_prefix(runner, tmp_path):
    """Test shell completion filters by prefix."""
    from project_guide.cli import _complete_mode_names

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        result = _complete_mode_names(None, None, 'plan_')

        assert all(name.startswith('plan_') for name in result)
        assert "plan_concept" in result
        assert "plan_features" in result
        assert "plan_tech_spec" in result
        assert "default" not in result
        assert "debug" not in result


def test_mode_shell_completion_no_config(runner, tmp_path):
    """Test shell completion returns empty list when no config exists."""
    from project_guide.cli import _complete_mode_names

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # No init — no config file
        result = _complete_mode_names(None, None, '')
        assert result == []


def test_mode_shell_completion_handles_errors_silently(runner, tmp_path):
    """Test shell completion never crashes — returns [] on any error."""
    from project_guide.cli import _complete_mode_names

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create a corrupt config so loading fails
        Path(".project-guide.yml").write_text("not: valid: yaml: [[[")
        result = _complete_mode_names(None, None, '')
        assert result == []


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
        assert "Would update" in result.output
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


# --- Story N.g ---------------------------------------------------------------


def test_status_stories_section_shows_counts(runner, tmp_path):
    """status with populated stories.md shows correct total/done/planned counts."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        Path("docs/specs").mkdir(parents=True, exist_ok=True)
        Path("docs/specs/stories.md").write_text(
            "### Story A.a: v0.1.0 Hello World [Done]\n"
            "### Story A.b: v0.2.0 Second Story [Planned]\n"
            "### Story A.c: v0.3.0 Third Story [Planned]\n"
        )

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "Stories:" in result.output
        assert "3 total" in result.output
        assert "1 done" in result.output
        assert "2 planned" in result.output
        assert "0 in progress" in result.output
        assert "Story A.b: v0.2.0 Second Story" in result.output


def test_status_stories_all_done(runner, tmp_path):
    """status with all-Done stories shows 0 planned, 0 in progress."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        Path("docs/specs").mkdir(parents=True, exist_ok=True)
        Path("docs/specs/stories.md").write_text(
            "### Story A.a: v0.1.0 Hello World [Done]\n"
            "### Story A.b: v0.2.0 Another Done [Done]\n"
        )

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "2 done" in result.output
        assert "0 planned" in result.output
        assert "0 in progress" in result.output


def test_status_stories_section_omitted_when_no_file(runner, tmp_path):
    """status omits the Stories section when stories.md is absent."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        # docs/specs/stories.md does not exist

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "Stories:" not in result.output


def test_status_stories_section_omitted_when_empty(runner, tmp_path):
    """status omits Stories section when stories.md has no story headings."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        Path("docs/specs").mkdir(parents=True, exist_ok=True)
        Path("docs/specs/stories.md").write_text(
            "# stories.md\n\nNo stories yet.\n\n## Future\n\nSome future items.\n"
        )

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0
        assert "Stories:" not in result.output


def test_status_stories_verbose_shows_phase_breakdown(runner, tmp_path):
    """status --verbose shows per-phase line when stories.md is present."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        Path("docs/specs").mkdir(parents=True, exist_ok=True)
        Path("docs/specs/stories.md").write_text(
            "## Phase A: Alpha Phase (v0.1.0)\n\n"
            "### Story A.a: v0.1.0 Hello World [Done]\n"
            "### Story A.b: v0.2.0 Second Story [Planned]\n"
        )

        result = runner.invoke(main, ['status', '--verbose'])

        assert result.exit_code == 0
        assert "Phase A:" in result.output
        assert "Alpha Phase" in result.output
        assert "1/2 done" in result.output


# --- End Story N.g -----------------------------------------------------------


# --- Story N.h ---------------------------------------------------------------


def test_mode_list_marks_available_mode(runner, tmp_path):
    """Modes with all files_exist present are marked ✓ in the listing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        # plan_concept has no files_exist prerequisite, so it's always available
        result = runner.invoke(main, ['mode'])

        assert result.exit_code == 0
        assert "✓" in result.output


def test_mode_list_marks_unavailable_mode(runner, tmp_path):
    """Modes with unmet files_exist are marked ✗ in the listing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        # code_direct requires docs/specs/stories.md and CHANGELOG.md — not present after bare init
        result = runner.invoke(main, ['mode'])

        assert result.exit_code == 0
        assert "✗" in result.output


def test_mode_list_current_mode_highlighted(runner, tmp_path):
    """Current mode name is rendered with cyan background (reversed) in the listing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        # Use color=True so click.style() escapes are included in output
        result = runner.invoke(main, ['mode'], color=True)

        assert result.exit_code == 0
        # click.style(fg='black', bg='cyan') produces ANSI with bg cyan (46m) and fg black (30m)
        assert "\x1b[30m\x1b[46m" in result.output or "\x1b[46m" in result.output


def test_mode_list_non_tty_shows_listing_no_prompt(runner, tmp_path):
    """Non-TTY CliRunner → annotated listing, no interactive prompt, exit 0."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        # CliRunner stdin is always non-TTY — should_skip_input auto-fires
        result = runner.invoke(main, ['mode'])

        assert result.exit_code == 0
        assert "Current mode:" in result.output
        # Grouped categories shown
        assert "Planning" in result.output
        # No selection prompt emitted
        assert "Select mode" not in result.output


def test_mode_interactive_selection_switches_mode(runner, tmp_path, monkeypatch):
    """Selecting a valid number in the interactive menu switches the mode."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Simulate TTY: should_skip_input returns False so the menu fires
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        # The numbered list puts modes in category order. We'll select
        # whichever number corresponds to 'plan_concept' by looking at output first.
        # Easier: just feed "1\n" and verify mode switched to whatever is #1.
        result = runner.invoke(main, ['mode'], input="1\n")

        assert result.exit_code == 0
        assert "Mode set:" in result.output


# --- End Story N.h -----------------------------------------------------------


# --- Story N.j ---------------------------------------------------------------


def test_init_pyve_detected_stores_version(runner, tmp_path, monkeypatch):
    """init with successful pyve --version stores pyve_version in config.

    Story R.n: what lands in the config is the **bare** version, not the raw
    `pyve --version` line the probe read.
    """
    import subprocess as sp

    import project_guide.cli as cli_module

    mock_result = sp.CompletedProcess(args=['pyve', '--version'], returncode=0, stdout="pyve 1.2.3\n", stderr="")
    monkeypatch.setattr(cli_module.subprocess, 'run', lambda *a, **kw: mock_result)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        config = Config.load(".project-guide.yml")
        assert config.pyve_version == "1.2.3"


def test_init_pyve_not_found_stores_none(runner, tmp_path, monkeypatch):
    """init with FileNotFoundError from pyve stores None; init exits 0."""
    import project_guide.cli as cli_module

    def raise_fnf(*a, **kw):
        raise FileNotFoundError("pyve not found")

    monkeypatch.setattr(cli_module.subprocess, 'run', raise_fnf)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        config = Config.load(".project-guide.yml")
        assert config.pyve_version is None


# --- End Story N.j -----------------------------------------------------------


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


def test_update_modified_file_auto_backup(runner, tmp_path):
    """Test update auto-backs-up and overwrites modified files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Modify a file so its hash differs
        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("User-modified content")

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0
        assert "Updated (backed up)" in result.output
        assert "templates/modes/debug-mode.md" in result.output

        # Verify backup was created
        backups = list(Path("docs/project-guide/templates/modes").glob("debug-mode.md.bak.*"))
        assert len(backups) == 1


def test_update_dry_run_with_modified_file(runner, tmp_path):
    """Test update --dry-run shows modified files without changing them."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        Path("docs/project-guide/templates/modes/debug-mode.md").write_text("User-modified content")
        original = Path("docs/project-guide/templates/modes/debug-mode.md").read_text(encoding="utf-8")

        result = runner.invoke(main, ['update', '--dry-run'])

        assert result.exit_code == 0
        assert "Would update" in result.output
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


def test_update_bulk_auto_backup(runner, tmp_path):
    """Test that update auto-backs-up many modified files in one pass."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Modify all .md files so they all appear modified
        target_dir = Path("docs/project-guide")
        for f in target_dir.rglob("*.md"):
            f.write_text("Modified content")

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0
        assert "Updated (backed up)" in result.output

        # Verify backups were created
        backups = list(target_dir.rglob("*.bak.*"))
        assert len(backups) > 0


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


# --- Story N.e ---------------------------------------------------------------


def test_purge_no_input_flag_skips_confirm(runner, tmp_path):
    """purge --no-input skips confirmation and exits 0."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['purge', '--no-input'])

        assert result.exit_code == 0
        assert not Path(".project-guide.yml").exists()


def test_purge_ci_env_skips_confirm(runner, tmp_path, monkeypatch):
    """CI=1 skips confirmation prompt in purge."""
    monkeypatch.setenv("CI", "1")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['purge'])

        assert result.exit_code == 0
        assert not Path(".project-guide.yml").exists()


def test_purge_tty_without_flag_prompts(runner, tmp_path, monkeypatch):
    """purge without --force or --no-input shows confirmation prompt (regression guard).

    We patch should_skip_input to False to simulate a real TTY environment,
    since CliRunner's stdin is always non-TTY and would auto-skip otherwise.
    """
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        # Simulate a real TTY: should_skip_input returns False
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        # Provide empty input → click.confirm receives "" → aborts
        result = runner.invoke(main, ['purge'], input="\n")

        assert result.exit_code != 0
        assert Path(".project-guide.yml").exists()


def test_update_no_input_flag_exits_zero(runner, tmp_path):
    """update --no-input exits 0."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['update', '--no-input'])

        assert result.exit_code == 0


def test_update_project_guide_no_input_env(runner, tmp_path, monkeypatch):
    """PROJECT_GUIDE_NO_INPUT=1 → update exits 0."""
    monkeypatch.setenv("PROJECT_GUIDE_NO_INPUT", "1")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0


# --- End Story N.e -----------------------------------------------------------


# --- Story N.f ---------------------------------------------------------------


def test_init_quiet_success_emits_no_stdout(runner, tmp_path):
    """init --quiet: success emits nothing to stdout (embedding-friendly)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--quiet'])

        assert result.exit_code == 0
        assert result.stdout == ''
        combined = result.stdout + (result.stderr or '')
        assert "✓ Installed" not in combined
        assert "⚠ Skipped" not in combined


def test_init_quiet_already_initialized_emits_no_stdout(runner, tmp_path):
    """init --quiet when already initialized exits 0 with empty stdout."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        result = runner.invoke(main, ['init', '--quiet'])

        assert result.exit_code == 0
        assert result.stdout == ''


def test_init_force_quiet_backup_notice_on_stderr(runner, tmp_path):
    """init --force --quiet still surfaces the previous-config backup notice on stderr."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        result = runner.invoke(main, ['init', '--force', '--quiet'])

        assert result.exit_code == 0
        assert result.stdout == ''
        stderr = result.stderr or ''
        assert 'Previous config backed up to' in stderr
        assert '.project-guide.yml.bak.' in stderr


def test_update_quiet_success_emits_no_stdout(runner, tmp_path):
    """update --quiet: success emits nothing to stdout."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['update', '--quiet'])

        assert result.exit_code == 0
        assert result.stdout == ''
        combined = result.stdout + (result.stderr or '')
        assert "  ✓ " not in combined
        assert "  + " not in combined
        assert "  • " not in combined


def test_update_quiet_override_warnings_on_stderr(runner, tmp_path):
    """update --quiet still surfaces overridden-file notices on stderr."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        runner.invoke(main, ['override', 'templates/modes/debug-mode.md', 'testing'])

        result = runner.invoke(main, ['update', '--quiet'])

        assert result.exit_code == 0
        assert result.stdout == ''
        assert 'Skipped (overridden)' in (result.stderr or '')
        assert 'debug-mode.md' in (result.stderr or '')


def test_purge_quiet_force_emits_no_stdout(runner, tmp_path):
    """purge --quiet --force: no stdout; no interactive preamble."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['purge', '--quiet', '--force'])

        assert result.exit_code == 0
        assert result.stdout == ''
        stderr = result.stderr or ''
        assert 'The following will be removed' not in stderr
        assert '✓ Removed' not in stderr
        assert 'purged' not in stderr.lower()


def test_quiet_does_not_suppress_errors(runner, tmp_path):
    """Error output is always emitted regardless of --quiet (regression guard)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['update', '--quiet'])

        assert result.exit_code != 0
        assert 'Error' in (result.stderr or '')


# --- End Story N.f -----------------------------------------------------------


# --- Story N.p ---------------------------------------------------------------

def _init_project(runner):
    """Initialize project-guide in the current isolated filesystem."""
    result = runner.invoke(main, ['init'])
    assert result.exit_code == 0, result.output


def _rewrite_config_version(version: str) -> None:
    """Rewrite the `version:` line in `.project-guide.yml` to the given value."""
    config_path = Path(".project-guide.yml")
    content = config_path.read_text()
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("version:"):
            lines[i] = f"version: '{version}'"
            break
    config_path.write_text("\n".join(lines) + "\n")


def test_update_older_schema_does_not_backup_and_aborts(runner, tmp_path):
    """update with an older schema version refuses the load and exits 1.

    The backup moved to ``init --force`` in Story N.q; ``update`` now only
    points the user at the recovery command. Re-running ``update`` against an
    unresolved older-schema config must therefore NOT spam new backups on
    each invocation.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        _rewrite_config_version("1.0")

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 1
        assert "Schema mismatch" in result.output
        assert "init --force" in result.output

        backups = list(Path(".").glob(".project-guide.yml.bak.*"))
        assert backups == [], f"Expected no backup from update, got: {backups}"


def test_update_older_schema_repeated_invocations_create_no_backups(runner, tmp_path):
    """Repeated ``update`` against an older-schema config creates zero backups.

    Regression guard for the backup-spam bug that motivated Story N.q: the
    prior design wrote a new timestamped backup every time ``update`` was
    invoked before the user ran the recovery command.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        _rewrite_config_version("1.0")

        for _ in range(3):
            result = runner.invoke(main, ['update'])
            assert result.exit_code == 1

        backups = list(Path(".").glob(".project-guide.yml.bak.*"))
        assert backups == [], f"Expected no backups on repeated update, got: {backups}"


def test_update_newer_schema_does_not_backup(runner, tmp_path):
    """update with a newer schema version does NOT back up; instructs upgrade."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        _rewrite_config_version("99.0")

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 1
        assert "Upgrade project-guide" in result.output

        backups = list(Path(".").glob(".project-guide.yml.bak.*"))
        assert backups == [], f"Expected no backup on newer-schema path, got: {backups}"


def test_status_older_schema_propagates_error(runner, tmp_path):
    """status with an older schema version surfaces the schema error."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        _rewrite_config_version("1.0")

        result = runner.invoke(main, ['status'])

        assert result.exit_code != 0
        assert "older" in result.output or "schema" in result.output.lower()


def test_update_rerenders_go_md_when_missing(runner, tmp_path):
    """update re-renders go.md when it is missing, even with no template changes.

    Regression guard: go.md is rendered output (not a tracked file), so deleting
    it must cause update to recreate it on the next run even if no templates
    changed. Previously guarded only by `if template_files:` which silently
    skipped the re-render in this case.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        go_md = Path("docs/project-guide/go.md")
        assert go_md.exists(), "init should have rendered go.md"
        go_md.unlink()
        assert not go_md.exists()

        result = runner.invoke(main, ['update'])

        assert result.exit_code == 0, result.output
        assert go_md.exists(), "update should have re-rendered go.md"


# --- End Story N.p -----------------------------------------------------------


# --- Story N.q ---------------------------------------------------------------


def test_init_force_on_existing_config_creates_backup(runner, tmp_path):
    """init --force on an existing project backs up the prior config.

    The backup is the only record of any local customization once the file is
    overwritten, so this is the destructive-overwrite guarantee.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        original = Path(".project-guide.yml").read_text(encoding="utf-8")

        result = runner.invoke(main, ['init', '--force'])

        assert result.exit_code == 0, result.output
        backups = list(Path(".").glob(".project-guide.yml.bak.*"))
        assert len(backups) == 1, f"Expected exactly one backup, got: {backups}"
        assert backups[0].read_text(encoding="utf-8") == original
        assert "Previous config backed up to" in result.output
        assert str(backups[0]) in result.output


def test_init_on_fresh_project_creates_no_backup(runner, tmp_path):
    """init (no --force) on a fresh project does not create a backup."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])

        assert result.exit_code == 0, result.output
        backups = list(Path(".").glob(".project-guide.yml.bak.*"))
        assert backups == [], f"Expected no backup on fresh init, got: {backups}"


def test_init_force_on_fresh_project_creates_no_backup(runner, tmp_path):
    """init --force with no prior config creates no backup (nothing to lose)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--force'])

        assert result.exit_code == 0, result.output
        assert Path(".project-guide.yml").exists()
        backups = list(Path(".").glob(".project-guide.yml.bak.*"))
        assert backups == [], f"Expected no backup on fresh init --force, got: {backups}"


def test_update_older_schema_then_init_force_backs_up_and_recovers(runner, tmp_path):
    """End-to-end recovery flow: update surfaces the mismatch, init --force backs up and refreshes."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        _rewrite_config_version("1.0")
        stale_config = Path(".project-guide.yml").read_text(encoding="utf-8")

        result = runner.invoke(main, ['update'])
        assert result.exit_code == 1
        assert list(Path(".").glob(".project-guide.yml.bak.*")) == []

        result = runner.invoke(main, ['init', '--force'])
        assert result.exit_code == 0, result.output

        backups = list(Path(".").glob(".project-guide.yml.bak.*"))
        assert len(backups) == 1, f"Expected exactly one backup, got: {backups}"
        assert backups[0].read_text(encoding="utf-8") == stale_config

        refreshed = Path(".project-guide.yml").read_text(encoding="utf-8")
        assert "version: '2.0'" in refreshed or 'version: "2.0"' in refreshed


# --- End Story N.q -----------------------------------------------------------


# --- Story N.s ---------------------------------------------------------------


def test_init_project_name_cli_flag_wins(runner, tmp_path, monkeypatch):
    """--project-name explicit-name is persisted to config."""
    monkeypatch.delenv("PROJECT_GUIDE_PROJECT_NAME", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--project-name', 'explicit-name'])
        assert result.exit_code == 0, result.output
        assert Config.load(".project-guide.yml").project_name == "explicit-name"


def test_init_project_name_env_var_wins_over_pyproject(runner, tmp_path, monkeypatch):
    """PROJECT_GUIDE_PROJECT_NAME env var overrides pyproject.toml."""
    monkeypatch.setenv("PROJECT_GUIDE_PROJECT_NAME", "env-name")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("pyproject.toml").write_text(
            '[project]\nname = "from-pyproject"\nversion = "0.0.1"\n', encoding="utf-8"
        )
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0, result.output
        assert Config.load(".project-guide.yml").project_name == "env-name"


def test_init_project_name_reads_pyproject_toml(runner, tmp_path, monkeypatch):
    """With no flag and no env, init reads [project].name from pyproject.toml."""
    monkeypatch.delenv("PROJECT_GUIDE_PROJECT_NAME", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("pyproject.toml").write_text(
            '[project]\nname = "from-pyproject"\nversion = "0.0.1"\n', encoding="utf-8"
        )
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0, result.output
        assert Config.load(".project-guide.yml").project_name == "from-pyproject"


def test_init_project_name_falls_back_to_cwd_name(runner, tmp_path, monkeypatch):
    """With no flag, env, or pyproject.toml, init uses cwd().name."""
    monkeypatch.delenv("PROJECT_GUIDE_PROJECT_NAME", raising=False)
    project_dir = tmp_path / "my-cwd-project"
    project_dir.mkdir()
    with runner.isolated_filesystem(temp_dir=project_dir):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0, result.output
        # isolated_filesystem creates a sub-dir, so check the name is a real
        # filesystem name (not empty); any non-empty resolution is acceptable.
        loaded = Config.load(".project-guide.yml")
        assert loaded.project_name != ""
        assert loaded.project_name == Path.cwd().name


def test_archive_stories_uses_config_project_name_when_header_absent(runner, tmp_path):
    """archive-stories populates fresh stories.md from config.project_name when the old header is missing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--project-name', 'demo'])
        assert result.exit_code == 0

        specs = Path("docs/specs")
        specs.mkdir(parents=True, exist_ok=True)
        # Source without a `# stories.md -- ...` header — forces the CLI to
        # fall back to config.project_name.
        (specs / "stories.md").write_text(
            "## Phase A: Foundation\n\n"
            "### Story A.a: v0.1.0 Hello [Done]\n\n"
            "- [x] Print hello\n",
            encoding="utf-8",
        )

        result = runner.invoke(main, ['archive-stories'])
        assert result.exit_code == 0, result.output

        fresh = (specs / "stories.md").read_text(encoding="utf-8")
        assert "demo" in fresh
        assert "{{" not in fresh


def test_archive_stories_drift_warning_when_cwd_differs_from_config(runner, tmp_path):
    """A mismatch between cwd().name and config.project_name prints a warning; exit 0."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--project-name', 'config-name'])
        assert result.exit_code == 0
        # cwd().name here is the isolated_filesystem tmp, not "config-name"

        specs = Path("docs/specs")
        specs.mkdir(parents=True, exist_ok=True)
        (specs / "stories.md").write_text(
            "# stories.md -- config-name (Python)\n\n"
            "## Phase A: Foundation\n\n"
            "### Story A.a: v0.1.0 Hello [Done]\n\n"
            "- [x] Print hello\n",
            encoding="utf-8",
        )

        result = runner.invoke(main, ['archive-stories'])
        assert result.exit_code == 0, result.output
        combined = result.output + (result.stderr or "")
        assert "differs from config project_name 'config-name'" in combined


# --- End Story N.s -----------------------------------------------------------


# --- Story O.q (v2.5.15) -----------------------------------------------------
# Pin the mode-section rename, _CATEGORY_ORDER reorder, and CLI help expansion:
#   - Planning → Project Planning
#   - Post-Release → Release Planning
#   - plan_phase moves from Project Planning to Release Planning
#   - plan_production_phase joins Release Planning
#   - _CATEGORY_ORDER: Getting Started, Project Planning, Scaffold, Coding,
#     Debugging, Documentation, Refactoring, Release Planning
#   - mode --help docstring enumerates three invocation paths


def test_mode_help_documents_three_invocation_paths(runner, tmp_path):
    """`project-guide mode --help` must enumerate the three invocation modes.

    Reason: the docstring was a single line ("Set or show the active
    development mode."), giving no indication that a positional skips
    the menu, --no-input enumerates modes, or that the bare invocation
    opens an interactive picker. The expanded docstring closes that gap.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['mode', '--help'])
        assert result.exit_code == 0

    # All three invocation paths are documented as worked examples.
    assert "project-guide mode <name>" in result.output
    assert "project-guide mode --no-input" in result.output
    # The interactive menu is named.
    assert "interactive" in result.output.lower()


def test_mode_listing_uses_renamed_sections(runner, tmp_path):
    """The annotated mode listing uses the renamed section labels.

    `Planning` is now `Project Planning`; `Post-Release` is now
    `Release Planning`. The legacy labels must not appear as standalone
    section headers (substring matches like 'Project Planning' contain
    'Planning' — that's expected).
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', '--no-input'])
        assert result.exit_code == 0

    # New labels present
    assert "Project Planning" in result.output
    assert "Release Planning" in result.output
    # Legacy labels are gone as standalone section headers — pin the
    # exact section heading shape so partial matches don't false-positive.
    # Section headings are indented with two spaces in the listing.
    assert "  Post-Release\n" not in result.output


def test_mode_listing_section_order(runner, tmp_path):
    """Sections appear in the new lifecycle order.

    Order: Getting Started → Project Planning → Scaffold → Coding →
    Debugging → Documentation → Refactoring → Release Planning.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', '--no-input'])
        assert result.exit_code == 0

    output = result.output
    # Find each section heading's index; assert ascending order.
    sections_in_order = [
        "Getting Started",
        "Project Planning",
        "Scaffold",
        "Coding",
        "Debugging",
        "Documentation",
        "Refactoring",
        "Release Planning",
    ]
    indices = [output.find(s) for s in sections_in_order]
    # All sections present
    for s, i in zip(sections_in_order, indices, strict=True):
        assert i >= 0, f"Section {s!r} missing from listing"
    # Ascending order
    for s_prev, s_next, i_prev, i_next in zip(
        sections_in_order[:-1],
        sections_in_order[1:],
        indices[:-1],
        indices[1:],
        strict=True,
    ):
        assert i_prev < i_next, (
            f"{s_prev!r} (idx {i_prev}) must appear before "
            f"{s_next!r} (idx {i_next}) in the listing"
        )


def test_plan_phase_in_release_planning_section(runner, tmp_path):
    """plan_phase is grouped under Release Planning, not Project Planning.

    Per Story O.q's lifecycle organization: phase planning is repeated
    work (each release ships at least one phase), not one-time-per-project
    work. plan_phase moves to Release Planning alongside plan_production_phase
    and archive_stories.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', '--no-input'])
        assert result.exit_code == 0

    output = result.output
    release_idx = output.find("Release Planning")
    project_idx = output.find("Project Planning")
    # The next section after Release Planning is the end of the listing
    # (or the implicit footer); use the end of output as the upper bound.
    plan_phase_idx = output.find("plan_phase\n") if "plan_phase\n" in output else output.find("plan_phase ")
    # plan_phase must appear after the Release Planning header and before
    # any text following it that isn't another mode name.
    assert release_idx >= 0
    assert plan_phase_idx > release_idx, (
        "plan_phase must appear under the Release Planning section, "
        "not under Project Planning."
    )
    # And plan_phase appears AFTER Project Planning (the previous section
    # heading), not within it — the Project Planning section is bounded
    # above by the Release Planning section heading.
    assert plan_phase_idx > project_idx


def test_plan_production_phase_registered_in_release_planning(runner, tmp_path):
    """plan_production_phase appears under Release Planning.

    Confirms that `_MODE_CATEGORIES["plan_production_phase"]` resolves
    to "Release Planning" and that the mode appears in the rendered
    listing under that section.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', '--no-input'])
        assert result.exit_code == 0

    output = result.output
    release_idx = output.find("Release Planning")
    pp_idx = output.find("plan_production_phase")
    assert release_idx >= 0
    assert pp_idx > release_idx, (
        "plan_production_phase must appear under the Release Planning section."
    )


# --- End Story O.q -----------------------------------------------------------


# --- Story P.a: heal command ------------------------------------------------


@pytest.fixture
def prompt_tty(monkeypatch):
    """Force the [Y/n] prompt path by simulating an interactive TTY.

    CliRunner's stdin is non-TTY, which makes ``should_skip_input()`` return
    True and trigger the auto-yes / stderr-notice path added in Story P.c.
    Tests that specifically exercise the prompt path patch this signal off.
    """
    import project_guide.cli as cli_module

    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)


def test_heal_clean_state_is_silent_and_writes_nothing(runner, tmp_path):
    """heal exits 0 with no stdout and no writes when there is no drift."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        # Snapshot file mtimes so we can prove no writes happened.
        target = Path("docs/project-guide")
        before = {p: p.stat().st_mtime_ns for p in target.rglob("*") if p.is_file()}

        result = runner.invoke(main, ['heal'])

        assert result.exit_code == 0, result.output
        assert result.stdout == "", f"Expected silent stdout, got: {result.stdout!r}"

        after = {p: p.stat().st_mtime_ns for p in target.rglob("*") if p.is_file()}
        assert before == after, "heal must not write when there is no drift"


def test_heal_creates_missing_files_on_default_yes(runner, tmp_path, prompt_tty):
    """heal prompts on missing files and creates them when the user accepts default (Enter)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()
        assert not missing_path.exists()

        result = runner.invoke(main, ['heal'], input="\n")

        assert result.exit_code == 0, result.output
        assert "missing or stale" in result.output
        assert missing_path.exists()


def test_heal_creates_missing_files_on_explicit_yes(runner, tmp_path, prompt_tty):
    """heal accepts an explicit `y` response."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        result = runner.invoke(main, ['heal'], input="y\n")

        assert result.exit_code == 0, result.output
        assert missing_path.exists()


def test_heal_creates_missing_files_on_capital_yes(runner, tmp_path, prompt_tty):
    """heal accepts an explicit `Y` response."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        result = runner.invoke(main, ['heal'], input="Y\n")

        assert result.exit_code == 0, result.output
        assert missing_path.exists()


def test_heal_repairs_stale_files_with_backup(runner, tmp_path, prompt_tty):
    """heal backs up and overwrites files whose content drifted from the template."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        stale_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        # The bundled template is UTF-8; on Windows, Path.read_text() defaults
        # to the locale (cp1252) and fails on multi-byte sequences — pin to
        # utf-8 explicitly here and on every comparison read below.
        original = stale_path.read_text(encoding='utf-8')
        stale_path.write_text("Locally modified — not the template", encoding='utf-8')

        result = runner.invoke(main, ['heal'], input="y\n")

        assert result.exit_code == 0, result.output
        assert "missing or stale" in result.output
        assert stale_path.read_text(encoding='utf-8') == original

        backups = list(stale_path.parent.glob("debug-mode.md.bak.*"))
        assert len(backups) == 1


def test_heal_decline_exits_one_and_writes_nothing(runner, tmp_path, prompt_tty):
    """Declining the prompt exits 1 and does not modify any files."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        result = runner.invoke(main, ['heal'], input="n\n")

        assert result.exit_code == 1
        assert not missing_path.exists()


def test_heal_without_config_exits_one_with_exact_message(runner, tmp_path):
    """heal in an uninitialized project exits 1 with the canonical error."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['heal'])

        assert result.exit_code == 1
        assert (
            "Missing .project-guide.yml — run 'project-guide init' to bootstrap the project."
            in result.output
        )


def test_heal_older_schema_propagates_guidance(runner, tmp_path):
    """heal preserves update's older-schema guidance (point at init --force)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        _rewrite_config_version("1.0")

        result = runner.invoke(main, ['heal'])

        assert result.exit_code == 1
        assert "Schema mismatch" in result.output
        assert "init --force" in result.output


def test_heal_newer_schema_propagates_guidance(runner, tmp_path):
    """heal preserves update's newer-schema guidance."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        _rewrite_config_version("99.0")

        result = runner.invoke(main, ['heal'])

        assert result.exit_code == 1
        assert "Upgrade project-guide" in result.output


# --- End Story P.a -----------------------------------------------------------


# --- Story P.b: auto-heal hook ----------------------------------------------


@pytest.fixture
def hook_enabled(monkeypatch):
    """Opt out of the autouse PROJECT_GUIDE_HEALING=1 guard.

    Tests in this section exercise the hook itself, so they must run with
    the hook active. The autouse fixture in ``conftest.py`` disables it by
    default for every other test.
    """
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)


def test_hook_invisible_when_no_drift(runner, tmp_path, hook_enabled):
    """Hook produces no extra output when the install is clean."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0, result.output
        assert "missing or stale" not in result.output


def test_hook_applies_fix_on_yes_then_runs_subcommand(runner, tmp_path, hook_enabled, prompt_tty):
    """Drift + 'y' → hook heals + the requested subcommand still runs."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        result = runner.invoke(main, ['status'], input="y\n")

        assert result.exit_code == 0, result.output
        assert "missing or stale" in result.output
        assert missing_path.exists()
        # Status's own header still rendered, proving the subcommand ran.
        assert "project-guide v" in result.output


def test_hook_decline_continues_subcommand_without_writing(runner, tmp_path, hook_enabled, prompt_tty):
    """Drift + 'n' → no writes, but the subcommand still runs."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        result = runner.invoke(main, ['status'], input="n\n")

        assert result.exit_code == 0, result.output
        assert "missing or stale" in result.output
        assert not missing_path.exists()
        # Subcommand still ran.
        assert "project-guide v" in result.output


def test_hook_skipped_when_config_missing(runner, tmp_path, hook_enabled):
    """No `.project-guide.yml` → hook silently skips; subcommand handles it."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # No init — config is absent. Status should produce its own error.
        result = runner.invoke(main, ['status'])

        assert "missing or stale" not in result.output
        assert ".project-guide.yml" in result.output


def test_hook_skipped_when_recursion_guard_set(runner, tmp_path, hook_enabled, monkeypatch):
    """PROJECT_GUIDE_HEALING=1 → hook skipped even with drift."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        monkeypatch.setenv("PROJECT_GUIDE_HEALING", "1")
        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0, result.output
        assert "missing or stale" not in result.output
        assert not missing_path.exists()


def test_hook_fires_for_help_flag(runner, tmp_path, hook_enabled, prompt_tty):
    """`--help` triggers the hook before the help text prints."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        result = runner.invoke(main, ['--help'], input="y\n")

        assert "missing or stale" in result.output
        assert missing_path.exists()
        # Help text still rendered.
        assert "Usage:" in result.output


def test_hook_fires_for_version_flag(runner, tmp_path, hook_enabled, prompt_tty):
    """`--version` triggers the hook before the version prints."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        result = runner.invoke(main, ['--version'], input="y\n")

        assert "missing or stale" in result.output
        assert missing_path.exists()
        # Version still printed.
        assert __version__ in result.output


def test_heal_command_sets_recursion_guard_env_var(runner, tmp_path, hook_enabled, prompt_tty, monkeypatch):
    """Direct `heal` invocation sets PROJECT_GUIDE_HEALING=1 (subprocess guard)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        # Explicitly clear before invocation.
        monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
        result = runner.invoke(main, ['heal'], input="y\n")

        assert result.exit_code == 0, result.output
        assert os.environ.get("PROJECT_GUIDE_HEALING") == "1"


# --- End Story P.b -----------------------------------------------------------


# --- Story P.c: --no-input auto-yes for heal --------------------------------


def test_heal_no_input_flag_auto_yes_writes_and_emits_notice(runner, tmp_path):
    """--no-input + drift → no prompt, stderr notice, files written, exit 0."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        # No piped input — would hang under the prompt path; --no-input bypasses.
        result = runner.invoke(main, ['heal', '--no-input'])

        assert result.exit_code == 0, result.output
        assert "Auto-healing" in result.output
        assert "--no-input" in result.output
        assert "missing or stale" not in result.output  # the prompt path's summary
        assert missing_path.exists()


def test_heal_ci_env_triggers_auto_yes(runner, tmp_path, monkeypatch):
    """CI=1 + drift → auto-yes path (no flag needed)."""
    monkeypatch.setenv("CI", "1")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        result = runner.invoke(main, ['heal'])

        assert result.exit_code == 0, result.output
        assert "Auto-healing" in result.output
        assert missing_path.exists()


def test_heal_non_tty_stdin_triggers_auto_yes(runner, tmp_path):
    """Non-TTY stdin + drift → auto-yes path (CliRunner stdin is non-TTY)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        # No --no-input flag, no CI env — should_skip_input returns True purely
        # via the non-TTY signal that CliRunner produces by default.
        result = runner.invoke(main, ['heal'])

        assert result.exit_code == 0, result.output
        assert "Auto-healing" in result.output
        assert missing_path.exists()


def test_heal_no_input_clean_state_remains_silent(runner, tmp_path):
    """--no-input with no drift → still silent; the notice is auto-healing-specific."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        result = runner.invoke(main, ['heal', '--no-input'])

        assert result.exit_code == 0, result.output
        assert result.stdout == "", f"Expected silent stdout, got: {result.stdout!r}"
        assert "Auto-healing" not in result.output


def test_hook_under_skip_input_heals_silently_with_notice(runner, tmp_path, hook_enabled):
    """Auto-hook under non-TTY parent invocation → auto-yes + notice + subcommand runs."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)

        missing_path = Path("docs/project-guide/templates/modes/debug-mode.md")
        missing_path.unlink()

        # No piped input. CliRunner's non-TTY stdin should trigger the hook's
        # auto-yes path (Story P.c) — the parent command is just `status`.
        result = runner.invoke(main, ['status'])

        assert result.exit_code == 0, result.output
        assert "Auto-healing" in result.output
        assert missing_path.exists()
        # Subcommand still ran.
        assert "project-guide v" in result.output


# --- End Story P.c -----------------------------------------------------------


# --- Story P.d / P.j / P.l: gitignore block inversion + tightening + IDE compat ---


def _expected_gitignore_block() -> str:
    """Compute the canonical gitignore block from the bundled template tree.

    Mirrors `_build_project_guide_block()`'s enumeration so tests stay
    honest when the bundled tree changes — adding a new top-level template
    file/directory will be picked up by both the writer and this helper.
    """
    from project_guide.cli import _get_package_template_dir

    pkg_root = _get_package_template_dir()
    target = "docs/project-guide"
    entries = ["# project-guide"]
    for child in sorted(pkg_root.iterdir(), key=lambda p: p.name):
        if child.name == "go.md":
            continue
        suffix = "/" if child.is_dir() else ""
        entries.append(f"/{target}/{child.name}{suffix}")
    entries.append(f"/{target}/**/*.bak.*")
    return "\n".join(entries) + "\n"


def test_init_fresh_writes_inverted_gitignore_block(runner, tmp_path):
    """Fresh `init` writes the canonical explicit-list track-only-go.md block."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])

        assert result.exit_code == 0, result.output
        gitignore = Path(".gitignore").read_text()
        expected = _expected_gitignore_block()
        assert expected in gitignore
        # No negation pattern — the whole point of the P.l rewrite.
        assert "!" not in gitignore.split("# project-guide", 1)[1].split("\n\n", 1)[0]


def test_init_force_rewrites_legacy_bak_only_block_cleanly(runner, tmp_path):
    """`init --force` replaces the pre-P.d `.bak.*`-only block in-place."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Seed a prior .gitignore with the pre-P.d block (the .bak.*-only
        # form this repo used through Story P.c).
        Path(".gitignore").write_text(
            "*.pyc\n"
            "\n"
            "# project-guide\n"
            "docs/project-guide/**/*.bak.*\n"
        )

        result = runner.invoke(main, ['init', '--force'])

        assert result.exit_code == 0, result.output
        gitignore = Path(".gitignore").read_text()
        # Old block lines that are not in the canonical form must be gone.
        assert gitignore.count("# project-guide") == 1, gitignore
        assert _expected_gitignore_block() in gitignore
        # Surrounding content preserved.
        assert "*.pyc\n" in gitignore


def test_init_force_rewrites_v260_four_line_block_to_explicit_list(runner, tmp_path):
    """`init --force` on a v2.6.0-shipped 4-line block migrates to the v2.7.1 explicit-list form."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # v2.6.0 canonical form — all four lines are still recognized,
        # so the writer cleanly rewrites the block.
        Path(".gitignore").write_text(
            "*.pyc\n"
            "\n"
            "# project-guide\n"
            "docs/project-guide/**\n"
            "!docs/project-guide/go.md\n"
            "docs/project-guide/**/*.bak.*\n"
        )

        result = runner.invoke(main, ['init', '--force'])

        assert result.exit_code == 0, result.output
        gitignore = Path(".gitignore").read_text()
        assert gitignore.count("# project-guide") == 1, gitignore
        assert _expected_gitignore_block() in gitignore
        # The old negation form must be gone.
        assert "!docs/project-guide/go.md" not in gitignore
        assert "*.pyc\n" in gitignore


def test_init_force_rewrites_v261_three_line_block_to_explicit_list(runner, tmp_path):
    """`init --force` on a v2.6.1/v2.7.0-shipped 3-line negation block migrates to v2.7.1 explicit-list."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".gitignore").write_text(
            "*.pyc\n"
            "\n"
            "# project-guide\n"
            "docs/project-guide/**\n"
            "!docs/project-guide/go.md\n"
        )

        result = runner.invoke(main, ['init', '--force'])

        assert result.exit_code == 0, result.output
        gitignore = Path(".gitignore").read_text()
        assert gitignore.count("# project-guide") == 1, gitignore
        assert _expected_gitignore_block() in gitignore
        assert "!docs/project-guide/go.md" not in gitignore


def test_init_with_existing_canonical_block_is_idempotent(runner, tmp_path):
    """Running `init` over a project whose .gitignore is already canonical does not rewrite."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".gitignore").write_text("foo\n\n" + _expected_gitignore_block())
        before = Path(".gitignore").read_text()

        result = runner.invoke(main, ['init'])

        assert result.exit_code == 0, result.output
        after = Path(".gitignore").read_text()
        assert after == before


def test_init_warns_on_foreign_project_guide_block_and_leaves_it_untouched(runner, tmp_path):
    """A `# project-guide` block with hand-customized lines is left alone with a warning."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        foreign_block = (
            "# project-guide\n"
            "docs/project-guide/**/*.bak.*\n"
            "some/unrelated/path\n"  # foreign line — not under /docs/project-guide/
        )
        Path(".gitignore").write_text(foreign_block)

        result = runner.invoke(main, ['init'])

        assert result.exit_code == 0, result.output
        # Warning emitted, no rewrite.
        assert "unrecognized entries" in result.output
        assert Path(".gitignore").read_text() == foreign_block


def test_init_appends_block_when_no_prior_project_guide_section(runner, tmp_path):
    """An existing .gitignore without a `# project-guide` header gets one appended."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".gitignore").write_text("*.pyc\n.venv/\n")

        result = runner.invoke(main, ['init'])

        assert result.exit_code == 0, result.output
        gitignore = Path(".gitignore").read_text()
        assert "*.pyc\n" in gitignore
        assert ".venv/\n" in gitignore
        assert _expected_gitignore_block() in gitignore


# --- End Story P.d / P.j / P.l ----------------------------------------------


# --- Story P.k: project-guide git-push wrapper ------------------------------


_STORIES_HEADER = """\
# stories.md -- testproject (python)

## Phase A: Initial

"""


def _write_stories_md(*headings: str) -> None:
    """Write `docs/specs/stories.md` with the provided story headings.

    Each entry must be a complete `### Story X.y: ... [Status]` line.
    A trivial `- [x] done` checklist item is appended after every heading
    so each story registers as a real (non-header) story under P.v's
    header-detection heuristic. Tests that need to author a header story
    (zero checklist items) or vary the body content should use
    ``_write_stories_md_raw`` instead.
    """
    decorated = "\n\n".join(f"{h}\n\n- [x] done" for h in headings)
    _write_stories_md_raw(decorated)


def _write_stories_md_raw(body: str) -> None:
    """Write `docs/specs/stories.md` verbatim under the standard header."""
    stories_dir = Path("docs/specs")
    stories_dir.mkdir(parents=True, exist_ok=True)
    (stories_dir / "stories.md").write_text(
        _STORIES_HEADER + body + "\n", encoding="utf-8"
    )


def _mock_git_log_subjects(monkeypatch, subjects: list[str], git_push_argv_capture: list | None = None, branch: str = "main"):
    """Patch subprocess.run so `git log` returns the given subjects, `git
    rev-parse --abbrev-ref HEAD` returns the given branch name, and
    `git-push` invocations capture their argv into the given list."""
    import project_guide.cli as cli_module

    class _FakeCompleted:
        def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(argv, **kwargs):
        if argv and argv[:2] == ["git", "log"]:
            return _FakeCompleted(0, stdout="\n".join(subjects) + ("\n" if subjects else ""))
        if argv and argv[:2] == ["git", "rev-parse"]:
            return _FakeCompleted(0, stdout=branch + "\n")
        # Anything else is a git-push invocation in these tests.
        if git_push_argv_capture is not None:
            git_push_argv_capture.append(list(argv))
        return _FakeCompleted(0)

    monkeypatch.setattr(cli_module.subprocess, "run", fake_run)


def _mock_git_push_on_path(monkeypatch, path: str | None = "/usr/local/bin/git-push"):
    """Patch `shutil.which("git-push")` to return the given path (or None)."""
    import project_guide.cli as cli_module

    def fake_which(name):
        if name == "git-push":
            return path
        return None  # other lookups don't matter for these tests

    monkeypatch.setattr(cli_module.shutil, "which", fake_which)


def test_git_push_happy_path_invokes_gitbetter_with_derived_message(runner, tmp_path, monkeypatch):
    """Last [Done] story, not yet committed → git-push called with derived message."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert len(captured) == 1, captured
        argv = captured[0]
        assert argv[0] == "/usr/local/bin/git-push"
        assert argv[1] == "A.a: v0.1.0 Hello World"


def test_git_push_passes_branch_name_through(runner, tmp_path, monkeypatch):
    """BRANCH_NAME positional appears as second argument to git-push."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-push', 'feature/xyz'])

        assert result.exit_code == 0, result.output
        argv = captured[0]
        assert argv == ["/usr/local/bin/git-push", "A.a: v0.1.0 Hello World", "feature/xyz"]


def test_git_push_transforms_backticks_and_double_quotes_to_single_quotes(runner, tmp_path, monkeypatch):
    """`foo` and \"Hello\" → 'foo' and 'Hello' in the derived message."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            '### Story G.a: v1.2.3 New command `foo` with "Hello" [Done]',
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert captured[0][1] == "G.a: v1.2.3 New command 'foo' with 'Hello'"


def test_git_push_passes_single_quotes_through_unchanged(runner, tmp_path, monkeypatch):
    """Single quotes in the title pass through (no shell quoting concern)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story B.c: Handle the developer's input correctly [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert captured[0][1] == "B.c: Handle the developer's input correctly"


def test_git_push_handles_doc_only_story_without_version_prefix(runner, tmp_path, monkeypatch):
    """Doc-only stories have no `vX.Y.Z` in the title — message reflects that."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story M.c: align specs with FR-9 [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert captured[0][1] == "M.c: align specs with FR-9"


def test_git_push_exits_zero_when_last_done_story_is_already_committed(runner, tmp_path, monkeypatch):
    """Already-committed → exit 0 (nothing real to commit; repo is in the
    desired state). Story P.v changed this from exit 1 to exit 0; git-push
    is still not invoked."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.a: v0.1.0 Hello World"],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0
        assert "Nothing to commit" in result.output
        assert captured == [], "git-push must not be invoked when there is nothing to commit"


def test_git_push_errors_on_multiple_uncommitted_done_stories_with_no_input(runner, tmp_path, monkeypatch):
    """Multi-uncommitted + --no-input → bundle offer auto-declined → exit 1
    listing the IDs; git-push not invoked. (P.u: the bundle-offer prompt is
    skipped under --no-input so CI never silently bundles.)"""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
            "### Story A.b: v0.2.0 Second story [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-push', '--no-input'])

        assert result.exit_code == 1
        assert "Multiple uncommitted [Done] stories" in result.output
        assert "A.a" in result.output
        assert "A.b" in result.output
        assert captured == []


def test_git_push_errors_on_multiple_uncommitted_when_bundle_declined(runner, tmp_path, monkeypatch):
    """Multi-uncommitted + interactive `n` at bundle prompt → exit 1 with the
    manual-resolution hint; git-push not invoked."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
            "### Story A.b: v0.2.0 Second story [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)
        # CliRunner stdin is non-TTY; simulate interactive shell.
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='n\n')

        assert result.exit_code == 1
        assert "Multiple uncommitted [Done] stories" in result.output
        assert captured == []


def test_git_push_errors_when_no_done_story_exists(runner, tmp_path, monkeypatch):
    """No [Done] heading in stories.md → exit 1 with no-completed-story message."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Planned]",
        )
        _mock_git_push_on_path(monkeypatch)

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 1
        assert "No completed story found" in result.output
        assert "docs/specs/stories.md" in result.output


def test_git_push_errors_when_stories_md_is_missing(runner, tmp_path, monkeypatch):
    """stories.md absent → exit 1 with a stories-md-not-found message."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Deliberately do NOT call _write_stories_md.
        _mock_git_push_on_path(monkeypatch)

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 1
        assert "docs/specs/stories.md not found" in result.output


def test_git_push_errors_when_gitbetter_not_on_path(runner, tmp_path, monkeypatch):
    """`git-push` missing on PATH → exit 1 with install hint."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
        )
        _mock_git_push_on_path(monkeypatch, path=None)
        _mock_git_log_subjects(monkeypatch, subjects=[])

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 1
        assert "git-push not found on PATH" in result.output
        assert "brew install pointmatic/tap/gitbetter" in result.output


def test_git_push_propagates_child_exit_code(runner, tmp_path, monkeypatch):
    """Non-zero exit from gitbetter's `git-push` propagates unchanged."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
        )
        _mock_git_push_on_path(monkeypatch)

        class _FakeCompleted:
            def __init__(self, returncode):
                self.returncode = returncode
                self.stdout = ""
                self.stderr = ""

        def fake_run(argv, **kwargs):
            if argv and argv[:2] == ["git", "log"]:
                return _FakeCompleted(0)
            # git-push invocation: return non-zero
            return _FakeCompleted(7)

        monkeypatch.setattr(cli_module.subprocess, "run", fake_run)

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 7, result.output


def test_git_push_picks_up_subnumbered_last_done_story_scenario_a(runner, tmp_path, monkeypatch):
    """Scenario A — post-implementation follow-up: ..., J.l, J.m, J.m.1.

    Reported bug: when the last [Done] story is `J.m.1`, the wrapper
    silently fell back to `J.l` and reported it as already committed.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story J.l: update remaining refs [Done]",
            "### Story J.m: v0.69.0 Integrate component [Done]",
            "### Story J.m.1: v0.70.0 Follow-up after J.m [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "J.l: update remaining refs",
                "J.m: v0.69.0 Integrate component",
            ],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == "J.m.1: v0.70.0 Follow-up after J.m"


def test_git_push_picks_up_subnumbered_last_done_story_scenario_b(runner, tmp_path, monkeypatch):
    """Scenario B — pre-implementation split: ..., J.l, J.m.1, J.m.2 (no bare J.m).

    When J.m's scope is split before implementation, the bare J.m heading
    never exists. The wrapper's "last [Done]" must be J.m.2.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story J.l: update remaining refs [Done]",
            "### Story J.m.1: v0.69.0 First half of the split [Done]",
            "### Story J.m.2: v0.70.0 Second half of the split [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "J.l: update remaining refs",
                "J.m.1: v0.69.0 First half of the split",
            ],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == "J.m.2: v0.70.0 Second half of the split"


def test_git_push_already_committed_subnumbered_takes_nothing_to_commit_path(runner, tmp_path, monkeypatch):
    """Already-committed detection must recognize sub-numbered IDs in
    commit subjects (e.g. `J.m.1: ...`), not just `J.m: ...`. Without
    this, a sub-numbered story would be re-pushed silently. P.v: the
    success case is now exit 0 + "nothing to commit"."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story J.m.1: v0.70.0 Follow-up after J.m [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["J.m.1: v0.70.0 Follow-up after J.m"],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0
        assert "Nothing to commit" in result.output
        assert captured == [], "git-push must not be invoked when there is nothing to commit"


# --- End Story P.k ----------------------------------------------------------


# --- Story P.u: bundle-offer flow + bundled-commit recognition --------------


def test_git_push_recognizes_bundled_commit_in_already_committed_check(runner, tmp_path, monkeypatch):
    """Field-bug regression: a bundled commit subject like
    `H.a, H.b, H.c InputSource ...` must mark all three IDs as committed.
    Pre-P.u, the single-ID regex missed bundled subjects entirely and
    spuriously reported the bundled stories as uncommitted. Post-P.v,
    "all committed" is the exit-0 nothing-to-commit path."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story H.a: InputSource sidecar labels [Done]",
            "### Story H.b: flat-image layout [Done]",
            "### Story H.c: InputSource partitions [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "H.a, H.b, H.c InputSource sidecar labels + flat-image layout + InputSource partitions",
            ],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0
        assert "Nothing to commit" in result.output
        assert captured == []


def test_git_push_bundle_offer_accepted_invokes_gitbetter(runner, tmp_path, monkeypatch):
    """Multi-uncommitted + interactive `y` → git-push invoked with bundled message."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story H.j: v0.10.0 sample_per_class filter [Done]",
            "### Story H.k: v0.11.0 sample_per_class_fractional filter [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='y\n')

        assert result.exit_code == 0, result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == (
            "H.j: v0.10.0, H.k: v0.11.0 "
            "sample_per_class filter + sample_per_class_fractional filter"
        )


def test_git_push_bundle_offer_format_omits_version_for_versionless_stories(runner, tmp_path, monkeypatch):
    """Stories without a leading `vX.Y.Z ` get no `: <ver>` segment in the bundle."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story H.a: InputSource sidecar labels [Done]",
            "### Story H.b: flat-image layout [Done]",
            "### Story H.c: InputSource partitions [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='y\n')

        assert result.exit_code == 0, result.output
        assert captured[0][1] == (
            "H.a, H.b, H.c: InputSource sidecar labels + flat-image layout + InputSource partitions"
        )


def test_git_push_bundle_offer_mixed_versions(runner, tmp_path, monkeypatch):
    """A bundle with some versioned + some versionless stories formats correctly."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story H.a: Foo [Done]",
            "### Story H.b: v1.2.3 Bar [Done]",
            "### Story H.c: Baz [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='y\n')

        assert result.exit_code == 0, result.output
        assert captured[0][1] == "H.a, H.b: v1.2.3, H.c: Foo + Bar + Baz"


def test_git_push_bundle_offer_branch_name_pass_through(runner, tmp_path, monkeypatch):
    """BRANCH_NAME positional still appears after the bundled message.

    Story R.p put one prompt ahead of this one: naming a destination from
    `main` now reaches the no-anchor offer (`Commit just the last one?`), and
    declining it falls through to the bundle offer this test is about. Hence
    `n` then `y` — the pass-through assertion is unchanged.
    """
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 first [Done]",
            "### Story A.b: v0.2.0 second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push', 'feature/xyz'], input='n\ny\n')

        assert result.exit_code == 0, result.output
        argv = captured[0]
        assert argv[0] == "/usr/local/bin/git-push"
        assert argv[1] == "A.a: v0.1.0, A.b: v0.2.0 first + second"
        assert argv[2] == "feature/xyz"


def test_git_push_bundle_offer_no_input_does_not_prompt(runner, tmp_path, monkeypatch):
    """Under --no-input the bundle offer is auto-declined and no Y/n prompt is shown."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 first [Done]",
            "### Story A.b: v0.2.0 second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-push', '--no-input'])

        assert result.exit_code == 1
        assert "Use this message?" not in result.output
        assert "Multiple uncommitted [Done] stories" in result.output
        assert captured == []


def test_git_push_duplicate_story_id_warning_interactive_continue(runner, tmp_path, monkeypatch):
    """Same ID in 2+ commit subjects → warning + Y/n; `y` proceeds with normal flow."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        # A.a appears in two commit subjects → duplicate.
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "A.a: v0.1.0 Hello World",
                "A.a: v0.1.1 Hello World patch",
            ],
            git_push_argv_capture=captured,
        )
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='y\n')

        # A.a is committed → A.b is the lone uncommitted; single-story flow.
        assert result.exit_code == 0, result.output
        assert "duplicate story ID" in result.output
        assert "A.a" in result.output
        assert len(captured) == 1
        assert captured[0][1] == "A.b: v0.2.0 Second"


def test_git_push_duplicate_story_id_warning_interactive_abort(runner, tmp_path, monkeypatch):
    """Same ID in 2+ commit subjects → warning + Y/n; `n` exits 1 without invoking git-push."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "A.a: v0.1.0 Hello World",
                "A.a: v0.1.1 Hello World patch",
            ],
            git_push_argv_capture=captured,
        )
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='n\n')

        assert result.exit_code == 1
        assert "duplicate story ID" in result.output
        assert captured == []


def test_git_push_duplicate_story_id_warning_no_input_auto_aborts(runner, tmp_path, monkeypatch):
    """Under --no-input the duplicate warning auto-aborts (no Y/n prompt)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "A.a: v0.1.0 Hello World",
                "A.a: v0.1.1 Hello World patch",
            ],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push', '--no-input'])

        assert result.exit_code == 1
        assert "duplicate story ID" in result.output
        assert "Continue?" not in result.output
        assert "Aborting under --no-input" in result.output
        assert captured == []


def test_git_push_duplicate_detection_treats_bundle_ids_as_distinct(runner, tmp_path, monkeypatch):
    """A single bundled commit with multiple distinct IDs is not a duplicate.
    Both stories committed → P.v exit-0 nothing-to-commit path; no duplicate warning."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
            "### Story B.a: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        # Both IDs appear, but each only once across all subjects.
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "A.a, B.a Bundled foundation work",
            ],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0
        assert "duplicate story ID" not in result.output
        assert "Nothing to commit" in result.output


def test_git_push_bundle_offer_sanitizes_quotes(runner, tmp_path, monkeypatch):
    """Backticks and double quotes inside bundled titles become single quotes."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 New command `foo` [Done]",
            "### Story A.b: v0.2.0 Said \"hi\" [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='y\n')

        assert result.exit_code == 0, result.output
        assert captured[0][1] == (
            "A.a: v0.1.0, A.b: v0.2.0 New command 'foo' + Said 'hi'"
        )


# --- End Story P.u ----------------------------------------------------------


# --- Story P.v: header-story awareness + out-of-sequence detection ----------


def _stories_md_with_bodies(*entries: tuple[str, str]) -> str:
    """Build a stories.md body from `(heading, body)` pairs.

    The `body` is appended verbatim after the heading. Use an empty body
    string for a header story (no checklist items); use `"- [x] done"` for
    a real story.
    """
    return "\n\n".join(
        f"{heading}\n\n{body}" if body else heading
        for heading, body in entries
    )


def test_git_push_skips_header_story_with_no_checklist(runner, tmp_path, monkeypatch):
    """A [Done] story whose body has no `- [ ]` / `- [x]` items is treated as
    a header. If it is the only `uncommitted` candidate, the wrapper takes
    the P.v exit-0 nothing-to-commit path and does not invoke git-push."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md_raw(_stories_md_with_bodies(
            ("### Story H.m: Group overview [Done]", ""),
        ))
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert "Nothing to commit" in result.output
        assert "header" in result.output.lower()
        assert captured == []


def test_git_push_filters_header_alongside_real_story(runner, tmp_path, monkeypatch):
    """A header [Done] story alongside a single real uncommitted story →
    header is filtered, single-story flow proceeds with the real story."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md_raw(_stories_md_with_bodies(
            ("### Story H.m: Group overview [Done]", ""),
            ("### Story H.m.1: v0.10.0 Real work [Done]", "- [x] done"),
        ))
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert len(captured) == 1
        assert captured[0][1] == "H.m.1: v0.10.0 Real work"


def test_git_push_filters_header_then_bundles_real_stories(runner, tmp_path, monkeypatch):
    """A header [Done] alongside 2+ real uncommitted stories → bundle offer
    proposes only the real stories, not the header."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md_raw(_stories_md_with_bodies(
            ("### Story H.m: Group overview [Done]", ""),
            ("### Story H.m.1: v0.10.0 First child [Done]", "- [x] done"),
            ("### Story H.m.2: v0.11.0 Second child [Done]", "- [x] done"),
        ))
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='y\n')

        assert result.exit_code == 0, result.output
        # Header H.m must not appear in the bundle subject.
        assert "H.m," not in captured[0][1] and "H.m:" not in captured[0][1]
        assert captured[0][1] == (
            "H.m.1: v0.10.0, H.m.2: v0.11.0 First child + Second child"
        )


def test_git_push_field_bug_regression_header_plus_n1(runner, tmp_path, monkeypatch):
    """Regression for the real field bug: pre-P.v, the wrapper proposed
    `H.m, H.n.1: ...` as a bundle subject, even though H.m.1/H.m.2/H.m.3
    sat committed between them in document order. Post-P.v: H.m is filtered
    as a header; uncommitted reduces to just H.n.1; single-story flow."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md_raw(_stories_md_with_bodies(
            ("### Story H.m: Group overview [Done]", ""),
            ("### Story H.m.1: v0.10.0 First child [Done]", "- [x] done"),
            ("### Story H.m.2: v0.11.0 Second child [Done]", "- [x] done"),
            ("### Story H.m.3: v0.12.0 Third child [Done]", "- [x] done"),
            ("### Story H.n.1: v0.13.0 Sibling work [Done]", "- [x] done"),
        ))
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "H.m.1: v0.10.0 First child",
                "H.m.2: v0.11.0 Second child",
                "H.m.3: v0.12.0 Third child",
            ],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert len(captured) == 1
        assert captured[0][1] == "H.n.1: v0.13.0 Sibling work"


def test_git_push_out_of_sequence_single_offender(runner, tmp_path, monkeypatch):
    """Real (non-header) [Done] story uncommitted with later [Done] story
    committed → out-of-sequence error, exit 1, both stories named."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        # A.a uncommitted; A.b (later) committed.
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.b: v0.2.0 Second"],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 1
        assert "Out-of-sequence" in result.output
        assert "A.a" in result.output
        assert "A.b" in result.output
        assert captured == []


def test_git_push_out_of_sequence_multiple_offenders(runner, tmp_path, monkeypatch):
    """Two real uncommitted stories each with at least one committed story
    after them → error lists every offender + their later-committed
    context + the eligible-tail context if any."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First (uncommitted; offender) [Done]",
            "### Story A.b: v0.2.0 Second (committed) [Done]",
            "### Story A.c: v0.3.0 Third (uncommitted; offender) [Done]",
            "### Story A.d: v0.4.0 Fourth (committed) [Done]",
            "### Story A.e: v0.5.0 Fifth (uncommitted; eligible tail) [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "A.b: v0.2.0 Second (committed)",
                "A.d: v0.4.0 Fourth (committed)",
            ],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 1
        assert "Out-of-sequence" in result.output
        # Both offenders named.
        assert "A.a" in result.output
        assert "A.c" in result.output
        # Eligible-tail context names A.e.
        assert "A.e" in result.output
        assert captured == []


def test_git_push_out_of_sequence_fires_under_no_input(runner, tmp_path, monkeypatch):
    """Out-of-sequence is an unambiguous error path — --no-input does not
    auto-yes / auto-no it. Always exit 1, always emit the error block."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.b: v0.2.0 Second"],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push', '--no-input'])

        assert result.exit_code == 1
        assert "Out-of-sequence" in result.output
        assert captured == []


# --- Story Q.p: single out-of-sequence story opt-in commit ------------------


def test_git_push_single_out_of_sequence_accepted_invokes_gitbetter(runner, tmp_path, monkeypatch):
    """A single uncommitted [Done] story sitting out of sequence → the
    wrapper offers [y/N]; accepting derives the single-story message and
    invokes git-push (Story Q.p)."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        # A.a uncommitted; A.b (later) committed → A.a is the single offender.
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.b: v0.2.0 Second"],
            git_push_argv_capture=captured,
        )
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='y\n')

        assert result.exit_code == 0, result.output
        assert "Out-of-sequence" not in result.output
        assert len(captured) == 1
        assert captured[0][1] == "A.a: v0.1.0 First"


def test_git_push_single_out_of_sequence_declined_shows_error_block(runner, tmp_path, monkeypatch):
    """Declining the [y/N] opt-in falls through to the existing out-of-sequence
    error block and exit 1 (Story Q.p). The default is N, so empty input also
    declines."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.b: v0.2.0 Second"],
            git_push_argv_capture=captured,
        )
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        # Empty input → accepts the default (N) → declines.
        result = runner.invoke(main, ['git-push'], input='\n')

        assert result.exit_code == 1
        assert "Out-of-sequence" in result.output
        assert "A.a" in result.output
        assert "A.b" in result.output
        assert captured == []


def test_git_push_single_out_of_sequence_no_input_auto_declines(runner, tmp_path, monkeypatch):
    """--no-input never auto-yeses the out-of-sequence opt-in (Story Q.p):
    the single-offender case auto-declines to the error block, exit 1."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.b: v0.2.0 Second"],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push', '--no-input'])

        assert result.exit_code == 1
        assert "Out-of-sequence" in result.output
        assert captured == []


def test_git_push_multiple_out_of_sequence_offers_no_opt_in(runner, tmp_path, monkeypatch):
    """The single-story opt-in does NOT relax the multi-uncommitted case: with
    2+ uncommitted [Done] stories out of sequence, the wrapper errors without
    ever prompting, even when stdin would say yes (Story Q.p)."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First (uncommitted; offender) [Done]",
            "### Story A.b: v0.2.0 Second (committed) [Done]",
            "### Story A.c: v0.3.0 Third (uncommitted; offender) [Done]",
            "### Story A.d: v0.4.0 Fourth (committed) [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "A.b: v0.2.0 Second (committed)",
                "A.d: v0.4.0 Fourth (committed)",
            ],
            git_push_argv_capture=captured,
        )
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='y\n')

        assert result.exit_code == 1
        assert "Out-of-sequence" in result.output
        assert "Commit this single out-of-sequence story?" not in result.output
        assert captured == []


def test_git_push_nothing_to_commit_names_present_headers(runner, tmp_path, monkeypatch):
    """The exit-0 nothing-to-commit message names any [Done] header stories
    present (so the developer understands why the header isn't being
    proposed for commit)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md_raw(_stories_md_with_bodies(
            ("### Story H.m: Group overview [Done]", ""),
            ("### Story H.m.1: v0.10.0 Real work [Done]", "- [x] done"),
        ))
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["H.m.1: v0.10.0 Real work"],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0
        assert "Nothing to commit" in result.output
        # The H.m header is named in the parenthetical.
        assert "H.m" in result.output


def test_git_push_no_done_stories_still_exits_one(runner, tmp_path, monkeypatch):
    """The no-[Done]-headings-at-all path keeps its exit-1 stories.md-
    authoring-problem semantics; only the all-committed case became exit 0."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md_raw(
            "### Story A.a: v0.1.0 Hello World [Planned]\n\n- [ ] todo"
        )
        _mock_git_push_on_path(monkeypatch)

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 1
        assert "No completed story found" in result.output


# --- End Story P.v ----------------------------------------------------------


# --- Story Q.u: branch-aware git-push (squash-merge presumption) ------------


def test_git_push_nonmain_presumes_prefix_before_first_committed(runner, tmp_path, monkeypatch):
    """On a non-main branch, [Done] stories earlier in document order than the
    first branch-committed story are presumed squash-merged to main: the
    wrapper announces the anchor, skips the out-of-sequence error/prompt, and
    proceeds with the normal flow on the genuinely uncommitted tail."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
            "### Story A.c: v0.3.0 Third [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        # A.a was squashed into main under a PR-title subject → unparseable;
        # only A.b is recognizable in this branch's log.
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.b: v0.2.0 Second"],
            git_push_argv_capture=captured,
            branch="feature/x",
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert "first committed story in branch 'feature/x' is: A.b" in result.output
        assert "Out-of-sequence" not in result.output
        assert "Commit this single out-of-sequence story?" not in result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == "A.c: v0.3.0 Third"


def test_git_push_nonmain_no_story_commits_multiple_done_prompt_accept(runner, tmp_path, monkeypatch):
    """Non-main branch with zero recognizable story commits and multiple [Done]
    stories → 'Commit just the last one? [Y/n]' (default Y); accepting pushes
    only the last [Done] story."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
            "### Story A.c: v0.3.0 Third [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch, subjects=[], git_push_argv_capture=captured, branch="feature/x",
        )
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='\n')  # default Y

        assert result.exit_code == 0, result.output
        assert "Branch 'feature/x' has no story commits" in result.output
        assert "Commit just the last one?" in result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == "A.c: v0.3.0 Third"


def test_git_push_nonmain_no_story_commits_prompt_declined_falls_to_bundle(runner, tmp_path, monkeypatch):
    """Declining 'Commit just the last one?' falls through to the normal
    bundle offer over all uncommitted [Done] stories."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch, subjects=[], git_push_argv_capture=captured, branch="feature/x",
        )
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push'], input='n\ny\n')  # decline last-one, accept bundle

        assert result.exit_code == 0, result.output
        assert "Proposed bundled commit subject" in result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == "A.a: v0.1.0, A.b: v0.2.0 First + Second"


def test_git_push_nonmain_no_story_commits_no_input_auto_declines(runner, tmp_path, monkeypatch):
    """Under --no-input the 'Commit just the last one?' prompt is skipped
    (auto-decline) and the flow falls to the bundle offer, which also
    auto-declines → exit 1. CI never silently picks a story."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch, subjects=[], git_push_argv_capture=captured, branch="feature/x",
        )

        result = runner.invoke(main, ['git-push', '--no-input'])

        assert result.exit_code == 1
        assert "Commit just the last one?" not in result.output
        assert "Multiple uncommitted [Done] stories" in result.output
        assert captured == []


def test_git_push_nonmain_no_story_commits_single_done_no_prompt(runner, tmp_path, monkeypatch):
    """Non-main branch, empty log, exactly one [Done] story → normal
    single-story push with no 'Commit just the last one?' prompt."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch, subjects=[], git_push_argv_capture=captured, branch="feature/x",
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 0, result.output
        assert "Commit just the last one?" not in result.output
        assert captured[0][1] == "A.a: v0.1.0 Hello World"


def test_git_push_master_branch_keeps_out_of_sequence_discipline(runner, tmp_path, monkeypatch):
    """Literal `master` is treated like `main`: the full out-of-sequence
    detection (P.v/Q.p) remains in force."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First (uncommitted; offender) [Done]",
            "### Story A.b: v0.2.0 Second (committed) [Done]",
            "### Story A.c: v0.3.0 Third (uncommitted; offender) [Done]",
            "### Story A.d: v0.4.0 Fourth (committed) [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "A.b: v0.2.0 Second (committed)",
                "A.d: v0.4.0 Fourth (committed)",
            ],
            git_push_argv_capture=captured,
            branch="master",
        )

        result = runner.invoke(main, ['git-push', '--no-input'])

        assert result.exit_code == 1
        assert "Out-of-sequence" in result.output
        assert captured == []


def test_git_push_nonmain_duplicate_id_warning_still_fires(runner, tmp_path, monkeypatch):
    """The duplicate-story-ID warning stays active on non-main branches."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=[
                "A.a: v0.1.0 Hello World",
                "A.a: v0.1.1 Hello World patch",
            ],
            git_push_argv_capture=captured,
            branch="feature/x",
        )

        result = runner.invoke(main, ['git-push', '--no-input'])

        assert result.exit_code == 1
        assert "duplicate story ID" in result.output
        assert captured == []


# --- End Story Q.u ----------------------------------------------------------


# --- Story R.p: destination-aware branch gate --------------------------------
#
# Q.u built the right behavior and asked the wrong question. The gate read
# `_get_current_branch()` — where the developer is standing — when gitbetter's
# positional argument is what declares where the work is going. Kicking off a
# branch from a squash-merged `main` therefore hit the full strict discipline
# against a log that cannot contain the stories, and either hard-errored or
# proposed a commit subject covering the whole file.


def test_branch_argument_from_main_reaches_the_presumption_path(runner, tmp_path, monkeypatch):
    """The headline: naming a destination selects the relaxed path from `main`.

    Zero parseable story IDs is the squash-merged repo's steady state — every
    earlier story shipped under a PR title. Before this story the wrapper
    proposed one bundled subject spanning every [Done] story in the file.
    """
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
            "### Story A.c: v0.3.0 Third [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch, subjects=[], git_push_argv_capture=captured, branch="main",
        )
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-push', 'feature/x'], input='\n')  # default Y

        assert result.exit_code == 0, result.output
        assert "Commit just the last one?" in result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == "A.c: v0.3.0 Third"
        assert captured[0][2] == "feature/x"


def test_branch_argument_from_main_presumes_prefix_before_the_anchor(runner, tmp_path, monkeypatch):
    """The partial-anchor case: presumption, not a hard error.

    A.a squash-merged under a PR title while A.b kept its subject, so the
    strict gate saw an uncommitted story preceding a committed one — the
    out-of-sequence shape — and refused.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
            "### Story A.c: v0.3.0 Third [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.b: v0.2.0 Second"],
            git_push_argv_capture=captured,
            branch="main",
        )

        result = runner.invoke(main, ['git-push', 'feature/x'])

        assert result.exit_code == 0, result.output
        assert "Out-of-sequence" not in result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == "A.c: v0.3.0 Third"


def test_the_announcements_name_the_branch_that_was_scanned(runner, tmp_path, monkeypatch):
    """Boundary case 2: quote the log we read, not the branch we are heading for.

    The destination has no log yet — it may not exist at all — so naming it in
    "the first committed story in branch X" would assert something about a
    branch nobody looked at.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
            "### Story A.c: v0.3.0 Third [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.b: v0.2.0 Second"],
            git_push_argv_capture=[],
            branch="main",
        )

        result = runner.invoke(main, ['git-push', 'feature/x'])

        assert "first committed story in branch 'main' is: A.b" in result.output
        assert "branch 'feature/x' is" not in result.output


def test_naming_the_current_branch_is_not_branch_work(runner, tmp_path, monkeypatch):
    """Boundary case 1: `git-push main` while on `main` keeps the strict gate.

    Pushing the branch you are already on is ordinary work, not a kickoff, so
    the argument must not become a way to opt out of out-of-sequence detection.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
            "### Story A.c: v0.3.0 Third [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        # A.a uncommitted while A.c is committed — the out-of-sequence shape.
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.c: v0.3.0 Third"],
            git_push_argv_capture=captured,
            branch="main",
        )

        result = runner.invoke(main, ['git-push', 'main'])

        assert result.exit_code == 1
        assert "Out-of-sequence" in result.output
        assert captured == []


def test_a_same_named_branch_argument_off_main_still_relaxes(runner, tmp_path, monkeypatch):
    """The mirror of boundary case 1, which must NOT become strict.

    On `feature/x`, `git-push feature/x` is the ordinary push-this-branch
    invocation. It was relaxed before this story (non-main), and the
    equal-names rule must not accidentally tighten it.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
            "### Story A.c: v0.3.0 Third [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.b: v0.2.0 Second"],
            git_push_argv_capture=captured,
            branch="feature/x",
        )

        result = runner.invoke(main, ['git-push', 'feature/x'])

        assert result.exit_code == 0, result.output
        assert "Out-of-sequence" not in result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == "A.c: v0.3.0 Third"


def test_main_without_a_branch_argument_keeps_the_strict_gate(runner, tmp_path, monkeypatch):
    """The relaxation is reachable only by explicitly naming a destination."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
            "### Story A.c: v0.3.0 Third [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.c: v0.3.0 Third"],
            git_push_argv_capture=captured,
            branch="main",
        )

        result = runner.invoke(main, ['git-push'])

        assert result.exit_code == 1
        assert "Out-of-sequence" in result.output
        assert captured == []


def test_an_undeterminable_branch_keeps_the_strict_gate(runner, tmp_path, monkeypatch):
    """No current branch means no log to presume against, and no name to quote.

    Git absent, not a repo, or no commits yet: Q.u folded this into the strict
    side and it stays there. The relaxation's whole mechanism is "scan the
    branch we are on and presume around what it shows", which needs a branch.
    """
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
            "### Story A.c: v0.3.0 Third [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.c: v0.3.0 Third"],
            git_push_argv_capture=captured,
            branch="main",
        )
        monkeypatch.setattr(cli_module, "_get_current_branch", lambda: None)

        result = runner.invoke(main, ['git-push', 'feature/x'])

        assert result.exit_code == 1
        assert "Out-of-sequence" in result.output
        assert captured == []


def test_git_commit_gets_the_same_gate(runner, tmp_path, monkeypatch):
    """Both wrappers share `_run_gitbetter_wrapper`, so neither may drift."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        monkeypatch.setattr(
            cli_module.shutil, "which",
            lambda name: "/usr/local/bin/git-commit" if name == "git-commit" else None,
        )
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch, subjects=[], git_push_argv_capture=captured, branch="main",
        )
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-commit', 'feature/x'], input='\n')

        assert result.exit_code == 0, result.output
        assert "Commit just the last one?" in result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == "A.b: v0.2.0 Second"


# --- End Story R.p ------------------------------------------------------------


# --- Story R.q: gitbetter --keep / --amend pass-through -----------------------
#
# Both wrappers built `argv = [tool_path, message]` plus an optional branch, so
# two gitbetter flags were unreachable. `--keep` is a plain pass-through.
# `--amend` is a short-circuit, not a new branch through the derivation flow:
# no message is being decided, so the machinery that decides messages does not
# apply. What it does need is two guards.


def _mock_git(monkeypatch, *, subjects, branch="main", capture=None, last_subject=None):
    """Like `_mock_git_log_subjects`, but also answers `git log -1 --pretty=%s`.

    `last_subject=None` means "no previous commit" (non-zero exit), which is
    the state `--amend` has to report rather than hand to gitbetter.
    """
    import project_guide.cli as cli_module

    class _Completed:
        def __init__(self, returncode: int, stdout: str = ""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = ""

    def fake_run(argv, **kwargs):
        if argv[:2] == ["git", "log"] and "-1" in argv:
            if last_subject is None:
                return _Completed(128)
            return _Completed(0, stdout=last_subject + "\n")
        if argv[:2] == ["git", "log"]:
            return _Completed(0, stdout="\n".join(subjects) + ("\n" if subjects else ""))
        if argv[:2] == ["git", "rev-parse"]:
            return _Completed(0, stdout=branch + "\n")
        if capture is not None:
            capture.append(list(argv))
        return _Completed(0)

    monkeypatch.setattr(cli_module.subprocess, "run", fake_run)


def _interactive(monkeypatch):
    import project_guide.cli as cli_module

    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)


def test_keep_reaches_gitbetter(runner, tmp_path, monkeypatch):
    """A pass-through with no project-guide semantics attached."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md("### Story A.a: v0.1.0 First [Done]")
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git(monkeypatch, subjects=[], capture=captured)

        result = runner.invoke(main, ['git-push', '--keep'])

        assert result.exit_code == 0, result.output
        assert captured[0][1] == "A.a: v0.1.0 First"
        assert "--keep" in captured[0]


def test_keep_composes_with_a_branch_argument(runner, tmp_path, monkeypatch):
    """`--keep` is exactly the sustained-feature-branch flag, so the two must compose."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md("### Story A.a: v0.1.0 First [Done]")
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git(monkeypatch, subjects=[], capture=captured)

        result = runner.invoke(main, ['git-push', 'feature/x', '-k'])

        assert result.exit_code == 0, result.output
        argv = captured[0]
        assert argv[1] == "A.a: v0.1.0 First"
        assert argv[2] == "feature/x"
        assert "--keep" in argv


def test_amend_passes_the_previous_subject_back_verbatim(runner, tmp_path, monkeypatch):
    """Preserve, never re-derive.

    The stored title here has drifted from the commit's (a version was
    assigned after the fact). Re-deriving would silently rename the commit as
    a side effect of amending a fix into it.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md("### Story A.a: v0.1.0 First [Done]")
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git(
            monkeypatch,
            subjects=["A.a: First"],
            capture=captured,
            last_subject="A.a: First",
        )
        _interactive(monkeypatch)

        result = runner.invoke(main, ['git-push', '--amend'])

        assert result.exit_code == 0, result.output
        assert captured[0][1] == "A.a: First"  # not "A.a: v0.1.0 First"
        assert "--amend" in captured[0]


def test_amend_bypasses_the_nothing_to_commit_exit(runner, tmp_path, monkeypatch):
    """Already-committed is `--amend`'s precondition, not its blocker.

    Left to the normal flow the wrapper would exit 0 with "Nothing to commit"
    before ever invoking gitbetter, and `--amend` would appear to do nothing.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md("### Story A.a: v0.1.0 First [Done]")
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git(
            monkeypatch,
            subjects=["A.a: v0.1.0 First"],
            capture=captured,
            last_subject="A.a: v0.1.0 First",
        )
        _interactive(monkeypatch)

        result = runner.invoke(main, ['git-push', '--amend'])

        assert result.exit_code == 0, result.output
        assert "Nothing to commit" not in result.output
        assert len(captured) == 1, captured


def test_amend_is_refused_under_no_input(runner, tmp_path, monkeypatch):
    """It force-pushes with --force-with-lease; a history-shape decision is
    not a CI default. Same reasoning as the out-of-sequence path never
    auto-yesing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md("### Story A.a: v0.1.0 First [Done]")
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git(
            monkeypatch,
            subjects=["A.a: v0.1.0 First"],
            capture=captured,
            last_subject="A.a: v0.1.0 First",
        )

        result = runner.invoke(main, ['git-push', '--amend', '--no-input'])

        assert result.exit_code == 1
        assert "--amend" in result.output
        assert captured == []


def test_amend_is_refused_when_a_done_story_is_uncommitted(runner, tmp_path, monkeypatch):
    """The staging guard: gitbetter runs `git add -A` before amending.

    Finishing A.b in the tree and amending while the last commit is A.a lands
    A.b's diff inside A.a's commit under A.a's message — straight through the
    one-unit-of-work-one-commit invariant this wrapper exists to serve.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git(
            monkeypatch,
            subjects=["A.a: v0.1.0 First"],
            capture=captured,
            last_subject="A.a: v0.1.0 First",
        )
        _interactive(monkeypatch)

        result = runner.invoke(main, ['git-push', '--amend'])

        assert result.exit_code == 1
        assert "A.b" in result.output  # the offender is named
        assert captured == []


def test_the_staging_guard_ignores_planned_work(runner, tmp_path, monkeypatch):
    """Where the guard stops, deliberately.

    In-progress work on a `[Planned]` story is invisible to it and will still
    be folded in by `git add -A`. Amending stages your tree — that is git's
    contract — and the wrapper does not become a general working-tree guard.
    It intervenes where `stories.md` gives it standing, and nowhere else.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md_raw(
            "### Story A.a: v0.1.0 First [Done]\n\n- [x] done\n\n"
            "### Story A.b: Second [Planned]\n\n- [ ] todo"
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git(
            monkeypatch,
            subjects=["A.a: v0.1.0 First"],
            capture=captured,
            last_subject="A.a: v0.1.0 First",
        )
        _interactive(monkeypatch)

        result = runner.invoke(main, ['git-push', '--amend'])

        assert result.exit_code == 0, result.output
        assert len(captured) == 1, captured


def test_the_staging_guard_does_not_fire_on_squash_merged_history(runner, tmp_path, monkeypatch):
    """The guard must read the same committed-set the rest of the wrapper does.

    On a feature branch, earlier `[Done]` stories were squash-merged to main
    under PR titles and do not parse out of this branch's log. Their work *is*
    committed. Refusing here would make `--amend` unusable on exactly the
    workflow `--keep` and `--amend` exist for.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
            "### Story A.c: v0.3.0 Third [Done]",
        )
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        # Only A.c parses from this branch's log; A.a and A.b shipped via a
        # squashed PR and are unrecognizable.
        _mock_git(
            monkeypatch,
            subjects=["A.c: v0.3.0 Third"],
            branch="feature/x",
            capture=captured,
            last_subject="A.c: v0.3.0 Third",
        )
        _interactive(monkeypatch)

        result = runner.invoke(main, ['git-push', '--amend'])

        assert result.exit_code == 0, result.output
        assert len(captured) == 1, captured
        assert captured[0][1] == "A.c: v0.3.0 Third"


def test_amend_reports_no_previous_commit_clearly(runner, tmp_path, monkeypatch):
    """A fresh repo has nothing to amend; say so rather than let gitbetter fail."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md("### Story A.a: v0.1.0 First [Done]")
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git(monkeypatch, subjects=[], capture=captured, last_subject=None)
        _interactive(monkeypatch)

        result = runner.invoke(main, ['git-push', '--amend'])

        assert result.exit_code == 1
        assert "no previous commit" in result.output.lower()
        assert captured == []


def test_amend_tolerates_a_missing_stories_md(runner, tmp_path, monkeypatch):
    """`--amend` reads its message from git, so `stories.md` is only the guard's input.

    The normal flow exits 1 on a missing file because it cannot derive a
    message without one. The short-circuit can: the guard simply has nothing
    to check.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("docs/specs").mkdir(parents=True, exist_ok=True)
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git(monkeypatch, subjects=[], capture=captured, last_subject="wip")
        _interactive(monkeypatch)

        result = runner.invoke(main, ['git-push', '--amend'])

        assert result.exit_code == 0, result.output
        assert captured[0][1] == "wip"


def test_amend_composes_with_keep_and_a_branch(runner, tmp_path, monkeypatch):
    """All three reach gitbetter together, in a shape it parses."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md("### Story A.a: v0.1.0 First [Done]")
        _mock_git_push_on_path(monkeypatch)
        captured: list = []
        _mock_git(
            monkeypatch,
            subjects=["A.a: v0.1.0 First"],
            capture=captured,
            last_subject="A.a: v0.1.0 First",
        )
        _interactive(monkeypatch)

        result = runner.invoke(main, ['git-push', 'feature/x', '--amend', '--keep'])

        assert result.exit_code == 0, result.output
        argv = captured[0]
        assert argv[1] == "A.a: v0.1.0 First"
        assert argv[2] == "feature/x"
        assert "--amend" in argv and "--keep" in argv


@pytest.mark.parametrize("flags", [["--keep"], ["--amend"]])
def test_git_commit_gets_the_same_flags(runner, tmp_path, monkeypatch, flags):
    """Both wrappers share `_run_gitbetter_wrapper`; neither may drift."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md("### Story A.a: v0.1.0 First [Done]")
        monkeypatch.setattr(
            cli_module.shutil, "which",
            lambda name: "/usr/local/bin/git-commit" if name == "git-commit" else None,
        )
        captured: list = []
        _mock_git(
            monkeypatch,
            subjects=["A.a: v0.1.0 First"] if flags == ["--amend"] else [],
            capture=captured,
            last_subject="A.a: v0.1.0 First",
        )
        _interactive(monkeypatch)

        result = runner.invoke(main, ['git-commit', *flags])

        assert result.exit_code == 0, result.output
        assert captured[0][0] == "/usr/local/bin/git-commit"
        assert flags[0] in captured[0]


# --- End Story R.q ------------------------------------------------------------


# --- Story R.a: project-guide git-commit subcommand -------------------------


def _mock_git_commit_on_path(monkeypatch, path: str | None = "/usr/local/bin/git-commit"):
    """Patch `shutil.which("git-commit")` to return the given path (or None)."""
    import project_guide.cli as cli_module

    def fake_which(name):
        if name == "git-commit":
            return path
        return None  # other lookups don't matter for these tests

    monkeypatch.setattr(cli_module.shutil, "which", fake_which)


def test_git_commit_happy_path_invokes_gitbetter_with_derived_message(runner, tmp_path, monkeypatch):
    """Last [Done] story, not yet committed → git-commit called with derived message."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
        )
        _mock_git_commit_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-commit'])

        assert result.exit_code == 0, result.output
        assert len(captured) == 1, captured
        argv = captured[0]
        assert argv[0] == "/usr/local/bin/git-commit"
        assert argv[1] == "A.a: v0.1.0 Hello World"


def test_git_commit_passes_branch_name_through(runner, tmp_path, monkeypatch):
    """BRANCH_NAME positional appears as second argument to git-commit."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
        )
        _mock_git_commit_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-commit', 'feature/xyz'])

        assert result.exit_code == 0, result.output
        argv = captured[0]
        assert argv == ["/usr/local/bin/git-commit", "A.a: v0.1.0 Hello World", "feature/xyz"]


def test_git_commit_not_on_path_errors_with_install_hint(runner, tmp_path, monkeypatch):
    """git-commit missing from PATH → exit 1 naming the tool + gitbetter install hint."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
        )
        _mock_git_commit_on_path(monkeypatch, path=None)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-commit'])

        assert result.exit_code == 1
        assert "git-commit not found on PATH" in result.output
        assert "brew install pointmatic/tap/gitbetter" in result.output
        assert captured == []


def test_git_commit_no_done_stories_errors(runner, tmp_path, monkeypatch):
    """No [Done] story in stories.md → exit 1 (stories.md authoring problem)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Planned]",
        )
        _mock_git_commit_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-commit'])

        assert result.exit_code == 1
        assert "No completed story found" in result.output
        assert captured == []


def test_git_commit_nothing_to_commit_exits_zero(runner, tmp_path, monkeypatch):
    """Every real [Done] story already committed → exit 0, no git-commit invocation."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 Hello World [Done]",
        )
        _mock_git_commit_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.a: v0.1.0 Hello World"],
            git_push_argv_capture=captured,
        )

        result = runner.invoke(main, ['git-commit'])

        assert result.exit_code == 0, result.output
        assert "Nothing to commit" in result.output
        assert captured == []


def test_git_commit_bundle_offer_accepted_invokes_git_commit(runner, tmp_path, monkeypatch):
    """2+ uncommitted [Done] stories → bundled subject offered [Y/n]; accepting
    invokes git-commit with the bundled message."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 first [Done]",
            "### Story A.b: v0.2.0 second [Done]",
        )
        _mock_git_commit_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-commit'], input='y\n')

        assert result.exit_code == 0, result.output
        assert len(captured) == 1, captured
        assert captured[0][0] == "/usr/local/bin/git-commit"
        assert captured[0][1] == "A.a: v0.1.0, A.b: v0.2.0 first + second"


def test_git_commit_bundle_declined_under_no_input_names_git_commit(runner, tmp_path, monkeypatch):
    """--no-input auto-declines the bundle offer → exit 1; the manual-resolution
    hint names git-commit (not git-push)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 first [Done]",
            "### Story A.b: v0.2.0 second [Done]",
        )
        _mock_git_commit_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(monkeypatch, subjects=[], git_push_argv_capture=captured)

        result = runner.invoke(main, ['git-commit', '--no-input'])

        assert result.exit_code == 1
        assert "Multiple uncommitted [Done] stories" in result.output
        assert "'git-commit'" in result.output
        assert captured == []


def test_git_commit_single_out_of_sequence_accepted_invokes_gitbetter(runner, tmp_path, monkeypatch):
    """A single uncommitted [Done] story sitting out of sequence → the wrapper
    offers [y/N]; accepting derives the single-story message and invokes
    git-commit (mirrors the Q.p git-push flow)."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _write_stories_md(
            "### Story A.a: v0.1.0 First [Done]",
            "### Story A.b: v0.2.0 Second [Done]",
        )
        _mock_git_commit_on_path(monkeypatch)
        captured: list = []
        _mock_git_log_subjects(
            monkeypatch,
            subjects=["A.b: v0.2.0 Second"],
            git_push_argv_capture=captured,
        )
        monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

        result = runner.invoke(main, ['git-commit'], input='y\n')

        assert result.exit_code == 0, result.output
        assert "Out-of-sequence" not in result.output
        assert len(captured) == 1
        assert captured[0][0] == "/usr/local/bin/git-commit"
        assert captured[0][1] == "A.a: v0.1.0 First"


# --- End Story R.a ----------------------------------------------------------


# --- Story P.o: untracked-by-default go.md policy ---------------------------


def _git_init_repo() -> None:
    """Initialize a throwaway git repo in the cwd for the tracked-go.md tests."""
    import subprocess
    subprocess.run(["git", "init", "-q", "-b", "main"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Test"], check=True)


def test_init_emits_untracked_note_on_stderr(runner, tmp_path, prompt_tty):
    """init prints the 'intentionally untracked' note when stdin is interactive."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])

        assert result.exit_code == 0, result.output
        assert "is intentionally untracked" in result.output
        assert "Do not 'git add' it" in result.output


def test_init_quiet_suppresses_untracked_note(runner, tmp_path, prompt_tty):
    """`init --quiet` suppresses the 'intentionally untracked' note."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--quiet'])

        assert result.exit_code == 0
        assert "intentionally untracked" not in result.output


def test_init_no_input_suppresses_untracked_note(runner, tmp_path):
    """`init --no-input` suppresses the 'intentionally untracked' note (no prompt_tty)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init', '--no-input'])

        assert result.exit_code == 0, result.output
        assert "intentionally untracked" not in result.output


def test_heal_warns_when_go_md_is_tracked(runner, tmp_path, prompt_tty, monkeypatch):
    """In a git repo where go.md is in the index, heal warns with a copyable command."""
    # The recursion-guard env var is set autouse-globally by conftest to suppress
    # the auto-hook; it would also suppress the P.o warning. Clear it for tests
    # that exercise the warning path itself.
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _git_init_repo()
        _init_project(runner)

        import subprocess
        # Force-add go.md so it lands in the index regardless of the gitignore
        # block (which doesn't ignore go.md, but we want to be explicit).
        subprocess.run(
            ["git", "add", "-f", "docs/project-guide/go.md"], check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "seed"], check=True
        )

        result = runner.invoke(main, ['heal'])

        assert result.exit_code == 0, result.output
        assert "docs/project-guide/go.md is tracked" in result.output
        # The migration command must be copy-pasteable verbatim.
        assert (
            "`git rm --cached docs/project-guide/go.md && git commit`"
            in result.output
        )


def test_heal_silent_when_go_md_is_untracked(runner, tmp_path, prompt_tty, monkeypatch):
    """In a git repo where go.md is not in the index, heal is silent (no warning)."""
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _git_init_repo()
        _init_project(runner)
        # Leave go.md untracked — do not `git add` it.

        result = runner.invoke(main, ['heal'])

        assert result.exit_code == 0, result.output
        assert "is tracked" not in result.output


def test_heal_silent_when_not_in_git_repo(runner, tmp_path, prompt_tty, monkeypatch):
    """In a non-git directory, heal emits no warning and no errors."""
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        # No `git init` — the cwd is not a git work tree.

        result = runner.invoke(main, ['heal'])

        assert result.exit_code == 0, result.output
        assert "is tracked" not in result.output


def test_heal_suppresses_warning_under_no_input(runner, tmp_path, monkeypatch):
    """`PROJECT_GUIDE_NO_INPUT=1` suppresses the tracked-go.md warning."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _git_init_repo()
        _init_project(runner)

        import subprocess
        subprocess.run(
            ["git", "add", "-f", "docs/project-guide/go.md"], check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "seed"], check=True
        )

        monkeypatch.setenv("PROJECT_GUIDE_NO_INPUT", "1")
        result = runner.invoke(main, ['heal'])

        assert result.exit_code == 0, result.output
        assert "is tracked" not in result.output


# --- End Story P.o ----------------------------------------------------------


# --- Story P.s / P.u: commit-subject parser (single + bundle) ---------------
#
# P.s introduced the `Story <id>:` permissive form via a regex. P.u retired
# that regex in favor of `parse_committed_ids_from_subject` (lives in
# stories.py) which also handles bundled subjects. These four tests preserve
# the original P.s coverage; the comprehensive parser test suite lives in
# tests/test_stories.py.


def test_commit_subject_parser_matches_story_prefix_form():
    """Recognize the `Story <id>: ...` form (the docs-example convention)."""
    from project_guide.stories import parse_committed_ids_from_subject

    assert parse_committed_ids_from_subject(
        "Story J.m.2: v0.71.0 — 'QuizProvider' Protocol → 'AssessmentProvider'"
    ) == ["J.m.2"]


def test_commit_subject_parser_matches_bare_form():
    """Bare `<id>: ...` form continues to match (regression check for P.k/P.m)."""
    from project_guide.stories import parse_committed_ids_from_subject

    assert parse_committed_ids_from_subject(
        "J.m.2: v0.71.0 — Integrate Published Component"
    ) == ["J.m.2"]


def test_commit_subject_parser_matches_plain_letter_id_both_forms():
    """Both forms recognize plain-letter (non-sub-numbered) IDs."""
    from project_guide.stories import parse_committed_ids_from_subject

    assert parse_committed_ids_from_subject("A.a: v0.1.0 Hello World") == ["A.a"]
    assert parse_committed_ids_from_subject("Story A.a: v0.1.0 Hello World") == ["A.a"]


def test_commit_subject_parser_rejects_other_prefixes():
    """`Fix`/`Feat`/etc. prefixes are not absorbed by the optional `Story` group."""
    from project_guide.stories import parse_committed_ids_from_subject

    assert parse_committed_ids_from_subject("Fix J.m.2: something") == []
    assert parse_committed_ids_from_subject("Feat A.a: hello") == []
    # No colon → still no match (preserves the single-ID disambiguation rule).
    assert parse_committed_ids_from_subject("Story J.m.2 some other text") == []


# --- End Story P.s / P.u ----------------------------------------------------


# --- Story Q.m: pyve-managed-hosting awareness ------------------------------

def test_status_shows_pyve_footer_when_detected(runner, tmp_path):
    """status appends a dim 'Managed by pyve v<version>' footer when pyve cached.

    The footer reads the cached config value (no runtime re-detection) and
    extracts the bare version token from the raw `pyve --version` string.
    """
    import yaml
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        cfg = yaml.safe_load(Path('.project-guide.yml').read_text())
        cfg['pyve_version'] = 'pyve version 2.6.2'
        Path('.project-guide.yml').write_text(yaml.dump(cfg))

        result = runner.invoke(main, ['status'])
        assert result.exit_code == 0
        assert 'Managed by pyve v2.6.2 (detected at init time).' in result.output


def test_status_omits_pyve_footer_when_not_detected(runner, tmp_path):
    """status shows no pyve footer when pyve was not detected at init time."""
    import yaml
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        cfg = yaml.safe_load(Path('.project-guide.yml').read_text())
        cfg['pyve_version'] = None
        Path('.project-guide.yml').write_text(yaml.dump(cfg))

        result = runner.invoke(main, ['status'])
        assert result.exit_code == 0
        assert 'Managed by pyve' not in result.output


# --- End Story Q.m ----------------------------------------------------------


# --- Story Q.q: readiness-gated local-install warning -----------------------
#
# Q-4 makes _warn_if_local_install_under_pyve non-destructive: it consults
# `pyve self provision --status --json` and only advises `pip uninstall` on
# exit 0 (a runnable global replacement confirmed). Every other outcome is
# silent (exit 2) or readiness-first guidance (exit 1 / 127 / OSError / other).

def _fake_pyve_on_path(monkeypatch, cli_module, *, present=True):
    """Make `shutil.which("pyve")` resolve (or not) without touching real PATH."""
    real_which = cli_module.shutil.which

    def fake_which(name):
        if name == 'pyve':
            return '/usr/local/bin/pyve' if present else None
        return real_which(name)

    monkeypatch.setattr(cli_module.shutil, 'which', fake_which)


def _fake_site_packages_install(monkeypatch, cli_module):
    """Point _running_install_path at a pip-installed copy under cwd."""
    fake = Path.cwd() / '.venv/lib/python3.12/site-packages/project_guide'
    resolved = fake.resolve()
    monkeypatch.setattr(cli_module, '_running_install_path', lambda: resolved)
    return resolved


def test_warn_exit0_with_version_advises_removal(runner, tmp_path, monkeypatch):
    """exit 0 + parseable version → benign-duplicate notice naming the version."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (0, '2.15.0'))

        result = runner.invoke(main, ['status'])
        assert 'pyve-managed global project-guide (v2.15.0)' in result.output
        assert 'pip uninstall project-guide' in result.output


def test_warn_exit0_without_version_falls_back(runner, tmp_path, monkeypatch):
    """exit 0 with no parseable JSON version → version-less removal advice."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (0, None))

        result = runner.invoke(main, ['status'])
        assert 'A pyve-managed global project-guide is active' in result.output
        assert 'pip uninstall project-guide' in result.output
        assert '(v' not in result.output  # no version token leaked


def test_warn_exit2_is_silent(runner, tmp_path, monkeypatch):
    """exit 2 (not pyve-managed here) → no warning at all."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (2, None))

        result = runner.invoke(main, ['status'])
        assert 'pip uninstall' not in result.output
        assert "hosting isn't ready" not in result.output


@pytest.mark.parametrize('exit_code', [1, 127, None])
def test_warn_readiness_first_never_advises_removal(runner, tmp_path, monkeypatch, exit_code):
    """exit 1 / 127 / OSError(None) → readiness-first guidance, never removal."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (exit_code, None))

        result = runner.invoke(main, ['status'])
        assert "hosting isn't ready" in result.output
        assert 'pyve self provision' in result.output
        assert 'pip uninstall' not in result.output


def test_query_provision_status_handles_oserror(monkeypatch):
    """The status helper degrades to (None, None) when pyve cannot be launched."""
    import project_guide.cli as cli_module

    def raise_oserror(*a, **kw):
        raise OSError("no such binary")

    monkeypatch.setattr(cli_module.subprocess, 'run', raise_oserror)
    assert cli_module._query_pyve_provision_status('/usr/local/bin/pyve') == (None, None)


def test_query_provision_status_parses_version(monkeypatch):
    """exit 0 with a well-formed JSON payload yields the project_guide.version."""
    import project_guide.cli as cli_module

    class _Proc:
        returncode = 0
        stdout = '{"project_guide": {"version": "2.15.0"}}'

    monkeypatch.setattr(cli_module.subprocess, 'run', lambda *a, **kw: _Proc())
    assert cli_module._query_pyve_provision_status('/usr/local/bin/pyve') == (0, '2.15.0')


def test_query_provision_status_tolerates_bad_json(monkeypatch):
    """exit 0 with unparseable stdout yields (0, None), not a crash."""
    import project_guide.cli as cli_module

    class _Proc:
        returncode = 0
        stdout = 'not json at all'

    monkeypatch.setattr(cli_module.subprocess, 'run', lambda *a, **kw: _Proc())
    assert cli_module._query_pyve_provision_status('/usr/local/bin/pyve') == (0, None)


def test_query_provision_status_bounds_subprocess(monkeypatch):
    """The probe must pass a finite timeout and a closed stdin to subprocess.run.

    Regression test for the v2.15.0 hang: an older pyve that does not recognize
    ``self provision --status`` can fall into an interactive/blocking path. With
    no ``timeout`` the pre-invoke hook hangs every ``project-guide`` invocation;
    with an inherited stdin the hidden prompt blocks forever. Pin both guards.
    """
    import project_guide.cli as cli_module

    captured = {}

    class _Proc:
        returncode = 0
        stdout = '{"project_guide": {"version": "2.15.0"}}'

    def fake_run(*a, **kw):
        captured.update(kw)
        return _Proc()

    monkeypatch.setattr(cli_module.subprocess, 'run', fake_run)
    cli_module._query_pyve_provision_status('/usr/local/bin/pyve')

    assert captured.get('timeout'), "subprocess.run must be bounded by a finite timeout"
    assert captured.get('stdin') == cli_module.subprocess.DEVNULL, (
        "subprocess.run must close stdin so an interactive pyve fallback gets EOF"
    )


def test_query_provision_status_handles_timeout(monkeypatch):
    """A hung pyve probe degrades to (None, None), same as OSError."""
    import project_guide.cli as cli_module

    def raise_timeout(*a, **kw):
        raise cli_module.subprocess.TimeoutExpired(cmd=a[0], timeout=5)

    monkeypatch.setattr(cli_module.subprocess, 'run', raise_timeout)
    assert cli_module._query_pyve_provision_status('/usr/local/bin/pyve') == (None, None)


def test_warn_silent_when_pyve_absent(runner, tmp_path, monkeypatch):
    """pyve not on PATH → standalone usage, no warning (no status query run)."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module, present=False)
        _fake_site_packages_install(monkeypatch, cli_module)

        def fail(pyve):  # pragma: no cover - must not be called
            raise AssertionError("status query ran despite pyve absent")

        monkeypatch.setattr(cli_module, '_query_pyve_provision_status', fail)

        result = runner.invoke(main, ['status'])
        assert 'pip uninstall' not in result.output
        assert "hosting isn't ready" not in result.output


def test_warn_silent_on_editable_checkout(runner, tmp_path, monkeypatch):
    """No warning for an editable source checkout (no site-packages segment)."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        fake = (Path.cwd() / 'project_guide').resolve()
        monkeypatch.setattr(cli_module, '_running_install_path', lambda: fake)

        result = runner.invoke(main, ['status'])
        assert 'pip uninstall' not in result.output
        assert "hosting isn't ready" not in result.output


def test_warn_silent_when_not_under_cwd(runner, tmp_path, monkeypatch):
    """No warning when the running install is outside the project root."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        foreign = Path('/opt/foreign/lib/site-packages/project_guide')
        monkeypatch.setattr(cli_module, '_running_install_path', lambda: foreign)

        result = runner.invoke(main, ['status'])
        assert 'pip uninstall' not in result.output
        assert "hosting isn't ready" not in result.output


def test_warn_silent_under_skip_input(runner, tmp_path, monkeypatch):
    """should_skip_input() suppresses the warning entirely (preserved gate)."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    # Do not override should_skip_input — CliRunner's non-TTY stdin makes it True.

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (0, '2.15.0'))

        result = runner.invoke(main, ['status'])
        assert 'pip uninstall' not in result.output


def test_warn_detects_pyve_installed_after_init(runner, tmp_path, monkeypatch):
    """Live shutil.which gate engages even when init cached no pyve_version."""
    import yaml

    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        cfg = yaml.safe_load(Path('.project-guide.yml').read_text())
        cfg['pyve_version'] = None  # pyve was not present at init time
        Path('.project-guide.yml').write_text(yaml.dump(cfg))

        _fake_pyve_on_path(monkeypatch, cli_module)  # but it's on PATH now
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (0, '2.15.0'))

        result = runner.invoke(main, ['status'])
        assert 'pip uninstall project-guide' in result.output


def test_heal_offer_accepted_invokes_pyve_provision(runner, tmp_path, monkeypatch):
    """In the readiness-first branch, heal offers to provision and delegates on yes."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    recorded = []
    monkeypatch.setattr(cli_module, '_provision_pyve_hosting',
                        lambda pyve: recorded.append(pyve))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (1, None))

        result = runner.invoke(main, ['heal'], input='y\n')
        assert 'Provision pyve-managed project-guide now?' in result.output
        assert recorded == ['/usr/local/bin/pyve']


def test_heal_offer_declined_is_noop(runner, tmp_path, monkeypatch):
    """Declining the heal provisioning offer delegates nothing and advises no removal."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    recorded = []
    monkeypatch.setattr(cli_module, '_provision_pyve_hosting',
                        lambda pyve: recorded.append(pyve))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (1, None))

        result = runner.invoke(main, ['heal'], input='n\n')
        assert 'Provision pyve-managed project-guide now?' in result.output
        assert recorded == []
        assert 'pip uninstall' not in result.output


def test_heal_offer_suppressed_under_no_input(runner, tmp_path, monkeypatch):
    """--no-input never prompts to provision and never delegates."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)

    recorded = []
    monkeypatch.setattr(cli_module, '_provision_pyve_hosting',
                        lambda pyve: recorded.append(pyve))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (1, None))

        result = runner.invoke(main, ['heal', '--no-input'])
        assert 'Provision pyve-managed project-guide now?' not in result.output
        assert recorded == []


def test_auto_hook_never_prompts_to_provision(runner, tmp_path, monkeypatch):
    """The pre-invoke auto-hook emits readiness text but never the provision offer."""
    import project_guide.cli as cli_module
    monkeypatch.delenv('PROJECT_GUIDE_HEALING', raising=False)
    monkeypatch.setattr(cli_module, 'should_skip_input', lambda *a, **kw: False)

    recorded = []
    monkeypatch.setattr(cli_module, '_provision_pyve_hosting',
                        lambda pyve: recorded.append(pyve))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (1, None))

        result = runner.invoke(main, ['status'])
        assert "hosting isn't ready" in result.output
        assert 'Provision pyve-managed project-guide now?' not in result.output
        assert recorded == []


# --- End Story Q.q ----------------------------------------------------------


# --- Story Q.ac (v2.18.0) -----------------------------------------------------
# Pin the removal of the bump-version command. Version stamping is
# per-ecosystem (and increasingly Pyve's domain); project-guide no longer
# ships a Python-shaped mechanical version writer.


def test_bump_version_command_is_removed(runner, tmp_path):
    """`project-guide bump-version` is no longer a registered command."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['bump-version', '0.2.0'])
        assert result.exit_code == 2
        msg = (result.stderr or "") + (result.output or "")
        assert "No such command" in msg


def test_bump_version_absent_from_help(runner, tmp_path):
    """The top-level --help output no longer lists bump-version."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'bump-version' not in result.output


def test_bump_version_helpers_are_removed():
    """The bump-version helper functions and its private regex are gone."""
    import project_guide.cli as cli_module

    for name in (
        'bump_version',
        '_bump_pyproject_version',
        '_bump_version_file',
        '_bump_changelog',
        '_find_version_file',
        '_SEMVER_RE',
    ):
        assert not hasattr(cli_module, name), (
            f"project_guide.cli.{name} should have been removed with bump-version"
        )


# --- End Story Q.ac -----------------------------------------------------------


# --- Story R.h: heal stale-completion warning ---------------------------------
#
# Warn-don't-auto-fix, the same shape as the tracked-`go.md` and
# local-install-under-pyve warnings above. `heal` may say a rc file is broken;
# it may never write to one.


@pytest.fixture
def home_with_completion(tmp_path, monkeypatch):
    """Point `~` at a scratch directory and install completion into it.

    Returns a callable taking the binary to bake in, so a test can choose
    between a live path (current) and a dead one (stale).
    """
    from project_guide import completion as completion_module

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setenv("XDG_DATA_HOME", str(home / "xdg"))

    def install(shell: str, bin_path: str):
        script = completion_module.build_script(shell, bin_path)
        if shell == "zsh":
            autoload_dir = home / "xdg" / "project-guide" / "zsh-completions"
            completion_module.install_autoload_file(autoload_dir, script)
            body = completion_module.build_zsh_bootstrap(autoload_dir)
        else:
            body = script
        completion_module.install_block(
            completion_module.default_rc_path(shell),
            completion_module.build_block(body),
        )
        return home

    return install


def _live_binary(tmp_path) -> str:
    binary = tmp_path / "project-guide"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)
    return str(binary)


def test_heal_warns_when_completion_is_stale(
    runner, tmp_path, prompt_tty, monkeypatch, home_with_completion
):
    """The pyve toolchain-bump case: a baked path that no longer resolves.

    Both shells degrade silently in this state, so without a warning the user
    has no signal at all that completion stopped working.
    """
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    dead = str(tmp_path / "toolchain-3.12" / "project-guide")
    home_with_completion("bash", dead)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['heal'])

    assert result.exit_code == 0, result.output
    assert "stale" in result.stderr
    assert dead in result.stderr
    assert "project-guide completion install --shell bash" in result.stderr


def test_heal_warns_about_completion_exactly_once(
    runner, tmp_path, prompt_tty, monkeypatch, home_with_completion
):
    """The pre-invoke hook already runs before `heal`, so `heal` must not re-warn.

    The hook fires ahead of every subcommand, `heal` included. Calling the
    warning from both places — as the older sibling warnings do — prints it
    twice for the one command a user is most likely to run about it.
    """
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    home_with_completion("bash", str(tmp_path / "gone" / "project-guide"))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['heal'])

    assert result.stderr.count("completion is stale") == 1


def test_heal_completion_warning_goes_to_stderr_only(
    runner, tmp_path, prompt_tty, monkeypatch, home_with_completion
):
    """Diagnostics never pollute stdout — the rule `completion show` pinned."""
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    home_with_completion("bash", str(tmp_path / "gone" / "project-guide"))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['heal'])

    assert "stale" not in result.stdout


def test_heal_never_repairs_the_rc_file(
    runner, tmp_path, prompt_tty, monkeypatch, home_with_completion
):
    """Warn-don't-auto-fix: writing to a user's rc file unasked is out of bounds.

    Same constraint that bounds the `git-push` wrapper — project-guide reports,
    the user decides when to act.
    """
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    home = home_with_completion("bash", str(tmp_path / "gone" / "project-guide"))
    rc = home / ".bashrc"
    before = rc.read_text()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        runner.invoke(main, ['heal'])

    assert rc.read_text() == before
    assert not list(home.glob(".bashrc.bak.*"))


def test_heal_silent_when_completion_is_current(
    runner, tmp_path, prompt_tty, monkeypatch, home_with_completion
):
    """A working install is not drift."""
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    home_with_completion("bash", _live_binary(tmp_path))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['heal'])

    assert "completion" not in result.stderr.lower()


def test_heal_silent_when_completion_is_absent(
    runner, tmp_path, prompt_tty, monkeypatch
):
    """An uninstalled convenience is not drift either — R.f's rule, inherited."""
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setenv("XDG_DATA_HOME", str(home / "xdg"))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['heal'])

    assert "completion" not in result.stderr.lower()


def test_heal_warns_on_a_partial_zsh_install(
    runner, tmp_path, prompt_tty, monkeypatch, home_with_completion
):
    """A half-installed zsh pair is just as silently broken as a stale path."""
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    home = home_with_completion("zsh", _live_binary(tmp_path))
    (home / "xdg" / "project-guide" / "zsh-completions" / "_project-guide").unlink()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['heal'])

    assert "zsh" in result.stderr
    assert "project-guide completion install --shell zsh" in result.stderr


def test_heal_silent_on_a_damaged_block(
    runner, tmp_path, prompt_tty, monkeypatch, home_with_completion
):
    """`heal` has nothing useful to say about a block only a human can repair.

    Re-running `install` hits the same parse error, so nagging about it every
    invocation would be noise the user cannot act on from here.
    """
    from project_guide import completion as completion_module

    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    home = home_with_completion("bash", _live_binary(tmp_path))
    (home / ".bashrc").write_text(f"{completion_module.SENTINEL_START}\nhalf a block\n")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['heal'])

    assert result.exit_code == 0
    assert "completion" not in result.stderr.lower()


def test_completion_warning_is_silent_under_no_input(
    runner, tmp_path, monkeypatch, home_with_completion
):
    """Matches both sibling warnings: diagnostics for a human, not for CI.

    Completion is an interactive-shell convenience; a CI run has no shell to
    fix, so the warning would be pure log noise.
    """
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    home_with_completion("bash", str(tmp_path / "gone" / "project-guide"))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['heal', '--no-input'])

    assert "stale" not in result.stderr


def test_completion_warning_fires_from_the_pre_invoke_hook(
    runner, tmp_path, prompt_tty, monkeypatch, home_with_completion
):
    """It must catch a toolchain bump without the user thinking to run `heal`.

    Same split as the Q-4 local-install precedent: the *warning* fires from
    the hook, and only an interactive *offer* would be heal-scoped. There is
    no offer here — this is warn-only.
    """
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    home_with_completion("bash", str(tmp_path / "gone" / "project-guide"))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['status'])

    assert "stale" in result.stderr


def test_completion_warning_respects_the_recursion_guard(
    runner, tmp_path, prompt_tty, monkeypatch, home_with_completion
):
    """A nested project-guide invocation must not re-warn."""
    monkeypatch.setenv("PROJECT_GUIDE_HEALING", "1")
    home_with_completion("bash", str(tmp_path / "gone" / "project-guide"))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['heal'])

    assert "stale" not in result.stderr


def test_hook_steady_state_stays_silent_with_completion_installed(
    runner, tmp_path, prompt_tty, monkeypatch, home_with_completion
):
    """The auto-hook's defining property: a clean install says nothing at all."""
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    home_with_completion("bash", _live_binary(tmp_path))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['--version'])

    assert result.exit_code == 0
    assert result.stderr == ""


# --- End Story R.h ------------------------------------------------------------


# --- Story R.h.1: de-duplicate the pre-invoke warnings ------------------------
#
# Both older warnings were registered at two call sites — the pre-invoke hook
# and `heal` — so `project-guide heal` printed each of them twice. The fix must
# not cost the warnings their hook coverage, and must not cost `heal` its
# provisioning offer.


def test_go_md_warning_appears_once_during_heal(
    runner, tmp_path, prompt_tty, monkeypatch
):
    """`heal` printed this twice: once from the hook, once from its own call."""
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _git_init_repo()
        _init_project(runner)

        import subprocess
        subprocess.run(["git", "add", "-f", "docs/project-guide/go.md"], check=True)
        subprocess.run(["git", "commit", "-q", "-m", "seed"], check=True)

        result = runner.invoke(main, ['heal'])

    assert result.exit_code == 0, result.output
    assert result.output.count("docs/project-guide/go.md is tracked") == 1


def test_go_md_warning_still_fires_from_the_hook(
    runner, tmp_path, prompt_tty, monkeypatch
):
    """De-duplicating must not cost the warning its coverage of other commands."""
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _git_init_repo()
        _init_project(runner)

        import subprocess
        subprocess.run(["git", "add", "-f", "docs/project-guide/go.md"], check=True)
        subprocess.run(["git", "commit", "-q", "-m", "seed"], check=True)

        result = runner.invoke(main, ['status'])

    assert result.output.count("docs/project-guide/go.md is tracked") == 1


def test_local_install_warning_appears_once_during_heal(
    runner, tmp_path, prompt_tty, monkeypatch
):
    """Same duplication, but this call site cannot simply be deleted.

    `heal` passes `offer_provision=True`, and that offer is heal-scoped by a
    Subphase Q-4 invariant. Only the warning body may be suppressed.
    """
    import project_guide.cli as cli_module

    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (1, None))
        monkeypatch.setattr(cli_module, '_provision_pyve_hosting', lambda pyve: None)

        result = runner.invoke(main, ['heal'], input="n\n")

    assert result.output.count("hosting isn't ready") == 1


def test_heal_still_offers_provisioning_after_dedup(
    runner, tmp_path, prompt_tty, monkeypatch
):
    """The heal-scoped offer is the reason `heal`'s call cannot just be removed."""
    import project_guide.cli as cli_module

    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    provisioned = []
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (1, None))
        monkeypatch.setattr(cli_module, '_provision_pyve_hosting',
                            lambda pyve: provisioned.append(pyve))

        result = runner.invoke(main, ['heal'], input="y\n")

    assert "Provision pyve-managed project-guide now?" in result.output
    assert provisioned == ['/usr/local/bin/pyve']


def test_hook_alone_never_offers_provisioning(
    runner, tmp_path, prompt_tty, monkeypatch
):
    """The Q-4 invariant the dedup must not erode: the hook warns, never prompts."""
    import project_guide.cli as cli_module

    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (1, None))

        result = runner.invoke(main, ['status'])

    assert "hosting isn't ready" in result.output
    assert "Provision pyve-managed project-guide now?" not in result.output


def test_local_install_removal_advice_appears_once_during_heal(
    runner, tmp_path, prompt_tty, monkeypatch
):
    """The exit-0 branch duplicated too, and it carries the destructive advice."""
    import project_guide.cli as cli_module

    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ['init'])
        _fake_pyve_on_path(monkeypatch, cli_module)
        _fake_site_packages_install(monkeypatch, cli_module)
        monkeypatch.setattr(cli_module, '_query_pyve_provision_status',
                            lambda pyve: (0, '2.15.0'))

        result = runner.invoke(main, ['heal'])

    assert result.output.count("pip uninstall project-guide") == 1


def test_dedup_preserves_steady_state_silence(runner, tmp_path, prompt_tty, monkeypatch):
    """A clean install still says nothing at all."""
    monkeypatch.delenv("PROJECT_GUIDE_HEALING", raising=False)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_project(runner)
        result = runner.invoke(main, ['heal'])

    assert result.exit_code == 0
    assert result.output == ""


# --- End Story R.h.1 ----------------------------------------------------------


# --- Story R.k: host-supplied pyve version ------------------------------------
#
# pyve invokes `project-guide init` and knows its own version with certainty.
# Accepting it removes a guess — and a subprocess — from the one place the
# answer is not in doubt. Same shape as `--bin` in Subphase R-1: project-guide
# owns the rendering decision, the host tool supplies the fact it alone knows.


def _config_data(path=".project-guide.yml"):
    import yaml

    return yaml.safe_load(Path(path).read_text())


@pytest.fixture
def no_probe(monkeypatch):
    """Fail the test if the pyve probe runs.

    Skipping the subprocess is the point of the flag, not a side benefit, so
    it is asserted directly rather than inferred from the recorded version.
    """
    import project_guide.cli as cli_module

    def _boom():
        raise AssertionError("the pyve probe ran despite a host-supplied version")

    monkeypatch.setattr(cli_module, "_probe_pyve_version", _boom)


def test_pyve_version_flag_is_recorded_without_probing(runner, tmp_path, no_probe):
    """The flag wins outright and sets the render gate on."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init", "--pyve-version", "3.2.2"])

        assert result.exit_code == 0, result.output
        data = _config_data()

    assert data["pyve_version"] == "3.2.2"
    assert data["pyve_installed"] is True


def test_pyve_version_env_var_is_recorded_without_probing(runner, tmp_path, monkeypatch, no_probe):
    """The env-var equivalent, for hosts that would rather export than pass flags."""
    monkeypatch.setenv("PYVE_VERSION", "3.3.0")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init"]).exit_code == 0
        data = _config_data()

    assert data["pyve_version"] == "3.3.0"
    assert data["pyve_installed"] is True


def test_pyve_version_flag_beats_the_env_var(runner, tmp_path, monkeypatch, no_probe):
    """Resolution order matches `--project-name`: CLI flag → env var → probe."""
    monkeypatch.setenv("PYVE_VERSION", "from-env")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init", "--pyve-version", "from-flag"]).exit_code == 0
        data = _config_data()

    assert data["pyve_version"] == "from-flag"


def test_probe_runs_when_nothing_is_supplied(runner, tmp_path, monkeypatch):
    """The last link in the chain is the behavior that existed before this story."""
    import project_guide.cli as cli_module

    monkeypatch.delenv("PYVE_VERSION", raising=False)
    monkeypatch.setattr(cli_module, "_probe_pyve_version", lambda: "from-probe")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init"]).exit_code == 0
        data = _config_data()

    assert data["pyve_version"] == "from-probe"
    assert data["pyve_installed"] is True


def test_a_failed_probe_still_records_a_miss(runner, tmp_path, monkeypatch):
    """`init` remains the one site allowed to write `pyve_installed: false`."""
    import project_guide.cli as cli_module

    monkeypatch.delenv("PYVE_VERSION", raising=False)
    monkeypatch.setattr(cli_module, "_probe_pyve_version", lambda: None)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init"]).exit_code == 0
        data = _config_data()

    assert data["pyve_version"] is None
    assert data["pyve_installed"] is False


@pytest.mark.parametrize("supplied", ["", "   "])
def test_a_blank_flag_falls_through_to_the_next_link(runner, tmp_path, monkeypatch, supplied):
    """Blank is "not supplied", not "pyve version is the empty string".

    A host tool interpolating an unset shell variable produces exactly this,
    and treating it as an answer would record a useless version *and* skip the
    probe that would have found the real one.
    """
    import project_guide.cli as cli_module

    monkeypatch.delenv("PYVE_VERSION", raising=False)
    monkeypatch.setattr(cli_module, "_probe_pyve_version", lambda: "from-probe")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init", "--pyve-version", supplied]).exit_code == 0
        data = _config_data()

    assert data["pyve_version"] == "from-probe"


def test_a_blank_env_var_falls_through_to_the_probe(runner, tmp_path, monkeypatch):
    """Same reasoning for `PYVE_VERSION=` — an exported-but-empty variable."""
    import project_guide.cli as cli_module

    monkeypatch.setenv("PYVE_VERSION", "  ")
    monkeypatch.setattr(cli_module, "_probe_pyve_version", lambda: "from-probe")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init"]).exit_code == 0
        data = _config_data()

    assert data["pyve_version"] == "from-probe"


def test_a_supplied_version_is_stripped(runner, tmp_path, no_probe):
    """Surrounding whitespace is a transport artifact, not part of the value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init", "--pyve-version", "  3.2.2\n"]).exit_code == 0
        data = _config_data()

    assert data["pyve_version"] == "3.2.2"


def test_a_supplied_version_is_not_validated(runner, tmp_path, no_probe):
    """The field records an observation; it does not constrain one.

    Refusing a value the host asserts about *itself* would be project-guide
    second-guessing the one component that knows for certain. Story R.n
    *normalizes* the stored form — `pyve version 3.2.2-rc1` → `3.2.2-rc1` —
    which is not the same thing as validating it: nothing is rejected, and a
    value with no recognizable version token is stored exactly as given (see
    `test_the_normalizer_passes_through_what_it_cannot_parse`).
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init", "--pyve-version", "pyve version 3.2.2-rc1"])

        assert result.exit_code == 0
        assert _config_data()["pyve_version"] == "3.2.2-rc1"


def test_a_supplied_version_renders_the_pyve_guidance(runner, tmp_path, no_probe):
    """The end the flag exists for: guidance in `go.md` without a probe."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, ["init", "--pyve-version", "3.2.2"]).exit_code == 0
        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    assert "### Pyve Essentials" in content


@pytest.mark.parametrize("command", ["update", "mode"])
def test_pyve_version_flag_is_init_only(runner, tmp_path, command):
    """Later changes are handled by re-detection (R.l), not by more flags.

    A `--pyve-version` on `update` would invite a host tool to re-assert the
    fact on every invocation, which is the coupling the refresh sites remove.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ["init"])

        result = runner.invoke(main, [command, "--pyve-version", "3.2.2"])

    assert result.exit_code == 2
    assert "no such option" in result.output.lower()


# --- End Story R.k ------------------------------------------------------------


# --- Story R.l: re-detect on `update` and explicit `mode <name>` --------------
#
# `pyve_version` is a cache, so treat it as one. Refreshing it at two explicit,
# developer-initiated sites converts a permanent detection failure into a
# transient one — while the pre-invoke auto-hook stays subprocess-free, because
# a probe there is the Q.t (v2.15.1) hang class.


class _Probe:
    """A scriptable stand-in for the pyve probe that records its call count."""

    def __init__(self, *results):
        self._results = list(results)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self._results[min(self.calls - 1, len(self._results) - 1)]


def _install_probe(monkeypatch, *results):
    import project_guide.cli as cli_module

    probe = _Probe(*results)
    monkeypatch.setattr(cli_module, "_probe_pyve_version", probe)
    return probe


def _go_md() -> str:
    return Path("docs/project-guide/go.md").read_text(encoding="utf-8")


def _init_with_a_detection_miss(runner, monkeypatch):
    """The broken state this story repairs: pyve present, but init never saw it."""
    monkeypatch.delenv("PYVE_VERSION", raising=False)
    probe = _install_probe(monkeypatch, None)
    assert runner.invoke(main, ["init"]).exit_code == 0
    assert _config_data()["pyve_installed"] is False
    assert "### Pyve Essentials" not in _go_md()
    return probe


def test_update_refreshes_detection_and_restores_the_guidance(runner, tmp_path, monkeypatch):
    """The headline repair: pyve turns up later, and `update` puts the ~80 lines back."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_with_a_detection_miss(runner, monkeypatch)
        _install_probe(monkeypatch, "3.2.2")

        result = runner.invoke(main, ["update"])

        assert result.exit_code == 0, result.output
        data = _config_data()
        assert data["pyve_installed"] is True
        assert data["pyve_version"] == "3.2.2"
        assert "### Pyve Essentials" in _go_md()


def test_mode_switch_refreshes_detection_and_restores_the_guidance(runner, tmp_path, monkeypatch):
    """Same repair via the other sanctioned site — an explicit `mode <name>`."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_with_a_detection_miss(runner, monkeypatch)
        _install_probe(monkeypatch, "3.2.2")

        result = runner.invoke(main, ["mode", "code_direct"])

        assert result.exit_code == 0, result.output
        data = _config_data()
        assert data["pyve_installed"] is True
        assert data["pyve_version"] == "3.2.2"
        assert "### Pyve Essentials" in _go_md()


def test_update_re_renders_even_when_no_template_drifted(runner, tmp_path, monkeypatch):
    """The refresh has to *reach* `go.md`.

    `update` re-renders only when a template changed or `go.md` is missing.
    A freshly-initialised project satisfies neither, so without the detection
    result joining that condition the config would flip to `true` while the
    file on disk kept the guidance stripped — a fix visible only in YAML.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_with_a_detection_miss(runner, monkeypatch)
        _install_probe(monkeypatch, "3.2.2")

        result = runner.invoke(main, ["update"])

        assert result.exit_code == 0, result.output
        assert "Already current" in result.output  # nothing drifted...
        assert "### Pyve Essentials" in _go_md()  # ...and the section came back


def test_the_auto_hook_performs_no_pyve_subprocess(runner, tmp_path, monkeypatch, hook_enabled):
    """The Q.t guard, stated explicitly rather than left incidental.

    `_apply_heal` runs from the pre-invoke hook ahead of *every* command,
    `--help` and `--version` included. A pyve subprocess there is a probe
    before literally every invocation — the exact shape of the v2.15.1 hang.
    Both layers are guarded: the helper, and a re-implementation that reached
    for `subprocess.run` directly.
    """
    import subprocess as subprocess_module

    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_with_a_detection_miss(runner, monkeypatch)

        def _boom():
            raise AssertionError("the auto-hook probed for pyve")

        real_run = subprocess_module.run

        def _guarded_run(argv, *args, **kwargs):
            if list(argv)[:2] == ["pyve", "--version"]:
                raise AssertionError("the auto-hook shelled out to `pyve --version`")
            return real_run(argv, *args, **kwargs)

        monkeypatch.setattr(cli_module, "_probe_pyve_version", _boom)
        monkeypatch.setattr(cli_module.subprocess, "run", _guarded_run)

        Path("docs/project-guide/templates/modes/debug-mode.md").unlink()  # force a heal

        result = runner.invoke(main, ["--version"], input="y\n")

        assert result.exit_code == 0, result.output


def test_the_bare_mode_listing_performs_no_probe(runner, tmp_path, monkeypatch):
    """Only an explicit switch refreshes. Listing the modes renders nothing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_with_a_detection_miss(runner, monkeypatch)
        probe = _install_probe(monkeypatch, "3.2.2")

        assert runner.invoke(main, ["mode", "--no-input"]).exit_code == 0

        assert probe.calls == 0


def test_a_dry_run_update_neither_probes_nor_writes(runner, tmp_path, monkeypatch):
    """`--dry-run` promises to change nothing, and the config is a something."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_with_a_detection_miss(runner, monkeypatch)
        probe = _install_probe(monkeypatch, "3.2.2")

        assert runner.invoke(main, ["update", "--dry-run"]).exit_code == 0

        assert probe.calls == 0
        assert _config_data()["pyve_installed"] is False


@pytest.mark.parametrize("command", [["update"], ["mode", "code_direct"]])
def test_a_failed_refresh_leaves_the_cached_value_alone(runner, tmp_path, monkeypatch, command):
    """Sticky-true: a miss is never evidence of absence, only of a failed look."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _install_probe(monkeypatch, "3.2.2")
        assert runner.invoke(main, ["init"]).exit_code == 0

        _install_probe(monkeypatch, None)
        result = runner.invoke(main, command)

        assert result.exit_code == 0, result.output
        data = _config_data()
        assert data["pyve_installed"] is True
        assert data["pyve_version"] == "3.2.2"
        assert "### Pyve Essentials" in _go_md()


@pytest.mark.parametrize("command", [["update"], ["mode", "code_direct"]])
def test_a_failed_refresh_is_silent(runner, tmp_path, monkeypatch, command):
    """Absence is the steady state for non-pyve projects; warning about it is noise.

    The loud warning belongs to `init` (Story R.m) — a once-per-project event.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_with_a_detection_miss(runner, monkeypatch)
        _install_probe(monkeypatch, None)

        result = runner.invoke(main, command)

        assert result.exit_code == 0, result.output
        # Not a bare "pyve" search: `update` legitimately lists the
        # `pyve-essentials.md` artifact among the files it checked.
        assert "⚠" not in result.output
        assert "Warning" not in result.output
        assert "not found" not in result.output.lower()


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.TimeoutExpired(cmd=["pyve", "--version"], timeout=5),
        FileNotFoundError("pyve"),
        OSError("exec format error"),
    ],
    ids=["timeout", "not-found", "oserror"],
)
def test_a_broken_probe_does_not_fail_the_command(runner, tmp_path, monkeypatch, failure):
    """Q.t probe discipline, exercised through the real `_probe_pyve_version`.

    Bounded by a `timeout` and total across every exception class the call can
    raise: a refresh is an opportunistic improvement to a cached value, never a
    reason for the command it precedes to fail.
    """
    import project_guide.cli as cli_module

    real_probe = cli_module._probe_pyve_version

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_with_a_detection_miss(runner, monkeypatch)

        def _raise(*args, **kwargs):
            raise failure

        # The real probe, so the exception travels its actual `except` clause.
        monkeypatch.setattr(cli_module, "_probe_pyve_version", real_probe)
        monkeypatch.setattr(cli_module.subprocess, "run", _raise)

        result = runner.invoke(main, ["update"])

        assert result.exit_code == 0, result.output
        assert _config_data()["pyve_installed"] is False


def test_the_probe_is_bounded_by_a_timeout(runner, tmp_path, monkeypatch):
    """The bound itself, asserted rather than assumed — an unbounded probe hangs."""
    import project_guide.cli as cli_module

    seen = {}
    real_probe = cli_module._probe_pyve_version

    def _capture(argv, *args, **kwargs):
        seen.update(kwargs)
        raise FileNotFoundError("pyve")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_with_a_detection_miss(runner, monkeypatch)
        # Put the real probe back — the point here is the subprocess call it makes.
        monkeypatch.setattr(cli_module, "_probe_pyve_version", real_probe)
        monkeypatch.setattr(cli_module.subprocess, "run", _capture)

        assert runner.invoke(main, ["update"]).exit_code == 0

    assert seen.get("timeout") is not None


def test_a_successful_refresh_overrides_a_hand_edited_false(runner, tmp_path, monkeypatch):
    """The consequence of making detection reachable, pinned rather than discovered.

    Story R.j called turning the flag off "an explicit user action — hand-editing
    `.project-guide.yml`", and while nothing re-detected, that edit stood. Once
    `update` / `mode` refresh, a live detection sets it back on: at refresh time
    a hand-written `false` is byte-identical to the `false` a missed probe wrote
    at `init`, and repairing the latter is the whole point of this story.

    That leaves no durable opt-out while pyve is genuinely installed — the
    deliberate direction of the asymmetry, since irrelevant guidance is noise
    and missing guidance is a removed guardrail. A real `auto|always|never`
    opt-out is named out of scope in the subphase plan.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _install_probe(monkeypatch, "3.2.2")
        assert runner.invoke(main, ["init"]).exit_code == 0

        import yaml

        data = _config_data()
        data["pyve_installed"] = False
        Path(".project-guide.yml").write_text(yaml.dump(data))

        assert runner.invoke(main, ["update"]).exit_code == 0

        assert _config_data()["pyve_installed"] is True


def test_an_unchanged_refresh_does_not_rewrite_the_config(runner, tmp_path, monkeypatch):
    """Detecting what is already recorded is not a change; skip the write."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _install_probe(monkeypatch, "3.2.2")
        assert runner.invoke(main, ["init"]).exit_code == 0

        config = Config.load(".project-guide.yml")
        saves = []
        monkeypatch.setattr(
            Config, "save", lambda self, path=".project-guide.yml": saves.append(path)
        )

        cli_module._refresh_pyve_detection(config, Path(".project-guide.yml"))

    assert saves == []


def test_a_changed_refresh_persists_the_new_value(runner, tmp_path, monkeypatch):
    """The other half: a genuinely new observation is written back."""
    import project_guide.cli as cli_module

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _init_with_a_detection_miss(runner, monkeypatch)
        _install_probe(monkeypatch, "3.2.2")

        config = Config.load(".project-guide.yml")
        changed = cli_module._refresh_pyve_detection(config, Path(".project-guide.yml"))

        assert changed is True
        assert _config_data()["pyve_version"] == "3.2.2"


# --- End Story R.l ------------------------------------------------------------


# --- Story R.m: warn loudly on a detection miss at `init` ---------------------
#
# A silent `null` is indistinguishable from a deliberate non-pyve project, so
# the one failure that costs ~80 lines of guardrail is also the one that says
# nothing. This converts an invisible failure into a visible one — once, at
# `init`, where the miss actually happens.


def test_init_warns_when_detection_misses(runner, tmp_path, monkeypatch):
    """The headline: a miss is announced rather than silently recorded."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _install_probe(monkeypatch, None)

        result = runner.invoke(main, ["init"])

        assert result.exit_code == 0, result.output
        assert "pyve was not found" in result.stderr
        assert _config_data()["pyve_installed"] is False


def test_the_warning_names_what_was_lost_and_how_to_fix_it(runner, tmp_path, monkeypatch):
    """A warning that only says "not found" leaves the reader to guess the cost.

    Both halves are load-bearing: *what went missing* (the Pyve guidance is
    absent from the rendered guide, which is why the LLM will not be told to
    use `pyve test`) and *the remedy* (`update` re-detects since Story R.l).
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _install_probe(monkeypatch, None)

        result = runner.invoke(main, ["init"])

        assert "docs/project-guide/go.md" in result.stderr
        assert "project-guide update" in result.stderr


def test_init_is_silent_when_detection_succeeds(runner, tmp_path, monkeypatch):
    """Nothing to warn about — and the warning must not become a fixture."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _install_probe(monkeypatch, "3.2.2")

        result = runner.invoke(main, ["init"])

        assert result.exit_code == 0, result.output
        assert "pyve was not found" not in result.stderr


@pytest.mark.parametrize("supply", ["flag", "env"])
def test_no_warning_when_the_version_was_host_supplied(runner, tmp_path, monkeypatch, supply, no_probe):
    """No detection was attempted, so there is no detection miss to report.

    The `no_probe` fixture makes this structural rather than incidental: if the
    warning ever fires here it can only be because something probed.
    """
    args = ["init"]
    if supply == "flag":
        args += ["--pyve-version", "3.2.2"]
    else:
        monkeypatch.setenv("PYVE_VERSION", "3.2.2")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, args)

        assert result.exit_code == 0, result.output
        assert "pyve was not found" not in result.stderr


def test_a_blank_host_value_still_warns_when_the_probe_then_misses(runner, tmp_path, monkeypatch):
    """Blank means *not supplied* (R.k), so the probe ran and really did miss.

    The suppression follows whether a probe happened, not whether the flag was
    typed — otherwise a host interpolating an unset shell variable would
    silence the warning it most needs to see.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _install_probe(monkeypatch, None)

        result = runner.invoke(main, ["init", "--pyve-version", "   "])

        assert "pyve was not found" in result.stderr


def test_the_warning_survives_quiet(runner, tmp_path, monkeypatch):
    """Material warning per FR-9: `--quiet` silences stdout, never stderr."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _install_probe(monkeypatch, None)

        result = runner.invoke(main, ["init", "--quiet"])

        assert result.exit_code == 0, result.output
        assert result.stdout == ""
        assert "pyve was not found" in result.stderr


def test_the_warning_survives_no_input(runner, tmp_path, monkeypatch):
    """The embedded case is where a silent miss does the most damage.

    Unlike the P.o "intentionally untracked" *note*, this is a warning about
    content that will be missing from every render — a CI log or a host tool's
    output is exactly where it needs to appear.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _install_probe(monkeypatch, None)

        result = runner.invoke(main, ["init", "--no-input", "--quiet"])

        assert result.exit_code == 0, result.output
        assert "pyve was not found" in result.stderr


@pytest.mark.parametrize("command", [["update"], ["mode", "code_direct"]])
def test_a_refresh_miss_does_not_repeat_the_warning(runner, tmp_path, monkeypatch, command):
    """`init` only — a once-per-project event, not startup noise.

    Story R.l's refresh sites run on every `update` / `mode`; warning there
    would print this on every invocation for every project that does not use
    pyve, which is the fastest way to teach a developer to ignore it.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _install_probe(monkeypatch, None)
        assert runner.invoke(main, ["init"]).exit_code == 0

        result = runner.invoke(main, command)

        assert result.exit_code == 0, result.output
        assert "pyve was not found" not in result.stderr


def test_the_resolution_reports_whether_it_probed(runner, tmp_path, monkeypatch):
    """The suppression rule reads a fact the resolver knows, not a re-derivation.

    `init` cannot ask "was this host-supplied?" after the fact without
    re-walking the chain and drifting from it. The resolver returns it.
    """
    import project_guide.cli as cli_module

    monkeypatch.delenv("PYVE_VERSION", raising=False)
    _install_probe(monkeypatch, "from-probe")

    assert cli_module._resolve_pyve_version("3.2.2") == ("3.2.2", False)
    assert cli_module._resolve_pyve_version(None) == ("from-probe", True)

    _install_probe(monkeypatch, None)
    assert cli_module._resolve_pyve_version(None) == (None, True)


# --- End Story R.m ------------------------------------------------------------


# --- Story R.n: store a bare version string, read the legacy form ------------
#
# The field held the whole `pyve --version` line, so every display had to
# re-parse it. Normalize once at the two points a value enters the system —
# the probe and the host-supplied legs — and keep the reader tolerant, because
# `.project-guide.yml` files in the wild carry the raw form.


def _probe_returning(monkeypatch, stdout, returncode=0):
    """Drive the *real* `_probe_pyve_version` with a canned `pyve --version`."""
    import project_guide.cli as cli_module

    class _Completed:
        def __init__(self):
            self.stdout = stdout
            self.returncode = returncode

    monkeypatch.setattr(cli_module.subprocess, "run", lambda *a, **kw: _Completed())


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("pyve version 3.2.2", "3.2.2"),
        ("pyve 3.2.2", "3.2.2"),
        ("3.2.2", "3.2.2"),
        ("  pyve version 3.2.2  ", "3.2.2"),
        ("pyve version 3.2.2-rc1", "3.2.2-rc1"),
        ("pyve version v3.2.2", "3.2.2"),
    ],
    ids=["legacy", "short", "already-bare", "padded", "prerelease", "v-prefixed"],
)
def test_the_normalizer_extracts_the_version(raw, expected):
    """One function, applied on write and again on read. Total by construction."""
    from project_guide.cli import _normalize_pyve_version

    assert _normalize_pyve_version(raw) == expected


@pytest.mark.parametrize("unrecognizable", ["dev-build", "from source", "?"])
def test_the_normalizer_passes_through_what_it_cannot_parse(unrecognizable):
    """Normalizing is not validating (Story R.k).

    Nothing is rejected and nothing raises: a value with no recognizable
    version token is stored exactly as given. Refusing a value the host
    asserts about *itself* would be project-guide second-guessing the one
    component that knows for certain.
    """
    from project_guide.cli import _normalize_pyve_version

    assert _normalize_pyve_version(unrecognizable) == unrecognizable


def test_the_probe_stores_a_bare_version(runner, tmp_path, monkeypatch):
    """The probe's raw stdout is normalized before it ever reaches the config."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _probe_returning(monkeypatch, "pyve version 3.2.2\n")

        assert runner.invoke(main, ["init"]).exit_code == 0

        assert _config_data()["pyve_version"] == "3.2.2"


def test_a_failed_probe_still_records_nothing(runner, tmp_path, monkeypatch):
    """Normalization must not turn a non-zero exit into a stored value."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        _probe_returning(monkeypatch, "some error", returncode=1)

        assert runner.invoke(main, ["init"]).exit_code == 0

        assert _config_data()["pyve_version"] is None


@pytest.mark.parametrize("supply", ["flag", "env"])
def test_a_host_supplied_version_is_normalized_too(runner, tmp_path, monkeypatch, supply, no_probe):
    """Both write paths, or the field's format depends on who wrote it."""
    args = ["init"]
    if supply == "flag":
        args += ["--pyve-version", "pyve version 3.2.2"]
    else:
        monkeypatch.setenv("PYVE_VERSION", "pyve version 3.2.2")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert runner.invoke(main, args).exit_code == 0

        assert _config_data()["pyve_version"] == "3.2.2"


def test_a_refresh_repairs_a_legacy_stored_value(runner, tmp_path, monkeypatch):
    """Existing projects migrate themselves at the first Story R.l refresh.

    The stored legacy string and the freshly normalized one differ, so
    `record_pyve_detection` reports a change and writes the bare form — no
    migration step, and no `SCHEMA_VERSION` bump, required.
    """
    import yaml

    with runner.isolated_filesystem(temp_dir=tmp_path):
        monkeypatch.delenv("PYVE_VERSION", raising=False)
        # Both probes go through the real `_probe_pyve_version`, so the
        # normalization under test is the shipped one, not a stub's.
        _probe_returning(monkeypatch, "", returncode=1)
        assert runner.invoke(main, ["init"]).exit_code == 0

        data = _config_data()
        data["pyve_version"] = "pyve version 3.2.2"  # the form in the wild
        data["pyve_installed"] = True
        Path(".project-guide.yml").write_text(yaml.dump(data))

        _probe_returning(monkeypatch, "pyve version 3.2.2\n")
        assert runner.invoke(main, ["update"]).exit_code == 0

        assert _config_data()["pyve_version"] == "3.2.2"


@pytest.mark.parametrize(
    "stored",
    ["3.2.2", "pyve version 3.2.2"],
    ids=["bare", "legacy"],
)
def test_the_status_footer_renders_from_either_stored_form(runner, tmp_path, monkeypatch, stored):
    """The tolerant reader, which is why the normalizer survives on the read side.

    A config written before this story keeps the raw line until something
    refreshes it, and `status` is not a refresh site — so the footer has to
    cope with both forms indefinitely.
    """
    import yaml

    with runner.isolated_filesystem(temp_dir=tmp_path):
        _install_probe(monkeypatch, None)
        assert runner.invoke(main, ["init"]).exit_code == 0

        data = _config_data()
        data["pyve_version"] = stored
        Path(".project-guide.yml").write_text(yaml.dump(data))

        result = runner.invoke(main, ["status"])

        assert result.exit_code == 0, result.output
        assert "Managed by pyve v3.2.2 (detected at init time)." in result.output


# --- End Story R.n ------------------------------------------------------------
