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

from jinja2 import Environment, FileSystemLoader, Undefined

from project_guide.exceptions import ActionError, MetadataError
from project_guide.runtime import UNRENDERED_PLACEHOLDER_RE


class _LenientUndefined(Undefined):
    """
    Jinja2 undefined that renders as `{{ name }}` instead of blank.

    Used by `render_fresh_stories_artifact` so that, if the caller cannot
    supply `project_name` / `programming_language` (e.g. when archiving a
    project that has no extractable header), the fresh output preserves
    the placeholders verbatim rather than silently emitting empty strings.

    Mirrors `project_guide.render._LenientUndefined` — kept local here to
    avoid a dependency loop between actions.py and render.py.
    """

    def __str__(self) -> str:
        return f"{{{{ {self._undefined_name} }}}}" if self._undefined_name else ""

    def __iter__(self):
        return iter([])

    def __bool__(self) -> bool:
        return False


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

# Matches the stories.md first-line header:
#   `# stories.md -- <project-name> (<programming-language>)`
# Both the em-dash variant and the double-hyphen variant are tolerated.
_STORIES_HEADER_RE = re.compile(
    r"^#\s+stories\.md\s*(?:--|—)\s*(?P<project_name>[^(]+?)\s*\((?P<programming_language>[^)]+)\)\s*$",
    re.M,
)


def increment_phase_letter(letter: str) -> str:
    """
    Return the successor of `letter` in the base-26-no-zero sequence.

    Examples:
        A → B, Y → Z, Z → AA, AA → AB, AZ → BA, ZZ → AAA

    The scheme is base-26 with no zero, so a "carry" advances to the next
    length once `Z` is exceeded (`Z` → `AA`, `ZZ` → `AAA`, etc.). This
    matches `_phase-letters.md` and the ordering used by
    `detect_latest_phase_letter`.
    """
    if not letter or not letter.isalpha() or not letter.isupper():
        raise ActionError(
            f"Invalid phase letter '{letter}': must be one or more uppercase A-Z"
        )

    chars = list(letter)
    i = len(chars) - 1
    while i >= 0:
        if chars[i] != "Z":
            chars[i] = chr(ord(chars[i]) + 1)
            return "".join(chars)
        chars[i] = "A"
        i -= 1
    # All positions were 'Z' — carry into a new leading 'A'.
    return "A" + "".join(chars)


def next_phase_letter(stories_text: str, archive_dir: Path) -> str:
    """
    Determine the next phase letter for a `plan_phase` operation.

    Lookup order:
      1. If `stories_text` contains any `## Phase <Letter>:` headings, return
         the successor of the highest one.
      2. Else, scan `archive_dir` for files matching `stories-vX.Y.Z.md` (or
         `stories-vX.Y.Z<suffix>` for the same stem). If any exist, read the
         one with the highest version, find its highest phase letter, and
         return the successor.
      3. Else, return `'A'` (fresh project, no archive).

    This mirrors the algorithm documented in `_phase-letters.md` and is
    intended to be callable from future plan_phase tooling. The current
    plan_phase mode template describes the same algorithm in prose so the
    LLM can perform it directly without invoking Python.

    Args:
        stories_text: Contents of `docs/specs/stories.md` (may be empty body).
        archive_dir: Path to `docs/specs/.archive/` (may not exist).

    Returns:
        The next phase letter as a string (e.g., `'A'`, `'K'`, `'AA'`).
    """
    # Case 1: stories.md already has phases — advance from the highest.
    try:
        current = detect_latest_phase_letter(stories_text)
        return increment_phase_letter(current)
    except ActionError:
        pass  # No phases in stories.md — fall through to archive lookup.

    # Case 2: empty stories.md — look in the archive directory.
    if archive_dir.exists() and archive_dir.is_dir():
        archived = _find_latest_archived_stories(archive_dir)
        if archived is not None:
            try:
                last_phase = detect_latest_phase_letter(
                    archived.read_text(encoding="utf-8")
                )
                return increment_phase_letter(last_phase)
            except ActionError:
                pass  # Archived file has no phases — treat as fresh.

    # Case 3: no phases anywhere — fresh project.
    return "A"


# Matches archived stories filenames: `stories-vX.Y.Z.md`, allowing any
# stem prefix and any suffix so this also works for `stories-tmp-v1.0.0.md`
# style names.
_ARCHIVED_STORIES_RE = re.compile(
    r"^(?P<stem>.+)-v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)\.md$"
)


def _find_latest_archived_stories(archive_dir: Path) -> Path | None:
    """
    Return the archived stories file with the highest version, or None if
    no archived stories files are present.

    Considers only files whose name starts with `stories-` to avoid picking
    up unrelated archived artifacts.
    """
    candidates: list[tuple[tuple[int, int, int], Path]] = []
    for path in archive_dir.iterdir():
        if not path.is_file():
            continue
        m = _ARCHIVED_STORIES_RE.match(path.name)
        if not m:
            continue
        if not m.group("stem").startswith("stories"):
            continue
        version = (int(m.group("major")), int(m.group("minor")), int(m.group("patch")))
        candidates.append((version, path))

    if not candidates:
        return None
    candidates.sort()
    return candidates[-1][1]


def extract_stories_header_context(text: str) -> dict[str, str]:
    """
    Parse the stories.md first-line header and return `project_name` and
    `programming_language` if found, otherwise an empty dict.

    The archive pipeline uses this so the fresh re-render preserves the
    original header values — falling back to lenient placeholders when
    extraction fails.
    """
    m = _STORIES_HEADER_RE.search(text)
    if not m:
        return {}
    return {
        "project_name": m.group("project_name").strip(),
        "programming_language": m.group("programming_language").strip(),
    }


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
        undefined=_LenientUndefined,
    )
    template = env.get_template(artifact_template.name)
    rendered = template.render(phases_and_stories="", **context)

    if future_section:
        replacement = future_section.rstrip() + "\n"
        rendered = _FUTURE_RE.sub(lambda _m: replacement, rendered)

    # Any placeholder that survived Jinja is the fingerprint of a missing
    # context variable, a typo, or a removed `{% if %}` guard — previously
    # these leaked silently into the fresh stories.md header.
    matches = UNRENDERED_PLACEHOLDER_RE.findall(rendered)
    if matches:
        seen: set[str] = set()
        unique: list[str] = []
        for name in matches:
            if name not in seen:
                seen.add(name)
                unique.append(name)
        raise ActionError(
            f"Unrendered placeholder(s) in {artifact_template.name}: "
            f"{', '.join(unique)}. "
            "Hint: check the caller's context dict for a missing variable."
        )

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

    # Auto-extract header context from the source so the fresh re-render
    # preserves `project_name` / `programming_language`. The caller's
    # context takes precedence if both provide a value.
    merged_context = {**extract_stories_header_context(text), **context}

    archive_dir = source.parent / ".archive"
    archive_dir.mkdir(exist_ok=True)
    archive_target = archive_dir / f"{source.stem}-{version}{source.suffix}"

    if archive_target.exists():
        raise ActionError(f"Archive target already exists: {archive_target}")

    shutil.move(str(source), str(archive_target))

    try:
        fresh = render_fresh_stories_artifact(artifact_template, merged_context, future)
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
