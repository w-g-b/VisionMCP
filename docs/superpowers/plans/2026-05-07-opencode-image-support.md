# OpenCode Image Paste Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable Vision MCP to automatically extract and analyze images pasted in OpenCode by recognizing `[Image x]` references.

**Architecture:** Add image extraction module that reads OpenCode's prompt-history.jsonl backwards to find recent image data URIs, then enhance existing MCP tools to auto-detect image references vs file paths vs base64 data.

**Tech Stack:** Python 3.10+, fastmcp, openai, pathlib, json, re (standard library)

---

## File Structure

**Create:**
- `src/image_extractor.py` - Image extraction from OpenCode history

**Modify:**
- `src/main.py` - Add auto-detection to `describe_image` and `ask_image` tools

**Test:**
- `tests/test_image_extractor.py` - Unit tests for extraction logic
- `tests/test_main_integration.py` - Integration tests for tool enhancement

---

### Task 1: Create image_extractor.py module and test structure

**Files:**
- Create: `src/image_extractor.py`
- Create: `tests/test_image_extractor.py`

- [ ] **Step 1: Create empty image_extractor.py with imports**

```python
import json
import re
from pathlib import Path
from typing import Optional


class ImageExtractor:
    """Extract image data from OpenCode prompt history."""
    
    HISTORY_FILE = Path("~/.local/state/opencode/prompt-history.jsonl").expanduser()
```

- [ ] **Step 2: Create test file with basic test structure**

```python
import pytest
from pathlib import Path
from src.image_extractor import ImageExtractor


class TestImageExtractor:
    def test_init(self):
        """Test ImageExtractor initialization."""
        extractor = ImageExtractor()
        expected_path = Path("~/.local/state/opencode/prompt-history.jsonl").expanduser()
        assert extractor.HISTORY_FILE == expected_path
```

- [ ] **Step 3: Run test to verify module loads**

Run: `.venv/bin/pytest tests/test_image_extractor.py::TestImageExtractor::test_init -v`

Expected: PASS

- [ ] **Step 4: Commit module scaffold**

```bash
git add src/image_extractor.py tests/test_image_extractor.py
git commit -m "feat: add image_extractor module scaffold"
```

---

### Task 2: Implement is_image_reference helper function

**Files:**
- Modify: `src/image_extractor.py`
- Modify: `tests/test_image_extractor.py`

- [ ] **Step 1: Write tests for is_image_reference**

Add to `tests/test_image_extractor.py`:

```python
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
```

- [ ] **Step 2: Run tests to see failures**

Run: `.venv/bin/pytest tests/test_image_extractor.py::TestIsImageReference -v`

Expected: FAIL (function not defined)

- [ ] **Step 3: Implement is_image_reference**

Add to `src/image_extractor.py`:

```python
def is_image_reference(text: str) -> bool:
    """Check if text is an OpenCode image reference format.
    
    Matches:
    - "[Image 1]", "[Image 2]", etc.
    - "Image 1", "Image 2", etc.
    
    Args:
        text: Input text to check
        
    Returns:
        True if text matches image reference pattern
    """
    pattern = r'^\[Image\s+\d+\]$|^Image\s+\d+$'
    return bool(re.match(pattern, text.strip()))
```

- [ ] **Step 4: Run tests to verify implementation**

Run: `.venv/bin/pytest tests/test_image_extractor.py::TestIsImageReference -v`

Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit helper function**

```bash
git add src/image_extractor.py tests/test_image_extractor.py
git commit -m "feat: implement is_image_reference helper"
```

---

### Task 3: Implement parse_data_uri helper function

**Files:**
- Modify: `src/image_extractor.py`
- Modify: `tests/test_image_extractor.py`

- [ ] **Step 1: Write tests for parse_data_uri**

Add to `tests/test_image_extractor.py`:

