# Vision MCP 增强错误提示实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为Vision MCP工具增强错误提示，使其返回包含HTTP状态码、错误消息、错误类型和建议的结构化JSON格式错误信息。

**Architecture:** 在VisionClient中捕获OpenAI API异常并返回APIError数据类对象，在main.py的tool函数中将APIError转换为JSON格式返回，同时处理本地异常。

**Tech Stack:** Python 3.10+, OpenAI SDK, FastMCP, pytest

---

## 文件结构

**修改文件：**
- `src/vision_client.py` - 添加APIError数据类，改进call_model方法捕获异常并返回APIError
- `src/main.py` - 修改describe_image、ask_image、compare_images三个tool函数的错误处理逻辑
- `tests/test_vision_client.py` - 添加APIError异常处理测试
- `tests/test_main.py` - 添加JSON错误返回格式测试

**文件职责：**
- `src/vision_client.py`: API调用和错误捕获，返回APIError对象或正常结果
- `src/main.py`: 检测返回类型，转换为JSON格式，处理本地异常
- 测试文件: 验证错误处理逻辑和JSON格式

---

### Task 1: 添加APIError数据类和错误映射函数

**Files:**
- Modify: `src/vision_client.py`

- [ ] **Step 1: 在vision_client.py顶部添加导入和数据类**

```python
from dataclasses import dataclass
from typing import Optional
from openai import OpenAI, APIStatusError, APIError as OpenAI_APIError
from config import ModelConfig


@dataclass
class APIError:
    status_code: Optional[int]
    error_message: str
    error_type: str
    suggestion: str


def _get_error_info(status_code: Optional[int], message: str) -> dict:
    """根据HTTP状态码映射错误类型和建议"""
    error_mapping = {
        400: {
            "error_type": "invalid_request",
            "suggestion": "请求参数无效，请检查图片格式或请求内容"
        },
        401: {
            "error_type": "auth_error",
            "suggestion": "请检查config.yaml中的api_key是否正确"
        },
        403: {
            "error_type": "auth_error",
            "suggestion": "权限不足，请检查api_key权限或model_name配置"
        },
        404: {
            "error_type": "not_found",
            "suggestion": "请检查config.yaml中的base_url和model_name配置，确认API端点正确"
        },
        429: {
            "error_type": "rate_limit",
            "suggestion": "请求频率超限，请稍后重试"
        },
        500: {
            "error_type": "server_error",
            "suggestion": "API服务器错误，请稍后重试"
        },
        502: {
            "error_type": "server_error",
            "suggestion": "API网关错误，请稍后重试"
        },
        503: {
            "error_type": "server_error",
            "suggestion": "API服务不可用，请稍后重试"
        }
    }
    
    if status_code and status_code in error_mapping:
        info = error_mapping[status_code]
    else:
        info = {
            "error_type": "unknown",
            "suggestion": "未知错误，请查看错误消息详情"
        }
    
    info["status_code"] = status_code
    info["error_message"] = message
    return info


class VisionClient:
    # ... existing code
```

- [ ] **Step 2: 验证文件修改正确**

Read `src/vision_client.py` and confirm imports and dataclass are added correctly at the top.

- [ ] **Step 3: 提交修改**

```bash
git add src/vision_client.py
git commit -m "feat: add APIError dataclass and error mapping function"
```

---

### Task 2: 改进VisionClient的call_model方法

**Files:**
- Modify: `src/vision_client.py:14-25`

- [ ] **Step 1: 编写call_model方法的测试用例**

Add to `tests/test_vision_client.py`:

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from vision_client import VisionClient, APIError
from config import ModelConfig
from openai import APIStatusError, APIError as OpenAI_APIError


def test_call_model_returns_string_on_success():
    """测试正常响应返回字符串"""
    config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    client = VisionClient(config)
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "测试响应内容"
    
    with patch.object(client._client.chat.completions, 'create', return_value=mock_response):
        result = client.call_model([{"role": "user", "content": "test"}])
        
    assert isinstance(result, str)
    assert result == "测试响应内容"


def test_call_model_returns_api_error_on_404():
    """测试404错误返回APIError对象"""
    config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    client = VisionClient(config)
    
    mock_error = APIStatusError(
        message="Error code: 404 - model not found",
        response=Mock(status_code=404),
        body=None
    )
    
    with patch.object(client._client.chat.completions, 'create', side_effect=mock_error):
        result = client.call_model([{"role": "user", "content": "test"}])
        
    assert isinstance(result, APIError)
    assert result.status_code == 404
    assert result.error_type == "not_found"
    assert "base_url" in result.suggestion.lower() or "model_name" in result.suggestion.lower()


