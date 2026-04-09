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

from project_guide.exceptions import ConfigError


@dataclass
class GuideOverride:
    """Represents an overridden guide."""
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
    def from_dict(cls, data: dict) -> "GuideOverride":
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
    overrides: dict[str, GuideOverride] = field(default_factory=dict)

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

        # Parse overrides
        overrides = {}
        if 'overrides' in data:
            for guide_name, override_data in data['overrides'].items():
                try:
                    # Convert last_updated string to date object if needed
                    if 'last_updated' in override_data and isinstance(override_data['last_updated'], str):
                        from datetime import datetime
                        override_data['last_updated'] = datetime.strptime(override_data['last_updated'], '%Y-%m-%d').date()
                    overrides[guide_name] = GuideOverride(**override_data)
                except (TypeError, ValueError) as e:
                    raise ConfigError(f"Invalid override data for '{guide_name}': {e}")

        return Config(
            version=data.get('version', '2.0'),
            installed_version=data.get('installed_version'),
            target_dir=data.get('target_dir', 'docs/project-guide'),
            metadata_file=data.get('metadata_file', '.metadata.yml'),
            current_mode=data.get('current_mode', 'default'),
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
        }

        if self.overrides:
            overrides_dict = {
                guide_name: override.to_dict()
                for guide_name, override in self.overrides.items()
            }
            data["overrides"] = overrides_dict  # type: ignore[assignment]

        config_path = Path(path)
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def is_overridden(self, guide_name: str) -> bool:
        """Check if a guide is overridden."""
        return guide_name in self.overrides

    def add_override(self, guide_name: str, reason: str, version: str) -> None:
        """Add or update an override."""
        self.overrides[guide_name] = GuideOverride(
            reason=reason,
            locked_version=version,
            last_updated=date.today(),
        )

    def remove_override(self, guide_name: str) -> None:
        """Remove an override."""
        self.overrides.pop(guide_name, None)
