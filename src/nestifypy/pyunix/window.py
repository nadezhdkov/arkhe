"""
nestifypy.pyunix.window
--------------------
Window creation and management wrapper.

This module encapsulates Pygame's display initialization and window management
capabilities into a clean, object-oriented API. It provides a global `Window`
singleton to easily manage screen resolution, flags, and icons.
"""

from __future__ import annotations

import os
from typing import Any, Tuple

from nestifypy.pyunix.exceptions import WindowError

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class WindowSystem:
    """
    Manages the Pygame display surface and window properties.

    Provides methods to initialize the display, toggle fullscreen, set window
    icons, and retrieve dimensional information.
    """

    def __init__(self) -> None:
        """Initialize the WindowSystem with empty dimensions and surface."""
        self.surface: Any = None
        self.width = 0
        self.height = 0

    def create(
        self,
        title: str,
        size: Tuple[int, int],
        fullscreen: bool = False,
        vsync: bool = True,
        resizable: bool = False,
    ) -> Any:
        """
        Initialize the Pygame display and create the main application window.

        Args:
            title (str): The text to display in the window's title bar.
            size (Tuple[int, int]): A tuple containing the (width, height) of the window in pixels.
            fullscreen (bool): Whether to create the window in fullscreen mode. Defaults to False.
            vsync (bool): Whether to enable vertical synchronization. Defaults to True.
            resizable (bool): Whether the window should be resizable by the user. Defaults to False.

        Raises:
            WindowError: If Pygame is not installed in the environment.

        Returns:
            Any: The main Pygame display Surface.
        """
        if not _HAS_PYGAME:
            raise WindowError("pygame is required to create a window")

        if not pygame.get_init():
            pygame.init()

        flags = 0
        if fullscreen:
            flags |= pygame.FULLSCREEN
        if resizable:
            flags |= pygame.RESIZABLE

        # Some platforms/drivers don't support vsync flag well, fallback gracefully
        try:
            self.surface = pygame.display.set_mode(size, flags, vsync=int(vsync))
        except pygame.error:
            self.surface = pygame.display.set_mode(size, flags)

        pygame.display.set_caption(title)
        self.width, self.height = size

        return self.surface

    def center(self) -> None:
        """
        Force the window to spawn in the center of the user's monitor.

        Note:
            This method must be called **before** `Window.create()` to have any effect,
            as it modifies OS-level environment variables used by SDL.
        """
        os.environ['SDL_VIDEO_CENTERED'] = '1'

    def set_icon(self, path: str) -> None:
        """
        Set the window's icon from an image file.

        Args:
            path (str): The file path to the image to use as the icon.

        Raises:
            WindowError: If the image fails to load (e.g., file not found or invalid format).
        """
        if not _HAS_PYGAME:
            return
        try:
            icon = pygame.image.load(path)
            pygame.display.set_icon(icon)
        except Exception as e:
            raise WindowError(f"Failed to load icon '{path}': {e}")

    def toggle_fullscreen(self) -> None:
        """
        Toggle the window between windowed and fullscreen modes.

        Does nothing if Pygame is not installed or the window has not been created yet.
        """
        if not _HAS_PYGAME or not self.surface:
            return
        pygame.display.toggle_fullscreen()

    @property
    def center_pos(self) -> Tuple[int, int]:
        """
        Get the exact center coordinates of the current window.

        Returns:
            Tuple[int, int]: The (x, y) coordinates representing the center of the screen.
        """
        return (self.width // 2, self.height // 2)


# Global singleton
Window = WindowSystem()