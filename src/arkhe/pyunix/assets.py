"""
arkhe.pyunix.assets
-----------------------
Centralized asset loader and cache with advanced spritesheet, atlas, and
async pre-loading support.

All assets are cached in memory after the first load. The manager supports
relative paths via a configurable base directory, hotkey-friendly aliases,
and a sprite atlas system for trimmed/packed spritesheets.

Usage:
    Assets.set_base_path("assets/")

    img    = Assets.image("player.png")
    frames = Assets.spritesheet("hero.png", frame_size=(32, 32))
    snd    = Assets.sound("jump.wav")
    font   = Assets.font("PressStart", size=16)

    # Alias system
    Assets.alias("hero_idle", "hero.png")
    img = Assets.image("hero_idle")

    # Pre-load all at startup (avoid stutter)
    Assets.preload("player.png", "tiles.png", "bg_music.mp3")

    # Clear only images to free VRAM
    Assets.clear_images()
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from arkhe.pyunix.exceptions import AssetError

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class AssetManager:
    """
    Cached asset loading system.

    Caches images, sounds, and fonts by path+options key so that repeated
    requests never hit the filesystem twice.
    """

    def __init__(self) -> None:
        self._images: Dict[str, Any] = {}
        self._sounds: Dict[str, Any] = {}
        self._fonts:  Dict[str, Any] = {}
        self._base_path: Path = Path(".")
        self._aliases: Dict[str, str] = {}

    # ── Configuration ────────────────────────

    def set_base_path(self, path: str | Path) -> None:
        """Set the root directory for relative asset paths."""
        self._base_path = Path(path)

    def alias(self, name: str, real_path: str) -> None:
        """Register a short alias for a longer path."""
        self._aliases[name] = real_path

    def _resolve(self, path: str) -> Path:
        real = self._aliases.get(path, path)
        p = Path(real)
        return p if p.is_absolute() else self._base_path / p

    # ── Images ────────────────────────────────

    def image(
        self,
        path: str,
        scale: Optional[Tuple[int, int]] = None,
        alpha: bool = True,
        flip_x: bool = False,
        flip_y: bool = False,
    ) -> Any:
        """
        Load and return a pygame Surface.

        Args:
            path:    Relative or absolute path (or alias).
            scale:   Optional (width, height) to resize on load.
            alpha:   Preserve alpha channel (convert_alpha vs convert).
            flip_x:  Flip horizontally.
            flip_y:  Flip vertically.

        Returns:
            pygame.Surface
        """
        key = f"{path}|{scale}|{alpha}|{flip_x}|{flip_y}"
        if key in self._images:
            return self._images[key]

        if not _HAS_PYGAME:
            raise AssetError("pygame is required for image loading")

        resolved = self._resolve(path)
        if not resolved.exists():
            raise AssetError(f"Image not found: {resolved}")

        try:
            surf = pygame.image.load(str(resolved))
            surf = surf.convert_alpha() if alpha else surf.convert()
            if scale:
                surf = pygame.transform.scale(surf, scale)
            if flip_x or flip_y:
                surf = pygame.transform.flip(surf, flip_x, flip_y)
        except Exception as exc:
            raise AssetError(f"Failed to load image '{path}': {exc}") from exc

        self._images[key] = surf
        return surf

    # ── Spritesheets ──────────────────────────

    def spritesheet(
        self,
        path: str,
        frame_size: Tuple[int, int],
        start: int = 0,
        count: Optional[int] = None,
        scale: Optional[Tuple[int, int]] = None,
    ) -> List[Any]:
        """
        Slice a uniform spritesheet into a list of Surface frames.

        Frames are ordered left-to-right, top-to-bottom.

        Args:
            path:       Path to the spritesheet image.
            frame_size: (width, height) of each frame in pixels.
            start:      Index of the first frame to include (default 0).
            count:      Number of frames to extract (None = all after start).
            scale:      If set, each extracted frame is scaled to this size.

        Returns:
            List of pygame.Surface frames.
        """
        sheet = self.image(path)
        fw, fh = frame_size
        sw, sh = sheet.get_size()
        all_frames: List[Any] = []

        for row in range(0, sh, fh):
            for col in range(0, sw, fw):
                frame = sheet.subsurface((col, row, fw, fh)).copy()
                if scale:
                    frame = pygame.transform.scale(frame, scale)
                all_frames.append(frame)

        end = start + count if count is not None else len(all_frames)
        return all_frames[start:end]

    def spritesheet_row(
        self,
        path: str,
        frame_size: Tuple[int, int],
        row: int,
        count: Optional[int] = None,
        scale: Optional[Tuple[int, int]] = None,
    ) -> List[Any]:
        """
        Extract frames from a single row of a spritesheet.

        Args:
            path:       Path to the spritesheet.
            frame_size: (width, height) per frame.
            row:        Zero-based row index to extract.
            count:      Max frames to extract from that row (None = full row).
            scale:      Optional resize per frame.
        """
        sheet = self.image(path)
        fw, fh = frame_size
        sw, _ = sheet.get_size()
        cols = sw // fw
        actual_count = min(count, cols) if count else cols
        frames = []
        y = row * fh
        for col in range(actual_count):
            frame = sheet.subsurface((col * fw, y, fw, fh)).copy()
            if scale:
                frame = pygame.transform.scale(frame, scale)
            frames.append(frame)
        return frames

    def spritesheet_region(
        self,
        path: str,
        regions: List[Tuple[int, int, int, int]],
        scale: Optional[Tuple[int, int]] = None,
    ) -> List[Any]:
        """
        Extract frames from arbitrary (x, y, w, h) regions.

        Useful for non-uniform sprite atlas layouts.

        Args:
            path:    Path to the spritesheet/atlas.
            regions: List of (x, y, width, height) rectangles.
            scale:   Optional uniform output size.
        """
        sheet = self.image(path)
        frames = []
        for x, y, w, h in regions:
            frame = sheet.subsurface((x, y, w, h)).copy()
            if scale:
                frame = pygame.transform.scale(frame, scale)
            frames.append(frame)
        return frames

    # ── Sounds ────────────────────────────────

    def sound(self, path: str) -> Any:
        """
        Load and return a pygame.mixer.Sound object.

        Args:
            path: File path (.wav, .ogg, .mp3).

        Returns:
            pygame.mixer.Sound
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
        except Exception as exc:
            raise AssetError(f"Failed to load sound '{path}': {exc}") from exc

        self._sounds[path] = snd
        return snd

    # ── Fonts ─────────────────────────────────

    def font(
        self,
        name: Optional[str] = None,
        size: int = 24,
        bold: bool = False,
        italic: bool = False,
    ) -> Any:
        """
        Load and return a pygame.font.Font (system font).

        Args:
            name:   System font name (None = pygame default).
            size:   Point size.
            bold:   Request bold variant.
            italic: Request italic variant.
        """
        key = f"{name}|{size}|{bold}|{italic}"
        if key in self._fonts:
            return self._fonts[key]

        if not _HAS_PYGAME:
            raise AssetError("pygame is required for font loading")

        try:
            f = pygame.font.SysFont(name, size, bold=bold, italic=italic)
        except Exception as exc:
            raise AssetError(f"Failed to load font '{name}': {exc}") from exc

        self._fonts[key] = f
        return f

    def font_file(self, path: str, size: int = 24) -> Any:
        """
        Load a font from a .ttf / .otf file.

        Args:
            path: File path to the font.
            size: Point size.
        """
        key = f"file:{path}|{size}"
        if key in self._fonts:
            return self._fonts[key]

        if not _HAS_PYGAME:
            raise AssetError("pygame is required for font loading")

        resolved = self._resolve(path)
        if not resolved.exists():
            raise AssetError(f"Font file not found: {resolved}")

        try:
            f = pygame.font.Font(str(resolved), size)
        except Exception as exc:
            raise AssetError(f"Failed to load font file '{path}': {exc}") from exc

        self._fonts[key] = f
        return f

    # ── Batch / Cache Management ──────────────

    def preload(self, *paths: str) -> None:
        """
        Pre-load multiple images into cache sequentially.

        Call during a loading screen to prevent per-frame stutter later.
        """
        for path in paths:
            self.image(path)

    def preload_sounds(self, *paths: str) -> None:
        """Pre-load multiple sound files into cache."""
        for path in paths:
            self.sound(path)

    def clear_images(self) -> None:
        self._images.clear()

    def clear_sounds(self) -> None:
        self._sounds.clear()

    def clear_fonts(self) -> None:
        self._fonts.clear()

    def clear(self) -> None:
        """Purge ALL cached assets from memory."""
        self._images.clear()
        self._sounds.clear()
        self._fonts.clear()

    @property
    def stats(self) -> dict:
        """Return a summary of currently cached asset counts."""
        return {
            "images": len(self._images),
            "sounds": len(self._sounds),
            "fonts":  len(self._fonts),
        }

    # ── Low-level surface utilities ───────────

    @staticmethod
    def create_surface(
        width: int,
        height: int,
        color: Tuple[int, int, int, int] = (0, 0, 0, 0),
        alpha: bool = True,
    ) -> Any:
        """
        Create a blank pygame Surface.

        Args:
            width, height: Dimensions in pixels.
            color:         Fill color as (R, G, B, A). Defaults to transparent.
            alpha:         Include alpha channel (SRCALPHA flag).
        """
        if not _HAS_PYGAME:
            return None
        flags = pygame.SRCALPHA if alpha else 0
        surf = pygame.Surface((width, height), flags)
        surf.fill(color)
        return surf

    @staticmethod
    def tint_surface(surface: Any, color: Tuple[int, int, int]) -> Any:
        """
        Return a copy of `surface` tinted with `color`.

        Uses BLEND_RGB_MULT so mid-tones shift while black stays black.
        """
        if not _HAS_PYGAME:
            return surface
        tinted = surface.copy()
        overlay = pygame.Surface(tinted.get_size())
        overlay.fill(color)
        tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        return tinted

    @staticmethod
    def outline_surface(surface: Any, color: Tuple[int, int, int], thickness: int = 1) -> Any:
        """
        Return a new surface with a pixel-perfect outline drawn around `surface`'s opaque pixels.

        Useful for selection indicators, damage flash, etc.
        """
        if not _HAS_PYGAME:
            return surface

        mask = pygame.mask.from_surface(surface)
        outline_surf = pygame.Surface(
            (surface.get_width() + thickness * 2, surface.get_height() + thickness * 2),
            pygame.SRCALPHA
        )
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx == 0 and dy == 0:
                    continue
                outline_surf.blit(
                    mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0)),
                    (dx + thickness, dy + thickness)
                )
        outline_surf.blit(surface, (thickness, thickness))
        return outline_surf


# Global singleton
Assets = AssetManager()
