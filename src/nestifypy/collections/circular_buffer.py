"""
nestifypy.collections.circular_buffer
---------------------------------------
A fixed-capacity circular buffer (ring buffer).

When the buffer is full, adding a new element automatically evicts the
oldest one, keeping memory usage constant and bounded.

Backed by ``collections.deque(maxlen=capacity)`` for O(1) add and O(1)
eviction.

Example::

    from nestifypy.collections import CircularBuffer

    logs = CircularBuffer(3)
    logs.add("A").add("B").add("C")
    list(logs)   # ["A", "B", "C"]

    logs.add("D")
    list(logs)   # ["B", "C", "D"]  — "A" was evicted

Streaming the last N items::

    metrics = CircularBuffer(100)
    # ... fill with readings ...
    avg = metrics.stream().map(lambda m: m.value).reduce(lambda a, b: a + b, 0) / metrics.size()
"""

from __future__ import annotations

import collections
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    TypeVar,
    TYPE_CHECKING,
)

T = TypeVar("T")
U = TypeVar("U")


class CircularBuffer(Generic[T]):
    """
    A fixed-capacity FIFO buffer that overwrites the oldest elements when full.

    All mutation methods return ``self`` for chaining.
    """

    __slots__ = ("_data", "_capacity")

    def __init__(self, capacity: int) -> None:
        """
        Initialize a new CircularBuffer.

        Args:
            capacity (int): Maximum number of elements. Must be >= 1.

        Raises:
            ValueError: If *capacity* is less than 1.
        """
        if capacity < 1:
            raise ValueError(f"CircularBuffer capacity must be >= 1, got {capacity}")
        self._capacity = capacity
        self._data: collections.deque[T] = collections.deque(maxlen=capacity)

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, capacity: int, *items: T) -> "CircularBuffer[T]":
        """
        Create a CircularBuffer with *capacity* pre-filled with *items*.

        Args:
            capacity (int): Maximum buffer size.
            *items (T): Initial elements (only the last *capacity* are kept).

        Returns:
            CircularBuffer[T]: New buffer.
        """
        buf: CircularBuffer[T] = cls(capacity)
        buf.add_all(items)
        return buf

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, item: T) -> "CircularBuffer[T]":
        """
        Add *item* to the buffer.

        If the buffer is at capacity the oldest element is silently evicted.

        Args:
            item (T): Element to add.

        Returns:
            CircularBuffer[T]: self
        """
        self._data.append(item)
        return self

    def add_all(self, items: Iterable[T]) -> "CircularBuffer[T]":
        """
        Add all *items* to the buffer, evicting oldest as needed.

        Args:
            items (Iterable[T]): Elements to add.

        Returns:
            CircularBuffer[T]: self
        """
        for item in items:
            self._data.append(item)
        return self

    def clear(self) -> "CircularBuffer[T]":
        """Remove all elements (capacity is preserved)."""
        self._data.clear()
        return self

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def peek_oldest(self) -> Optional[T]:
        """
        Return the oldest element without removing it, or ``None`` if empty.

        Returns:
            Optional[T]: Oldest element or None.
        """
        return self._data[0] if self._data else None

    def peek_newest(self) -> Optional[T]:
        """
        Return the most recently added element without removing it, or ``None`` if empty.

        Returns:
            Optional[T]: Newest element or None.
        """
        return self._data[-1] if self._data else None

    def is_empty(self) -> bool:
        """Return ``True`` if the buffer holds no elements."""
        return not self._data

    def is_full(self) -> bool:
        """Return ``True`` if the buffer has reached its capacity."""
        return len(self._data) == self._capacity

    def size(self) -> int:
        """Return the number of elements currently held."""
        return len(self._data)

    @property
    def capacity(self) -> int:
        """The maximum number of elements this buffer can hold."""
        return self._capacity

    # ------------------------------------------------------------------
    # Transformation
    # ------------------------------------------------------------------

    def map(self, transform: Callable[[T], U]) -> "CircularBuffer[U]":
        """
        Return a new CircularBuffer (same capacity) with *transform* applied to each element.

        Args:
            transform (Callable[[T], U]): Mapping function.

        Returns:
            CircularBuffer[U]: Transformed buffer.
        """
        result: CircularBuffer[U] = CircularBuffer(self._capacity)
        result.add_all(transform(item) for item in self._data)
        return result

    def filter(self, predicate: Callable[[T], bool]) -> "CircularBuffer[T]":
        """
        Return a new CircularBuffer (same capacity) with only matching elements.

        Args:
            predicate (Callable[[T], bool]): Test function.

        Returns:
            CircularBuffer[T]: Filtered buffer.
        """
        result: CircularBuffer[T] = CircularBuffer(self._capacity)
        result.add_all(item for item in self._data if predicate(item))
        return result

    def for_each(self, action: Callable[[T], None]) -> "CircularBuffer[T]":
        """
        Execute *action* for each element (oldest to newest).

        Args:
            action (Callable[[T], None]): Side-effecting function.

        Returns:
            CircularBuffer[T]: self
        """
        for item in self._data:
            action(item)
        return self

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_list(self) -> List[T]:
        """Return elements as a list (oldest first)."""
        return list(self._data)

    # ------------------------------------------------------------------
    # Stream interop
    # ------------------------------------------------------------------

    def stream(self) -> "Stream[T]":
        """Return a Stream over the buffer's elements (oldest first)."""
        from nestifypy.collections.stream import Stream
        return Stream(list(self._data))

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
        if isinstance(other, CircularBuffer):
            return self._capacity == other._capacity and list(self._data) == list(other._data)
        return NotImplemented

    def __repr__(self) -> str:
        return f"CircularBuffer(capacity={self._capacity}, data={list(self._data)!r})"


if TYPE_CHECKING:
    from nestifypy.collections.stream import Stream
