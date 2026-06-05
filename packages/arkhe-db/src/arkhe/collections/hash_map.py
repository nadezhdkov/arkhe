"""
arkhe.collections.hash_map
--------------------------------
A fluent wrapper around Python's ``dict`` with functional programming
utilities and :class:`~arkhe.collections.stream.Stream` interoperability.

Example::

    from arkhe.collections import HashMap

    scores = (
        HashMap({"alice": 80, "bob": 95, "carol": 70})
        .put("dave", 88)
        .filter_values(lambda v: v >= 80)
        .map_values(lambda v: f"{v}%")
    )
    # HashMap({'alice': '80%', 'bob': '95%', 'dave': '88%'})
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

K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")
R = TypeVar("R")


class HashMap(Generic[K, V]):
    """
    A fluent ``dict`` wrapper with functional transformations and chaining.
    """

    __slots__ = ("_data",)

    def __init__(self, initial_data: Optional[Dict[K, V]] = None) -> None:
        self._data: Dict[K, V] = initial_data.copy() if initial_data is not None else {}

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, **kwargs: V) -> "HashMap[str, V]":
        """Create a HashMap from keyword arguments (keys become strings)."""
        return cls(kwargs)  # type: ignore[arg-type]

    @classmethod
    def from_entries(cls, entries: Iterable[Tuple[K, V]]) -> "HashMap[K, V]":
        """Create a HashMap from an iterable of (key, value) tuples."""
        return cls(dict(entries))

    @classmethod
    def empty(cls) -> "HashMap[K, V]":
        return cls()

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def put(self, key: K, value: V) -> "HashMap[K, V]":
        """Add or update a key-value pair."""
        self._data[key] = value
        return self

    def put_if_absent(self, key: K, value: V) -> "HashMap[K, V]":
        """Add *key* → *value* only if *key* is not already present."""
        self._data.setdefault(key, value)
        return self

    def put_all(self, other: "Dict[K, V] | HashMap[K, V]") -> "HashMap[K, V]":
        """Merge all entries from *other* into this map (last-write-wins)."""
        if isinstance(other, HashMap):
            self._data.update(other._data)
        else:
            self._data.update(other)
        return self

    def remove(self, key: K) -> "HashMap[K, V]":
        """Remove *key* from the map; no-op if not present."""
        self._data.pop(key, None)
        return self

    def remove_if(self, predicate: Callable[[K, V], bool]) -> "HashMap[K, V]":
        """Remove all entries for which *predicate(key, value)* is True."""
        self._data = {k: v for k, v in self._data.items() if not predicate(k, v)}
        return self

    def clear(self) -> "HashMap[K, V]":
        self._data.clear()
        return self

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def get(self, key: K) -> Optional[V]:
        """Return the value for *key*, or ``None`` if not found."""
        return self._data.get(key)

    def get_or(self, key: K, default: V) -> V:
        """Return the value for *key*, or *default* if not found."""
        return self._data.get(key, default)

    def get_or_else(self, key: K, supplier: Callable[[], V]) -> V:
        """Return the value for *key*, or call *supplier* lazily."""
        return self._data[key] if key in self._data else supplier()

    def get_or_put(self, key: K, supplier: Callable[[], V]) -> V:
        """Return the value for *key*; if absent, insert and return *supplier()*."""
        if key not in self._data:
            self._data[key] = supplier()
        return self._data[key]

    def contains_key(self, key: K) -> bool:
        return key in self._data

    def contains_value(self, value: V) -> bool:
        return value in self._data.values()

    def is_empty(self) -> bool:
        return not self._data

    def size(self) -> int:
        return len(self._data)

    # ------------------------------------------------------------------
    # Bulk retrieval
    # ------------------------------------------------------------------

    def keys(self) -> List[K]:
        return list(self._data.keys())

    def values(self) -> List[V]:
        return list(self._data.values())

    def entries(self) -> List[Tuple[K, V]]:
        return list(self._data.items())

    # ------------------------------------------------------------------
    # Transformation — new instances
    # ------------------------------------------------------------------

    def map_values(self, transform: Callable[[V], U]) -> "HashMap[K, U]":
        """Return a new HashMap with the same keys and transformed values."""
        return HashMap({k: transform(v) for k, v in self._data.items()})

    def map_keys(self, transform: Callable[[K], Any]) -> "HashMap[Any, V]":
        """Return a new HashMap with transformed keys and the same values (last-write-wins on collision)."""
        return HashMap({transform(k): v for k, v in self._data.items()})

    def map_entries(self, transform: Callable[[K, V], Tuple[Any, Any]]) -> "HashMap[Any, Any]":
        """Apply *transform(key, value) → (new_key, new_value)* to every entry."""
        return HashMap(dict(transform(k, v) for k, v in self._data.items()))

    def filter_keys(self, predicate: Callable[[K], bool]) -> "HashMap[K, V]":
        """Return a new HashMap with only the entries whose key satisfies *predicate*."""
        return HashMap({k: v for k, v in self._data.items() if predicate(k)})

    def filter_values(self, predicate: Callable[[V], bool]) -> "HashMap[K, V]":
        """Return a new HashMap with only the entries whose value satisfies *predicate*."""
        return HashMap({k: v for k, v in self._data.items() if predicate(v)})

    def filter_entries(self, predicate: Callable[[K, V], bool]) -> "HashMap[K, V]":
        """Return a new HashMap keeping entries where *predicate(key, value)* is True."""
        return HashMap({k: v for k, v in self._data.items() if predicate(k, v)})

    def merge(self, other: "Dict[K, V] | HashMap[K, V]") -> "HashMap[K, V]":
        """Return a **new** HashMap merging this and *other* (other wins on conflicts)."""
        result = HashMap(self._data)
        result.put_all(other)
        return result

    def group_values_by(self, key_fn: Callable[[V], Any]) -> "HashMap[Any, List[V]]":
        """Group values by the result of *key_fn* applied to each value."""
        groups: Dict[Any, List[V]] = {}
        for v in self._data.values():
            groups.setdefault(key_fn(v), []).append(v)
        return HashMap(groups)

    def invert(self) -> "HashMap[V, K]":
        """Return a new HashMap with keys and values swapped (last-write-wins on collision)."""
        return HashMap({v: k for k, v in self._data.items()})

    def reduce_values(self, fn: Callable[[R, V], R], initial: R) -> R:
        """Fold the map's values using *fn*."""
        return functools.reduce(fn, self._data.values(), initial)

    def for_each(self, action: Callable[[K, V], None]) -> "HashMap[K, V]":
        """Execute *action(key, value)* for each entry; supports chaining."""
        for k, v in self._data.items():
            action(k, v)
        return self

    # ------------------------------------------------------------------
    # Stream interop
    # ------------------------------------------------------------------

    def stream_keys(self) -> "Stream[K]":
        """Return a Stream over the map's keys."""
        from arkhe.collections.stream import Stream
        return Stream(list(self._data.keys()))

    def stream_values(self) -> "Stream[V]":
        """Return a Stream over the map's values."""
        from arkhe.collections.stream import Stream
        return Stream(list(self._data.values()))

    def stream_entries(self) -> "Stream[Tuple[K, V]]":
        """Return a Stream over (key, value) tuples."""
        from arkhe.collections.stream import Stream
        return Stream(list(self._data.items()))

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[K, V]:
        return dict(self._data)

    # ------------------------------------------------------------------
    # Operator overloads
    # ------------------------------------------------------------------

    def __or__(self, other: "HashMap[K, V]") -> "HashMap[K, V]":
        """Support ``map1 | map2`` (merge, other wins)."""
        return self.merge(other)

    def __ior__(self, other: "Dict[K, V] | HashMap[K, V]") -> "HashMap[K, V]":
        """Support ``map |= other`` (in-place merge)."""
        return self.put_all(other)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[K]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __setitem__(self, key: K, value: V) -> None:
        self._data[key] = value

    def __contains__(self, key: Any) -> bool:
        return key in self._data

    def __eq__(self, other: object) -> bool:
        if isinstance(other, HashMap):
            return self._data == other._data
        if isinstance(other, dict):
            return self._data == other
        return NotImplemented

    def __repr__(self) -> str:
        return f"HashMap({self._data!r})"


if TYPE_CHECKING:
    from arkhe.collections.stream import Stream
