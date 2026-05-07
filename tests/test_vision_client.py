import pytest
from unittest.mock import patch, MagicMock
from src.config import ModelConfig
from src.vision_client import VisionClient


@pytest.fixture
def model_config():
    return ModelConfig(
        base_url="https://api.example.com/v1",
        api_key="sk-test",
        model_name="gpt-4o",
        max_tokens=1024,
        timeout=30,
    )


def test_vision_client_init(model_config):
    client = VisionClient(model_config)
    assert client._config == model_config


@patch("src.vision_client.OpenAI")
def test_call_model(mock_openai, model_config):
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a cat."
    mock_instance.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_instance

    client = VisionClient(model_config)
    messages = [
        {"role": "system", "content": "Describe the image"},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,aW1hZ2U=",
                        "detail": "auto",
                    },
                },
                {"type": "text", "text": "What is in this image?"},
            ],
        },
    ]

    result = client.call_model(messages)
    assert result == "This is a cat."
    mock_instance.chat.completions.create.assert_called_once()
    call_kwargs = mock_instance.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4o"
    assert call_kwargs["max_tokens"] == 1024


@patch("src.vision_client.OpenAI")
def test_call_model_error(mock_openai, model_config):
    mock_instance = MagicMock()
    mock_instance.chat.completions.create.side_effect = Exception("API error")
    mock_openai.return_value = mock_instance

    client = VisionClient(model_config)
    with pytest.raises(Exception, match="API error"):
        client.call_model([])


@patch("src.vision_client.OpenAI")
def test_call_model_empty_choices_raises(mock_openai, model_config):
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = []
    mock_instance.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_instance

    client = VisionClient(model_config)
    with pytest.raises(ValueError, match="Model returned empty response"):
        client.call_model([])


@patch("src.vision_client.OpenAI")
def test_call_model_none_content_raises(mock_openai, model_config):
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    mock_instance.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_instance

    client = VisionClient(model_config)
    with pytest.raises(ValueError, match="Model returned null content"):
        client.call_model([])
