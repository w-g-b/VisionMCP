from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = Field(..., min_length=1)
    model_name: str = "gpt-4o"
    max_tokens: int = 2048
    timeout: int = 60


class Config(BaseModel):
    model: ModelConfig
    logging: bool = False


def load_config(config_path: Path | None = None) -> Config:
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return Config(**data)
