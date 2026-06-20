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
    derive_bundle_commit_message,
    derive_commit_message,
    parse_committed_ids_from_subject,
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


def test_story_re_matches_h4_and_h5_headings():
    """Story Q.v: headings at `####` and `#####` depth parse identically to
    `###`. The colon after the ID stays required (example-3's colon-less form
    was a typo, not a supported shape)."""
    h4 = "#### Story A.c: v0.1.2 Bar [Planned]\n"
    h5 = "##### Story A.c.1: Baz [Planned]\n"
    assert _STORY_RE.findall(h4) == [("A.c", "v0.1.2 Bar", "Planned")]
    assert _STORY_RE.findall(h5) == [("A.c.1", "Baz", "Planned")]


def test_story_re_rejects_out_of_range_heading_depths():
    """Story Q.v: only `###`/`####`/`#####` are story depths. `##` is the
    phase level (too shallow) and `######` is too deep — neither is a story."""
    h2 = "## Story X.y: too shallow [Done]\n"
    h6 = "###### Story X.y: too deep [Done]\n"
    assert _STORY_RE.findall(h2) == []
    assert _STORY_RE.findall(h6) == []


def test_story_re_still_requires_colon():
    """Story Q.v: the colon after the ID remains mandatory at every depth —
    a colon-less heading is not recognized."""
    no_colon = "##### Story A.c.1 Baz [Planned]\n"
    assert _STORY_RE.findall(no_colon) == []


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
            "### Story J.l: update remaining refs [Done]\n\n- [x] done\n\n"
            "### Story J.m: v0.69.0 Integrate component [Done]\n\n- [x] done\n\n"
            "### Story J.m.1: v0.70.0 Follow-up after J.m [Done]\n\n- [x] done\n"
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
            "### Story J.l: update remaining refs [Done]\n\n- [x] done\n\n"
            "### Story J.m.1: v0.69.0 First half of the split [Done]\n\n- [x] done\n\n"
            "### Story J.m.2: v0.70.0 Second half of the split [Done]\n\n- [x] done\n"
        ),
    )
    headings = _read_done_stories(str(specs))
    assert headings is not None
    assert [h.story_id for h in headings] == ["J.l", "J.m.1", "J.m.2"]
    assert headings[-1].story_id == "J.m.2"


def test_read_done_stories_recognizes_deeper_heading_levels(tmp_path):
    """Story Q.v: a `### Story` group header followed by `#####` children is
    parsed so that (a) all three depths are recognized as stories and (b) the
    parent's body ends at the first child heading — so a checklist-less parent
    reads as a header while each child's own checklist governs its is_header.
    Without the body-boundary breaking on the deeper heading, the parent would
    swallow the children's checklists and wrongly read as a real story."""
    specs = _write(
        tmp_path,
        (
            "### Story J.m: Group overview [Done]\n\n"
            "Prose only, no checklist.\n\n"
            "##### Story J.m.1: First child [Done]\n\n- [x] done\n\n"
            "##### Story J.m.2: Second child [Done]\n\n- [x] done\n"
        ),
    )
    headings = _read_done_stories(str(specs))
    assert headings is not None
    assert [h.story_id for h in headings] == ["J.m", "J.m.1", "J.m.2"]
    # Parent's (correctly bounded) body has no checklist → header.
    assert headings[0].is_header is True
    # Children carry their own checklists → real stories.
    assert headings[1].is_header is False
    assert headings[2].is_header is False


# ---------------------------------------------------------------------------
# derive_commit_message — round-trip with the cli's commit-subject regex
# ---------------------------------------------------------------------------


def test_derive_commit_message_with_sub_numbered_id():
    """Output preserves the full sub-numbered ID, including the colon."""
    heading = StoryHeading(story_id="J.m.1", title="v0.70.0 Follow-up after J.m")
    assert derive_commit_message(heading) == "J.m.1: v0.70.0 Follow-up after J.m"


def test_derive_commit_message_round_trip_with_subject_parser():
    """The commit-subject already-committed check (parse_committed_ids_from_subject)
    must recognize the sub-numbered ID it would produce from our own
    `derive_commit_message`. Without this, a J.m.1 commit subject would
    not register in the "committed" set, breaking the wrapper's
    duplicate-detection path even after the stories.md side is fixed.
    """
    subject = derive_commit_message(
        StoryHeading(story_id="J.m.1", title="v0.70.0 Follow-up after J.m")
    )
    assert parse_committed_ids_from_subject(subject) == ["J.m.1"]


# ---------------------------------------------------------------------------
# parse_committed_ids_from_subject — Story P.u multi-ID parser
# ---------------------------------------------------------------------------


def test_parse_subject_single_bare():
    assert parse_committed_ids_from_subject("A.a: v0.1.0 Hello World") == ["A.a"]


def test_parse_subject_single_bare_no_version():
    assert parse_committed_ids_from_subject("M.c: align specs with FR-9") == ["M.c"]


