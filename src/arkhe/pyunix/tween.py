"""
arkhe.pyunix.tween
----------------------
Declarative tween (interpolation) engine — animate any numeric property
on any object over time with easing functions, chaining, and callbacks.

Inspired by DOTween (Unity) and Godot's Tween node.

Usage:
    # Tween a single property
    Tween.to(player.transform, "x", target=300, duration=1.0, ease=Ease.OUT_CUBIC)

    # Chain tweens
    (Tween.to(box, "x", 200, 0.5)
          .then(Tween.to(box, "y", 300, 0.5))
          .on_complete(lambda: print("done!")))

    # Animate a Vector2
    Tween.move(entity, target=Vector2(400, 300), duration=1.0)

    # Tween a Color
    Tween.color(sprite, "tint", Color.RED, duration=0.5)

    # Shake utility
    Tween.shake(entity, intensity=8, duration=0.4)

    # Update all tweens each frame (handled automatically by Game loop)
    TweenManager.update(dt)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional


# ---------------------------------------------------------------------------
# Easing Functions
# ---------------------------------------------------------------------------

class Ease:
    """Collection of easing functions. All take t in [0, 1] and return [0, 1]."""

    @staticmethod
    def LINEAR(t: float) -> float:
        return t

    @staticmethod
    def IN_QUAD(t: float) -> float:
        return t * t

    @staticmethod
    def OUT_QUAD(t: float) -> float:
        return t * (2 - t)

    @staticmethod
    def IN_OUT_QUAD(t: float) -> float:
        return 2*t*t if t < 0.5 else -1 + (4 - 2*t)*t

    @staticmethod
    def IN_CUBIC(t: float) -> float:
        return t * t * t

    @staticmethod
    def OUT_CUBIC(t: float) -> float:
        p = t - 1
        return p * p * p + 1

    @staticmethod
    def IN_OUT_CUBIC(t: float) -> float:
        return 4*t*t*t if t < 0.5 else (t-1)*(2*t-2)*(2*t-2)+1

    @staticmethod
    def IN_QUART(t: float) -> float:
        return t * t * t * t

    @staticmethod
    def OUT_QUART(t: float) -> float:
        p = t - 1
        return 1 - p * p * p * p

    @staticmethod
    def IN_OUT_QUART(t: float) -> float:
        if t < 0.5:
            return 8 * t * t * t * t
        p = t - 1
        return 1 - 8 * p * p * p * p

    @staticmethod
    def IN_SINE(t: float) -> float:
        return 1 - math.cos(t * math.pi / 2)

    @staticmethod
    def OUT_SINE(t: float) -> float:
        return math.sin(t * math.pi / 2)

    @staticmethod
    def IN_OUT_SINE(t: float) -> float:
        return -(math.cos(math.pi * t) - 1) / 2

    @staticmethod
    def IN_EXPO(t: float) -> float:
        return 0 if t == 0 else math.pow(2, 10 * t - 10)

    @staticmethod
    def OUT_EXPO(t: float) -> float:
        return 1 if t == 1 else 1 - math.pow(2, -10 * t)

    @staticmethod
    def IN_OUT_EXPO(t: float) -> float:
        if t == 0: return 0
        if t == 1: return 1
        if t < 0.5: return math.pow(2, 20*t - 10) / 2
        return (2 - math.pow(2, -20*t + 10)) / 2

    @staticmethod
    def IN_ELASTIC(t: float) -> float:
        c4 = (2 * math.pi) / 3
        if t == 0: return 0
        if t == 1: return 1
        return -math.pow(2, 10*t - 10) * math.sin((t*10 - 10.75) * c4)

    @staticmethod
    def OUT_ELASTIC(t: float) -> float:
        c4 = (2 * math.pi) / 3
        if t == 0: return 0
        if t == 1: return 1
        return math.pow(2, -10*t) * math.sin((t*10 - 0.75) * c4) + 1

    @staticmethod
    def OUT_BOUNCE(t: float) -> float:
        n1, d1 = 7.5625, 2.75
        if t < 1/d1:
            return n1 * t * t
        elif t < 2/d1:
            t -= 1.5/d1
            return n1*t*t + 0.75
        elif t < 2.5/d1:
            t -= 2.25/d1
            return n1*t*t + 0.9375
        else:
            t -= 2.625/d1
            return n1*t*t + 0.984375

    @staticmethod
    def IN_BOUNCE(t: float) -> float:
        return 1 - Ease.OUT_BOUNCE(1 - t)

    @staticmethod
    def IN_OUT_BOUNCE(t: float) -> float:
        if t < 0.5:
            return (1 - Ease.OUT_BOUNCE(1 - 2*t)) / 2
        return (1 + Ease.OUT_BOUNCE(2*t - 1)) / 2

    @staticmethod
    def OUT_BACK(t: float) -> float:
        c1, c3 = 1.70158, 2.70158
        return 1 + c3 * math.pow(t - 1, 3) + c1 * math.pow(t - 1, 2)

    @staticmethod
    def IN_BACK(t: float) -> float:
        c1, c3 = 1.70158, 2.70158
        return c3*t*t*t - c1*t*t

    @staticmethod
    def IN_OUT_BACK(t: float) -> float:
        c2 = 1.70158 * 1.525
        if t < 0.5:
            return (math.pow(2*t, 2) * ((c2+1)*2*t - c2)) / 2
        return (math.pow(2*t-2, 2) * ((c2+1)*(2*t-2) + c2) + 2) / 2


# ---------------------------------------------------------------------------
# TweenEntry
# ---------------------------------------------------------------------------

class TweenEntry:
    """
    A single tween job — animates one property from start to end over `duration`
    seconds using an easing function.
    """

    def __init__(
        self,
        target: Any,
        attr: str,
        end_value: Any,
        duration: float,
        ease: Callable[[float], float],
        delay: float,
        on_complete: Optional[Callable],
    ) -> None:
        self._target = target
        self._attr = attr
        self._start_value = None  # captured on first update
        self._end_value = end_value
        self._duration = max(duration, 0.0001)
        self._ease = ease
        self._delay = delay
        self._elapsed = 0.0
        self._on_complete = on_complete
        self._done = False
        self._next: Optional["TweenEntry"] = None    # chain
        self._started = False

    # ── Chaining ─────────────────────────────

    def then(self, next_tween: "TweenEntry") -> "TweenEntry":
        """Queue `next_tween` to start when this one completes."""
        self._next = next_tween
        return next_tween

    def on_complete(self, callback: Callable) -> "TweenEntry":
        """Register a completion callback."""
        self._on_complete = callback
        return self

    # ── Internal ─────────────────────────────

    def _lerp_value(self, a: Any, b: Any, t: float) -> Any:
        """Interpolate between two values of any numeric / Vector2 / Color type."""
        try:
            from arkhe.pyunix.math import Vector2, Color
            if isinstance(a, Vector2):
                return a.lerp(b, t)
            if isinstance(a, Color):
                return a.lerp(b, t)
        except ImportError:
            pass
        return a + (b - a) * t

    def update(self, dt: float) -> bool:
        """
        Advance the tween.

        Returns True when the tween is complete.
        """
        if self._done:
            return True

        # Handle delay
        if self._delay > 0:
            self._delay -= dt
            return False

        # Capture start on first actual tick
        if not self._started:
            self._started = True
            self._start_value = getattr(self._target, self._attr, None)
            if self._start_value is None:
                self._done = True
                return True

        self._elapsed += dt
        t = min(self._elapsed / self._duration, 1.0)
        eased_t = self._ease(t)

        new_val = self._lerp_value(self._start_value, self._end_value, eased_t)
        setattr(self._target, self._attr, new_val)

        if t >= 1.0:
            self._done = True
            if self._on_complete:
                self._on_complete()
            # Start chained tween
            if self._next is not None:
                _TweenManager._active.append(self._next)
            return True

        return False


# ---------------------------------------------------------------------------
# TweenManager (global)
# ---------------------------------------------------------------------------

class _TweenManager:
    _active: List[TweenEntry] = []

    @classmethod
    def update(cls, dt: float) -> None:
        """Tick all running tweens. Called by the engine loop automatically."""
        cls._active = [t for t in cls._active if not t.update(dt)]

    @classmethod
    def kill_all(cls, target: Any = None) -> None:
        """Stop all tweens, or only tweens on `target` if provided."""
        if target is None:
            cls._active.clear()
        else:
            cls._active = [t for t in cls._active if t._target is not target]

    @classmethod
    def _add(cls, entry: TweenEntry) -> TweenEntry:
        cls._active.append(entry)
        return entry


# ---------------------------------------------------------------------------
# Tween public API
# ---------------------------------------------------------------------------

class _TweenAPI:
    """
    Static factory methods for creating and starting tweens.
    Keeps user-facing syntax clean: Tween.to(...), Tween.move(...), etc.
    """

    @staticmethod
    def to(
        target: Any,
        attr: str,
        end_value: Any,
        duration: float,
        ease: Callable[[float], float] = Ease.LINEAR,
        delay: float = 0.0,
        on_complete: Optional[Callable] = None,
    ) -> TweenEntry:
        """
        Animate any numeric attribute on `target` to `end_value` over `duration` seconds.

        Args:
            target:     The object whose attribute will be animated.
            attr:       The attribute name as a string (e.g., "x", "alpha").
            end_value:  The target value (same type as the current attribute).
            duration:   Length of the animation in seconds.
            ease:       Easing function from the Ease class. Defaults to Ease.LINEAR.
            delay:      Seconds to wait before starting. Defaults to 0.
            on_complete: Optional callback fired on completion.

        Returns:
            TweenEntry: The created tween (for chaining).
        """
        entry = TweenEntry(target, attr, end_value, duration, ease, delay, on_complete)
        return _TweenManager._add(entry)

    @staticmethod
    def move(
        entity: Any,
        target: Any,           # Vector2
        duration: float,
        ease: Callable = Ease.OUT_CUBIC,
        delay: float = 0.0,
        on_complete: Optional[Callable] = None,
    ) -> TweenEntry:
        """Animate an entity's transform.position to `target` (Vector2)."""
        return _TweenAPI.to(entity.transform, "local_position", target, duration, ease, delay, on_complete)

    @staticmethod
    def scale_to(
        entity: Any,
        target: Any,           # Vector2
        duration: float,
        ease: Callable = Ease.OUT_BACK,
        delay: float = 0.0,
    ) -> TweenEntry:
        """Animate an entity's transform.scale to `target` (Vector2)."""
        return _TweenAPI.to(entity.transform, "local_scale", target, duration, ease, delay)

    @staticmethod
    def rotate_to(
        entity: Any,
        target_degrees: float,
        duration: float,
        ease: Callable = Ease.OUT_CUBIC,
        delay: float = 0.0,
    ) -> TweenEntry:
        """Animate an entity's rotation to `target_degrees`."""
        return _TweenAPI.to(entity.transform, "local_rotation", target_degrees, duration, ease, delay)

    @staticmethod
    def fade(
        entity: Any,
        end_alpha: float,
        duration: float,
        ease: Callable = Ease.IN_OUT_SINE,
        delay: float = 0.0,
    ) -> TweenEntry:
        """Animate an entity's `alpha` attribute (0–255) to `end_alpha`."""
        return _TweenAPI.to(entity, "alpha", end_alpha, duration, ease, delay)

    @staticmethod
    def color(
        entity: Any,
        attr: str,
        end_color: Any,        # Color
        duration: float,
        ease: Callable = Ease.LINEAR,
        delay: float = 0.0,
    ) -> TweenEntry:
        """Animate a Color attribute on `entity`."""
        return _TweenAPI.to(entity, attr, end_color, duration, ease, delay)

    @staticmethod
    def sequence(*tweens: TweenEntry) -> TweenEntry:
        """
        Chain multiple TweenEntry objects to execute one after another.

        Usage:
            Tween.sequence(
                Tween.to(obj, "x", 200, 0.5),
                Tween.to(obj, "y", 300, 0.5),
            )
        Note: tweens should NOT be added to the manager yet (pass them before calling Tween.to
        or create them manually). Prefer Tween.to(...).then(Tween.to(...)) for simple chains.
        """
        for i in range(len(tweens) - 1):
            tweens[i]._next = tweens[i + 1]
        return tweens[0]

    @staticmethod
    def kill(target: Any) -> None:
        """Stop all active tweens targeting `target`."""
        _TweenManager.kill_all(target)

    @staticmethod
    def kill_all() -> None:
        """Stop every active tween."""
        _TweenManager.kill_all()


Tween = _TweenAPI()
TweenManager = _TweenManager
