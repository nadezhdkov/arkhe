"""
arkhe.collections.immutable_list
--------------------------------------
An immutable, ordered sequence backed by a Python ``tuple``.

Inspired by Java's ``List.of(...)`` and ``Collections.unmodifiableList()``,
this class provides a fully read-only view over a sequence. Any attempt to
mutate it raises ``UnsupportedOperationException`` at runtime.

Because the backing store is a ``tuple``, ``ImmutableList`` is:

* **Hashable** — safe to use as a dict key or set element (provided elements are hashable).
* **Memory-efficient** — no extra list copy, no wasted capacity.
* **Thread-safe by construction** — no mutation means no race conditions.

Example::

    from arkhe.collections import ImmutableList

    primes = ImmutableList.of(2, 3, 5, 7, 11)
    primes[0]          # 2
    len(primes)        # 5
    primes.contains(5) # True

    doubled = primes.map(lambda n: n * 2)  # new ImmutableList([4, 6, 10, 14, 22])

    # Any mutation attempt raises UnsupportedOperationException:
    primes.append(13)  # ✗ raises UnsupportedOperationException

Wrapping a mutable collection::

    from arkhe.collections import ArrayList, ImmutableList

    mutable = ArrayList([1, 2, 3])
    frozen  = ImmutableList.copy_of(mutable)
    # Changes to `mutable` no longer affect `frozen`

Stream interop::

    from arkhe.collections import ImmutableList

    result = ImmutableList.of(1, 2, 3, 4, 5).stream().filter(lambda n: n % 2 == 0).to_list()
    # [2, 4]
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
    overload,
    TYPE_CHECKING,
)

T = TypeVar("T")
U = TypeVar("U")
K = TypeVar("K")
R = TypeVar("R")


class UnsupportedOperationException(TypeError):
    """
    Raised when a mutating operation is attempted on an immutable collection.

    Mirrors the semantics of ``java.lang.UnsupportedOperationException``.
    """


class ImmutableList(Generic[T]):
    """
    An immutable, ordered sequence backed by a ``tuple``.

    All transformation methods return **new** ``ImmutableList`` instances.
    Mutation methods are present as stubs that unconditionally raise
    :class:`UnsupportedOperationException`, mirroring the contract of
    ``Collections.unmodifiableList()`` in Java.
    """

    __slots__ = ("_data",)

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        """
        Initialize a new ImmutableList.

        Args:
            items (Optional[Iterable[T]]): Seed elements. Defaults to empty.

        Note:
            Prefer the factory methods :meth:`of`, :meth:`copy_of`, or
            :meth:`empty` over calling ``__init__`` directly.
        """
        object.__setattr__(self, "_data", tuple(items) if items is not None else ())

    # ------------------------------------------------------------------
    # Prevent attribute mutation on the object itself
    # ------------------------------------------------------------------

    def __setattr__(self, name: str, value: Any) -> None:  # type: ignore[override]
        raise UnsupportedOperationException(
            f"ImmutableList does not allow attribute assignment ('{name}')."
        )

    def __delattr__(self, name: str) -> None:
        raise UnsupportedOperationException(
            f"ImmutableList does not allow attribute deletion ('{name}')."
        )

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, *items: T) -> "ImmutableList[T]":
        """
        Create an ImmutableList from positional arguments.

        This is the closest equivalent to Java's ``List.of(e1, e2, ...)``.

        Args:
            *items (T): Elements in order.

        Returns:
            ImmutableList[T]: A new immutable list.

        Example::

            nums = ImmutableList.of(10, 20, 30)
        """
        return cls(items)

    @classmethod
    def empty(cls) -> "ImmutableList[T]":
        """
        Create an empty ImmutableList.

        Returns:
            ImmutableList[T]: An empty immutable list.
        """
        return cls(())

    @classmethod
    def copy_of(cls, iterable: Iterable[T]) -> "ImmutableList[T]":
        """
        Create an ImmutableList from any iterable, taking a defensive copy.

        This mirrors ``List.copyOf(collection)`` from Java 10+.
        Changes to the source after this call do not affect the result.

        Args:
            iterable (Iterable[T]): Source collection or sequence.

        Returns:
            ImmutableList[T]: A new immutable list.
        """
        return cls(iterable)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def get(self, index: int) -> T:
        """
        Return the element at *index*.

        Args:
            index (int): Zero-based index (negative indices supported).

        Raises:
            IndexError: If *index* is out of bounds.

        Returns:
            T: The element.
        """
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
        """Return ``True`` if the list holds no elements."""
        return not self._data

    def size(self) -> int:
        """Return the number of elements."""
        return len(self._data)

    def count_by(self, predicate: Callable[[T], bool]) -> int:
        """Return the number of elements satisfying *predicate*."""
        return sum(1 for item in self._data if predicate(item))

    # ------------------------------------------------------------------
    # Transformations — all return new ImmutableList instances
    # ------------------------------------------------------------------

    def map(self, transform: Callable[[T], U]) -> "ImmutableList[U]":
        """Return a new ImmutableList with *transform* applied to each element."""
        return ImmutableList(transform(item) for item in self._data)

    def filter(self, predicate: Callable[[T], bool]) -> "ImmutableList[T]":
        """Return a new ImmutableList with only elements matching *predicate*."""
        return ImmutableList(item for item in self._data if predicate(item))

    def flat_map(self, transform: Callable[[T], Iterable[U]]) -> "ImmutableList[U]":
        """Apply *transform* to each element and flatten one level."""
        result: List[U] = []
        for item in self._data:
            result.extend(transform(item))
        return ImmutableList(result)

    def reduce(self, fn: Callable[[R, T], R], initial: R) -> R:
        """Fold the list left using *fn*, starting from *initial*."""
        return functools.reduce(fn, self._data, initial)

    def distinct(self) -> "ImmutableList[T]":
        """Return a new ImmutableList with duplicates removed (first-occurrence order)."""
        seen: set = set()
        result: List[T] = []
        for item in self._data:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return ImmutableList(result)

    def take(self, n: int) -> "ImmutableList[T]":
        """Return a new ImmutableList with the first *n* elements."""
        return ImmutableList(self._data[:n])

    def drop(self, n: int) -> "ImmutableList[T]":
        """Return a new ImmutableList skipping the first *n* elements."""
        return ImmutableList(self._data[n:])

    def take_while(self, predicate: Callable[[T], bool]) -> "ImmutableList[T]":
        """Return elements from the front while *predicate* holds."""
        result: List[T] = []
        for item in self._data:
            if predicate(item):
                result.append(item)
            else:
                break
        return ImmutableList(result)

    def drop_while(self, predicate: Callable[[T], bool]) -> "ImmutableList[T]":
        """Skip elements from the front while *predicate* holds; return the rest."""
        i = 0
        while i < len(self._data) and predicate(self._data[i]):
            i += 1
        return ImmutableList(self._data[i:])

    def sorted(
        self,
        *,
        key: Optional[Callable[[T], Any]] = None,
        reverse: bool = False,
    ) -> "ImmutableList[T]":
        """Return a new sorted ImmutableList (original is unchanged)."""
        return ImmutableList(sorted(self._data, key=key, reverse=reverse))

    def reversed(self) -> "ImmutableList[T]":
        """Return a new ImmutableList with elements in reversed order."""
        return ImmutableList(reversed(self._data))

    def zip_with(self, other: Iterable[U]) -> "ImmutableList[Tuple[T, U]]":
        """Pair each element with the corresponding element of *other*."""
        return ImmutableList(zip(self._data, other))

    def group_by(self, key_fn: Callable[[T], K]) -> Dict[K, "ImmutableList[T]"]:
        """
        Group elements by the result of *key_fn*.

        Returns:
            Dict[K, ImmutableList[T]]: Mapping from key to grouped ImmutableList.
        """
        groups: Dict[K, List[T]] = {}
        for item in self._data:
            groups.setdefault(key_fn(item), []).append(item)
        return {k: ImmutableList(v) for k, v in groups.items()}

    def partition(
        self, predicate: Callable[[T], bool]
    ) -> Tuple["ImmutableList[T]", "ImmutableList[T]"]:
        """
        Split into two ImmutableLists: (matching, non-matching).

        Returns:
            Tuple[ImmutableList[T], ImmutableList[T]]: (truthy, falsy).
        """
        yes: List[T] = []
        no: List[T] = []
        for item in self._data:
            (yes if predicate(item) else no).append(item)
        return ImmutableList(yes), ImmutableList(no)

    def concat(self, other: "ImmutableList[T] | Iterable[T]") -> "ImmutableList[T]":
        """
        Return a new ImmutableList with *other* appended.

        Neither this list nor *other* is modified.

        Args:
            other (ImmutableList[T] | Iterable[T]): Elements to append.

        Returns:
            ImmutableList[T]: Combined list.
        """
        return ImmutableList((*self._data, *other))

    def for_each(self, action: Callable[[T], None]) -> "ImmutableList[T]":
        """Execute *action* for each element; supports chaining."""
        for item in self._data:
            action(item)
        return self

    # ------------------------------------------------------------------
    # Stream interop
    # ------------------------------------------------------------------

    def stream(self) -> "Stream[T]":
        """Return a :class:`~arkhe.collections.stream.Stream` backed by this list."""
        from arkhe.collections.stream import Stream
        return Stream(self._data)

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_list(self) -> List[T]:
        """Return a mutable shallow copy as a plain Python ``list``."""
        return list(self._data)

    def to_tuple(self) -> Tuple[T, ...]:
        """Return the underlying ``tuple`` directly (zero-copy)."""
        return self._data

    def to_set(self) -> Set[T]:
        """Return the elements as a plain Python ``set``."""
        return set(self._data)

    def to_mutable(self) -> "ArrayList[T]":
        """
        Return a mutable :class:`~arkhe.collections.array_list.ArrayList` copy.

        Returns:
            ArrayList[T]: A new mutable list with the same elements.
        """
        from arkhe.collections.array_list import ArrayList
        return ArrayList(self._data)

    # ------------------------------------------------------------------
    # Mutation stubs — always raise UnsupportedOperationException
    # ------------------------------------------------------------------

    def _mutation_error(self, operation: str) -> None:
        raise UnsupportedOperationException(
            f"ImmutableList does not support '{operation}'. "
            "Use transformation methods (map, filter, concat, …) to produce a new list, "
            "or call .to_mutable() to obtain a mutable copy."
        )

    def append(self, item: Any) -> None:  # type: ignore[return]
        """Raises UnsupportedOperationException — ImmutableList cannot be mutated."""
        self._mutation_error("append")

    def extend(self, items: Any) -> None:  # type: ignore[return]
        """Raises UnsupportedOperationException — ImmutableList cannot be mutated."""
        self._mutation_error("extend")

    def insert(self, index: Any, item: Any) -> None:  # type: ignore[return]
        """Raises UnsupportedOperationException — ImmutableList cannot be mutated."""
        self._mutation_error("insert")

    def remove(self, item: Any) -> None:  # type: ignore[return]
        """Raises UnsupportedOperationException — ImmutableList cannot be mutated."""
        self._mutation_error("remove")

    def pop(self, index: Any = -1) -> None:  # type: ignore[return]
        """Raises UnsupportedOperationException — ImmutableList cannot be mutated."""
        self._mutation_error("pop")

    def clear(self) -> None:  # type: ignore[return]
        """Raises UnsupportedOperationException — ImmutableList cannot be mutated."""
        self._mutation_error("clear")

    def sort(self, **kwargs: Any) -> None:  # type: ignore[return]
        """Raises UnsupportedOperationException — use .sorted() instead."""
        self._mutation_error("sort (use .sorted() to get a sorted copy)")

    def reverse(self) -> None:  # type: ignore[return]
        """Raises UnsupportedOperationException — use .reversed() instead."""
        self._mutation_error("reverse (use .reversed() to get a reversed copy)")

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
    def __getitem__(self, index: slice) -> "ImmutableList[T]": ...

    def __getitem__(self, index: int | slice) -> "T | ImmutableList[T]":
        if isinstance(index, slice):
            return ImmutableList(self._data[index])
        return self._data[index]

    def __setitem__(self, index: Any, value: Any) -> None:
        raise UnsupportedOperationException(
            "ImmutableList does not support item assignment. "
            "Call .to_mutable() to obtain a mutable copy."
        )

    def __delitem__(self, index: Any) -> None:
        raise UnsupportedOperationException(
            "ImmutableList does not support item deletion. "
            "Call .to_mutable() to obtain a mutable copy."
        )

    def __contains__(self, item: Any) -> bool:
        return item in self._data

    def __add__(self, other: "ImmutableList[T] | tuple") -> "ImmutableList[T]":
        """Support ``list1 + list2`` — returns a new ImmutableList."""
        return ImmutableList((*self._data, *other))

    def __mul__(self, n: int) -> "ImmutableList[T]":
        """Support ``list * n`` — returns a new ImmutableList."""
        return ImmutableList(self._data * n)

    def __rmul__(self, n: int) -> "ImmutableList[T]":
        return self.__mul__(n)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ImmutableList):
            return self._data == other._data
        if isinstance(other, (list, tuple)):
            return self._data == tuple(other)
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._data)

    def __repr__(self) -> str:
        return f"ImmutableList({list(self._data)!r})"


if TYPE_CHECKING:
    from arkhe.collections.stream import Stream
    from arkhe.collections.array_list import ArrayList
