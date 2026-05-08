import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastmcp import FastMCP

from src.main import create_app
from src.config import Config, ModelConfig

VALID_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4DwAAAQEBABjdcbQAAAAASUVORK5CYII="
