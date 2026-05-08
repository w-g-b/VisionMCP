import pytest
from pathlib import Path
from src.config import Config, load_config, ModelConfig


def test_load_valid_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
model:
  base_url: "https://api.example.com/v1"
  api_key: "sk-test-key"
  model_name: "gpt-4o"
  max_tokens: 1024
  timeout: 30

config:
  logging: true
""")
    config = load_config(config_file)
    assert config.model.base_url == "https://api.example.com/v1"
    assert config.model.api_key == "sk-test-key"
    assert config.model.model_name == "gpt-4o"
    assert config.model.max_tokens == 1024
    assert config.model.timeout == 30
    assert config.logging == True


def test_missing_api_key_raises(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
model:
  base_url: "https://api.example.com/v1"
  api_key: ""
  model_name: "gpt-4o"
""")
    with pytest.raises(ValueError, match="api_key"):
        load_config(config_file)


def test_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/config.yaml"))


def test_config_with_logging():
    """Test Config accepts logging field"""
    model_config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    config = Config(model=model_config, logging=True)
    assert config.logging == True
    
    config_disabled = Config(model=model_config)
    assert config_disabled.logging == False


def test_load_config_defaults_logging_to_false(tmp_path):
    """Test logging defaults to False when config section missing"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
model:
  base_url: "https://api.example.com/v1"
  api_key: "sk-test-key"
""")
    config = load_config(config_file)
    assert config.logging == False


def test_load_config_with_logging_enabled(tmp_path):
    """Test loading config with logging enabled"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
model:
  base_url: "https://api.example.com/v1"
  api_key: "sk-test-key"

config:
  logging: true
""")
    config = load_config(config_file)
    assert config.logging == True
