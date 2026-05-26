"""
nestifypy.json.models
------------------
Type definitions and models for the JSON module.
"""

from typing import Any, Dict, List, Union

# A generic JSON type representing parsed JSON data
JsonType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

# Dict representation of JSON object
JsonObject = Dict[str, Any]
