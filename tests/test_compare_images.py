import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastmcp import FastMCP

from src.main import create_app
from src.config import Config, ModelConfig

VALID_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4DwAAAQEBABjdcbQAAAAASUVORK5CYII="


def test_load_image_with_path():
    from src.main import _load_image
    from unittest.mock import patch
    
    with patch("src.main.ImageHelper.prepare_image", return_value=("image/png", VALID_PNG_BASE64)):
        result = _load_image("/some/path.png", "path", "png")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "image/png"
        assert result[1] == VALID_PNG_BASE64


def test_load_image_with_base64():
    from src.main import _load_image
    
    result = _load_image(VALID_PNG_BASE64, "base64", "png")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == "image/png"
    assert result[1] == VALID_PNG_BASE64


def test_load_image_invalid_path():
    from src.main import _load_image
    
    with pytest.raises(FileNotFoundError):
        _load_image("/nonexistent/path.png", "path", "png")


def test_compare_images_success():
    config = Config(model=ModelConfig(api_key="sk-test"))
    mock_response = """### 总体对比
两张图片在整体风格上存在明显差异。

### 详细对比分析

**排版布局**
图片1采用居中布局，图片2采用网格布局。

**颜色**
图片1主色调为蓝色，图片2主色调为绿色。

**文字**
图片1包含标题文字，图片2无文字元素。

**风格样式**
图片1为简约风格，图片2为现代风格。

**内容主题**
图片1为主题海报，图片2为产品展示。

**细节差异**
图片1有更多装饰元素，图片2更注重功能性。

### 总结
两张图片在设计风格和内容表达上存在显著差异。"""
    
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.return_value = mock_response
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool(
                    "compare_images",
                    {
                        "image_source_1": VALID_PNG_BASE64,
                        "image_source_2": VALID_PNG_BASE64,
                        "source_type_1": "base64",
                        "source_type_2": "base64",
                    },
                )
            )
            text = result.content[0].text
            assert text == mock_response
            assert "总体对比" in text
            assert "详细对比分析" in text
            assert "排版布局" in text
            assert "颜色" in text


def test_compare_images_error_image1_not_found():
    import json
    config = Config(model=ModelConfig(api_key="sk-test"))
    mock_vision_client = MagicMock()
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool(
                    "compare_images",
                    {
                        "image_source_1": "/nonexistent/path1.png",
                        "image_source_2": VALID_PNG_BASE64,
                        "source_type_1": "path",
                        "source_type_2": "base64",
                    },
                )
            )
            text = result.content[0].text
            error_dict = json.loads(text)
            assert error_dict["error_type"] == "local_error"
            assert error_dict["status_code"] is None
            assert "not found" in error_dict["error_message"].lower()


def test_compare_images_error_image2_not_found():
    import json
    config = Config(model=ModelConfig(api_key="sk-test"))
    mock_vision_client = MagicMock()
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool(
                    "compare_images",
                    {
                        "image_source_1": VALID_PNG_BASE64,
                        "image_source_2": "/nonexistent/path2.png",
                        "source_type_1": "base64",
                        "source_type_2": "path",
                    },
                )
            )
            text = result.content[0].text
            error_dict = json.loads(text)
            assert error_dict["error_type"] == "local_error"
            assert error_dict["status_code"] is None
            assert "not found" in error_dict["error_message"].lower()


def test_compare_images_error_api_failure():
    import json
    config = Config(model=ModelConfig(api_key="sk-test"))
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.side_effect = Exception("API connection failed")
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool(
                    "compare_images",
                    {
                        "image_source_1": VALID_PNG_BASE64,
                        "image_source_2": VALID_PNG_BASE64,
                        "source_type_1": "base64",
                        "source_type_2": "base64",
                    },
                )
            )
            text = result.content[0].text
            error_dict = json.loads(text)
            assert error_dict["error_type"] == "local_error"
            assert error_dict["status_code"] is None
            assert "API connection failed" in error_dict["error_message"]


def test_compare_images_auto_detection():
    config = Config(model=ModelConfig(api_key="sk-test"))
    mock_response = "对比分析结果"
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.return_value = mock_response
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool(
                    "compare_images",
                    {
                        "image_source_1": VALID_PNG_BASE64,
                        "image_source_2": VALID_PNG_BASE64,
                        "source_type_1": "auto",
                        "source_type_2": "auto",
                    },
                )
            )
            text = result.content[0].text
            assert text == mock_response


def test_compare_images_different_detail_levels():
    config = Config(model=ModelConfig(api_key="sk-test"))
    mock_response = "对比分析结果"
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.return_value = mock_response
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool(
                    "compare_images",
                    {
                        "image_source_1": VALID_PNG_BASE64,
                        "image_source_2": VALID_PNG_BASE64,
                        "source_type_1": "base64",
                        "source_type_2": "base64",
                        "detail": "low",
                    },
                )
            )
            assert result.content[0].text == mock_response
            
            result = asyncio.run(
                mcp.call_tool(
                    "compare_images",
                    {
                        "image_source_1": VALID_PNG_BASE64,
                        "image_source_2": VALID_PNG_BASE64,
                        "source_type_1": "base64",
                        "source_type_2": "base64",
                        "detail": "high",
                    },
                )
            )
            assert result.content[0].text == mock_response


def test_compare_images_returns_json_on_api_error():
    """测试compare_images API错误返回JSON"""
    import json
    from pathlib import Path
    from src.vision_client import APIError
    
    config = Config(model=ModelConfig(api_key="sk-test"))
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    
    api_error = APIError(
        status_code=429,
        error_message="Error code: 429 - rate limit exceeded",
        error_type="rate_limit",
        suggestion="请求频率超限，请稍后重试"
    )
    
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.return_value = api_error
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool(
                    "compare_images",
                    {
                        "image_source_1": str(test_image_path),
                        "image_source_2": str(test_image_path)
                    }
                )
            )
    
    text = result.content[0].text
    error_dict = json.loads(text)
    assert error_dict["status_code"] == 429
    assert error_dict["error_type"] == "rate_limit"


def test_compare_images_returns_json_on_local_error():
    """测试compare_images本地错误返回JSON"""
    import json
    
    config = Config(model=ModelConfig(api_key="sk-test"))
    
    with patch("src.main.load_config", return_value=config):
        mcp = create_app()
        
        result = asyncio.run(
            mcp.call_tool(
                "compare_images",
                {
                    "image_source_1": "/nonexistent1.png",
                    "image_source_2": "/nonexistent2.png",
                    "source_type_1": "path",
                    "source_type_2": "path"
                }
            )
        )
    
    text = result.content[0].text
    error_dict = json.loads(text)
    assert error_dict["status_code"] is None
    assert error_dict["error_type"] == "local_error"


def test_compare_images_returns_string_on_success():
    """测试compare_images成功返回字符串"""
    import json
    from pathlib import Path
    
    config = Config(model=ModelConfig(api_key="sk-test"))
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    
    mock_vision_client = MagicMock()
    mock_vision_client.call_model.return_value = "两张图片非常相似"
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.main.VisionClient", return_value=mock_vision_client):
            mcp = create_app()
            
            result = asyncio.run(
                mcp.call_tool(
                    "compare_images",
                    {
                        "image_source_1": str(test_image_path),
                        "image_source_2": str(test_image_path)
                    }
                )
            )
    
    text = result.content[0].text
    assert isinstance(text, str)
    assert not text.startswith("{") or "两张图片非常相似" in text
    if not text.startswith("{"):
        assert text == "两张图片非常相似"
