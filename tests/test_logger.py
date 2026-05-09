from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime


def test_logger_default_log_dir():
    """Test that default log_dir is project root"""
    from src.logger import ImageRequestLogger, PROJECT_ROOT
    
    logger = ImageRequestLogger(enabled=True)
    assert logger.log_dir == PROJECT_ROOT / "log"


def test_logger_disabled():
    """Test that disabled logger does not create files"""
    from src.logger import ImageRequestLogger
    
    with TemporaryDirectory() as tmpdir:
        logger = ImageRequestLogger(enabled=False, log_dir=tmpdir)
        
        logger.log_request(
            tool_name="describe_image",
            timestamp=datetime.now().isoformat(),
            image_urls=["data:image/png;base64,test123"],
            source_type="auto",
            detail="auto",
            image_format="png"
        )
        
        # Check that no files were created
        log_path = Path(tmpdir)
        assert len(list(log_path.iterdir())) == 0


def test_logger_enabled_creates_file():
    """Test that enabled logger creates log file"""
    from src.logger import ImageRequestLogger
    
    with TemporaryDirectory() as tmpdir:
        logger = ImageRequestLogger(enabled=True, log_dir=tmpdir)
        
        timestamp = datetime.now().isoformat()
        logger.log_request(
            tool_name="describe_image",
            timestamp=timestamp,
            image_urls=["data:image/png;base64,test123"],
            source_type="auto",
            detail="auto",
            image_format="png"
        )
        
        # Check that a log file was created
        log_path = Path(tmpdir)
        log_files = list(log_path.iterdir())
        assert len(log_files) == 1
        assert log_files[0].name.endswith(".log")


def test_logger_log_content_format():
    """Test that log content format is correct"""
    from src.logger import ImageRequestLogger
    
    with TemporaryDirectory() as tmpdir:
        logger = ImageRequestLogger(enabled=True, log_dir=tmpdir)
        
        timestamp = datetime.now().isoformat()
        logger.log_request(
            tool_name="describe_image",
            timestamp=timestamp,
            image_urls=["data:image/png;base64,test123"],
            source_type="auto",
            detail="auto",
            image_format="png"
        )
        
        # Read log file and check format
        log_path = Path(tmpdir)
        log_file = list(log_path.iterdir())[0]
        content = log_file.read_text()
        
        assert f"[{timestamp}] Tool: describe_image" in content
        assert "Parameters:" in content
        assert "Image URLs:" in content
        assert "data:image/png;base64,test123" in content
        assert "-" * 80 in content


def test_logger_multiple_image_urls():
    """Test that logger handles multiple image URLs (for compare_images)"""
    from src.logger import ImageRequestLogger
    
    with TemporaryDirectory() as tmpdir:
        logger = ImageRequestLogger(enabled=True, log_dir=tmpdir)
        
        timestamp = datetime.now().isoformat()
        logger.log_request(
            tool_name="compare_images",
            timestamp=timestamp,
            image_urls=[
                "data:image/png;base64,image1",
                "data:image/jpeg;base64,image2"
            ],
            source_type_1="auto",
            source_type_2="auto",
            detail="high"
        )
        
        # Read log file and check both URLs are logged
        log_path = Path(tmpdir)
        log_file = list(log_path.iterdir())[0]
        content = log_file.read_text()
        
        assert "data:image/png;base64,image1" in content
        assert "data:image/jpeg;base64,image2" in content
        assert "compare_images" in content


def test_logger_error_handling():
    """Test that error handling is silent (no exceptions raised)"""
    from src.logger import ImageRequestLogger
    
    # Try to log to an invalid directory
    logger = ImageRequestLogger(enabled=True, log_dir="/nonexistent/directory/path")
    
    # Should not raise an exception
    try:
        logger.log_request(
            tool_name="describe_image",
            timestamp=datetime.now().isoformat(),
            image_urls=["data:image/png;base64,test123"],
            source_type="auto",
            detail="auto",
            image_format="png"
        )
        # If we get here without exception, error handling worked
        assert True
    except Exception as e:
        # Should not reach here - exceptions should be caught
        assert False, f"Exception should have been caught: {e}"