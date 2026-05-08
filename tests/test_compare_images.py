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
