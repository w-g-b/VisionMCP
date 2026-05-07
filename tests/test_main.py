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
    config = Config(model=ModelConfig(api_key="sk-test"))
    with patch("src.main.load_config", return_value=config):
        mcp = create_app()

        result = asyncio.run(
            mcp.call_tool("describe_image", {"image_source": "/nonexistent/path.png", "source_type": "path"})
        )
        text = result.content[0].text
        assert text.startswith("Error:")
        assert "No such file" in text or "not found" in text.lower()


def test_ask_image_error_api_failure():
    config = Config(model=ModelConfig(api_key="sk-test"))
    with patch("src.main.load_config", return_value=config):
        with patch("src.vision_client.VisionClient.call_model", side_effect=Exception("API connection failed")):
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
            assert text == "Error: API connection failed"
