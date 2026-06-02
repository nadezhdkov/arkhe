"""
nestifypy.collections.bi_map
-----------------------------
A bidirectional map (BiMap) that maintains a one-to-one mapping between
keys and values, allowing O(1) lookup in both directions.

Unlike a regular dict, a BiMap enforces uniqueness on *both* keys and
values: assigning a value that already exists removes the old key that
held it.

Example::

    from nestifypy.collections import BiMap

    roles = BiMap()
    roles.put("ADMIN", 1).put("MOD", 2).put("USER", 3)

    roles.get("ADMIN")    # 1
    roles.get_key(2)      # "MOD"
    roles.inverse()       # BiMap({1: "ADMIN", 2: "MOD", 3: "USER"})
"""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
)

K = TypeVar("K")
V = TypeVar("V")


class BiMap(Generic[K, V]):
    """
    A bidirectional map that enforces a one-to-one relationship between
    keys and values.

    Both keys and values must be **hashable**.

    Mutation methods return ``self`` for chaining.
    """

    __slots__ = ("_forward", "_inverse")

    def __init__(self, initial_data: Optional[Dict[K, V]] = None) -> None:
        """
        Initialize a new BiMap.

        Args:
            initial_data (Optional[Dict[K, V]]): Seed entries. Must be a
                one-to-one mapping (no duplicate values); raises ``ValueError``
                if violated.
        """
        self._forward: Dict[K, V] = {}
        self._inverse: Dict[V, K] = {}
        if initial_data:
            for k, v in initial_data.items():
                self.put(k, v)

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, **kwargs: V) -> "BiMap[str, V]":
        """Create a BiMap from keyword arguments (keys become strings)."""
        return cls(kwargs)  # type: ignore[arg-type]

    @classmethod
    def from_entries(cls, entries: Iterable[Tuple[K, V]]) -> "BiMap[K, V]":
        """Create a BiMap from an iterable of (key, value) tuples."""
        return cls(dict(entries))

    @classmethod
    def empty(cls) -> "BiMap[K, V]":
        """Create an empty BiMap."""
        return cls()

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def put(self, key: K, value: V) -> "BiMap[K, V]":
        """
        Insert or replace the mapping ``key → value``.

        If *key* already exists its old value is removed from the inverse map.
        If *value* already exists its old key is removed from the forward map,
        maintaining the one-to-one invariant.

        Args:
            key (K): The key.
            value (V): The value (must be hashable).

        Returns:
            BiMap[K, V]: self
        """
        # Remove stale entries to preserve bijectivity
        if key in self._forward:
            del self._inverse[self._forward[key]]
        if value in self._inverse:
            del self._forward[self._inverse[value]]
        self._forward[key] = value
        self._inverse[value] = key
        return self

    def remove(self, key: K) -> "BiMap[K, V]":
        """
        Remove the entry for *key*; no-op if not present.

        Args:
            key (K): Key to remove.

        Returns:
            BiMap[K, V]: self
        """
        if key in self._forward:
            del self._inverse[self._forward[key]]
            del self._forward[key]
        return self

    def remove_value(self, value: V) -> "BiMap[K, V]":
        """
        Remove the entry whose value is *value*; no-op if not present.

        Args:
            value (V): Value to remove.

        Returns:
            BiMap[K, V]: self
        """
        if value in self._inverse:
            del self._forward[self._inverse[value]]
            del self._inverse[value]
        return self

    def clear(self) -> "BiMap[K, V]":
        """Remove all entries."""
        self._forward.clear()
        self._inverse.clear()
        return self

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, key: K) -> Optional[V]:
        """
        Return the value for *key*, or ``None`` if not found.

        Args:
            key (K): Key to look up.

        Returns:
            Optional[V]: Associated value or None.
        """
        return self._forward.get(key)

    def get_or(self, key: K, default: V) -> V:
        """Return the value for *key*, or *default* if not found."""
        return self._forward.get(key, default)

    def get_key(self, value: V) -> Optional[K]:
        """
        Return the key associated with *value*, or ``None`` if not found.

        Args:
            value (V): Value to look up.

        Returns:
            Optional[K]: Associated key or None.
        """
        return self._inverse.get(value)

    def get_key_or(self, value: V, default: K) -> K:
        """Return the key for *value*, or *default* if not found."""
        return self._inverse.get(value, default)

    def contains_key(self, key: K) -> bool:
        """Return ``True`` if *key* exists in the map."""
        return key in self._forward

    def contains_value(self, value: V) -> bool:
        """Return ``True`` if *value* exists in the map."""
        return value in self._inverse

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Return ``True`` if the map has no entries."""
        return not self._forward

    def size(self) -> int:
        """Return the number of entries."""
        return len(self._forward)

    def keys(self) -> List[K]:
        """Return all keys as a list."""
        return list(self._forward.keys())

    def values(self) -> List[V]:
        """Return all values as a list."""
        return list(self._forward.values())

    def entries(self) -> List[Tuple[K, V]]:
        """Return all (key, value) pairs as a list."""
        return list(self._forward.items())

    # ------------------------------------------------------------------
    # Views & transforms
    # ------------------------------------------------------------------

    def inverse(self) -> "BiMap[V, K]":
        """
        Return a new BiMap with keys and values swapped.

        Returns:
            BiMap[V, K]: Inverted BiMap.
        """
        result: BiMap[V, K] = BiMap.__new__(BiMap)
        result._forward = dict(self._inverse)
        result._inverse = dict(self._forward)
        return result

    def to_dict(self) -> Dict[K, V]:
        """Return a plain ``dict`` copy of the forward mapping."""
        return dict(self._forward)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[K]:
        return iter(self._forward)

    def __len__(self) -> int:
        return len(self._forward)

    def __contains__(self, key: Any) -> bool:
        return key in self._forward

    def __getitem__(self, key: K) -> V:
        return self._forward[key]

    def __setitem__(self, key: K, value: V) -> None:
        self.put(key, value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BiMap):
            return self._forward == other._forward
        if isinstance(other, dict):
            return self._forward == other
        return NotImplemented

    def __repr__(self) -> str:
        return f"BiMap({self._forward!r})"
