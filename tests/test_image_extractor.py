import pytest
from pathlib import Path
from src.image_extractor import ImageExtractor, is_image_reference, parse_data_uri


class TestImageExtractor:
    def test_init(self):
        """Test ImageExtractor initialization."""
        extractor = ImageExtractor()
        expected_path = Path("~/.local/state/opencode/prompt-history.jsonl").expanduser()
        assert extractor.HISTORY_FILE == expected_path


class TestIsImageReference:
    def test_bracketed_format(self):
        """Test [Image x] format detection."""
        assert is_image_reference("[Image 1]") == True
        assert is_image_reference("[Image 2]") == True
        assert is_image_reference("[Image 10]") == True
    
    def test_simple_format(self):
        """Test Image x format detection."""
        assert is_image_reference("Image 1") == True
        assert is_image_reference("Image 2") == True
        assert is_image_reference("Image 10") == True
    
    def test_invalid_formats(self):
        """Test non-image-reference inputs."""
        assert is_image_reference("/path/to/file.png") == False
        assert is_image_reference("base64string") == False
        assert is_image_reference("not an image ref") == False
        assert is_image_reference("[Image]") == False
        assert is_image_reference("") == False
    
    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert is_image_reference("[image 1]") == True
        assert is_image_reference("IMAGE 2") == True
        assert is_image_reference("[IMAGE 10]") == True
    
    def test_whitespace_handling(self):
        """Test whitespace edge cases."""
        assert is_image_reference("  [Image 1]  ") == True
        assert is_image_reference("\tImage 2\n") == True


class TestParseDataUri:
    def test_png_data_uri(self):
        """Test parsing PNG data URI."""
        data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEA"
        mime, b64 = parse_data_uri(data_uri)
        assert mime == "image/png"
        assert b64 == "iVBORw0KGgoAAAANSUhEUgAAAAEA"
    
    def test_jpeg_data_uri(self):
        """Test parsing JPEG data URI."""
        data_uri = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQAB"
        mime, b64 = parse_data_uri(data_uri)
        assert mime == "image/jpeg"
        assert b64 == "/9j/4AAQSkZJRgABAQAAAQAB"
    
    def test_invalid_data_uri(self):
        """Test invalid data URI raises ValueError."""
        with pytest.raises(ValueError, match="Invalid data URI"):
            parse_data_uri("not-a-data-uri")
        
        with pytest.raises(ValueError, match="not an image"):
            parse_data_uri("data:text/plain;base64,some-data")