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
    #: Whether the Pyve guidance section renders into ``go.md``.
    #:
    #: Deliberately *not* derived from ``pyve_version`` (Story R.j). The two
    #: answer different questions — "should the guidance render?" versus
    #: "which pyve was seen?" — and deriving the first from the second is what
    #: turned a single failed ``pyve --version`` probe into the permanent loss
    #: of ~80 lines of guardrail from every rendered ``go.md``.
    pyve_installed: bool = False
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

        # Migration default (Story R.j): a config written before this field
        # existed has no key, so fall back to exactly the answer the old
        # derived gate would have given. Upgrading therefore changes no
        # project's behavior at the moment of upgrade; it changes on the next
        # `update` / `mode`, which is the intended repair. A key that *is*
        # present always wins — that is how a hand-edited opt-out survives.
        raw_installed = data.get('pyve_installed')
        pyve_installed = (
            bool(raw_installed) if raw_installed is not None else pyve_version is not None
        )

        return Config(
            version=data.get('version', '2.0'),
            installed_version=data.get('installed_version'),
            target_dir=data.get('target_dir', 'docs/project-guide'),
            metadata_file=data.get('metadata_file', '.metadata.yml'),
            current_mode=data.get('current_mode', 'default'),
            test_first=bool(data.get('test_first', False)),
            pyve_version=pyve_version,
            pyve_installed=pyve_installed,
            project_name=str(data.get('project_name', '') or ''),
            metadata_overrides=metadata_overrides,
            overrides=overrides
        )

    def record_pyve_detection(self, detected_version: str | None) -> bool:
        """Fold an *automatic* pyve detection result in. Returns whether it changed.

        This is the single function every automatic update must flow through,
        and it enforces the load-bearing rule of Subphase R-2:

        > **Automatic detection may only ever set ``pyve_installed`` to
        > ``true``. It never sets it to ``false``.**

        A failed probe leaves both fields exactly as they were. Detection is
        unreliable in ways that have nothing to do with whether pyve is really
        present — a `PATH` that has not been rehashed, a slow first run, a
        sandbox — and treating any of those as "pyve is gone" is what silently
        removed the guardrail. Once a project has seen pyve even once, no
        later miss can strip the guidance again.

        Turning the flag off stays an explicit user action: hand-editing
        ``.project-guide.yml``. The accepted trade is that a project which
        genuinely stops using pyve keeps rendering the section until the
        developer opts out — irrelevant guidance is noise, missing guidance is
        a removed guardrail.

        ``init`` deliberately does **not** call this: it is the one site
        allowed to record a miss as ``false``, because there is no prior
        observation to preserve.

        The boolean return lets callers skip a pointless config write.
        """
        if detected_version is None:
            return False

        changed = not self.pyve_installed or self.pyve_version != detected_version
        self.pyve_installed = True
        self.pyve_version = detected_version
        return changed

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
            "pyve_installed": self.pyve_installed,
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