def test_call_model_returns_api_error_on_401():
    """测试401错误返回APIError对象"""
    config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    client = VisionClient(config)
    
    mock_error = APIStatusError(
        message="Error code: 401 - invalid api key",
        response=Mock(status_code=401),
        body=None
    )
    
    with patch.object(client._client.chat.completions, 'create', side_effect=mock_error):
        result = client.call_model([{"role": "user", "content": "test"}])
        
    assert isinstance(result, APIError)
    assert result.status_code == 401
    assert result.error_type == "auth_error"
    assert "api_key" in result.suggestion.lower()


def test_call_model_returns_api_error_on_network_error():
    """测试网络错误返回APIError对象"""
    config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    client = VisionClient(config)
    
    with patch.object(client._client.chat.completions, 'create', side_effect=Exception("Connection timeout")):
        result = client.call_model([{"role": "user", "content": "test"}])
        
    assert isinstance(result, APIError)
    assert result.status_code is None
    assert result.error_type == "network_error"
    assert "网络" in result.suggestion


def test_call_model_returns_api_error_on_empty_response():
    """测试空响应返回APIError对象"""
    config = ModelConfig(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model_name="gpt-4o",
        max_tokens=2048,
        timeout=60
    )
    
    client = VisionClient(config)
    
    mock_response = Mock()
    mock_response.choices = []
    
    with patch.object(client._client.chat.completions, 'create', return_value=mock_response):
        result = client.call_model([{"role": "user", "content": "test"}])
        
    assert isinstance(result, APIError)
    assert result.error_type == "server_error"
    assert result.status_code is None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_vision_client.py -v
```

Expected: Tests fail because call_model doesn't return APIError yet.

- [ ] **Step 3: 修改call_model方法实现异常捕获**

Replace the `call_model` method in `src/vision_client.py`:

```python
def call_model(self, messages: list[dict]) -> str | APIError:
    try:
        response = self._client.chat.completions.create(
            model=self._config.model_name,
            messages=messages,
            max_tokens=self._config.max_tokens,
        )
        if not response.choices:
            return APIError(
                status_code=None,
                error_message="Model returned empty response",
                error_type="server_error",
                suggestion="API返回空响应，请稍后重试"
            )
        content = response.choices[0].message.content
        if content is None:
            return APIError(
                status_code=None,
                error_message="Model returned null content",
                error_type="server_error",
                suggestion="API返回空内容，请稍后重试"
            )
        return content
    except APIStatusError as e:
        error_info = _get_error_info(e.status_code, str(e))
        return APIError(**error_info)
    except OpenAI_APIError as e:
        return APIError(
            status_code=None,
            error_message=str(e),
            error_type="api_error",
            suggestion="API调用失败，请检查配置或稍后重试"
        )
    except Exception as e:
        error_message = str(e).lower()
        if "connection" in error_message or "timeout" in error_message:
            return APIError(
                status_code=None,
                error_message=str(e),
                error_type="network_error",
                suggestion="网络连接失败，请检查网络或base_url配置"
            )
        return APIError(
            status_code=None,
            error_message=str(e),
            error_type="unknown",
            suggestion="未知错误，请查看错误消息详情"
        )
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_vision_client.py -v
```

Expected: All tests pass.

- [ ] **Step 5: 提交修改**

```bash
git add src/vision_client.py tests/test_vision_client.py
git commit -m "feat: enhance call_model with structured error handling"
```

---

### Task 3: 修改describe_image工具的错误处理

**Files:**
- Modify: `src/main.py:99-161`

- [ ] **Step 1: 编写describe_image的JSON错误返回测试**

Add to `tests/test_main.py`:

```python
import json
from main import create_app
from vision_client import APIError


def test_describe_image_returns_json_on_api_error():
    """测试API错误返回JSON格式"""
    app = create_app()
    describe_image = app._tool_manager._tools['describe_image'].fn
    
    with patch('vision_client.VisionClient.call_model') as mock_call:
        mock_call.return_value = APIError(
            status_code=404,
            error_message="Error code: 404 - model not found",
            error_type="not_found",
            suggestion="请检查config.yaml中的base_url和model_name配置"
        )
        
        result = describe_image("[Image 1]")
        
    assert isinstance(result, str)
    error_dict = json.loads(result)
    assert error_dict["status_code"] == 404
    assert error_dict["error_type"] == "not_found"
    assert "base_url" in error_dict["suggestion"]


def test_describe_image_returns_json_on_local_error():
    """测试本地错误返回JSON格式"""
    app = create_app()
    describe_image = app._tool_manager._tools['describe_image'].fn
    
    result = describe_image("/nonexistent/path/image.png")
    
    assert isinstance(result, str)
    error_dict = json.loads(result)
    assert error_dict["status_code"] is None
    assert error_dict["error_type"] == "local_error"
    assert "not found" in error_dict["error_message"].lower() or "不存在" in error_dict["error_message"]


