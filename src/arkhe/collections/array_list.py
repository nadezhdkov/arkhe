"""
arkhe.collections.array_list
---------------------------------
A fluent, Java-inspired wrapper around Python's built-in ``list``.

Provides a chainable, object-oriented API with functional programming
utilities (``map``, ``filter``, ``flat_map``, ``reduce``, ``for_each``,
``group_by``, ``zip_with``, …) and seamless interoperability with
:class:`~arkhe.collections.stream.Stream`.

Example::

    from arkhe.collections import ArrayList

    result = (
        ArrayList([1, 2, 3, 4, 5])
        .filter(lambda n: n % 2 == 0)
        .map(lambda n: n * 10)
        .to_list()
    )  # [20, 40]
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
    Tuple,
    TypeVar,
    overload,
)

T = TypeVar("T")
U = TypeVar("U")
K = TypeVar("K")
R = TypeVar("R")


class ArrayList(Generic[T]):
    """
    A dynamic array wrapping Python's ``list`` with a fluent, chainable API.

    Mutation methods return ``self``; transformation methods return new instances.
    """

    __slots__ = ("_data",)

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        """
        Initialize a new ArrayList.

        Args:
            items (Optional[Iterable[T]]): Seed elements. Defaults to an empty list.
        """
        self._data: List[T] = list(items) if items is not None else []

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, *items: T) -> "ArrayList[T]":
        """Create an ArrayList from positional arguments."""
        return cls(items)

    @classmethod
    def empty(cls) -> "ArrayList[T]":
        """Create an empty ArrayList."""
        return cls()

    # ------------------------------------------------------------------
    # Mutation — return self for chaining
    # ------------------------------------------------------------------

    def add(self, item: T) -> "ArrayList[T]":
        """Append *item* to the end of the list."""
        self._data.append(item)
        return self

    def add_all(self, items: Iterable[T]) -> "ArrayList[T]":
        """Extend the list with all elements from *items*."""
        self._data.extend(items)
        return self

    def insert(self, index: int, item: T) -> "ArrayList[T]":
        """Insert *item* before the element at *index*."""
        self._data.insert(index, item)
        return self

    def remove(self, item: T) -> "ArrayList[T]":
        """Remove the first occurrence of *item*; no-op if not found."""
        if item in self._data:
            self._data.remove(item)
        return self

    def remove_at(self, index: int) -> T:
        """
        Remove and return the element at *index*.

        Raises:
            IndexError: If *index* is out of range.
        """
        return self._data.pop(index)

    def remove_if(self, predicate: Callable[[T], bool]) -> "ArrayList[T]":
        """Remove all elements for which *predicate* returns True."""
        self._data = [item for item in self._data if not predicate(item)]
        return self

    def set(self, index: int, value: T) -> "ArrayList[T]":
        """Replace the element at *index* with *value*."""
        self._data[index] = value
        return self

    def sort(self, *, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> "ArrayList[T]":
        """Sort the list in place."""
        self._data.sort(key=key, reverse=reverse)
        return self

    def reverse(self) -> "ArrayList[T]":
        """Reverse the list in place."""
        self._data.reverse()
        return self

    def clear(self) -> "ArrayList[T]":
        """Remove all elements."""
        self._data.clear()
        return self

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def get(self, index: int) -> T:
        """Return the element at *index*."""
        return self._data[index]

    def get_or(self, index: int, default: T) -> T:
        """Return the element at *index*, or *default* if out of bounds."""
        try:
            return self._data[index]
        except IndexError:
            return default

    def first(self) -> Optional[T]:
        """Return the first element, or ``None`` if empty."""
        return self._data[0] if self._data else None

    def last(self) -> Optional[T]:
        """Return the last element, or ``None`` if empty."""
        return self._data[-1] if self._data else None

    def contains(self, item: T) -> bool:
        """Return ``True`` if *item* is in the list."""
        return item in self._data

    def index_of(self, item: T) -> int:
        """Return the first index of *item*, or ``-1`` if not found."""
        try:
            return self._data.index(item)
        except ValueError:
            return -1

    def is_empty(self) -> bool:
        """Return ``True`` if the list has no elements."""
        return not self._data

    def size(self) -> int:
        """Return the number of elements."""
        return len(self._data)

    def count_by(self, predicate: Callable[[T], bool]) -> int:
        """Return the number of elements satisfying *predicate*."""
        return sum(1 for item in self._data if predicate(item))

    # ------------------------------------------------------------------
    # Transformation — return new instances
    # ------------------------------------------------------------------

    def map(self, transform: Callable[[T], U]) -> "ArrayList[U]":
        """Return a new ArrayList with *transform* applied to each element."""
        return ArrayList(transform(item) for item in self._data)

    def filter(self, predicate: Callable[[T], bool]) -> "ArrayList[T]":
        """Return a new ArrayList containing only elements where *predicate* is True."""
        return ArrayList(item for item in self._data if predicate(item))

    def flat_map(self, transform: Callable[[T], Iterable[U]]) -> "ArrayList[U]":
        """Apply *transform* (returning an iterable) to each element and flatten one level."""
        result: List[U] = []
        for item in self._data:
            result.extend(transform(item))
        return ArrayList(result)

    def reduce(self, fn: Callable[[R, T], R], initial: R) -> R:
        """Fold the list left using *fn*, starting from *initial*."""
        return functools.reduce(fn, self._data, initial)

    def distinct(self) -> "ArrayList[T]":
        """Return a new ArrayList with duplicates removed, preserving first-occurrence order."""
        seen: set = set()
        result: List[T] = []
        for item in self._data:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return ArrayList(result)

    def take(self, n: int) -> "ArrayList[T]":
        """Return a new ArrayList with the first *n* elements."""
        return ArrayList(self._data[:n])

    def drop(self, n: int) -> "ArrayList[T]":
        """Return a new ArrayList skipping the first *n* elements."""
        return ArrayList(self._data[n:])

    def take_while(self, predicate: Callable[[T], bool]) -> "ArrayList[T]":
        """Return elements from the front while *predicate* is True."""
        result: List[T] = []
        for item in self._data:
            if predicate(item):
                result.append(item)
            else:
                break
        return ArrayList(result)

    def drop_while(self, predicate: Callable[[T], bool]) -> "ArrayList[T]":
        """Drop elements from the front while *predicate* is True; return the rest."""
        i = 0
        while i < len(self._data) and predicate(self._data[i]):
            i += 1
        return ArrayList(self._data[i:])

    def zip_with(self, other: Iterable[U]) -> "ArrayList[Tuple[T, U]]":
        """Pair each element with the corresponding element of *other*."""
        return ArrayList(zip(self._data, other))

    def group_by(self, key_fn: Callable[[T], K]) -> Dict[K, "ArrayList[T]"]:
        """
        Group elements by the result of *key_fn*.

        Returns:
            Dict[K, ArrayList[T]]: Mapping from key to grouped ArrayList.
        """
        groups: Dict[K, List[T]] = {}
        for item in self._data:
            groups.setdefault(key_fn(item), []).append(item)
        return {k: ArrayList(v) for k, v in groups.items()}

    def partition(self, predicate: Callable[[T], bool]) -> Tuple["ArrayList[T]", "ArrayList[T]"]:
        """
        Split into two ArrayLists: matching and non-matching elements.

        Returns:
            Tuple[ArrayList[T], ArrayList[T]]: (matching, non-matching).
        """
        yes: List[T] = []
        no: List[T] = []
        for item in self._data:
            (yes if predicate(item) else no).append(item)
        return ArrayList(yes), ArrayList(no)

    def chunk(self, size: int) -> "ArrayList[ArrayList[T]]":
        """
        Split the list into chunks of *size* elements. Last chunk may be smaller.

        Args:
            size (int): Chunk size (must be >= 1).

        Returns:
            ArrayList[ArrayList[T]]: ArrayList of chunks.
        """
        if size < 1:
            raise ValueError(f"chunk size must be >= 1, got {size}")
        return ArrayList(
            ArrayList(self._data[i : i + size]) for i in range(0, len(self._data), size)
        )

    def flatten(self) -> "ArrayList[Any]":
        """Flatten one level when elements are themselves iterables."""
        result: List[Any] = []
        for item in self._data:
            try:
                result.extend(item)  # type: ignore[arg-type]
            except TypeError:
                result.append(item)
        return ArrayList(result)

    def sorted(self, *, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> "ArrayList[T]":
        """Return a new sorted ArrayList (non-mutating)."""
        return ArrayList(sorted(self._data, key=key, reverse=reverse))

    def reversed(self) -> "ArrayList[T]":
        """Return a new reversed ArrayList (non-mutating)."""
        return ArrayList(reversed(self._data))

    def enumerate(self, start: int = 0) -> "ArrayList[Tuple[int, T]]":
        """Pair each element with its index."""
        return ArrayList(builtins_enumerate(self._data, start))

    # ------------------------------------------------------------------
    # Side effects — no return value
    # ------------------------------------------------------------------

    def for_each(self, action: Callable[[T], None]) -> "ArrayList[T]":
        """Execute *action* for each element; supports chaining."""
        for item in self._data:
            action(item)
        return self

    # ------------------------------------------------------------------
    # Stream interop
    # ------------------------------------------------------------------

    def stream(self) -> "Stream[T]":
        """
        Return a :class:`~arkhe.collections.stream.Stream` backed by a
        copy of this list, enabling lazy pipeline operations.

        Returns:
            Stream[T]: A new Stream.
        """
        from arkhe.collections.stream import Stream
        return Stream(list(self._data))

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_list(self) -> List[T]:
        """Return a shallow copy as a plain Python list."""
        return list(self._data)

    def to_set(self) -> set:
        """Return the elements as a plain Python set."""
        return set(self._data)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> "ArrayList[T]": ...

    def __getitem__(self, index: int | slice) -> "T | ArrayList[T]":
        if isinstance(index, slice):
            return ArrayList(self._data[index])
        return self._data[index]

    def __setitem__(self, index: int, value: T) -> None:
        self._data[index] = value

    def __contains__(self, item: Any) -> bool:
        return item in self._data

    def __add__(self, other: "ArrayList[T]") -> "ArrayList[T]":
        return ArrayList(self._data + list(other))

    def __iadd__(self, other: Iterable[T]) -> "ArrayList[T]":
        self._data.extend(other)
        return self

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ArrayList):
            return self._data == other._data
        if isinstance(other, list):
            return self._data == other
        return NotImplemented

    def __hash__(self) -> int:  # type: ignore[override]
        return hash(tuple(self._data))

    def __repr__(self) -> str:
        return f"ArrayList({self._data!r})"


import builtins as _builtins
builtins_enumerate = _builtins.enumerate

# Avoid circular import at module level
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from arkhe.collections.stream import Stream
