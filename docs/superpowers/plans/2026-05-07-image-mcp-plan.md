# Image MCP 服务实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发一个本地 MCP 服务，支持通过 config.yaml 配置视觉模型，提供 describe_image 和 ask_image 两个工具供 Agent 调用。

**Architecture:** 基于 FastMCP 框架构建 MCP Server，使用 openai SDK 调用 OpenAI 兼容的视觉模型 API，通过 YAML 配置文件管理模型参数。

**Tech Stack:** Python, FastMCP, openai SDK, pydantic, pyyaml

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `pyproject.toml` | 项目元数据和依赖声明 |
| `config.yaml` | 模型配置模板 |
| `src/__init__.py` | 包初始化 |
| `src/config.py` | 加载并校验 config.yaml |
| `src/image_helper.py` | 图片读取、base64 编码、格式校验 |
| `src/vision_client.py` | 封装 openai SDK 调用逻辑 |
| `src/main.py` | FastMCP 入口，注册工具 |
| `tests/test_config.py` | 配置加载测试 |
| `tests/test_image_helper.py` | 图片处理测试 |
| `tests/test_vision_client.py` | 模型调用测试 |

---

### Task 1: 项目骨架和依赖

**Files:**
- Create: `pyproject.toml`
- Create: `src/__init__.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "image-mcp"
version = "0.1.0"
description = "A local MCP server for image understanding via vision models"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=2.0.0",
    "openai>=1.0.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0.0",
]

[project.scripts]
image-mcp = "src.main:main"
```

- [ ] **Step 2: 创建 src/__init__.py**

```python
```

- [ ] **Step 3: 安装依赖**

```bash
cd /usr1/wgb/image_mcp && pip install -e .
```

- [ ] **Step 4: Commit**

```bash
cd /usr1/wgb/image_mcp && git add -A && git commit -m "chore: add project skeleton and dependencies"
```

---

### Task 2: 配置加载模块

**Files:**
- Create: `src/config.py`
- Create: `tests/test_config.py`
- Create: `config.yaml`

- [ ] **Step 1: 创建 config.yaml 模板**

```yaml
model:
  base_url: "https://api.openai.com/v1"
  api_key: ""
  model_name: "gpt-4o"
  max_tokens: 2048
  timeout: 60
```

- [ ] **Step 2: 编写配置测试**

```python
# tests/test_config.py
import pytest
from pathlib import Path
from src.config import Config, load_config

def test_load_valid_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
model:
  base_url: "https://api.example.com/v1"
  api_key: "sk-test-key"
  model_name: "gpt-4o"
  max_tokens: 1024
  timeout: 30
""")
    config = load_config(config_file)
    assert config.model.base_url == "https://api.example.com/v1"
    assert config.model.api_key == "sk-test-key"
    assert config.model.model_name == "gpt-4o"
    assert config.model.max_tokens == 1024
    assert config.model.timeout == 30

def test_missing_api_key_raises(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
model:
  base_url: "https://api.example.com/v1"
  api_key: ""
  model_name: "gpt-4o"
""")
    with pytest.raises(ValueError, match="api_key"):
        load_config(config_file)

def test_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/config.yaml"))
```

- [ ] **Step 3: 运行测试确认失败**

```bash
cd /usr1/wgb/image_mcp && python -m pytest tests/test_config.py -v
```
Expected: FAIL (模块不存在)

- [ ] **Step 4: 实现配置加载**

```python
# src/config.py
from pathlib import Path
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = Field(..., min_length=1)
    model_name: str = "gpt-4o"
    max_tokens: int = 2048
    timeout: int = 60


class Config(BaseModel):
    model: ModelConfig


def load_config(config_path: Path | None = None) -> Config:
    import yaml

    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    config = Config(**data)

    if not config.model.api_key:
        raise ValueError("model.api_key is required but empty")

    return config
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd /usr1/wgb/image_mcp && python -m pytest tests/test_config.py -v
```
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
cd /usr1/wgb/image_mcp && git add -A && git commit -m "feat: add config loading and validation"
```

---

### Task 3: 图片处理模块

**Files:**
- Create: `src/image_helper.py`
- Create: `tests/test_image_helper.py`

- [ ] **Step 1: 编写图片处理测试**

```python
# tests/test_image_helper.py
import pytest
import base64
from pathlib import Path
from src.image_helper import ImageHelper

