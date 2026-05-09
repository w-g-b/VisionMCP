import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastmcp import FastMCP

from src.main import create_app
from src.config import Config, ModelConfig

VALID_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4DwAAAQEBABjdcbQAAAAASUVORK5CYII="


def test_create_app_returns_mcp():
    config = Config(model=ModelConfig(api_key="sk-test"))
    with patch("src.main.load_config", return_value=config):
        mcp = create_app()
        assert isinstance(mcp, FastMCP)


def test_describe_image_error_file_not_found():
    import json
    config = Config(model=ModelConfig(api_key="sk-test"))
    with patch("src.main.load_config", return_value=config):
        mcp = create_app()

        result = asyncio.run(
            mcp.call_tool("describe_image", {"image_source": "/nonexistent/path.png", "source_type": "path"})
        )
        text = result.content[0].text
        error_dict = json.loads(text)
        assert error_dict["error_type"] == "local_error"
        assert error_dict["status_code"] is None
        assert "No such file" in error_dict["error_message"] or "not found" in error_dict["error_message"].lower()


def test_ask_image_error_api_failure():
    import json
    config = Config(model=ModelConfig(api_key="sk-test"))
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.side_effect = Exception("API connection failed")
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()

            result = asyncio.run(
                mcp.call_tool(
                    "ask_image",
                    {
                        "image_source": VALID_PNG_BASE64,
                        "question": "What is this?",
                        "source_type": "base64",
                    },
                )
            )
            text = result.content[0].text
            error_dict = json.loads(text)
            assert error_dict["error_type"] == "local_error"
            assert error_dict["status_code"] is None
            assert "API connection failed" in error_dict["error_message"]


def test_describe_image_returns_json_on_api_error():
    """测试API错误返回JSON格式"""
    import json
    from pathlib import Path
    from src.vision_client import APIError
    
    config = Config(model=ModelConfig(api_key="sk-test"))
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    test_image_path.parent.mkdir(exist_ok=True)
    if not test_image_path.exists():
        import base64
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        test_image_path.write_bytes(png_data)
    
    api_error = APIError(
        status_code=404,
        error_message="Error code: 404 - model not found",
        error_type="not_found",
        suggestion="请检查config.yaml中的base_url和model_name配置"
    )
    
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.return_value = api_error
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool("describe_image", {"image_source": str(test_image_path)})
            )
    
    text = result.content[0].text
    assert isinstance(text, str)
    error_dict = json.loads(text)
    assert error_dict["status_code"] == 404
    assert error_dict["error_type"] == "not_found"
    assert "base_url" in error_dict["suggestion"] or "model_name" in error_dict["suggestion"]


def test_describe_image_returns_json_on_local_error():
    """测试本地错误（文件不存在）返回JSON格式"""
    import json
    
    config = Config(model=ModelConfig(api_key="sk-test"))
    
    with patch("src.main.load_config", return_value=config):
        mcp = create_app()
        
        result = asyncio.run(
            mcp.call_tool("describe_image", {"image_source": "/nonexistent/path/image.png", "source_type": "path"})
        )
    
    text = result.content[0].text
    assert isinstance(text, str)
    error_dict = json.loads(text)
    assert error_dict["status_code"] is None
    assert error_dict["error_type"] == "local_error"
    assert "not found" in error_dict["error_message"].lower() or "不存在" in error_dict["error_message"] or "no such file" in error_dict["error_message"].lower()


def test_describe_image_returns_string_on_success():
    """测试成功时返回字符串（非JSON）"""
    import json
    from pathlib import Path
    
    config = Config(model=ModelConfig(api_key="sk-test"))
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.return_value = "这是一张测试图片的描述"
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool("describe_image", {"image_source": str(test_image_path)})
            )
    
    text = result.content[0].text
    assert isinstance(text, str)
    assert not text.startswith("{") or "这是一张测试图片的描述" in text
    if not text.startswith("{"):
        assert text == "这是一张测试图片的描述"


def test_ask_image_returns_json_on_api_error():
    """测试ask_image API错误返回JSON"""
    import json
    from pathlib import Path
    from src.vision_client import APIError
    
    config = Config(model=ModelConfig(api_key="sk-test"))
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    
    api_error = APIError(
        status_code=401,
        error_message="Error code: 401 - invalid api key",
        error_type="auth_error",
        suggestion="请检查config.yaml中的api_key是否正确"
    )
    
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.return_value = api_error
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool(
                    "ask_image",
                    {
                        "image_source": str(test_image_path),
                        "question": "What is in this image?"
                    }
                )
            )
    
    text = result.content[0].text
    error_dict = json.loads(text)
    assert error_dict["status_code"] == 401
    assert error_dict["error_type"] == "auth_error"
    assert "api_key" in error_dict["suggestion"]


def test_ask_image_returns_json_on_local_error():
    """测试ask_image本地错误返回JSON"""
    import json
    
    config = Config(model=ModelConfig(api_key="sk-test"))
    
    with patch("src.main.load_config", return_value=config):
        mcp = create_app()
        
        result = asyncio.run(
            mcp.call_tool(
                "ask_image",
                {
                    "image_source": "/nonexistent/image.png",
                    "question": "What is this?",
                    "source_type": "path"
                }
            )
        )
    
    text = result.content[0].text
    error_dict = json.loads(text)
    assert error_dict["status_code"] is None
    assert error_dict["error_type"] == "local_error"


def test_ask_image_returns_string_on_success():
    """测试ask_image成功返回字符串"""
    import json
    from pathlib import Path
    
    config = Config(model=ModelConfig(api_key="sk-test"))
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.return_value = "这是一个苹果"
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool(
                    "ask_image",
                    {
                        "image_source": str(test_image_path),
                        "question": "What is this?"
                    }
                )
            )
    
    text = result.content[0].text
    assert isinstance(text, str)
    assert not text.startswith("{") or "这是一个苹果" in text
    if not text.startswith("{"):
        assert text == "这是一个苹果"
