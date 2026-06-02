"""
nestifypy.collections.priority_queue
--------------------------------------
A priority queue backed by Python's ``heapq`` module.

Elements are dequeued in ascending priority order by default
(lowest number = highest priority, consistent with min-heap semantics).
Pass ``reverse=True`` to use max-heap semantics (highest number first).

Example::

    from nestifypy.collections import PriorityQueue

    tasks = PriorityQueue()
    tasks.add("Low priority task",  priority=10)
    tasks.add("High priority task", priority=1)
    tasks.add("Medium task",        priority=5)

    tasks.poll()   # "High priority task"
    tasks.poll()   # "Medium task"
    tasks.peek()   # "Low priority task"  (not removed)

With custom key::

    jobs = PriorityQueue(key=lambda j: j["urgency"])
    jobs.add({"name": "Deploy", "urgency": 1})
    jobs.add({"name": "Docs",   "urgency": 9})
    jobs.poll()    # {"name": "Deploy", "urgency": 1}
"""

from __future__ import annotations

import heapq
import itertools
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
    TYPE_CHECKING,
)

T = TypeVar("T")

# Tie-breaking counter ensures FIFO ordering for equal-priority entries
# and prevents comparison errors on non-orderable element types.
_COUNTER = itertools.count()


class PriorityQueue(Generic[T]):
    """
    A min-heap priority queue with a fluent API.

    Elements with *lower* priority numbers are dequeued first.
    Use ``reverse=True`` to flip to max-priority-first ordering.

    All mutation methods return ``self`` for chaining.
    """

    __slots__ = ("_heap", "_key", "_reverse", "_size")

    def __init__(
        self,
        key: Optional[Callable[[T], Any]] = None,
        reverse: bool = False,
    ) -> None:
        """
        Initialize a new PriorityQueue.

        Args:
            key (Callable[[T], Any] | None): Optional function to extract a
                priority value from each element. When provided, ``add``
                does not require an explicit ``priority`` argument.
            reverse (bool): If ``True``, higher priority numbers are dequeued
                first (max-heap). Defaults to ``False`` (min-heap).
        """
        self._heap: List[Tuple[Any, int, T]] = []  # (priority, seq, item)
        self._key = key
        self._reverse = reverse
        self._size = 0

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, *items: T, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> "PriorityQueue[T]":
        """
        Create a PriorityQueue from positional arguments.

        Requires *key* to be set (or all items to have a natural ordering used
        as priority). Alternatively use :meth:`add` with explicit priorities.

        Args:
            *items (T): Elements to enqueue. Priority derived from *key*.
            key: Priority extractor.
            reverse: Max-heap mode.

        Returns:
            PriorityQueue[T]: New queue.
        """
        pq: PriorityQueue[T] = cls(key=key, reverse=reverse)
        for item in items:
            pq.add(item)
        return pq

    @classmethod
    def empty(cls) -> "PriorityQueue[T]":
        """Create an empty PriorityQueue."""
        return cls()

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, item: T, *, priority: Optional[Any] = None) -> "PriorityQueue[T]":
        """
        Add *item* to the queue.

        Priority resolution order:
        1. Explicit ``priority`` keyword argument.
        2. The ``key`` function supplied at construction time.
        3. The item itself (must be comparable).

        Args:
            item (T): The element to enqueue.
            priority: Explicit priority value (optional).

        Returns:
            PriorityQueue[T]: self

        Raises:
            ValueError: If no priority can be determined.
        """
        if priority is not None:
            prio = priority
        elif self._key is not None:
            prio = self._key(item)
        else:
            prio = item  # assume item is self-orderable

        # Negate for max-heap behaviour
        effective = -prio if self._reverse else prio
        seq = next(_COUNTER)
        heapq.heappush(self._heap, (effective, seq, item))
        self._size += 1
        return self

    def add_all(self, items: Iterable[T], *, priorities: Optional[Iterable[Any]] = None) -> "PriorityQueue[T]":
        """
        Add multiple items.

        Args:
            items (Iterable[T]): Elements to add.
            priorities (Iterable[Any] | None): Parallel iterable of priorities.
                If omitted, priority is derived from *key* or the item itself.

        Returns:
            PriorityQueue[T]: self
        """
        if priorities is not None:
            for item, p in zip(items, priorities):
                self.add(item, priority=p)
        else:
            for item in items:
                self.add(item)
        return self

    def poll(self) -> T:
        """
        Remove and return the highest-priority element.

        Returns:
            T: The top element.

        Raises:
            IndexError: If the queue is empty.
        """
        if not self._heap:
            raise IndexError("poll from empty PriorityQueue")
        _, _, item = heapq.heappop(self._heap)
        self._size -= 1
        return item

    def poll_or(self, default: T) -> T:
        """Remove and return the top element, or *default* if empty."""
        if not self._heap:
            return default
        return self.poll()

    def clear(self) -> "PriorityQueue[T]":
        """Remove all elements."""
        self._heap.clear()
        self._size = 0
        return self

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def peek(self) -> Optional[T]:
        """
        Return the highest-priority element without removing it.

        Returns:
            Optional[T]: Top element or ``None`` if empty.
        """
        if not self._heap:
            return None
        return self._heap[0][2]

    def is_empty(self) -> bool:
        """Return ``True`` if the queue has no elements."""
        return self._size == 0

    def size(self) -> int:
        """Return the number of elements in the queue."""
        return self._size

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_sorted_list(self) -> List[T]:
        """
        Return all elements as a list in priority order (non-destructive).

        Returns:
            List[T]: Elements sorted by priority.
        """
        return [item for _, _, item in sorted(self._heap)]

    def to_list(self) -> List[T]:
        """
        Return all elements as a list in *heap* (storage) order.
        Use :meth:`to_sorted_list` for priority order.

        Returns:
            List[T]: Elements in heap storage order.
        """
        return [item for _, _, item in self._heap]

    # ------------------------------------------------------------------
    # Stream interop
    # ------------------------------------------------------------------

    def stream(self) -> "Stream[T]":
        """Return a Stream over elements in priority order (non-destructive)."""
        from nestifypy.collections.stream import Stream
        return Stream(self.to_sorted_list())

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[T]:
        """Iterate in heap storage order (not priority order)."""
        return (item for _, _, item in self._heap)

    def __len__(self) -> int:
        return self._size

    def __contains__(self, item: Any) -> bool:
        return any(el == item for _, _, el in self._heap)

    def __bool__(self) -> bool:
        return self._size > 0

    def __repr__(self) -> str:
        top = self.peek()
        return f"PriorityQueue(size={self._size}, peek={top!r})"


if TYPE_CHECKING:
    from nestifypy.collections.stream import Stream
