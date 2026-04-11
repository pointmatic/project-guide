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

import importlib.resources
from pathlib import Path

import pytest

from project_guide.actions import (
    ActionType,
    ArchiveResult,
    Artifact,
    detect_latest_phase_letter,
    detect_latest_version,
    extract_future_section,
    perform_archive,
    render_fresh_stories_artifact,
)
from project_guide.exceptions import ActionError, MetadataError

# ---------------------------------------------------------------------------
# ActionType enum
# ---------------------------------------------------------------------------


def test_action_type_members():
    assert {a.value for a in ActionType} == {"create", "modify", "archive"}


def test_action_type_is_string_subclass():
    """StrEnum: members compare equal to their string values."""
    assert ActionType.CREATE == "create"
    assert ActionType.MODIFY == "modify"
    assert ActionType.ARCHIVE == "archive"
    assert str(ActionType.ARCHIVE) == "archive"
    # Construction from string
    assert ActionType("archive") is ActionType.ARCHIVE


def test_action_type_rejects_unknown_value():
    with pytest.raises(ValueError):
        ActionType("arhive")  # typo


# ---------------------------------------------------------------------------
# Artifact dataclass
# ---------------------------------------------------------------------------


def test_artifact_from_dict_full():
    a = Artifact.from_dict(
        {"file": "docs/specs/stories.md", "action": "archive"},
        mode_name="archive_stories",
        index=0,
    )
    assert a.file == "docs/specs/stories.md"
    assert a.action is ActionType.ARCHIVE
    assert a.webpage is None
    assert a.framework is None


def test_artifact_from_dict_no_action():
    """Artifacts without an `action:` field are tolerated."""
    a = Artifact.from_dict({"file": "docs/specs/new-phase.md"}, mode_name="plan_phase", index=0)
    assert a.file == "docs/specs/new-phase.md"
    assert a.action is None


def test_artifact_from_dict_webpage_target():
    a = Artifact.from_dict(
        {"webpage": "docs/site/index.md", "action": "create"},
        mode_name="document_landing",
        index=0,
    )
    assert a.webpage == "docs/site/index.md"
    assert a.file is None
    assert a.action is ActionType.CREATE


def test_artifact_from_dict_framework_target():
    a = Artifact.from_dict(
        {"framework": "mkdocs", "action": "create"},
        mode_name="document_landing",
        index=1,
    )
    assert a.framework == "mkdocs"
    assert a.action is ActionType.CREATE


def test_artifact_from_dict_rejects_unknown_action():
    with pytest.raises(MetadataError, match="unknown action 'arhive'"):
        Artifact.from_dict(
            {"file": "x.md", "action": "arhive"},
            mode_name="mode_a",
            index=0,
        )


