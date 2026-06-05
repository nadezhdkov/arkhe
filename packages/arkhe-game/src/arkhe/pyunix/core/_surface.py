"""
arkhe.pyunix.core._surface
------------------------------
Internal Surface wrapper that hides pygame.Surface from the user.
"""
from __future__ import annotations
from typing import Any, Tuple

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False

from arkhe.pyunix.math import Color

class Surface:
    """
    Wrapper over pygame.Surface.
    Never exposed directly to the developer — only through semantic methods.
    """
    def __init__(self, width: int, height: int, alpha: bool = True):
        if not _HAS_PYGAME:
            self._surface = None
            return
        flags = pygame.SRCALPHA if alpha else 0
        self._surface = pygame.Surface((width, height), flags)

    @classmethod
    def from_pygame(cls, pygame_surface: Any) -> "Surface":
        s = cls(1, 1)
        s._surface = pygame_surface
        return s

    @property
    def internal(self) -> Any:
        """Returns the internal pygame.Surface. Only for engine use."""
        return self._surface

    def tint(self, color: Color) -> "Surface":
        if not self._surface: return self
        new_surf = self._surface.copy()
        new_surf.fill(color.to_rgb(), special_flags=pygame.BLEND_RGBA_MULT)
        return Surface.from_pygame(new_surf)

    def outline(self, color: Color, thickness: int = 1) -> "Surface":
        if not self._surface: return self
        w, h = self._surface.get_size()
        out = pygame.Surface((w + thickness * 2, h + thickness * 2), pygame.SRCALPHA)
        mask = pygame.mask.from_surface(self._surface)
        mask_surf = mask.to_surface(setcolor=color.to_rgb(), unsetcolor=(0,0,0,0))
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx == 0 and dy == 0: continue
                out.blit(mask_surf, (thickness + dx, thickness + dy))
        out.blit(self._surface, (thickness, thickness))
        return Surface.from_pygame(out)

    def scale(self, new_size: Tuple[int, int]) -> "Surface":
        if not self._surface: return self
        scaled = pygame.transform.scale(self._surface, new_size)
        return Surface.from_pygame(scaled)

    def flip(self, x: bool = False, y: bool = False) -> "Surface":
        if not self._surface: return self
        flipped = pygame.transform.flip(self._surface, x, y)
        return Surface.from_pygame(flipped)

    def rotate(self, degrees: float) -> "Surface":
        if not self._surface: return self
        rotated = pygame.transform.rotate(self._surface, degrees)
        return Surface.from_pygame(rotated)

    def crop(self, x: int, y: int, width: int, height: int) -> "Surface":
        if not self._surface: return self
        cropped = self._surface.subsurface(pygame.Rect(x, y, width, height)).copy()
        return Surface.from_pygame(cropped)

    @property
    def width(self) -> int:
        return self._surface.get_width() if self._surface else 0

    @property
    def height(self) -> int:
        return self._surface.get_height() if self._surface else 0

    @property
    def size(self) -> Tuple[int, int]:
        return (self.width, self.height)
