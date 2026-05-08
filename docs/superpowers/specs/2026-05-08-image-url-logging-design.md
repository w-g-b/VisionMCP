# Image URL Logging Design

**Date:** 2026-05-08  
**Status:** Draft  
**Author:** AI Assistant  

## Overview

Add logging functionality to record all image_url content from vision tool requests to the `log/` directory. The logging is controlled via configuration and disabled by default.

## Requirements

### Functional Requirements

1. **Log Image URLs**: Record complete image_url content (including base64 data) for all three vision tools
2. **Configuration Control**: Enable/disable logging via `config.logging` setting
3. **Date-Based Files**: Create one log file per day with format `YYYY-MM-DD.log`
4. **Complete Request Info**: Log timestamp, tool name, all parameters, and image URLs
5. **Non-Blocking**: Logging failures should not affect tool execution

### Non-Functional Requirements

1. **Default Off**: Logging disabled by default (config.logging defaults to false)
2. **Automatic Directory Creation**: Create `log/` directory if it doesn't exist
3. **No Auto-Cleanup**: Manual log management (no automatic deletion)

## Design

### Architecture

Add a dedicated logging module that integrates with the existing tool functions:

```
src/
├── logger.py           # NEW: ImageRequestLogger class
├── config.py          # UPDATED: Add logging field
├── main.py            # UPDATED: Integrate logger calls
└── ...
```

### Components

#### 1. Configuration (config.py, config.yaml)

**config.yaml:**
```yaml
model:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key-here"
  model_name: "gpt-4o"
  max_tokens: 2048
  timeout: 60

config:
  logging: false  # Optional, defaults to false
```

**config.py:**
```python
from dataclasses import dataclass

@dataclass
class ModelConfig:
    base_url: str
    api_key: str
    model_name: str
    max_tokens: int
    timeout: int

@dataclass
class Config:
    model: ModelConfig
    logging: bool = False  # Default to False

def load_config() -> Config:
    # Load from config.yaml
    # If config.logging not specified, default to False
```

#### 2. Logger Module (logger.py)

```python
from datetime import datetime
from pathlib import Path
from typing import Any

class ImageRequestLogger:
    def __init__(self, enabled: bool = False, log_dir: str = "log"):
        self.enabled = enabled
        self.log_dir = Path(log_dir)
    
    def log_request(
        self,
        tool_name: str,
        timestamp: str,
        image_urls: list[str],
        **params: Any
    ) -> None:
        """Log request to daily log file"""
        if not self.enabled:
            return
        
        try:
            # Create log directory if needed
            self.log_dir.mkdir(exist_ok=True)
            
            # Generate filename by date
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"{date_str}.log"
            
            # Format log content
            lines = [
                f"[{timestamp}] Tool: {tool_name}",
                f"Parameters: {params}",
                f"Image URLs: {image_urls}",
                "-" * 80,
            ]
            
            # Append to log file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception:
            # Silently ignore logging errors
            pass
```

#### 3. Tool Integration (main.py)

**Initialization:**
```python
def create_app() -> FastMCP:
    config = load_config()
    vision = VisionClient(config.model)
    logger = ImageRequestLogger(enabled=config.logging)  # NEW
    mcp = FastMCP("vision-mcp")
    
    # ... tool definitions
```

**describe_image:**
```python
@mcp.tool()
def describe_image(...) -> str:
    try:
        # ... existing code to get mime and b64
        image_url = f"data:{mime};base64,{b64}"
        
        # NEW: Log request
        logger.log_request(
            tool_name="describe_image",
            timestamp=datetime.now().isoformat(),
            image_urls=[image_url],
            source_type=source_type,
            detail=detail,
            image_format=image_format
        )
        
        # ... rest of existing code
```

**ask_image:**
```python
@mcp.tool()
def ask_image(...) -> str:
    try:
        # ... existing code to get mime and b64
        image_url = f"data:{mime};base64,{b64}"
        
        # NEW: Log request
        logger.log_request(
            tool_name="ask_image",
            timestamp=datetime.now().isoformat(),
            image_urls=[image_url],
            question=question,
            source_type=source_type,
            detail=detail,
            image_format=image_format
        )
        
        # ... rest of existing code
```

**compare_images:**
```python
@mcp.tool()
def compare_images(...) -> str:
    try:
        # ... existing code to get mime_1, b64_1, mime_2, b64_2
        image_url_1 = f"data:{mime_1};base64,{b64_1}"
        image_url_2 = f"data:{mime_2};base64,{b64_2}"
        
        # NEW: Log request
        logger.log_request(
            tool_name="compare_images",
            timestamp=datetime.now().isoformat(),
            image_urls=[image_url_1, image_url_2],
            source_type_1=source_type_1,
            source_type_2=source_type_2,
            detail=detail,
            image_format_1=image_format_1,
            image_format_2=image_format_2
        )
        
        # ... rest of existing code
```

### Data Flow

1. User calls vision tool with image source
2. Tool extracts/loads image data and builds image_url
3. Logger records timestamp, tool name, parameters, and image_url(s)
4. Log written to daily file (e.g., `log/2026-05-08.log`)
5. Tool continues with vision API call

### Error Handling

- **Logging failures**: Caught and silently ignored in `log_request()`
- **Missing log directory**: Auto-created with `mkdir(exist_ok=True)`
- **Missing config.logging**: Defaults to False in Config dataclass

## Implementation Plan

### Files to Modify

1. **config.yaml** - Add `config.logging: false`
2. **config.py** - Add `logging: bool` field to Config
3. **logger.py** - Create new file with ImageRequestLogger class
4. **main.py** - Initialize logger and add log calls to all three tools

### Implementation Order

1. Update config.py to add logging field
2. Update config.yaml with new config structure
3. Create logger.py with ImageRequestLogger class
4. Integrate logger into main.py tools
5. Update README.md with logging documentation

## Testing

### Unit Tests

1. **test_config.py** - Test Config dataclass with logging field
2. **test_logger.py** - Test ImageRequestLogger:
   - Test disabled logging (no file created)
   - Test enabled logging (file created)
   - Test daily file naming
   - Test log format
   - Test error handling

### Integration Tests

1. Test with logging disabled (default)
2. Test with logging enabled
3. Test log file content format
4. Test across date boundaries

## Migration

No migration needed - this is a new feature with backward-compatible defaults.

## Documentation Updates

Update README.md to document:

1. New logging feature in Features section
2. Configuration example with `config.logging`
3. Log file format and location
4. Note about base64 data size in logs

## Security Considerations

- Logs contain full base64 image data which can be large
- Logs may contain sensitive image content
- Users should be aware of disk space usage
- Consider adding note in README about log management

## Limitations

- No automatic log rotation or cleanup
- Large log files possible with many requests
- No log compression
- No remote logging support