def test_artifact_from_dict_rejects_non_mapping():
    with pytest.raises(MetadataError, match="must be a mapping"):
        Artifact.from_dict("not a dict", mode_name="mode_a", index=0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# detect_latest_version
# ---------------------------------------------------------------------------


def test_detect_latest_version_single_story():
    text = "### Story A.a: v0.1.0 Hello World [Done]\n"
    assert detect_latest_version(text) == (0, 1, 0)


def test_detect_latest_version_multiple_stories_picks_highest():
    text = (
        "### Story A.a: v0.1.0 First [Done]\n\n"
        "### Story A.b: v0.2.3 Second [Done]\n\n"
        "### Story B.a: v1.10.0 Third [Done]\n\n"
        "### Story B.b: v0.9.9 Fourth [Done]\n"
    )
    # v1.10.0 > v0.9.9 (numeric, not lexical)
    assert detect_latest_version(text) == (1, 10, 0)


def test_detect_latest_version_ignores_non_story_versions():
    text = (
        "The spec mentions v99.99.99 in prose, which should NOT match.\n\n"
        "### Story A.a: v0.1.0 Hello [Done]\n"
    )
    assert detect_latest_version(text) == (0, 1, 0)


def test_detect_latest_version_raises_when_none_found():
    text = "## Phase A: Foundation\n\nJust some prose, no stories.\n"
    with pytest.raises(ActionError, match="No versioned story headings"):
        detect_latest_version(text)


# ---------------------------------------------------------------------------
# detect_latest_phase_letter
# ---------------------------------------------------------------------------


def test_detect_latest_phase_letter_single_phase():
    text = "## Phase A: Foundation\n"
    assert detect_latest_phase_letter(text) == "A"


def test_detect_latest_phase_letter_multiple_phases_picks_highest():
    text = (
        "## Phase A: Foundation\n\n"
        "## Phase B: Core\n\n"
        "## Phase C: Polish\n"
    )
    assert detect_latest_phase_letter(text) == "C"


def test_detect_latest_phase_letter_base26_ordering_post_z():
    """Z < AA < AB < ZZ < AAA (length-then-lex)."""
    text = (
        "## Phase Y: Alpha\n\n"
        "## Phase Z: Beta\n\n"
        "## Phase AA: Gamma\n\n"
        "## Phase AB: Delta\n"
    )
    # AA and AB are both 2 letters, so AB is highest; A/Y/Z are single-letter
    assert detect_latest_phase_letter(text) == "AB"


def test_detect_latest_phase_letter_single_letter_beats_nothing():
    """Z alone beats no multi-letter phases."""
    text = "## Phase A: One\n\n## Phase Z: Final\n"
    assert detect_latest_phase_letter(text) == "Z"


def test_detect_latest_phase_letter_triple_letter_beats_double():
    text = "## Phase ZZ: Big\n\n## Phase AAA: Bigger\n"
    assert detect_latest_phase_letter(text) == "AAA"


def test_detect_latest_phase_letter_raises_when_none_found():
    with pytest.raises(ActionError, match="No phase headings"):
        detect_latest_phase_letter("# Just a heading, no phases\n")


# ---------------------------------------------------------------------------
# extract_future_section
# ---------------------------------------------------------------------------


def test_extract_future_section_present_with_content():
    text = (
        "## Phase A: Foundation\n\n"
        "### Story A.a: v0.1.0 Hello [Done]\n\n"
        "---\n\n"
        "## Future\n\n"
        "### Deferred Thing\n\nSome content.\n"
    )
    section = extract_future_section(text)
    assert section.startswith("## Future")
    assert "Deferred Thing" in section
    assert "Some content." in section
    # The phases should NOT be in the extracted section
    assert "Phase A" not in section


def test_extract_future_section_absent_returns_empty():
    text = "## Phase A: Foundation\n\n### Story A.a: v0.1.0 Hello [Done]\n"
    assert extract_future_section(text) == ""


def test_extract_future_section_heading_only_no_content():
    text = "## Phase A: Foundation\n\n## Future\n"
    section = extract_future_section(text)
    assert section.strip() == "## Future"


# ---------------------------------------------------------------------------
# render_fresh_stories_artifact
# ---------------------------------------------------------------------------


def _bundled_stories_template() -> Path:
    """Return the path to the bundled stories.md artifact template."""
    ref = importlib.resources.files("project_guide.templates").joinpath(
        "project-guide/templates/artifacts/stories.md"
    )
    with importlib.resources.as_file(ref) as path:
        return Path(path)


def test_render_fresh_stories_artifact_preserves_default_future_when_empty():
    """With no carried future section, the template's default Future block is kept."""
    template = _bundled_stories_template()
    rendered = render_fresh_stories_artifact(
        template,
        {"project_name": "demo", "programming_language": "Python"},
    )
    assert "demo" in rendered
    assert "## Future" in rendered
    # Default template has an HTML comment explainer
    assert "<!--" in rendered
    assert "{{phases_and_stories}}" not in rendered


def test_render_fresh_stories_artifact_replaces_future_when_carried():
    """Carried future section replaces the template's default Future block verbatim."""
    template = _bundled_stories_template()
    carried = "## Future\n\n### Deferred Thing [Deferred]\n\nSpecial note.\n"
    rendered = render_fresh_stories_artifact(
        template,
        {"project_name": "demo", "programming_language": "Python"},
        future_section=carried,
    )
    assert "## Future" in rendered
    assert "Deferred Thing" in rendered
    assert "Special note." in rendered
    # Default template's HTML-comment explainer is replaced, not appended
    assert "<!--" not in rendered


# ---------------------------------------------------------------------------
# perform_archive — integration-ish tests against a tmp copy
# ---------------------------------------------------------------------------


def _make_fixture_stories(tmp_path: Path, content: str) -> Path:
    stories = tmp_path / "stories.md"
    stories.write_text(content, encoding="utf-8")
    return stories


FIXTURE_MINIMAL = """\
# stories.md -- demo (Python)

---

## Phase A: Foundation

### Story A.a: v0.1.0 Hello [Done]

- [x] Print hello

### Story A.b: v0.2.0 Goodbye [Done]

- [x] Print goodbye

## Future

### Deferred Feature

Something to do later.
"""


def test_perform_archive_happy_path(tmp_path):
    source = _make_fixture_stories(tmp_path, FIXTURE_MINIMAL)
    template = _bundled_stories_template()

    result = perform_archive(
        source,
        template,
        {"project_name": "demo", "programming_language": "Python"},
    )

    assert isinstance(result, ArchiveResult)
    assert result.version == "v0.2.0"
    assert result.phase_letter == "A"
    assert result.future_carried is True

    # Archive location and content
    archived = tmp_path / ".archive" / "stories-v0.2.0.md"
    assert archived.exists()
    assert archived.read_text(encoding="utf-8") == FIXTURE_MINIMAL
    assert result.archived_to == archived

    # Fresh source: empty body, Future section carried verbatim
    assert source.exists()
    fresh = source.read_text(encoding="utf-8")
    assert "## Phase A" not in fresh
    assert "Story A.a" not in fresh
    assert "## Future" in fresh
    assert "Deferred Feature" in fresh
    assert "Something to do later." in fresh
    assert "{{phases_and_stories}}" not in fresh


def test_perform_archive_no_future_section_uses_template_default(tmp_path):
    content = FIXTURE_MINIMAL.split("## Future")[0].rstrip() + "\n"
    source = _make_fixture_stories(tmp_path, content)
    template = _bundled_stories_template()

    result = perform_archive(
        source,
        template,
        {"project_name": "demo", "programming_language": "Python"},
    )

    assert result.future_carried is False
    fresh = source.read_text(encoding="utf-8")
    # Template default Future block (with HTML-comment explainer) is used
    assert "## Future" in fresh
    assert "<!--" in fresh


def test_perform_archive_raises_when_source_missing(tmp_path):
    missing = tmp_path / "does-not-exist.md"
    template = _bundled_stories_template()
    with pytest.raises(ActionError, match="Source file not found"):
        perform_archive(missing, template, {"project_name": "demo", "programming_language": "Python"})


def test_perform_archive_raises_when_target_already_exists(tmp_path):
    source = _make_fixture_stories(tmp_path, FIXTURE_MINIMAL)
    archive_dir = tmp_path / ".archive"
    archive_dir.mkdir()
    # Pre-create the archive target to force a collision
    (archive_dir / "stories-v0.2.0.md").write_text("pre-existing", encoding="utf-8")

    template = _bundled_stories_template()
    with pytest.raises(ActionError, match="Archive target already exists"):
        perform_archive(source, template, {"project_name": "demo", "programming_language": "Python"})

    # Source must remain untouched on the failure path
    assert source.read_text(encoding="utf-8") == FIXTURE_MINIMAL


def test_perform_archive_raises_when_template_missing(tmp_path):
    source = _make_fixture_stories(tmp_path, FIXTURE_MINIMAL)
    bogus_template = tmp_path / "nope.md"
    with pytest.raises(ActionError, match="Artifact template not found"):
        perform_archive(source, bogus_template, {"project_name": "demo", "programming_language": "Python"})

    # Source remains untouched on pre-check failures
    assert source.read_text(encoding="utf-8") == FIXTURE_MINIMAL


def test_perform_archive_raises_when_no_versions_in_source(tmp_path):
    content = "## Phase A: Foundation\n\nNo versioned stories here.\n"
    source = _make_fixture_stories(tmp_path, content)
    template = _bundled_stories_template()
    with pytest.raises(ActionError, match="No versioned story headings"):
        perform_archive(source, template, {"project_name": "demo", "programming_language": "Python"})

    # Source remains untouched on pre-check failures
    assert source.read_text(encoding="utf-8") == content


# ---------------------------------------------------------------------------
# Round-trip against the real Phase J archive fixture
# ---------------------------------------------------------------------------


def test_perform_archive_round_trip_against_phase_j_fixture(tmp_path):
    """
    Archive a copy of the real Phase J stories.md (stories-v2.0.20.md in .archive).
    The archived file must byte-match the original source, and the fresh source
    must contain the carried Future section.
    """
    repo_root = Path(__file__).resolve().parent.parent
    fixture_src = repo_root / "docs" / "specs" / ".archive" / "stories-v2.0.20.md"
    if not fixture_src.exists():
        pytest.skip(f"Phase J fixture not present: {fixture_src}")

    original = fixture_src.read_text(encoding="utf-8")
    source = tmp_path / "stories.md"
    source.write_text(original, encoding="utf-8")

    template = _bundled_stories_template()
    result = perform_archive(
        source,
        template,
        {"project_name": "project-guide", "programming_language": "Python"},
    )

    assert result.version == "v2.0.20"
    assert result.phase_letter == "J"
    assert result.future_carried is True

    archived = tmp_path / ".archive" / "stories-v2.0.20.md"
    assert archived.exists()
    assert archived.read_text(encoding="utf-8") == original

    fresh = source.read_text(encoding="utf-8")
    assert "## Phase J" not in fresh
    assert "## Future" in fresh
    # The Phase J Future section had specific deferred-story content
    assert "Deferred" in fresh
