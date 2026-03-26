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

from project_guides.config import Config
from project_guides.exceptions import GuideNotFoundError
from project_guides.sync import (
    backup_guide,
    compare_versions,
    copy_guide,
    get_all_guide_names,
    get_package_version,
    get_template_path,
    sync_guides,
)
from project_guides.version import __version__


def test_get_template_path_returns_valid_paths():
    """Test that get_template_path returns valid paths for existing templates."""
    # Test main guide
    path = get_template_path("project-guide.md")
    assert isinstance(path, Path)
    assert path.name == "project-guide.md"

    # Test another guide
    path = get_template_path("debug-guide.md")
    assert isinstance(path, Path)
    assert path.name == "debug-guide.md"


def test_get_template_path_developer_guide():
    """Test getting path to developer subdirectory guide."""
    path = get_template_path("developer/codecov-setup-guide.md")
    assert isinstance(path, Path)
    assert path.name == "codecov-setup-guide.md"


def test_get_template_path_nonexistent():
    """Test that get_template_path raises error for non-existent templates."""
    with pytest.raises(GuideNotFoundError, match="Guide 'nonexistent-guide.md' not found"):
        get_template_path("nonexistent-guide.md")


def test_get_all_guide_names_returns_all_guides():
    """Test that get_all_guide_names returns all available guides."""
    guide_names = get_all_guide_names()

    # Should be a list
    assert isinstance(guide_names, list)

    # Should contain main guides
    assert "project-guide.md" in guide_names
    assert "best-practices-guide.md" in guide_names
    assert "debug-guide.md" in guide_names
    assert "documentation-setup-guide.md" in guide_names

    # Should contain developer guides
    assert "developer/codecov-setup-guide.md" in guide_names
    assert "developer/production-mode.md" in guide_names

    # Should be sorted
    assert guide_names == sorted(guide_names)


def test_get_package_version_matches_version_py():
    """Test that get_package_version returns the correct version."""
    version = get_package_version()

    assert version == __version__


def test_copy_guide_creates_files_correctly(tmp_path):
    """Test that copy_guide creates files in the target directory."""
    target_dir = tmp_path / "guides"

    copy_guide("project-guide.md", target_dir)

    target_file = target_dir / "project-guide.md"
    assert target_file.exists()
    assert target_file.is_file()
    assert target_file.stat().st_size > 0


def test_copy_guide_creates_subdirectories(tmp_path):
    """Test that copy_guide creates subdirectories for developer guides."""
    target_dir = tmp_path / "guides"

    copy_guide("developer/codecov-setup-guide.md", target_dir)

    target_file = target_dir / "developer" / "codecov-setup-guide.md"
    assert target_file.exists()
    assert target_file.is_file()


def test_copy_guide_respects_force_flag(tmp_path):
    """Test that copy_guide respects the force flag."""
    target_dir = tmp_path / "guides"

    # First copy should succeed
    copy_guide("debug-guide.md", target_dir)

    # Second copy without force should fail
    with pytest.raises(FileExistsError, match="File already exists"):
        copy_guide("debug-guide.md", target_dir, force=False)

    # Second copy with force should succeed
    copy_guide("debug-guide.md", target_dir, force=True)

    target_file = target_dir / "debug-guide.md"
    assert target_file.exists()


def test_backup_guide_creates_bak_files(tmp_path):
    """Test that backup_guide creates .bak files with timestamp."""
    guide_file = tmp_path / "test-guide.md"
    guide_file.write_text("Test content")

    backup_path = backup_guide(guide_file)

    assert backup_path.exists()
    assert ".bak." in backup_path.name
    assert backup_path.read_text() == "Test content"


def test_backup_guide_nonexistent_file(tmp_path):
    """Test that backup_guide raises error for non-existent file."""
    guide_file = tmp_path / "nonexistent.md"

    with pytest.raises(FileNotFoundError, match="Guide file not found"):
        backup_guide(guide_file)


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


def test_sync_guides_with_no_overrides(tmp_path):
    """Test syncing guides with no overrides."""
    config = Config(
        installed_version="0.5.0",
        target_dir=str(tmp_path / "guides")
    )

    # Sync a subset of guides
    updated, skipped, current, missing, modified = sync_guides(
        config,
        guides=["project-guide.md", "debug-guide.md"]
    )

    # Files don't exist, so they should be in missing list
    assert len(missing) == 2
    assert "project-guide.md" in missing
    assert "debug-guide.md" in missing
    assert len(updated) == 0
    assert len(skipped) == 0
    assert len(current) == 0

    # Verify files were created
    assert (tmp_path / "guides" / "project-guide.md").exists()
    assert (tmp_path / "guides" / "debug-guide.md").exists()

    # Verify files were created
    assert (tmp_path / "guides" / "project-guide.md").exists()
    assert (tmp_path / "guides" / "debug-guide.md").exists()


def test_sync_guides_with_overrides_skipped(tmp_path):
    """Test that overridden guides are skipped."""
    config = Config(
        installed_version="0.5.0",
        target_dir=str(tmp_path / "guides")
    )
    config.add_override("debug-guide.md", "Custom content", "0.5.0")

    updated, skipped, current, missing, modified = sync_guides(
        config,
        guides=["project-guide.md", "debug-guide.md"]
    )

    assert len(updated) == 0
    assert len(skipped) == 1
    assert "debug-guide.md" in skipped
    assert len(missing) == 1
    assert "project-guide.md" in missing
    assert len(current) == 0


