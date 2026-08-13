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

from datetime import date

import pytest

from project_guide.config import SCHEMA_VERSION, Config
from project_guide.exceptions import ConfigError, SchemaVersionError


def test_config_creation_with_defaults():
    """Test creating a config with default values."""
    config = Config()

    assert config.version == "2.0"
    assert config.installed_version == ""
    assert config.target_dir == "docs/project-guide"
    assert config.current_mode == "default"
    assert config.overrides == {}


def test_config_save_load_round_trip(tmp_path):
    """Test saving and loading a config file."""
    config_file = tmp_path / ".project-guide.yml"

    config = Config(
        version="2.0",
        installed_version="0.2.0",
        target_dir="docs/guides",
    )
    config.add_override("debug-guide.md", "Custom case study", "0.2.0")

    config.save(str(config_file))

    loaded_config = Config.load(str(config_file))

    assert loaded_config.version == "2.0"
    assert loaded_config.installed_version == "0.2.0"
    assert loaded_config.target_dir == "docs/guides"
    assert "debug-guide.md" in loaded_config.overrides
    assert loaded_config.overrides["debug-guide.md"].reason == "Custom case study"
    assert loaded_config.overrides["debug-guide.md"].locked_version == "0.2.0"
    assert loaded_config.overrides["debug-guide.md"].last_updated == date.today()


def test_override_add_remove():
    """Test adding and removing overrides."""
    config = Config()

    assert not config.is_overridden("debug-guide.md")

    config.add_override("debug-guide.md", "Custom content", "0.1.0")

    assert config.is_overridden("debug-guide.md")
    assert config.overrides["debug-guide.md"].reason == "Custom content"
    assert config.overrides["debug-guide.md"].locked_version == "0.1.0"

    config.remove_override("debug-guide.md")

    assert not config.is_overridden("debug-guide.md")
    assert "debug-guide.md" not in config.overrides


def test_invalid_yaml_handling(tmp_path):
    """Test handling of invalid YAML."""
    config_file = tmp_path / ".project-guide.yml"

    config_file.write_text("invalid: yaml: content:")

    with pytest.raises(ConfigError, match="Invalid YAML"):
        Config.load(str(config_file))


def test_missing_config_file():
    """Test loading from non-existent config file."""
    with pytest.raises(ConfigError, match="Configuration file not found"):
        Config.load("/nonexistent/path/.project-guide.yml")


def test_config_with_no_overrides(tmp_path):
    """Test config without any overrides."""
    config_file = tmp_path / ".project-guide.yml"

    config = Config(
        version="2.0",
        installed_version="0.2.0",
        target_dir="docs/guides",
    )

    config.save(str(config_file))
    loaded_config = Config.load(str(config_file))

    assert loaded_config.overrides == {}


def test_override_update():
    """Test updating an existing override."""
    config = Config()

    config.add_override("debug-guide.md", "Original reason", "0.1.0")
    original_date = config.overrides["debug-guide.md"].last_updated

    config.add_override("debug-guide.md", "Updated reason", "0.2.0")

    assert config.overrides["debug-guide.md"].reason == "Updated reason"
    assert config.overrides["debug-guide.md"].locked_version == "0.2.0"
    assert config.overrides["debug-guide.md"].last_updated >= original_date


# --- Story N.d ---------------------------------------------------------------


def test_config_test_first_round_trip(tmp_path):
    """test_first=True survives a save/load cycle."""
    config_file = tmp_path / ".project-guide.yml"
    config = Config(test_first=True)
    config.save(str(config_file))
    loaded = Config.load(str(config_file))
    assert loaded.test_first is True


def test_config_test_first_default_false(tmp_path):
    """test_first defaults to False and round-trips as False."""
    config_file = tmp_path / ".project-guide.yml"
    Config().save(str(config_file))
    loaded = Config.load(str(config_file))
    assert loaded.test_first is False


# --- Story N.i ---------------------------------------------------------------


