"""
nestifypy.pyunix.camera
--------------------
Camera system for rendering offsets, follow, screenshake, and zoom.

This module provides a 2D camera system that calculates the necessary visual
offsets to keep a target centered on the screen, while also supporting dynamic
effects like screen shake and zooming.

Usage:
    Camera.follow(player)
    Camera.shake(intensity=5, duration=0.5)
"""

from __future__ import annotations

import random
from typing import Any, Tuple

from nestifypy.pyunix.sprite import Entity


class CameraSystem:
    """
    Manages 2D camera translation, target tracking, and visual effects.

    The camera calculates an `offset` which should be subtracted from the
    world coordinates of sprites during rendering to position them correctly
    on the screen.
    """

    def __init__(self) -> None:
        """Initialize the CameraSystem with default values."""
        self.x: float = 0.0
        self.y: float = 0.0
        self.zoom_level: float = 1.0
        self.target: Any = None
        self.smoothness: float = 0.1

        # Shake state
        self._shake_intensity: float = 0.0
        self._shake_duration: float = 0.0
        self._shake_offset: Tuple[float, float] = (0.0, 0.0)

    def follow(self, target: Entity, smooth: float = 0.1) -> None:
        """
        Set an entity target for the camera to follow.

        The camera will smoothly interpolate (Lerp) its position towards the target
        to keep it centered on the screen.

        Args:
            target (Entity): The game entity to track.
            smooth (float): The interpolation factor between 0.0 and 1.0.
                Lower values mean a slower, "lazier" camera, while 1.0 means
                the camera instantly snaps to the target. Defaults to 0.1.
        """
        self.target = target
        self.smoothness = smooth

    def shake(self, intensity: float, duration: float) -> None:
        """
        Trigger a screen shake effect.

        The camera will rapidly offset its position by random amounts within
        the given intensity. The intensity decays exponentially over the duration.

        Args:
            intensity (float): The maximum displacement in pixels during the shake.
            duration (float): How long the shake effect should last, in seconds.
        """
        self._shake_intensity = intensity
        self._shake_duration = duration

    def zoom(self, factor: float) -> None:
        """
        Set the zoom level for the camera.

        Note:
            The zoom level relies on the renderer properly scaling the surface
            or sprites using `Camera.zoom_level`. It does not scale graphics automatically.

        Args:
            factor (float): The zoom multiplier (e.g., 2.0 for 200% zoom).
        """
        self.zoom_level = factor

    def update(self, dt: float, screen_width: int, screen_height: int) -> None:
        """
        Update the camera's position, follow logic, and shake state.

        This method is automatically called every frame by the game loop.

        Args:
            dt (float): The delta time (time elapsed since the last frame).
            screen_width (int): The current width of the game window.
            screen_height (int): The current height of the game window.
        """
        # Follow logic
        if self.target:
            target_x = self.target.x - (screen_width / 2)
            target_y = self.target.y - (screen_height / 2)

            # Lerp (Linear Interpolation)
            self.x += (target_x - self.x) * self.smoothness
            self.y += (target_y - self.y) * self.smoothness

        # Shake logic
        if self._shake_duration > 0:
            self._shake_duration -= dt
            offset_x = random.uniform(-self._shake_intensity, self._shake_intensity)
            offset_y = random.uniform(-self._shake_intensity, self._shake_intensity)
            self._shake_offset = (offset_x, offset_y)
            # Decay intensity smoothly
            self._shake_intensity = max(0.0, self._shake_intensity * 0.9)
        else:
            self._shake_offset = (0.0, 0.0)
            self._shake_intensity = 0.0

    @property
    def offset(self) -> Tuple[float, float]:
        """
        Get the current visual offset of the camera.

        This combines the camera's base position (from following the target)
        and the randomized offset from the shake effect.

        Returns:
            Tuple[float, float]: The total (x, y) offset to apply during rendering.
        """
        return (self.x + self._shake_offset[0], self.y + self._shake_offset[1])


# Global singleton
Camera = CameraSystem()