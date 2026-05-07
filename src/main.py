from pathlib import Path
from fastmcp import FastMCP

from src.config import load_config
from src.vision_client import VisionClient
from src.image_helper import ImageHelper
from src.image_extractor import is_image_reference, extract_image_by_reference

DESCRIBE_SYSTEM_PROMPT = "请详细描述这张图片的内容"
ASK_SYSTEM_PROMPT = "你是一个视觉助手，请根据用户提供的图片回答问题"


def create_app() -> FastMCP:
    config = load_config()
    vision = VisionClient(config.model)
    mcp = FastMCP("vision-mcp")

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
        """
        try:
            if source_type == "auto":
                image_source_stripped = image_source.strip()
                
                if is_image_reference(image_source_stripped):
                    mime, b64 = extract_image_by_reference(image_source_stripped)
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
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            return f"Error: {e}"
        except Exception as e:
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
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def debug_image_input(image_data: str) -> str:
        """Debug tool to analyze the format of image input from OpenCode.

        Args:
            image_data: The image data passed by OpenCode (unknown format)
        """
        import json
        import os

        result = {
            "type": str(type(image_data).__name__),
            "length": len(image_data),
        }

        if isinstance(image_data, str):
            preview = image_data[:200] if len(image_data) > 200 else image_data
            result["preview"] = preview

            if image_data.startswith("data:image/"):
                result["detected_format"] = "data URI"
                parts = image_data.split(",", 1)
                if len(parts) == 2:
                    mime_part = parts[0]
                    result["mime_type"] = mime_part.replace("data:", "").split(";")[0]
                    result["base64_part_length"] = len(parts[1])
            elif os.path.exists(image_data):
                result["detected_format"] = "file path"
                result["file_exists"] = True
                result["file_size"] = os.path.getsize(image_data)
                result["is_absolute"] = os.path.isabs(image_data)
            else:
                try:
                    import base64
                    base64.b64decode(image_data[:100], validate=True)
                    result["detected_format"] = "base64 string"
                except Exception:
                    result["detected_format"] = "unknown"

        return json.dumps(result, indent=2, ensure_ascii=False)

    return mcp


def main():
    mcp = create_app()
    mcp.run()


if __name__ == "__main__":
    main()
