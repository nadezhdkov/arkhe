"""
nestifypy.collections.linked_list
------------------------------
A fluent doubly-linked list implementation.

This module provides a `LinkedList` class that wraps Python's highly optimized
`collections.deque` to offer a doubly-linked list data structure. It features
an object-oriented API with support for method chaining and functional operations.
"""

from __future__ import annotations

import collections
from typing import Any, Callable, Generic, Iterable, Iterator, Optional, TypeVar

T = TypeVar("T")
U = TypeVar("U")

class LinkedList(Generic[T]):
    """
    A doubly-linked list wrapping Python's collections.deque.

    Provides efficient $O(1)$ operations for adding and removing elements from
    both ends, while offering a chainable API for fluent data manipulation.
    """

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        """
        Initialize a new LinkedList.

        Args:
            items (Optional[Iterable[T]]): An iterable of elements to populate
                the list initially. If None, an empty list is created. Defaults to None.
        """
        self._data: collections.deque[T] = collections.deque(items if items is not None else [])

    def add_first(self, item: T) -> LinkedList[T]:
        """
        Add an item to the beginning (left side) of the list.

        Args:
            item (T): The item to add.

        Returns:
            LinkedList[T]: The current LinkedList instance to allow method chaining.
        """
        self._data.appendleft(item)
        return self

    def add_last(self, item: T) -> LinkedList[T]:
        """
        Add an item to the end (right side) of the list.

        Args:
            item (T): The item to add.

        Returns:
            LinkedList[T]: The current LinkedList instance to allow method chaining.
        """
        self._data.append(item)
        return self

    def remove_first(self) -> T:
        """
        Remove and return the first item from the list.

        Raises:
            IndexError: If the list is empty when remove_first is called.

        Returns:
            T: The item that was at the beginning of the list.
        """
        if not self._data:
            raise IndexError("remove_first from empty LinkedList")
        return self._data.popleft()

    def remove_last(self) -> T:
        """
        Remove and return the last item from the list.

        Raises:
            IndexError: If the list is empty when remove_last is called.

        Returns:
            T: The item that was at the end of the list.
        """
        if not self._data:
            raise IndexError("remove_last from empty LinkedList")
        return self._data.pop()

    def peek_first(self) -> Optional[T]:
        """
        Return the first item of the list without removing it.

        Returns:
            Optional[T]: The first item, or None if the list is empty.
        """
        return self._data[0] if self._data else None

    def peek_last(self) -> Optional[T]:
        """
        Return the last item of the list without removing it.

        Returns:
            Optional[T]: The last item, or None if the list is empty.
        """
        return self._data[-1] if self._data else None

    def contains(self, item: T) -> bool:
        """
        Check if the list contains the specified item.

        Args:
            item (T): The item to check for.

        Returns:
            bool: True if the item exists in the list, False otherwise.
        """
        return item in self._data

    def is_empty(self) -> bool:
        """
        Check if the list has no elements.

        Returns:
            bool: True if the list is empty, False otherwise.
        """
        return len(self._data) == 0

    def size(self) -> int:
        """
        Get the total number of items currently in the list.

        Returns:
            int: The size of the list.
        """
        return len(self._data)

    def clear(self) -> LinkedList[T]:
        """
        Remove all items from the list.

        Returns:
            LinkedList[T]: The current LinkedList instance to allow method chaining.
        """
        self._data.clear()
        return self

    def filter(self, predicate: Callable[[T], bool]) -> LinkedList[T]:
        """
        Create a new LinkedList containing only items that match the given predicate.

        Args:
            predicate (Callable[[T], bool]): A function that evaluates each item and
                returns True to keep the item or False to drop it.

        Returns:
            LinkedList[T]: A new LinkedList with the filtered items.
        """
        return LinkedList([item for item in self._data if predicate(item)])

    def map(self, transform: Callable[[T], U]) -> LinkedList[U]:
        """
        Create a new LinkedList with the results of applying the transform function
        to each item.

        Args:
            transform (Callable[[T], U]): A function that takes an item of type T
                and returns a new value of type U.

        Returns:
            LinkedList[U]: A new LinkedList containing the transformed items.
        """
        return LinkedList([transform(item) for item in self._data])

    def to_list(self) -> list[T]:
        """
        Convert the LinkedList into a standard Python list.

        Returns:
            list[T]: A copy of the underlying items, ordered from first to last.
        """
        return list(self._data)

    def __iter__(self) -> Iterator[T]:
        """
        Iterate over the items in the list from first to last.

        Returns:
            Iterator[T]: An iterator over the list's elements.
        """
        return iter(self._data)

    def __len__(self) -> int:
        """
        Get the number of items in the list (allows `len(linked_list)`).

        Returns:
            int: The size of the list.
        """
        return len(self._data)

    def __contains__(self, item: Any) -> bool:
        """
        Check if an item is in the list (allows `item in linked_list`).

        Args:
            item (Any): The item to check for.

        Returns:
            bool: True if the item exists in the list, False otherwise.
        """
        return item in self._data

    def __repr__(self) -> str:
        """
        Get the string representation of the LinkedList.

        Returns:
            str: A string showing the class name and its elements.
        """
        return f"LinkedList({list(self._data)})"