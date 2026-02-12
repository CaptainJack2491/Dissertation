"""
Configuration loader for the experiment framework.
Loads config.yaml and provides access to providers, models, scenarios.
"""
import os
import yaml
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    name: str
    api_key_env: str
    base_url: str
    extra_body: Dict[str, Any] = field(default_factory=dict)

    @property
    def api_key(self) -> str:
        """Get API key from environment variable."""
        key = os.environ.get(self.api_key_env)
        if not key:
            raise ValueError(f"Environment variable {self.api_key_env} not set")
        return key


@dataclass
class ModelConfig:
    """Configuration for a model."""
    id: str
    provider: str
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    extra_body: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioConfig:
    """Configuration for a scenario."""
    path: str
    runs: int = 1
    oversight_levels: List[str] = field(default_factory=list)


class ConfigLoader:
    """Load and manage experiment configuration."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._providers: Dict[str, ProviderConfig] = {}
        self._models: List[ModelConfig] = []
        self._scenarios: List[ScenarioConfig] = []

    def load(self) -> None:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

        self._parse_providers()
        self._parse_models()
        self._parse_scenarios()

    def _parse_providers(self) -> None:
        """Parse provider configurations."""
        providers = self._config.get('providers', {})
        for name, config in providers.items():
            self._providers[name] = ProviderConfig(
                name=name,
                api_key_env=config.get('api_key_env', ''),
                base_url=config.get('base_url', ''),
                extra_body=config.get('extra_body', {})
            )

    def _parse_models(self) -> None:
        """Parse model configurations."""
        defaults = self._config.get('defaults', {})
        models = self._config.get('models', [])

        for model in models:
            self._models.append(ModelConfig(
                id=model['id'],
                provider=model['provider'],
                temperature=model.get('temperature', defaults.get('temperature', 1.0)),
                max_tokens=model.get('max_tokens', defaults.get('max_tokens')),
                extra_body=model.get('extra_body', {})
            ))

    def _parse_scenarios(self) -> None:
        """Parse scenario configurations."""
        scenarios = self._config.get('scenarios', [])

        for scenario in scenarios:
            oversight_levels = self._load_oversight_levels(scenario['path'])
            self._scenarios.append(ScenarioConfig(
                path=scenario['path'],
                runs=scenario.get('runs', 1),
                oversight_levels=oversight_levels
            ))

    def _load_oversight_levels(self, scenario_path: str) -> List[str]:
        """
        Load oversight level identifiers from a scenario directory.
        Looks for a subdirectory named 'oversight' containing *.md files.
        Returns the list of filenames without extension.
        If the subdirectory does not exist, falls back to the global
        oversight_levels defined in the config (or an empty list).
        """
        oversight_dir = os.path.join(scenario_path, "oversight")
        if not os.path.isdir(oversight_dir):
            # Fallback to global config oversight levels
            return self._config.get('oversight_levels', [])
        files = [f for f in os.listdir(oversight_dir) if f.endswith('.md')]
        return [os.path.splitext(f)[0] for f in files]

    @property
    def providers(self) -> Dict[str, ProviderConfig]:
        """Get all provider configurations."""
        return self._providers

    @property
    def models(self) -> List[ModelConfig]:
        """Get all model configurations."""
        return self._models

    @property
    def scenarios(self) -> List[ScenarioConfig]:
        """Get all scenario configurations."""
        return self._scenarios

    @property
    def oversight_levels(self) -> List[str]:
        """Get global oversight levels to test (used as fallback)."""
        return self._config.get('oversight_levels', ['low'])

    @property
    def defaults(self) -> Dict[str, Any]:
        """Get default configuration."""
        return self._config.get('defaults', {})

    @property
    def output_dir(self) -> str:
        """Get output directory."""
        return self._config.get('output', {}).get('dir', 'output')

    def get_provider(self, name: str) -> ProviderConfig:
        """Get a specific provider configuration."""
        if name not in self._providers:
            raise ValueError(f"Unknown provider: {name}")
        return self._providers[name]

    def get_model(self, model_id: str) -> ModelConfig:
        """Get a specific model configuration."""
        for model in self._models:
            if model.id == model_id:
                return model
        raise ValueError(f"Unknown model: {model_id}")

    def get_scenario(self, path: str) -> ScenarioConfig:
        """Get a specific scenario configuration."""
        for scenario in self._scenarios:
            if scenario.path == path:
                return scenario
        raise ValueError(f"Unknown scenario: {path}")


def load_config(config_path: str = "config.yaml") -> ConfigLoader:
    """Convenience function to load configuration."""
    loader = ConfigLoader(config_path)
    loader.load()
    return loader
