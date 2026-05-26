"""
nestifypy.pyunix.exceptions
-------------------------
Custom exceptions for the Pyunix game framework.
"""


class PyunixError(Exception):
    """Base exception for all Pyunix errors."""
    pass


class WindowError(PyunixError):
    """Raised when window creation or management fails."""
    pass


class AssetError(PyunixError):
    """Raised when an asset cannot be loaded or found."""
    pass


class SceneError(PyunixError):
    """Raised when a scene operation fails."""
    pass


class InputError(PyunixError):
    """Raised when an input binding fails."""
    pass


class AudioError(PyunixError):
    """Raised when audio playback fails."""
    pass
