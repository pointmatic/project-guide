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

import pytest

from project_guide.exceptions import RenderError
from project_guide.metadata import Metadata, ModeDefinition
from project_guide.render import render_go_project_guide


@pytest.fixture
def template_dir(tmp_path):
    """Create a minimal template directory for rendering tests."""
    # Templates subdirectory
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(parents=True)
    modes_dir = templates_dir / "modes"
    modes_dir.mkdir()

    # Entry point template lives inside templates/
    (templates_dir / "llm_entry_point.md").write_text(
        "# Guide\n\n{% include 'modes/_header-common.md' %}\n\n{% include mode_template %}\n"
    )

    (modes_dir / "_header-common.md").write_text(
        "Mode: {{ mode_name }} ({{ sequence_or_cycle }})\n\n---\n"
    )
    (modes_dir / "_header-sequence.md").write_text(
        "Next: `project-guide mode {{ next_mode }}`\n"
    )
    (modes_dir / "plan-concept-mode.md").write_text(
        "## Plan Concept\n\nDefine the problem.\n\n{% include 'modes/_header-sequence.md' %}\n"
    )

    return tmp_path


@pytest.fixture
def sample_mode():
    return ModeDefinition(
        name="plan_concept",
        info="Generate a concept",
        description="Define the problem and solution space.",
        sequence_or_cycle="sequence",
        mode_template="modes/plan-concept-mode.md",
        next_mode="plan_features",
    )


@pytest.fixture
def sample_metadata():
    return Metadata(common={"project_name": "test-project"}, modes=[])


def test_render_produces_output(template_dir, sample_mode, sample_metadata):
    """Test that rendering produces a file with expected content."""
    output = template_dir / "output.md"
    render_go_project_guide(template_dir, sample_mode, sample_metadata, output)

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "# Guide" in content
    assert "Mode: plan_concept (sequence)" in content
    assert "## Plan Concept" in content
    assert "Next: `project-guide mode plan_features`" in content


def test_render_includes_metadata_common_vars(template_dir, sample_mode, sample_metadata):
    """Test that common metadata variables are available in templates."""
    # Add a template that uses a common variable
    (template_dir / "templates" / "modes" / "_header-common.md").write_text(
        "Project: {{ project_name }}\n"
    )
    output = template_dir / "output.md"
    render_go_project_guide(template_dir, sample_mode, sample_metadata, output)

    content = output.read_text(encoding="utf-8")
    assert "Project: test-project" in content


def test_render_missing_templates_dir(tmp_path, sample_mode, sample_metadata):
    """Test RenderError when templates directory does not exist."""
    with pytest.raises(RenderError, match="Templates directory not found"):
        render_go_project_guide(tmp_path, sample_mode, sample_metadata, tmp_path / "out.md")


def test_render_missing_entry_point(tmp_path, sample_mode, sample_metadata):
    """Test RenderError when llm_entry_point.md template is missing."""
    (tmp_path / "templates").mkdir()
    with pytest.raises(RenderError, match="Template not found"):
        render_go_project_guide(tmp_path, sample_mode, sample_metadata, tmp_path / "out.md")


def test_render_undefined_vars_raise_render_error(template_dir, sample_mode, sample_metadata):
    """Undefined variables surface as RenderError via the post-render validator.

    Contract change in v2.3.1 (Story M.b): previously, ``_LenientUndefined``
    caused undefined variables to pass through as literal ``{{ name }}``
    strings in the rendered output. That was the *mechanism* the validator
    now detects — lenient-undefined still produces the placeholder shape,
    but the post-render validator catches it and raises ``RenderError``
    before anything is written to disk.
    """
    (template_dir / "templates" / "modes" / "plan-concept-mode.md").write_text(
        "## Concept\n\n{{ unknown_variable }}\n"
    )
    output = template_dir / "output.md"
    with pytest.raises(RenderError, match="unknown_variable"):
        render_go_project_guide(template_dir, sample_mode, sample_metadata, output)
    # Nothing should be written when the validator raises.
    assert not output.exists()


def test_render_end_to_end_with_package_templates():
    """Test rendering with actual package templates (plan_concept mode)."""
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        output = Path("docs/project-guide/go.md")
        assert output.exists()

        content = output.read_text(encoding="utf-8")
        assert "Project-Guide" in content
        assert "default" in content or "Default" in content


def _get_all_mode_names():
    """Load bundled metadata and return all mode names for parametrization."""
    import importlib.resources

    from project_guide.metadata import load_metadata

    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath(
            "project-guide/.metadata.yml"
        )
    ) as path:
        metadata = load_metadata(path)
    return metadata.list_mode_names()


