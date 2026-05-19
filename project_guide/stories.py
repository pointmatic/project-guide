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

# Matches: ### Story N.a: v2.4.0 Some Title [Done]
# The optional `(?:\.\d+)?` tail captures sub-numbered IDs (`J.m.1`, `J.m.2`, …)
# used for pre-implementation splits or post-implementation follow-ups. See
# `_phase-letters.md` (Sub-numbered stories).
_STORY_RE = re.compile(
    r"^### Story ([A-Z]\.[a-z]+(?:\.\d+)?): (.+) \[(Done|In Progress|Planned)\]\s*$",
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
    """
    story_id: str
    title: str


def _read_done_stories(spec_artifacts_path: str) -> list[StoryHeading] | None:
    """Return all ``[Done]`` story headings from stories.md in file order.

    Returns ``None`` when the file is absent or unreadable. Returns an empty
    list when the file exists but contains no ``[Done]`` headings (callers
    distinguish the two cases when reporting errors).
    """
    stories_path = Path(spec_artifacts_path) / "stories.md"
    if not stories_path.exists():
        return None
    try:
        text = stories_path.read_text(encoding="utf-8")
    except OSError:
        return None

    return [
        StoryHeading(story_id=sid, title=title)
        for sid, title, status in _STORY_RE.findall(text)
        if status == "Done"
    ]


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
