"""
nestifypy.pyunix.sprite
--------------------
Sprite and collision system designed for ECS compatibility.
Decorators define entity lifecycle hooks.

Usage:
    @Sprite.ready
    def on_ready(self):
        self.image = Assets.image("player.png")

    @Sprite.update
    def on_update(self, dt):
        self.x += 100 * dt
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Tuple

from nestifypy.pyunix.physics import Collider, PhysicsWorld, Rigidbody

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class SpriteGroup:
    """
    A collection of sprites for batch updating and rendering.

    Provides methods to easily manage multiple entities, dispatching lifecycle
    events (like update and draw) to all of them at once.
    """

    def __init__(self) -> None:
        """Initialize an empty SpriteGroup."""
        self.sprites: List[Entity] = []

    def add(self, *sprites: Entity) -> None:
        """
        Add one or more entities to the group.

        Ignores entities that are already present in the group.

        Args:
            *sprites (Entity): Variable length argument list of Entity objects to add.
        """
        for s in sprites:
            if s not in self.sprites:
                self.sprites.append(s)

    def remove(self, *sprites: Entity) -> None:
        """
        Remove one or more entities from the group.

        Ignores entities that are not currently in the group.

        Args:
            *sprites (Entity): Variable length argument list of Entity objects to remove.
        """
        for s in sprites:
            if s in self.sprites:
                self.sprites.remove(s)

    def update(self, dt: float) -> None:
        """
        Call the `update` hooks on all sprites in the group.

        Args:
            dt (float): The delta time (time elapsed since the last frame) to pass to the sprites.
        """
        for s in self.sprites:
            s._dispatch("update", dt)

    def fixed_update(self) -> None:
        """
        Call the `fixed_update` hooks on all sprites in the group.

        Typically used for physics calculations that require a constant time step.
        """
        for s in self.sprites:
            s._dispatch("fixed_update")

    def draw(self, surface: Any, offset: Tuple[float, float] = (0, 0)) -> None:
        """
        Call the `draw` hooks and render images for all sprites.

        If `pygame` is available and the entity has an image, it automatically
        blits the image to the surface applying the given offset (useful for cameras).

        Args:
            surface (Any): The Pygame display surface (or equivalent) to draw on.
            offset (Tuple[float, float]): The (x, y) camera offset to apply during rendering.
                Defaults to (0, 0).
        """
        for s in self.sprites:
            s._dispatch("draw", surface)
            if s.image and _HAS_PYGAME:
                # Basic render with offset
                render_x = s.x - offset[0]
                render_y = s.y - offset[1]
                surface.blit(s.image, (render_x, render_y))


class SpriteSystem:
    """
    Decorator namespace for sprite lifecycle hooks.

    Provides static decorators used to mark methods inside an `Entity` class
    so they are automatically executed during the game loop.
    """

    @staticmethod
    def ready(func: Callable) -> Callable:
        """
        Decorator to mark a method to be called once when the entity is instantiated.

        Args:
            func (Callable): The method to decorate.

        Returns:
            Callable: The decorated method.
        """
        func._pyunix_sprite = "ready"
        return func

    @staticmethod
    def update(func: Callable) -> Callable:
        """
        Decorator to mark a method to be called every frame.

        Args:
            func (Callable): The method to decorate. It should accept a `dt` (delta time) argument.

        Returns:
            Callable: The decorated method.
        """
        func._pyunix_sprite = "update"
        return func

    @staticmethod
    def fixed_update(func: Callable) -> Callable:
        """
        Decorator to mark a method to be called at a fixed interval (e.g., for physics).

        Args:
            func (Callable): The method to decorate.

        Returns:
            Callable: The decorated method.
        """
        func._pyunix_sprite = "fixed_update"
        return func

    @staticmethod
    def draw(func: Callable) -> Callable:
        """
        Decorator to mark a method for custom rendering logic.

        Args:
            func (Callable): The method to decorate. It should accept a `surface` argument.

        Returns:
            Callable: The decorated method.
        """
        func._pyunix_sprite = "draw"
        return func

    @staticmethod
    def on_collision_enter(func: Callable) -> Callable:
        """Decorator to mark a method to be called when a collision begins."""
        func._pyunix_sprite = "on_collision_enter"
        return func

    @staticmethod
    def on_collision_stay(func: Callable) -> Callable:
        """Decorator to mark a method to be called every frame a collision continues."""
        func._pyunix_sprite = "on_collision_stay"
        return func

    @staticmethod
    def on_collision_exit(func: Callable) -> Callable:
        """Decorator to mark a method to be called when a collision ends."""
        func._pyunix_sprite = "on_collision_exit"
        return func

    @staticmethod
    def destroy(func: Callable) -> Callable:
        """
        Decorator to mark a method to be called when the entity is destroyed.

        Args:
            func (Callable): The method to decorate.

        Returns:
            Callable: The decorated method.
        """
        func._pyunix_sprite = "destroy"
        return func


Sprite = SpriteSystem()


class Entity:
    """
    Base class for all game objects in the ECS/Sprite system.

    Automatically registers lifecycle hooks via the `@Sprite` decorators
    and handles basic spatial properties (x, y) and collision logic.
    """

    __slots__ = ("x", "y", "layer", "image", "rigidbody", "collider", "_hooks")

    def __init__(
        self, 
        x: float = 0.0, 
        y: float = 0.0, 
        layer: str = "default",
        rigidbody: Optional[Rigidbody] = None,
        collider: Optional[Collider] = None
    ) -> None:
        """
        Initialize the Entity.

        Args:
            x (float): The initial X position. Defaults to 0.0.
            y (float): The initial Y position. Defaults to 0.0.
        """
        self.x = x
        self.y = y
        self.layer = layer
        self.image: Optional[Any] = None
        self.rigidbody = rigidbody
        self.collider = collider

        if self.rigidbody:
            self.rigidbody.entity = self

        if self.rigidbody or self.collider:
            PhysicsWorld.register(self)

        self._hooks: Dict[str, List[Callable]] = {
            "ready": [],
            "update": [],
            "fixed_update": [],
            "draw": [],
            "destroy": [],
            "on_collision_enter": [],
            "on_collision_stay": [],
            "on_collision_exit": []
        }
        self._register_hooks()
        self._dispatch("ready")

    def _register_hooks(self) -> None:
        """
        Scan all methods of the instance for `@Sprite` decorators and map them
        to the internal `_hooks` dictionary for fast dispatching.
        """
        for attr_name in dir(self):
            # Skip magic methods to avoid executing properties unexpectedly
            if attr_name.startswith("__"):
                continue
            try:
                attr = getattr(self, attr_name)
                if hasattr(attr, "_pyunix_sprite"):
                    hook_name = attr._pyunix_sprite
                    self._hooks[hook_name].append(attr)
            except AttributeError:
                pass

    def _dispatch(self, hook: str, *args: Any, **kwargs: Any) -> None:
        """
        Execute all methods registered for a specific lifecycle hook.

        Args:
            hook (str): The name of the hook to trigger (e.g., "update", "ready").
            *args (Any): Positional arguments to pass to the hook methods.
            **kwargs (Any): Keyword arguments to pass to the hook methods.
        """
        for func in self._hooks[hook]:
            func(*args, **kwargs)

    @property
    def rect(self) -> Any:
        """
        Get the Pygame Rect representing the entity's bounding box.

        Requires `pygame` to be installed. If an `image` is set, the rect
        matches its dimensions. Otherwise, returns a 0x0 rect at (x, y).

        Returns:
            Any: A `pygame.Rect` object, or None if Pygame is not available.
        """
        if not _HAS_PYGAME:
            return None
        if self.image:
            r = self.image.get_rect()
            r.topleft = (self.x, self.y)
            return r
        return pygame.Rect(self.x, self.y, 0, 0)

    # ── Collision Helpers ─────────────────────

    def collides_with(self, other: Entity) -> bool:
        """
        Perform a basic Axis-Aligned Bounding Box (AABB) collision check
        against another entity.

        Args:
            other (Entity): The other entity to check collision against.

        Returns:
            bool: True if the bounding rectangles intersect, False otherwise.
                Always returns False if Pygame is not installed.
        """
        if not _HAS_PYGAME:
            return False
        r1 = self.rect
        r2 = other.rect
        if r1 and r2:
            return r1.colliderect(r2)
        return False

    def distance_to(self, other: Entity) -> float:
        """
        Calculate the Euclidean distance between this entity and another.

        Args:
            other (Entity): The target entity.

        Returns:
            float: The distance in pixels (or current coordinate units).
        """
        return math.hypot(self.x - other.x, self.y - other.y)

    def destroy(self) -> None:
        """
        Trigger destruction logic by dispatching the `destroy` hook.

        This should be called right before removing the entity from active
        groups or systems to allow it to clean up resources.
        """
        self._dispatch("destroy")
        PhysicsWorld.unregister(self)