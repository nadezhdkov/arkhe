"""
nestifypy.collections.hash_map
---------------------------
A fluent wrapper around Python's dictionary.

This module provides a `HashMap` class that encapsulates a standard Python dictionary
while offering a fluent interface (method chaining) and utility methods commonly
found in other programming languages like Java or Kotlin.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Generic, Iterable, Iterator, List, Optional, Tuple, TypeVar

K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")

class HashMap(Generic[K, V]):
    """
    A fluent wrapper around Python's dict.

    Provides an object-oriented, chainable API for dictionary manipulation.
    """

    def __init__(self, initial_data: Optional[Dict[K, V]] = None) -> None:
        """
        Initialize a new HashMap.

        Args:
            initial_data (Optional[Dict[K, V]]): A dictionary to initialize the
                map with. If None, an empty map is created. Defaults to None.
        """
        self._data: Dict[K, V] = initial_data.copy() if initial_data is not None else {}

    def put(self, key: K, value: V) -> HashMap[K, V]:
        """
        Add or update a key-value pair in the map.

        Args:
            key (K): The key to insert or update.
            value (V): The value associated with the key.

        Returns:
            HashMap[K, V]: The current HashMap instance to allow method chaining.
        """
        self._data[key] = value
        return self

    def get(self, key: K) -> Optional[V]:
        """
        Get the value for a given key.

        Args:
            key (K): The key to look up.

        Returns:
            Optional[V]: The value associated with the key, or None if the key is not found.
        """
        return self._data.get(key)

    def get_or_default(self, key: K, default: V) -> V:
        """
        Get the value for a key, or a default value if the key does not exist.

        Args:
            key (K): The key to look up.
            default (V): The value to return if the key is missing.

        Returns:
            V: The found value, or the provided default.
        """
        return self._data.get(key, default)

    def remove(self, key: K) -> HashMap[K, V]:
        """
        Remove a key and its associated value from the map.

        Args:
            key (K): The key to remove.

        Returns:
            HashMap[K, V]: The current HashMap instance to allow method chaining.
        """
        self._data.pop(key, None)
        return self

    def contains_key(self, key: K) -> bool:
        """
        Check if the map contains the specified key.

        Args:
            key (K): The key to check for.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return key in self._data

    def contains_value(self, value: V) -> bool:
        """
        Check if the map contains the specified value.

        Args:
            value (V): The value to check for.

        Returns:
            bool: True if the value exists in the map, False otherwise.
        """
        return value in self._data.values()

    def is_empty(self) -> bool:
        """
        Check if the map contains no key-value pairs.

        Returns:
            bool: True if the map is empty, False otherwise.
        """
        return len(self._data) == 0

    def size(self) -> int:
        """
        Get the total number of key-value pairs in the map.

        Returns:
            int: The size of the map.
        """
        return len(self._data)

    def clear(self) -> HashMap[K, V]:
        """
        Remove all key-value pairs from the map.

        Returns:
            HashMap[K, V]: The current HashMap instance to allow method chaining.
        """
        self._data.clear()
        return self

    def keys(self) -> List[K]:
        """
        Retrieve all keys in the map.

        Returns:
            List[K]: A list containing all the keys.
        """
        return list(self._data.keys())

    def values(self) -> List[V]:
        """
        Retrieve all values in the map.

        Returns:
            List[V]: A list containing all the values.
        """
        return list(self._data.values())

    def entries(self) -> List[Tuple[K, V]]:
        """
        Retrieve all key-value pairs in the map.

        Returns:
            List[Tuple[K, V]]: A list of tuples, where each tuple is a (key, value) pair.
        """
        return list(self._data.items())

    def merge(self, other: Dict[K, V] | HashMap[K, V]) -> HashMap[K, V]:
        """
        Merge another dictionary or HashMap into a new HashMap.

        Note that this does not mutate the current HashMap, but returns a new one.

        Args:
            other (Dict[K, V] | HashMap[K, V]): The mapping object to merge from.

        Returns:
            HashMap[K, V]: A new HashMap containing the merged data.
        """
        result = HashMap(self._data)
        if isinstance(other, HashMap):
            result._data.update(other._data)
        else:
            result._data.update(other)
        return result

    def map_values(self, transform: Callable[[V], U]) -> HashMap[K, U]:
        """
        Create a new HashMap with the same keys, but with transformed values.

        Args:
            transform (Callable[[V], U]): A function that takes a value of type V
                and returns a new value of type U.

        Returns:
            HashMap[K, U]: A new HashMap with the transformed values.
        """
        return HashMap({k: transform(v) for k, v in self._data.items()})

    def for_each(self, action: Callable[[K, V], None]) -> HashMap[K, V]:
        """
        Apply a given action (function) to each key-value pair in the map.

        Args:
            action (Callable[[K, V], None]): A function to execute for each item.
                It takes a key and a value as arguments.

        Returns:
            HashMap[K, V]: The current HashMap instance to allow method chaining.
        """
        for k, v in self._data.items():
            action(k, v)
        return self

    def to_dict(self) -> Dict[K, V]:
        """
        Convert the HashMap back to a standard Python dictionary.

        Returns:
            Dict[K, V]: A shallow copy of the underlying dictionary.
        """
        return dict(self._data)

    def __iter__(self) -> Iterator[K]:
        """
        Iterate over the keys of the map.

        Returns:
            Iterator[K]: An iterator over the map's keys.
        """
        return iter(self._data)

    def __len__(self) -> int:
        """
        Get the number of items in the map (allows `len(hash_map)`).

        Returns:
            int: The size of the map.
        """
        return len(self._data)

    def __getitem__(self, key: K) -> V:
        """
        Get an item using square bracket notation (`hash_map[key]`).

        Args:
            key (K): The key to lookup.

        Raises:
            KeyError: If the key is not found in the map.

        Returns:
            V: The value associated with the key.
        """
        return self._data[key]

    def __setitem__(self, key: K, value: V) -> None:
        """
        Set an item using square bracket notation (`hash_map[key] = value`).

        Args:
            key (K): The key to insert or update.
            value (V): The value to store.
        """
        self._data[key] = value

    def __contains__(self, key: Any) -> bool:
        """
        Check if a key is in the map (allows `key in hash_map`).

        Args:
            key (Any): The key to check for.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return key in self._data

    def __repr__(self) -> str:
        """
        Get the string representation of the HashMap.

        Returns:
            str: A string showing the class name and the underlying dictionary.
        """
        return f"HashMap({self._data})"