from openai import OpenAI
from src.config import ModelConfig


class VisionClient:
    def __init__(self, config: ModelConfig):
        self.config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )

    def call_model(self, messages: list[dict]) -> str:
        response = self._client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content