```python
class TestParseDataUri:
    def test_png_data_uri(self):
        """Test parsing PNG data URI."""
        from src.image_extractor import parse_data_uri
        
        data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEA"
        mime, b64 = parse_data_uri(data_uri)
        assert mime == "image/png"
        assert b64 == "iVBORw0KGgoAAAANSUhEUgAAAAEA"
    
    def test_jpeg_data_uri(self):
        """Test parsing JPEG data URI."""
        from src.image_extractor import parse_data_uri
        
        data_uri = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQAB"
        mime, b64 = parse_data_uri(data_uri)
        assert mime == "image/jpeg"
        assert b64 == "/9j/4AAQSkZJRgABAQAAAQAB"
    
    def test_invalid_data_uri(self):
        """Test invalid data URI raises ValueError."""
        from src.image_extractor import parse_data_uri
        
        with pytest.raises(ValueError, match="Invalid data URI"):
            parse_data_uri("not-a-data-uri")
        
        with pytest.raises(ValueError, match="not an image"):
            parse_data_uri("data:text/plain;base64,some-data")
```

- [ ] **Step 2: Run tests to see failures**

Run: `.venv/bin/pytest tests/test_image_extractor.py::TestParseDataUri -v`

Expected: FAIL (function not defined)

- [ ] **Step 3: Implement parse_data_uri**

Add to `src/image_extractor.py`:

```python
def parse_data_uri(data_uri: str) -> tuple[str, str]:
    """Parse data URI into mime type and base64 data.
    
    Args:
        data_uri: Data URI string (e.g., "data:image/png;base64,<data>")
        
    Returns:
        Tuple of (mime_type, base64_data)
        
    Raises:
        ValueError: If data URI format is invalid or not an image
    """
    if not data_uri.startswith("data:"):
        raise ValueError("Invalid data URI: must start with 'data:'")
    
    # Parse: data:image/png;base64,<data>
    parts = data_uri.split(",", 1)
    if len(parts) != 2:
        raise ValueError("Invalid data URI: missing comma separator")
    
    header = parts[0]
    b64_data = parts[1]
    
    # Extract mime type: data:image/png;base64
    if not header.startswith("data:image/"):
        raise ValueError(f"Invalid data URI: '{header}' is not an image type")
    
    # Remove "data:" and ";base64"
    mime_part = header.replace("data:", "").replace(";base64", "")
    
    return mime_part, b64_data
```

- [ ] **Step 4: Run tests to verify implementation**

Run: `.venv/bin/pytest tests/test_image_extractor.py::TestParseDataUri -v`

Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit parse function**

```bash
git add src/image_extractor.py tests/test_image_extractor.py
git commit -m "feat: implement parse_data_uri helper"
```

---

### Task 4: Implement extract_image_by_reference core function

**Files:**
- Modify: `src/image_extractor.py`
- Modify: `tests/test_image_extractor.py`
- Create: `tests/fixtures/sample_history.jsonl`

- [ ] **Step 1: Create test fixture file**

Create `tests/fixtures/sample_history.jsonl`:

```json
{"input":"Some text without image","parts":[],"mode":"normal"}
{"input":"[Image 1] Test image","parts":[{"type":"file","mime":"image/png","filename":"clipboard","url":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}],"mode":"normal"}
{"input":"Another text","parts":[],"mode":"normal"}
{"input":"[Image 1] Second image (different session)","parts":[{"type":"file","mime":"image/jpeg","filename":"clipboard","url":"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKcpbKjQoHBxgNDAsLAwcKDQgMCggABwcICgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCv/wAALCAABAAIBAREA/8QAFgABAQEAAAAAAAAAAAAAAAAAAAUH/8QAIRAAAgIDAQEAAAAAAAAAAAAAAQIDBAAFIRIiMUH/2gAIAQEAAD8AM0ttKkWapZbV//Z"}],"mode":"normal"}
{"input":"[Image 999] Non-existent","parts":[],"mode":"normal"}
```

- [ ] **Step 2: Write tests for extract_image_by_reference**

Add to `tests/test_image_extractor.py`:

