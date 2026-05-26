"""
nestifypy.json.utils
-----------------
Internal utilities for the JSON module.
"""

from typing import Any, Dict
from nestifypy.yaml import DotDict

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively deep merge two dictionaries.
    Values from 'override' will overwrite values from 'base' in case of conflict.
    """
    result = base.copy()
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = val
    return result

def to_dotdict(data: Dict[str, Any]) -> DotDict:
    """Convert a dictionary to a DotDict."""
    return DotDict(data)
