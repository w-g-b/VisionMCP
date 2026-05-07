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


def extract_image_by_reference(image_ref: str) -> tuple[str, str]:
    """Extract image data from OpenCode history by reference.
    
    Args:
        image_ref: Image reference like "[Image 1]" or "Image 1"
        
    Returns:
        Tuple of (mime_type, base64_data)
        
    Raises:
        FileNotFoundError: History file doesn't exist
        ValueError: Reference not found or data invalid
    """
    # Normalize reference: ensure bracketed format
    ref_normalized = image_ref.strip()
    if not ref_normalized.startswith("["):
        ref_normalized = f"[{ref_normalized}]"
    
    # Case-insensitive matching (OpenCode may use different capitalization)
    ref_pattern = re.compile(re.escape(ref_normalized), re.IGNORECASE)
    
    # Check history file exists
    if not ImageExtractor.HISTORY_FILE.exists():
        raise FileNotFoundError("OpenCode历史文件不存在，请确认已粘贴图片")
    
    # Read and reverse lines (most recent first)
    try:
        with open(ImageExtractor.HISTORY_FILE, "r") as f:
            lines = f.readlines()
    except IOError as e:
        raise IOError(f"无法读取历史文件: {e}")
    
    # Iterate backwards to find most recent match
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        # Check if input contains our image reference (case-insensitive)
        input_text = entry.get("input", "")
        if not ref_pattern.search(input_text):
            continue
        
        # Found match! Check parts for image data
        parts = entry.get("parts", [])
        for part in parts:
            if part.get("type") != "file":
                continue
            
            mime = part.get("mime", "")
            if not mime.startswith("image/"):
                continue
            
            url = part.get("url", "")
            if not url:
                continue
            
            # Parse data URI
            return parse_data_uri(url)
    
    # No match found after full traversal
    raise ValueError(f"未找到图片引用'{image_ref}'对应的图片数据")