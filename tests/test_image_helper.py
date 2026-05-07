import pytest
import base64
from pathlib import Path
from src.image_helper import ImageHelper

SUPPORTED_FORMATS = ["png", "jpg", "jpeg", "gif", "webp"]

def test_read_image_from_path(tmp_path):
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"fake-image-data")
    result = ImageHelper.read_image(img_path)
    assert isinstance(result, bytes)
    assert result == b"fake-image-data"

def test_read_image_not_found():
    with pytest.raises(FileNotFoundError, match="not found"):
        ImageHelper.read_image(Path("/nonexistent/image.png"))

def test_encode_to_base64(tmp_path):
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"test-bytes")
    encoded = ImageHelper.encode_to_base64(img_path)
    decoded = base64.b64decode(encoded)
    assert decoded == b"test-bytes"

def test_encode_base64_string():
    raw = b"test-image"
    encoded = ImageHelper.encode_base64_string(raw)
    assert isinstance(encoded, str)
    decoded = base64.b64decode(encoded)
    assert decoded == raw

def test_detect_mime_type(tmp_path):
    for ext, expected in [
        ("png", "image/png"),
        ("jpg", "image/jpeg"),
        ("jpeg", "image/jpeg"),
        ("gif", "image/gif"),
        ("webp", "image/webp"),
    ]:
        p = tmp_path / f"test.{ext}"
        p.write_bytes(b"x")
        assert ImageHelper.detect_mime_type(p) == expected

def test_detect_mime_type_unsupported(tmp_path):
    p = tmp_path / "test.bmp"
    p.write_bytes(b"x")
    with pytest.raises(ValueError, match="Unsupported"):
        ImageHelper.detect_mime_type(p)

def test_prepare_image_from_path(tmp_path):
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"img")
    mime, b64 = ImageHelper.prepare_image(img_path)
    assert mime == "image/png"
    assert base64.b64decode(b64) == b"img"

def test_prepare_image_from_base64():
    b64_input = base64.b64encode(b"raw").decode()
    mime, b64 = ImageHelper.prepare_image_from_base64(b64_input, "png")
    assert mime == "image/png"
    assert b64 == b64_input
