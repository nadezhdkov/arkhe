"""
nestifypy.pyunix.text
------------------
Declarative UI text rendering with rich formatting.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from nestifypy.pyunix.fonts import Fonts
from nestifypy.pyunix.sprite import Entity, Sprite
from nestifypy.types import Color

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class Text(Entity):
    """
    Declarative text entity with support for rich rendering features.
    """
    __slots__ = (
        "text", "font_name", "size", "color", "shadow", "shadow_color",
        "shadow_offset", "outline", "outline_color", "outline_size",
        "align", "anchor", "antialias", "_surface", "_rect"
    )

    def __init__(
        self,
        text: str,
        x: float = 0.0,
        y: float = 0.0,
        font: str = "default",
        size: int = 24,
        color: str | Tuple[int, int, int] | Color = "white",
        shadow: bool = False,
        shadow_color: str | Tuple[int, int, int] | Color = "black",
        shadow_offset: Tuple[int, int] = (2, 2),
        outline: bool = False,
        outline_color: str | Tuple[int, int, int] | Color = "black",
        outline_size: int = 1,
        align: str = "left",       # "left", "center", "right"
        anchor: str = "top_left",  # e.g., "center", "bottom_right"
        layer: str = "ui",
        antialias: bool = True
    ) -> None:
        super().__init__(x=x, y=y, layer=layer)
        self.text = text
        self.font_name = font
        self.size = size
        self.color = self._parse_color(color)
        self.shadow = shadow
        self.shadow_color = self._parse_color(shadow_color)
        self.shadow_offset = shadow_offset
        self.outline = outline
        self.outline_color = self._parse_color(outline_color)
        self.outline_size = outline_size
        self.align = align
        self.anchor = anchor
        self.antialias = antialias
        
        self._surface: Optional[Any] = None
        self._rect: Optional[Any] = None

        if _HAS_PYGAME:
            self._render()

    def _parse_color(self, color: Any) -> Tuple[int, int, int]:
        if isinstance(color, str):
            # Very basic fallback for named colors if needed, normally Color handles hex
            # For simplicity, if it's not a hex, let pygame color handle it later or use a predefined dict.
            if color.startswith("#"):
                return Color.from_hex(color).to_rgb()
            else:
                return pygame.Color(color)[:3] if _HAS_PYGAME else (255, 255, 255)
        elif isinstance(color, Color):
            return color.to_rgb()
        return color[:3]

    def set_text(self, new_text: str) -> None:
        if self.text != new_text:
            self.text = new_text
            if _HAS_PYGAME:
                self._render()

    def _render(self) -> None:
        """Internal method to generate the text surface."""
        if not _HAS_PYGAME:
            return

        font = Fonts.get(self.font_name, self.size)
        if not font:
            return

        # Basic text render
        base_surface = font.render(self.text, self.antialias, self.color)
        base_rect = base_surface.get_rect()

        final_width = base_rect.width
        final_height = base_rect.height

        if self.shadow:
            final_width += max(0, self.shadow_offset[0])
            final_height += max(0, self.shadow_offset[1])

        if self.outline:
            final_width += self.outline_size * 2
            final_height += self.outline_size * 2

        # Create a surface large enough to hold outline/shadow
        self._surface = pygame.Surface((final_width, final_height), pygame.SRCALPHA)
        self._rect = self._surface.get_rect()

        # Calculate base drawing position within the final surface
        draw_x = self.outline_size if self.outline else 0
        draw_y = self.outline_size if self.outline else 0

        # Draw shadow
        if self.shadow:
            shadow_surface = font.render(self.text, self.antialias, self.shadow_color)
            self._surface.blit(shadow_surface, (draw_x + self.shadow_offset[0], draw_y + self.shadow_offset[1]))

        # Draw outline
        if self.outline:
            outline_surface = font.render(self.text, self.antialias, self.outline_color)
            for dx in range(-self.outline_size, self.outline_size + 1):
                for dy in range(-self.outline_size, self.outline_size + 1):
                    if dx == 0 and dy == 0:
                        continue
                    self._surface.blit(outline_surface, (draw_x + dx, draw_y + dy))

        # Draw main text
        self._surface.blit(base_surface, (draw_x, draw_y))

        # Apply anchor
        setattr(self._rect, self.anchor, (self.x, self.y))

    @Sprite.draw
    def draw(self, surface: Any) -> None:
        if _HAS_PYGAME and self._surface and self._rect:
            # Re-apply anchor in case x/y moved
            setattr(self._rect, self.anchor, (self.x, self.y))
            surface.blit(self._surface, self._rect)

