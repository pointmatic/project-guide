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
End-to-end integration tests for the archive_stories mode (Story K.d).

These tests exercise the full pipeline:
  1. `project-guide init` — scaffolds a fresh project with bundled templates
  2. `project-guide mode archive_stories` — sets the mode and renders go.md
  3. `project-guide archive-stories` — runs the deterministic archive action

The fixture is the real Phase J stories.md (`docs/specs/.archive/stories-v2.0.20.md`)
copied into the isolated filesystem so the round-trip reflects real content.
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from project_guide.cli import main

FIXTURE_STORIES = """\
# stories.md -- demo-project (Python)

This document breaks the demo-project project into phases.

---

## Phase A: Foundation

### Story A.a: v0.1.0 Hello World [Done]

- [x] Print hello

### Story A.b: v0.2.0 Goodbye [Done]

- [x] Print goodbye

## Phase B: Core

### Story B.a: v1.0.0 First release [Done]

- [x] Ship it

## Future

### Deferred Thing [Deferred]

Something to do later.
"""


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def initialized_project(runner, tmp_path):
    """
    Yield an initialized project directory with a fixture stories.md in place.
    Uses `runner.isolated_filesystem` so cwd is the temp dir for the duration.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init", "--project-name", "demo-project"])
        assert result.exit_code == 0, f"init failed: {result.output}"

        specs = Path("docs/specs")
        specs.mkdir(parents=True, exist_ok=True)
        stories = specs / "stories.md"
        stories.write_text(FIXTURE_STORIES, encoding="utf-8")

        yield stories


# ---------------------------------------------------------------------------
# Mode template rendering
# ---------------------------------------------------------------------------


def test_archive_stories_mode_renders(runner, initialized_project):
    """
    `project-guide mode archive_stories` sets the mode and renders a go.md
    that contains the step-by-step instructions plus the phase-letter include.
    """
    result = runner.invoke(main, ["mode", "archive_stories"])
    assert result.exit_code == 0, result.output
    assert "Mode set: archive_stories" in result.output

    go = Path("docs/project-guide/go.md").read_text(encoding="utf-8")
    # Mode-specific content
    assert "Archive the completed" in go
    assert "project-guide archive-stories" in go
    # Shared phase letters include (from K.b) is pulled in
    assert "## Phase and Story ID Scheme" in go
    # Next mode suggestion
    assert "plan_phase" in go


def test_archive_stories_mode_prereq_warning(runner, tmp_path):
    """
    If `docs/specs/stories.md` does not yet exist, the mode command still
    succeeds but prints a 'Prerequisites not yet met' warning.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0

        result = runner.invoke(main, ["mode", "archive_stories"])
        assert result.exit_code == 0
        assert "Prerequisites not yet met" in result.output
        assert "docs/specs/stories.md" in result.output


# ---------------------------------------------------------------------------
# archive-stories CLI command — happy path
# ---------------------------------------------------------------------------


def test_archive_stories_cli_happy_path(runner, initialized_project):
    """
    After `mode archive_stories`, running `archive-stories` moves the source
    to .archive/ and re-renders a fresh stories.md with the Future section
    carried over verbatim.
    """
    stories = initialized_project

    result = runner.invoke(main, ["mode", "archive_stories"])
    assert result.exit_code == 0

    result = runner.invoke(main, ["archive-stories"])
    assert result.exit_code == 0, result.output
    assert "Archived stories.md" in result.output
    assert "v1.0.0" in result.output
    assert "Last phase:" in result.output
    assert "B" in result.output  # Phase B was the last phase in the fixture
    assert "carried from source" in result.output

    archived = Path("docs/specs/.archive/stories-v1.0.0.md")
    assert archived.exists()
    # The archived file must match the original byte-for-byte
    assert archived.read_text(encoding="utf-8") == FIXTURE_STORIES

    # Fresh stories.md: empty body, carried Future section, header preserved
    fresh = stories.read_text(encoding="utf-8")
    assert "## Phase A" not in fresh
    assert "## Phase B" not in fresh
    assert "Story A.a" not in fresh
    assert "## Future" in fresh
    assert "Deferred Thing" in fresh
    # Header extraction populated project_name/programming_language — no
    # leftover Jinja placeholders in the fresh output
    assert "{{" not in fresh
    assert "demo-project" in fresh


def test_archive_stories_cli_no_future_section(runner, tmp_path):
    """
    Archive succeeds when the source has no `## Future` section, falling back
    to the template's default Future block.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0

        specs = Path("docs/specs")
        specs.mkdir(parents=True, exist_ok=True)
        content = FIXTURE_STORIES.split("## Future")[0].rstrip() + "\n"
        stories = specs / "stories.md"
        stories.write_text(content, encoding="utf-8")

        result = runner.invoke(main, ["archive-stories"])
        assert result.exit_code == 0, result.output
        assert "template default" in result.output

        fresh = stories.read_text(encoding="utf-8")
        assert "## Future" in fresh
        # The default Future block in the bundled template has an HTML-comment
        # explainer — confirms the template default was used, not a carryover.
        assert "<!--" in fresh


# ---------------------------------------------------------------------------
# archive-stories CLI command — error paths
# ---------------------------------------------------------------------------


def test_archive_stories_cli_no_config(runner, tmp_path):
    """Fails cleanly when no .project-guide.yml is present."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["archive-stories"])
        assert result.exit_code != 0
        assert "No .project-guide.yml found" in result.output


def test_archive_stories_cli_source_missing(runner, tmp_path):
    """Fails cleanly when stories.md does not exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0

        result = runner.invoke(main, ["archive-stories"])
        assert result.exit_code != 0
        assert "Source file not found" in result.output


def test_archive_stories_cli_target_already_exists(runner, initialized_project):
    """
    If an archive target already exists, the command errors and leaves the
    source untouched (exercising the pre-check before `shutil.move`).
    """
    stories = initialized_project

    archive_dir = Path("docs/specs/.archive")
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "stories-v1.0.0.md").write_text("pre-existing", encoding="utf-8")

    result = runner.invoke(main, ["archive-stories"])
    assert result.exit_code != 0
    assert "already exists" in result.output
    # Source must remain untouched
    assert stories.read_text(encoding="utf-8") == FIXTURE_STORIES
    # Pre-existing archive target must remain untouched
    assert (archive_dir / "stories-v1.0.0.md").read_text(encoding="utf-8") == "pre-existing"


def test_archive_stories_cli_no_versioned_stories(runner, tmp_path):
    """
    If stories.md exists but has no versioned story headings, the command
    errors cleanly without mutating anything.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0

        specs = Path("docs/specs")
        specs.mkdir(parents=True, exist_ok=True)
        stories = specs / "stories.md"
        no_versions = "## Phase A: Foundation\n\nNo stories yet.\n"
        stories.write_text(no_versions, encoding="utf-8")

        result = runner.invoke(main, ["archive-stories"])
        assert result.exit_code != 0
        assert "No versioned story headings" in result.output
        # Source must remain untouched
        assert stories.read_text(encoding="utf-8") == no_versions
        # No .archive/ created on failure
        assert not Path("docs/specs/.archive").exists()