def _render_artifact_stories_template(**context):
    """Render the bundled stories.md artifact template with the given context."""
    import importlib.resources

    from jinja2 import Environment, FileSystemLoader

    template_ref = importlib.resources.files("project_guide.templates").joinpath(
        "project-guide/templates/artifacts/stories.md"
    )
    with importlib.resources.as_file(template_ref) as template_path:
        env = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            keep_trailing_newline=True,
        )
        template = env.get_template(template_path.name)
        return template.render(**context)


def test_artifact_stories_template_includes_future_when_empty():
    """The stories.md artifact template renders a Future section even when phases_and_stories is empty."""
    rendered = _render_artifact_stories_template(
        project_name="test-project",
        programming_language="Python",
        phases_and_stories="",
    )
    assert "## Future" in rendered
    assert "test-project" in rendered


def test_artifact_stories_template_includes_future_when_populated():
    """The stories.md artifact template renders a Future section after populated phases."""
    phases = "## Phase A: Foundation\n\n### Story A.a: v0.1.0 Hello World [Planned]\n\n- [ ] Print hello\n"
    rendered = _render_artifact_stories_template(
        project_name="test-project",
        programming_language="Python",
        phases_and_stories=phases,
    )
    assert "## Phase A: Foundation" in rendered
    assert "## Future" in rendered
    # Future section must appear AFTER the phases content
    assert rendered.index("## Phase A") < rendered.index("## Future")


# --- Story M.a: project-essentials.md placeholder and render hook ---------


@pytest.fixture
def essentials_template_dir(tmp_path):
    """Template dir where _header-common.md renders the Project Essentials section.

    Mirrors the production ``_header-common.md`` guard so this unit-test
    fixture exercises the same Jinja2 shape as the bundled template.
    """
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(parents=True)
    modes_dir = templates_dir / "modes"
    modes_dir.mkdir()

    (templates_dir / "llm_entry_point.md").write_text(
        "# Guide\n\n{% include 'modes/_header-common.md' %}\n\n{% include mode_template %}\n"
    )

    # This is a faithful reproduction of the production guard — if anyone
    # removes the `{% if %}` in the real template, this fixture will still
    # guard, but the regression tests below running against the isolated
    # CliRunner install will catch it.
    (modes_dir / "_header-common.md").write_text(
        "Mode: {{ mode_name }}\n\n"
        "{% if project_essentials %}## Project Essentials\n\n"
        "{{ project_essentials }}\n\n---\n{% endif %}\n"
        "# {{ mode_name }} mode\n"
    )
    (modes_dir / "_header-sequence.md").write_text(
        "Next: {{ next_mode }}\n"
    )
    (modes_dir / "plan-concept-mode.md").write_text(
        "## Plan Concept\n\n{% include 'modes/_header-sequence.md' %}\n"
    )

    return tmp_path


@pytest.fixture
def essentials_metadata():
    """Minimal metadata whose common block points at a ``docs/specs`` path."""
    return Metadata(
        common={"project_name": "test-project", "spec_artifacts_path": "docs/specs"},
        modes=[],
    )


def test_project_essentials_rendered_when_file_non_empty(
    essentials_template_dir, sample_mode, essentials_metadata, monkeypatch
):
    """A populated project-essentials.md appears as a section in the rendered output."""
    monkeypatch.chdir(essentials_template_dir)
    specs_dir = Path("docs/specs")
    specs_dir.mkdir(parents=True)
    (specs_dir / "project-essentials.md").write_text(
        "- Workflow rule: use `pyve run` for runtime, `pyve test` for pytest.\n"
        "- Dogfooding: edit templates in `project_guide/templates/`, not `docs/`.\n",
        encoding="utf-8",
    )

    output = essentials_template_dir / "output.md"
    render_go_project_guide(
        essentials_template_dir, sample_mode, essentials_metadata, output
    )
    content = output.read_text(encoding="utf-8")

    assert "## Project Essentials" in content
    assert "Workflow rule: use `pyve run`" in content
    assert "Dogfooding: edit templates" in content
    # The section must appear between the header and the mode body
    assert content.index("## Project Essentials") < content.index("# plan_concept mode")


