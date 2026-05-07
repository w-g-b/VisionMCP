# Vision MCP

A local MCP server for image understanding via vision models.

## Features

- **describe_image**: Automatically describe image content
- **ask_image**: Ask specific questions about an image

## Prerequisites

Requires Python 3.10+

## Installation

```bash
pip install -e .
```

## Configuration

Edit `config.yaml` in the project root directory:

```yaml
model:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key-here"
  model_name: "gpt-4o"
  max_tokens: 2048
  timeout: 60
```

## Usage

```bash
vision-mcp
```

Or for development:

```bash
python -m src.main
```

## MCP Client Configuration

### OpenCode

Add the following to your `opencode.json` (or `opencode.jsonc`) config file:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "vision-mcp": {
      "type": "local",
      "command": ["vision-mcp"],
      "enabled": true
    }
  }
}
```

Or if running from the project directory without installing globally:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "vision-mcp": {
      "type": "local",
      "command": ["python", "-m", "src.main"],
      "enabled": true
    }
  }
}
```

After configuring, you can ask OpenCode to analyze images:

```
describe this image.png using vision-mcp
```

```
what is in this screenshot.png? use vision-mcp
```

### Claude Desktop / Other Clients

To connect an MCP client (such as Claude Desktop), add the following to your client's MCP server configuration:

```json
{
  "mcpServers": {
    "vision-mcp": {
      "command": "vision-mcp"
    }
  }
}
```

## Supported Image Formats

PNG, JPG, JPEG, GIF, WebP
