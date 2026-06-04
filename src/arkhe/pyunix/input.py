"""
arkhe.pyunix.input
----------------------
Declarative input system with actions, axes, mouse, and gamepad support.

Mirrors the best parts of Unity's Input System and Godot's InputMap:
- **Actions** decouple intent from physical keys ("jump" → SPACE or W)
- **Axes** give smooth -1/+1 directional values
- **Polling API** for use inside update loops
- **Decorator API** for event-driven responses
- **Gamepad** basic left-stick and button support (via pygame.joystick)

Usage:
    # Map actions at startup
    Input.bind_action("jump",   "SPACE", "W", "UP")
    Input.bind_action("attack", "z")
    Input.bind_axis("horizontal", positive="RIGHT", negative="LEFT")
    Input.bind_axis("vertical",   positive="DOWN",  negative="UP")

    # Decorator API (inside a Game class)
    @Input.key_down("SPACE")
    def on_jump(self): ...

    @Input.action("attack")
    def on_attack(self): ...

    @Input.mouse_click("left")
    def on_click(self): ...

    # Polling API (inside update)
    h = Input.get_axis("horizontal")      # -1.0, 0.0, or 1.0
    if Input.is_pressed("LSHIFT"): ...
    pos = Input.mouse_position            # (x, y) tuple
    held = Input.action_held("jump")      # True if any bound key is held
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


# ---------------------------------------------------------------------------
# Internal registries  (populated by decorators at class-definition time)
# ---------------------------------------------------------------------------

_KEY_DOWN_HANDLERS:    List[Tuple[Callable, str]] = []
_KEY_UP_HANDLERS:      List[Tuple[Callable, str]] = []
_KEY_HELD_HANDLERS:    List[Tuple[Callable, str]] = []
_MOUSE_CLICK_HANDLERS: List[Tuple[Callable, str]] = []
_MOUSE_MOTION_HANDLERS: List[Callable] = []
_ACTION_HANDLERS:      List[Tuple[Callable, str]] = []

# Runtime mappings
_ACTION_MAP: Dict[str, List[str]] = {}          # action → keys
_AXIS_MAP:   Dict[str, Tuple[str, str]] = {}    # axis → (pos_key, neg_key)

# State tracked across frames
_just_pressed:  Set[int] = set()
_just_released: Set[int] = set()
_held_keys:     Set[int] = set()
_mouse_pos:     Tuple[int, int] = (0, 0)
_mouse_rel:     Tuple[int, int] = (0, 0)
_mouse_buttons: Tuple[bool, bool, bool] = (False, False, False)
_scroll_delta:  float = 0.0


def _resolve_key(key_name: str) -> int:
    """Convert a human-readable key name to a Pygame key constant integer."""
    if not _HAS_PYGAME:
        return 0
    name = f"K_{key_name.upper()}"
    val = getattr(pygame, name, None)
    if val is not None:
        return val
    return getattr(pygame, key_name.upper(), 0)


def _update_state(event: Any) -> None:
    """Called by the runtime loop for every pygame event to track state."""
    global _mouse_pos, _mouse_rel, _mouse_buttons, _scroll_delta

    if not _HAS_PYGAME:
        return

    if event.type == pygame.KEYDOWN:
        code = event.key
        _just_pressed.add(code)
        _held_keys.add(code)

    elif event.type == pygame.KEYUP:
        code = event.key
        _just_released.add(code)
        _held_keys.discard(code)

    elif event.type == pygame.MOUSEMOTION:
        _mouse_pos = event.pos
        _mouse_rel = event.rel

    elif event.type == pygame.MOUSEBUTTONDOWN:
        _mouse_buttons = pygame.mouse.get_pressed()

    elif event.type == pygame.MOUSEBUTTONUP:
        _mouse_buttons = pygame.mouse.get_pressed()

    elif event.type == pygame.MOUSEWHEEL:
        _scroll_delta = float(event.y)


def _clear_frame_state() -> None:
    """Flush per-frame state (called at the start of each loop iteration)."""
    global _scroll_delta
    _just_pressed.clear()
    _just_released.clear()
    _scroll_delta = 0.0


# ---------------------------------------------------------------------------
# Public Input API
# ---------------------------------------------------------------------------

class _InputAPI:
    """
    Unified input access: decorators, polling, action map, and gamepad.
    """

    # ─── Decorator API ─────────────────────────────────────────────────────

    @staticmethod
    def key_down(key: str) -> Callable:
        """Fires once on the frame the key is pressed."""
        def decorator(func: Callable) -> Callable:
            func._pyunix_input = ("key_down", key)
            _KEY_DOWN_HANDLERS.append((func, key))
            return func
        return decorator

    @staticmethod
    def key_up(key: str) -> Callable:
        """Fires once on the frame the key is released."""
        def decorator(func: Callable) -> Callable:
            func._pyunix_input = ("key_up", key)
            _KEY_UP_HANDLERS.append((func, key))
            return func
        return decorator

    @staticmethod
    def key_held(key: str) -> Callable:
        """Fires every frame while the key is held down."""
        def decorator(func: Callable) -> Callable:
            func._pyunix_input = ("key_held", key)
            _KEY_HELD_HANDLERS.append((func, key))
            return func
        return decorator

    @staticmethod
    def mouse_click(button: str = "left") -> Callable:
        """Fires when a mouse button is clicked. button: 'left'|'middle'|'right'."""
        def decorator(func: Callable) -> Callable:
            func._pyunix_input = ("mouse_click", button)
            _MOUSE_CLICK_HANDLERS.append((func, button))
            return func
        return decorator

    @staticmethod
    def mouse_motion(func: Callable) -> Callable:
        """Fires when the mouse moves. Method receives (pos, rel)."""
        func._pyunix_input = ("mouse_motion", None)
        _MOUSE_MOTION_HANDLERS.append(func)
        return func

    @staticmethod
    def action(action_name: str) -> Callable:
        """Fires on key-down of any key bound to `action_name`."""
        def decorator(func: Callable) -> Callable:
            func._pyunix_input = ("action", action_name)
            _ACTION_HANDLERS.append((func, action_name))
            return func
        return decorator

    # ─── Binding API ───────────────────────────────────────────────────────

    @staticmethod
    def bind_action(action_name: str, *keys: str) -> None:
        """Bind one or more physical keys to a named action."""
        if action_name not in _ACTION_MAP:
            _ACTION_MAP[action_name] = []
        _ACTION_MAP[action_name].extend(k.upper() for k in keys)

    @staticmethod
    def unbind_action(action_name: str) -> None:
        """Remove all key bindings for an action."""
        _ACTION_MAP.pop(action_name, None)

    @staticmethod
    def bind_axis(axis_name: str, positive: str, negative: str) -> None:
        """Bind +1/-1 axis to two keys (e.g. D/A or RIGHT/LEFT)."""
        _AXIS_MAP[axis_name] = (positive.upper(), negative.upper())

    @staticmethod
    def get_bindings(action_name: str) -> List[str]:
        """Return the list of keys bound to an action."""
        return list(_ACTION_MAP.get(action_name, []))

    # ─── Polling API ───────────────────────────────────────────────────────

    @staticmethod
    def is_pressed(key: str) -> bool:
        """True if the key is currently held down (continuous)."""
        if not _HAS_PYGAME:
            return False
        code = _resolve_key(key)
        return bool(code) and code in _held_keys

    @staticmethod
    def is_just_pressed(key: str) -> bool:
        """True only on the exact frame the key was first pressed."""
        if not _HAS_PYGAME:
            return False
        code = _resolve_key(key)
        return code in _just_pressed

    @staticmethod
    def is_just_released(key: str) -> bool:
        """True only on the exact frame the key was released."""
        if not _HAS_PYGAME:
            return False
        code = _resolve_key(key)
        return code in _just_released

    @staticmethod
    def action_pressed(action_name: str) -> bool:
        """True if ANY key bound to the action is currently held."""
        keys = _ACTION_MAP.get(action_name, [])
        return any(_InputAPI.is_pressed(k) for k in keys)

    @staticmethod
    def action_just_pressed(action_name: str) -> bool:
        """True on the frame any bound key is first pressed."""
        keys = _ACTION_MAP.get(action_name, [])
        return any(_InputAPI.is_just_pressed(k) for k in keys)

    @staticmethod
    def action_just_released(action_name: str) -> bool:
        """True on the frame any bound key is released."""
        keys = _ACTION_MAP.get(action_name, [])
        return any(_InputAPI.is_just_released(k) for k in keys)

    # Keep old name for backward compat
    action_held = action_pressed

    @staticmethod
    def get_axis(axis_name: str) -> float:
        """
        Return -1.0, 0.0, or 1.0 for a bound axis.

        Returns 0.0 if the axis is not bound or Pygame is unavailable.
        """
        if not _HAS_PYGAME or axis_name not in _AXIS_MAP:
            return 0.0
        pos_key, neg_key = _AXIS_MAP[axis_name]
        val = 0.0
        if _InputAPI.is_pressed(pos_key):
            val += 1.0
        if _InputAPI.is_pressed(neg_key):
            val -= 1.0
        return val

    @staticmethod
    def get_axis_vector(h_axis: str, v_axis: str) -> Any:
        """
        Return a Vector2 from two axes — useful for movement.

        Usage:
            vel = Input.get_axis_vector("horizontal", "vertical") * 150
        """
        from arkhe.pyunix.math import Vector2
        return Vector2(
            _InputAPI.get_axis(h_axis),
            _InputAPI.get_axis(v_axis),
        )

    # ─── Mouse ─────────────────────────────────────────────────────────────

    @property
    def mouse_position(self) -> Tuple[int, int]:
        """Current mouse position in screen pixels."""
        if _HAS_PYGAME:
            return pygame.mouse.get_pos()
        return (0, 0)

    @property
    def mouse_delta(self) -> Tuple[int, int]:
        """Mouse movement delta since last frame."""
        return _mouse_rel

    @staticmethod
    def mouse_pressed(button: str = "left") -> bool:
        """True if the given mouse button is currently held."""
        if not _HAS_PYGAME:
            return False
        btn_map = {"left": 0, "middle": 1, "right": 2}
        idx = btn_map.get(button, 0)
        return pygame.mouse.get_pressed()[idx]

    @property
    def scroll(self) -> float:
        """Scroll delta for this frame (+ve = up, -ve = down)."""
        return _scroll_delta

    @staticmethod
    def set_cursor_visible(visible: bool) -> None:
        """Show or hide the OS cursor."""
        if _HAS_PYGAME:
            pygame.mouse.set_visible(visible)

    # ─── Gamepad ───────────────────────────────────────────────────────────

    @staticmethod
    def gamepad_axis(joystick_id: int, axis_id: int, dead_zone: float = 0.15) -> float:
        """
        Read a raw joystick axis value.

        Args:
            joystick_id: Joystick index (0 for the first controller).
            axis_id:     Axis index (0=left-x, 1=left-y, 2=right-x, 3=right-y typically).
            dead_zone:   Values smaller than this are returned as 0.0.
        """
        if not _HAS_PYGAME:
            return 0.0
        try:
            joy = pygame.joystick.Joystick(joystick_id)
            val = joy.get_axis(axis_id)
            return 0.0 if abs(val) < dead_zone else val
        except Exception:
            return 0.0

    @staticmethod
    def gamepad_button(joystick_id: int, button_id: int) -> bool:
        """Return True if the specified gamepad button is pressed."""
        if not _HAS_PYGAME:
            return False
        try:
            joy = pygame.joystick.Joystick(joystick_id)
            return joy.get_button(button_id)
        except Exception:
            return False

    @staticmethod
    def gamepad_count() -> int:
        """Return the number of connected joysticks/gamepads."""
        if not _HAS_PYGAME:
            return 0
        return pygame.joystick.get_count()

    # ─── Dispatching (called by runtime) ──────────────────────────────────

    @staticmethod
    def _dispatch_event(event: Any, target: Any) -> None:
        """Route a pygame event to matching decorator-registered handlers."""
        _update_state(event)

        if not _HAS_PYGAME:
            return

        if event.type == pygame.KEYDOWN:
            code = event.key
            for func, key_str in _KEY_DOWN_HANDLERS:
                if code == _resolve_key(key_str):
                    func(target)
            for func, action_name in _ACTION_HANDLERS:
                for k in _ACTION_MAP.get(action_name, []):
                    if code == _resolve_key(k):
                        func(target)
                        break

        elif event.type == pygame.KEYUP:
            code = event.key
            for func, key_str in _KEY_UP_HANDLERS:
                if code == _resolve_key(key_str):
                    func(target)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            btn_map = {1: "left", 2: "middle", 3: "right"}
            btn = btn_map.get(event.button, "")
            for func, b in _MOUSE_CLICK_HANDLERS:
                if b == btn:
                    func(target)

        elif event.type == pygame.MOUSEMOTION:
            for func in _MOUSE_MOTION_HANDLERS:
                func(target, event.pos, event.rel)

    @staticmethod
    def _process_held(target: Any) -> None:
        """Poll continuously-held keys and fire @key_held handlers."""
        if not _HAS_PYGAME:
            return
        for func, key_str in _KEY_HELD_HANDLERS:
            code = _resolve_key(key_str)
            if code and code in _held_keys:
                func(target)


Input = _InputAPI()
