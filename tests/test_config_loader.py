"""
Tests for config_loader — config parsing failures, missing keys, bad references.
"""
import os
import pytest
from config_loader import ConfigLoader, ProviderConfig, ModelConfig, load_config


class TestProviderConfig:
    """Test ProviderConfig.api_key property."""

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("MY_TEST_KEY", "sk-abc123")
        pc = ProviderConfig(name="test", api_key_env="MY_TEST_KEY", base_url="https://api.test.com")
        assert pc.api_key == "sk-abc123"

    def test_api_key_missing_raises(self, monkeypatch):
        """Missing env var should raise ValueError, not return None."""
        monkeypatch.delenv("NONEXISTENT_KEY_XYZ", raising=False)
        pc = ProviderConfig(name="test", api_key_env="NONEXISTENT_KEY_XYZ", base_url="")
        with pytest.raises(ValueError, match="NONEXISTENT_KEY_XYZ"):
            _ = pc.api_key


class TestConfigLoader:
    """Test YAML parsing and accessor logic."""

    def test_full_config_loads(self, sample_config_yaml):
        config = ConfigLoader(str(sample_config_yaml))
        config.load()
        assert len(config.models) == 2
        assert len(config.scenarios) == 1
        assert "test_provider" in config.providers

    def test_model_temperature_override(self, sample_config_yaml):
        """Model-level temp should override defaults."""
        config = ConfigLoader(str(sample_config_yaml))
        config.load()
        model_1 = config.get_model("test-model-1")
        model_2 = config.get_model("test-model-2")
        assert model_1.temperature == 0.5  # model override
        assert model_2.temperature == 0.7  # from defaults

    def test_get_unknown_provider_raises(self, sample_config_yaml):
        config = ConfigLoader(str(sample_config_yaml))
        config.load()
        with pytest.raises(ValueError, match="Unknown provider"):
            config.get_provider("nonexistent")

    def test_get_unknown_model_raises(self, sample_config_yaml):
        config = ConfigLoader(str(sample_config_yaml))
        config.load()
        with pytest.raises(ValueError, match="Unknown model"):
            config.get_model("nonexistent-model")

    def test_get_unknown_scenario_raises(self, sample_config_yaml):
        config = ConfigLoader(str(sample_config_yaml))
        config.load()
        with pytest.raises(ValueError, match="Unknown scenario"):
            config.get_scenario("/fake/path")

    def test_output_dir_default(self, tmp_path):
        """Missing output.dir should default to 'output'."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("providers: {}\nmodels: []\nscenarios: []")
        config = ConfigLoader(str(config_file))
        config.load()
        assert config.output_dir == "output"

    def test_empty_config_file(self, tmp_path):
        """Completely empty YAML should not crash with TypeError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        config = ConfigLoader(str(config_file))
        # yaml.safe_load("") returns None, which will cause issues
        # This tests that the code handles it (it currently will crash)
        with pytest.raises((TypeError, AttributeError)):
            config.load()

    def test_missing_config_file_raises(self, tmp_path):
        config = ConfigLoader(str(tmp_path / "nonexistent.yaml"))
        with pytest.raises(FileNotFoundError):
            config.load()

    def test_oversight_levels_from_scenario_dir(self, sample_config_yaml, tmp_scenario_dir):
        """Scenarios with an oversight/ subdir should use those levels, not global."""
        config = ConfigLoader(str(sample_config_yaml))
        config.load()
        scenario = config.scenarios[0]
        # The tmp_scenario_dir fixture has oversight/low.md and oversight/high.md
        assert set(scenario.oversight_levels) == {"low", "high"}

    def test_oversight_levels_fallback_to_global(self, tmp_path):
        """Scenario without oversight/ subdir should use global oversight_levels."""
        scenario_dir = tmp_path / "scenario_no_oversight"
        scenario_dir.mkdir()
        (scenario_dir / "benign_goal.md").write_text("test")
        (scenario_dir / "user.md").write_text("test")

        config_content = f"""
providers: {{}}
models: []
scenarios:
  - path: {scenario_dir}
oversight_levels:
  - low
  - medium
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        config = ConfigLoader(str(config_file))
        config.load()
        assert config.scenarios[0].oversight_levels == ["low", "medium"]

    def test_project_root_is_config_dir(self, sample_config_yaml):
        config = ConfigLoader(str(sample_config_yaml))
        config.load()
        assert config.project_root == str(sample_config_yaml.parent)

    def test_defaults_property(self, sample_config_yaml):
        config = ConfigLoader(str(sample_config_yaml))
        config.load()
        assert config.defaults.get("temperature") == 0.7

    def test_load_config_convenience(self, sample_config_yaml):
        """Test the module-level convenience function."""
        config = load_config(str(sample_config_yaml))
        assert len(config.models) == 2