```python
class TestExtractImageByReference:
    def test_extract_recent_image(self, tmp_path):
        """Test extracting most recent image reference."""
        from src.image_extractor import extract_image_by_reference
        
        # Copy fixture to temp location
        fixture = Path("tests/fixtures/sample_history.jsonl")
        history_file = tmp_path / "prompt-history.jsonl"
        history_file.write_text(fixture.read_text())
        
        # Monkey patch HISTORY_FILE
        import src.image_extractor as module
        original = module.ImageExtractor.HISTORY_FILE
        module.ImageExtractor.HISTORY_FILE = history_file
        
        try:
            mime, b64 = extract_image_by_reference("[Image 1]")
            # Should return the SECOND occurrence (most recent)
            assert mime == "image/jpeg"
            assert b64.startswith("/9j/4AAQSkZJRgABAQ")
        finally:
            module.ImageExtractor.HISTORY_FILE = original
    
    def test_extract_nonexistent_raises(self, tmp_path):
        """Test ValueError for non-existent reference."""
        from src.image_extractor import extract_image_by_reference
        
        fixture = Path("tests/fixtures/sample_history.jsonl")
        history_file = tmp_path / "prompt-history.jsonl"
        history_file.write_text(fixture.read_text())
        
        import src.image_extractor as module
        original = module.ImageExtractor.HISTORY_FILE
        module.ImageExtractor.HISTORY_FILE = history_file
        
        try:
            with pytest.raises(ValueError, match="未找到图片引用"):
                extract_image_by_reference("[Image 999]")
        finally:
            module.ImageExtractor.HISTORY_FILE = original
    
    def test_missing_history_file_raises(self, tmp_path):
        """Test FileNotFoundError when history file missing."""
        from src.image_extractor import extract_image_by_reference
        
        import src.image_extractor as module
        original = module.ImageExtractor.HISTORY_FILE
        module.ImageExtractor.HISTORY_FILE = tmp_path / "nonexistent.jsonl"
        
        try:
            with pytest.raises(FileNotFoundError, match="OpenCode历史文件不存在"):
                extract_image_by_reference("[Image 1]")
        finally:
            module.ImageExtractor.HISTORY_FILE = original
```

- [ ] **Step 3: Run tests to see failures**

Run: `.venv/bin/pytest tests/test_image_extractor.py::TestExtractImageByReference -v`

Expected: FAIL (function not defined)

- [ ] **Step 4: Implement extract_image_by_reference**

Add to `src/image_extractor.py`:

```python
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
    
    # Check history file exists
    if not ImageExtractor.HISTORY_FILE.exists():
        raise FileNotFoundError("OpenCode历史文件不存在，请确认已粘贴图片")
    
    # Read and reverse lines (most recent first)
    try:
        with open(ImageExtractor.HISTORY_FILE, "r") as f:
            lines = f.readlines()
    except IOError as e:
        raise IOError(f"无法读取历史文件：{e}")
    
    # Iterate backwards to find most recent match
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        # Check if input contains our image reference
        input_text = entry.get("input", "")
        if ref_normalized not in input_text:
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
```

- [ ] **Step 5: Run tests to verify implementation**

Run: `.venv/bin/pytest tests/test_image_extractor.py::TestExtractImageByReference -v`

Expected: PASS (all 3 tests)

- [ ] **Step 6: Commit core extraction logic**

```bash
git add src/image_extractor.py tests/test_image_extractor.py tests/fixtures/sample_history.jsonl
git commit -m "feat: implement extract_image_by_reference core function"
```

---

### Task 5: Enhance describe_image tool in main.py

**Files:**
- Modify: `src/main.py`
- Modify: `tests/test_main.py` (if exists, or create new test)

- [ ] **Step 1: Add imports to main.py**

At top of `src/main.py`, add after existing imports:

```python
from src.image_extractor import is_image_reference, extract_image_by_reference
```

- [ ] **Step 2: Modify describe_image function signature**

In `src/main.py`, find `describe_image` function (around line 50-78). Change the signature:

Old: `source_type: str = "path"`
New: `source_type: str = "auto"`

Update the docstring:

