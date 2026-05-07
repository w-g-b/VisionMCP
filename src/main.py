import asyncio
from pathlib import Path
from fastmcp import FastMCP

from src.config import load_config
from src.vision_client import VisionClient
from src.image_helper import ImageHelper

config = load_config()
vision = VisionClient(config.model)

mcp = FastMCP("image-mcp")


@mcp.tool()
def describe_image(
    image_source: str,
    source_type: str = "path",
    detail: str = "auto",
) -> str:
    """Describe the content of an image.

    Args:
        image_source: Local file path or base64 encoded image string
        source_type: "path" or "base64"
        detail: "low", "high", or "auto"
    """
    try:
        if source_type == "path":
            mime, b64 = ImageHelper.prepare_image(Path(image_source))
        else:
            mime, b64 = ImageHelper.prepare_image_from_base64(image_source)

        messages = [
            {
                "role": "system",
                "content": "请详细描述这张图片的内容",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}",
                            "detail": detail,
                        },
                    },
                    {"type": "text", "text": "请描述这张图片"},
                ],
            },
        ]
        return vision.call_model(messages)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def ask_image(
    image_source: str,
    question: str,
    source_type: str = "path",
    detail: str = "auto",
) -> str:
    """Ask a question about an image.

    Args:
        image_source: Local file path or base64 encoded image string
        question: The question to ask about the image
        source_type: "path" or "base64"
        detail: "low", "high", or "auto"
    """
    try:
        if source_type == "path":
            mime, b64 = ImageHelper.prepare_image(Path(image_source))
        else:
            mime, b64 = ImageHelper.prepare_image_from_base64(image_source)

        messages = [
            {
                "role": "system",
                "content": "你是一个视觉助手，请根据用户提供的图片回答问题",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}",
                            "detail": detail,
                        },
                    },
                    {"type": "text", "text": question},
                ],
            },
        ]
        return vision.call_model(messages)
    except Exception as e:
        return f"Error: {e}"


def main():
    mcp.run()


if __name__ == "__main__":
    main()