def test_describe_image_returns_string_on_success():
    """测试成功时返回字符串（非JSON）"""
    app = create_app()
    describe_image = app._tool_manager._tools['describe_image'].fn
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    
    with patch('vision_client.VisionClient.call_model') as mock_call:
        mock_call.return_value = "这是一张测试图片的描述"
        
        result = describe_image(str(test_image_path))
        
    assert isinstance(result, str)
    assert not result.startswith("{")
    assert result == "这是一张测试图片的描述"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_main.py::test_describe_image -v
```

Expected: Tests fail because describe_image doesn't return JSON on errors.

- [ ] **Step 3: 在main.py顶部添加json导入**

Add to imports in `src/main.py`:

```python
from pathlib import Path
import json
from fastmcp import FastMCP

from config import load_config
from vision_client import VisionClient, APIError
from image_helper import ImageHelper
from image_extractor import is_image_reference, extract_image_by_reference
```

- [ ] **Step 4: 修改describe_image工具的错误处理**

Replace the describe_image function in `src/main.py` (lines 99-161):

```python
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
        
        result = vision.call_model(messages)
        
        if isinstance(result, APIError):
            return json.dumps({
                "status_code": result.status_code,
                "error_message": result.error_message,
                "error_type": result.error_type,
                "suggestion": result.suggestion
            }, ensure_ascii=False, indent=2)
        
        return result
    except Exception as e:
        return json.dumps({
            "status_code": None,
            "error_message": str(e),
            "error_type": "local_error",
            "suggestion": "请检查输入参数是否正确"
        }, ensure_ascii=False, indent=2)
```

- [ ] **Step 5: 运行测试验证通过**

```bash
pytest tests/test_main.py::test_describe_image -v
```

Expected: All tests pass.

- [ ] **Step 6: 提交修改**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: enhance describe_image with JSON error handling"
```

---

### Task 4: 修改ask_image工具的错误处理

**Files:**
- Modify: `src/main.py:162-227`

- [ ] **Step 1: 编写ask_image的JSON错误返回测试**

Add to `tests/test_main.py`:

```python
def test_ask_image_returns_json_on_api_error():
    """测试API错误返回JSON格式"""
    app = create_app()
    ask_image = app._tool_manager._tools['ask_image'].fn
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    
    with patch('vision_client.VisionClient.call_model') as mock_call:
        mock_call.return_value = APIError(
            status_code=401,
            error_message="Error code: 401 - invalid api key",
            error_type="auth_error",
            suggestion="请检查config.yaml中的api_key是否正确"
        )
        
        result = ask_image(str(test_image_path), "What is this?")
        
    assert isinstance(result, str)
    error_dict = json.loads(result)
    assert error_dict["status_code"] == 401
    assert error_dict["error_type"] == "auth_error"
    assert "api_key" in error_dict["suggestion"]


def test_ask_image_returns_json_on_local_error():
    """测试本地错误返回JSON格式"""
    app = create_app()
    ask_image = app._tool_manager._tools['ask_image'].fn
    
    result = ask_image("/nonexistent/image.png", "What is this?")
    
    assert isinstance(result, str)
    error_dict = json.loads(result)
    assert error_dict["status_code"] is None
    assert error_dict["error_type"] == "local_error"


def test_ask_image_returns_string_on_success():
    """测试成功时返回字符串"""
    app = create_app()
    ask_image = app._tool_manager._tools['ask_image'].fn
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    
    with patch('vision_client.VisionClient.call_model') as mock_call:
        mock_call.return_value = "这是一个测试回答"
        
        result = ask_image(str(test_image_path), "What is this?")
        
    assert isinstance(result, str)
    assert result == "这是一个测试回答"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_main.py::test_ask_image -v
```

Expected: Tests fail.

- [ ] **Step 3: 修改ask_image工具的错误处理**

Replace the ask_image function in `src/main.py` (lines 162-227):

```python
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
        
        result = vision.call_model(messages)
        
        if isinstance(result, APIError):
            return json.dumps({
                "status_code": result.status_code,
                "error_message": result.error_message,
                "error_type": result.error_type,
                "suggestion": result.suggestion
            }, ensure_ascii=False, indent=2)
        
        return result
    except Exception as e:
        return json.dumps({
            "status_code": None,
            "error_message": str(e),
            "error_type": "local_error",
            "suggestion": "请检查输入参数是否正确"
        }, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_main.py::test_ask_image -v
```

Expected: All tests pass.

- [ ] **Step 5: 提交修改**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: enhance ask_image with JSON error handling"
```

---

### Task 5: 修改compare_images工具的错误处理

**Files:**
- Modify: `src/main.py:228-294`

- [ ] **Step 1: 编写compare_images的JSON错误返回测试**

Add to `tests/test_compare_images.py`:

```python
import json
from main import create_app
from vision_client import APIError


