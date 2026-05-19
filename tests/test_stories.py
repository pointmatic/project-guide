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

from pathlib import Path

from project_guide.stories import (
    _STORY_RE,
    StoryHeading,
    _read_done_stories,
    derive_commit_message,
)

_HEADER = """\
# stories.md -- testproject (python)

## Phase J: Demo

"""


def _write(tmp_path: Path, body: str) -> Path:
    specs = tmp_path / "docs" / "specs"
    specs.mkdir(parents=True)
    (specs / "stories.md").write_text(_HEADER + body, encoding="utf-8")
    return specs


# ---------------------------------------------------------------------------
# _STORY_RE — direct regex coverage for sub-numbered story IDs
# ---------------------------------------------------------------------------


def test_story_re_matches_plain_letter_id():
    """Baseline: ordinary `J.l` form still matches."""
    line = "### Story J.l: update remaining quizazz refs [Done]\n"
    matches = _STORY_RE.findall(line)
    assert matches == [("J.l", "update remaining quizazz refs", "Done")]


def test_story_re_matches_sub_numbered_id():
    """Sub-numbered `J.m.1` form (post-impl follow-up or pre-impl split)
    must be parsed the same way as the plain form."""
    line = "### Story J.m.1: v0.70.0 Follow-up after J.m [Done]\n"
    matches = _STORY_RE.findall(line)
    assert matches == [("J.m.1", "v0.70.0 Follow-up after J.m", "Done")]


def test_story_re_matches_multi_digit_sub_number():
    """Sub-numbers can exceed a single digit (e.g., `.10`, `.11`)."""
    line = "### Story J.m.10: tenth follow-up [Done]\n"
    matches = _STORY_RE.findall(line)
    assert matches == [("J.m.10", "tenth follow-up", "Done")]


# ---------------------------------------------------------------------------
# _read_done_stories — "last [Done]" selection with sub-numbered IDs
# ---------------------------------------------------------------------------


def test_read_done_stories_scenario_a_subnumber_follows_bare_letter(tmp_path):
    """Scenario A — post-implementation follow-up.

    Sequence: J.l, J.m, J.m.1 (all Done). J.m was implemented, then a
    follow-up bug/feature surfaced as J.m.1 before proceeding to J.n.
    The wrapper's "last [Done]" must be J.m.1, not J.m or J.l.
    """
    specs = _write(
        tmp_path,
        (
            "### Story J.l: update remaining refs [Done]\n\n"
            "### Story J.m: v0.69.0 Integrate component [Done]\n\n"
            "### Story J.m.1: v0.70.0 Follow-up after J.m [Done]\n"
        ),
    )
    headings = _read_done_stories(str(specs))
    assert headings is not None
    assert [h.story_id for h in headings] == ["J.l", "J.m", "J.m.1"]
    assert headings[-1] == StoryHeading(
        story_id="J.m.1", title="v0.70.0 Follow-up after J.m"
    )


def test_read_done_stories_scenario_b_subnumber_without_bare_letter(tmp_path):
    """Scenario B — pre-implementation split.

    Sequence: J.l, J.m.1, J.m.2 (all Done). J.m's scope was deemed too
    large before any implementation began, so it was split into J.m.1
    and J.m.2 and the bare J.m heading never existed. The wrapper's
    "last [Done]" must be J.m.2.
    """
    specs = _write(
        tmp_path,
        (
            "### Story J.l: update remaining refs [Done]\n\n"
            "### Story J.m.1: v0.69.0 First half of the split [Done]\n\n"
            "### Story J.m.2: v0.70.0 Second half of the split [Done]\n"
        ),
    )
    headings = _read_done_stories(str(specs))
    assert headings is not None
    assert [h.story_id for h in headings] == ["J.l", "J.m.1", "J.m.2"]
    assert headings[-1].story_id == "J.m.2"


# ---------------------------------------------------------------------------
# derive_commit_message — round-trip with the cli's commit-subject regex
# ---------------------------------------------------------------------------


def test_derive_commit_message_with_sub_numbered_id():
    """Output preserves the full sub-numbered ID, including the colon."""
    heading = StoryHeading(story_id="J.m.1", title="v0.70.0 Follow-up after J.m")
    assert derive_commit_message(heading) == "J.m.1: v0.70.0 Follow-up after J.m"


def test_derive_commit_message_round_trip_with_cli_subject_regex():
    """The commit-subject already-committed check (cli._COMMIT_SUBJECT_STORY_ID_RE)
    must recognize the sub-numbered ID it would produce from our own
    `derive_commit_message`. Without this, a J.m.1 commit subject would
    not register in the "committed" set, breaking the wrapper's
    duplicate-detection path even after the stories.md side is fixed.
    """
    from project_guide.cli import _COMMIT_SUBJECT_STORY_ID_RE

    subject = derive_commit_message(
        StoryHeading(story_id="J.m.1", title="v0.70.0 Follow-up after J.m")
    )
    m = _COMMIT_SUBJECT_STORY_ID_RE.match(subject)
    assert m is not None, f"regex failed to match subject: {subject!r}"
    assert m.group(1) == "J.m.1"
