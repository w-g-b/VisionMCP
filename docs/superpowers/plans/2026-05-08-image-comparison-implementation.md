# 图片对比工具实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Vision MCP 添加 compare_images 工具，支持两张图片的多维度对比分析

**Architecture:** 在 src/main.py 添加新的 MCP 工具，复用现有的图片加载和Vision API调用逻辑，采用TDD方式开发并添加完整测试

**Tech Stack:** FastMCP, pytest, unittest.mock, OpenAI Vision API

---

## File Structure

**创建文件：**
- `tests/test_compare_images.py` - 图片对比工具测试

**修改文件：**
- `src/main.py` - 添加 COMPARE_SYSTEM_PROMPT 常量、_load_image 辅助函数和 compare_images 工具
- `README.md` - 更新 Features 和 Examples 部分

**不修改：**
- `src/image_helper.py` - 已有完整的图片加载逻辑
- `src/vision_client.py` - 已有完整的API调用逻辑
- `src/image_extractor.py` - 已有完整的OpenCode引用提取逻辑
- 其他测试文件 - 保持不变

---

## Task 1: 创建测试文件基础结构

**Files:**
- Create: `tests/test_compare_images.py`

- [ ] **Step 1: 创建测试文件并添加基础导入和常量**

```python
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastmcp import FastMCP

from src.main import create_app
from src.config import Config, ModelConfig

VALID_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4DwAAAQEBABjdcbQAAAAASUVORK5CYII="
```

写入文件：`tests/test_compare_images.py`

- [ ] **Step 2: 验证测试文件创建成功**

Run: `pytest tests/test_compare_images.py -v`
Expected: PASS (no tests yet, just imports)

- [ ] **Step 3: Commit 测试文件基础结构**

```bash
git add tests/test_compare_images.py
git commit -m "test: create test file for compare_images tool"
```

---

## Task 2: 实现图片加载辅助函数测试

**Files:**
- Modify: `tests/test_compare_images.py:1-12` (追加测试)
- Create: `src/main.py:_load_image` (新增函数)

- [ ] **Step 1: 编写 _load_image 辅助函数的测试**

在 `tests/test_compare_images.py` 文件末尾追加：

```python
def test_load_image_with_path():
    from src.main import _load_image
    from pathlib import Path
    
    test_file = Path(__file__).parent.parent / "src" / "__init__.py"
    result = _load_image(str(test_file), "path", "png")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == "image/png"


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
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_compare_images.py::test_load_image_with_path -v`
Expected: FAIL with "cannot import name '_load_image' from 'src.main'"

- [ ] **Step 3: 在 src/main.py 实现 _load_image 辅助函数**

在 `src/main.py` 文件中，在 `DESCRIBE_SYSTEM_PROMPT` 常量定义之前添加：

```python
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
```

位置：在 `from image_extractor import is_image_reference, extract_image_by_reference` 导入语句之后，在 `DESCRIBE_SYSTEM_PROMPT = "..."` 常量定义之前。

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_compare_images.py::test_load_image_with_path tests/test_compare_images.py::test_load_image_with_base64 tests/test_compare_images.py::test_load_image_invalid_path -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit _load_image 辅助函数**

```bash
git add src/main.py tests/test_compare_images.py
git commit -m "feat: add _load_image helper function with tests"
```

---

## Task 3: 添加对比系统提示语

**Files:**
- Modify: `src/main.py:10-11` (添加 COMPARE_SYSTEM_PROMPT)

- [ ] **Step 1: 在 src/main.py 添加 COMPARE_SYSTEM_PROMPT 常量**

在 `src/main.py` 文件中，在 `ASK_SYSTEM_PROMPT` 常量定义之后添加：

```python
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
```

- [ ] **Step 2: 验证代码无语法错误**

Run: `.venv/bin/python -c "from src.main import COMPARE_SYSTEM_PROMPT; print('SUCCESS')"`
Expected: SUCCESS

