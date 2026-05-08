from datetime import datetime
from pathlib import Path
import json
from fastmcp import FastMCP

from .config import load_config
from .vision_client import VisionClient, APIError
from .image_helper import ImageHelper
from .image_extractor import is_image_reference, extract_image_by_reference
from .logger import ImageRequestLogger


def _load_image(image_source: str, source_type: str, image_format: str) -> tuple[str, str]:
    """加载图片并返回mime和base64数据"""
    image_source = image_source.strip()
    
    if source_type == "auto":
        if is_image_reference(image_source):
            return extract_image_by_reference(image_source)
        elif Path(image_source).exists():
            return ImageHelper.prepare_image(Path(image_source))
        else:
            return ImageHelper.prepare_image_from_base64(image_source, image_format)
    elif source_type == "path":
        return ImageHelper.prepare_image(Path(image_source))
    else:
        return ImageHelper.prepare_image_from_base64(image_source, image_format)


DESCRIBE_SYSTEM_PROMPT = "请详细描述这张图片的内容"
ASK_SYSTEM_PROMPT = "你是一个视觉助手，请根据用户提供的图片回答问题"
COMPARE_SYSTEM_PROMPT = """你是一个专业的视觉对比分析助手。请对比两张图片，从以下维度进行详细分析：

## 对比维度

1. **排版布局**
   - 元素位置和分布差异
   - 层次结构对比
   - 空间利用差异

2. **颜色**
   - 主色调差异
   - 色彩对比度变化
   - 调色板差异

3. **文字**
   - 文字内容差异
   - 字体样式对比
   - 文字排版差异

4. **风格样式**
   - 整体风格特征差异
   - 设计元素对比
   - 视觉效果差异

5. **内容主题**
   - 主题内容差异
   - 语义表达对比
   - 信息传达差异

6. **细节差异**
   - 关键细节变化
   - 细微差异识别
   - 整体细节对比

## 输出格式

请按照以下结构返回对比分析结果：

### 总体对比
[简要说明两张图片的主要差异和相似之处]

### 详细对比分析

**排版布局**
[具体的排版布局差异分析]

**颜色**
[颜色差异分析]

**文字**
[文字差异分析]

**风格样式**
[风格样式差异分析]

**内容主题**
[内容主题差异分析]

**细节差异**
[细节差异分析]

### 总结
[关键差异点的总结]"""


def _format_error_json(
    status_code: int | None,
    error_message: str,
    error_type: str,
    suggestion: str
) -> str:
    """Format error information as JSON string.
    
    Args:
        status_code: HTTP status code or None for local errors
        error_message: Detailed error message
        error_type: Error type classification
        suggestion: User-friendly suggestion
        
    Returns:
        JSON formatted error string
    """
    return json.dumps({
        "status_code": status_code,
        "error_message": error_message,
        "error_type": error_type,
        "suggestion": suggestion
    }, ensure_ascii=False, indent=2)


def create_app() -> FastMCP:
    config = load_config()
    vision = VisionClient(config.model)
    logger = ImageRequestLogger(enabled=config.logging)
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
            Image description text or error message in JSON format
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
            
            image_url = f"data:{mime};base64,{b64}"
            logger.log_request(
                tool_name="describe_image",
                timestamp=datetime.now().isoformat(),
                image_urls=[image_url],
                source_type=source_type,
                detail=detail,
                image_format=image_format
            )
            
            messages = [
                {"role": "system", "content": DESCRIBE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": detail,
                            },
                        },
                        {"type": "text", "text": "请描述这张图片"},
                    ],
                },
            ]
            
            result = vision.call_model(messages)
            
            if isinstance(result, APIError):
                return _format_error_json(
                    result.status_code,
                    result.error_message,
                    result.error_type,
                    result.suggestion
                )
            
            return result
        except Exception as e:
            return _format_error_json(
                None,
                str(e),
                "local_error",
                "请检查输入参数是否正确"
            )

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
            Answer to the question or error message in JSON format
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
            
            image_url = f"data:{mime};base64,{b64}"
            logger.log_request(
                tool_name="ask_image",
                timestamp=datetime.now().isoformat(),
                image_urls=[image_url],
                source_type=source_type,
                detail=detail,
                image_format=image_format,
                question=question
            )
            
            messages = [
                {"role": "system", "content": ASK_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": detail,
                            },
                        },
                        {"type": "text", "text": question},
                    ],
                },
            ]
            
            result = vision.call_model(messages)
            
            if isinstance(result, APIError):
                return _format_error_json(
                    result.status_code,
                    result.error_message,
                    result.error_type,
                    result.suggestion
                )
            
            return result
        except Exception as e:
            return _format_error_json(
                None,
                str(e),
                "local_error",
                "请检查输入参数是否正确"
            )

    @mcp.tool()
    def compare_images(
        image_source_1: str,
        image_source_2: str,
        source_type_1: str = "auto",
        source_type_2: str = "auto",
        detail: str = "auto",
        image_format_1: str = "png",
        image_format_2: str = "png",
    ) -> str:
        """Compare two images and analyze their differences across multiple dimensions.

        Args:
            image_source_1: First image source - can be:
                - Image reference like "[Image 1]" (from OpenCode paste)
                - Local file path
                - Base64 encoded string
            image_source_2: Second image source - can be:
                - Image reference like "[Image 2]" (from OpenCode paste)
                - Local file path
                - Base64 encoded string
            source_type_1: Source type for first image:
                - "auto": Auto-detect source type (recommended)
                - "path": Treat as file path
                - "base64": Treat as base64 string
            source_type_2: Source type for second image:
                - "auto": Auto-detect source type (recommended)
                - "path": Treat as file path
                - "base64": Treat as base64 string
            detail: Detail level for image analysis ("low", "high", "auto")
            image_format_1: Image format for first base64 image (default "png")
            image_format_2: Image format for second base64 image (default "png")
        
        Returns:
            Structured comparison analysis or error message in JSON format
        """
        try:
            mime_1, b64_1 = _load_image(image_source_1, source_type_1, image_format_1)
            mime_2, b64_2 = _load_image(image_source_2, source_type_2, image_format_2)
            
            image_url_1 = f"data:{mime_1};base64,{b64_1}"
            image_url_2 = f"data:{mime_2};base64,{b64_2}"
            logger.log_request(
                tool_name="compare_images",
                timestamp=datetime.now().isoformat(),
                image_urls=[image_url_1, image_url_2],
                source_type=source_type_1,
                detail=detail,
                image_format=image_format_1
            )
            
            messages = [
                {"role": "system", "content": COMPARE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url_1,
                                "detail": detail,
                            },
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url_2,
                                "detail": detail,
                            },
                        },
                        {"type": "text", "text": "请对比这两张图片"},
                    ],
                },
            ]
            
            result = vision.call_model(messages)
            
            if isinstance(result, APIError):
                return _format_error_json(
                    result.status_code,
                    result.error_message,
                    result.error_type,
                    result.suggestion
                )
            
            return result
        except Exception as e:
            return _format_error_json(
                None,
                str(e),
                "local_error",
                "请检查输入参数是否正确"
            )

    return mcp


def main():
    mcp = create_app()
    mcp.run()


if __name__ == "__main__":
    main()
