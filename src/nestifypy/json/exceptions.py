"""
nestifypy.json.exceptions
----------------------
Custom exceptions for the JSON module.
"""

from nestifypy.core import ConfigError

class JsonError(ConfigError):
    """Base exception for all JSON-related errors."""
    pass

class JsonParseError(JsonError):
    """Raised when JSON parsing fails."""
    pass

class JsonValidationError(JsonError):
    """Raised when JSON schema validation fails."""
    pass
