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

# Matches: ### / #### / ##### Story N.a: v2.4.0 Some Title [Done]
# The `#{3,5}` prefix accepts H3–H5 depths so sub-numbered clusters can nest a
# group header (`### Story J.m`) above deeper children (`##### Story J.m.1`);
# `##` (phase level) and `######` (too deep) are not story headings (Story Q.v).
# The optional `(?:\.\d+)?` tail captures sub-numbered IDs (`J.m.1`, `J.m.2`, …)
# used for pre-implementation splits or post-implementation follow-ups. See
# `_phase-letters.md` (Sub-numbered stories). The colon after the ID stays
# required at every depth.
_STORY_RE = re.compile(
    r"^#{3,5} Story ([A-Z]\.[a-z]+(?:\.\d+)?): (.+) \[(Done|In Progress|Planned)\]\s*$",
    re.MULTILINE,
)

# Matches: ## Phase N: Phase Name (v2.4.0)  or  ## Phase N: Phase Name
_PHASE_RE = re.compile(
    r"^## Phase ([A-Z]): ([^(\n]+)",
    re.MULTILINE,
)


@dataclass
class PhaseSummary:
    letter: str
    name: str
    done: int
    total: int


@dataclass
class StoriesSummary:
    total: int
    done: int
    in_progress: int
    planned: int
    next_story: str | None
    phases: list[PhaseSummary] = field(default_factory=list)


@dataclass(frozen=True)
class StoryHeading:
    """A ``[Done]`` story heading parsed from stories.md.

    ``story_id`` is the bracketed phase-letter form (``"G.a"``, ``"P.k"``);
    ``title`` is the heading text between ``: `` and `` [Done]`` verbatim.
    The :func:`derive_commit_message` helper produces the gitbetter-ready
    commit subject from these two fields.

    ``is_header`` (Story P.v) is ``True`` when the story's body contains zero
    Markdown checklist items (no ``- [ ]`` and no ``- [x]``), indicating a
    "group overview" / header heading rather than a real unit of work. The
    ``git-push`` wrapper filters header stories out of its uncommitted-
    detection flow. Default ``False`` preserves backward compatibility for
    callers that construct ``StoryHeading`` directly without body context.
    """
    story_id: str
    title: str
    is_header: bool = False


# Matches a Markdown checklist line at any indent: ``- [ ] task`` or ``- [x] task``.
_CHECKLIST_ITEM_RE = re.compile(r"^\s*- \[[ x]\]\s", re.MULTILINE)


def _story_body_has_checklist(body: str) -> bool:
    """Return True iff the body contains at least one ``- [ ]`` or ``- [x]`` line."""
    return _CHECKLIST_ITEM_RE.search(body) is not None


def _read_done_stories(spec_artifacts_path: str) -> list[StoryHeading] | None:
    """Return all ``[Done]`` story headings from stories.md in file order.

    Returns ``None`` when the file is absent or unreadable. Returns an empty
    list when the file exists but contains no ``[Done]`` headings (callers
    distinguish the two cases when reporting errors).

    Each ``StoryHeading.is_header`` flag is populated by scanning the story's
    body — the text between this ``### Story`` heading and the next
    ``### Story`` / ``## Phase`` / ``## Future`` / EOF — for Markdown
    checklist items (Story P.v).
    """
    stories_path = Path(spec_artifacts_path) / "stories.md"
    if not stories_path.exists():
        return None
    try:
        text = stories_path.read_text(encoding="utf-8")
    except OSError:
        return None

    # Match every story-heading line (any status); body extends from after the
    # heading up to the next story / phase / future heading or EOF.
    headings = list(_STORY_RE.finditer(text))
    results: list[StoryHeading] = []
    for i, m in enumerate(headings):
        sid, title, status = m.group(1), m.group(2), m.group(3)
        if status != "Done":
            continue
        body_start = m.end()
        body_end = _find_story_body_end(text, body_start, headings, i)
        body = text[body_start:body_end]
        results.append(
            StoryHeading(
                story_id=sid,
                title=title,
                is_header=not _story_body_has_checklist(body),
            )
        )
    return results


_PHASE_BOUNDARY_RE = re.compile(r"^(?:## Phase |## Future)", re.MULTILINE)