def test_project_essentials_omitted_when_file_empty(
    essentials_template_dir, sample_mode, essentials_metadata, monkeypatch
):
    """An empty project-essentials.md omits the section entirely (no blank heading)."""
    monkeypatch.chdir(essentials_template_dir)
    specs_dir = Path("docs/specs")
    specs_dir.mkdir(parents=True)
    (specs_dir / "project-essentials.md").write_text("", encoding="utf-8")

    output = essentials_template_dir / "output.md"
    render_go_project_guide(
        essentials_template_dir, sample_mode, essentials_metadata, output
    )
    content = output.read_text(encoding="utf-8")

    assert "## Project Essentials" not in content


def test_project_essentials_omitted_when_file_whitespace_only(
    essentials_template_dir, sample_mode, essentials_metadata, monkeypatch
):
    """A whitespace-only project-essentials.md is treated as empty."""
    monkeypatch.chdir(essentials_template_dir)
    specs_dir = Path("docs/specs")
    specs_dir.mkdir(parents=True)
    (specs_dir / "project-essentials.md").write_text("   \n\n\t\n", encoding="utf-8")

    output = essentials_template_dir / "output.md"
    render_go_project_guide(
        essentials_template_dir, sample_mode, essentials_metadata, output
    )
    content = output.read_text(encoding="utf-8")

    assert "## Project Essentials" not in content


def test_project_essentials_omitted_when_file_missing(
    essentials_template_dir, sample_mode, essentials_metadata, monkeypatch
):
    """No project-essentials.md at all renders cleanly with no error."""
    monkeypatch.chdir(essentials_template_dir)
    # docs/specs/ is not even created — the lookup must not raise
    output = essentials_template_dir / "output.md"
    render_go_project_guide(
        essentials_template_dir, sample_mode, essentials_metadata, output
    )
    content = output.read_text(encoding="utf-8")

    assert "## Project Essentials" not in content


def test_project_essentials_omitted_when_spec_artifacts_path_not_in_metadata(
    essentials_template_dir, sample_mode, sample_metadata, monkeypatch
):
    """Metadata without spec_artifacts_path → no file lookup, section omitted.

    This is the minimal-metadata unit-test path (matches ``sample_metadata``).
    """
    monkeypatch.chdir(essentials_template_dir)
    output = essentials_template_dir / "output.md"
    render_go_project_guide(
        essentials_template_dir, sample_mode, sample_metadata, output
    )
    content = output.read_text(encoding="utf-8")

    assert "## Project Essentials" not in content


# (The temporary `test_project_essentials_never_renders_literal_placeholder`
# regression guard from Story M.a was removed in M.b — the general
# post-render placeholder validator in `_validate_no_unrendered_placeholders`
# subsumes it. If the `{% if %}` guard on `_header-common.md` is ever
# removed, the M.b validator raises `RenderError` on every mode render
# that has no populated `project-essentials.md`, which is far louder than
# a single dedicated test.)


# --- End Story M.a tests ---------------------------------------------------


# --- Story M.b: post-render placeholder validator --------------------------


def test_validator_raises_on_single_undefined_variable(
    template_dir, sample_mode, sample_metadata
):
    """Rendering a template with one undefined variable raises RenderError."""
    (template_dir / "templates" / "modes" / "plan-concept-mode.md").write_text(
        "## Concept\n\n{{ typoed_variable }}\n"
    )
    output = template_dir / "output.md"
    with pytest.raises(RenderError) as excinfo:
        render_go_project_guide(template_dir, sample_mode, sample_metadata, output)
    assert "typoed_variable" in str(excinfo.value)
    assert "Unrendered placeholder" in str(excinfo.value)


def test_validator_error_message_lists_all_offenders(
    template_dir, sample_mode, sample_metadata
):
    """The error message names every distinct offending placeholder."""
    (template_dir / "templates" / "modes" / "plan-concept-mode.md").write_text(
        "## Concept\n\n{{ alpha }}\n{{ beta }}\n{{ gamma }}\n"
    )
    output = template_dir / "output.md"
    with pytest.raises(RenderError) as excinfo:
        render_go_project_guide(template_dir, sample_mode, sample_metadata, output)
    message = str(excinfo.value)
    assert "alpha" in message
    assert "beta" in message
    assert "gamma" in message


def test_validator_deduplicates_repeated_offenders(
    template_dir, sample_mode, sample_metadata
):
    """Repeated offenders appear once in the error message, in first-occurrence order."""
    (template_dir / "templates" / "modes" / "plan-concept-mode.md").write_text(
        "## Concept\n\n"
        "{{ first }}\n{{ second }}\n{{ first }}\n{{ second }}\n{{ first }}\n"
    )
    output = template_dir / "output.md"
    with pytest.raises(RenderError) as excinfo:
        render_go_project_guide(template_dir, sample_mode, sample_metadata, output)
    message = str(excinfo.value)
    # Dedup: each name appears exactly once in the message
    assert message.count("first") == 1
    assert message.count("second") == 1
    # First-occurrence order preserved
    assert message.index("first") < message.index("second")


