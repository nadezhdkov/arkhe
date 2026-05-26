"""
nestifypy.json.serializer
----------------------
Serialization logic for JSON strings and files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union

from nestifypy.yaml import DotDict
from nestifypy.core import Logger

class JsonSerializer:
    """Handles serialization of Python objects to JSON."""

    @staticmethod
    def stringify(data: Any, pretty: bool = False) -> str:
        """Serialize data to a JSON string."""
        if isinstance(data, DotDict):
            data = data.to_dict()
        
        indent = 4 if pretty else None
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @staticmethod
    def save_file(path: Union[str, Path], data: Any, pretty: bool = True) -> None:
        """Serialize and write data to a JSON file."""
        p = Path(path)
        if isinstance(data, DotDict):
            data = data.to_dict()
            
        indent = 4 if pretty else None
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        Logger.info(f"Saved JSON → {p}")