def test_parse_subject_single_storied_legacy():
    """P.s legacy form: `Story <id>: ...`."""
    assert parse_committed_ids_from_subject(
        "Story J.m.2: v0.71.0 — refactor"
    ) == ["J.m.2"]


def test_parse_subject_single_subnumbered():
    """P.m sub-numbered IDs continue to parse."""
    assert parse_committed_ids_from_subject(
        "J.m.1: v0.70.0 Follow-up"
    ) == ["J.m.1"]


def test_parse_subject_rejects_single_id_without_colon():
    """Disambiguation rule preserved from P.s: single ID without `:` is not
    a story commit (prevents `Story J.m.2 some text` from matching)."""
    assert parse_committed_ids_from_subject("Story J.m.2 some other text") == []
    assert parse_committed_ids_from_subject("A.a Hello World") == []


def test_parse_subject_rejects_non_story_prefixes():
    """`Fix`/`Feat`/etc. prefixes are not absorbed by the optional `Story` group."""
    assert parse_committed_ids_from_subject("Fix J.m.2: something") == []
    assert parse_committed_ids_from_subject("Feat A.a: hello") == []


def test_parse_subject_rejects_garbage():
    assert parse_committed_ids_from_subject("") == []
    assert parse_committed_ids_from_subject("Image corruption features planning") == []
    assert parse_committed_ids_from_subject("commit 48c05090af3471d61fd0918962656c05a8a71776") == []


def test_parse_subject_bundle_legacy_no_colons():
    """Legacy bundled subject with no colons at all (real-world field example)."""
    assert parse_committed_ids_from_subject(
        "H.a, H.b, H.c InputSource sidecar labels + flat-image layout"
    ) == ["H.a", "H.b", "H.c"]


def test_parse_subject_bundle_canonical_unversioned():
    assert parse_committed_ids_from_subject(
        "H.a, H.b, H.c: Foo bar bing baz"
    ) == ["H.a", "H.b", "H.c"]


def test_parse_subject_bundle_all_versioned():
    assert parse_committed_ids_from_subject(
        "H.j: v0.10.0, H.k: v0.11.0 sample_per_class filter"
    ) == ["H.j", "H.k"]


def test_parse_subject_bundle_mixed_versions():
    assert parse_committed_ids_from_subject(
        "H.a, H.b: v1.2.3, H.c: Foo bar bing baz"
    ) == ["H.a", "H.b", "H.c"]


def test_parse_subject_bundle_single_trailing_version():
    """Single shared version covering bare IDs (valid on parse; not formatter-emitted)."""
    assert parse_committed_ids_from_subject(
        "H.a, H.b, H.c: v1.2.3 Foo bar bing baz"
    ) == ["H.a", "H.b", "H.c"]


def test_parse_subject_bundle_storied_prefix():
    """`Story ` prefix tolerated on bundles too."""
    assert parse_committed_ids_from_subject(
        "Story H.a, H.b, H.c InputSource sidecar"
    ) == ["H.a", "H.b", "H.c"]


def test_parse_subject_bundle_subnumbered_ids():
    assert parse_committed_ids_from_subject(
        "J.m.1, J.m.2 split work"
    ) == ["J.m.1", "J.m.2"]


# ---------------------------------------------------------------------------
# derive_bundle_commit_message — Story P.u bundle formatter
# ---------------------------------------------------------------------------


def test_derive_bundle_all_versionless():
    headings = [
        StoryHeading(story_id="H.a", title="InputSource sidecar labels"),
        StoryHeading(story_id="H.b", title="flat-image layout"),
        StoryHeading(story_id="H.c", title="InputSource partitions"),
    ]
    assert derive_bundle_commit_message(headings) == (
        "H.a, H.b, H.c: InputSource sidecar labels + flat-image layout + InputSource partitions"
    )


def test_derive_bundle_all_versioned():
    headings = [
        StoryHeading(story_id="H.j", title="v0.10.0 sample_per_class filter"),
        StoryHeading(story_id="H.k", title="v0.11.0 sample_per_class_fractional filter"),
    ]
    # Last token already ends with ": <ver>", so no extra colon before title.
    assert derive_bundle_commit_message(headings) == (
        "H.j: v0.10.0, H.k: v0.11.0 sample_per_class filter + sample_per_class_fractional filter"
    )


def test_derive_bundle_mixed_versions():
    headings = [
        StoryHeading(story_id="H.a", title="Foo"),
        StoryHeading(story_id="H.b", title="v1.2.3 Bar"),
        StoryHeading(story_id="H.c", title="Baz"),
    ]
    assert derive_bundle_commit_message(headings) == (
        "H.a, H.b: v1.2.3, H.c: Foo + Bar + Baz"
    )


def test_derive_bundle_sanitizes_backticks_and_double_quotes():
    headings = [
        StoryHeading(story_id="A.a", title='New command `foo`'),
        StoryHeading(story_id="A.b", title='Said "hello"'),
    ]
    assert derive_bundle_commit_message(headings) == (
        "A.a, A.b: New command 'foo' + Said 'hello'"
    )