def test_validator_error_message_includes_fix_hint(
    template_dir, sample_mode, sample_metadata
):
    """The error message points at the two most common causes."""
    (template_dir / "templates" / "modes" / "plan-concept-mode.md").write_text(
        "{{ some_missing_var }}\n"
    )
    output = template_dir / "output.md"
    with pytest.raises(RenderError) as excinfo:
        render_go_project_guide(template_dir, sample_mode, sample_metadata, output)
    message = str(excinfo.value)
    assert "render.py context variables" in message
    assert "template variable spellings" in message


def test_validator_does_not_write_output_on_failure(
    template_dir, sample_mode, sample_metadata
):
    """When the validator raises, the output file must not be created."""
    (template_dir / "templates" / "modes" / "plan-concept-mode.md").write_text(
        "{{ will_not_render }}\n"
    )
    output = template_dir / "output.md"
    # Pre-condition: the output file does not exist yet
    assert not output.exists()
    with pytest.raises(RenderError):
        render_go_project_guide(template_dir, sample_mode, sample_metadata, output)
    # Post-condition: still does not exist — the raise happened before write
    assert not output.exists()


def test_validator_passes_when_all_vars_defined(
    template_dir, sample_mode, sample_metadata
):
    """A template with every variable defined renders without error.

    Baseline check: the existing `template_dir` fixture + `sample_mode`
    produce a fully-resolved render, so the validator must be a silent
    no-op on the happy path.
    """
    output = template_dir / "output.md"
    render_go_project_guide(template_dir, sample_mode, sample_metadata, output)
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    # Sanity: no unrendered placeholders leaked through
    import re as _re
    assert _re.search(r"\{\{\s*[a-zA-Z_]\w*\s*\}\}", content) is None


def test_validator_passes_on_template_with_no_jinja_variables(
    tmp_path, sample_mode, sample_metadata
):
    """A template with no Jinja variables at all renders cleanly.

    Covers the regex's edge case: zero matches must not raise. This is
    separate from the happy-path test above — it builds a minimal
    no-variable template from scratch to isolate the empty-match behavior.
    """
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(parents=True)
    modes_dir = templates_dir / "modes"
    modes_dir.mkdir()
    (templates_dir / "llm_entry_point.md").write_text(
        "static header\n\n{% include 'modes/_header-common.md' %}\n"
        "\n{% include mode_template %}\n"
    )
    (modes_dir / "_header-common.md").write_text("no variables here\n")
    (modes_dir / "plan-concept-mode.md").write_text("plain text only\n")

    output = tmp_path / "output.md"
    render_go_project_guide(tmp_path, sample_mode, sample_metadata, output)
    assert output.exists()
    assert "no variables here" in output.read_text(encoding="utf-8")


# --- End Story M.b tests ---------------------------------------------------


# --- Story M.c: plan_tech_spec populates project-essentials.md -------------


def test_plan_tech_spec_mode_prompts_for_project_essentials():
    """Rendering the plan_tech_spec mode emits the project-essentials capture step.

    End-to-end render: init a fresh project, switch to plan_tech_spec, and
    read the resulting go.md. The prompt for project-essentials must appear
    (post-approval step), include at least one concrete worked example so
    the LLM's read-time behavior is anchored, and reference the artifact
    template path so the LLM knows where to generate from.
    """
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', 'plan_tech_spec'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    # The capture step is explicit and ordered after approval
    assert "After tech-spec approval, capture project essentials" in content

    # Concrete worked examples from at least two categories must be present —
    # the story is specific that abstract category names alone are not enough
    # to jog the developer's memory at read time.
    assert "pyve run python" in content or "poetry run python" in content
    assert "Workflow rules" in content
    assert "Architecture quirks" in content

    # The "skip if none" escape hatch must be present so plan_tech_spec does
    # not leave empty project-essentials.md files behind on fresh projects.
    assert "skip to step 7" in content or "do not create an empty" in content

    # References the artifact template path (so the LLM knows what to render)
    assert "templates/artifacts/project-essentials.md" in content

    # Heading convention reminder (no top-level `#`; `###` for subsections)
    # to prevent heading-level collision with the wrapper in _header-common.md
    assert "do NOT include a top-level" in content
    assert "###" in content


