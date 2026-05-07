# Image MCP 服务设计文档

**日期：** 2026-05-07
**状态：** 设计中

## 概述

开发一个本地 MCP 服务，使 Agent 能够调用视觉模型 API 来理解图片内容。服务支持配置模型 URL 和 API Key，提供图片描述和问答两个工具。

## 架构

```
Agent/Client → FastMCP Server (stdio) → VisionClient (openai SDK) → Vision Model API
```

**核心组件：**
1. **FastMCP Server** — 主入口，注册工具，管理配置
2. **VisionClient** — 封装模型调用逻辑
3. **Config** — 加载 config.yaml，校验必填项
4. **ImageHelper** — 处理文件读取、base64 编码、格式校验

## 工具设计

### describe_image
自动描述图片内容。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| image_source | string | 是 | - | 本地文件路径或 base64 字符串 |
| source_type | string | 否 | "path" | "path" 或 "base64" |
| detail | string | 否 | "auto" | "low", "high", "auto" |

**系统提示：** "请详细描述这张图片的内容"

### ask_image
针对图片回答特定问题。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| image_source | string | 是 | - | 本地文件路径或 base64 字符串 |
| source_type | string | 否 | "path" | "path" 或 "base64" |
| question | string | 是 | - | 用户问题 |
| detail | string | 否 | "auto" | "low", "high", "auto" |

## 配置设计

**配置文件：** `config.yaml`

```yaml
model:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-xxx"
  model_name: "gpt-4o"
  max_tokens: 2048
  timeout: 60
```

**必填项：** `api_key`，缺失时启动报错。

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 配置文件不存在 | 报错退出 |
| 缺少 api_key | 启动时立即报错退出 |
| 文件路径不存在 | 工具返回错误信息 |
| 图片格式不支持 | 工具返回错误信息 |
| 模型 API 调用失败 | 返回错误详情，不崩溃 |
| 网络超时 | 使用配置的 timeout，超时返回错误 |

## 项目结构

```
image_mcp/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── vision_client.py
│   └── image_helper.py
├── config.yaml
├── pyproject.toml
└── README.md
```

**依赖：** fastmcp, openai, pydantic, pyyaml

## 启动方式

```bash
python -m src.main
```