def _find_story_body_end(
    text: str,
    body_start: int,
    headings: list,
    heading_index: int,
) -> int:
    """Return the offset where the current story's body ends.

    The body ends at the next ``### Story`` heading (from ``headings``) or at
    the next ``## Phase`` / ``## Future`` heading, whichever comes first;
    falls back to EOF.
    """
    next_story_start = (
        headings[heading_index + 1].start()
        if heading_index + 1 < len(headings)
        else len(text)
    )
    m = _PHASE_BOUNDARY_RE.search(text, body_start, next_story_start)
    if m is not None:
        return m.start()
    return next_story_start


def derive_commit_message(heading: StoryHeading) -> str:
    r"""Transform a story heading into a gitbetter-ready commit subject.

    Rules (Story P.k):
      - Output is ``"<id>: <title>"`` (preserve the colon — it's the
        anchor the already-committed check searches for in ``git log %s``).
      - Backticks in the title become single quotes (``\`foo\``` → ``'foo'``).
      - Double quotes in the title become single quotes (``"Hello"`` → ``'Hello'``).
      - Single quotes in the title pass through unchanged (the wrapper
        invokes gitbetter via ``subprocess.run([...], shell=False)``, so
        no shell quoting concern).
    """
    cleaned_title = heading.title.replace("`", "'").replace('"', "'")
    return f"{heading.story_id}: {cleaned_title}"


# --- Multi-ID commit-subject parser and bundle formatter (Story P.u) --------
#
# The parser supersedes the single-regex `_COMMIT_SUBJECT_STORY_ID_RE` used by
# P.k/P.s. It extracts the ordered ID list from a commit subject covering:
#   - Single bare:     `A.a: v0.1.0 Hello World`
#   - Single storied:  `Story A.a: v0.1.0 Hello World`  (P.s legacy)
#   - Bundle legacy:   `H.a, H.b, H.c InputSource ...`  (no colon before title)
#   - Bundle canonical (unversioned): `H.a, H.b, H.c: Foo bar`
#   - Bundle versioned (per-story):   `H.a: v0.10.0, H.b: v0.11.0 sample ...`
#   - Bundle mixed:    `H.a, H.b: v1.2.3, H.c: Foo bar`
#   - Bundle single-trailing-version: `H.a, H.b, H.c: v1.2.3 Foo`
#
# Disambiguation rule preserved from P.s: a single ID without a `:` is NOT a
# story commit (`Story J.m.2 some other text` → []). Bundles are recognized by
# the comma separator between IDs, so the colon before the title is optional
# in bundles only.

_ID_PATTERN = r"[A-Z]\.[a-z]+(?:\.\d+)?"
_VERSION_PATTERN = r"v\d+\.\d+\.\d+"

_STORY_PREFIX_RE = re.compile(r"^Story\s+")
_ID_RE = re.compile(rf"^({_ID_PATTERN})")
_COLON_VERSION_RE = re.compile(rf"^:\s*({_VERSION_PATTERN})")
_BUNDLE_SEP_RE = re.compile(r"^,\s*")
_LEADING_VERSION_IN_TITLE_RE = re.compile(rf"^({_VERSION_PATTERN})\s+(.*)$")


def parse_committed_ids_from_subject(line: str) -> list[str]:
    """Return the ordered list of bare story IDs in a commit-subject line.

    Returns ``[]`` when the line is not a recognized story-commit subject.
    See module-level comment for the grammar and supported forms.
    """
    s = line
    m = _STORY_PREFIX_RE.match(s)
    if m:
        s = s[m.end():]

    m = _ID_RE.match(s)
    if not m:
        return []
    ids = [m.group(1)]
    s = s[m.end():]

    first_consumed_version = False
    m = _COLON_VERSION_RE.match(s)
    if m:
        first_consumed_version = True
        s = s[m.end():]

    has_bundle = False
    while True:
        m = _BUNDLE_SEP_RE.match(s)
        if not m:
            break
        has_bundle = True
        s = s[m.end():]
        m = _ID_RE.match(s)
        if not m:
            return []
        ids.append(m.group(1))
        s = s[m.end():]
        m = _COLON_VERSION_RE.match(s)
        if m:
            s = s[m.end():]

    if not has_bundle:
        # Single-ID form: require the ":" anchor (post-version if any) so plain
        # prose like "Story J.m.2 some other text" does not falsely match.
        if first_consumed_version:
            if s == "" or s.startswith(" "):
                return ids
            return []
        if s.startswith(":"):
            return ids
        return []

    # Bundle form: optional ":" before title, then space or EOL.
    if s.startswith(":"):
        s = s[1:]
    if s == "" or s[0].isspace():
        return ids
    return []


