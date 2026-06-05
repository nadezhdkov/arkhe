"""
arkhe.pyunix.animation
--------------------------
Professional sprite-sheet animation system with a built-in state machine.

Provides frame-based animations loaded from sprite sheets, with support for
events on specific frames, transitions between animation states, easing on
playback speed, and callbacks on loop/completion.

Usage:
    # Build clips from a spritesheet
    anim = Animator(entity)
    anim.add_clip("idle",   Assets.spritesheet("hero.png", (32, 32))[0:4],   fps=8)
    anim.add_clip("run",    Assets.spritesheet("hero.png", (32, 32))[4:12],  fps=16)
    anim.add_clip("jump",   Assets.spritesheet("hero.png", (32, 32))[12:16], fps=12, loop=False)

    # Automatic transitions
    anim.add_transition("idle", "run",  condition=lambda: speed > 10)
    anim.add_transition("run",  "idle", condition=lambda: speed <= 10)

    # Play
    anim.play("idle")

    # Inside update:
    anim.update(dt)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Animation Clip
# ---------------------------------------------------------------------------

@dataclass
class AnimationClip:
    """
    A named sequence of frames (pygame Surfaces) with playback settings.

    Attributes:
        name:         Unique clip identifier.
        frames:       Ordered list of pygame Surface frames.
        fps:          Playback speed in frames per second.
        loop:         Whether to loop the clip. Defaults to True.
        ping_pong:    Play forward then backward. Defaults to False.
        frame_events: Map of frame index → callback fired when that frame is shown.
        on_complete:  Callback fired once when a non-looping clip finishes.
        on_loop:      Callback fired each time a looping clip restarts.
    """
    name: str
    frames: List[Any]
    fps: float = 12.0
    loop: bool = True
    ping_pong: bool = False
    frame_events: Dict[int, Callable] = field(default_factory=dict)
    on_complete: Optional[Callable] = None
    on_loop: Optional[Callable] = None

    @property
    def frame_duration(self) -> float:
        """Seconds per frame."""
        return 1.0 / max(self.fps, 0.001)

    @property
    def total_frames(self) -> int:
        return len(self.frames)


# ---------------------------------------------------------------------------
# Animator
# ---------------------------------------------------------------------------

@dataclass
class _Transition:
    from_clip: str
    to_clip: str
    condition: Callable[[], bool]
    priority: int = 0          # Higher wins when multiple conditions fire


class Animator:
    """
    Per-entity animation controller.

    Owns a set of AnimationClips, the currently playing state, and an
    optional set of automatic transitions that drive a state machine.

    Designed to be attached to an Entity and ticked each frame via update(dt).
    """

    def __init__(self, entity: Any) -> None:
        """
        Args:
            entity: The Entity this animator belongs to (used to set entity.image).
        """
        self._entity = entity
        self._clips: Dict[str, AnimationClip] = {}
        self._transitions: List[_Transition] = []

        # Playback state
        self._current_clip: Optional[AnimationClip] = None
        self._frame_index: int = 0
        self._elapsed: float = 0.0
        self._playing: bool = False
        self._speed: float = 1.0          # Global speed multiplier
        self._direction: int = 1           # +1 forward / -1 backward (ping-pong)
        self._fired_events: set = set()   # Frame indices already fired this loop

    # ── Clip Management ──────────────────────

    def add_clip(
        self,
        name: str,
        frames: List[Any],
        fps: float = 12.0,
        loop: bool = True,
        ping_pong: bool = False,
        frame_events: Dict[int, Callable] = None,
        on_complete: Optional[Callable] = None,
        on_loop: Optional[Callable] = None,
    ) -> "Animator":
        """
        Register an animation clip.

        Returns self for chaining:
            anim.add_clip(...).add_clip(...).play("idle")
        """
        self._clips[name] = AnimationClip(
            name=name,
            frames=frames,
            fps=fps,
            loop=loop,
            ping_pong=ping_pong,
            frame_events=frame_events or {},
            on_complete=on_complete,
            on_loop=on_loop,
        )
        return self

    def remove_clip(self, name: str) -> None:
        self._clips.pop(name, None)

    def has_clip(self, name: str) -> bool:
        return name in self._clips

    # ── Transitions ──────────────────────────

    def add_transition(
        self,
        from_clip: str,
        to_clip: str,
        condition: Callable[[], bool],
        priority: int = 0,
    ) -> "Animator":
        """
        Add an automatic transition from one clip to another.

        Transitions are evaluated every frame; the first truthy condition
        (or the highest-priority one) triggers a clip switch.

        Returns self for chaining.
        """
        self._transitions.append(_Transition(from_clip, to_clip, condition, priority))
        return self

    # ── Playback Control ─────────────────────

    def play(self, name: str, reset: bool = False) -> None:
        """
        Switch to and start playing the named clip.

        Args:
            name:  Clip identifier registered via add_clip.
            reset: If the clip is already playing, force it to restart from frame 0.
        """
        if name not in self._clips:
            return
        clip = self._clips[name]
        if self._current_clip is clip and not reset:
            return
        self._current_clip = clip
        self._frame_index  = 0
        self._elapsed      = 0.0
        self._direction    = 1
        self._fired_events = set()
        self._playing      = True
        self._apply_frame()

    def stop(self) -> None:
        """Pause playback at the current frame."""
        self._playing = False

    def resume(self) -> None:
        """Resume paused playback."""
        self._playing = True

    def set_speed(self, speed: float) -> None:
        """
        Set the global playback speed multiplier.

        1.0 = normal, 2.0 = double speed, 0.5 = half speed, -1.0 = reverse.
        """
        self._speed = speed

    def set_frame(self, index: int) -> None:
        """Jump to a specific frame index (clamped to clip length)."""
        if self._current_clip:
            self._frame_index = max(0, min(index, self._current_clip.total_frames - 1))
            self._apply_frame()

    @property
    def current_clip_name(self) -> Optional[str]:
        return self._current_clip.name if self._current_clip else None

    @property
    def current_frame(self) -> int:
        return self._frame_index

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def normalized_time(self) -> float:
        """Current position in clip as 0.0–1.0."""
        if not self._current_clip or self._current_clip.total_frames == 0:
            return 0.0
        return self._frame_index / max(self._current_clip.total_frames - 1, 1)

    # ── Update ───────────────────────────────

    def update(self, dt: float) -> None:
        """
        Advance the animation by `dt` seconds.
        Must be called every frame (handled automatically if attached to Entity).
        """
        if not self._playing or not self._current_clip:
            return

        clip = self._current_clip

        # --- Evaluate transitions first ---
        candidates = [
            t for t in self._transitions
            if t.from_clip == clip.name and t.condition()
        ]
        if candidates:
            best = max(candidates, key=lambda t: t.priority)
            self.play(best.to_clip)
            return

        # --- Advance time ---
        effective_dt = dt * abs(self._speed)
        self._elapsed += effective_dt

        # --- Advance frames ---
        while self._elapsed >= clip.frame_duration:
            self._elapsed -= clip.frame_duration
            self._advance_frame(clip)

        self._apply_frame()

    def _advance_frame(self, clip: AnimationClip) -> None:
        next_index = self._frame_index + self._direction

        if clip.ping_pong:
            if next_index >= clip.total_frames:
                self._direction = -1
                next_index = clip.total_frames - 2
            elif next_index < 0:
                self._direction = 1
                next_index = 1
        else:
            if next_index >= clip.total_frames:
                if clip.loop:
                    next_index = 0
                    self._fired_events.clear()
                    if clip.on_loop:
                        clip.on_loop()
                else:
                    self._playing = False
                    next_index = clip.total_frames - 1
                    if clip.on_complete:
                        clip.on_complete()
            elif next_index < 0:
                next_index = 0

        self._frame_index = next_index

        # Fire frame events
        if next_index not in self._fired_events and next_index in clip.frame_events:
            self._fired_events.add(next_index)
            clip.frame_events[next_index]()

    def _apply_frame(self) -> None:
        """Write the current frame surface onto the entity's image."""
        if self._current_clip and self._entity is not None:
            frames = self._current_clip.frames
            if frames and 0 <= self._frame_index < len(frames):
                self._entity.image = frames[self._frame_index]

    # ── Debug ─────────────────────────────────

    def __repr__(self) -> str:
        return (f"Animator(clip={self.current_clip_name!r}, "
                f"frame={self._frame_index}, playing={self._playing})")
