"""
nestify.yaml.exceptions
----------------------
YAML specific exceptions.
"""

from nestify.core import ConfigError

class YamlPathError(ConfigError):
    """Raised when a requested YAML dot-path cannot be found."""
    pass
