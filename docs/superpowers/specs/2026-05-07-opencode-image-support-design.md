# Vision MCP: OpenCode图片粘贴支持设计

## 背景

当前Vision MCP服务支持通过文件路径或base64编码处理图片，但用户在OpenCode中粘贴图片时，图片以`[Image x]`占位符形式传递给MCP工具，导致无法直接处理。

实际图片数据存储在`~/.local/state/opencode/prompt-history.jsonl`文件中，以data URI格式保存（包含完整的base64编码数据）。

## 目标

增强Vision MCP服务，使其能够自动识别并提取OpenCode粘贴的图片，实现无缝的图片分析体验。

## 需求

1. **自动识别图片引用**：识别`[Image x]`格式的图片引用
2. **自动提取图片数据**：从OpenCode历史记录中提取对应的图片data URI
3. **向后兼容**：保持现有的文件路径和base64输入方式
4. **处理重名情况**：多个session可能存在相同编号的图片引用（如多个`[Image 1]`），需要提取最近的记录

## 设计方案

### 1. 新增图片提取模块

**文件：`src/image_extractor.py`**

**功能：从OpenCode历史记录提取图片数据**

**核心函数：**
```python
def extract_image_by_reference(image_ref: str) -> tuple[str, str]:
    """
    根据图片引用从OpenCode历史记录中提取最近的匹配图片
    
    Args:
        image_ref: 图片引用，如 "[Image 1]" 或 "Image 1"
    
    Returns:
        (mime_type, base64_data): 图片的MIME类型和base64编码数据
    
    Raises:
        FileNotFoundError: 历史文件不存在
        ValueError: 未找到匹配的图片或数据格式无效
    """
```

**算法逻辑：**
1. 打开`~/.local/state/opencode/prompt-history.jsonl`文件
2. 从最后一行开始逆向遍历（确保找到最近记录）
3. 解析每行JSON数据
4. 检查`input`字段是否包含目标图片引用（如`"[Image 1]"`）
5. 如果匹配，检查`parts`数组中是否存在`type="file"`且`mime`为图片类型的条目
6. 从`url`字段提取data URI（格式：`data:image/png;base64,<base64数据>`）
7. 解析data URI：分离MIME类型和base64数据
8. 返回MIME类型和base64数据

**处理重名情况：**
- 逆向遍历确保匹配到最近的记录
- 首次匹配即返回，避免误匹配旧记录

**支持的图片格式：**
- PNG（image/png）
- JPEG（image/jpeg）
- GIF（image/gif）
- WebP（image/webp）

### 2. 增强现有MCP工具

**修改文件：`src/main.py`**

**变化点：**

#### 2.1 describe_image工具增强

**参数变化：**
- `source_type`默认值从`"path"`改为`"auto"`
- 支持`"auto"`智能识别模式

**智能识别逻辑：**
```python
def describe_image(
    image_source: str,
    source_type: str = "auto",  # 新默认值
    detail: str = "auto",
    image_format: str = "png",
) -> str:
    """描述图片内容
    
    Args:
        image_source: 图片来源（文件路径、base64字符串、或[Image x]引用）
        source_type: 来源类型
            - "auto": 自动识别（推荐）
            - "path": 文件路径
            - "base64": base64编码字符串
        detail: 图片分析精度（"low", "high", "auto"）
        image_format: base64输入的图片格式（默认"png"）
    """
    try:
        if source_type == "auto":
            # 智能识别
            image_source_stripped = image_source.strip()
            
            # 检查是否为图片引用
            if is_image_reference(image_source_stripped):
                # 从OpenCode历史提取
                mime, b64 = extract_image_by_reference(image_source_stripped)
            else:
                # 检查是否为文件路径
                if Path(image_source).exists():
                    mime, b64 = ImageHelper.prepare_image(image_source)
                else:
                    # 作为base64处理
                    mime, b64 = ImageHelper.prepare_image_from_base64(
                        image_source, image_format
                    )
        else:
            # 原有逻辑：显式指定source_type
            if source_type == "path":
                mime, b64 = ImageHelper.prepare_image(Path(image_source))
            else:
                mime, b64 = ImageHelper.prepare_image_from_base64(
                    image_source, image_format
                )
        
        # 构建消息并调用视觉模型
        messages = _build_messages(DESCRIBE_SYSTEM_PROMPT, "请描述这张图片", ...)
        return vision.call_model(messages)
        
    except Exception as e:
        return f"Error: {e}"
```

**辅助函数：**
```python
def is_image_reference(text: str) -> bool:
    """检查文本是否为图片引用格式
    
    匹配模式：
    - "[Image 1]"
    - "Image 1"
    - "[Image 2]"
    - "Image 2"
    等
    """
    import re
    pattern = r'^\[Image\s+\d+\]$|^Image\s+\d+$'
    return bool(re.match(pattern, text))
```

#### 2.2 ask_image工具增强