def test_plan_tech_spec_metadata_declares_project_essentials_artifact():
    """The bundled metadata lists project-essentials.md as a create artifact.

    This is the story's explicit wiring checkpoint: after M.c ships,
    `plan_tech_spec` declares two artifacts (tech-spec.md + project-essentials.md),
    both with action: create. M.d/M.e will add modify/modify wiring on other modes.
    """
    import importlib.resources

    from project_guide.actions import ActionType
    from project_guide.metadata import load_metadata

    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath(
            "project-guide/.metadata.yml"
        )
    ) as path:
        metadata = load_metadata(path)

    mode = metadata.get_mode("plan_tech_spec")
    artifact_files = [a.file for a in mode.artifacts if a.file]

    # Both artifacts present
    assert any("tech-spec.md" in f for f in artifact_files), (
        f"tech-spec.md missing from plan_tech_spec artifacts: {artifact_files}"
    )
    assert any("project-essentials.md" in f for f in artifact_files), (
        f"project-essentials.md missing from plan_tech_spec artifacts: {artifact_files}"
    )

    # project-essentials.md must be declared with action: create (not modify).
    # This is deliberate: M.c creates it fresh; M.d (refactor_plan) uses
    # modify, M.e (plan_phase) uses modify.
    essentials_artifact = next(
        a for a in mode.artifacts if a.file and "project-essentials.md" in a.file
    )
    assert essentials_artifact.action is ActionType.CREATE


# --- End Story M.c tests ---------------------------------------------------


# --- Story M.d: refactor_plan refreshes project-essentials.md --------------


def test_refactor_plan_mode_prompts_for_project_essentials_revisit():
    """Rendering refactor_plan emits the revisit-project-essentials step.

    End-to-end render: init a fresh project, switch to refactor_plan, and
    read the resulting go.md. The revisit step must be present as a final
    step (not per-document), must distinguish the create-vs-modify branches,
    must list at least one concrete worked example, and must reference
    the artifact template path for the create branch.
    """
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', 'refactor_plan'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    # Terminal step present, once (not per-document)
    assert "Final Step: Revisit Project Essentials" in content
    # Run once, not per document — explicit instruction
    assert "once" in content and "not per-document" in content

    # Create/modify branching is explicit
    assert "Create path" in content or "create path" in content
    assert "Modify path" in content or "modify path" in content

    # Legacy project is flagged as the highest-value case
    assert "legacy" in content.lower()

    # At least one concrete worked example from the refactor-specific list
    # must be present — the story is specific that abstract categories are
    # not sufficient, especially for a refactor where the developer has
    # already internalized the new convention.
    assert "environment manager" in content
    assert "pyve" in content or "poetry" in content or "uv" in content or "hatch" in content

    # References the artifact template (create path needs it)
    assert "templates/artifacts/project-essentials.md" in content

    # Heading convention reminder (no top-level `#`; `###` for subsections)
    assert "do NOT include a top-level" in content

    # The "skip if none" escape hatch must be present
    assert "Skip if there are none" in content or "skip this step" in content

    # Refactor-framing principle (fork-in-the-road / wrong choice still "works")
    assert "fork-in-the-road" in content or 'still "works"' in content


def test_refactor_plan_metadata_declares_project_essentials_modify_artifact():
    """refactor_plan declares project-essentials.md as a modify artifact.

    This is the M.d wiring checkpoint. Distinct from M.c which uses CREATE:
    refactor_plan may run against a project that already has the file OR
    one that doesn't (legacy project being migrated). The `modify` action
    type is the conversational escape hatch — the mode template handles
    the create-if-absent case in prose (Step F.1's branching).
    """
    import importlib.resources

    from project_guide.actions import ActionType
    from project_guide.metadata import load_metadata

    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath(
            "project-guide/.metadata.yml"
        )
    ) as path:
        metadata = load_metadata(path)

    mode = metadata.get_mode("refactor_plan")
    essentials_artifacts = [
        a for a in mode.artifacts if a.file and "project-essentials.md" in a.file
    ]
    assert len(essentials_artifacts) == 1, (
        f"expected exactly one project-essentials.md artifact on refactor_plan, "
        f"got {len(essentials_artifacts)}"
    )
    assert essentials_artifacts[0].action is ActionType.MODIFY


# --- End Story M.d tests ---------------------------------------------------


# --- Story M.e: plan_phase appends to project-essentials.md ----------------


