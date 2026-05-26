"""
nestifypy.pyunix.input
-------------------
Decorator-driven input system with action mapping.

This module provides an elegant way to handle user input (keyboard and mouse)
using decorators. The decorators only register metadata; the actual event
dispatching is handled by the engine's main runtime loop.

Usage:
    @Input.key_down("SPACE")
    def jump(self):
        ...

    @Input.key_held("LEFT")
    def move_left(self):
        ...

    @Input.action("jump")
    def on_jump(self):
        ...

    Input.bind_action("jump", "SPACE")
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


# ─────────────────────────────────────────────
#  Internal registries (populated by decorators)
# ─────────────────────────────────────────────

# Method-level registries: list of (method_name_or_func, key, handler_type)
_KEY_DOWN_HANDLERS: List[Tuple[Callable, str]] = []
_KEY_UP_HANDLERS: List[Tuple[Callable, str]] = []
_KEY_HELD_HANDLERS: List[Tuple[Callable, str]] = []
_MOUSE_CLICK_HANDLERS: List[Tuple[Callable, str]] = []
_MOUSE_MOTION_HANDLERS: List[Callable] = []

# Action mapping: action_name -> list of keys
_ACTION_MAP: Dict[str, List[str]] = {}
_ACTION_HANDLERS: List[Tuple[Callable, str]] = []

# Axis mapping: axis_name -> (positive_key, negative_key)
_AXIS_MAP: Dict[str, Tuple[str, str]] = {}


def _resolve_key(key_name: str) -> int:
    """
    Convert a human-readable key name to a Pygame key constant.

    Args:
        key_name (str): The string representation of the key (e.g., "SPACE", "A", "ESCAPE").

    Returns:
        int: The Pygame constant integer corresponding to the key, or 0 if not found/Pygame is missing.
    """
    if not _HAS_PYGAME:
        return 0
    name = f"K_{key_name.upper()}"
    val = getattr(pygame, name, None)
    if val is not None:
        return val
    # Try direct (e.g., K_SPACE, K_ESCAPE)
    return getattr(pygame, key_name.upper(), 0)


class Input:
    """
    Decorator-based input system.

    Provides a collection of static methods to decorate instance methods for handling
    user input, as well as utility functions to check key states and axes at runtime.
    """

    # ── Decorator APIs ────────────────────────

    @staticmethod
    def key_down(key: str) -> Callable:
        """
        Register a handler for a single key-press event.

        The decorated method will fire exactly once when the specified key is pressed down.

        Args:
            key (str): The string name of the key (e.g., "SPACE", "RETURN").

        Returns:
            Callable: The decorator function.
        """
        def decorator(func: Callable) -> Callable:
            func._pyunix_input = ("key_down", key)
            _KEY_DOWN_HANDLERS.append((func, key))
            return func
        return decorator

    @staticmethod
    def key_up(key: str) -> Callable:
        """
        Register a handler for a key-release event.

        The decorated method will fire exactly once when the specified key is released.

        Args:
            key (str): The string name of the key (e.g., "W", "UP").

        Returns:
            Callable: The decorator function.
        """
        def decorator(func: Callable) -> Callable:
            func._pyunix_input = ("key_up", key)
            _KEY_UP_HANDLERS.append((func, key))
            return func
        return decorator

    @staticmethod
    def key_held(key: str) -> Callable:
        """
        Register a handler fired every frame while a key is held down.

        Args:
            key (str): The string name of the key.

        Returns:
            Callable: The decorator function.
        """
        def decorator(func: Callable) -> Callable:
            func._pyunix_input = ("key_held", key)
            _KEY_HELD_HANDLERS.append((func, key))
            return func
        return decorator

    @staticmethod
    def mouse_click(button: str = "left") -> Callable:
        """
        Register a handler for a mouse button click.

        Args:
            button (str): The mouse button to listen for ("left", "middle", or "right").
                Defaults to "left".

        Returns:
            Callable: The decorator function.
        """
        def decorator(func: Callable) -> Callable:
            func._pyunix_input = ("mouse_click", button)
            _MOUSE_CLICK_HANDLERS.append((func, button))
            return func
        return decorator

    @staticmethod
    def mouse_motion(func: Callable) -> Callable:
        """
        Register a handler for mouse movement.

        The decorated method should accept two additional arguments: `pos` (Tuple[int, int])
        for the absolute screen position, and `rel` (Tuple[int, int]) for the relative movement.

        Args:
            func (Callable): The method to decorate.

        Returns:
            Callable: The decorated method.
        """
        func._pyunix_input = ("mouse_motion", None)
        _MOUSE_MOTION_HANDLERS.append(func)
        return func

    @staticmethod
    def action(action_name: str) -> Callable:
        """
        Register a handler for a named abstract action.

        Actions allow decoupling the physical key from the logic. They must be bound
        using `Input.bind_action` elsewhere in the code.

        Args:
            action_name (str): The custom name of the action (e.g., "jump", "shoot").

        Returns:
            Callable: The decorator function.
        """
        def decorator(func: Callable) -> Callable:
            func._pyunix_input = ("action", action_name)
            _ACTION_HANDLERS.append((func, action_name))
            return func
        return decorator

    # ── Runtime binding APIs ──────────────────

    @staticmethod
    def bind_action(action_name: str, *keys: str) -> None:
        """
        Bind one or more physical keys to a named action.

        Args:
            action_name (str): The custom name of the action.
            *keys (str): Variable length list of key names to bind to this action.
        """
        if action_name not in _ACTION_MAP:
            _ACTION_MAP[action_name] = []
        _ACTION_MAP[action_name].extend(keys)

    @staticmethod
    def bind_axis(axis_name: str, positive: str, negative: str) -> None:
        """
        Bind an axis to two keys representing positive and negative directions.

        Useful for continuous movement like an analog stick or W/S keys.

        Args:
            axis_name (str): The custom name for this axis (e.g., "horizontal").
            positive (str): The key representing the +1.0 direction (e.g., "D" or "RIGHT").
            negative (str): The key representing the -1.0 direction (e.g., "A" or "LEFT").
        """
        _AXIS_MAP[axis_name] = (positive, negative)

    @staticmethod
    def get_axis(axis_name: str) -> float:
        """
        Get the current value of a bound axis (-1.0, 0.0, or 1.0).

        Must be called during the game loop (after Pygame has been initialized).

        Args:
            axis_name (str): The name of the axis to query.

        Returns:
            float: 1.0 if the positive key is held, -1.0 if the negative key is held,
                0.0 if neither or both are held.
        """
        if not _HAS_PYGAME or axis_name not in _AXIS_MAP:
            return 0.0
        pos_key, neg_key = _AXIS_MAP[axis_name]
        keys = pygame.key.get_pressed()
        val = 0.0
        pos_code = _resolve_key(pos_key)
        neg_code = _resolve_key(neg_key)
        if pos_code and keys[pos_code]:
            val += 1.0
        if neg_code and keys[neg_code]:
            val -= 1.0
        return val

    @staticmethod
    def is_pressed(key: str) -> bool:
        """
        Check if a specific key is currently being held down.

        Can be used inside an `update` loop for continuous polling instead of decorators.

        Args:
            key (str): The string name of the key.

        Returns:
            bool: True if the key is currently pressed, False otherwise.
        """
        if not _HAS_PYGAME:
            return False
        code = _resolve_key(key)
        if not code:
            return False
        return pygame.key.get_pressed()[code]