SUPPORTED_FORMATS = ["png", "jpg", "jpeg", "gif", "webp"]

def test_read_image_from_path(tmp_path):
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"fake-image-data")
    result = ImageHelper.read_image(img_path)
    assert isinstance(result, bytes)
    assert result == b"fake-image-data"

def test_read_image_not_found():
    with pytest.raises(FileNotFoundError, match="not found"):
        ImageHelper.read_image(Path("/nonexistent/image.png"))

def test_encode_to_base64(tmp_path):
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"test-bytes")
    encoded = ImageHelper.encode_to_base64(img_path)
    decoded = base64.b64decode(encoded)
    assert decoded == b"test-bytes"

def test_encode_base64_string():
    raw = b"test-image"
    encoded = ImageHelper.encode_base64_string(raw)
    assert isinstance(encoded, str)
    decoded = base64.b64decode(encoded)
    assert decoded == raw

def test_detect_mime_type(tmp_path):
    for ext, expected in [
        ("png", "image/png"),
        ("jpg", "image/jpeg"),
        ("jpeg", "image/jpeg"),
        ("gif", "image/gif"),
        ("webp", "image/webp"),
    ]:
        p = tmp_path / f"test.{ext}"
        p.write_bytes(b"x")
        assert ImageHelper.detect_mime_type(p) == expected

def test_detect_mime_type_unsupported(tmp_path):
    p = tmp_path / "test.bmp"
    p.write_bytes(b"x")
    with pytest.raises(ValueError, match="Unsupported"):
        ImageHelper.detect_mime_type(p)

def test_prepare_image_from_path(tmp_path):
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"img")
    mime, b64 = ImageHelper.prepare_image(img_path)
    assert mime == "image/png"
    assert base64.b64decode(b64) == b"img"

def test_prepare_image_from_base64():
    b64_input = base64.b64encode(b"raw").decode()
    mime, b64 = ImageHelper.prepare_image_from_base64(b64_input, "png")
    assert mime == "image/png"
    assert b64 == b64_input
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /usr1/wgb/image_mcp && python -m pytest tests/test_image_helper.py -v
```
Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现图片处理**

```python
# src/image_helper.py
import base64
from pathlib import Path


MIME_MAP = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}


class ImageHelper:
    @staticmethod
    def read_image(path: Path) -> bytes:
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        return path.read_bytes()

    @staticmethod
    def encode_to_base64(path: Path) -> str:
        data = ImageHelper.read_image(path)
        return base64.b64encode(data).decode("utf-8")

    @staticmethod
    def encode_base64_string(raw_bytes: bytes) -> str:
        return base64.b64encode(raw_bytes).decode("utf-8")

    @staticmethod
    def detect_mime_type(path: Path) -> str:
        ext = path.suffix.lower().lstrip(".")
        if ext not in MIME_MAP:
            raise ValueError(f"Unsupported image format: .{ext}")
        return MIME_MAP[ext]

    @staticmethod
    def prepare_image(path: Path) -> tuple[str, str]:
        mime = ImageHelper.detect_mime_type(path)
        b64 = ImageHelper.encode_to_base64(path)
        return mime, b64

    @staticmethod
    def prepare_image_from_base64(b64_str: str, ext: str = "png") -> tuple[str, str]:
        ext = ext.lower().lstrip(".")
        if ext not in MIME_MAP:
            raise ValueError(f"Unsupported image format: .{ext}")
        return MIME_MAP[ext], b64_str
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /usr1/wgb/image_mcp && python -m pytest tests/test_image_helper.py -v
```
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd /usr1/wgb/image_mcp && git add -A && git commit -m "feat: add image helper for reading and encoding"
```

