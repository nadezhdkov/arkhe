"""
nestifypy.pyunix.timer
-------------------
Game-aware timer system integrated into the engine loop.

This module provides a robust, frame-rate independent timer system.
Because it relies on the game loop's delta time (`dt`) rather than
system time, timers will correctly pause if the game loop pauses.

Usage:
    Timer.after(2.0, lambda: print("Boom!"))
    Timer.every(1.0, lambda: print("Tick"))
"""

from __future__ import annotations

from typing import Callable, List, Optional


class _TimerEntry:
    """
    Internal timer representation.

    Stores the state of an individual timer, including its delay,
    callback function, and whether it should repeat automatically.
    """

    __slots__ = ("delay", "callback", "repeat", "elapsed", "active")

    def __init__(self, delay: float, callback: Callable, repeat: bool) -> None:
        """
        Initialize a new timer entry.

        Args:
            delay (float): The time in seconds to wait before firing.
            callback (Callable): The function to execute when the timer fires.
            repeat (bool): If True, the timer resets and fires repeatedly.
                           If False, it fires once and deactivates.
        """
        self.delay = delay
        self.callback = callback
        self.repeat = repeat
        self.elapsed = 0.0
        self.active = True

    def tick(self, dt: float) -> bool:
        """
        Advance the timer by the given delta time.

        Args:
            dt (float): The time elapsed since the last frame, in seconds.

        Returns:
            bool: True if the timer fired during this tick, False otherwise.
        """
        if not self.active:
            return False

        self.elapsed += dt

        if self.elapsed >= self.delay:
            self.callback()
            if self.repeat:
                # Deduct delay to maintain accurate intervals over time
                self.elapsed -= self.delay
            else:
                self.active = False
            return True

        return False


class TimerManager:
    """
    Manages all game timers.

    This manager is automatically ticked by the internal Pyunix engine loop.
    It handles registering, updating, and cleaning up both one-off and
    repeating timers.
    """

    def __init__(self) -> None:
        """Initialize the TimerManager with an empty list of timers."""
        self._timers: List[_TimerEntry] = []

    def after(self, seconds: float, callback: Callable) -> _TimerEntry:
        """
        Fire a callback once after a specified delay.

        Args:
            seconds (float): The delay in seconds before the callback is executed.
            callback (Callable): The function to execute.

        Returns:
            _TimerEntry: The created timer instance, which can be used to cancel it later.
        """
        entry = _TimerEntry(seconds, callback, repeat=False)
        self._timers.append(entry)
        return entry

    def every(self, seconds: float, callback: Callable) -> _TimerEntry:
        """
        Fire a callback repeatedly at a specified interval.

        Args:
            seconds (float): The interval in seconds between each execution.
            callback (Callable): The function to execute.

        Returns:
            _TimerEntry: The created timer instance, which can be used to cancel it later.
        """
        entry = _TimerEntry(seconds, callback, repeat=True)
        self._timers.append(entry)
        return entry

    def cancel(self, entry: _TimerEntry) -> None:
        """
        Cancel an active timer, preventing its callback from firing.

        Args:
            entry (_TimerEntry): The timer instance to cancel.
        """
        entry.active = False

    def tick(self, dt: float) -> None:
        """
        Advance all active timers by `dt` seconds.

        Note:
            This method is called automatically by the `_GameRuntime` loop.
            Inactive (completed or canceled) timers are garbage collected here.

        Args:
            dt (float): The time elapsed since the last frame, in seconds.
        """
        # Filter out inactive timers (garbage collection)
        self._timers = [t for t in self._timers if t.active]
        for timer in self._timers:
            timer.tick(dt)

    def clear(self) -> None:
        """
        Cancel and remove all active timers from the manager.
        """
        self._timers.clear()


# Global singleton
Timer = TimerManager()