```python
@mcp.tool()
def describe_image(
    image_source: str,
    source_type: str = "auto",  # Changed default
    detail: str = "auto",
    image_format: str = "png",
) -> str:
    """Describe the content of an image.

    Args:
        image_source: Local file path, base64 string, or image reference ([Image x])
        source_type: "auto" (auto-detect), "path", or "base64"
        detail: "low", "high", or "auto"
        image_format: Image format for base64 input (default "png")
    """
```

- [ ] **Step 3: Add auto-detection logic**

Replace the try block in `describe_image`. The old `_build_messages` helper still exists, so we need to get mime/b64 first:

```python
    try:
        # Auto-detect or use explicit source_type
        if source_type == "auto":
            image_source_stripped = image_source.strip()
            
            if is_image_reference(image_source_stripped):
                # OpenCode image reference
                mime, b64 = extract_image_by_reference(image_source_stripped)
            elif Path(image_source).exists():
                # File path
                mime, b64 = ImageHelper.prepare_image(Path(image_source))
            else:
                # Assume base64
                mime, b64 = ImageHelper.prepare_image_from_base64(
                    image_source, image_format
                )
        elif source_type == "path":
            mime, b64 = ImageHelper.prepare_image(Path(image_source))
        else:  # source_type == "base64"
            mime, b64 = ImageHelper.prepare_image_from_base64(
                image_source, image_format
            )
        
        # Build message with extracted data
        messages = [
            {"role": "system", "content": DESCRIBE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}",
                            "detail": detail,
                        },
                    },
                    {"type": "text", "text": "请描述这张图片"},
                ],
            },
        ]
        return vision.call_model(messages)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"
```

- [ ] **Step 4: Run existing tests**

Run: `.venv/bin/pytest tests/ -v`

Expected: Existing tests still pass (backward compatibility)

- [ ] **Step 5: Commit describe_image enhancement**

```bash
git add src/main.py
git commit -m "feat: enhance describe_image with auto-detection"
```

---

### Task 6: Enhance ask_image tool in main.py

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: Modify ask_image function signature**

In `src/main.py`, find `ask_image` function (around line 80-110). Change signature:

Old: `source_type: str = "path"`
New: `source_type: str = "auto"`

Update docstring:

```python
@mcp.tool()
def ask_image(
    image_source: str,
    question: str,
    source_type: str = "auto",  # Changed default
    detail: str = "auto",
    image_format: str = "png",
) -> str:
    """Ask a question about an image.

    Args:
        image_source: Local file path, base64 string, or image reference ([Image x])
        question: The question to ask about the image
        source_type: "auto" (auto-detect), "path", or "base64"
        detail: "low", "high", or "auto"
        image_format: Image format for base64 input (default "png")
    """
```

- [ ] **Step 2: Add auto-detection logic**

Replace try block in `ask_image` with same pattern as describe_image:

```python
    try:
        if source_type == "auto":
            image_source_stripped = image_source.strip()
            
            if is_image_reference(image_source_stripped):
                mime, b64 = extract_image_by_reference(image_source_stripped)
            elif Path(image_source).exists():
                mime, b64 = ImageHelper.prepare_image(Path(image_source))
            else:
                mime, b64 = ImageHelper.prepare_image_from_base64(
                    image_source, image_format
                )
        elif source_type == "path":
            mime, b64 = ImageHelper.prepare_image(Path(image_source))
        else:
            mime, b64 = ImageHelper.prepare_image_from_base64(
                image_source, image_format
            )
        
        messages = [
            {"role": "system", "content": ASK_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}",
                            "detail": detail,
                        },
                    },
                    {"type": "text", "text": question},
                ],
            },
        ]
        return vision.call_model(messages)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"
```

- [ ] **Step 3: Run all tests**

Run: `.venv/bin/pytest tests/ -v`

Expected: All tests pass

- [ ] **Step 4: Commit ask_image enhancement**

```bash
git add src/main.py
git commit -m "feat: enhance ask_image with auto-detection"
```

---

### Task 7: Remove debug tool and cleanup

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: Remove debug_image_input tool**

Find and remove the `debug_image_input` function that was added for testing (around line 112-140 in main.py).

