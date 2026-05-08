from openai import OpenAI
from config import ModelConfig


class VisionClient:
    def __init__(self, config: ModelConfig):
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )

    def call_model(self, messages: list[dict]) -> str:
        response = self._client.chat.completions.create(
            model=self._config.model_name,
            messages=messages,
            max_tokens=self._config.max_tokens,
        )
        if not response.choices:
            raise ValueError("Model returned empty response")
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Model returned null content")
        return content
