"""
nestifypy.json.parser
------------------
Parsing logic for JSON strings and files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from nestifypy.yaml import DotDict
from nestifypy.json.exceptions import JsonParseError
from nestifypy.json.models import JsonObject
from nestifypy.json.utils import to_dotdict

class JsonParser:
    """Handles parsing of JSON strings and files."""

    @staticmethod
    def parse(text: str, as_dotdict: bool = False) -> Any:
        """Parse a JSON string."""
        try:
            data = json.loads(text)
            if as_dotdict and isinstance(data, dict):
                return to_dotdict(data)
            return data
        except json.JSONDecodeError as e:
            raise JsonParseError(f"Failed to parse JSON string: {e}")

    @staticmethod
    def read_file(path: Union[str, Path], as_dotdict: bool = False) -> Any:
        """Read and parse a JSON file."""
        p = Path(path)
        if not p.exists():
            raise JsonParseError(f"JSON file not found: {p}")
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            if as_dotdict and isinstance(data, dict):
                return to_dotdict(data)
            return data
        except json.JSONDecodeError as e:
            raise JsonParseError(f"Failed to parse JSON file '{p}': {e}")
