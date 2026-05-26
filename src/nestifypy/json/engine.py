"""
nestifypy.json.engine
------------------
Main orchestrator for the JSON module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Type, Union

from nestifypy.yaml import DotDict
from nestifypy.json.parser import JsonParser
from nestifypy.json.serializer import JsonSerializer
from nestifypy.json.validator import JsonValidator
from nestifypy.json.utils import deep_merge
from nestifypy.json.models import JsonObject

class Json:
    """
    Nestifypy JSON engine.
    
    Usage:
        config = Json.load("config.json")
        config.window.width
        
        raw_dict = Json.read("config.json")
    """

    @classmethod
    def load(cls, path: Union[str, Path], defaults: Optional[Dict[str, Any]] = None) -> DotDict:
        """Load a JSON file and return as a DotDict with optional defaults."""
        data = JsonParser.read_file(path, as_dotdict=False)
        if not isinstance(data, dict):
            # If the root is not an object, DotDict won't work well
            if defaults:
                return DotDict(defaults)
            raise TypeError(f"Cannot load JSON as DotDict, root is not an object: {type(data).__name__}")
            
        if defaults:
            data = deep_merge(defaults, data)
            
        return DotDict(data)

    @classmethod
    def read(cls, path: Union[str, Path]) -> Any:
        """Load a JSON file and return as raw Python objects (dict, list, etc.)."""
        return JsonParser.read_file(path, as_dotdict=False)

    @classmethod
    def parse(cls, text: str) -> Any:
        """Parse a JSON string into a raw Python object."""
        return JsonParser.parse(text, as_dotdict=False)
        
    @classmethod
    def parse_as_dotdict(cls, text: str) -> DotDict:
        """Parse a JSON string into a DotDict."""
        return JsonParser.parse(text, as_dotdict=True)

    @classmethod
    def save(cls, path: Union[str, Path], data: Any, pretty: bool = True) -> None:
        """Serialize data and save to a JSON file."""
        JsonSerializer.save_file(path, data, pretty=pretty)

    @classmethod
    def stringify(cls, data: Any) -> str:
        """Serialize data to a JSON string (compact)."""
        return JsonSerializer.stringify(data, pretty=False)

    @classmethod
    def pretty(cls, data: Any) -> str:
        """Serialize data to a pretty-formatted JSON string."""
        return JsonSerializer.stringify(data, pretty=True)

    @classmethod
    def merge(cls, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        return deep_merge(base, override)

    @classmethod
    def exists(cls, path: Union[str, Path]) -> bool:
        """Check if a JSON file exists."""
        return Path(path).is_file()

    @classmethod
    def validate(cls, config: Union[DotDict, JsonObject], schema: Dict[str, Type]) -> bool:
        """Validate a JSON object or DotDict against a flat schema."""
        return JsonValidator.validate(config, schema)
