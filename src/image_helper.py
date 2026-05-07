import base64
from pathlib import Path


MIME_MAP: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}


class ImageHelper:
    @staticmethod
    def read_image(path: Path | str) -> bytes:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        if path.stat().st_size == 0:
            raise ValueError("Image file is empty")
        return path.read_bytes()

    @staticmethod
    def encode_to_base64(path: Path | str) -> str:
        data = ImageHelper.read_image(path)
        return base64.b64encode(data).decode("utf-8")

    @staticmethod
    def encode_base64_string(raw_bytes: bytes) -> str:
        return base64.b64encode(raw_bytes).decode("utf-8")

    @staticmethod
    def mime_type_from_extension(path: Path | str) -> str:
        ext = Path(path).suffix.lower().lstrip(".")
        if ext not in MIME_MAP:
            raise ValueError(f"Unsupported image format: .{ext}")
        return MIME_MAP[ext]

    @staticmethod
    def prepare_image(path: Path | str) -> tuple[str, str]:
        mime = ImageHelper.mime_type_from_extension(path)
        b64 = ImageHelper.encode_to_base64(path)
        return mime, b64

    @staticmethod
    def prepare_image_from_base64(b64_str: str, ext: str = "png") -> tuple[str, str]:
        try:
            base64.b64decode(b64_str, validate=True)
        except Exception:
            raise ValueError("Invalid base64 string")
        ext = ext.lower().lstrip(".")
        if ext not in MIME_MAP:
            raise ValueError(f"Unsupported image format: .{ext}")
        return MIME_MAP[ext], b64_str
