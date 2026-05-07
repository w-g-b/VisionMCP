import json
import re
from pathlib import Path
from typing import Optional


class ImageExtractor:
    """Extract image data from OpenCode prompt history."""
    
    HISTORY_FILE = Path("~/.local/state/opencode/prompt-history.jsonl").expanduser()