"""
nestifypy.collections.ordered_set
------------------------------
A fluent insertion-ordered set.

This module provides an `OrderedSet` class that guarantees the preservation of
insertion order, leveraging the built-in dictionary ordering introduced in Python 3.7.
It offers a fluent API for easy method chaining.
"""

from __future__ import annotations

from typing import Any, Generic, Iterable, Iterator, Optional, TypeVar

T = TypeVar("T")

class OrderedSet(Generic[T]):
    """
    An insertion-ordered set based on Python's guaranteed dict ordering.

    Provides a collection of unique elements that remembers the order in which
    elements were added, while offering a chainable API.
    """

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        """
        Initialize a new OrderedSet.

        Args:
            items (Optional[Iterable[T]]): An iterable of elements to populate
                the set initially. If None, an empty set is created. Defaults to None.
        """
        # dict.fromkeys preserves insertion order (Python 3.7+)
        self._data: dict[T, None] = dict.fromkeys(items) if items is not None else {}

    def add(self, item: T) -> OrderedSet[T]:
        """
        Add an item to the set.

        If the item is already present, its position in the insertion order remains unchanged.

        Args:
            item (T): The item to add.

        Returns:
            OrderedSet[T]: The current OrderedSet instance to allow method chaining.
        """
        self._data[item] = None
        return self

    def remove(self, item: T) -> OrderedSet[T]:
        """
        Remove an item from the set. Does nothing if the item is not found.

        Args:
            item (T): The item to remove.

        Returns:
            OrderedSet[T]: The current OrderedSet instance to allow method chaining.
        """
        self._data.pop(item, None)
        return self

    def contains(self, item: T) -> bool:
        """
        Check if the set contains a specific item.

        Args:
            item (T): The item to check for.

        Returns:
            bool: True if the item exists in the set, False otherwise.
        """
        return item in self._data

    def is_empty(self) -> bool:
        """
        Check if the set has no elements.

        Returns:
            bool: True if the set is empty, False otherwise.
        """
        return len(self._data) == 0

    def size(self) -> int:
        """
        Get the total number of unique items in the set.

        Returns:
            int: The size of the set.
        """
        return len(self._data)

    def clear(self) -> OrderedSet[T]:
        """
        Remove all items from the set.

        Returns:
            OrderedSet[T]: The current OrderedSet instance to allow method chaining.
        """
        self._data.clear()
        return self

    def union(self, other: Iterable[T]) -> OrderedSet[T]:
        """
        Create a new OrderedSet containing all elements from both this set and another iterable.

        Elements from this set appear first, followed by new elements from `other`.

        Args:
            other (Iterable[T]): The collection of elements to unite with this set.

        Returns:
            OrderedSet[T]: A new OrderedSet containing the union of both collections.
        """
        result = OrderedSet(self._data.keys())
        for item in other:
            result.add(item)
        return result

    def intersection(self, other: Iterable[T]) -> OrderedSet[T]:
        """
        Create a new OrderedSet containing only the elements common to both collections.

        The insertion order of the resulting set matches the order of this set.

        Args:
            other (Iterable[T]): The collection of elements to intersect with.

        Returns:
            OrderedSet[T]: A new OrderedSet containing the common elements.
        """
        other_set = set(other)
        result = OrderedSet(item for item in self._data if item in other_set)
        return result

    def to_list(self) -> list[T]:
        """
        Convert the OrderedSet into a standard list.

        Returns:
            list[T]: A list of the set's items, preserving their insertion order.
        """
        return list(self._data.keys())

    def __iter__(self) -> Iterator[T]:
        """
        Iterate over the elements of the set in insertion order.

        Returns:
            Iterator[T]: An iterator over the set's elements.
        """
        return iter(self._data.keys())

    def __len__(self) -> int:
        """
        Get the number of items in the set (allows `len(ordered_set)`).

        Returns:
            int: The size of the set.
        """
        return len(self._data)

    def __contains__(self, item: Any) -> bool:
        """
        Check if an item is in the set (allows `item in ordered_set`).

        Args:
            item (Any): The item to check for.

        Returns:
            bool: True if the item exists, False otherwise.
        """
        return item in self._data

    def __repr__(self) -> str:
        """
        Get the string representation of the OrderedSet.

        Returns:
            str: A string showing the class name and its elements.
        """
        return f"OrderedSet({list(self._data.keys())})"