def test_config_metadata_overrides_round_trip(tmp_path):
    """metadata_overrides saves and loads correctly."""
    config_file = tmp_path / ".project-guide.yml"
    overrides = {"code_direct": {"next_mode": "debug", "info": "Custom info"}}
    Config(metadata_overrides=overrides).save(str(config_file))
    loaded = Config.load(str(config_file))
    assert loaded.metadata_overrides == overrides


def test_config_metadata_overrides_default_empty(tmp_path):
    """metadata_overrides defaults to empty dict and round-trips cleanly."""
    config_file = tmp_path / ".project-guide.yml"
    Config().save(str(config_file))
    loaded = Config.load(str(config_file))
    assert loaded.metadata_overrides == {}


# --- End Story N.i -----------------------------------------------------------


# --- Story N.p ---------------------------------------------------------------

def test_schema_version_matching_loads_normally(tmp_path):
    """Current SCHEMA_VERSION in config loads without error."""
    config_file = tmp_path / ".project-guide.yml"
    Config(version=SCHEMA_VERSION).save(str(config_file))
    loaded = Config.load(str(config_file))
    assert loaded.version == SCHEMA_VERSION


def test_schema_version_older_raises_schema_version_error(tmp_path):
    """An older schema version raises SchemaVersionError with direction='older'."""
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text("version: '1.0'\ncurrent_mode: default\n")
    with pytest.raises(SchemaVersionError) as exc_info:
        Config.load(str(config_file))
    assert exc_info.value.direction == "older"
    assert "older" in str(exc_info.value)


def test_schema_version_newer_raises_schema_version_error(tmp_path):
    """A newer schema version raises SchemaVersionError with direction='newer'."""
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text("version: '99.0'\ncurrent_mode: default\n")
    with pytest.raises(SchemaVersionError) as exc_info:
        Config.load(str(config_file))
    assert exc_info.value.direction == "newer"
    assert "newer" in str(exc_info.value)
    assert "Upgrade project-guide" in str(exc_info.value)


def test_schema_version_absent_defaults_to_current(tmp_path):
    """An absent version field defaults to SCHEMA_VERSION and loads normally."""
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text("current_mode: default\ninstalled_version: '1.0.0'\n")
    loaded = Config.load(str(config_file))
    assert loaded.version == SCHEMA_VERSION


def test_schema_version_unparseable_raises_schema_version_error(tmp_path):
    """A non-PEP440 version string is treated as an older-style mismatch."""
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text("version: 'not-a-version'\ncurrent_mode: default\n")
    with pytest.raises(SchemaVersionError) as exc_info:
        Config.load(str(config_file))
    assert exc_info.value.direction == "older"


def test_schema_version_error_is_config_error():
    """SchemaVersionError is a subclass of ConfigError for existing handlers."""
    err = SchemaVersionError("test", direction="older")
    assert isinstance(err, ConfigError)


# --- End Story N.p -----------------------------------------------------------


# --- Story N.s ---------------------------------------------------------------


def test_config_project_name_round_trip(tmp_path):
    """project_name survives a save/load cycle."""
    config_file = tmp_path / ".project-guide.yml"
    Config(project_name="demo-project").save(str(config_file))
    loaded = Config.load(str(config_file))
    assert loaded.project_name == "demo-project"


def test_config_project_name_defaults_to_empty(tmp_path):
    """Absent project_name defaults to '' (additive-with-default policy)."""
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text(f"version: '{SCHEMA_VERSION}'\ncurrent_mode: default\n")
    loaded = Config.load(str(config_file))
    assert loaded.project_name == ""


# --- End Story N.s -----------------------------------------------------------


# --- Story R.j: persisted pyve_installed render gate --------------------------
#
# `pyve_installed` answers "should the Pyve guidance render?"; `pyve_version`
# answers "which pyve was seen?". Deriving the first from the second is what
# turned a single detection miss into permanent loss of ~80 lines of guardrail
# from go.md, so the two fields are decoupled here.


def test_pyve_installed_defaults_to_false_on_a_fresh_config():
    """A brand-new Config has seen no pyve."""
    assert Config().pyve_installed is False


