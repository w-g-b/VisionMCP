import pytest
from pathlib import Path
from src.image_extractor import ImageExtractor


class TestImageExtractor:
    def test_init(self):
        """Test ImageExtractor initialization."""
        extractor = ImageExtractor()
        expected_path = Path("~/.local/state/opencode/prompt-history.jsonl").expanduser()
        assert extractor.HISTORY_FILE == expected_path


class TestIsImageReference:
    def test_bracketed_format(self):
        """Test [Image x] format detection."""
        from src.image_extractor import is_image_reference
        
        assert is_image_reference("[Image 1]") == True
        assert is_image_reference("[Image 2]") == True
        assert is_image_reference("[Image 10]") == True
    
    def test_simple_format(self):
        """Test Image x format detection."""
        from src.image_extractor import is_image_reference
        
        assert is_image_reference("Image 1") == True
        assert is_image_reference("Image 2") == True
        assert is_image_reference("Image 10") == True
    
    def test_invalid_formats(self):
        """Test non-image-reference inputs."""
        from src.image_extractor import is_image_reference
        
        assert is_image_reference("/path/to/file.png") == False
        assert is_image_reference("base64string") == False
        assert is_image_reference("not an image ref") == False
        assert is_image_reference("[Image]") == False
        assert is_image_reference("") == False