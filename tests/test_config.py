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
