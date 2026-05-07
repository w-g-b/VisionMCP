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


class ImageExtractor:
    """Extract image data from OpenCode prompt history."""
    
    HISTORY_FILE = Path("~/.local/state/opencode/prompt-history.jsonl").expanduser()