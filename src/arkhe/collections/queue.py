"""
arkhe.collections.queue
----------------------------
A fluent FIFO queue wrapping ``collections.deque``.

Example::

    from arkhe.collections import Queue

    front = Queue.of(1, 2, 3).enqueue(4).peek()  # 1
"""

from __future__ import annotations

import collections
from typing import Any, Generic, Iterable, Iterator, List, Optional, TypeVar, TYPE_CHECKING

T = TypeVar("T")


class Queue(Generic[T]):
    """
    A First-In-First-Out (FIFO) queue with a fluent, chainable API.

    Backed by ``collections.deque`` for O(1) enqueue and dequeue at both ends.
    """

    __slots__ = ("_data",)

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        """
        Initialize a new Queue.

        Args:
            items (Optional[Iterable[T]]): Seed elements. The first element
                yielded becomes the front of the queue.
        """
        self._data: collections.deque[T] = collections.deque(
            items if items is not None else []
        )

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, *items: T) -> "Queue[T]":
        """Create a Queue from positional arguments."""
        return cls(items)

    @classmethod
    def empty(cls) -> "Queue[T]":
        """Create an empty Queue."""
        return cls()

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def enqueue(self, item: T) -> "Queue[T]":
        """Add *item* to the back of the queue (O(1))."""
        self._data.append(item)
        return self

    def enqueue_all(self, items: Iterable[T]) -> "Queue[T]":
        """Add all *items* to the back in iteration order."""
        self._data.extend(items)
        return self

    def dequeue(self) -> T:
        """
        Remove and return the front element (O(1)).

        Raises:
            IndexError: If the queue is empty.
        """
        if not self._data:
            raise IndexError("dequeue from empty Queue")
        return self._data.popleft()

    def dequeue_or(self, default: T) -> T:
        """Remove and return the front element, or *default* if empty."""
        return self._data.popleft() if self._data else default

    def peek(self) -> Optional[T]:
        """Return the front element without removing it, or ``None`` if empty."""
        return self._data[0] if self._data else None

    def peek_last(self) -> Optional[T]:
        """Return the back element without removing it, or ``None`` if empty."""
        return self._data[-1] if self._data else None

    def clear(self) -> "Queue[T]":
        """Remove all elements."""
        self._data.clear()
        return self

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        return not self._data

    def size(self) -> int:
        return len(self._data)

    # ------------------------------------------------------------------
    # Stream interop
    # ------------------------------------------------------------------

    def stream(self) -> "Stream[T]":
        """Return a :class:`~arkhe.collections.stream.Stream` (front-to-back order)."""
        from arkhe.collections.stream import Stream
        return Stream(list(self._data))

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_list(self) -> List[T]:
        """Return a copy ordered from front to back."""
        return list(self._data)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, item: Any) -> bool:
        return item in self._data

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Queue):
            return list(self._data) == list(other._data)
        return NotImplemented

    def __repr__(self) -> str:
        return f"Queue({list(self._data)!r})"


if TYPE_CHECKING:
    from arkhe.collections.stream import Stream
