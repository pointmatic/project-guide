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

from project_guide.config import Config
from project_guide.exceptions import ProjectFileNotFoundError
from project_guide.sync import (
    backup_file,
    compare_versions,
    copy_file,
    get_all_file_names,
    get_package_version,
    get_template_path,
    sync_files,
)
from project_guide.version import __version__


def test_get_template_path_returns_valid_paths():
    """Test that get_template_path returns valid paths for existing templates."""
    path = get_template_path("README.md")
    assert isinstance(path, Path)
    assert path.name == "README.md"

    path = get_template_path("templates/modes/plan-concept-mode.md")
    assert isinstance(path, Path)
    assert path.name == "plan-concept-mode.md"


def test_get_template_path_developer_file():
    """Test getting path to developer subdirectory file."""
    path = get_template_path("developer/codecov-setup-guide.md")
    assert isinstance(path, Path)
    assert path.name == "codecov-setup-guide.md"


def test_get_template_path_nonexistent():
    """Test that get_template_path raises error for non-existent templates."""
    with pytest.raises(ProjectFileNotFoundError, match="File 'nonexistent-file.md' not found"):
        get_template_path("nonexistent-file.md")


def test_get_all_file_names_returns_all_files():
    """Test that get_all_file_names returns all tracked files."""
    file_names = get_all_file_names()

    # Should be a list
    assert isinstance(file_names, list)

    # Should contain main files
    assert "README.md" in file_names
    assert "templates/modes/debug-mode.md" in file_names

    # Should contain mode templates
    assert "templates/modes/plan-concept-mode.md" in file_names
    assert "templates/modes/debug-mode.md" in file_names

    # Should contain developer files
    assert "developer/codecov-setup-guide.md" in file_names

    # Entry point template should be included (it's a source file, not a rendered artifact)
    assert "templates/go.md" in file_names

    # Should be sorted
    assert file_names == sorted(file_names)


def test_get_package_version_matches_version_py():
    """Test that get_package_version returns the correct version."""
    version = get_package_version()

    assert version == __version__


def test_copy_file_creates_files_correctly(tmp_path):
    """Test that copy_file creates files in the target directory."""
    target_dir = tmp_path / "project-guide"

    copy_file("README.md", target_dir)

    target_file = target_dir / "README.md"
    assert target_file.exists()
    assert target_file.is_file()
    assert target_file.stat().st_size > 0


def test_copy_file_creates_subdirectories(tmp_path):
    """Test that copy_file creates subdirectories for nested files."""
    target_dir = tmp_path / "project-guide"

    copy_file("developer/codecov-setup-guide.md", target_dir)

    target_file = target_dir / "developer" / "codecov-setup-guide.md"
    assert target_file.exists()
    assert target_file.is_file()


def test_copy_file_respects_force_flag(tmp_path):
    """Test that copy_file respects the force flag."""
    target_dir = tmp_path / "project-guide"

    # First copy should succeed
    copy_file("templates/modes/debug-mode.md", target_dir)

    # Second copy without force should fail
    with pytest.raises(FileExistsError, match="File already exists"):
        copy_file("templates/modes/debug-mode.md", target_dir, force=False)

    # Second copy with force should succeed
    copy_file("templates/modes/debug-mode.md", target_dir, force=True)

    target_file = target_dir / "templates/modes/debug-mode.md"
    assert target_file.exists()


def test_backup_file_creates_bak_files(tmp_path):
    """Test that backup_file creates .bak files with timestamp."""
    test_file = tmp_path / "test-file.md"
    test_file.write_text("Test content")

    backup_path = backup_file(test_file)

    assert backup_path.exists()
    assert ".bak." in backup_path.name
    assert backup_path.read_text() == "Test content"


def test_backup_file_nonexistent_file(tmp_path):
    """Test that backup_file raises error for non-existent file."""
    test_file = tmp_path / "nonexistent.md"

    with pytest.raises(FileNotFoundError, match="File not found"):
        backup_file(test_file)


def test_compare_versions_with_various_strings():
    """Test version comparison with various version strings."""
    # installed < package
    assert compare_versions("0.1.0", "0.2.0") == -1
    assert compare_versions("0.1.0", "1.0.0") == -1

    # installed == package
    assert compare_versions("0.2.0", "0.2.0") == 0
    assert compare_versions("1.0.0", "1.0.0") == 0

    # installed > package
    assert compare_versions("0.3.0", "0.2.0") == 1
    assert compare_versions("1.0.0", "0.9.9") == 1


def test_sync_files_with_no_overrides(tmp_path):
    """Test syncing files with no overrides."""
    config = Config(
        installed_version="0.5.0",
        target_dir=str(tmp_path / "project-guide")
    )

    # Sync a subset of files
    updated, skipped, current, missing, modified = sync_files(
        config,
        files=["README.md", "templates/modes/debug-mode.md"]
    )

    # Files don't exist, so they should be in missing list
    assert len(missing) == 2
    assert "README.md" in missing
    assert "templates/modes/debug-mode.md" in missing
    assert len(updated) == 0
    assert len(skipped) == 0
    assert len(current) == 0

    # Verify files were created
    assert (tmp_path / "project-guide" / "README.md").exists()
    assert (tmp_path / "project-guide" / "templates/modes/debug-mode.md").exists()


def test_sync_files_with_overrides_skipped(tmp_path):
    """Test that overridden files are skipped."""
    config = Config(
        installed_version="0.5.0",
        target_dir=str(tmp_path / "project-guide")
    )
    config.add_override("templates/modes/debug-mode.md", "Custom content", "0.5.0")

    updated, skipped, current, missing, modified = sync_files(
        config,
        files=["README.md", "templates/modes/debug-mode.md"]
    )

    assert len(updated) == 0
    assert len(skipped) == 1
    assert "templates/modes/debug-mode.md" in skipped
    assert len(missing) == 1
    assert "README.md" in missing
    assert len(current) == 0


