"""
arkhe.collections.ordered_set
-----------------------------------
A fluent insertion-ordered set backed by Python's ``dict``.

Guarantees unique elements while preserving the order in which they
were first added. Supports full set algebra (union, intersection,
difference, symmetric difference) and Stream interoperability.

Example::

    from arkhe.collections import OrderedSet

    s = (
        OrderedSet([3, 1, 4, 1, 5, 9, 2, 6])
        .remove(4)
        .filter(lambda x: x > 2)
    )
    # OrderedSet([3, 5, 9, 6])
"""

from __future__ import annotations

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
    Set,
    Tuple,
    TypeVar,
    TYPE_CHECKING,
)

T = TypeVar("T")
U = TypeVar("U")
K = TypeVar("K")
R = TypeVar("R")


class OrderedSet(Generic[T]):
    """
    An insertion-ordered set with a fluent API and full set algebra support.

    All elements must be **hashable**.
    """

    __slots__ = ("_data",)

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        self._data: Dict[T, None] = (
            dict.fromkeys(items) if items is not None else {}
        )

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, *items: T) -> "OrderedSet[T]":
        return cls(items)

    @classmethod
    def empty(cls) -> "OrderedSet[T]":
        return cls()

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, item: T) -> "OrderedSet[T]":
        """Add *item*; if already present its position is unchanged."""
        self._data[item] = None
        return self

    def add_all(self, items: Iterable[T]) -> "OrderedSet[T]":
        """Add all *items*."""
        for item in items:
            self._data[item] = None
        return self

    def remove(self, item: T) -> "OrderedSet[T]":
        """Remove *item*; no-op if not present."""
        self._data.pop(item, None)
        return self

    def discard(self, item: T) -> "OrderedSet[T]":
        """Alias for :meth:`remove`."""
        return self.remove(item)

    def clear(self) -> "OrderedSet[T]":
        self._data.clear()
        return self

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def contains(self, item: T) -> bool:
        return item in self._data

    def is_empty(self) -> bool:
        return not self._data

    def size(self) -> int:
        return len(self._data)

    def count_by(self, predicate: Callable[[T], bool]) -> int:
        return sum(1 for item in self._data if predicate(item))

    # ------------------------------------------------------------------
    # Set algebra — all return new instances
    # ------------------------------------------------------------------

    def union(self, other: Iterable[T]) -> "OrderedSet[T]":
        """Return a new set containing all elements from both."""
        result = OrderedSet(self._data.keys())
        for item in other:
            result._data[item] = None
        return result

    def intersection(self, other: Iterable[T]) -> "OrderedSet[T]":
        """Return a new set containing only elements present in both."""
        other_set: Set[Any] = set(other)
        return OrderedSet(item for item in self._data if item in other_set)

    def difference(self, other: Iterable[T]) -> "OrderedSet[T]":
        """Return a new set with elements from this set not in *other*."""
        other_set: Set[Any] = set(other)
        return OrderedSet(item for item in self._data if item not in other_set)

    def symmetric_difference(self, other: Iterable[T]) -> "OrderedSet[T]":
        """Return a new set with elements in exactly one of the two sets."""
        other_ordered = OrderedSet(other)
        result: List[T] = [item for item in self._data if item not in other_ordered._data]
        result += [item for item in other_ordered._data if item not in self._data]
        return OrderedSet(result)

    def is_subset(self, other: Iterable[T]) -> bool:
        """Return ``True`` if every element of this set is in *other*."""
        other_set: Set[Any] = set(other)
        return all(item in other_set for item in self._data)

    def is_superset(self, other: Iterable[T]) -> bool:
        """Return ``True`` if this set contains every element of *other*."""
        return all(item in self._data for item in other)

    def is_disjoint(self, other: Iterable[T]) -> bool:
        """Return ``True`` if this set and *other* share no elements."""
        other_set: Set[Any] = set(other)
        return not any(item in other_set for item in self._data)

    # ------------------------------------------------------------------
    # Transformation — new instances
    # ------------------------------------------------------------------

    def map(self, transform: Callable[[T], U]) -> "OrderedSet[U]":
        """Apply *transform* to each element; duplicates in the output are merged."""
        return OrderedSet(transform(item) for item in self._data)

    def filter(self, predicate: Callable[[T], bool]) -> "OrderedSet[T]":
        """Return a new set containing only elements where *predicate* is True."""
        return OrderedSet(item for item in self._data if predicate(item))

    def reduce(self, fn: Callable[[R, T], R], initial: R) -> R:
        return functools.reduce(fn, self._data.keys(), initial)

    def sorted(self, *, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> "OrderedSet[T]":
        """Return a new OrderedSet with elements in sorted order."""
        return OrderedSet(sorted(self._data.keys(), key=key, reverse=reverse))

    def for_each(self, action: Callable[[T], None]) -> "OrderedSet[T]":
        for item in self._data:
            action(item)
        return self

    # ------------------------------------------------------------------
    # Stream interop
    # ------------------------------------------------------------------

    def stream(self) -> "Stream[T]":
        from arkhe.collections.stream import Stream
        return Stream(list(self._data.keys()))

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_list(self) -> List[T]:
        return list(self._data.keys())

    def to_set(self) -> Set[T]:
        return set(self._data.keys())

    # ------------------------------------------------------------------
    # Operator overloads
    # ------------------------------------------------------------------

    def __or__(self, other: "OrderedSet[T]") -> "OrderedSet[T]":
        return self.union(other)

    def __and__(self, other: "OrderedSet[T]") -> "OrderedSet[T]":
        return self.intersection(other)

    def __sub__(self, other: "OrderedSet[T]") -> "OrderedSet[T]":
        return self.difference(other)

    def __xor__(self, other: "OrderedSet[T]") -> "OrderedSet[T]":
        return self.symmetric_difference(other)

    def __le__(self, other: "OrderedSet[T]") -> bool:
        return self.is_subset(other)

    def __ge__(self, other: "OrderedSet[T]") -> bool:
        return self.is_superset(other)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[T]:
        return iter(self._data.keys())

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, item: Any) -> bool:
        return item in self._data

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OrderedSet):
            return list(self._data.keys()) == list(other._data.keys())
        return NotImplemented

    def __hash__(self) -> int:  # type: ignore[override]
        return hash(tuple(self._data.keys()))

    def __repr__(self) -> str:
        return f"OrderedSet({list(self._data.keys())!r})"


if TYPE_CHECKING:
    from arkhe.collections.stream import Stream
