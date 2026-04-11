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

"""
Artifact action handlers.

Mode metadata entries can declare an `action:` on each artifact, describing
what should happen to the file when the mode runs. Most actions are
LLM-driven (the mode template prompts the developer conversationally), but
the `archive` action is deterministic: it moves the source to `.archive/`
under a version-stamped name and re-renders a fresh source from the artifact
template, preserving the `## Future` section verbatim.

This module defines:
  - the valid action constants (`create`, `modify`, `archive`)
  - pure helpers for version/phase/future detection
  - the `perform_archive` runtime used by the `archive_stories` mode
"""

from __future__ import annotations

import contextlib
import re
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from project_guide.exceptions import ActionError, MetadataError


class ActionType(StrEnum):
    """
    Valid values for an artifact's `action:` field in `.metadata.yml`.

    Subclasses `str` so `ActionType.ARCHIVE == "archive"` is `True` and the
    enum members serialize back to bare YAML strings unchanged.
    """
    CREATE = "create"
    MODIFY = "modify"
    ARCHIVE = "archive"


@dataclass
class Artifact:
    """
    Parsed artifact entry from a mode's `artifacts:` list.

    Exactly one of `file`, `webpage`, or `framework` is typically set (this
    mirrors the existing YAML schema where each artifact uses one of those
    keys as its target). `action` is optional — some legacy entries declare
    only a target with no explicit action.
    """
    file: str | None = None
    webpage: str | None = None
    framework: str | None = None
    action: ActionType | None = None

    @classmethod
    def from_dict(cls, raw: dict, *, mode_name: str, index: int) -> Artifact:
        """
        Build an `Artifact` from a raw YAML dict, validating the `action` field.

        Raises `MetadataError` if the dict is malformed or if `action` is
        present but not a recognized `ActionType`. This is a metadata-parse
        failure, not a runtime action failure, hence `MetadataError`.
        """
        if not isinstance(raw, dict):
            raise MetadataError(
                f"Mode '{mode_name}': artifacts[{index}] must be a mapping, "
                f"got {type(raw).__name__}"
            )

        raw_action = raw.get("action")
        action: ActionType | None = None
        if raw_action is not None:
            try:
                action = ActionType(raw_action)
            except ValueError:
                valid = ", ".join(a.value for a in ActionType)
                raise MetadataError(
                    f"Mode '{mode_name}': artifacts[{index}] has unknown "
                    f"action '{raw_action}'. Valid actions: {valid}"
                ) from None

        return cls(
            file=raw.get("file"),
            webpage=raw.get("webpage"),
            framework=raw.get("framework"),
            action=action,
        )

# Matches `### Story <Phase>.<sub>: vMAJOR.MINOR.PATCH ...`
_VERSION_RE = re.compile(
    r"^###\s+Story\s+[A-Za-z]+\.[a-z]+:\s+v(\d+)\.(\d+)\.(\d+)",
    re.M,
)

# Matches `## Phase <Letters>:` — letters only, base-26 no-zero scheme.
_PHASE_RE = re.compile(r"^##\s+Phase\s+([A-Z]+):", re.M)

# Matches the `## Future` heading and everything following it to EOF.
_FUTURE_RE = re.compile(r"^##\s+Future\s*$.*", re.M | re.S)


def detect_latest_version(text: str) -> tuple[int, int, int]:
    """
    Return the highest `vMAJOR.MINOR.PATCH` found in `### Story ...` headings.

    Raises `ActionError` if no versioned story headings are found.
    """
    versions = [
        (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        for m in _VERSION_RE.finditer(text)
    ]
    if not versions:
        raise ActionError(
            "No versioned story headings found — expected `### Story X.y: vN.N.N ...`"
        )
    return max(versions)


def detect_latest_phase_letter(text: str) -> str:
    """
    Return the highest `## Phase <Letter>:` heading using base-26-no-zero order.

    The ordering is `A` < `B` < ... < `Z` < `AA` < `AB` < ... < `ZZ` < `AAA`,
    which is equivalent to sorting by `(len(letters), letters)`.

    Raises `ActionError` if no phase headings are found.
    """
    letters = [m.group(1) for m in _PHASE_RE.finditer(text)]
    if not letters:
        raise ActionError(
            "No phase headings found — expected `## Phase <Letter>:`"
        )
    letters.sort(key=lambda s: (len(s), s))
    return letters[-1]


def extract_future_section(text: str) -> str:
    """
    Return the `## Future` section verbatim (heading included, through EOF),
    or an empty string if no such section exists.
    """
    m = _FUTURE_RE.search(text)
    return m.group(0) if m else ""


def render_fresh_stories_artifact(
    artifact_template: Path,
    context: dict,
    future_section: str = "",
) -> str:
    """
    Re-render the stories.md artifact template with an empty body.

    If `future_section` is non-empty, it replaces the template's default
    `## Future` block verbatim. Otherwise the template's default Future block
    (with its HTML-comment explainer) is preserved so the developer gets a
    helpful empty-state.
    """
    env = Environment(
        loader=FileSystemLoader(str(artifact_template.parent), encoding="utf-8"),
        keep_trailing_newline=True,
    )
    template = env.get_template(artifact_template.name)
    rendered = template.render(phases_and_stories="", **context)

    if future_section:
        replacement = future_section.rstrip() + "\n"
        rendered = _FUTURE_RE.sub(lambda _m: replacement, rendered)

    return rendered


@dataclass(frozen=True)
class ArchiveResult:
    """Outcome of a successful `perform_archive` call."""
    archived_to: Path
    source_rewritten: Path
    version: str
    phase_letter: str
    future_carried: bool


def perform_archive(
    source: Path,
    artifact_template: Path,
    context: dict,
) -> ArchiveResult:
    """
    Execute the `archive` action against `source` (e.g. `docs/specs/stories.md`).

    1. Read the source, detect latest version and phase letter, extract any
       `## Future` section.
    2. Move the source to `<dirname>/.archive/<stem>-vX.Y.Z<suffix>`.
    3. Re-render a fresh source from `artifact_template` with the Future
       section carried over verbatim.

    Returns an `ArchiveResult` describing the operation.

    Raises `ActionError` on any validation or I/O failure. Best-effort: if the
    fresh re-render fails, the moved source is restored from `.archive/`.
    """
    if not source.exists():
        raise ActionError(f"Source file not found: {source}")
    if not artifact_template.exists():
        raise ActionError(f"Artifact template not found: {artifact_template}")

    text = source.read_text(encoding="utf-8")

    major, minor, patch = detect_latest_version(text)
    version = f"v{major}.{minor}.{patch}"
    phase_letter = detect_latest_phase_letter(text)
    future = extract_future_section(text)

    archive_dir = source.parent / ".archive"
    archive_dir.mkdir(exist_ok=True)
    archive_target = archive_dir / f"{source.stem}-{version}{source.suffix}"

    if archive_target.exists():
        raise ActionError(f"Archive target already exists: {archive_target}")

    shutil.move(str(source), str(archive_target))

    try:
        fresh = render_fresh_stories_artifact(artifact_template, context, future)
        source.write_text(fresh, encoding="utf-8")
    except Exception as exc:
        # Best-effort rollback so we don't leave the workspace with the
        # source file missing.
        with contextlib.suppress(OSError):
            shutil.move(str(archive_target), str(source))
        raise ActionError(f"Failed to re-render {source.name}: {exc}") from exc

    return ArchiveResult(
        archived_to=archive_target,
        source_rewritten=source,
        version=version,
        phase_letter=phase_letter,
        future_carried=bool(future),
    )