---

### Task 4: 视觉模型客户端

**Files:**
- Create: `src/vision_client.py`
- Create: `tests/test_vision_client.py`

- [ ] **Step 1: 编写模型客户端测试**

```python
# tests/test_vision_client.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.config import ModelConfig
from src.vision_client import VisionClient


@pytest.fixture
def model_config():
    return ModelConfig(
        base_url="https://api.example.com/v1",
        api_key="sk-test",
        model_name="gpt-4o",
        max_tokens=1024,
        timeout=30,
    )


def test_vision_client_init(model_config):
    client = VisionClient(model_config)
    assert client.config == model_config


@patch("src.vision_client.OpenAI")
def test_call_model(mock_openai, model_config):
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a cat."
    mock_instance.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_instance

    client = VisionClient(model_config)
    messages = [
        {"role": "system", "content": "Describe the image"},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,aW1hZ2U=",
                        "detail": "auto",
                    },
                },
                {"type": "text", "text": "What is in this image?"},
            ],
        },
    ]

    result = client.call_model(messages)
    assert result == "This is a cat."
    mock_instance.chat.completions.create.assert_called_once()
    call_kwargs = mock_instance.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4o"
    assert call_kwargs["max_tokens"] == 1024


@patch("src.vision_client.OpenAI")
def test_call_model_error(mock_openai, model_config):
    mock_instance = MagicMock()
    mock_instance.chat.completions.create.side_effect = Exception("API error")
    mock_openai.return_value = mock_instance

    client = VisionClient(model_config)
    with pytest.raises(Exception, match="API error"):
        client.call_model([])
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /usr1/wgb/image_mcp && python -m pytest tests/test_vision_client.py -v
```
Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现模型客户端**

```python
# src/vision_client.py
from openai import OpenAI
from src.config import ModelConfig


class VisionClient:
    def __init__(self, config: ModelConfig):
        self.config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )

    def call_model(self, messages: list[dict]) -> str:
        response = self._client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /usr1/wgb/image_mcp && python -m pytest tests/test_vision_client.py -v
```
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd /usr1/wgb/image_mcp && git add -A && git commit -m "feat: add vision client for model API calls"
```

---

### Task 5: MCP 主入口和工具注册

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: 实现 MCP 主入口**

```python
# src/main.py
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
```

- [ ] **Step 2: 验证模块可导入**

```bash
cd /usr1/wgb/image_mcp && python -c "from src.main import mcp; print('OK')"
```
Expected: OK

- [ ] **Step 3: Commit**

```bash
cd /usr1/wgb/image_mcp && git add -A && git commit -m "feat: add MCP server with describe_image and ask_image tools"
```

---

### Task 6: 完善配置模板和 README

**Files:**
- Modify: `config.yaml`
- Create: `README.md`

- [ ] **Step 1: 更新 config.yaml 为完整模板**

```yaml
model:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key-here"
  model_name: "gpt-4o"
  max_tokens: 2048
  timeout: 60
```

- [ ] **Step 2: 创建 README.md**

```markdown
# Image MCP

A local MCP server for image understanding via vision models.

## Features

- **describe_image**: Automatically describe image content
- **ask_image**: Ask specific questions about an image

## Configuration

Edit `config.yaml`:

```yaml
model:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key-here"
  model_name: "gpt-4o"
  max_tokens: 2048
  timeout: 60
```

## Installation

```bash
pip install -e .
```

## Usage

```bash
python -m src.main
```

## Supported Image Formats

PNG, JPG, JPEG, GIF, WebP
```

- [ ] **Step 3: Commit**

```bash
cd /usr1/wgb/image_mcp && git add -A && git commit -m "docs: add README and finalize config template"
```

---
