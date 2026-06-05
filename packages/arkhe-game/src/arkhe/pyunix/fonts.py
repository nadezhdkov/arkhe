"""
arkhe.pyunix.fonts
----------------------
Font registry: load .ttf/.otf files by name and retrieve at any size with caching.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class FontSystem:
    __slots__ = ("_paths", "_cache")

    def __init__(self) -> None:
        self._paths: Dict[str, str]           = {}
        self._cache: Dict[str, Dict[int, Any]] = {}

    def load(self, name: str, path: str) -> None:
        """Register a font file under `name`."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Font file not found: {path}")
        self._paths[name] = path
        self._cache.setdefault(name, {})

    def get(self, name: str, size: int) -> Optional[Any]:
        """Return a cached (or freshly loaded) pygame Font object."""
        if not _HAS_PYGAME:
            return None
        if not pygame.font.get_init():
            pygame.font.init()

        if name not in self._paths:
            return None  # Caller will use fallback

        cache = self._cache.setdefault(name, {})
        if size not in cache:
            cache[size] = pygame.font.Font(self._paths[name], size)
        return cache[size]

    def clear(self) -> None:
        for name in self._cache:
            self._cache[name] = {}

    @property
    def registered(self) -> list:
        return list(self._paths.keys())


Fonts = FontSystem()
