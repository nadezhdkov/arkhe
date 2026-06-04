"""
arkhe.collections.stack
----------------------------
A fluent LIFO stack wrapping Python's ``list``.

Example::

    from arkhe.collections import Stack

    top = Stack.of(1, 2, 3).push(4).peek()  # 4
"""

from __future__ import annotations

from typing import Any, Generic, Iterable, Iterator, List, Optional, TypeVar, TYPE_CHECKING

T = TypeVar("T")


class Stack(Generic[T]):
    """
    A Last-In-First-Out (LIFO) stack with a fluent, chainable API.

    The end of the underlying list represents the top of the stack,
    giving O(1) push/pop/peek.
    """

    __slots__ = ("_data",)

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        """
        Initialize a new Stack.

        Args:
            items (Optional[Iterable[T]]): Seed elements. The last element
                yielded by *items* becomes the top of the stack.
        """
        self._data: List[T] = list(items) if items is not None else []

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, *items: T) -> "Stack[T]":
        """Create a Stack from positional arguments."""
        return cls(items)

    @classmethod
    def empty(cls) -> "Stack[T]":
        """Create an empty Stack."""
        return cls()

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def push(self, item: T) -> "Stack[T]":
        """Push *item* onto the top (O(1))."""
        self._data.append(item)
        return self

    def push_all(self, items: Iterable[T]) -> "Stack[T]":
        """Push all elements of *items* in iteration order."""
        self._data.extend(items)
        return self

    def pop(self) -> T:
        """
        Remove and return the top element (O(1)).

        Raises:
            IndexError: If the stack is empty.
        """
        if not self._data:
            raise IndexError("pop from empty Stack")
        return self._data.pop()

    def pop_or(self, default: T) -> T:
        """Remove and return the top element, or *default* if empty."""
        return self._data.pop() if self._data else default

    def peek(self) -> Optional[T]:
        """Return the top element without removing it, or ``None`` if empty."""
        return self._data[-1] if self._data else None

    def clear(self) -> "Stack[T]":
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
        """Return a :class:`~arkhe.collections.stream.Stream` (bottom-to-top order)."""
        from arkhe.collections.stream import Stream
        return Stream(list(self._data))

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_list(self) -> List[T]:
        """Return a copy ordered from bottom to top."""
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
        if isinstance(other, Stack):
            return self._data == other._data
        return NotImplemented

    def __repr__(self) -> str:
        return f"Stack({self._data!r})"


if TYPE_CHECKING:
    from arkhe.collections.stream import Stream
