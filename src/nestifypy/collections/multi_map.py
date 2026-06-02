"""
nestifypy.collections.multi_map
--------------------------------
A map that associates each key with a *list* of values, rather than a
single value. Ideal for groupings, indices, and query-parameter bags.

Example::

    from nestifypy.collections import MultiMap

    params = MultiMap()
    params.put("color", "red").put("color", "blue").put("size", "M")

    params.get("color")      # ["red", "blue"]
    params.get("size")       # ["M"]
    params.get("missing")    # []

    for key, values in params.entries():
        print(key, values)
"""

from __future__ import annotations

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

K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")


class MultiMap(Generic[K, V]):
    """
    A map that may associate multiple values with a single key.

    All mutation methods return ``self`` for chaining.
    """

    __slots__ = ("_data",)

    def __init__(self, initial_data: Optional[Dict[K, List[V]]] = None) -> None:
        """
        Initialize a new MultiMap.

        Args:
            initial_data (Optional[Dict[K, List[V]]]): Seed data. Each key
                maps to a *list* of values. A shallow copy is made.
        """
        if initial_data is not None:
            self._data: Dict[K, List[V]] = {k: list(v) for k, v in initial_data.items()}
        else:
            self._data = {}

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def empty(cls) -> "MultiMap[K, V]":
        """Create an empty MultiMap."""
        return cls()

    @classmethod
    def from_entries(cls, entries: Iterable[Tuple[K, V]]) -> "MultiMap[K, V]":
        """
        Create a MultiMap from an iterable of (key, value) pairs.

        Duplicate keys accumulate their values.

        Args:
            entries (Iterable[Tuple[K, V]]): Sequence of (key, value) pairs.

        Returns:
            MultiMap[K, V]: Populated MultiMap.
        """
        mm: MultiMap[K, V] = cls()
        for k, v in entries:
            mm.put(k, v)
        return mm

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def put(self, key: K, value: V) -> "MultiMap[K, V]":
        """
        Add *value* to the list of values associated with *key*.

        Args:
            key (K): The key.
            value (V): The value to append.

        Returns:
            MultiMap[K, V]: self
        """
        self._data.setdefault(key, []).append(value)
        return self

    def put_all(self, key: K, values: Iterable[V]) -> "MultiMap[K, V]":
        """
        Add multiple *values* to the list associated with *key*.

        Args:
            key (K): The key.
            values (Iterable[V]): Values to append.

        Returns:
            MultiMap[K, V]: self
        """
        self._data.setdefault(key, []).extend(values)
        return self

    def replace(self, key: K, values: List[V]) -> "MultiMap[K, V]":
        """
        Replace all values for *key* with the given list.

        Args:
            key (K): The key.
            values (List[V]): New list of values.

        Returns:
            MultiMap[K, V]: self
        """
        self._data[key] = list(values)
        return self

    def remove(self, key: K) -> "MultiMap[K, V]":
        """
        Remove all values for *key*; no-op if not present.

        Args:
            key (K): Key to remove entirely.

        Returns:
            MultiMap[K, V]: self
        """
        self._data.pop(key, None)
        return self

    def remove_value(self, key: K, value: V) -> "MultiMap[K, V]":
        """
        Remove a single occurrence of *value* from the list for *key*.
        Removes the key entirely if the list becomes empty.

        Args:
            key (K): The key.
            value (V): The value to remove.

        Returns:
            MultiMap[K, V]: self
        """
        if key in self._data:
            try:
                self._data[key].remove(value)
            except ValueError:
                pass
            if not self._data[key]:
                del self._data[key]
        return self

    def clear(self) -> "MultiMap[K, V]":
        """Remove all entries."""
        self._data.clear()
        return self

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, key: K) -> List[V]:
        """
        Return all values for *key*, or an empty list if not found.

        The returned list is a **copy** — mutating it does not affect the map.

        Args:
            key (K): Key to look up.

        Returns:
            List[V]: Associated values.
        """
        return list(self._data.get(key, []))

    def get_first(self, key: K) -> Optional[V]:
        """
        Return the first value for *key*, or ``None`` if not found.

        Args:
            key (K): Key to look up.

        Returns:
            Optional[V]: First value or None.
        """
        values = self._data.get(key)
        return values[0] if values else None

    def get_last(self, key: K) -> Optional[V]:
        """
        Return the last value for *key*, or ``None`` if not found.

        Args:
            key (K): Key to look up.

        Returns:
            Optional[V]: Last value or None.
        """
        values = self._data.get(key)
        return values[-1] if values else None

    def contains_key(self, key: K) -> bool:
        """Return ``True`` if *key* has at least one associated value."""
        return key in self._data

    def contains_entry(self, key: K, value: V) -> bool:
        """Return ``True`` if (*key*, *value*) is a stored association."""
        return value in self._data.get(key, [])

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Return ``True`` if the map has no entries."""
        return not self._data

    def key_count(self) -> int:
        """Return the number of distinct keys."""
        return len(self._data)

    def value_count(self) -> int:
        """Return the total number of (key, value) associations."""
        return sum(len(vs) for vs in self._data.values())

    def size(self) -> int:
        """Alias for :meth:`key_count`."""
        return self.key_count()

    def keys(self) -> List[K]:
        """Return all keys as a list."""
        return list(self._data.keys())

    def values_flat(self) -> List[V]:
        """Return all values as a flat list (preserves per-key insertion order)."""
        result: List[V] = []
        for vs in self._data.values():
            result.extend(vs)
        return result

    def entries(self) -> List[Tuple[K, List[V]]]:
        """Return (key, [values]) pairs as a list."""
        return [(k, list(vs)) for k, vs in self._data.items()]

    def flat_entries(self) -> List[Tuple[K, V]]:
        """Return a flat list of (key, value) pairs, one per association."""
        result: List[Tuple[K, V]] = []
        for k, vs in self._data.items():
            for v in vs:
                result.append((k, v))
        return result

    # ------------------------------------------------------------------
    # Transformation
    # ------------------------------------------------------------------

    def map_values(self, transform: Callable[[V], U]) -> "MultiMap[K, U]":
        """
        Return a new MultiMap with *transform* applied to every value.

        Args:
            transform (Callable[[V], U]): Mapping function.

        Returns:
            MultiMap[K, U]: Transformed MultiMap.
        """
        return MultiMap({k: [transform(v) for v in vs] for k, vs in self._data.items()})

    def filter_keys(self, predicate: Callable[[K], bool]) -> "MultiMap[K, V]":
        """Return a new MultiMap keeping only keys that satisfy *predicate*."""
        return MultiMap({k: list(vs) for k, vs in self._data.items() if predicate(k)})

    def filter_values(self, predicate: Callable[[V], bool]) -> "MultiMap[K, V]":
        """
        Return a new MultiMap keeping only values that satisfy *predicate*.
        Keys with no remaining values are omitted.
        """
        result: Dict[K, List[V]] = {}
        for k, vs in self._data.items():
            filtered = [v for v in vs if predicate(v)]
            if filtered:
                result[k] = filtered
        return MultiMap(result)

    def for_each(self, action: Callable[[K, V], None]) -> "MultiMap[K, V]":
        """
        Execute *action(key, value)* for every (key, value) association.

        Args:
            action (Callable[[K, V], None]): Side-effecting function.

        Returns:
            MultiMap[K, V]: self
        """
        for k, vs in self._data.items():
            for v in vs:
                action(k, v)
        return self

    def to_dict(self) -> Dict[K, List[V]]:
        """Return a plain ``dict`` copy mapping each key to its value list."""
        return {k: list(vs) for k, vs in self._data.items()}

    # ------------------------------------------------------------------
    # Stream interop
    # ------------------------------------------------------------------

    def stream_entries(self) -> "Stream[Tuple[K, V]]":
        """Return a Stream over flat (key, value) pairs."""
        from nestifypy.collections.stream import Stream
        return Stream(self.flat_entries())

    def stream_keys(self) -> "Stream[K]":
        """Return a Stream over distinct keys."""
        from nestifypy.collections.stream import Stream
        return Stream(list(self._data.keys()))

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[K]:
        return iter(self._data)

    def __len__(self) -> int:
        return self.key_count()

    def __contains__(self, key: Any) -> bool:
        return key in self._data

    def __getitem__(self, key: K) -> List[V]:
        return self.get(key)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MultiMap):
            return self._data == other._data
        return NotImplemented

    def __repr__(self) -> str:
        return f"MultiMap({self._data!r})"


if TYPE_CHECKING:
    from nestifypy.collections.stream import Stream