def test_sync_files_with_force_flag(tmp_path):
    """Test that force flag updates modified overridden files."""
    target_dir = tmp_path / "project-guide"
    config = Config(
        installed_version="0.5.0",
        target_dir=str(target_dir)
    )

    # Create file, modify it, and mark as overridden
    copy_file("templates/modes/debug-mode.md", target_dir)
    (target_dir / "templates/modes/debug-mode.md").write_text("Custom content")
    config.add_override("templates/modes/debug-mode.md", "Custom content", "0.5.0")

    updated, skipped, current, missing, modified = sync_files(
        config,
        files=["templates/modes/debug-mode.md"],
        force=True
    )

    assert len(updated) == 1
    assert "templates/modes/debug-mode.md" in updated
    assert len(skipped) == 0

    # Verify backup was created
    backup_files = list((target_dir / "templates" / "modes").glob("debug-mode.md.bak.*"))
    assert len(backup_files) == 1


def test_sync_files_dry_run_mode(tmp_path):
    """Test that dry-run mode doesn't actually copy files."""
    config = Config(
        installed_version="0.5.0",
        target_dir=str(tmp_path / "project-guide")
    )

    updated, skipped, current, missing, modified = sync_files(
        config,
        files=["README.md"],
        dry_run=True
    )

    # File doesn't exist, so should be in missing list
    assert len(missing) == 1
    assert "README.md" in missing
    assert len(updated) == 0

    # Verify file was NOT created (dry-run mode)
    assert not (tmp_path / "project-guide" / "README.md").exists()


def test_sync_files_current_version(tmp_path):
    """Test that files at current version are not updated."""
    from project_guide.version import __version__

    target_dir = tmp_path / "project-guide"
    config = Config(
        installed_version=__version__,  # Same as current package version
        target_dir=str(target_dir)
    )

    # Create existing file
    copy_file("README.md", target_dir)

    updated, skipped, current, missing, modified = sync_files(
        config,
        files=["README.md"]
    )

    assert len(updated) == 0
    assert len(skipped) == 0
    assert len(current) == 1
    assert "README.md" in current
    assert len(missing) == 0


def test_sync_files_detects_missing_files(tmp_path):
    """Test that missing files are detected and created."""
    from project_guide.version import __version__

    target_dir = tmp_path / "project-guide"
    config = Config(
        installed_version=__version__,
        target_dir=str(target_dir)
    )

    # Don't create any files - they should be detected as missing
    updated, skipped, current, missing, modified = sync_files(
        config,
        files=["README.md", "templates/modes/debug-mode.md"]
    )

    assert len(missing) == 2
    assert "README.md" in missing
    assert "templates/modes/debug-mode.md" in missing
    assert len(updated) == 0
    assert len(current) == 0

    # Verify files were created
    assert (target_dir / "README.md").exists()
    assert (target_dir / "templates/modes/debug-mode.md").exists()


def test_sync_files_detects_user_modifications(tmp_path):
    """Test that user-modified files are detected."""
    from project_guide.version import __version__

    target_dir = tmp_path / "project-guide"
    config = Config(
        installed_version=__version__,
        target_dir=str(target_dir)
    )

    # Create file and modify it
    copy_file("README.md", target_dir)
    target_file = target_dir / "README.md"

    # Modify the file content
    with open(target_file, 'a') as f:
        f.write("\n# User added content\n")

    updated, skipped, current, missing, modified = sync_files(
        config,
        files=["README.md"]
    )

    # Modified file should be in modified list (awaiting user decision)
    assert len(modified) == 1
    assert "README.md" in modified
    assert len(updated) == 0
    assert len(current) == 0
    assert len(missing) == 0


def test_sync_files_force_overwrites_modified_with_backup(tmp_path):
    """Test that --force backs up and overwrites user-modified files."""
    from project_guide.version import __version__

    target_dir = tmp_path / "project-guide"
    config = Config(
        installed_version=__version__,
        target_dir=str(target_dir)
    )

    # Create file and modify it
    copy_file("README.md", target_dir)
    target_file = target_dir / "README.md"

    with open(target_file, 'a') as f:
        f.write("\n# User added content\n")

    updated, skipped, current, missing, modified = sync_files(
        config,
        files=["README.md"],
        force=True
    )

    # With --force, modified file should be backed up and updated
    assert len(updated) == 1
    assert "README.md" in updated
    assert len(modified) == 0

    # Verify a backup was created
    backup_files = list(target_dir.glob("README.md.bak.*"))
    assert len(backup_files) == 1


def test_file_matches_template_with_identical_content(tmp_path):
    """Test that file_matches_template returns True for identical content."""
    from project_guide.sync import file_matches_template

    target_dir = tmp_path / "project-guide"
    copy_file("README.md", target_dir)

    assert file_matches_template(target_dir / "README.md", "README.md")


def test_file_matches_template_with_modified_content(tmp_path):
    """Test that file_matches_template returns False for modified content."""
    from project_guide.sync import file_matches_template

    target_dir = tmp_path / "project-guide"
    copy_file("README.md", target_dir)

    # Modify the file
    target_file = target_dir / "README.md"
    with open(target_file, 'a') as f:
        f.write("\n# Modified\n")

    assert not file_matches_template(target_file, "README.md")


def test_file_matches_template_with_nonexistent_file(tmp_path):
    """Test that file_matches_template returns False for nonexistent files."""
    from project_guide.sync import file_matches_template

    nonexistent = tmp_path / "nonexistent.md"
    assert not file_matches_template(nonexistent, "README.md")
