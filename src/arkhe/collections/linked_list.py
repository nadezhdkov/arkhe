"""
arkhe.collections.linked_list
----------------------------------
A fluent doubly-linked list wrapping ``collections.deque``.

Provides O(1) operations at both ends, functional transformations, and
seamless :class:`~arkhe.collections.stream.Stream` interoperability.

Example::

    from arkhe.collections import LinkedList

    ll = (
        LinkedList([1, 2, 3])
        .add_first(0)
        .add_last(4)
        .map(lambda x: x * 2)
        .filter(lambda x: x > 2)
    )
    # LinkedList([4, 6, 8])
"""

from __future__ import annotations

import collections
import functools
from typing import (
    Any,
    Callable,
    Dict,
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
U = TypeVar("U")
K = TypeVar("K")
R = TypeVar("R")


class LinkedList(Generic[T]):
    """
    A doubly-linked list wrapping ``collections.deque`` with a fluent API.

    Mutation methods return ``self``; transformation methods return new instances.
    """

    __slots__ = ("_data",)

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        self._data: collections.deque[T] = collections.deque(
            items if items is not None else []
        )

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, *items: T) -> "LinkedList[T]":
        return cls(items)

    @classmethod
    def empty(cls) -> "LinkedList[T]":
        return cls()

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_first(self, item: T) -> "LinkedList[T]":
        """Prepend *item* (O(1))."""
        self._data.appendleft(item)
        return self

    def add_last(self, item: T) -> "LinkedList[T]":
        """Append *item* (O(1))."""
        self._data.append(item)
        return self

    def add_all_last(self, items: Iterable[T]) -> "LinkedList[T]":
        """Extend from the right."""
        self._data.extend(items)
        return self

    def remove_first(self) -> T:
        """Remove and return the first element (O(1))."""
        if not self._data:
            raise IndexError("remove_first from empty LinkedList")
        return self._data.popleft()

    def remove_last(self) -> T:
        """Remove and return the last element (O(1))."""
        if not self._data:
            raise IndexError("remove_last from empty LinkedList")
        return self._data.pop()

    def remove(self, item: T) -> "LinkedList[T]":
        """Remove the first occurrence of *item*; no-op if not present."""
        try:
            self._data.remove(item)
        except ValueError:
            pass
        return self

    def remove_if(self, predicate: Callable[[T], bool]) -> "LinkedList[T]":
        """Remove all elements for which *predicate* returns True (mutates in place)."""
        self._data = collections.deque(item for item in self._data if not predicate(item))
        return self

    def clear(self) -> "LinkedList[T]":
        self._data.clear()
        return self

    def reverse(self) -> "LinkedList[T]":
        """Reverse in place (O(n))."""
        self._data.reverse()
        return self

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def peek_first(self) -> Optional[T]:
        return self._data[0] if self._data else None

    def peek_last(self) -> Optional[T]:
        return self._data[-1] if self._data else None

    def contains(self, item: T) -> bool:
        return item in self._data

    def is_empty(self) -> bool:
        return not self._data

    def size(self) -> int:
        return len(self._data)

    def count_by(self, predicate: Callable[[T], bool]) -> int:
        return sum(1 for item in self._data if predicate(item))

    # ------------------------------------------------------------------
    # Transformation — new instances
    # ------------------------------------------------------------------

    def map(self, transform: Callable[[T], U]) -> "LinkedList[U]":
        return LinkedList(transform(item) for item in self._data)

    def filter(self, predicate: Callable[[T], bool]) -> "LinkedList[T]":
        return LinkedList(item for item in self._data if predicate(item))

    def flat_map(self, transform: Callable[[T], Iterable[U]]) -> "LinkedList[U]":
        result: List[U] = []
        for item in self._data:
            result.extend(transform(item))
        return LinkedList(result)

    def reduce(self, fn: Callable[[R, T], R], initial: R) -> R:
        return functools.reduce(fn, self._data, initial)

    def distinct(self) -> "LinkedList[T]":
        seen: set = set()
        result: List[T] = []
        for item in self._data:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return LinkedList(result)

    def take(self, n: int) -> "LinkedList[T]":
        return LinkedList(list(self._data)[:n])

    def drop(self, n: int) -> "LinkedList[T]":
        return LinkedList(list(self._data)[n:])

    def zip_with(self, other: Iterable[U]) -> "LinkedList[Tuple[T, U]]":
        return LinkedList(zip(self._data, other))

    def group_by(self, key_fn: Callable[[T], K]) -> Dict[K, "LinkedList[T]"]:
        groups: Dict[K, List[T]] = {}
        for item in self._data:
            groups.setdefault(key_fn(item), []).append(item)
        return {k: LinkedList(v) for k, v in groups.items()}

    def sorted(self, *, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> "LinkedList[T]":
        return LinkedList(sorted(self._data, key=key, reverse=reverse))

    def reversed(self) -> "LinkedList[T]":
        return LinkedList(reversed(self._data))

    def for_each(self, action: Callable[[T], None]) -> "LinkedList[T]":
        for item in self._data:
            action(item)
        return self

    # ------------------------------------------------------------------
    # Stream interop
    # ------------------------------------------------------------------

    def stream(self) -> "Stream[T]":
        from arkhe.collections.stream import Stream
        return Stream(list(self._data))

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_list(self) -> List[T]:
        return list(self._data)

    def to_set(self) -> set:
        return set(self._data)

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
        if isinstance(other, LinkedList):
            return list(self._data) == list(other._data)
        return NotImplemented

    def __repr__(self) -> str:
        return f"LinkedList({list(self._data)!r})"


if TYPE_CHECKING:
    from arkhe.collections.stream import Stream
