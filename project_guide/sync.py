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
from project_guide.exceptions import ProjectFileNotFoundError, SyncError
from project_guide.version import __version__


def _get_package_template_root() -> Path:
    """Get the root path to bundled project-guide templates."""
    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath("project-guide")
    ) as path:
        return Path(path)


def get_template_path(file_name: str) -> Path:
    """Get path to bundled template for a tracked file."""
    root = _get_package_template_root()
    candidate = root / file_name
    if candidate.exists():
        return candidate
    raise ProjectFileNotFoundError(file_name, get_all_file_names())


_EXCLUDED_FROM_SYNC: set[str] = set()


def get_all_file_names() -> list[str]:
    """Get list of all tracked file names (excludes rendered artifacts).

    Always returns forward-slash paths for cross-platform consistency.
    """
    root = _get_package_template_root()
    file_names: set[str] = set()

    for pattern in ("*.md", "*.md.j2", "*.yml", ".*.yml"):
        for path in root.rglob(pattern):
            # Use forward slashes for cross-platform consistency
            rel = path.relative_to(root).as_posix()
            if rel not in _EXCLUDED_FROM_SYNC:
                file_names.add(rel)

    return sorted(file_names)


def get_package_version() -> str:
    """Get current package version."""
    return __version__


def copy_file(file_name: str, target_dir: Path, force: bool = False) -> None:
    """
    Copy a tracked file template to the target directory.

    Args:
        file_name: Name of the file to copy
        target_dir: Target directory path
        force: If True, overwrite existing files

    Raises:
        FileExistsError: If file exists and force is False
        SyncError: If copy operation fails
    """
    template_path = get_template_path(file_name)
    target_file = target_dir / file_name

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
        raise SyncError(f"Failed to copy {file_name}: {e}")


def backup_file(file_path: Path) -> Path:
    """Create a backup of a tracked file."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = file_path.with_suffix(f"{file_path.suffix}.bak.{timestamp}")

    shutil.copy2(file_path, backup_path)
    return backup_path


def file_matches_template(file_path: Path, file_name: str) -> bool:
    """
    Check if a file's content matches the bundled template.

    Args:
        file_path: Path to the file to check
        file_name: Name of the tracked file template to compare against

    Returns:
        True if file content matches template, False otherwise
    """
    if not file_path.exists():
        return False

    try:
        # Get template content
        template_path = get_template_path(file_name)
        with open(template_path, 'rb') as f:
            template_hash = hashlib.sha256(f.read()).hexdigest()

        # Get file content
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        return template_hash == file_hash
    except (OSError, ProjectFileNotFoundError):
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


def apply_file_update(file_name: str, config: Config, make_backup: bool = False) -> None:
    """
    Apply a single file update, optionally creating a backup first.

    Args:
        file_name: Name of the file to update
        config: Project configuration
        make_backup: If True, create a .bak backup before overwriting
    """
    target_dir = Path(config.target_dir)
    target_file = target_dir / file_name

    if make_backup and target_file.exists():
        backup_file(target_file)

    copy_file(file_name, target_dir, force=True)


def sync_files(
    config: Config,
    files: list[str] | None = None,
    force: bool = False,
    dry_run: bool = False
) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    """
    Sync tracked files to latest version using content hash comparison.

    Args:
        config: Project configuration
        files: List of specific files to sync, or None for all files
        force: If True, update even overridden/modified files (creates backups)
        dry_run: If True, show what would change without applying

    Returns:
        Tuple of (updated, skipped, current, missing, modified) file name lists
        - updated: Files that were updated (force mode only)
        - skipped: Files skipped due to override (unless force=True)
        - current: Files whose content matches the bundled template
        - missing: Files that don't exist and were/will be created
        - modified: Files whose content differs from the bundled template
                    These are NOT automatically updated; caller must handle them
    """
    updated = []
    skipped = []
    current = []
    missing = []
    modified = []

    # Get list of files to sync
    files_to_sync = get_all_file_names() if files is None else files

    target_dir = Path(config.target_dir)

    for file_name in files_to_sync:
        target_file = target_dir / file_name

        # Check if file is overridden
        if config.is_overridden(file_name) and not force:
            skipped.append(file_name)
            continue

        # Check if file exists
        if not target_file.exists():
            missing.append(file_name)
            if not dry_run:
                copy_file(file_name, target_dir, force=True)
            continue

        # File exists - use content hash to determine freshness
        if file_matches_template(target_file, file_name):
            current.append(file_name)
        elif force:
            # --force: backup and overwrite without prompting
            if not dry_run:
                apply_file_update(file_name, config, make_backup=True)
            updated.append(file_name)
        else:
            # Content differs - defer to caller to prompt
            modified.append(file_name)

    return (updated, skipped, current, missing, modified)
