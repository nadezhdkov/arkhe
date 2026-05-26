"""
nestifypy.pyunix.events
--------------------
Decoupled event bus for game-wide communication.

This module implements a simple Publisher/Subscriber (Pub/Sub) pattern.
It allows different systems (like UI, physics, and gameplay logic) to communicate
without needing direct references to each other, improving modularity.

Usage:
    @Event.on("player_death")
    def handle_death(data):
        print(f"Player died. Score: {data['score']}")

    Event.emit("player_death", {"score": 100})
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List


class EventBus:
    """
    Central event dispatch system.

    Provides decorators to register listener functions and runtime methods
    to emit events globally across the application.
    """

    def __init__(self) -> None:
        """Initialize the EventBus with an empty listener dictionary."""
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event_name: str) -> Callable:
        """
        Decorator to register a function as a listener for a specific event.

        Args:
            event_name (str): The name of the event to listen for.

        Returns:
            Callable: The decorator function.
        """
        def decorator(func: Callable) -> Callable:
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            self._listeners[event_name].append(func)
            func._pyunix_event = event_name
            return func
        return decorator

    def emit(self, event_name: str, data: Any = None) -> None:
        """
        Dispatch an event to all registered listeners.

        Args:
            event_name (str): The name of the event to emit.
            data (Any, optional): The payload to pass to the listener functions.
                If None, the listeners are called without arguments. Defaults to None.
        """
        for callback in self._listeners.get(event_name, []):
            if data is not None:
                callback(data)
            else:
                callback()

    def remove(self, event_name: str, func: Callable) -> None:
        """
        Remove a specific listener function from an event.

        Args:
            event_name (str): The name of the event.
            func (Callable): The specific function reference to unregister.
        """
        if event_name in self._listeners:
            self._listeners[event_name] = [
                f for f in self._listeners[event_name] if f is not func
            ]

    def clear(self, event_name: str = None) -> None:
        """
        Clear listeners for a specific event, or all events if no name is provided.

        Args:
            event_name (str, optional): The name of the event to clear.
                If None, flushes the entire event bus. Defaults to None.
        """
        if event_name:
            self._listeners.pop(event_name, None)
        else:
            self._listeners.clear()

    def listeners(self, event_name: str) -> List[Callable]:
        """
        Return a list of all currently registered listeners for an event.

        Args:
            event_name (str): The name of the event to query.

        Returns:
            List[Callable]: A list of functions registered to the event.
        """
        return list(self._listeners.get(event_name, []))


# Global singleton
Event = EventBus()