def test_compare_images_returns_json_on_api_error():
    """测试API错误返回JSON格式"""
    app = create_app()
    compare_images = app._tool_manager._tools['compare_images'].fn
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    
    with patch('vision_client.VisionClient.call_model') as mock_call:
        mock_call.return_value = APIError(
            status_code=429,
            error_message="Error code: 429 - rate limit exceeded",
            error_type="rate_limit",
            suggestion="请求频率超限，请稍后重试"
        )
        
        result = compare_images(str(test_image_path), str(test_image_path))
        
    assert isinstance(result, str)
    error_dict = json.loads(result)
    assert error_dict["status_code"] == 429
    assert error_dict["error_type"] == "rate_limit"


def test_compare_images_returns_json_on_local_error():
    """测试本地错误返回JSON格式"""
    app = create_app()
    compare_images = app._tool_manager._tools['compare_images'].fn
    
    result = compare_images("/nonexistent1.png", "/nonexistent2.png")
    
    assert isinstance(result, str)
    error_dict = json.loads(result)
    assert error_dict["status_code"] is None
    assert error_dict["error_type"] == "local_error"


def test_compare_images_returns_string_on_success():
    """测试成功时返回字符串"""
    app = create_app()
    compare_images = app._tool_manager._tools['compare_images'].fn
    
    test_image_path = Path(__file__).parent / "fixtures" / "test.png"
    
    with patch('vision_client.VisionClient.call_model') as mock_call:
        mock_call.return_value = "两张图片的对比分析结果"
        
        result = compare_images(str(test_image_path), str(test_image_path))
        
    assert isinstance(result, str)
    assert result == "两张图片的对比分析结果"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_compare_images.py::test_compare_images -v
```

Expected: Tests fail.

- [ ] **Step 3: 修改compare_images工具的错误处理**

Replace the compare_images function in `src/main.py` (lines 228-294):

```python
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
        
        messages = [
            {"role": "system", "content": COMPARE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_1};base64,{b64_1}",
                            "detail": detail,
                        },
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_2};base64,{b64_2}",
                            "detail": detail,
                        },
                    },
                    {"type": "text", "text": "请对比这两张图片"},
                ],
            },
        ]
        
        result = vision.call_model(messages)
        
        if isinstance(result, APIError):
            return json.dumps({
                "status_code": result.status_code,
                "error_message": result.error_message,
                "error_type": result.error_type,
                "suggestion": result.suggestion
            }, ensure_ascii=False, indent=2)
        
        return result
    except Exception as e:
        return json.dumps({
            "status_code": None,
            "error_message": str(e),
            "error_type": "local_error",
            "suggestion": "请检查输入参数是否正确"
        }, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_compare_images.py::test_compare_images -v
```

Expected: All tests pass.

- [ ] **Step 5: 提交修改**

```bash
git add src/main.py tests/test_compare_images.py
git commit -m "feat: enhance compare_images with JSON error handling"
```

---

### Task 6: 运行所有测试确保完整性

**Files:**
- No file modifications

- [ ] **Step 1: 运行完整测试套件**

```bash
pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: 手动测试错误返回格式**

Start the MCP server and test with invalid configuration to verify JSON error format:

```bash
vision-mcp
```

Then in another terminal, test with invalid inputs and verify JSON output format.

- [ ] **Step 3: 提交最终版本**

```bash
git add -A
git commit -m "feat: complete enhanced error handling implementation"
```

---

## Self-Review Checklist

**Spec Coverage:**
- ✓ APIError dataclass with 4 fields (status_code, error_message, error_type, suggestion)
- ✓ Error type classification (8 types: not_found, auth_error, rate_limit, network_error, invalid_request, server_error, local_error, unknown)
- ✓ HTTP status code to error type mapping
- ✓ JSON error format return
- ✓ All 3 tools enhanced (describe_image, ask_image, compare_images)
- ✓ Tests for all error scenarios

**Placeholder Scan:**
- ✓ No TBD/TODO/placeholder text
- ✓ All code blocks contain complete implementation
- ✓ All test code is complete
- ✓ All commands specified with expected output

**Type Consistency:**
- ✓ APIError dataclass matches usage across all files
- ✓ Import statements consistent (APIError imported from vision_client)
- ✓ Method signatures consistent (call_model returns str | APIError)
- ✓ JSON.dumps format consistent across all tools

---

## 执行方式选择

计划已完成并保存到 `docs/superpowers/plans/2026-05-08-enhance-error-handling.md`。

两种执行方式：

**1. Subagent-Driven (推荐)** - 每个Task派发一个新的子agent，Task之间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中使用executing-plans执行，批量执行带有审查检查点

选择哪种方式？