- [ ] **Step 3: Commit 系统提示语**

```bash
git add src/main.py
git commit -m "feat: add COMPARE_SYSTEM_PROMPT for image comparison"
```

---

## Task 4: 实现 compare_images 工具

**Files:**
- Modify: `src/main.py:create_app()` (添加 compare_images 工具)
- Modify: `tests/test_compare_images.py` (添加成功对比测试)

- [ ] **Step 1: 编写 compare_images 工具的成功对比测试**

在 `tests/test_compare_images.py` 文件末尾追加：

```python
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
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.vision_client.VisionClient.call_model", return_value=mock_response):
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
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_compare_images.py::test_compare_images_success -v`
Expected: FAIL with "Tool 'compare_images' not found" or similar

- [ ] **Step 3: 在 src/main.py 实现 compare_images 工具**

在 `src/main.py` 文件的 `create_app()` 函数中，在 `ask_image` 工具定义之后（在 `return mcp` 之前）添加：

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
            Structured comparison analysis or error message starting with "Error: "
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
            return vision.call_model(messages)
        except Exception as e:
            return f"Error: {e}"
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_compare_images.py::test_compare_images_success -v`
Expected: PASS

- [ ] **Step 5: Commit compare_images 工具实现**

```bash
git add src/main.py tests/test_compare_images.py
git commit -m "feat: implement compare_images tool with success test"
```

---

## Task 5: 测试错误处理场景

**Files:**
- Modify: `tests/test_compare_images.py` (追加错误处理测试)

- [ ] **Step 1: 编写图片1加载失败的测试**

在 `tests/test_compare_images.py` 文件末尾追加：

```python
def test_compare_images_error_image1_not_found():
    config = Config(model=ModelConfig(api_key="sk-test"))
    with patch("src.main.load_config", return_value=config):
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
```

- [ ] **Step 2: 编写图片2加载失败的测试**

在 `tests/test_compare_images.py` 文件末尾追加：

```python
def test_compare_images_error_image2_not_found():
    config = Config(model=ModelConfig(api_key="sk-test"))
    with patch("src.main.load_config", return_value=config):
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
```

- [ ] **Step 3: 编写API调用失败的测试**

在 `tests/test_compare_images.py` 文件末尾追加：

```python
def test_compare_images_error_api_failure():
    config = Config(model=ModelConfig(api_key="sk-test"))
    with patch("src.main.load_config", return_value=config):
        with patch("src.vision_client.VisionClient.call_model", side_effect=Exception("API connection failed")):
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
```

- [ ] **Step 4: 运行所有错误处理测试验证通过**

Run: `pytest tests/test_compare_images.py::test_compare_images_error_image1_not_found tests/test_compare_images.py::test_compare_images_error_image2_not_found tests/test_compare_images.py::test_compare_images_error_api_failure -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit 错误处理测试**

```bash
git add tests/test_compare_images.py
git commit -m "test: add error handling tests for compare_images tool"
```

---

## Task 6: 测试不同参数组合场景

**Files:**
- Modify: `tests/test_compare_images.py` (追加参数组合测试)

- [ ] **Step 1: 编写auto检测模式的测试**

在 `tests/test_compare_images.py` 文件末尾追加：

```python
def test_compare_images_auto_detection():
    config = Config(model=ModelConfig(api_key="sk-test"))
    mock_response = "对比分析结果"
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.vision_client.VisionClient.call_model", return_value=mock_response):
            mcp = create_app()
            
            # Test auto mode with base64 strings
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
```

- [ ] **Step 2: 编写不同detail级别的测试**

在 `tests/test_compare_images.py` 文件末尾追加：

```python
def test_compare_images_different_detail_levels():
    config = Config(model=ModelConfig(api_key="sk-test"))
    mock_response = "对比分析结果"
    
    with patch("src.main.load_config", return_value=config):
        with patch("src.vision_client.VisionClient.call_model", return_value=mock_response):
            mcp = create_app()
            
            # Test with low detail
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
            
            # Test with high detail
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
```