def test_plan_phase_mode_prompts_for_project_essentials_append():
    """Rendering plan_phase emits the append-new-facts step.

    End-to-end render: init a fresh project, switch to plan_phase, and
    read the resulting go.md. The append step must be present, must come
    after the stories-approval step, must use append-only semantics (not
    refresh/modify), must handle the create-if-absent case for legacy
    projects, and must include at least one concrete phase-specific
    worked example.
    """
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', 'plan_phase'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    # Append step present and runs after stories approval
    assert "append any new must-know facts" in content.lower()
    assert "once" in content  # runs once per phase, not per-story

    # Append-only semantics are explicit (not refresh/rewrite)
    assert "append" in content.lower()
    assert "do not rewrite or reorder" in content.lower() or "append-only" in content.lower()

    # Create-if-absent branch for legacy projects
    assert "does NOT exist" in content or "does not exist" in content
    assert "legacy project" in content.lower()

    # Phase-specific worked example categories
    assert "architecture boundary" in content.lower() or "integration surface" in content.lower()
    assert "workflow rule" in content.lower() or "CLI contract" in content.lower()

    # Skip-if-none escape hatch
    assert "Skip if there are none" in content or "skip this step" in content

    # References the artifact template for the create branch
    assert "templates/artifacts/project-essentials.md" in content

    # Heading convention reminder
    assert "do NOT include a top-level" in content


def test_plan_phase_metadata_declares_project_essentials_modify_artifact():
    """plan_phase declares project-essentials.md as a modify artifact.

    Third planning-mode wiring checkpoint: plan_phase now carries three
    artifacts (new-phase-*.md, stories.md, project-essentials.md), the
    last two both with action: modify.
    """
    import importlib.resources

    from project_guide.actions import ActionType
    from project_guide.metadata import load_metadata

    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath(
            "project-guide/.metadata.yml"
        )
    ) as path:
        metadata = load_metadata(path)

    mode = metadata.get_mode("plan_phase")
    essentials_artifacts = [
        a for a in mode.artifacts if a.file and "project-essentials.md" in a.file
    ]
    assert len(essentials_artifacts) == 1, (
        f"expected exactly one project-essentials.md artifact on plan_phase, "
        f"got {len(essentials_artifacts)}"
    )
    assert essentials_artifacts[0].action is ActionType.MODIFY

    # Sanity: the other two expected artifacts are still there — the
    # M.e wiring must not clobber the existing new-phase-*.md and
    # stories.md declarations.
    artifact_files = [a.file for a in mode.artifacts if a.file]
    assert any("new-phase-" in f for f in artifact_files), (
        f"new-phase-*.md missing from plan_phase artifacts: {artifact_files}"
    )
    assert any("stories.md" in f for f in artifact_files), (
        f"stories.md missing from plan_phase artifacts: {artifact_files}"
    )


# --- End Story M.e tests ---------------------------------------------------


# --- Story M.g: approval-gate lane rule and code-mode lane separation ------


@pytest.mark.parametrize("mode_name", _get_all_mode_names())
def test_header_common_approval_gate_rule_renders_in_every_mode(mode_name):
    """The M.g approval-gate rule must appear in every rendered mode.

    Critical parametrized test: the rule is injected via `_header-common.md`,
    which is included once by `llm_entry_point.md`, so every rendered `go.md`
    must contain the pinned substring. If any mode misses it, either the
    include chain is broken or someone removed the rule from
    `_header-common.md`.
    """
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', mode_name])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    # Pinned substring from the new rule — if this ever changes, update both
    # `_header-common.md` and this test in the same commit.
    assert "do not prompt for git operations" in content, (
        f"mode {mode_name!r} is missing the M.g approval-gate rule"
    )
    # The rule sits under the **Rules** block, after "Never auto-advance"
    rules_idx = content.find("**Rules**")
    rule_idx = content.find("do not prompt for git operations")
    assert rules_idx >= 0 and rule_idx > rules_idx, (
        f"mode {mode_name!r}: approval-gate rule is not inside the Rules block"
    )


def test_code_direct_mode_separates_llm_lane_from_developer_lane():
    """code_direct's Velocity Practices section must label the two lanes.

    The two-lane structure is load-bearing: it forces future template
    authors to classify every workflow item as LLM-lane or developer-lane,
    which prevents the commit-prompt overreach bug from recurring.
    """
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', 'code_direct'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    # Both lane headers present
    assert "**LLM's role in each cycle:**" in content
    assert "**Developer's role (do NOT prompt for, offer, or initiate):**" in content

    # The "do NOT prompt" language is in the developer-lane header —
    # this is the load-bearing phrase for future template authors
    dev_lane_idx = content.find("**Developer's role")
    assert "do NOT prompt for, offer, or initiate" in content[dev_lane_idx:dev_lane_idx + 200]

    # Commit-related content appears in the developer lane, not before it.
    # "Direct commits to main" is the specific bullet that used to live
    # in the pre-M.g unlabeled bullet list.
    commit_idx = content.find("Direct commits to main")
    assert commit_idx > dev_lane_idx, (
        "'Direct commits to main' must appear after the developer-lane header"
    )

    # The LLM-lane header must come BEFORE the developer-lane header
    llm_lane_idx = content.find("**LLM's role in each cycle:**")
    assert llm_lane_idx < dev_lane_idx