def _split_leading_version(title: str) -> tuple[str | None, str]:
    """Split a leading ``vX.Y.Z`` off a heading title.

    ``StoryHeading.title`` carries the version inline at the head (e.g.,
    ``"v0.10.0 sample_per_class filter op"``). Returns ``(version, rest)``
    when the title starts with a version; otherwise ``(None, title)``.
    """
    m = _LEADING_VERSION_IN_TITLE_RE.match(title)
    if m:
        return m.group(1), m.group(2)
    return None, title


def derive_bundle_commit_message(headings: list[StoryHeading]) -> str:
    """Compose a bundled commit subject from two or more story headings.

    Format rules (Story P.u):
      - Per-story token: ``<id>`` when the story has no version, ``<id>: <version>`` when it does.
      - Tokens are joined with ``", "``.
      - The title boundary uses ``": "`` after the last token, unless that
        token already ends with ``": <version>"`` — in which case the version's
        colon doubles as the boundary and only a single space precedes the title.
      - Per-story titles (with the leading version stripped) are joined with ``" + "``.
      - Backticks and double quotes in titles become single quotes (same as
        :func:`derive_commit_message`).
      - Final message has leading/trailing whitespace trimmed and any internal
        whitespace run collapsed to a single space.

    Callers are expected to supply at least two headings; the formatter does
    not enforce this (a single-element input simply produces a single-token
    bundle, which is structurally indistinguishable from the canonical
    single-ID subject :func:`derive_commit_message` produces).
    """
    parts: list[tuple[str, str | None, str]] = []
    for h in headings:
        ver, rest = _split_leading_version(h.title)
        cleaned = rest.replace("`", "'").replace('"', "'")
        parts.append((h.story_id, ver, cleaned))

    id_tokens = [
        f"{sid}: {ver}" if ver else sid
        for sid, ver, _ in parts
    ]
    id_list = ", ".join(id_tokens)

    last_token_has_version = parts[-1][1] is not None
    boundary = " " if last_token_has_version else ": "

    titles = " + ".join(p[2] for p in parts)
    message = id_list + boundary + titles
    message = re.sub(r"\s+", " ", message).strip()
    return message


def _read_stories_summary(spec_artifacts_path: str) -> "StoriesSummary | None":
    """Parse stories.md and return a summary.

    Returns None if the file is absent, unreadable, or contains no story
    headings (e.g. a freshly-archived empty file).
    """
    stories_path = Path(spec_artifacts_path) / "stories.md"
    if not stories_path.exists():
        return None

    try:
        text = stories_path.read_text(encoding="utf-8")
    except OSError:
        return None

    matches = _STORY_RE.findall(text)
    if not matches:
        return None

    done = sum(1 for _, _, s in matches if s == "Done")
    in_progress = sum(1 for _, _, s in matches if s == "In Progress")
    planned = sum(1 for _, _, s in matches if s == "Planned")

    next_story: str | None = None
    for story_id, title, status in matches:
        if status != "Done":
            next_story = f"Story {story_id}: {title}"
            break

    # Per-phase breakdown — preserve document order
    phases: list[PhaseSummary] = []
    for m in _PHASE_RE.finditer(text):
        letter = m.group(1)
        name = m.group(2).strip()
        phase_stories = [(sid, t, s) for sid, t, s in matches if sid.startswith(f"{letter}.")]
        if phase_stories:
            phases.append(PhaseSummary(
                letter=letter,
                name=name,
                done=sum(1 for _, _, s in phase_stories if s == "Done"),
                total=len(phase_stories),
            ))

    return StoriesSummary(
        total=len(matches),
        done=done,
        in_progress=in_progress,
        planned=planned,
        next_story=next_story,
        phases=phases,
    )
