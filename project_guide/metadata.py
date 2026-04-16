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

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from project_guide.actions import Artifact
from project_guide.exceptions import MetadataError


@dataclass
class ModeDefinition:
    """A single mode entry from .metadata.yml."""
    name: str
    info: str
    description: str
    sequence_or_cycle: str
    generation_type: str = "document"
    mode_template: str = ""
    next_mode: str | None = None
    artifacts: list[Artifact] = field(default_factory=list)
    files_exist: list[str] = field(default_factory=list)


@dataclass
class Metadata:
    """Parsed and resolved .metadata.yml."""
    common: dict[str, str]
    modes: list[ModeDefinition]

    def get_mode(self, name: str) -> ModeDefinition:
        """Look up a mode by name. Raises MetadataError if not found."""
        for mode in self.modes:
            if mode.name == name:
                return mode
        available = ", ".join(m.name for m in self.modes)
        raise MetadataError(f"Mode '{name}' not found. Available modes: {available}")

    def list_mode_names(self) -> list[str]:
        """Return all available mode names."""
        return [m.name for m in self.modes]


def _parse_artifacts(mode_name: str, raw_artifacts: object) -> list[Artifact]:
    """
    Convert a mode's raw `artifacts:` list (already variable-resolved) into a
    list of `Artifact` dataclass instances.

    Raises `MetadataError` if `artifacts` is not a list, or if any entry has
    an unknown `action:` value. Artifacts without an `action:` field are
    tolerated — some entries (e.g. the generated per-phase planning doc)
    declare only a target path.
    """
    if not isinstance(raw_artifacts, list):
        raise MetadataError(
            f"Mode '{mode_name}': 'artifacts' must be a list"
        )
    return [
        Artifact.from_dict(raw, mode_name=mode_name, index=i)
        for i, raw in enumerate(raw_artifacts)
    ]


def _resolve_variables(value: str, variables: dict[str, str]) -> str:
    """Replace {{var}} placeholders with values from the variables dict."""
    def replacer(match):
        key = match.group(1).strip()
        if key in variables:
            return variables[key]
        return match.group(0)  # leave unresolved placeholders as-is
    return re.sub(r"\{\{(\w+)\}\}", replacer, value)


def _resolve_dict(data, variables: dict[str, str]):
    """Recursively resolve {{var}} placeholders in a dict/list structure."""
    if isinstance(data, str):
        return _resolve_variables(data, variables)
    elif isinstance(data, dict):
        return {k: _resolve_dict(v, variables) for k, v in data.items()}
    elif isinstance(data, list):
        return [_resolve_dict(item, variables) for item in data]
    return data


_OVERRIDABLE_MODE_FIELDS: frozenset[str] = frozenset(
    {"next_mode", "files_exist", "info", "description"}
)


def _apply_metadata_overrides(metadata: Metadata, overrides: dict[str, dict]) -> None:
    """Patch mode fields in-place using the project's ``metadata_overrides`` config.

    Supports partial patches: only listed fields are changed; all others are
    left as-is.  Raises ``MetadataError`` for unknown mode names or fields.
    """
    for mode_name, patches in overrides.items():
        try:
            mode = metadata.get_mode(mode_name)
        except MetadataError:
            available = ", ".join(m.name for m in metadata.modes)
            raise MetadataError(
                f"metadata_overrides: unknown mode '{mode_name}'. "
                f"Available modes: {available}"
            )

        for field_name, value in patches.items():
            if field_name not in _OVERRIDABLE_MODE_FIELDS:
                raise MetadataError(
                    f"metadata_overrides['{mode_name}']: unknown field '{field_name}'. "
                    f"Supported fields: {', '.join(sorted(_OVERRIDABLE_MODE_FIELDS))}"
                )
            setattr(mode, field_name, value)


def load_metadata(path: str | Path) -> Metadata:
    """
    Load and validate .metadata.yml.

    Two-pass resolution: the `common` block defines variables, then all
    other fields containing {{var}} are resolved against those variables.
    """
    path = Path(path)
    if not path.exists():
        raise MetadataError(f"Metadata file not found: {path}")

    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise MetadataError(f"Invalid YAML in {path}: {e}")

    if not raw or not isinstance(raw, dict):
        raise MetadataError(f"Empty or invalid metadata file: {path}")

    # Extract common variables
    common = raw.get("common", {})
    if not isinstance(common, dict):
        raise MetadataError("'common' block must be a mapping")

    # Resolve common variables against themselves (for self-references)
    resolved_common: dict[str, str] = {}
    for key, value in common.items():
        resolved_common[key] = _resolve_variables(str(value), resolved_common)

    # Parse modes
    raw_modes = raw.get("modes", [])
    if not isinstance(raw_modes, list):
        raise MetadataError("'modes' must be a list")

    modes = []
    for raw_mode in raw_modes:
        if not isinstance(raw_mode, dict):
            raise MetadataError(f"Each mode must be a mapping, got: {type(raw_mode)}")

        # Resolve variables in all string fields
        resolved_mode = _resolve_dict(raw_mode, resolved_common)

        name = resolved_mode.get("name")
        if not name:
            raise MetadataError("Each mode must have a 'name' field")

        artifacts = _parse_artifacts(name, resolved_mode.get("artifacts", []))

        try:
            mode = ModeDefinition(
                name=name,
                info=resolved_mode.get("info", ""),
                description=resolved_mode.get("description", ""),
                sequence_or_cycle=resolved_mode.get("sequence_or_cycle", "sequence"),
                generation_type=resolved_mode.get("generation_type", "document"),
                mode_template=resolved_mode.get("mode_template", ""),
                next_mode=resolved_mode.get("next_mode"),
                artifacts=artifacts,
                files_exist=resolved_mode.get("files_exist", []),
            )
        except (TypeError, ValueError) as e:
            raise MetadataError(f"Invalid mode definition '{name}': {e}")

        modes.append(mode)

    if not modes:
        raise MetadataError("No modes defined in metadata")

    return Metadata(common=resolved_common, modes=modes)
