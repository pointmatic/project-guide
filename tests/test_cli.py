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
    """init with successful pyve --version stores pyve_version in config."""
    import subprocess as sp

    import project_guide.cli as cli_module

    mock_result = sp.CompletedProcess(args=['pyve', '--version'], returncode=0, stdout="pyve 1.2.3\n", stderr="")
    monkeypatch.setattr(cli_module.subprocess, 'run', lambda *a, **kw: mock_result)

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0
        config = Config.load(".project-guide.yml")
        assert config.pyve_version == "pyve 1.2.3"


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


# --- Story O.p (v2.5.14) -----------------------------------------------------
# Pin the bump-version CLI command behavior:
#   - Writes the supplied version to pyproject.toml + auto-detected version
#     source file + CHANGELOG.md
#   - Validates semver format
#   - --no-input contract: missing positional fails loud, exit 2
#   - Idempotent on re-run for the same version


def _seed_minimal_python_project(project_dir: Path, project_name: str = "demo") -> None:
    """Write a minimal Python project layout with pyproject.toml, version
    source, and CHANGELOG.md — used by bump-version tests."""
    (project_dir / "pyproject.toml").write_text(
        f'[project]\nname = "{project_name}"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    pkg = project_dir / project_name.replace("-", "_")
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "version.py").write_text(
        '__version__ = "0.1.0"\n',
        encoding="utf-8",
    )
    (project_dir / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 2026-01-01\n\n"
        "### Added\n- Initial release.\n",
        encoding="utf-8",
    )


def test_bump_version_writes_three_files(runner, tmp_path):
    """bump-version updates pyproject.toml, version source, and CHANGELOG."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _seed_minimal_python_project(Path.cwd(), "demo")

        result = runner.invoke(main, ['bump-version', '0.2.0'])
        assert result.exit_code == 0, result.output

        # pyproject.toml updated
        assert 'version = "0.2.0"' in Path("pyproject.toml").read_text(encoding="utf-8")
        # version source updated
        assert '__version__ = "0.2.0"' in (
            Path("demo/version.py").read_text(encoding="utf-8")
        )
        # CHANGELOG inserted a new section just below ## [Unreleased]
        changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
        assert "## [0.2.0] -" in changelog
        # The new section appears before the older [0.1.0] section
        new_idx = changelog.find("## [0.2.0]")
        old_idx = changelog.find("## [0.1.0]")
        assert 0 < new_idx < old_idx
        # Success line on stdout
        assert "Bumped version to 0.2.0" in result.output


def test_bump_version_is_idempotent(runner, tmp_path):
    """Re-running bump-version with the same version updates the date but
    leaves pyproject.toml / version source unchanged on disk content (modulo
    the date refresh in CHANGELOG)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _seed_minimal_python_project(Path.cwd(), "demo")

        first = runner.invoke(main, ['bump-version', '0.2.0'])
        assert first.exit_code == 0
        second = runner.invoke(main, ['bump-version', '0.2.0'])
        assert second.exit_code == 0
        assert "updated date on existing ## [0.2.0]" in second.output


def test_bump_version_rejects_invalid_semver(runner, tmp_path):
    """A non-semver argument fails with exit 2 and a clear message."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _seed_minimal_python_project(Path.cwd(), "demo")

        result = runner.invoke(main, ['bump-version', 'v1.2.3'])
        assert result.exit_code == 2
        assert "not a valid semver" in (result.stderr or result.output)


def test_bump_version_no_input_contract(runner, tmp_path):
    """--no-input without a positional VERSION fails loud, exit 2.

    Per the M.b --no-input contract, commands must fail loudly when a
    required setting has no default under --no-input. bump-version's
    required setting is the version positional itself.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _seed_minimal_python_project(Path.cwd(), "demo")

        result = runner.invoke(main, ['bump-version', '--no-input'])
        assert result.exit_code == 2
        # The error message names the missing arg and the canonical fix.
        msg = (result.stderr or "") + (result.output or "")
        assert "VERSION argument" in msg
        assert "--no-input" in msg


def test_bump_version_quiet_suppresses_success_stdout(runner, tmp_path):
    """--quiet on a successful bump produces no stdout (warnings still go
    to stderr; errors fail loud regardless)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _seed_minimal_python_project(Path.cwd(), "demo")

        result = runner.invoke(main, ['bump-version', '0.2.0', '--quiet'])
        assert result.exit_code == 0
        # The success-line stdout is suppressed
        assert "Bumped version to" not in result.output


def test_bump_version_warns_when_no_version_file_found(runner, tmp_path):
    """When no __version__ source is auto-detectable, bump-version still
    succeeds (pyproject + CHANGELOG updated) but warns to stderr."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _seed_minimal_python_project(Path.cwd(), "demo")
        # Remove the version.py so auto-detect finds nothing.
        Path("demo/version.py").unlink()

        result = runner.invoke(main, ['bump-version', '0.2.0'])
        assert result.exit_code == 0
        msg = (result.stderr or "") + (result.output or "")
        assert "No __version__ source file auto-detected" in msg
        # pyproject was still updated
        assert 'version = "0.2.0"' in Path("pyproject.toml").read_text(encoding="utf-8")


# --- End Story O.p (CLI tests) -----------------------------------------------


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


# --- Story P.d / P.j: gitignore block inversion + tightening ----------------


_EXPECTED_GITIGNORE_BLOCK = (
    "# project-guide\n"
    "docs/project-guide/**\n"
    "!docs/project-guide/go.md\n"
)


def test_init_fresh_writes_inverted_gitignore_block(runner, tmp_path):
    """Fresh `init` writes the canonical 3-line track-only-go.md block."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])

        assert result.exit_code == 0, result.output
        gitignore = Path(".gitignore").read_text()
        assert _EXPECTED_GITIGNORE_BLOCK in gitignore


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
        assert _EXPECTED_GITIGNORE_BLOCK in gitignore
        # The dropped legacy line must not survive.
        assert "docs/project-guide/**/*.bak.*" not in gitignore
        # Surrounding content preserved.
        assert "*.pyc\n" in gitignore


def test_init_force_rewrites_v260_four_line_block_to_three_lines(runner, tmp_path):
    """`init --force` on a v2.6.0-shipped 4-line block tightens it to the v2.6.1 3-line form (Story P.j)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # v2.6.0 canonical form — the line P.j drops is still recognized,
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
        assert _EXPECTED_GITIGNORE_BLOCK in gitignore
        # The redundant v2.6.0 line must be gone.
        assert "docs/project-guide/**/*.bak.*" not in gitignore
        assert "*.pyc\n" in gitignore


def test_init_with_existing_canonical_block_is_idempotent(runner, tmp_path):
    """Running `init` over a project whose .gitignore is already canonical does not rewrite."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".gitignore").write_text("foo\n\n" + _EXPECTED_GITIGNORE_BLOCK)
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
            "docs/project-guide/local-only.md\n"  # foreign line
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
        assert _EXPECTED_GITIGNORE_BLOCK in gitignore


# --- End Story P.d / P.j ----------------------------------------------------
