"""
arkhe.pyunix.exceptions
---------------------------
Custom exceptions hierarchy for the Pyunix game framework.
"""
from __future__ import annotations


class PyunixError(Exception):
    """Base exception for all Pyunix errors."""


class WindowError(PyunixError):
    """Raised when window creation or management fails."""


class AssetError(PyunixError):
    """Raised when an asset cannot be loaded or found."""


class SceneError(PyunixError):
    """Raised when a scene operation fails."""


class InputError(PyunixError):
    """Raised when an input binding configuration fails."""


class AudioError(PyunixError):
    """Raised when audio playback or loading fails."""


class AnimationError(PyunixError):
    """Raised when animation configuration or playback fails."""


class ComponentError(PyunixError):
    """Raised when a component is incorrectly configured or missing."""