**同样的智能识别逻辑：**
- `source_type`默认值改为`"auto"`
- 支持图片引用自动识别
- 保持向后兼容

### 3. 错误处理

**错误场景及处理：**

#### 3.1 历史文件不存在
```python
history_file = Path("~/.local/state/opencode/prompt-history.jsonl").expanduser()
if not history_file.exists():
    raise FileNotFoundError("OpenCode历史文件不存在，请确认已粘贴图片")
```

#### 3.2 未找到匹配的图片
```python
# 逆向遍历完成后未找到匹配
raise ValueError(f"未找到图片引用'{image_ref}'对应的图片数据")
```

#### 3.3 data URI解析失败
```python
if not url.startswith("data:image/"):
    raise ValueError("图片数据格式无效，无法解析")
```

#### 3.4 文件读取错误
```python
try:
    with open(history_file, 'r') as f:
        ...
except IOError as e:
    raise IOError(f"无法读取历史文件：{e}")
```

**用户友好的错误消息：**
- 错误信息通过工具返回值传递给用户
- 格式：`"Error: <具体错误原因>"`
- 包含可操作的提示（如"请确认已粘贴图片"）

### 4. 文件结构

**变化：**
```
vision_mcp/
├── src/
│   ├── main.py              # 修改：增强describe_image和ask_image
│   ├── image_extractor.py   # 新增：图片提取逻辑
│   ├── image_helper.py      # 现有：保持不变
│   ├── vision_client.py     # 现有：保持不变
│   └── config.py            # 现有：保持不变
│   └── __init__.py          # 现有：保持不变
├── docs/
│   └ superpowers/
│   └── specs/
│       └── 2026-05-07-opencode-image-support-design.md  # 本文档
├── config.yaml              # 现有：保持不变
├── pyproject.toml           # 现有：保持不变
└── README.md                # 现有：保持不变
```

**新增依赖：**
- 无需新增外部依赖
- 使用Python标准库：
  - `json`：解析JSON数据
  - `re`：正则表达式匹配
  - `pathlib.Path`：文件路径处理

### 5. 测试用例

**测试场景：**

1. **基本功能：图片引用识别**
   - 输入：`"[Image 1]"`
   - 预期：自动从历史提取并分析图片

2. **重名情况处理**
   - 多个session存在相同的`[Image 1]`
   - 预期：提取最近一次的图片

3. **向后兼容：文件路径**
   - 输入：`"/path/to/image.png"`，`source_type="auto"`
   - 预期：按文件路径处理

4. **向后兼容：base64**
   - 输入：base64字符串，`source_type="base64"`
   - 预期：按原有逻辑处理

5. **错误处理：未找到图片**
   - 输入：`"[Image 999]"`（不存在）
   - 预期：返回错误消息

6. **错误处理：历史文件不存在**
   - 前置：删除历史文件
   - 预期：返回错误消息

## 实现计划

待调用`writing-plans` skill生成详细实现步骤。

## 验收标准

1. 用户在OpenCode粘贴图片后，可直接调用`describe_image`或`ask_image`分析图片
2. 支持图片引用格式：`"[Image x]"`和`"Image x"`
3. 自动提取最近的图片数据（处理重名情况）
4. 保持向后兼容（文件路径和base64输入）
5. 提供清晰的用户错误提示
6. 无需新增外部依赖
7. 通过所有测试用例

## 风险和限制

**风险：**
- OpenCode历史文件位置可能变化（当前为`~/.local/state/opencode/prompt-history.jsonl`）
- OpenCode历史文件格式可能变化

**限制：**
- 只能分析最近的历史图片，无法分析已删除的历史
- 历史文件过大时，逆向遍历可能影响性能（可考虑限制回溯行数）

**缓解措施：**
- 提供清晰的错误提示，告知用户可能的解决方案
- 未来可考虑添加配置项，支持自定义历史文件路径

## 使用示例

**用户操作流程：**

1. 在OpenCode对话中粘贴图片（Ctrl+V）
2. 图片显示为占位符：`[Image 1] 这张图片有什么内容`
3. 用户调用MCP工具：
   ```
   请用vision-mcp描述[Image 1]
   ```
4. MCP工具自动识别并提取图片数据
5. 返回图片分析结果

**开发者API调用：**

```python
# 自动识别（推荐）
describe_image("[Image 1]")  # 自动从历史提取

# 显式指定（向后兼容）
describe_image("/path/to/image.png", source_type="path")
describe_image("base64string...", source_type="base64")
```

## 附录

**OpenCode prompt-history.jsonl格式示例：**
```json
{
  "input": "[Image 1] 这张图片有什么内容",
  "parts": [
    {
      "type": "file",
      "mime": "image/png",
      "filename": "clipboard",
      "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
    }
  ],
  "mode": "normal"
}
```

**data URI格式：**
```
data:image/png;base64,<base64编码数据>
data:image/jpeg;base64,<base64编码数据>
data:image/gif;base64,<base64编码数据>
data:image/webp;base64,<base64编码数据>
```