from pathlib import Path
from fastmcp import FastMCP

from config import load_config
from vision_client import VisionClient
from image_helper import ImageHelper
from image_extractor import is_image_reference, extract_image_by_reference

DESCRIBE_SYSTEM_PROMPT = "请详细描述这张图片的内容"
ASK_SYSTEM_PROMPT = "你是一个视觉助手，请根据用户提供的图片回答问题"


def create_app() -> FastMCP:
    config = load_config()
    vision = VisionClient(config.model)
    mcp = FastMCP("vision-mcp")

    @mcp.tool()
    def describe_image(
        image_source: str,
        source_type: str = "auto",
        detail: str = "auto",
        image_format: str = "png",
    ) -> str:
        """Describe the content of an image.

        Args:
            image_source: Image source - can be:
                - Image reference like "[Image 1]" (from OpenCode paste)
                - Local file path
                - Base64 encoded string
            source_type: Source type detection mode:
                - "auto": Auto-detect source type (recommended)
                - "path": Treat as file path
                - "base64": Treat as base64 string
            detail: Detail level for image analysis ("low", "high", "auto")
            image_format: Image format when using base64 (default "png")
        
        Returns:
            Image description text or error message starting with "Error: "
        """
        try:
            image_source = image_source.strip()
            
            if source_type == "auto":
                if is_image_reference(image_source):
                    mime, b64 = extract_image_by_reference(image_source)
                elif Path(image_source).exists():
                    mime, b64 = ImageHelper.prepare_image(Path(image_source))
                else:
                    mime, b64 = ImageHelper.prepare_image_from_base64(
                        image_source, image_format
                    )
            elif source_type == "path":
                mime, b64 = ImageHelper.prepare_image(Path(image_source))
            else:
                mime, b64 = ImageHelper.prepare_image_from_base64(
                    image_source, image_format
                )
            
            messages = [
                {"role": "system", "content": DESCRIBE_SYSTEM_PROMPT},
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
        source_type: str = "auto",
        detail: str = "auto",
        image_format: str = "png",
    ) -> str:
        """Ask a question about an image.

        Args:
            image_source: Image source - can be:
                - Image reference like "[Image 1]" (from OpenCode paste)
                - Local file path
                - Base64 encoded string
            question: The question to ask about the image
            source_type: Source type detection mode:
                - "auto": Auto-detect source type (recommended)
                - "path": Treat as file path
                - "base64": Treat as base64 string
            detail: Detail level for image analysis ("low", "high", "auto")
            image_format: Image format when using base64 (default "png")
        
        Returns:
            Answer to the question or error message starting with "Error: "
        """
        try:
            image_source = image_source.strip()
            question = question.strip()
            
            if source_type == "auto":
                if is_image_reference(image_source):
                    mime, b64 = extract_image_by_reference(image_source)
                elif Path(image_source).exists():
                    mime, b64 = ImageHelper.prepare_image(Path(image_source))
                else:
                    mime, b64 = ImageHelper.prepare_image_from_base64(
                        image_source, image_format
                    )
            elif source_type == "path":
                mime, b64 = ImageHelper.prepare_image(Path(image_source))
            else:
                mime, b64 = ImageHelper.prepare_image_from_base64(
                    image_source, image_format
                )
            
            messages = [
                {"role": "system", "content": ASK_SYSTEM_PROMPT},
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

    return mcp


def main():
    mcp = create_app()
    mcp.run()


if __name__ == "__main__":
    main()
