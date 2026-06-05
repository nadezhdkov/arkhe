"""
arkhe.pyunix.render.draw
----------------------------
API for drawing primitives (shapes, lines, images, text inline).
Delegates to pygame.draw and pygame.font internally.
"""
from __future__ import annotations
from typing import Any, List, Tuple, Union

from arkhe.pyunix.math import Color
from arkhe.pyunix.core._surface import Surface
from arkhe.pyunix.render.canvas import Canvas

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False

def _resolve_color(color: Union[Color, str]) -> Tuple[int, int, int, int]:
    if isinstance(color, Color):
        return color.to_rgba()
    if isinstance(color, str):
        if color.startswith("#"):
            c = Color.from_hex(color)
            return c.to_rgba()
        if _HAS_PYGAME:
            c = pygame.Color(color)
            return (c.r, c.g, c.b, c.a)
    return (255, 255, 255, 255)


class DrawAPI:
    """
    Primitive drawing API — shapes, lines, images, text.
    All rendering must go through here or Canvas, never pygame.draw directly.
    """

    def _get_target(self) -> Any:
        return Canvas._screen

    # ── Shapes ───────────────────────────────────────────────

    def rect(
        self,
        x: float, y: float,
        width: float, height: float,
        color: Union[Color, str],
        *,
        filled: bool = True,
        border_radius: int = 0,
        stroke_width: int = 1,
        alpha: int = 255,
    ) -> None:
        target = self._get_target()
        if not target or not _HAS_PYGAME: return
        
        c = _resolve_color(color)
        final_alpha = min(c[3], alpha)
        c = (c[0], c[1], c[2], final_alpha)
        width_arg = 0 if filled else stroke_width
        
        rect = pygame.Rect(x, y, width, height)
        
        if final_alpha < 255:
            temp = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(temp, c, (0,0,width,height), width_arg, border_radius)
            target.blit(temp, (x, y))
        else:
            pygame.draw.rect(target, c[:3], rect, width_arg, border_radius)

    def circle(
        self,
        x: float, y: float,
        radius: float,
        color: Union[Color, str],
        *,
        filled: bool = True,
        stroke_width: int = 1,
        alpha: int = 255,
    ) -> None:
        target = self._get_target()
        if not target or not _HAS_PYGAME: return
        
        c = _resolve_color(color)
        final_alpha = min(c[3], alpha)
        c = (c[0], c[1], c[2], final_alpha)
        width_arg = 0 if filled else stroke_width
        
        if final_alpha < 255:
            temp = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(temp, c, (radius, radius), radius, width_arg)
            target.blit(temp, (x - radius, y - radius))
        else:
            pygame.draw.circle(target, c[:3], (x, y), radius, width_arg)

    def ellipse(
        self,
        x: float, y: float,
        width: float, height: float,
        color: Union[Color, str],
        *,
        filled: bool = True,
        stroke_width: int = 1,
    ) -> None:
        target = self._get_target()
        if not target or not _HAS_PYGAME: return
        c = _resolve_color(color)
        width_arg = 0 if filled else stroke_width
        pygame.draw.ellipse(target, c[:3], pygame.Rect(x, y, width, height), width_arg)

    def line(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        color: Union[Color, str],
        width: int = 1,
    ) -> None:
        target = self._get_target()
        if not target or not _HAS_PYGAME: return
        c = _resolve_color(color)
        pygame.draw.line(target, c[:3], (x1, y1), (x2, y2), width)

    def lines(
        self,
        points: List[Tuple[float, float]],
        color: Union[Color, str],
        *,
        closed: bool = False,
        width: int = 1,
    ) -> None:
        target = self._get_target()
        if not target or not _HAS_PYGAME or len(points) < 2: return
        c = _resolve_color(color)
        pygame.draw.lines(target, c[:3], closed, points, width)

    def polygon(
        self,
        points: List[Tuple[float, float]],
        color: Union[Color, str],
        *,
        filled: bool = True,
        stroke_width: int = 1,
    ) -> None:
        target = self._get_target()
        if not target or not _HAS_PYGAME or len(points) < 3: return
        c = _resolve_color(color)
        width_arg = 0 if filled else stroke_width
        pygame.draw.polygon(target, c[:3], points, width_arg)

    # ── Images ──────────────────────────────────────────────

    def image(
        self,
        surface: Any,
        x: float, y: float,
        *,
        rotation: float = 0.0,
        alpha: int = 255,
    ) -> None:
        target = self._get_target()
        if not target or not _HAS_PYGAME: return
        
        if hasattr(surface, "internal"):
            surf = surface.internal
        else:
            surf = surface  # assume raw pygame.Surface
            
        if not surf: return
        
        if alpha < 255:
            temp = surf.copy()
            temp.set_alpha(alpha)
            surf = temp
            
        if rotation != 0.0:
            surf = pygame.transform.rotate(surf, rotation)
            
        target.blit(surf, (x, y))

    # ── Text inline ─────────────────────────────────────────

    def text(
        self,
        text: str,
        x: float, y: float,
        *,
        font: str = "default",
        size: int = 24,
        color: Union[Color, str] = "white",
        anchor: str = "topleft",
    ) -> None:
        target = self._get_target()
        if not target or not _HAS_PYGAME: return
        
        # Simple inline text (Text entity is better for rich text)
        sysfont = pygame.font.SysFont(None, size)
        c = _resolve_color(color)[:3]
        surf = sysfont.render(text, True, c)
        
        rect = surf.get_rect()
        setattr(rect, anchor, (int(x), int(y)))
        
        target.blit(surf, rect)

Draw = DrawAPI()
