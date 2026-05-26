"""
nestifypy.pyunix.fonts
-------------------
Font asset management and caching system.
"""

from __future__ import annotations

import os
from typing import Any, Dict

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class FontSystem:
    """
    Manages loading and caching of fonts at various sizes.
    """
    __slots__ = ("_paths", "_cache", "_default_font")

    def __init__(self):
        self._paths: Dict[str, str] = {}
        self._cache: Dict[str, Dict[int, Any]] = {}
        self._default_font: Any = None

    def load(self, name: str, path: str) -> None:
        """Register a font path under a specific name."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Font file not found: {path}")
        self._paths[name] = path
        if name not in self._cache:
            self._cache[name] = {}

    def get(self, name: str, size: int) -> Any:
        """
        Get a loaded pygame.font.Font object.
        If the size hasn't been loaded yet, it loads and caches it.
        """
        if not _HAS_PYGAME:
            return None

        if not pygame.font.get_init():
            pygame.font.init()

        # Fallback to default pygame font if not found
        if name not in self._paths:
            print(f"Warning: Font '{name}' not found. Using default.")
            return pygame.font.Font(None, size)

        # Return cached
        if size in self._cache[name]:
            return self._cache[name][size]

        # Load and cache
        path = self._paths[name]
        font = pygame.font.Font(path, size)
        self._cache[name][size] = font
        return font

    def clear(self) -> None:
        """Clear the font cache."""
        self._cache.clear()
        for name in self._paths:
            self._cache[name] = {}


Fonts = FontSystem()
