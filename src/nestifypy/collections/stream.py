"""
nestifypy.collections.stream
----------------------------
A lazy, composable pipeline for sequential data processing, modelled after
Java's ``Stream<T>`` API and Python's own ``itertools``.

A ``Stream`` wraps any ``Iterable`` and lets you chain functional
operations — ``map``, ``filter``, ``flat_map``, ``take``, ``drop``,
``distinct``, ``sorted_by``, and more — without evaluating anything until
a *terminal operation* is called (``to_list``, ``to_set``, ``reduce``,
``count``, ``first``, ``for_each``, …).

Because intermediate operations are lazy, Streams are memory-efficient for
large or infinite sequences.

Example::

    from nestifypy.collections import Stream

    result = (
        Stream.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        .filter(lambda n: n % 2 == 0)   # 2, 4, 6, 8, 10
        .map(lambda n: n ** 2)           # 4, 16, 36, 64, 100
        .take(3)                         # 4, 16, 36
        .to_list()                       # [4, 16, 36]
    )

Note:
    A Stream may only be consumed **once**. Attempting to reuse an exhausted
    stream raises ``StreamExhaustedException``.
"""

from __future__ import annotations

import itertools
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
)

T = TypeVar("T")
U = TypeVar("U")
K = TypeVar("K")
R = TypeVar("R")

# Sentinel used by pairwise() to detect the first iteration
_MISSING = object()


class StreamExhaustedException(RuntimeError):
    """Raised when a terminal operation is called on an already-consumed Stream."""


