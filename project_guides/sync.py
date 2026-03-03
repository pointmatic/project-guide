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
from typing import List, Tuple, Optional
import importlib.resources
import shutil
from datetime import datetime

from packaging.version import parse
from project_guides.version import __version__
from project_guides.config import Config
from project_guides.exceptions import GuideNotFoundError, SyncError


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
    
    raise GuideNotFoundError(guide_name, get_all_guide_names())


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


def copy_guide(guide_name: str, target_dir: Path, force: bool = False) -> None:
    """
    Copy a guide template to the target directory.
    
    Args:
        guide_name: Name of the guide to copy
        target_dir: Target directory path
        force: If True, overwrite existing files
    
    Raises:
        FileExistsError: If file exists and force is False
        SyncError: If copy operation fails
    """
    template_path = get_template_path(guide_name)
    target_file = target_dir / guide_name
    
    # Create subdirectories if needed
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise SyncError(f"Permission denied creating directory: {target_file.parent}")
    
    # Check if file exists
    if target_file.exists() and not force:
        raise FileExistsError(f"File already exists: {target_file}")
    
    # Copy the file
    try:
        shutil.copy2(template_path, target_file)
    except PermissionError:
        raise SyncError(f"Permission denied writing to: {target_file}")
    except OSError as e:
        raise SyncError(f"Failed to copy {guide_name}: {e}")


def backup_guide(guide_path: Path) -> Path:
    """Create a backup of a guide file."""
    guide_path = Path(guide_path)
    
    if not guide_path.exists():
        raise FileNotFoundError(f"Guide file not found: {guide_path}")
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = guide_path.with_suffix(f"{guide_path.suffix}.bak.{timestamp}")
    
    shutil.copy2(guide_path, backup_path)
    return backup_path


def compare_versions(installed: str, package: str) -> int:
    """
    Compare two version strings.
    
    Returns:
        -1 if installed < package
         0 if installed == package
         1 if installed > package
    """
    installed_ver = parse(installed)
    package_ver = parse(package)
    
    if installed_ver < package_ver:
        return -1
    elif installed_ver > package_ver:
        return 1
    else:
        return 0


def sync_guides(
    config: Config,
    guides: Optional[List[str]] = None,
    force: bool = False,
    dry_run: bool = False
) -> Tuple[List[str], List[str], List[str]]:
    """
    Sync guides to latest version.
    
    Args:
        config: Project configuration
        guides: List of specific guides to sync, or None for all guides
        force: If True, update even overridden guides (creates backups)
        dry_run: If True, show what would change without applying
    
    Returns:
        Tuple of (updated, skipped, current) guide name lists
    """
    updated = []
    skipped = []
    current = []
    
    # Get list of guides to sync
    if guides is None:
        guides_to_sync = get_all_guide_names()
    else:
        guides_to_sync = guides
    
    target_dir = Path(config.target_dir)
    package_version = get_package_version()
    
    for guide_name in guides_to_sync:
        target_file = target_dir / guide_name
        
        # Check if guide is overridden
        if config.is_overridden(guide_name) and not force:
            skipped.append(guide_name)
            continue
        
        # Check if guide exists and compare versions
        if target_file.exists():
            # If installed version equals package version, skip
            if config.installed_version and compare_versions(config.installed_version, package_version) == 0:
                current.append(guide_name)
                continue
        
        # Update the guide
        if not dry_run:
            # If overridden and force=True, create backup first
            if config.is_overridden(guide_name) and force and target_file.exists():
                backup_guide(target_file)
            
            # Copy the guide
            copy_guide(guide_name, target_dir, force=True)
        
        updated.append(guide_name)
    
    return (updated, skipped, current)