def test_code_direct_present_step_forbids_followup_prompts():
    """code_direct step 9 must explicitly forbid follow-up proposals.

    Belt-and-suspenders reinforcement: the universal rule in
    `_header-common.md` should be sufficient, but pinning the forbidden
    patterns in the code-mode-specific step catches LLMs that skim
    the header and jump straight to the cycle steps.
    """
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', 'code_direct'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    # Both pinned forbid-patterns present in step 9's prose
    assert "Do not propose commits" in content
    assert 'want me to also' in content


def test_code_test_first_present_step_forbids_followup_prompts():
    """code_test_first step 8 must also forbid follow-up proposals.

    code_test_first does not get the Velocity Practices lane restructure
    (it has no analogous section), but its Present step gets the same
    tightening as code_direct step 9.
    """
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        result = runner.invoke(main, ['mode', 'code_test_first'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    assert "Do not propose commits" in content
    assert 'want me to also' in content


# --- End Story M.g tests ---------------------------------------------------


# --- Story N.d ---------------------------------------------------------------


def test_default_mode_with_test_first_true_suggests_code_test_first():
    """Rendered default mode with test_first=True must suggest code_test_first."""
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init', '--test-first'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    assert "code_test_first" in content
    assert "code_direct" not in content.split("## Project Lifecycle")[1].split("##")[0]


def test_default_mode_with_test_first_false_suggests_code_direct():
    """Rendered default mode with test_first=False must suggest code_direct."""
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    assert "code_direct" in content


# --- End Story N.d -----------------------------------------------------------


# --- Story N.j ---------------------------------------------------------------


def test_scaffold_project_pyve_installed_shows_merge_instruction():
    """Rendered scaffold_project with pyve_installed=True contains pyve merge instruction."""
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ['init'])

        result = runner.invoke(main, ['mode', 'scaffold_project'])
        assert result.exit_code == 0

        # Patch config to simulate pyve detected, then re-render via mode switch
        import yaml
        config_data = yaml.safe_load(Path(".project-guide.yml").read_text())
        config_data["pyve_version"] = "1.2.3"
        Path(".project-guide.yml").write_text(yaml.dump(config_data))

        result = runner.invoke(main, ['mode', 'scaffold_project'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    assert "project-essentials-pyve.md" in content
    assert "Pyve" in content or "pyve" in content


def test_scaffold_project_pyve_not_installed_omits_pyve_section():
    """Rendered scaffold_project with pyve_installed=False omits pyve merge instruction."""
    import yaml
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ['init'])

        # Force pyve_version to None regardless of what detection found
        config_data = yaml.safe_load(Path(".project-guide.yml").read_text())
        config_data["pyve_version"] = None
        Path(".project-guide.yml").write_text(yaml.dump(config_data))

        result = runner.invoke(main, ['mode', 'scaffold_project'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    assert "project-essentials-pyve.md" not in content


def test_project_essentials_pyve_artifact_has_no_unrendered_placeholders():
    """project-essentials-pyve.md artifact contains no unrendered {{ var }} placeholders."""
    import importlib.resources
    import re

    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath(
            "project-guide/templates/artifacts/project-essentials-pyve.md"
        )
    ) as path:
        content = path.read_text(encoding="utf-8")

    matches = re.findall(r"\{\{\s*([a-zA-Z_]\w*)\s*\}\}", content)
    assert not matches, f"Unrendered placeholders in artifact: {matches}"
    assert "pyve" in content.lower()


# --- End Story N.j -----------------------------------------------------------


# --- Story N.k ---------------------------------------------------------------


def test_scaffold_project_contains_memory_review_step():
    """Rendered scaffold_project contains the Memory Review step."""
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ['init'])
        runner.invoke(main, ['mode', 'scaffold_project'])
        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    assert "Memory Review" in content


def test_scaffold_project_memory_review_before_present_for_approval():
    """Memory Review step appears before Present for Approval in scaffold_project."""
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ['init'])
        runner.invoke(main, ['mode', 'scaffold_project'])
        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    memory_pos = content.index("Memory Review")
    approval_pos = content.index("Present for Approval")
    assert memory_pos < approval_pos


def test_scaffold_project_memory_review_escape_hatch():
    """Memory Review step includes escape hatch for empty or inaccessible memory store."""
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ['init'])
        runner.invoke(main, ['mode', 'scaffold_project'])
        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    assert "empty or inaccessible" in content


