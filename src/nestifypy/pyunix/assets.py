"""
nestifypy.pyunix.assets
--------------------
Asset loading and caching manager.

This module provides a centralized manager for loading and caching external resources
like images, sounds, and fonts. It prevents redundant disk I/O by keeping loaded
assets in memory, drastically improving performance.

Usage:
    img  = Assets.image("player.png")
    sfx  = Assets.sound("jump.wav")
    font = Assets.font("Arial", 24)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from nestifypy.pyunix.exceptions import AssetError

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class AssetManager:
    """
    Cached asset loading system.

    Manages the lifecycle of game assets. Ensures that requesting the same
    asset multiple times only hits the disk once.
    """

    def __init__(self) -> None:
        """Initialize the empty asset caches."""
        self._images: Dict[str, Any] = {}
        self._sounds: Dict[str, Any] = {}
        self._fonts: Dict[str, Any] = {}
        self._base_path: Path = Path(".")

    def set_base_path(self, path: str | Path) -> None:
        """
        Set the root directory for relative asset paths.

        Args:
            path (str | Path): The directory to serve as the base path.
        """
        self._base_path = Path(path)

    def _resolve(self, path: str) -> Path:
        """
        Resolve a string path into a concrete Path object based on the base path.

        Args:
            path (str): The relative or absolute path to resolve.

        Returns:
            Path: The resolved absolute or base-relative path.
        """
        p = Path(path)
        if p.is_absolute():
            return p
        return self._base_path / p

    # ── Images ────────────────────────────────

    def image(
        self,
        path: str,
        scale: Optional[Tuple[int, int]] = None,
        alpha: bool = True,
    ) -> Any:
        """
        Load an image from disk or return it from the cache.

        Args:
            path (str): The path to the image file.
            scale (Optional[Tuple[int, int]]): A (width, height) tuple to resize
                the image upon loading. Defaults to None (original size).
            alpha (bool): Whether to keep the image's transparency channel.
                Setting this to False optimizes rendering for solid images. Defaults to True.

        Raises:
            AssetError: If Pygame is missing, the file is not found, or it fails to load.

        Returns:
            Any: A Pygame `Surface` object containing the image data.
        """
        key = f"{path}:{scale}"
        if key in self._images:
            return self._images[key]

        if not _HAS_PYGAME:
            raise AssetError("pygame is required for image loading")

        resolved = self._resolve(path)
        if not resolved.exists():
            raise AssetError(f"Image not found: {resolved}")

        try:
            surface = pygame.image.load(str(resolved))
            if alpha:
                surface = surface.convert_alpha()
            else:
                surface = surface.convert()
            if scale:
                surface = pygame.transform.scale(surface, scale)
        except Exception as e:
            raise AssetError(f"Failed to load image '{path}': {e}")

        self._images[key] = surface
        return surface

    # ── Sprite Sheets ─────────────────────────

    def spritesheet(
        self,
        path: str,
        frame_size: Tuple[int, int],
    ) -> List[Any]:
        """
        Load an image and slice it into a grid of individual frames.

        This is heavily used for 2D animations where multiple frames are packed
        into a single file.

        Args:
            path (str): The path to the spritesheet image.
            frame_size (Tuple[int, int]): The (width, height) in pixels of each individual frame.

        Returns:
            List[Any]: A list of Pygame `Surface` objects representing the extracted frames,
                ordered from left-to-right, top-to-bottom.
        """
        sheet = self.image(path)
        frames = []
        fw, fh = frame_size
        sw, sh = sheet.get_size()
        for y in range(0, sh, fh):
            for x in range(0, sw, fw):
                frame = sheet.subsurface((x, y, fw, fh))
                frames.append(frame)
        return frames

    # ── Sounds ────────────────────────────────

    def sound(self, path: str) -> Any:
        """
        Load a sound effect from disk or return it from the cache.

        Args:
            path (str): The path to the sound file (e.g., .wav or .ogg).

        Raises:
            AssetError: If Pygame is missing, the file is not found, or it fails to load.

        Returns:
            Any: A Pygame `Sound` object ready for playback.
        """
        if path in self._sounds:
            return self._sounds[path]

        if not _HAS_PYGAME:
            raise AssetError("pygame is required for sound loading")

        resolved = self._resolve(path)
        if not resolved.exists():
            raise AssetError(f"Sound not found: {resolved}")

        try:
            snd = pygame.mixer.Sound(str(resolved))
        except Exception as e:
            raise AssetError(f"Failed to load sound '{path}': {e}")

        self._sounds[path] = snd
        return snd

    # ── Fonts ─────────────────────────────────

    def font(self, name: Optional[str] = None, size: int = 24) -> Any:
        """
        Load a system font or return it from the cache.

        Args:
            name (Optional[str]): The name of the system font (e.g., "Arial").
                If None, the default Pygame font is used. Defaults to None.
            size (int): The font size in pixels. Defaults to 24.

        Raises:
            AssetError: If Pygame is missing or the font fails to load.

        Returns:
            Any: A Pygame `Font` object used to render text.
        """
        key = f"{name}:{size}"
        if key in self._fonts:
            return self._fonts[key]

        if not _HAS_PYGAME:
            raise AssetError("pygame is required for font loading")

        try:
            f = pygame.font.SysFont(name, size)
        except Exception as e:
            raise AssetError(f"Failed to load font '{name}': {e}")

        self._fonts[key] = f
        return f

    # ── Cache Management ──────────────────────

    def preload(self, *paths: str) -> None:
        """
        Load multiple images into the cache sequentially.

        Useful to call during a loading screen to prevent stuttering later in the game.

        Args:
            *paths (str): A variable number of string paths to image files.
        """
        for path in paths:
            self.image(path)

    def clear(self) -> None:
        """
        Purge all loaded assets from memory.

        This forces the manager to reload from disk the next time an asset is requested.
        Useful when changing heavy scenes to free up RAM.
        """
        self._images.clear()
        self._sounds.clear()
        self._fonts.clear()


# Global singleton
Assets = AssetManager()