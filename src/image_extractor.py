import json
import re
from pathlib import Path
from typing import Optional


def is_image_reference(text: str) -> bool:
    """Check if text is an OpenCode image reference format.
    
    Matches:
    - "[Image 1]", "[Image 2]", etc.
    - "Image 1", "Image 2", etc.
    - Case-insensitive (matches "image", "IMAGE", etc.)
    
    Args:
        text: Input text to check
        
    Returns:
        True if text matches image reference pattern
    """
    pattern = r'^\[Image\s+\d+\]$|^Image\s+\d+$'
    return bool(re.match(pattern, text.strip(), re.IGNORECASE))


def parse_data_uri(data_uri: str) -> tuple[str, str]:
    """Parse data URI into mime type and base64 data.
    
    Args:
        data_uri: Data URI string (e.g., "data:image/png;base64,<data>")
        
    Returns:
        Tuple of (mime_type, base64_data)
        
    Raises:
        ValueError: If data URI format is invalid or not an image
    """
    if not isinstance(data_uri, str) or not data_uri:
        raise ValueError("Invalid data URI: must be a non-empty string")
    
    if not data_uri.startswith("data:"):
        raise ValueError("Invalid data URI: must start with 'data:'")
    
    parts = data_uri.split(",", 1)
    if len(parts) != 2:
        raise ValueError("Invalid data URI: missing comma separator")
    
    header = parts[0]
    b64_data = parts[1]
    
    if ";base64" not in header:
        raise ValueError("Invalid data URI: must contain ';base64' marker")
    
    if not b64_data:
        raise ValueError("Invalid data URI: base64 data is empty")
    
    if not header.startswith("data:image/"):
        raise ValueError(f"Invalid data URI: '{header}' is not an image type")
    
    mime_part = header.replace("data:", "").replace(";base64", "")
    
    return mime_part, b64_data


class ImageExtractor:
    """Extract image data from OpenCode prompt history."""
    
    HISTORY_FILE = Path("~/.local/state/opencode/prompt-history.jsonl").expanduser()