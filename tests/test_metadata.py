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

import pytest

from project_guide.exceptions import MetadataError
from project_guide.metadata import load_metadata


@pytest.fixture
def sample_metadata_yml(tmp_path):
    """Create a minimal valid metadata YAML file."""
    content = """\
common:
  templates_path: "templates"
  specs_path: "docs/specs"

modes:
  - name: plan_concept
    info: Generate a concept
    description: Define the problem and solution space.
    sequence_or_cycle: sequence
    generation_type: document
    mode_template: "{{templates_path}}/modes/plan-concept-mode.md"
    next_mode: plan_features
    artifacts:
      - file: "{{specs_path}}/concept.md"
        action: create
    files_exist:
      - "{{templates_path}}/modes/plan-concept-mode.md"
  - name: plan_features
    info: Generate features
    description: Define what the project does.
    sequence_or_cycle: sequence
    generation_type: document
    mode_template: "{{templates_path}}/modes/plan-features-mode.md"
"""
    path = tmp_path / "metadata.yml"
    path.write_text(content)
    return path


def test_load_metadata_resolves_variables(sample_metadata_yml):
    """Test that {{var}} placeholders in common block are resolved."""
    metadata = load_metadata(sample_metadata_yml)

    assert metadata.common["templates_path"] == "templates"
    assert metadata.common["specs_path"] == "docs/specs"

    mode = metadata.get_mode("plan_concept")
    assert mode.mode_template == "templates/modes/plan-concept-mode.md"
    assert mode.artifacts[0]["file"] == "docs/specs/concept.md"
    assert mode.files_exist[0] == "templates/modes/plan-concept-mode.md"


def test_load_metadata_parses_modes(sample_metadata_yml):
    """Test that modes are parsed correctly."""
    metadata = load_metadata(sample_metadata_yml)

    assert len(metadata.modes) == 2
    assert metadata.list_mode_names() == ["plan_concept", "plan_features"]

    mode = metadata.get_mode("plan_concept")
    assert mode.name == "plan_concept"
    assert mode.info == "Generate a concept"
    assert mode.sequence_or_cycle == "sequence"
    assert mode.next_mode == "plan_features"


def test_get_mode_not_found(sample_metadata_yml):
    """Test MetadataError on unknown mode name."""
    metadata = load_metadata(sample_metadata_yml)

    with pytest.raises(MetadataError, match="Mode 'nonexistent' not found"):
        metadata.get_mode("nonexistent")


def test_load_metadata_file_not_found(tmp_path):
    """Test MetadataError when file does not exist."""
    with pytest.raises(MetadataError, match="not found"):
        load_metadata(tmp_path / "missing.yml")


def test_load_metadata_invalid_yaml(tmp_path):
    """Test MetadataError on invalid YAML."""
    path = tmp_path / "bad.yml"
    path.write_text("not: valid: yaml: [[[")

    with pytest.raises(MetadataError, match="Invalid YAML"):
        load_metadata(path)


def test_load_metadata_empty_file(tmp_path):
    """Test MetadataError on empty file."""
    path = tmp_path / "empty.yml"
    path.write_text("")

    with pytest.raises(MetadataError, match="Empty or invalid"):
        load_metadata(path)


def test_load_metadata_no_modes(tmp_path):
    """Test MetadataError when no modes defined."""
    path = tmp_path / "no_modes.yml"
    path.write_text("common:\n  foo: bar\nmodes: []\n")

    with pytest.raises(MetadataError, match="No modes defined"):
        load_metadata(path)


def test_load_metadata_mode_missing_name(tmp_path):
    """Test MetadataError when a mode lacks a name."""
    path = tmp_path / "no_name.yml"
    path.write_text("common: {}\nmodes:\n  - info: test\n    description: test\n    sequence_or_cycle: sequence\n")

    with pytest.raises(MetadataError, match="must have a 'name'"):
        load_metadata(path)


def test_load_metadata_from_package():
    """Test loading the actual bundled metadata file."""
    import importlib.resources
    with importlib.resources.as_file(
        importlib.resources.files("project_guide.templates").joinpath("project-guide/.metadata.yml")
    ) as path:
        metadata = load_metadata(path)

    assert len(metadata.modes) > 0
    assert "plan_concept" in metadata.list_mode_names()