class Stream(Generic[T]):
    """
    A lazy sequential pipeline over an ``Iterable[T]``.

    Intermediate operations (``map``, ``filter``, …) return new ``Stream``
    instances and do **not** iterate the source. Terminal operations
    (``to_list``, ``reduce``, ``count``, …) trigger evaluation.
    """

    __slots__ = ("_source", "_exhausted")

    def __init__(self, source: Iterable[T]) -> None:
        self._source: Iterator[T] = iter(source)
        self._exhausted = False

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, *items: T) -> "Stream[T]":
        """
        Create a Stream from positional arguments.

        Args:
            *items (T): Elements to stream.

        Returns:
            Stream[T]: A new Stream over the given items.
        """
        return cls(items)

    @classmethod
    def from_iterable(cls, iterable: Iterable[T]) -> "Stream[T]":
        """
        Create a Stream from any iterable.

        Args:
            iterable (Iterable[T]): Source iterable.

        Returns:
            Stream[T]: A new Stream wrapping the iterable.
        """
        return cls(iterable)

    @classmethod
    def empty(cls) -> "Stream[T]":
        """
        Create an empty Stream.

        Returns:
            Stream[T]: An empty Stream.
        """
        return cls(iter([]))

    @classmethod
    def iterate(cls, seed: T, fn: Callable[[T], T]) -> "Stream[T]":
        """
        Create an infinite Stream by repeatedly applying *fn* to the last value.

        Use :meth:`take` to bound the sequence.

        Args:
            seed (T): Initial value.
            fn (Callable[[T], T]): Function applied to each element to produce the next.

        Returns:
            Stream[T]: Infinite Stream starting from *seed*.
        """
        def _gen() -> Iterator[T]:
            val = seed
            while True:
                yield val
                val = fn(val)
        return cls(_gen())

    @classmethod
    def range(cls, *args: int) -> "Stream[int]":
        """
        Create a Stream from ``range(*args)`` — same signature as built-in ``range``.

        Returns:
            Stream[int]: A Stream over integers.
        """
        return cls(range(*args))  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check(self) -> None:
        if self._exhausted:
            raise StreamExhaustedException(
                "This Stream has already been consumed. Create a new one."
            )

    def _wrap(self, iterable: Iterable[U]) -> "Stream[U]":
        s: Stream[U] = Stream.__new__(Stream)
        s._source = iter(iterable)
        s._exhausted = False
        return s

    def _consume(self) -> Iterator[T]:
        self._check()
        self._exhausted = True
        return self._source

    # ------------------------------------------------------------------
    # Intermediate operations  (lazy — return new Stream)
    # ------------------------------------------------------------------

    def map(self, transform: Callable[[T], U]) -> "Stream[U]":
        """
        Return a new Stream with *transform* applied to each element.

        Args:
            transform (Callable[[T], U]): Mapping function.

        Returns:
            Stream[U]: Transformed Stream.
        """
        self._check()
        return self._wrap(map(transform, self._source))

    def filter(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """
        Return a new Stream containing only elements for which *predicate* is truthy.

        Args:
            predicate (Callable[[T], bool]): Test function.

        Returns:
            Stream[T]: Filtered Stream.
        """
        self._check()
        return self._wrap(filter(predicate, self._source))

    def flat_map(self, transform: Callable[[T], Iterable[U]]) -> "Stream[U]":
        """
        Apply *transform* (which returns an iterable) to each element and flatten.

        Args:
            transform (Callable[[T], Iterable[U]]): Function that returns an iterable.

        Returns:
            Stream[U]: Flattened Stream.
        """
        self._check()
        return self._wrap(itertools.chain.from_iterable(map(transform, self._source)))

    def take(self, n: int) -> "Stream[T]":
        """
        Return a Stream of at most *n* elements from the front.

        Args:
            n (int): Maximum number of elements to include.

        Returns:
            Stream[T]: Truncated Stream.
        """
        self._check()
        return self._wrap(itertools.islice(self._source, n))

    def drop(self, n: int) -> "Stream[T]":
        """
        Return a Stream skipping the first *n* elements.

        Args:
            n (int): Number of elements to skip.

        Returns:
            Stream[T]: Stream without the first *n* elements.
        """
        self._check()
        return self._wrap(itertools.islice(self._source, n, None))

    def take_while(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """
        Return elements while *predicate* is True; stop at the first False.

        Args:
            predicate (Callable[[T], bool]): Continuation predicate.

        Returns:
            Stream[T]: Prefix Stream.
        """
        self._check()
        return self._wrap(itertools.takewhile(predicate, self._source))

    def drop_while(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """
        Drop elements while *predicate* is True; yield the rest.

        Args:
            predicate (Callable[[T], bool]): Predicate to skip.

        Returns:
            Stream[T]: Stream after the leading run.
        """
        self._check()
        return self._wrap(itertools.dropwhile(predicate, self._source))

    def distinct(self) -> "Stream[T]":
        """
        Return a Stream with duplicate elements removed (preserving first occurrence).

        Elements must be hashable.

        Returns:
            Stream[T]: De-duplicated Stream.
        """
        self._check()
        def _gen() -> Iterator[T]:
            seen: Set[Any] = set()
            for item in self._source:
                if item not in seen:
                    seen.add(item)
                    yield item
        return self._wrap(_gen())

    def sorted(self, *, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> "Stream[T]":
        """
        Return a new Stream with elements in sorted order.

        This is *not* lazy — it materialises the current stream to sort it.

        Args:
            key (Callable | None): Sort key function. Defaults to None.
            reverse (bool): Sort descending when True. Defaults to False.

        Returns:
            Stream[T]: Sorted Stream.
        """
        self._check()
        data = builtins_sorted(self._source, key=key, reverse=reverse)
        return self._wrap(iter(data))

    def peek(self, action: Callable[[T], None]) -> "Stream[T]":
        """
        Execute *action* for each element as they pass through (for debugging).

        Args:
            action (Callable[[T], None]): Side-effecting function.

        Returns:
            Stream[T]: The same Stream (pass-through).
        """
        self._check()
        def _gen() -> Iterator[T]:
            for item in self._source:
                action(item)
                yield item
        return self._wrap(_gen())

    def zip_with(self, other: Iterable[U]) -> "Stream[Tuple[T, U]]":
        """
        Pair each element of this Stream with the corresponding element of *other*.

        Stops when the shorter sequence is exhausted.

        Args:
            other (Iterable[U]): Iterable to zip with.

        Returns:
            Stream[Tuple[T, U]]: Zipped Stream.
        """
        self._check()
        return self._wrap(zip(self._source, other))

    def enumerate(self, start: int = 0) -> "Stream[Tuple[int, T]]":
        """
        Pair each element with its index.

        Args:
            start (int): Starting index. Defaults to 0.

        Returns:
            Stream[Tuple[int, T]]: Enumerated Stream.
        """
        self._check()
        return self._wrap(builtins_enumerate(self._source, start))

    def flatten(self) -> "Stream[Any]":
        """
        Flatten a Stream of iterables by one level.

        Returns:
            Stream: Flattened Stream.
        """
        self._check()
        return self._wrap(itertools.chain.from_iterable(self._source))  # type: ignore[arg-type]

    def chunk(self, size: int) -> "Stream[List[T]]":
        """
        Partition the Stream into lists of *size* elements.
        The last chunk may be smaller.

        Args:
            size (int): Chunk size (must be >= 1).

        Returns:
            Stream[List[T]]: Stream of chunks.

        Raises:
            ValueError: If *size* is less than 1.
        """
        if size < 1:
            raise ValueError(f"chunk size must be >= 1, got {size}")
        self._check()
        def _gen() -> Iterator[List[T]]:
            batch: List[T] = []
            for item in self._source:
                batch.append(item)
                if len(batch) == size:
                    yield batch
                    batch = []
            if batch:
                yield batch
        return self._wrap(_gen())

    def distinct_by(self, key_fn: Callable[[T], Any]) -> "Stream[T]":
        """
        Return a Stream with duplicates removed using a custom key extractor.

        Only the first element for each key is kept. Unlike :meth:`distinct`,
        this works correctly on non-hashable objects and complex types.

        Args:
            key_fn (Callable[[T], Any]): Function that extracts the deduplication key.

        Returns:
            Stream[T]: De-duplicated Stream.

        Example::

            Stream.of(users).distinct_by(lambda u: u.id)
        """
        self._check()
        def _gen() -> Iterator[T]:
            seen: Set[Any] = set()
            for item in self._source:
                k = key_fn(item)
                if k not in seen:
                    seen.add(k)
                    yield item
        return self._wrap(_gen())

    def window(self, size: int) -> "Stream[List[T]]":
        """
        Produce a sliding window of *size* consecutive elements.

        Each step advances by one element. The stream must contain at least
        *size* elements for any window to be emitted.

        Args:
            size (int): Window size (must be >= 1).

        Returns:
            Stream[List[T]]: Stream of windows (each a plain list).

        Raises:
            ValueError: If *size* is less than 1.

        Example::

            Stream.range(1, 6).window(3)
            # [1, 2, 3], [2, 3, 4], [3, 4, 5]
        """
        if size < 1:
            raise ValueError(f"window size must be >= 1, got {size}")
        self._check()
        def _gen() -> Iterator[List[T]]:
            buf: List[T] = []
            for item in self._source:
                buf.append(item)
                if len(buf) == size:
                    yield list(buf)
                    buf.pop(0)
        return self._wrap(_gen())

    def pairwise(self) -> "Stream[Tuple[T, T]]":
        """
        Return a Stream of consecutive overlapping pairs.

        Equivalent to ``window(2)`` but yields tuples instead of lists.

        Returns:
            Stream[Tuple[T, T]]: Stream of (prev, next) pairs.

        Example::

            Stream.of(1, 2, 3, 4).pairwise()
            # (1, 2), (2, 3), (3, 4)
        """
        self._check()
        def _gen() -> Iterator[Tuple[T, T]]:
            prev = _MISSING
            for item in self._source:
                if prev is not _MISSING:
                    yield (prev, item)  # type: ignore[misc]
                prev = item
        return self._wrap(_gen())

    def map_not_none(self, transform: Callable[[T], Optional[U]]) -> "Stream[U]":
        """
        Apply *transform* to each element, discarding ``None`` results.

        Useful when the mapping function may fail or return nothing for
        certain inputs (e.g. parsing, type coercion).

        Args:
            transform (Callable[[T], U | None]): Mapping function.

        Returns:
            Stream[U]: Stream of non-None results.

        Example::

            Stream.of("1", "2", "x", "3").map_not_none(parse_int)
            # 1, 2, 3
        """
        self._check()
        def _gen() -> Iterator[U]:
            for item in self._source:
                result = transform(item)
                if result is not None:
                    yield result
        return self._wrap(_gen())

    def filter_is_instance(self, type_: type) -> "Stream[Any]":
        """
        Return a Stream containing only elements that are instances of *type_*.

        Args:
            type_ (type): The type to filter by.

        Returns:
            Stream: Stream of matching elements (cast to *type_*).

        Example::

            Stream.of(1, "hello", 2, "world").filter_is_instance(str)
            # "hello", "world"
        """
        self._check()
        return self._wrap(item for item in self._source if isinstance(item, type_))

    def associate_by(self, key_fn: Callable[[T], K]) -> "HashMap[K, T]":
        """
        Collect elements into a :class:`~nestifypy.collections.HashMap` keyed
        by the result of *key_fn*.

        If multiple elements produce the same key, the last one wins.

        Args:
            key_fn (Callable[[T], K]): Key extractor.

        Returns:
            HashMap[K, T]: Map from key to element.

        Example::

            users.stream().associate_by(lambda u: u.id)
            # {1: user1, 2: user2}
        """
        from nestifypy.collections.hash_map import HashMap
        result: HashMap[K, T] = HashMap()
        for item in self._consume():
            result.put(key_fn(item), item)
        return result

    def associate(
        self,
        key: Callable[[T], K],
        value: Callable[[T], U],
    ) -> "HashMap[K, U]":
        """
        Collect elements into a :class:`~nestifypy.collections.HashMap` with
        custom key and value extractors.

        If multiple elements produce the same key, the last one wins.

        Args:
            key (Callable[[T], K]): Key extractor.
            value (Callable[[T], U]): Value extractor.

        Returns:
            HashMap[K, U]: Map from extracted keys to extracted values.

        Example::

            users.stream().associate(key=lambda u: u.id, value=lambda u: u.name)
            # {1: "John", 2: "Maria"}
        """
        from nestifypy.collections.hash_map import HashMap
        result: HashMap[K, U] = HashMap()
        for item in self._consume():
            result.put(key(item), value(item))
        return result

    # ------------------------------------------------------------------
    # Terminal operations  (eager — trigger evaluation)
    # ------------------------------------------------------------------

    def to_list(self) -> List[T]:
        """
        Collect all elements into a ``list``.

        Returns:
            List[T]: Collected elements.
        """
        return list(self._consume())

    def to_set(self) -> Set[T]:
        """
        Collect all elements into a ``set``.

        Returns:
            Set[T]: Collected elements (duplicates removed).
        """
        return set(self._consume())

    def to_dict(self, key_fn: Callable[[T], K], value_fn: Callable[[T], U] = lambda x: x) -> Dict[K, U]:  # type: ignore[assignment]
        """
        Collect elements into a ``dict`` using key and value extractor functions.

        If multiple elements produce the same key, the last one wins.

        Args:
            key_fn (Callable[[T], K]): Extracts the dict key from each element.
            value_fn (Callable[[T], U]): Extracts the dict value. Defaults to identity.

        Returns:
            Dict[K, U]: Resulting dictionary.
        """
        return {key_fn(item): value_fn(item) for item in self._consume()}

    def group_by(self, key_fn: Callable[[T], K]) -> Dict[K, List[T]]:
        """
        Group elements into a dict keyed by *key_fn*, preserving insertion order.

        Args:
            key_fn (Callable[[T], K]): Grouping key extractor.

        Returns:
            Dict[K, List[T]]: Groups of elements.
        """
        result: Dict[K, List[T]] = {}
        for item in self._consume():
            k = key_fn(item)
            result.setdefault(k, []).append(item)
        return result

    def partition(self, predicate: Callable[[T], bool]) -> Tuple[List[T], List[T]]:
        """
        Split elements into two lists: those satisfying *predicate* and those that don't.

        Args:
            predicate (Callable[[T], bool]): Partitioning test.

        Returns:
            Tuple[List[T], List[T]]: (matching, non-matching) lists.
        """
        yes: List[T] = []
        no: List[T] = []
        for item in self._consume():
            (yes if predicate(item) else no).append(item)
        return yes, no

    def reduce(self, fn: Callable[[R, T], R], initial: R) -> R:
        """
        Fold the stream left using *fn*, starting from *initial*.

        Args:
            fn (Callable[[R, T], R]): Accumulator function (acc, item) → acc.
            initial (R): Starting accumulator value.

        Returns:
            R: Final accumulated value.
        """
        return functools.reduce(fn, self._consume(), initial)

    def count(self) -> int:
        """
        Count the number of elements in the Stream.

        Returns:
            int: Element count.
        """
        return sum(1 for _ in self._consume())

    def sum(self) -> Any:
        """
        Return the sum of all elements (elements must support ``+``).

        Returns:
            The total sum.
        """
        return builtins_sum(self._consume())

    def min(self, *, key: Optional[Callable[[T], Any]] = None) -> Optional[T]:
        """
        Return the minimum element, or ``None`` if the stream is empty.

        Args:
            key (Callable | None): Comparison key. Defaults to None.

        Returns:
            Optional[T]: Minimum element or None.
        """
        try:
            return builtins_min(self._consume(), key=key) if key else builtins_min(self._consume())
        except ValueError:
            return None

    def max(self, *, key: Optional[Callable[[T], Any]] = None) -> Optional[T]:
        """
        Return the maximum element, or ``None`` if the stream is empty.

        Args:
            key (Callable | None): Comparison key. Defaults to None.

        Returns:
            Optional[T]: Maximum element or None.
        """
        try:
            return builtins_max(self._consume(), key=key) if key else builtins_max(self._consume())
        except ValueError:
            return None

    def first(self) -> "Optional[T]":
        """
        Return an ``Optional`` containing the first element, or empty if the stream is empty.

        Returns:
            Optional[T]: First element wrapped in Optional.
        """
        from nestifypy.collections.optional import Optional as Opt
        try:
            return Opt.of(next(self._consume()))
        except StopIteration:
            self._exhausted = True
            return Opt.empty()

    def last(self) -> "Optional[T]":
        """
        Return an ``Optional`` containing the last element, or empty if the stream is empty.

        Returns:
            Optional[T]: Last element wrapped in Optional.
        """
        from nestifypy.collections.optional import Optional as Opt
        sentinel = object()
        last_val: Any = sentinel
        for item in self._consume():
            last_val = item
        if last_val is sentinel:
            return Opt.empty()
        return Opt.of(last_val)

    def any_match(self, predicate: Callable[[T], bool]) -> bool:
        """
        Return ``True`` if at least one element satisfies *predicate*.

        Args:
            predicate (Callable[[T], bool]): Test function.

        Returns:
            bool: True if any element matches.
        """
        return any(predicate(item) for item in self._consume())

    def all_match(self, predicate: Callable[[T], bool]) -> bool:
        """
        Return ``True`` if every element satisfies *predicate*.

        Args:
            predicate (Callable[[T], bool]): Test function.

        Returns:
            bool: True if all elements match.
        """
        return all(predicate(item) for item in self._consume())

    def none_match(self, predicate: Callable[[T], bool]) -> bool:
        """
        Return ``True`` if no element satisfies *predicate*.

        Args:
            predicate (Callable[[T], bool]): Test function.

        Returns:
            bool: True if no element matches.
        """
        return not any(predicate(item) for item in self._consume())

    def for_each(self, action: Callable[[T], None]) -> None:
        """
        Execute *action* for every element. Terminal — consumes the Stream.

        Args:
            action (Callable[[T], None]): Side-effecting function.
        """
        for item in self._consume():
            action(item)

    def find_first(self, predicate: Callable[[T], bool]) -> "Optional[T]":
        """
        Return the first element satisfying *predicate*, wrapped in Optional.

        Args:
            predicate (Callable[[T], bool]): Test function.

        Returns:
            Optional[T]: Matching element or empty Optional.
        """
        from nestifypy.collections.optional import Optional as Opt
        for item in self._consume():
            if predicate(item):
                self._exhausted = True
                return Opt.of(item)
        return Opt.empty()

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[T]:
        return self._consume()

    def __repr__(self) -> str:
        status = "exhausted" if self._exhausted else "pending"
        return f"Stream({status})"


# ---------------------------------------------------------------------------
# Avoid shadowing builtins inside the class body
# ---------------------------------------------------------------------------
import builtins as _builtins

builtins_sorted = _builtins.sorted
builtins_enumerate = _builtins.enumerate
builtins_sum = _builtins.sum
builtins_min = _builtins.min
builtins_max = _builtins.max
