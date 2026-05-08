# Vision MCP

A local MCP (Model Context Protocol) server for image understanding via vision models. Supports automatic detection of image sources from OpenCode pasted images, file paths, or base64 strings.

## Features

- **describe_image**: Automatically describe image content with detailed analysis
- **ask_image**: Ask specific questions about an image

### Auto-Detection Mode

Vision MCP automatically detects the image source type, eliminating the need for manual specification:

**Detection Priority:**
1. **OpenCode Image References** - Recognizes `[Image x]` format (e.g., `[Image 1]`, `[Image 2]`)
2. **File Paths** - Detects valid local file paths
3. **Base64 Strings** - Falls back to base64 encoded data

This makes the tool seamless to use - just paste an image in OpenCode and reference it naturally!

## Installation

### Prerequisites

- Python 3.10+
- Vision model API access (OpenAI GPT-4V, or compatible services)

### Setup

1. **Clone and install:**
```bash
cd /usr1/wgb/vision_mcp
pip install -e .
```

Or with virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows
pip install -e .
```

2. **Configure API:**

Edit `config.yaml` in the project root:

```yaml
model:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key-here"
  model_name: "gpt-4o"
  max_tokens: 2048
  timeout: 60
```

**Alternative providers:**
- Azure OpenAI: Set `base_url` to your Azure endpoint
- Local models: Use compatible API endpoints (e.g., Ollama with OpenAI-compatible API)
- Third-party: Any OpenAI-compatible vision model API

## Usage

### Basic Commands

Start the MCP server:
```bash
vision-mcp
```

The server will start and listen for MCP client connections via stdio.

### MCP Client Configuration

#### OpenCode

Add to your `opencode.json` config file (located at `~/.config/opencode/opencode.json`):

**Global installation:**
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

**From project directory (with virtual environment):**
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "vision-mcp": {
      "type": "local",
      "command": ["/usr1/wgb/vision_mcp/.venv/bin/vision-mcp"],
      "enabled": true
    }
  }
}
```

#### Claude Desktop / Other Clients

```json
{
  "mcpServers": {
    "vision-mcp": {
      "command": "vision-mcp"
    }
  }
}
```

## Examples

### Auto-Detection (Recommended)

Vision MCP automatically detects image sources - no manual specification needed:

**OpenCode Pasted Images:**
```
describe this [Image 1] using vision-mcp
what details can you see in [Image 2]? use vision-mcp
analyze the chart in [Image 3] with vision-mcp
```

**File Paths:**
```
describe screenshot.png using vision-mcp
what is in /path/to/photo.jpg? use vision-mcp
analyze this diagram.png with vision-mcp
```

**Base64 Strings:**
```
describe this base64image using vision-mcp
```

### Explicit Mode (Optional)

For precise control, specify the source type:

**Force file path mode:**
```json
{
  "image_source": "/path/to/image.png",
  "source_type": "path"
}
```

**Force base64 mode:**
```json
{
  "image_source": "iVBORw0KGgoAAAANSUhEUg...",
  "source_type": "base64",
  "image_format": "png"
}
```

## Supported Image Formats

- PNG
- JPEG / JPG
- GIF
- WebP

## Technical Details

### Image Reference Detection

The tool uses pattern matching to detect OpenCode image references:
- Format: `[Image x]` or `Image x` (case-insensitive)
- Examples: `[Image 1]`, `Image 2`, `[IMAGE 3]`, `image 4`

### Image Extraction Process

When an image reference is detected:
1. Reads OpenCode's prompt-history file (`~/.local/state/opencode/prompt-history.jsonl`)
2. Searches backwards (most recent first)
3. Extracts data URI from matching entry's `parts` array
4. Parses and validates the base64-encoded image data

### Error Handling

The tool provides clear error messages:
- **History file missing**: "OpenCode历史文件不存在，请确认已粘贴图片"
- **Reference not found**: "未找到图片引用'[Image x]'对应的图片数据"
- **Invalid data**: Specific validation errors for malformed data

## Limitations

- Only analyzes images from recent OpenCode history (reverse iteration)
- Requires valid vision model API credentials
- Large history files may impact performance (though typically negligible)
- Image references must match entries in prompt-history (can't analyze deleted/cleared history)

## Troubleshooting

**Image reference not found:**
- Ensure the image was pasted in current OpenCode session
- Check that the reference format matches (e.g., `[Image 1]`)
- Try re-pasting the image

**API errors:**
- Verify `config.yaml` has correct API credentials
- Check `base_url` matches your provider's endpoint
- Ensure the model supports vision (e.g., gpt-4o, gpt-4-vision-preview)

**File path errors:**
- Verify the path exists and is accessible
- Check file format is supported
- Ensure file is a valid image

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
vision_mcp/
├── src/
│   ├── __init__.py
│   ├── main.py              # MCP server and tool definitions
│   ├── image_extractor.py   # Image extraction from OpenCode history
│   ├── image_helper.py      # Image processing utilities
│   ├── vision_client.py     # Vision model API client
│   └── config.py            # Configuration management
├── tests/
│   ├── test_*.py            # Unit tests
│   └── fixtures/
├── config.yaml              # API configuration
├── config.yaml.example      # Example configuration
├── pyproject.toml           # Project metadata and dependencies
└── README.md
```

## License

MIT

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Acknowledgments

- Built with [FastMCP](https://github.com/lowlevelfunc/fastmcp)
- Powered by vision models via OpenAI-compatible APIs