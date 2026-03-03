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
import time

import pytest

from project_guides.sync import (
    get_template_path,
    get_all_guide_names,
    get_package_version,
    copy_guide,
    backup_guide,
    compare_versions,
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
    """Test that get_template_path raises error for non-existent guide."""
    with pytest.raises(FileNotFoundError, match="Template not found"):
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
    assert version == "0.5.0"


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
    with pytest.raises(FileExistsError, match="Guide already exists"):
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
