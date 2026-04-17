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

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml
from packaging.version import InvalidVersion, Version

from project_guide.exceptions import ConfigError, SchemaVersionError

SCHEMA_VERSION = "2.0"


def _check_schema_version(version_str: str) -> None:
    """Validate the config file's schema version against SCHEMA_VERSION.

    Raises SchemaVersionError when the loaded schema is older or newer than
    this package supports. Additive field changes do not bump SCHEMA_VERSION;
    only rename/remove/retype/semantic changes do.
    """
    try:
        found = Version(version_str)
        current = Version(SCHEMA_VERSION)
    except InvalidVersion:
        raise SchemaVersionError(
            f"Unrecognized config schema version {version_str!r}. "
            f"Expected {SCHEMA_VERSION!r}. "
            "Run 'project-guide update' to back up the stale config and refresh via 'init --force'.",
            direction="older",
        )
    if found < current:
        raise SchemaVersionError(
            f"Config schema {version_str!r} is older than this package's schema {SCHEMA_VERSION!r}. "
            "Run 'project-guide update' to back up the stale config and refresh via 'init --force'.",
            direction="older",
        )
    if found > current:
        raise SchemaVersionError(
            f"Config schema {version_str!r} is newer than this package's schema {SCHEMA_VERSION!r}. "
            "Upgrade project-guide to a version that supports this config.",
            direction="newer",
        )


@dataclass
class FileOverride:
    """Represents an overridden file."""
    reason: str
    locked_version: str
    last_updated: date

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "reason": self.reason,
            "locked_version": self.locked_version,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileOverride":
        """Create from dictionary loaded from YAML."""
        return cls(
            reason=data["reason"],
            locked_version=data["locked_version"],
            last_updated=date.fromisoformat(data["last_updated"]),
        )


@dataclass
class Config:
    """Project configuration for project-guide."""
    version: str = "2.0"
    installed_version: str = ""
    target_dir: str = "docs/project-guide"
    metadata_file: str = ".metadata.yml"
    current_mode: str = "default"
    test_first: bool = False
    pyve_version: str | None = None
    project_name: str = ""
    metadata_overrides: dict[str, dict] = field(default_factory=dict)
    overrides: dict[str, FileOverride] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str = ".project-guide.yml") -> "Config":
        """Load configuration from YAML file."""
        config_path = Path(path)

        if not config_path.exists():
            raise ConfigError(
                f"Configuration file not found: {config_path}\n"
                "Run 'project-guide init' to create it."
            )

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {config_path}: {e}")
        except PermissionError:
            raise ConfigError(f"Permission denied reading {config_path}")

        if not data:
            raise ConfigError(f"Empty configuration file: {config_path}")

        # Validate schema version before touching any fields.
        _check_schema_version(str(data.get('version', SCHEMA_VERSION)))

        # Parse overrides
        overrides = {}
        if 'overrides' in data:
            for file_name, override_data in data['overrides'].items():
                try:
                    # Convert last_updated string to date object if needed
                    if 'last_updated' in override_data and isinstance(override_data['last_updated'], str):
                        from datetime import datetime
                        override_data['last_updated'] = datetime.strptime(override_data['last_updated'], '%Y-%m-%d').date()
                    overrides[file_name] = FileOverride(**override_data)
                except (TypeError, ValueError) as e:
                    raise ConfigError(f"Invalid override data for '{file_name}': {e}")

        raw_meta_overrides = data.get('metadata_overrides', {})
        if not isinstance(raw_meta_overrides, dict):
            raise ConfigError("'metadata_overrides' must be a mapping")
        metadata_overrides = {k: dict(v) for k, v in raw_meta_overrides.items()}

        raw_pyve = data.get('pyve_version')
        pyve_version = str(raw_pyve) if raw_pyve is not None else None

        return Config(
            version=data.get('version', '2.0'),
            installed_version=data.get('installed_version'),
            target_dir=data.get('target_dir', 'docs/project-guide'),
            metadata_file=data.get('metadata_file', '.metadata.yml'),
            current_mode=data.get('current_mode', 'default'),
            test_first=bool(data.get('test_first', False)),
            pyve_version=pyve_version,
            project_name=str(data.get('project_name', '') or ''),
            metadata_overrides=metadata_overrides,
            overrides=overrides
        )

    def save(self, path: str = ".project-guide.yml") -> None:
        """Save configuration to YAML file."""
        data = {
            "version": self.version,
            "installed_version": self.installed_version,
            "target_dir": self.target_dir,
            "metadata_file": self.metadata_file,
            "current_mode": self.current_mode,
            "test_first": self.test_first,
            "pyve_version": self.pyve_version,
            "project_name": self.project_name,
        }

        if self.metadata_overrides:
            data["metadata_overrides"] = self.metadata_overrides

        if self.overrides:
            overrides_dict = {
                file_name: override.to_dict()
                for file_name, override in self.overrides.items()
            }
            data["overrides"] = overrides_dict

        config_path = Path(path)
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def is_overridden(self, file_name: str) -> bool:
        """Check if a file is overridden."""
        return file_name in self.overrides

    def add_override(self, file_name: str, reason: str, version: str) -> None:
        """Add or update a file override."""
        self.overrides[file_name] = FileOverride(
            reason=reason,
            locked_version=version,
            last_updated=date.today(),
        )

    def remove_override(self, file_name: str) -> None:
        """Remove a file override."""
        self.overrides.pop(file_name, None)
