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
from typing import List
import importlib.resources

from project_guides.version import __version__


def get_template_path(guide_name: str) -> Path:
    """Get path to bundled template for a guide."""
    # Use importlib.resources to access package data
    if importlib.resources.is_resource("project_guides.templates.guides", guide_name):
        # For files in the guides directory
        with importlib.resources.as_file(
            importlib.resources.files("project_guides.templates.guides").joinpath(guide_name)
        ) as path:
            return Path(path)
    elif "/" in guide_name or "\\" in guide_name:
        # For files in subdirectories like developer/
        parts = guide_name.replace("\\", "/").split("/")
        if len(parts) == 2 and parts[0] == "developer":
            with importlib.resources.as_file(
                importlib.resources.files("project_guides.templates.guides.developer").joinpath(parts[1])
            ) as path:
                return Path(path)
    
    raise FileNotFoundError(f"Template not found: {guide_name}")


def get_all_guide_names() -> List[str]:
    """Get list of all available guide names."""
    guide_names = []
    
    # Get files from main guides directory
    guides_files = importlib.resources.files("project_guides.templates.guides")
    for item in guides_files.iterdir():
        if item.is_file() and item.name.endswith(".md"):
            guide_names.append(item.name)
    
    # Get files from developer subdirectory
    try:
        developer_files = importlib.resources.files("project_guides.templates.guides.developer")
        for item in developer_files.iterdir():
            if item.is_file() and item.name.endswith(".md"):
                guide_names.append(f"developer/{item.name}")
    except (AttributeError, FileNotFoundError):
        pass
    
    return sorted(guide_names)


def get_package_version() -> str:
    """Get current package version."""
    return __version__
