"""
arkhe.json.models
---------------------
Type aliases and lightweight value types used across the JSON module.
"""
from __future__ import annotations

from typing import Any, Dict, List, Union

# ---------------------------------------------------------------------------
# Core JSON type aliases
# ---------------------------------------------------------------------------

#: Any value that can appear in a parsed JSON document.
JsonType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

#: A JSON object (dict at the root level).
JsonObject = Dict[str, Any]

#: A JSON array (list at the root level).
JsonArray = List[Any]


__all__ = ["JsonType", "JsonObject", "JsonArray"]
