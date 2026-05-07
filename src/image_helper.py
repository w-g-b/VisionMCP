import base64
from pathlib import Path


MIME_MAP = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}


class ImageHelper:
    @staticmethod
    def read_image(path: Path) -> bytes:
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        return path.read_bytes()

    @staticmethod
    def encode_to_base64(path: Path) -> str:
        data = ImageHelper.read_image(path)
        return base64.b64encode(data).decode("utf-8")

    @staticmethod
    def encode_base64_string(raw_bytes: bytes) -> str:
        return base64.b64encode(raw_bytes).decode("utf-8")

    @staticmethod
    def detect_mime_type(path: Path) -> str:
        ext = path.suffix.lower().lstrip(".")
        if ext not in MIME_MAP:
            raise ValueError(f"Unsupported image format: .{ext}")
        return MIME_MAP[ext]

    @staticmethod
    def prepare_image(path: Path) -> tuple[str, str]:
        mime = ImageHelper.detect_mime_type(path)
        b64 = ImageHelper.encode_to_base64(path)
        return mime, b64

    @staticmethod
    def prepare_image_from_base64(b64_str: str, ext: str = "png") -> tuple[str, str]:
        ext = ext.lower().lstrip(".")
        if ext not in MIME_MAP:
            raise ValueError(f"Unsupported image format: .{ext}")
        return MIME_MAP[ext], b64_str