- [ ] **Step 3: 运行参数组合测试验证通过**

Run: `pytest tests/test_compare_images.py::test_compare_images_auto_detection tests/test_compare_images.py::test_compare_images_different_detail_levels -v`
Expected: PASS (2 tests)

- [ ] **Step 4: 运行所有测试验证完整性**

Run: `pytest tests/test_compare_images.py -v`
Expected: PASS (all 10 tests)

- [ ] **Step 5: Commit 参数组合测试**

```bash
git add tests/test_compare_images.py
git commit -m "test: add parameter combination tests for compare_images"
```

---

## Task 7: 更新 README 文档

**Files:**
- Modify: `README.md:5-9` (Features部分)
- Modify: `README.md:125-149` (Examples部分)

- [ ] **Step 1: 更新 Features 部分**

在 `README.md` 的 Features 部分，修改为：

```markdown
## Features

- **describe_image**: Automatically describe image content with detailed analysis
- **ask_image**: Ask specific questions about an image
- **compare_images**: Compare two images and analyze differences across layout, color, text, style, content, and details
```

位置：第5-9行，替换原有的Features列表。

- [ ] **Step 2: 在 Examples 部分添加对比图片示例**

在 `README.md` 的 Examples 部分，在 "### Explicit Mode (Optional)" 之前添加新的子章节：

```markdown
### Image Comparison

Vision MCP can compare two images and provide detailed multi-dimensional analysis:

**Auto-Detection:**
```
compare [Image 1] and [Image 2] using vision-mcp
what's the difference between screenshot.png and screenshot_v2.png? use vision-mcp
analyze the differences in design.png and mockup.png with vision-mcp
```

**Structured Analysis:**
The comparison tool analyzes across 6 dimensions:
- **Layout**: Element positioning, hierarchy, spatial usage
- **Color**: Main colors, contrast, color palette differences
- **Text**: Content, fonts, typography
- **Style**: Overall aesthetic, design elements, visual effects
- **Content**: Subject matter, semantics, message delivery
- **Details**: Key variations, subtle differences

**Base64 Images:**
```
compare these two images using vision-mcp
```
(Provide two base64 image strings)
```

位置：在第125行之前插入，在 "### Auto-Detection (Recommended)" 之后。

- [ ] **Step 3: 验证 README 格式正确**

Run: `cat README.md | head -30`
Expected: Features部分包含compare_images描述

- [ ] **Step 4: Commit README 更新**

```bash
git add README.md
git commit -m "docs: add compare_images tool to README"
```

---

## Task 8: 最终验证和集成测试

**Files:**
- 全项目测试

- [ ] **Step 1: 运行所有项目测试**

Run: `pytest tests/ -v`
Expected: PASS (all tests including new compare_images tests)

- [ ] **Step 2: 测试 compare_images 工具可用性**

Run: `.venv/bin/python -c "from src.main import create_app; from src.config import Config, ModelConfig; import asyncio; from unittest.mock import patch; config = Config(model=ModelConfig(api_key='test')); mcp = create_app(); print('SUCCESS')"`
Expected: SUCCESS

- [ ] **Step 3: 验证 vision-mcp 启动无错误**

Run: `.venv/bin/vision-mcp --help`
Expected: FastMCP启动界面，无错误

- [ ] **Step 4: 最终commit**

```bash
git add -A
git commit -m "feat: complete compare_images tool implementation with tests and docs"
```

---

## Success Criteria Verification

完成后验证以下标准：
- [ ] compare_images工具可正常调用
- [ ] 返回结构化的对比分析文本
- [ ] 错误处理返回 "Error: " 前缀消息
- [ ] 测试覆盖率 >80%（运行 pytest --cov 查看）
- [ ] README文档包含compare_images说明和示例
- [ ] 与现有工具风格一致（参数命名、错误处理模式）