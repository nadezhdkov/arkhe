import asyncio
import inspect
from collections import defaultdict
from typing import Any, Callable, Type


class EventBus:
    """
    Synchronous and asynchronous event bus.
    Supports subscribe/publish patterns and wildcard (any-event) listeners.
    """

    def __init__(self):
        self._listeners: dict[Type, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type, handler: Callable):
        """Register a handler for a specific event type."""
        self._listeners[event_type].append(handler)

    def unsubscribe(self, event_type: Type, handler: Callable):
        self._listeners[event_type] = [
            h for h in self._listeners[event_type] if h != handler
        ]

    async def publish(self, event: Any):
        """Publish an event to all registered listeners (async)."""
        event_type = type(event)
        for handler in self._listeners.get(event_type, []):
            if inspect.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)

    def publish_sync(self, event: Any):
        """Publish an event synchronously (fire-and-forget for async handlers)."""
        event_type = type(event)
        for handler in self._listeners.get(event_type, []):
            if inspect.iscoroutinefunction(handler):
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(handler(event))
                except RuntimeError:
                    asyncio.run(handler(event))
            else:
                handler(event)

    def clear(self):
        self._listeners.clear()