def test_sync_guides_with_force_flag(tmp_path):
    """Test that force flag updates overridden guides."""
    target_dir = tmp_path / "guides"
    config = Config(
        installed_version="0.5.0",
        target_dir=str(target_dir)
    )

    # Create an existing guide and mark it as overridden
    copy_guide("debug-guide.md", target_dir)
    config.add_override("debug-guide.md", "Custom content", "0.5.0")

    updated, skipped, current, missing, modified = sync_guides(
        config,
        guides=["debug-guide.md"],
        force=True
    )

    assert len(updated) == 1
    assert "debug-guide.md" in updated
    assert len(skipped) == 0

    # Verify backup was created
    backup_files = list(target_dir.glob("debug-guide.md.bak.*"))
    assert len(backup_files) == 1


def test_sync_guides_dry_run_mode(tmp_path):
    """Test that dry-run mode doesn't actually copy files."""
    config = Config(
        installed_version="0.5.0",
        target_dir=str(tmp_path / "guides")
    )

    updated, skipped, current, missing, modified = sync_guides(
        config,
        guides=["project-guide.md"],
        dry_run=True
    )

    # File doesn't exist, so should be in missing list
    assert len(missing) == 1
    assert "project-guide.md" in missing
    assert len(updated) == 0

    # Verify file was NOT created (dry-run mode)
    assert not (tmp_path / "guides" / "project-guide.md").exists()


def test_sync_guides_current_version(tmp_path):
    """Test that guides at current version are not updated."""
    from project_guides.version import __version__

    target_dir = tmp_path / "guides"
    config = Config(
        installed_version=__version__,  # Same as current package version
        target_dir=str(target_dir)
    )

    # Create existing guide
    copy_guide("project-guide.md", target_dir)

    updated, skipped, current, missing, modified = sync_guides(
        config,
        guides=["project-guide.md"]
    )

    assert len(updated) == 0
    assert len(skipped) == 0
    assert len(current) == 1
    assert "project-guide.md" in current
    assert len(missing) == 0


def test_sync_guides_detects_missing_files(tmp_path):
    """Test that missing files are detected and created."""
    from project_guides.version import __version__

    target_dir = tmp_path / "guides"
    config = Config(
        installed_version=__version__,
        target_dir=str(target_dir)
    )

    # Don't create any files - they should be detected as missing
    updated, skipped, current, missing, modified = sync_guides(
        config,
        guides=["project-guide.md", "debug-guide.md"]
    )

    assert len(missing) == 2
    assert "project-guide.md" in missing
    assert "debug-guide.md" in missing
    assert len(updated) == 0
    assert len(current) == 0

    # Verify files were created
    assert (target_dir / "project-guide.md").exists()
    assert (target_dir / "debug-guide.md").exists()


def test_sync_guides_detects_user_modifications(tmp_path):
    """Test that user-modified files are detected and updated."""
    from project_guides.version import __version__

    target_dir = tmp_path / "guides"
    config = Config(
        installed_version=__version__,
        target_dir=str(target_dir)
    )

    # Create guide and modify it
    copy_guide("project-guide.md", target_dir)
    guide_file = target_dir / "project-guide.md"

    # Modify the file content
    with open(guide_file, 'a') as f:
        f.write("\n# User added content\n")

    updated, skipped, current, missing, modified = sync_guides(
        config,
        guides=["project-guide.md"]
    )

    # Modified file should be in modified list (awaiting user decision)
    assert len(modified) == 1
    assert "project-guide.md" in modified
    assert len(updated) == 0
    assert len(current) == 0
    assert len(missing) == 0


def test_sync_guides_force_overwrites_modified_with_backup(tmp_path):
    """Test that --force backs up and overwrites user-modified files."""
    from project_guides.version import __version__

    target_dir = tmp_path / "guides"
    config = Config(
        installed_version=__version__,
        target_dir=str(target_dir)
    )

    # Create guide and modify it
    copy_guide("project-guide.md", target_dir)
    guide_file = target_dir / "project-guide.md"

    with open(guide_file, 'a') as f:
        f.write("\n# User added content\n")

    updated, skipped, current, missing, modified = sync_guides(
        config,
        guides=["project-guide.md"],
        force=True
    )

    # With --force, modified file should be backed up and updated
    assert len(updated) == 1
    assert "project-guide.md" in updated
    assert len(modified) == 0

    # Verify a backup was created
    backup_files = list(target_dir.glob("project-guide.md.bak.*"))
    assert len(backup_files) == 1


def test_file_matches_template_with_identical_content(tmp_path):
    """Test that file_matches_template returns True for identical content."""
    from project_guides.sync import file_matches_template

    target_dir = tmp_path / "guides"
    copy_guide("project-guide.md", target_dir)

    assert file_matches_template(target_dir / "project-guide.md", "project-guide.md")


def test_file_matches_template_with_modified_content(tmp_path):
    """Test that file_matches_template returns False for modified content."""
    from project_guides.sync import file_matches_template

    target_dir = tmp_path / "guides"
    copy_guide("project-guide.md", target_dir)

    # Modify the file
    guide_file = target_dir / "project-guide.md"
    with open(guide_file, 'a') as f:
        f.write("\n# Modified\n")

    assert not file_matches_template(guide_file, "project-guide.md")


def test_file_matches_template_with_nonexistent_file(tmp_path):
    """Test that file_matches_template returns False for nonexistent files."""
    from project_guides.sync import file_matches_template

    nonexistent = tmp_path / "nonexistent.md"
    assert not file_matches_template(nonexistent, "project-guide.md")