Delete the entire function definition including `@mcp.tool()` decorator.

- [ ] **Step 2: Remove unused _build_messages helper**

If `_build_messages` helper function is no longer used after Task 5 & 6 changes, remove it.

Check: Look for any other usage of `_build_messages` in the file. If not used, delete it (lines 17-48).

- [ ] **Step 3: Verify tools still work**

Run: `.venv/bin/python -m src.main`

Expected: Server starts without errors

Cancel after a few seconds.

- [ ] **Step 4: Commit cleanup**

```bash
git add src/main.py
git commit -m "refactor: remove debug tool and unused helpers"
```

---

### Task 8: Update README with new usage

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add auto-detection section to README**

In `README.md`, after the existing Usage section, add:

```markdown
## Auto-Detection Mode

Vision MCP now supports automatic detection of image sources:

**Image References (OpenCode pasted images):**
```
describe this [Image 1] using vision-mcp
what is in [Image 2]? use vision-mcp
```

**File Paths:**
```
describe /path/to/image.png using vision-mcp
```

**Base64 Strings:**
```
ask about this base64string with vision-mcp
```

The `source_type` parameter defaults to "auto" for seamless operation.
For explicit control:
- `source_type="path"` - Force file path mode
- `source_type="base64"` - Force base64 mode
```

- [ ] **Step 2: Update example commands**

Update the example section in README to show the new auto-detection:

```markdown
After configuring, you can ask OpenCode to analyze images:

```
describe [Image 1] using vision-mcp
what is in this screenshot.png? use vision-mcp
```

The MCP tool automatically detects whether you're referencing:
- A pasted image (e.g., `[Image 1]`)
- A file path
- A base64-encoded string
```

- [ ] **Step 3: Commit README update**

```bash
git add README.md
git commit -m "docs: update README with auto-detection usage"
```

---

### Task 9: Final integration test

**Files:**
- Run manual test with real OpenCode history

- [ ] **Step 1: Verify with real history file**

Check that the implementation works with real OpenCode history:

```bash
# Check history file exists
ls ~/.local/state/opencode/prompt-history.jsonl

# Check it contains image data
grep "[Image" ~/.local/state/opencode/prompt-history.jsonl | tail -3
```

Expected: See recent entries with image references

- [ ] **Step 2: Test MCP server manually**

Start the server and verify tools:

```bash
.venv/bin/python -m src.main
```

Verify no startup errors. Cancel after confirming it starts.

- [ ] **Step 3: Run all tests**

```bash
.venv/bin/pytest tests/ -v --tb=short
```

Expected: All tests pass

- [ ] **Step 4: Final commit**

```bash
git status
# If any uncommitted changes, commit them
git add -A
git commit -m "chore: final integration verification"
```

---

## Self-Review Checklist

**Spec Coverage:**
- ✓ Image reference detection (`is_image_reference`)
- ✓ Image extraction from history (`extract_image_by_reference`)
- ✓ Parse data URI (`parse_data_uri`)
- ✓ Auto-detection in `describe_image`
- ✓ Auto-detection in `ask_image`
- ✓ Backward compatibility (explicit source_type still works)
- ✓ Error handling (FileNotFoundError, ValueError)
- ✓ Recent image prioritization (reverse iteration)
- ✓ README updated with new usage

**Placeholder Scan:**
- ✓ No TBD/TODO markers
- ✓ All code blocks contain actual implementation code
- ✓ All test code is complete and runnable
- ✓ No vague steps like "add error handling" without specifics

**Type Consistency:**
- ✓ `is_image_reference(text: str) -> bool` - used in both tools
- ✓ `extract_image_by_reference(image_ref: str) -> tuple[str, str]` - returns (mime, b64)
- ✓ `parse_data_uri(data_uri: str) -> tuple[str, str]` - returns (mime, b64)
- ✓ All functions in main.py use same (mime, b64) pattern

---

Plan complete and saved to `docs/superpowers/plans/2026-05-07-opencode-image-support.md`. 

**Two execution options:**

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?