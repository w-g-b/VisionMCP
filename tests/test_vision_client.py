import pytest
from unittest.mock import Mock, patch, MagicMock
from src.config import ModelConfig
from src.vision_client import VisionClient, APIError
from openai import APIStatusError


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
    result = client.call_model([])
    assert isinstance(result, APIError)
    assert result.error_type == "unknown"
    assert result.error_message == "API error"


@patch("src.vision_client.OpenAI")
def test_call_model_empty_choices_returns_error(mock_openai, model_config):
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = []
    mock_instance.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_instance

    client = VisionClient(model_config)
    result = client.call_model([])
    assert isinstance(result, APIError)
    assert result.error_type == "server_error"
    assert "空响应" in result.suggestion


@patch("src.vision_client.OpenAI")
def test_call_model_none_content_returns_error(mock_openai, model_config):
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    mock_instance.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_instance

    client = VisionClient(model_config)
    result = client.call_model([])
    assert isinstance(result, APIError)
    assert result.error_type == "server_error"
    assert "空内容" in result.suggestion


def test_call_model_returns_string_on_success():
    """测试正常响应返回字符串"""
    config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    client = VisionClient(config)
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "测试响应内容"
    
    with patch.object(client._client.chat.completions, 'create', return_value=mock_response):
        result = client.call_model([{"role": "user", "content": "test"}])
        
    assert isinstance(result, str)
    assert result == "测试响应内容"


def test_call_model_returns_api_error_on_404():
    """测试404错误返回APIError对象"""
    config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    client = VisionClient(config)
    
    mock_response = Mock()
    mock_response.status_code = 404
    
    mock_error = APIStatusError(
        message="Error code: 404 - model not found",
        response=mock_response,
        body=None
    )
    
    with patch.object(client._client.chat.completions, 'create', side_effect=mock_error):
        result = client.call_model([{"role": "user", "content": "test"}])
        
    assert isinstance(result, APIError)
    assert result.status_code == 404
    assert result.error_type == "not_found"
    assert "base_url" in result.suggestion.lower() or "model_name" in result.suggestion.lower()


def test_call_model_returns_api_error_on_401():
    """测试401错误返回APIError对象"""
    config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    client = VisionClient(config)
    
    mock_response = Mock()
    mock_response.status_code = 401
    
    mock_error = APIStatusError(
        message="Error code: 401 - invalid api key",
        response=mock_response,
        body=None
    )
    
    with patch.object(client._client.chat.completions, 'create', side_effect=mock_error):
        result = client.call_model([{"role": "user", "content": "test"}])
        
    assert isinstance(result, APIError)
    assert result.status_code == 401
    assert result.error_type == "auth_error"
    assert "api_key" in result.suggestion.lower()


def test_call_model_returns_api_error_on_network_error():
    """测试网络错误返回APIError对象"""
    config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    client = VisionClient(config)
    
    with patch.object(client._client.chat.completions, 'create', side_effect=Exception("Connection timeout")):
        result = client.call_model([{"role": "user", "content": "test"}])
        
    assert isinstance(result, APIError)
    assert result.status_code is None
    assert result.error_type == "network_error"
    assert "网络" in result.suggestion


def test_call_model_returns_api_error_on_empty_response():
    """测试空响应返回APIError对象"""
    config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    client = VisionClient(config)
    
    mock_response = Mock()
    mock_response.choices = []
    
    with patch.object(client._client.chat.completions, 'create', return_value=mock_response):
        result = client.call_model([{"role": "user", "content": "test"}])
        
    assert isinstance(result, APIError)
    assert result.error_type == "server_error"
    assert result.status_code is None
