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

import hashlib
import importlib.resources
import shutil
from datetime import datetime
from pathlib import Path

from packaging.version import parse

from project_guide.config import Config
from project_guide.exceptions import GuideNotFoundError, SyncError
from project_guide.version import __version__


def _get_package_template_root() -> Path:
    """Get the root path to bundled project-guide templates."""
    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath("project-guide")
    ) as path:
        return Path(path)


def get_template_path(guide_name: str) -> Path:
    """Get path to bundled template for a guide."""
    root = _get_package_template_root()
    candidate = root / guide_name
    if candidate.exists():
        return candidate
    raise GuideNotFoundError(guide_name, get_all_guide_names())


_EXCLUDED_FROM_SYNC: set[str] = set()


def get_all_guide_names() -> list[str]:
    """Get list of all available guide names (excludes rendered artifacts).

    Always returns forward-slash paths for cross-platform consistency.
    """
    root = _get_package_template_root()
    guide_names = []

    for pattern in ("*.md", "*.md.j2", "*.yml", ".*.yml"):
        for path in sorted(root.rglob(pattern)):
            # Use forward slashes for cross-platform consistency
            rel = path.relative_to(root).as_posix()
            if rel not in _EXCLUDED_FROM_SYNC:
                guide_names.append(rel)

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


def file_matches_template(file_path: Path, guide_name: str) -> bool:
    """
    Check if a file's content matches the bundled template.

    Args:
        file_path: Path to the file to check
        guide_name: Name of the guide template to compare against

    Returns:
        True if file content matches template, False otherwise
    """
    if not file_path.exists():
        return False

    try:
        # Get template content
        template_path = get_template_path(guide_name)
        with open(template_path, 'rb') as f:
            template_hash = hashlib.sha256(f.read()).hexdigest()

        # Get file content
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        return template_hash == file_hash
    except (OSError, GuideNotFoundError):
        return False


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


def apply_guide_update(guide_name: str, config: Config, make_backup: bool = False) -> None:
    """
    Apply a single guide update, optionally creating a backup first.

    Args:
        guide_name: Name of the guide to update
        config: Project configuration
        make_backup: If True, create a .bak backup before overwriting
    """
    target_dir = Path(config.target_dir)
    target_file = target_dir / guide_name

    if make_backup and target_file.exists():
        backup_guide(target_file)

    copy_guide(guide_name, target_dir, force=True)


def sync_guides(
    config: Config,
    guides: list[str] | None = None,
    force: bool = False,
    dry_run: bool = False
) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    """
    Sync guides to latest version.

    Args:
        config: Project configuration
        guides: List of specific guides to sync, or None for all guides
        force: If True, update even overridden guides (creates backups)
        dry_run: If True, show what would change without applying

    Returns:
        Tuple of (updated, skipped, current, missing, modified) guide name lists
        - updated: Guides that were/will be updated (outdated version)
        - skipped: Guides skipped due to override (unless force=True)
        - current: Guides that match template and are up-to-date
        - missing: Guides that don't exist and were/will be created
        - modified: Guides with user edits detected (version current but content differs)
                    These are NOT automatically updated; caller must handle them
    """
    updated = []
    skipped = []
    current = []
    missing = []
    modified = []

    # Get list of guides to sync
    guides_to_sync = get_all_guide_names() if guides is None else guides

    target_dir = Path(config.target_dir)
    package_version = get_package_version()

    for guide_name in guides_to_sync:
        target_file = target_dir / guide_name

        # Check if guide is overridden
        if config.is_overridden(guide_name) and not force:
            skipped.append(guide_name)
            continue

        # Check if file exists
        if not target_file.exists():
            # File is missing - always needs to be created
            missing.append(guide_name)
            if not dry_run:
                copy_guide(guide_name, target_dir, force=True)
            continue

        # File exists - check version and content
        if config.installed_version and compare_versions(config.installed_version, package_version) == 0:
            # Version is current - check if content matches template
            if file_matches_template(target_file, guide_name):
                # File matches template exactly - mark as current
                current.append(guide_name)
                continue
            else:
                # User has modified this file - report for caller to handle
                if force:
                    # --force: backup and overwrite without prompting
                    if not dry_run:
                        apply_guide_update(guide_name, config, make_backup=True)
                    updated.append(guide_name)
                else:
                    # No --force: defer to caller to prompt
                    modified.append(guide_name)
                continue

        # Outdated version - update unconditionally
        if not dry_run:
            if config.is_overridden(guide_name) and force:
                backup_guide(target_file)
            copy_guide(guide_name, target_dir, force=True)

        updated.append(guide_name)

    return (updated, skipped, current, missing, modified)
