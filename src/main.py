from pathlib import Path
from fastmcp import FastMCP

from src.config import load_config
from src.vision_client import VisionClient
from src.image_helper import ImageHelper

DESCRIBE_SYSTEM_PROMPT = "请详细描述这张图片的内容"
ASK_SYSTEM_PROMPT = "你是一个视觉助手，请根据用户提供的图片回答问题"


def create_app() -> FastMCP:
    config = load_config()
    vision = VisionClient(config.model)
    mcp = FastMCP("image-mcp")

    def _build_messages(
        system_prompt: str,
        user_text: str,
        image_source: str,
        source_type: str,
        detail: str,
        image_format: str = "png",
    ) -> list[dict]:
        if source_type not in ("path", "base64"):
            raise ValueError("source_type must be 'path' or 'base64'")

        if source_type == "path":
            mime, b64 = ImageHelper.prepare_image(Path(image_source))
        else:
            mime, b64 = ImageHelper.prepare_image_from_base64(image_source, image_format)

        return [
            {"role": "system", "content": system_prompt},
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
                    {"type": "text", "text": user_text},
                ],
            },
        ]

    @mcp.tool()
    def describe_image(
        image_source: str,
        source_type: str = "path",
        detail: str = "auto",
        image_format: str = "png",
    ) -> str:
        """Describe the content of an image.

        Args:
            image_source: Local file path or base64 encoded image string
            source_type: "path" or "base64"
            detail: "low", "high", or "auto"
            image_format: Image format for base64 input (default "png")
        """
        try:
            messages = _build_messages(
                DESCRIBE_SYSTEM_PROMPT,
                "请描述这张图片",
                image_source,
                source_type,
                detail,
                image_format,
            )
            return vision.call_model(messages)
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def ask_image(
        image_source: str,
        question: str,
        source_type: str = "path",
        detail: str = "auto",
        image_format: str = "png",
    ) -> str:
        """Ask a question about an image.

        Args:
            image_source: Local file path or base64 encoded image string
            question: The question to ask about the image
            source_type: "path" or "base64"
            detail: "low", "high", or "auto"
            image_format: Image format for base64 input (default "png")
        """
        try:
            messages = _build_messages(
                ASK_SYSTEM_PROMPT,
                question,
                image_source,
                source_type,
                detail,
                image_format,
            )
            return vision.call_model(messages)
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            return f"Error: {e}"

    return mcp


def main():
    mcp = create_app()
    mcp.run()


if __name__ == "__main__":
    main()
