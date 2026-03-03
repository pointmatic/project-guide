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

from project_guides.sync import get_template_path, get_all_guide_names, get_package_version
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
    assert version == "0.4.0"
