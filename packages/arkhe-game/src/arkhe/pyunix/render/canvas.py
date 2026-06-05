"""
arkhe.pyunix.render.canvas
------------------------------
Global Canvas API for high-level rendering operations.
Hides pygame.Surface completely.
"""
from __future__ import annotations
from typing import Any, Tuple, Union

from arkhe.pyunix.math import Color
from arkhe.pyunix.core._surface import Surface
from arkhe.pyunix.window import Window

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False

class CanvasSystem:
    """
    High-level rendering surface.
    Replaces raw screen manipulation (e.g. screen.fill).
    """
    
    @property
    def _screen(self) -> Any:
        return Window.surface

    def clear(self, color: Union[Color, str] = "black") -> None:
        """Clears the canvas with a color."""
        if not self._screen or not _HAS_PYGAME: return
        if isinstance(color, str):
            if color.startswith("#"):
                c = Color.from_hex(color).to_rgb()
            else:
                c = pygame.Color(color)[:3]
        else:
            c = color.to_rgb()
        self._screen.fill(c)

    def fill(self, color: Union[Color, str]) -> None:
        """Alias for clear()."""
        self.clear(color)

    def snapshot(self, path: str = "screenshot.png") -> None:
        """Saves the current frame to disk."""
        if not self._screen or not _HAS_PYGAME: return
        pygame.image.save(self._screen, path)

    @property
    def width(self) -> int:
        return Window.width

    @property
    def height(self) -> int:
        return Window.height

    @property
    def size(self) -> Tuple[int, int]:
        return (self.width, self.height)

    @property
    def center(self) -> Tuple[int, int]:
        return (self.width // 2, self.height // 2)

Canvas = CanvasSystem()