def test_pyve_installed_round_trips_through_yaml(tmp_path):
    """The flag is persisted, not recomputed on every load."""
    config_file = tmp_path / ".project-guide.yml"
    Config(pyve_installed=True, pyve_version="3.2.2").save(str(config_file))

    loaded = Config.load(str(config_file))

    assert loaded.pyve_installed is True
    assert "pyve_installed" in config_file.read_text()


def test_pyve_installed_migrates_from_a_legacy_config_with_a_version(tmp_path):
    """No `pyve_installed` key means today's derived answer, so upgrading is a no-op.

    An existing project must not change behavior at the moment of upgrade; it
    changes on the next `update` / `mode`, which is the intended repair.
    """
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text(
        f"version: '{SCHEMA_VERSION}'\ncurrent_mode: default\npyve_version: 'pyve 3.2.2'\n"
    )

    assert Config.load(str(config_file)).pyve_installed is True


def test_pyve_installed_migrates_to_false_without_a_version(tmp_path):
    """The other half of the migration default: no version seen, no guidance."""
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text(f"version: '{SCHEMA_VERSION}'\ncurrent_mode: default\n")

    assert Config.load(str(config_file)).pyve_installed is False


def test_an_explicit_false_overrides_the_derived_default(tmp_path):
    """Opting out is a hand-edit, and a hand-edit must survive a load.

    This is the *only* way the flag goes off, so the persisted value has to win
    over the migration default it would otherwise be derived into.
    """
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text(
        f"version: '{SCHEMA_VERSION}'\ncurrent_mode: default\n"
        "pyve_version: '3.2.2'\npyve_installed: false\n"
    )

    assert Config.load(str(config_file)).pyve_installed is False


def test_an_explicit_true_survives_a_null_version(tmp_path):
    """The decoupling in the other direction: render without knowing the version."""
    config_file = tmp_path / ".project-guide.yml"
    config_file.write_text(
        f"version: '{SCHEMA_VERSION}'\ncurrent_mode: default\npyve_installed: true\n"
    )

    loaded = Config.load(str(config_file))

    assert loaded.pyve_installed is True
    assert loaded.pyve_version is None


def test_adding_pyve_installed_does_not_bump_the_schema_version():
    """Additive-with-default, so the config-schema policy says do not bump.

    Pinned because the reverse — bumping for an additive field — would make
    every existing project fail to load until it ran `init --force`.
    """
    assert SCHEMA_VERSION == "2.0"


# --- sticky-true: automatic detection may turn the flag on, never off ---


def test_detection_success_turns_the_flag_on():
    """A successful probe is the repair path for a project stuck at false."""
    config = Config(pyve_installed=False, pyve_version=None)

    changed = config.record_pyve_detection("3.2.2")

    assert changed is True
    assert config.pyve_installed is True
    assert config.pyve_version == "3.2.2"


def test_detection_failure_never_turns_the_flag_off():
    """The load-bearing invariant of the subphase.

    Once a project has seen pyve, no later probe failure may strip the
    guidance again — that is the exact bug this subphase exists to close.
    """
    config = Config(pyve_installed=True, pyve_version="3.2.2")

    changed = config.record_pyve_detection(None)

    assert changed is False
    assert config.pyve_installed is True
    assert config.pyve_version == "3.2.2"


def test_detection_failure_leaves_a_false_flag_alone():
    """Absence is the steady state for a non-pyve project — nothing to write."""
    config = Config(pyve_installed=False, pyve_version=None)

    changed = config.record_pyve_detection(None)

    assert changed is False
    assert config.pyve_installed is False


def test_detection_reports_no_change_when_the_version_is_unchanged():
    """Callers use the return value to decide whether to write the file."""
    config = Config(pyve_installed=True, pyve_version="3.2.2")

    assert config.record_pyve_detection("3.2.2") is False


def test_detection_updates_a_changed_version_on_an_already_true_flag():
    """A pyve upgrade still refreshes the recorded version."""
    config = Config(pyve_installed=True, pyve_version="3.2.2")

    changed = config.record_pyve_detection("3.3.0")

    assert changed is True
    assert config.pyve_version == "3.3.0"


# --- End Story R.j -----------------------------------------------------------
