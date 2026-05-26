"""
nestifypy.yaml.exceptions
----------------------
YAML specific exceptions.
"""

from nestifypy.core import ConfigError

class YamlPathError(ConfigError):
    """Raised when a requested YAML dot-path cannot be found."""
    pass
