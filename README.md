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
