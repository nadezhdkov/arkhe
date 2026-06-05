"""
arkhe.pyunix.window
-----------------------
Window creation, management, and display utilities.
"""
from __future__ import annotations

import os
from typing import Any, Optional, Tuple

from arkhe.pyunix.exceptions import WindowError
from arkhe.pyunix.math import Color

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class WindowSystem:
    """Manages the pygame display surface and window properties."""

    def __init__(self) -> None:
        self.surface: Any       = None
        self.width:   int       = 0
        self.height:  int       = 0
        self._title:  str       = ""
        self._clear_color: Tuple[int, int, int] = (0, 0, 0)

    def create(
        self,
        title: str,
        size: Tuple[int, int],
        fullscreen: bool = False,
        vsync: bool = True,
        resizable: bool = False,
    ) -> Any:
        """
        Initialize pygame and create the main window.

        Args:
            title:      Window title bar text.
            size:       (width, height) in pixels.
            fullscreen: Start in fullscreen mode.
            vsync:      Enable V-Sync (may be ignored on some platforms/drivers).
            resizable:  Allow the user to resize the window.
        """
        if not _HAS_PYGAME:
            raise WindowError("pygame is required to create a window.")

        if not pygame.get_init():
            pygame.init()

        flags = 0
        if fullscreen:
            flags |= pygame.FULLSCREEN
        if resizable:
            flags |= pygame.RESIZABLE

        try:
            self.surface = pygame.display.set_mode(size, flags, vsync=int(vsync))
        except (pygame.error, TypeError):
            self.surface = pygame.display.set_mode(size, flags)

        pygame.display.set_caption(title)
        self._title = title
        self.width, self.height = size
        return self.surface

    def clear(self, color: Any = None) -> None:
        """
        Fill the window with `color` (or the configured clear color).

        Call at the start of every draw method to erase the last frame.
        """
        if self.surface is None:
            return
        if color is None:
            fill = self._clear_color
        elif isinstance(color, Color):
            fill = color.to_rgb()
        else:
            fill = color
        self.surface.fill(fill)

    def set_clear_color(self, color: Any) -> None:
        """Set the background color used by Window.clear()."""
        if isinstance(color, Color):
            self._clear_color = color.to_rgb()
        else:
            self._clear_color = color

    def set_title(self, title: str) -> None:
        self._title = title
        if _HAS_PYGAME:
            pygame.display.set_caption(title)

    def set_icon(self, path: str) -> None:
        """Load an image file and use it as the window icon."""
        if not _HAS_PYGAME:
            return
        try:
            icon = pygame.image.load(path)
            pygame.display.set_icon(icon)
        except Exception as exc:
            raise WindowError(f"Failed to load icon '{path}': {exc}") from exc

    def center(self) -> None:
        """
        Center the window on the monitor.
        Must be called BEFORE create().
        """
        os.environ["SDL_VIDEO_CENTERED"] = "1"

    def toggle_fullscreen(self) -> None:
        if _HAS_PYGAME and self.surface:
            pygame.display.toggle_fullscreen()

    def screenshot(self, path: str = "screenshot.png") -> None:
        """Save the current frame to an image file."""
        if _HAS_PYGAME and self.surface:
            pygame.image.save(self.surface, path)

    @property
    def size(self) -> Tuple[int, int]:
        return (self.width, self.height)

    @property
    def center_pos(self) -> Tuple[int, int]:
        return (self.width // 2, self.height // 2)

    @property
    def rect(self) -> Any:
        if _HAS_PYGAME:
            return pygame.Rect(0, 0, self.width, self.height)
        return None

    @property
    def title(self) -> str:
        return self._title


Window = WindowSystem()