# --- End Story N.k -----------------------------------------------------------


# --- Story N.l ---------------------------------------------------------------


@pytest.mark.parametrize("mode_name", _get_all_mode_names())
def test_header_common_memory_reflection_rule_renders_in_every_mode(mode_name):
    """Rule #7 (memory reflection) appears in the Rules block of every rendered mode."""
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ['init'])
        runner.invoke(main, ['mode', mode_name])
        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    rules_pos = content.index("**Rules**")
    # Find the end of the Rules block (next --- separator or heading)
    rules_end = content.find("\n---", rules_pos)
    rules_block = content[rules_pos:rules_end] if rules_end != -1 else content[rules_pos:]
    assert "Before recording a new memory, reflect" in rules_block, (
        f"Memory reflection rule missing from Rules block in mode '{mode_name}'"
    )


# --- End Story N.l -----------------------------------------------------------


# --- Story N.r ---------------------------------------------------------------


_PYVE_SUBSECTION_HEADING = "LLM-internal vs. developer-facing invocation"


def test_pyve_artifact_contains_llm_vs_developer_subsection():
    """Bundled project-essentials-pyve.md contains the new invocation subsection.

    The LLM reads this artifact during `scaffold_project` when pyve is
    detected; the subsection teaches it to keep `pyve run` out of
    developer-facing command suggestions.
    """
    import importlib.resources

    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath(
            "project-guide/templates/artifacts/project-essentials-pyve.md"
        )
    ) as path:
        content = path.read_text(encoding="utf-8")

    assert f"### {_PYVE_SUBSECTION_HEADING}" in content
    assert "project-guide mode plan_phase" in content
    assert "**Why:**" in content
    assert "**How to apply:**" in content

    # Placement: immediately after the initial bullet list, before the
    # Python invocation rule subsection (story ordering constraint).
    heading_pos = content.index(f"### {_PYVE_SUBSECTION_HEADING}")
    python_rule_pos = content.index("### Python invocation rule")
    assert heading_pos < python_rule_pos


def test_rendered_go_md_includes_subsection_when_project_essentials_merged(tmp_path):
    """When project-essentials.md has been merged with the pyve content, every
    rendered go.md surfaces the subsection via the ``## Project Essentials`` block.

    Simulates the post-scaffold state (the LLM has copied the pyve sections
    into ``docs/specs/project-essentials.md``) without actually running the
    scaffold flow.
    """
    import importlib.resources

    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath(
            "project-guide/templates/artifacts/project-essentials-pyve.md"
        )
    ) as path:
        pyve_essentials = path.read_text(encoding="utf-8")

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        specs_dir = Path("docs/specs")
        specs_dir.mkdir(parents=True, exist_ok=True)
        (specs_dir / "project-essentials.md").write_text(pyve_essentials, encoding="utf-8")

        # Re-render the current mode so project_essentials is picked up.
        result = runner.invoke(main, ['mode', 'default'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    assert "## Project Essentials" in content
    assert f"### {_PYVE_SUBSECTION_HEADING}" in content


def test_rendered_go_md_omits_subsection_when_no_project_essentials(tmp_path):
    """Fresh init → no project-essentials.md → subsection is absent from go.md.

    Regression guard for the existing inclusion gate: the subsection only
    reaches the developer when pyve detection has driven its content into
    ``docs/specs/project-essentials.md``. Without that merge step, go.md
    must not reference the subsection heading.
    """
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        content = Path("docs/project-guide/go.md").read_text(encoding="utf-8")

    assert f"### {_PYVE_SUBSECTION_HEADING}" not in content


# --- End Story N.r -----------------------------------------------------------


@pytest.mark.parametrize("mode_name", _get_all_mode_names())
def test_every_mode_renders_successfully(mode_name):
    """Every mode in the bundled metadata must render without errors.

    This proves a fresh install works and catches regressions when modes are added.
    """
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0, f"init failed: {result.output}"

        result = runner.invoke(main, ['mode', mode_name])
        assert result.exit_code == 0, f"mode {mode_name} failed: {result.output}"
        assert f"Mode set: {mode_name}" in result.output

        output = Path("docs/project-guide/go.md")
        assert output.exists()
        assert len(output.read_text(encoding="utf-8")) > 0
