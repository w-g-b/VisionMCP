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
            assert text.startswith("Error:")
            assert "not found" in text.lower() or "No such file" in text


def test_compare_images_error_image2_not_found():
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
            assert text.startswith("Error:")
            assert "not found" in text.lower() or "No such file" in text


def test_compare_images_error_api_failure():
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
            assert text == "Error: API connection failed"


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
