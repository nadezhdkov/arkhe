"""
arkhe.pyunix.text
---------------------
Rich text rendering entity with shadow, outline, word-wrap, and alignment.
"""
from __future__ import annotations

from typing import Any, Callable, List, Optional, Tuple, Union

from arkhe.pyunix.math import Color
from arkhe.pyunix.sprite import Entity, Sprite

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


def _resolve_color(color: Any) -> Tuple[int, int, int]:
    if isinstance(color, Color):
        return color.to_rgb()
    if isinstance(color, str):
        if color.startswith("#"):
            return Color.from_hex(color).to_rgb()
        if _HAS_PYGAME:
            return pygame.Color(color)[:3]
        return (255, 255, 255)
    return tuple(color[:3])


class Text(Entity):
    """
    Declarative text entity.

    Supports: shadow, outline, word-wrap, left/center/right alignment,
    anchor points, and dynamic color/text updates with lazy re-rendering.
    """

    def __init__(
        self,
        text: Union[str, Callable[[], str]] = "",
        x: float = 0.0,
        y: float = 0.0,
        font_name: str = "default",
        size: int = 24,
        color: Any = "white",
        bold: bool = False,
        italic: bool = False,
        shadow: bool = False,
        shadow_color: Any = "black",
        shadow_offset: Tuple[int, int] = (2, 2),
        outline: bool = False,
        outline_color: Any = "black",
        outline_size: int = 1,
        align: str = "left",
        anchor: str = "topleft",
        layer: str = "ui",
        antialias: bool = True,
        max_width: Optional[int] = None,   # word-wrap at this pixel width
    ) -> None:
        super().__init__(x=x, y=y, layer=layer)
        
        self._text_fn = None
        if callable(text):
            self._text_fn = text
            self.text = ""
        else:
            self.text = text
            
        self.font_name     = font_name
        self.font_size     = size
        self.color         = _resolve_color(color)
        self.bold          = bold
        self.italic        = italic
        self.shadow        = shadow
        self.shadow_color  = _resolve_color(shadow_color)
        self.shadow_offset = shadow_offset
        self.outline       = outline
        self.outline_color = _resolve_color(outline_color)
        self.outline_size  = outline_size
        self.align         = align      # "left" | "center" | "right"
        self.anchor        = anchor     # pygame Rect attribute name
        self.antialias     = antialias
        self.max_width     = max_width

        self._surface: Optional[Any] = None
        self._rect:    Optional[Any] = None
        self._dirty:   bool          = True

        if _HAS_PYGAME:
            self._rebuild()

    # ── Public API ───────────────────────────
    
    def bind(self, fn: Callable[[], str]) -> "Text":
        """Bind text to a reactive function."""
        self._text_fn = fn
        return self

    def set_text(self, text: str) -> None:
        if self.text != text:
            self.text  = text
            self._dirty = True

    def set_color(self, color: Any) -> None:
        self.color  = _resolve_color(color)
        self._dirty = True

    def set_size(self, size: int) -> None:
        self.font_size = size
        self._dirty    = True

    @property
    def width(self) -> int:
        return self._surface.get_width() if self._surface else 0

    @property
    def height(self) -> int:
        return self._surface.get_height() if self._surface else 0

    # ── Internal rendering ───────────────────

    def _get_font(self) -> Any:
        from arkhe.pyunix.fonts import Fonts
        f = Fonts.get(self.font_name, self.font_size)
        if f:
            return f
        # Fallback: system font
        return pygame.font.SysFont(None, self.font_size, bold=self.bold, italic=self.italic)

    def _wrap_text(self, font: Any, text: str, max_w: int) -> List[str]:
        """Word-wrap `text` to fit within `max_w` pixels."""
        words  = text.split(" ")
        lines: List[str] = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if font.size(test)[0] <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    def _rebuild(self) -> None:
        if not _HAS_PYGAME:
            return
        font = self._get_font()
        lines = (
            self._wrap_text(font, self.text, self.max_width)
            if self.max_width
            else [self.text]
        )

        line_surfaces = [font.render(ln, self.antialias, self.color) for ln in lines]
        line_h  = font.get_linesize()
        max_w   = max((s.get_width() for s in line_surfaces), default=1)
        total_h = line_h * len(lines)

        pad_x = self.outline_size + (self.shadow_offset[0] if self.shadow else 0)
        pad_y = self.outline_size + (self.shadow_offset[1] if self.shadow else 0)

        w = max_w  + pad_x * 2
        h = total_h + pad_y * 2

        canvas = pygame.Surface((w, h), pygame.SRCALPHA)

        for idx, (line_surf, line_text) in enumerate(zip(line_surfaces, lines)):
            lw = line_surf.get_width()
            if self.align == "center":
                bx = (w - lw) // 2
            elif self.align == "right":
                bx = w - lw - pad_x
            else:
                bx = pad_x
            by = pad_y + idx * line_h

            # Shadow
            if self.shadow:
                sh_surf = font.render(line_text, self.antialias, self.shadow_color)
                canvas.blit(sh_surf, (bx + self.shadow_offset[0], by + self.shadow_offset[1]))

            # Outline
            if self.outline:
                ol_surf = font.render(line_text, self.antialias, self.outline_color)
                for dx in range(-self.outline_size, self.outline_size + 1):
                    for dy in range(-self.outline_size, self.outline_size + 1):
                        if dx == 0 and dy == 0:
                            continue
                        canvas.blit(ol_surf, (bx + dx, by + dy))

            # Main text
            canvas.blit(line_surf, (bx, by))

        self._surface = canvas
        self._rect    = canvas.get_rect()
        self._dirty   = False

    # ── Draw hook ────────────────────────────

    @Sprite.draw
    def draw(self) -> None:
        if not _HAS_PYGAME:
            return
            
        if self._text_fn:
            new_text = str(self._text_fn())
            if new_text != self.text:
                self.text = new_text
                self._dirty = True

        if self._dirty:
            self._rebuild()
            
        from arkhe.pyunix.render.canvas import Canvas
        surface = Canvas._screen
        
        if self._surface and self._rect and surface:
            setattr(self._rect, self.anchor, (int(self.x), int(self.y)))
            surface.blit(self._surface, self._rect)
