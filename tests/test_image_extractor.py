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
    
    def test_missing_base64_marker(self):
        """Test data URI without ;base64 marker."""
        with pytest.raises(ValueError, match=";base64"):
            parse_data_uri("data:image/png,abc")
    
    def test_empty_base64_data(self):
        """Test data URI with empty base64 data."""
        with pytest.raises(ValueError, match="empty"):
            parse_data_uri("data:image/png;base64,")
    
    def test_none_input(self):
        """Test None input raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            parse_data_uri(None)
    
    def test_missing_comma_separator(self):
        """Test data URI without comma separator."""
        with pytest.raises(ValueError, match="missing comma separator"):
            parse_data_uri("data:image/png;base64")


class TestExtractImageByReference:
    def test_extract_recent_image(self, tmp_path):
        """Test extracting most recent [Image x] reference."""
        from src.image_extractor import extract_image_by_reference, ImageExtractor
        
        # Use test fixture
        fixture = Path("tests/fixtures/history-sample.jsonl")
        history_file = tmp_path / "prompt-history.jsonl"
        history_file.write_text(fixture.read_text())
        
        # Temporarily override HISTORY_FILE
        original = ImageExtractor.HISTORY_FILE
        ImageExtractor.HISTORY_FILE = history_file
        
        try:
            mime, b64 = extract_image_by_reference("[Image 1]")
            # Should return SECOND occurrence (most recent - reverse iteration)
            assert mime == "image/jpeg"
            assert b64.startswith("/9j/4AAQSkZJRgABAQ")
        finally:
            ImageExtractor.HISTORY_FILE = original
    
    def test_extract_nonexistent_raises(self, tmp_path):
        """Test ValueError for non-existent reference."""
        from src.image_extractor import extract_image_by_reference, ImageExtractor
        
        fixture = Path("tests/fixtures/history-sample.jsonl")
        history_file = tmp_path / "prompt-history.jsonl"
        history_file.write_text(fixture.read_text())
        
        original = ImageExtractor.HISTORY_FILE
        ImageExtractor.HISTORY_FILE = history_file
        
        try:
            with pytest.raises(ValueError, match="未找到"):
                extract_image_by_reference("[Image 999]")
        finally:
            ImageExtractor.HISTORY_FILE = original
    
    def test_missing_history_file_raises(self, tmp_path):
        """Test FileNotFoundError when history file doesn't exist."""
        from src.image_extractor import extract_image_by_reference, ImageExtractor
        
        original = ImageExtractor.HISTORY_FILE
        ImageExtractor.HISTORY_FILE = tmp_path / "nonexistent.jsonl"
        
        try:
            with pytest.raises(FileNotFoundError, match="不存在"):
                extract_image_by_reference("[Image 1]")
        finally:
            ImageExtractor.HISTORY_FILE = original