def test_derive_bundle_preserves_plus_inside_titles():
    """`+` inside an individual title passes through (not escaped)."""
    headings = [
        StoryHeading(story_id="A.a", title="A + B feature"),
        StoryHeading(story_id="A.b", title="cleanup"),
    ]
    assert derive_bundle_commit_message(headings) == (
        "A.a, A.b: A + B feature + cleanup"
    )


def test_derive_bundle_trims_and_collapses_whitespace():
    """Leading/trailing whitespace stripped; internal whitespace runs collapsed."""
    headings = [
        StoryHeading(story_id="A.a", title="   multi    space   title   "),
        StoryHeading(story_id="A.b", title="\t tabby \t title \t"),
    ]
    assert derive_bundle_commit_message(headings) == (
        "A.a, A.b: multi space title + tabby title"
    )


def test_derive_bundle_round_trips_with_parser_unversioned():
    headings = [
        StoryHeading(story_id="A.a", title="first"),
        StoryHeading(story_id="A.b", title="second"),
    ]
    msg = derive_bundle_commit_message(headings)
    assert parse_committed_ids_from_subject(msg) == ["A.a", "A.b"]


def test_derive_bundle_round_trips_with_parser_versioned():
    headings = [
        StoryHeading(story_id="A.a", title="v0.1.0 first"),
        StoryHeading(story_id="A.b", title="v0.2.0 second"),
    ]
    msg = derive_bundle_commit_message(headings)
    assert parse_committed_ids_from_subject(msg) == ["A.a", "A.b"]


# ---------------------------------------------------------------------------
# is_header detection — Story P.v
# ---------------------------------------------------------------------------


def test_is_header_true_when_body_has_no_checklist_items(tmp_path):
    """A [Done] story with prose-only body (no `- [ ]`, no `- [x]`) is a header."""
    specs = _write(
        tmp_path,
        (
            "### Story H.m: Group overview [Done]\n\n"
            "This is the umbrella story for H.m.1 / H.m.2 / H.m.3. See each "
            "child for actual task lists.\n\n"
            "### Story H.m.1: Real work [Done]\n\n- [x] task\n"
        ),
    )
    headings = _read_done_stories(str(specs))
    assert headings is not None
    by_id = {h.story_id: h for h in headings}
    assert by_id["H.m"].is_header is True
    assert by_id["H.m.1"].is_header is False


def test_is_header_false_when_body_has_unchecked_items(tmp_path):
    """Per Q3 (forgiving rule): a [Done] story with all unchecked items is
    NOT a header — it is a misflagged real story. Header signal requires
    *zero* checklist items, not "zero checked items"."""
    specs = _write(
        tmp_path,
        (
            "### Story A.a: Some real work [Done]\n\n"
            "- [ ] forgot to flip this\n"
            "- [ ] also forgot this\n"
        ),
    )
    headings = _read_done_stories(str(specs))
    assert headings is not None
    assert headings[0].is_header is False


def test_is_header_false_when_body_has_mixed_checklist(tmp_path):
    """Standard real-story shape with a mix of `[x]` and `[ ]` items."""
    specs = _write(
        tmp_path,
        (
            "### Story A.a: Partial story [Done]\n\n"
            "- [x] done part\n"
            "- [ ] still TODO\n"
        ),
    )
    headings = _read_done_stories(str(specs))
    assert headings is not None
    assert headings[0].is_header is False


def test_is_header_respects_story_body_boundaries(tmp_path):
    """A header followed immediately by a child story with `[x]` items must
    not borrow the child's checklist — the body of H.m ends at H.m.1's heading."""
    specs = _write(
        tmp_path,
        (
            "### Story H.m: Header only [Done]\n"
            "### Story H.m.1: Child has tasks [Done]\n\n- [x] task\n"
        ),
    )
    headings = _read_done_stories(str(specs))
    assert headings is not None
    by_id = {h.story_id: h for h in headings}
    assert by_id["H.m"].is_header is True
    assert by_id["H.m.1"].is_header is False


def test_is_header_counts_indented_checklist_items(tmp_path):
    """Indented checklist items (nested under a parent task) count toward the
    has-checklist test — they are still real work signals, not header signals."""
    specs = _write(
        tmp_path,
        (
            "### Story A.a: Nested tasks only [Done]\n\n"
            "  - [x] indented sub-task\n"
        ),
    )
    headings = _read_done_stories(str(specs))
    assert headings is not None
    assert headings[0].is_header is False


def test_is_header_respects_phase_boundary(tmp_path):
    """A header at the end of one phase must not borrow checklist items from
    the first story of the next phase. The body ends at the `## Phase` line."""
    specs = _write(
        tmp_path,
        (
            "### Story H.m: Header only [Done]\n\n"
            "Prose overview, no tasks.\n\n"
            "## Phase K: Next theme\n\n"
            "### Story K.a: Real work [Done]\n\n- [x] task\n"
        ),
    )
    headings = _read_done_stories(str(specs))
    assert headings is not None
    by_id = {h.story_id: h for h in headings}
    assert by_id["H.m"].is_header is True
    assert by_id["K.a"].is_header is False
