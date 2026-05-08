# 图片对比工具设计文档

**日期**: 2026-05-08
**作者**: opencode
**状态**: 已批准

## 概述

为 Vision MCP 添加图片对比功能，支持对两张图片进行全面的多维度对比分析，包括排版布局、颜色、文字、风格样式等维度。

## 背景

用户需要对比两张图片的差异，现有工具 `describe_image` 和 `ask_image` 只能处理单张图片，无法满足对比需求。

## 设计方案

### 方案选择

采用**单工具设计**（方案1），添加一个 `compare_images` 工具专门用于对比两张图片。

**理由**：
- 简单直接，易于理解和使用
- 参数设计清晰，与现有工具风格一致
- 实现和维护成本低
- 符合用户实际需求（对比两张图片）

### 工具定义

#### 工具名称
`compare_images`

#### 参数设计

```python
@mcp.tool()
def compare_images(
    image_source_1: str,          # 第一张图片
    image_source_2: str,          # 第二张图片
    source_type_1: str = "auto",  # 第一张图片source_type
    source_type_2: str = "auto",  # 第二张图片source_type
    detail: str = "auto",         # 图片分析详细度
    image_format_1: str = "png",  # 第一张图片格式
    image_format_2: str = "png",  # 第二张图片格式
) -> str:
```

**参数说明**：
- `image_source_1` 和 `image_source_2`: 图片源，支持：
  - OpenCode图片引用（如 `[Image 1]`）
  - 本地文件路径
  - Base64编码字符串
- `source_type_1` 和 `source_type_2`: 图片源类型检测模式：
  - `"auto"`: 自动检测（推荐）
  - `"path"`: 作为文件路径处理
  - `"base64"`: 作为base64字符串处理
- `detail`: 图片分析详细度（`"low"`、`"high"`、`"auto"`）
- `image_format_1` 和 `image_format_2`: base64图片格式（默认 `"png"`）

#### 返回值

返回结构化文本对比分析，包含：
- 总体对比摘要
- 详细对比分析（排版、颜色、文字、风格、内容、细节）
- 总结关键差异点

错误时返回 `"Error: [错误信息]"` 格式消息。

### 系统提示语设计

使用详细的中文提示语引导模型进行全面对比：

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

### 消息格式

构建包含两张图片的消息：

```python
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
```

### 错误处理

遵循现有工具的错误处理模式：

```python
try:
    # 图片加载和对比逻辑
    ...
except Exception as e:
    return f"Error: {e}"
```

**错误场景**：
- 图片1加载失败：`"Error: 图片1加载失败 - FileNotFoundError..."`
- 图片2加载失败：`"Error: 图片2加载失败 - ValueError..."`
- API调用失败：`"Error: API调用失败 - Timeout..."`
- 空响应：`"Error: 模型返回空响应"`

### 实现位置

**文件位置**: `src/main.py`

**添加位置**: `create_app()` 函数内，添加新的 `@mcp.tool()` 定义

**常量定义**: 在文件顶部添加 `COMPARE_SYSTEM_PROMPT`

**代码复用**:
- 图片加载：复用 `ImageHelper.prepare_image()` 和 `extract_image_by_reference()`
- API调用：复用 `VisionClient.call_model()`
- 参数处理：复用现有source_type判断逻辑

### 测试设计

**测试文件**: `tests/test_compare_images.py`

**测试场景**:
1. **成功对比**: 两张有效图片的成功对比
2. **图片1失败**: 第一张图片路径不存在或格式错误
3. **图片2失败**: 第二张图片加载失败
4. **两张图片都失败**: 验证错误信息的准确性
5. **不同source_type组合**: auto、path、base64的各种组合
6. **OpenCode引用**: 测试 `[Image 1]` 和 `[Image 2]` 的引用处理
7. **API失败场景**: 模拟API调用失败

**测试策略**:
- 使用 `tests/fixtures/` 中的示例图片
- Mock `VisionClient` 进行集成测试
- 验证返回文本的结构和内容

### 文档更新

**README.md 更新**:
- Features部分添加 `compare_images` 工具说明
- Examples部分添加图片对比示例
- 项目结构保持不变（只修改main.py）

## 实现要点

### 图片加载逻辑

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

### 工具实现流程

1. 加载图片1（处理错误）
2. 加载图片2（处理错误）
3. 构建包含两张图片的消息
4. 调用Vision API
5. 返回对比分析结果

### 性能考虑

- 两张图片可能增加token消耗
- 建议 `detail` 参数默认使用 `"auto"` 或 `"low"` 以节省成本
- 用户可根据需要调整 `detail` 为 `"high"` 获取更详细对比

## 风险和限制

1. **Token限制**: 两张图片可能接近API token限制，需要注意图片大小
2. **API支持**: 需要确认Vision API支持多图片输入（OpenAI GPT-4V已支持）
3. **响应质量**: 对比分析的准确性和全面性依赖模型能力

## 成功标准

1. 工具能成功对比两张图片
2. 返回结构化、全面的对比分析
3. 错误处理清晰、准确
4. 测试覆盖率 >80%
5. 与现有工具风格一致
6. README.md文档更新完整

## 下一步

使用 `writing-plans` skill 创建详细实现计划。