"""
arkhe.pyunix.camera
-----------------------
Professional 2D camera with smooth follow, dead zones, world bounds clamping,
zoom, screen shake, and parallax layers.

Usage:
    # Follow a player with lag
    Camera.follow(player, smooth=0.08)

    # Hard-snap follow
    Camera.follow(player, smooth=1.0)

    # Dead zone: camera only moves when target leaves a central region
    Camera.set_dead_zone(80, 60)

    # Clamp to a tile-map world
    Camera.set_world_bounds(0, 0, 3200, 1800)

    # Screen shake
    Camera.shake(intensity=8, duration=0.4)

    # Zoom in
    Camera.zoom(1.5)          # 150 %
    Camera.zoom_to(2.0, time=0.5)   # animated zoom

    # Parallax layers (backgrounds)
    Camera.add_parallax_layer("bg_sky",   surface_sky,   factor=0.1)
    Camera.add_parallax_layer("bg_cloud", surface_cloud, factor=0.4)

    # Apply offset to sprite rendering
    x_draw = sprite.x - Camera.offset[0]
    y_draw = sprite.y - Camera.offset[1]
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from arkhe.pyunix.math import Vector2


class _ParallaxLayer:
    __slots__ = ("name", "surface", "factor", "tile")

    def __init__(self, name: str, surface: Any, factor: float, tile: bool) -> None:
        self.name    = name
        self.surface = surface
        self.factor  = factor    # 0 = static, 1 = moves with camera
        self.tile    = tile


class CameraSystem:
    """
    2D camera with all the features a polished game needs.
    """

    def __init__(self) -> None:
        # Base position (world-space top-left corner of the viewport)
        self.x: float = 0.0
        self.y: float = 0.0
        self.zoom_level: float = 1.0

        # Follow
        self._target: Any = None
        self._smoothness: float = 0.1
        self._dead_zone_w: float = 0.0
        self._dead_zone_h: float = 0.0

        # World bounds clamping  (None = no clamping)
        self._bounds: Optional[Tuple[float, float, float, float]] = None  # l, t, r, b

        # Shake
        self._shake_intensity: float = 0.0
        self._shake_duration:  float = 0.0
        self._shake_offset:    Tuple[float, float] = (0.0, 0.0)
        self._shake_frequency: float = 30.0   # oscillations per second
        self._shake_time:      float = 0.0

        # Parallax
        self._parallax_layers: List[_ParallaxLayer] = []

        # Screen size (updated by the runtime each frame)
        self._screen_w: int = 800
        self._screen_h: int = 600

    # ── Follow ───────────────────────────────

    def follow(self, target: Any, smooth: float = 0.1) -> None:
        """
        Track a target entity.

        Args:
            target: Any object with `x` and `y` attributes (e.g. Entity).
            smooth: Lerp factor 0.0–1.0.  1.0 = instant snap.
        """
        self._target = target
        self._smoothness = max(0.0, min(1.0, smooth))

    def unfollow(self) -> None:
        """Stop following the current target."""
        self._target = None

    def set_dead_zone(self, width: float, height: float) -> None:
        """
        Set a rectangular dead zone (in world units) centered on the screen.

        The camera only scrolls when the target leaves this region.
        Set to (0, 0) to disable.
        """
        self._dead_zone_w = width
        self._dead_zone_h = height

    def set_world_bounds(
        self, left: float, top: float, right: float, bottom: float
    ) -> None:
        """
        Constrain the camera so it never shows outside the world rectangle.

        Args:
            left, top:     World-space origin of the level.
            right, bottom: World-space far edge of the level.
        """
        self._bounds = (left, top, right, bottom)

    def clear_bounds(self) -> None:
        self._bounds = None

    # ── Zoom ─────────────────────────────────

    def zoom(self, factor: float) -> None:
        """Immediately set the zoom level (1.0 = no zoom)."""
        self.zoom_level = max(0.05, factor)

    def zoom_to(self, factor: float, duration: float = 0.5) -> None:
        """
        Smoothly animate zoom to `factor` over `duration` seconds.
        Requires TweenManager to be running (done automatically by the game loop).
        """
        from arkhe.pyunix.tween import Tween, Ease
        Tween.to(self, "zoom_level", factor, duration, ease=Ease.IN_OUT_CUBIC)

    # ── Shake ────────────────────────────────

    def shake(
        self,
        intensity: float,
        duration: float,
        frequency: float = 30.0,
    ) -> None:
        """
        Trigger a screen-shake effect.

        Args:
            intensity:  Max displacement in pixels.
            duration:   Seconds the shake lasts.
            frequency:  Oscillations per second (higher = faster shake).
        """
        self._shake_intensity = intensity
        self._shake_duration  = duration
        self._shake_frequency = frequency
        self._shake_time      = 0.0

    def trauma(self, amount: float) -> None:
        """
        Add camera trauma (0–1) using the Squish/Juice approach.
        Intensity = trauma², duration accumulates. Good for hit-feel.
        """
        self.shake(
            intensity=64 * amount ** 2,
            duration=max(self._shake_duration, 0.3 * amount),
        )

    # ── Parallax ─────────────────────────────

    def add_parallax_layer(
        self,
        name: str,
        surface: Any,
        factor: float,
        tile: bool = True,
    ) -> None:
        """
        Register a parallax background layer.

        Args:
            name:    Unique identifier for the layer.
            surface: pygame Surface for this layer.
            factor:  Scroll factor relative to the camera. 0 = static, 1 = same as world.
            tile:    If True, the surface is tiled horizontally to fill the screen.
        """
        self._parallax_layers.append(_ParallaxLayer(name, surface, factor, tile))

    def remove_parallax_layer(self, name: str) -> None:
        self._parallax_layers = [l for l in self._parallax_layers if l.name != name]

    def draw_parallax(self, surface: Any) -> None:
        """
        Blit all registered parallax layers onto `surface`.
        Call this BEFORE drawing world sprites in your @Game.draw method.
        """
        try:
            import pygame
        except ImportError:
            return

        for layer in self._parallax_layers:
            lsurf = layer.surface
            if lsurf is None:
                continue
            lw = lsurf.get_width()
            lh = lsurf.get_height()
            offset_x = int(self.x * layer.factor) % max(lw, 1)
            offset_y = int(self.y * layer.factor) % max(lh, 1)

            if layer.tile:
                x = -offset_x
                while x < self._screen_w:
                    y = -offset_y
                    while y < self._screen_h:
                        surface.blit(lsurf, (x, y))
                        y += lh
                    x += lw
            else:
                surface.blit(lsurf, (-offset_x, -offset_y))

    # ── Update (called by runtime) ────────────

    def update(self, dt: float, screen_width: int, screen_height: int) -> None:
        """Advance follow logic, shake, and state. Called each frame by the engine."""
        self._screen_w = screen_width
        self._screen_h = screen_height

        # ── Follow ─────────────────────────
        if self._target is not None:
            target_x = getattr(self._target, "x", 0) - screen_width  / (2 * self.zoom_level)
            target_y = getattr(self._target, "y", 0) - screen_height / (2 * self.zoom_level)

            # Dead zone: only move when outside the box
            dx = target_x - self.x
            dy = target_y - self.y
            half_dz_w = self._dead_zone_w / 2
            half_dz_h = self._dead_zone_h / 2

            if abs(dx) > half_dz_w:
                clamped_target_x = target_x - (half_dz_w if dx > 0 else -half_dz_w)
                self.x += (clamped_target_x - self.x) * self._smoothness
            if abs(dy) > half_dz_h:
                clamped_target_y = target_y - (half_dz_h if dy > 0 else -half_dz_h)
                self.y += (clamped_target_y - self.y) * self._smoothness

        # ── Bounds clamping ─────────────────
        if self._bounds:
            l, t, r, b = self._bounds
            view_w = screen_width  / self.zoom_level
            view_h = screen_height / self.zoom_level
            self.x = max(l, min(self.x, r - view_w))
            self.y = max(t, min(self.y, b - view_h))

        # ── Shake ──────────────────────────
        if self._shake_duration > 0:
            self._shake_duration -= dt
            self._shake_time     += dt
            # Sinusoidal pattern for the x axis, phase-shifted for y
            import math
            freq = self._shake_frequency
            decay = max(0.0, self._shake_duration) / max(self._shake_duration + dt, 0.0001)
            ix = self._shake_intensity * decay
            ox = math.sin(self._shake_time * freq * 2 * math.pi) * ix
            oy = math.sin(self._shake_time * freq * 2 * math.pi + 1.5) * ix
            self._shake_offset = (ox, oy)
            self._shake_intensity *= 0.95   # exponential decay
        else:
            self._shake_offset   = (0.0, 0.0)
            self._shake_duration = 0.0

    # ── Coordinate conversion ─────────────────

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen-space pixel coordinates."""
        sx = (world_x - self.x) * self.zoom_level
        sy = (world_y - self.y) * self.zoom_level
        return (sx + self._shake_offset[0], sy + self._shake_offset[1])

    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen-space pixel coordinates to world coordinates."""
        wx = (screen_x - self._shake_offset[0]) / self.zoom_level + self.x
        wy = (screen_y - self._shake_offset[1]) / self.zoom_level + self.y
        return (wx, wy)

    # ── Properties ───────────────────────────

    @property
    def offset(self) -> Tuple[float, float]:
        """
        The (x, y) rendering offset to subtract from all world-space sprite positions.

        Usage in draw:
            entity.draw_self(screen, Camera.offset)
        """
        return (
            self.x + self._shake_offset[0],
            self.y + self._shake_offset[1],
        )

    @property
    def position(self) -> Vector2:
        """Camera world-space top-left as a Vector2."""
        return Vector2(self.x, self.y)

    @position.setter
    def position(self, value: Vector2) -> None:
        self.x = value.x
        self.y = value.y

    @property
    def target(self) -> Any:
        return self._target

    def __repr__(self) -> str:
        return f"Camera(pos=({self.x:.1f}, {self.y:.1f}), zoom={self.zoom_level:.2f})"


# Global singleton
Camera = CameraSystem()
