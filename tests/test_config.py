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
from pathlib import Path

import pytest

from project_guides.config import Config, GuideOverride
from project_guides.exceptions import ConfigError


def test_config_creation_with_defaults():
    """Test creating a config with default values."""
    config = Config()
    
    assert config.version == "1.0"
    assert config.installed_version == ""
    assert config.target_dir == "docs/guides"
    assert config.overrides == {}


def test_config_save_load_round_trip(tmp_path):
    """Test saving and loading a config file."""
    config_file = tmp_path / ".project-guides.yml"
    
    config = Config(
        version="1.0",
        installed_version="0.2.0",
        target_dir="docs/guides",
    )
    config.add_override("debug-guide.md", "Custom case study", "0.2.0")
    
    config.save(str(config_file))
    
    loaded_config = Config.load(str(config_file))
    
    assert loaded_config.version == "1.0"
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
    config_file = tmp_path / ".project-guides.yml"
    
    config_file.write_text("invalid: yaml: content:")
    
    with pytest.raises(ConfigError, match="Invalid YAML"):
        Config.load(str(config_file))


def test_missing_config_file():
    """Test loading from non-existent config file."""
    with pytest.raises(ConfigError, match="Configuration file not found"):
        Config.load("/nonexistent/path/.project-guides.yml")


def test_config_with_no_overrides(tmp_path):
    """Test config without any overrides."""
    config_file = tmp_path / ".project-guides.yml"
    
    config = Config(
        version="1.0",
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
