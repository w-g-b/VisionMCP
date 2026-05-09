from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent


class ImageRequestLogger:
    def __init__(self, enabled: bool = False, log_dir: str | None = None):
        self.enabled = enabled
        if log_dir is None:
            log_dir = PROJECT_ROOT / "log"
        self.log_dir = Path(log_dir)
    
    def log_request(
        self,
        tool_name: str,
        timestamp: str,
        image_urls: list[str],
        **params: Any
    ) -> None:
        if not self.enabled:
            return
        
        try:
            self.log_dir.mkdir(exist_ok=True)
            
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"{date_str}.log"
            
            lines = [
                f"[{timestamp}] Tool: {tool_name}",
                f"Parameters: {params}",
                f"Image URLs: {image_urls}",
                "-" * 80,
            ]
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception:
            pass