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
    # Entry point template (source lives in template dir, rendered output goes elsewhere)
    (tmp_path / "go-project-guide.md").write_text(
        "# Guide\n\n{% include 'modes/_header-common.md' %}\n\n{% include mode_template %}\n"
    )

    # Templates subdirectory
    modes_dir = tmp_path / "templates" / "modes"
    modes_dir.mkdir(parents=True)

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
    content = output.read_text()
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

    content = output.read_text()
    assert "Project: test-project" in content


def test_render_missing_templates_dir(tmp_path, sample_mode, sample_metadata):
    """Test RenderError when templates directory does not exist."""
    with pytest.raises(RenderError, match="Templates directory not found"):
        render_go_project_guide(tmp_path, sample_mode, sample_metadata, tmp_path / "out.md")


def test_render_missing_entry_point(tmp_path, sample_mode, sample_metadata):
    """Test RenderError when go-project-guide.md template is missing."""
    (tmp_path / "templates").mkdir()
    with pytest.raises(RenderError, match="Template not found"):
        render_go_project_guide(tmp_path, sample_mode, sample_metadata, tmp_path / "out.md")


def test_render_undefined_vars_are_preserved(template_dir, sample_mode, sample_metadata):
    """Test that undefined variables render as placeholders, not errors."""
    (template_dir / "templates" / "modes" / "plan-concept-mode.md").write_text(
        "## Concept\n\n{{ unknown_variable }}\n"
    )
    output = template_dir / "output.md"
    render_go_project_guide(template_dir, sample_mode, sample_metadata, output)

    content = output.read_text()
    assert "{{ unknown_variable }}" in content


def test_render_end_to_end_with_package_templates():
    """Test rendering with actual package templates (plan_concept mode)."""
    from click.testing import CliRunner  # noqa: I001

    from project_guide.cli import main

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['init'])
        assert result.exit_code == 0

        output = Path("docs/specs/go-project-guide.md")
        assert output.exists()

        content = output.read_text()
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

        output = Path("docs/specs/go-project-guide.md")
        assert output.exists()
        assert len(output.read_text()) > 0
