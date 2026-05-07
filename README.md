# Image MCP

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
image-mcp
```

Or for development:

```bash
python -m src.main
```

## MCP Client Configuration

To connect an MCP client (such as Claude Desktop), add the following to your client's MCP server configuration:

```json
{
  "mcpServers": {
    "image-mcp": {
      "command": "image-mcp"
    }
  }
}
```

## Supported Image Formats

PNG, JPG, JPEG, GIF, WebP
