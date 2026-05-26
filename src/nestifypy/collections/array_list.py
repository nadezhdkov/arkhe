"""
nestifypy.collections.array_list
-----------------------------
A fluent, Java-inspired wrapper around Python's built-in list.

This module provides an `ArrayList` class that encapsulates a standard Python
list while offering an object-oriented, chainable API and functional
programming utilities like `map`, `filter`, and `for_each`.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Iterable, Iterator, List, Optional, TypeVar

T = TypeVar("T")
U = TypeVar("U")

class ArrayList(Generic[T]):
    """
    A dynamic array implementation wrapping Python's list,
    providing a fluent, chainable API.
    """

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        """
        Initialize a new ArrayList.

        Args:
            items (Optional[Iterable[T]]): An iterable of elements to populate
                the list initially. If None, an empty list is created. Defaults to None.
        """
        self._data: List[T] = list(items) if items is not None else []

    def add(self, item: T) -> ArrayList[T]:
        """
        Add an item to the end of the list.

        This method mutates the list in place.

        Args:
            item (T): The item to add.

        Returns:
            ArrayList[T]: The current ArrayList instance to allow method chaining.
        """
        self._data.append(item)
        return self

    def remove(self, item: T) -> ArrayList[T]:
        """
        Remove the first occurrence of an item from the list.

        This method mutates the list in place. If the item is not found,
        the list remains unchanged.

        Args:
            item (T): The item to remove.

        Returns:
            ArrayList[T]: The current ArrayList instance to allow method chaining.
        """
        if item in self._data:
            self._data.remove(item)
        return self

    def remove_at(self, index: int) -> T:
        """
        Remove and return the item at the specified index.

        Args:
            index (int): The index of the item to remove.

        Raises:
            IndexError: If the index is out of range.

        Returns:
            T: The item that was removed from the list.
        """
        return self._data.pop(index)

    def contains(self, item: T) -> bool:
        """
        Check if the list contains the specified item.

        Args:
            item (T): The item to check for.

        Returns:
            bool: True if the item exists in the list, False otherwise.
        """
        return item in self._data

    def first(self) -> Optional[T]:
        """
        Retrieve the first item in the list.

        Returns:
            Optional[T]: The first item, or None if the list is empty.
        """
        return self._data[0] if self._data else None

    def last(self) -> Optional[T]:
        """
        Retrieve the last item in the list.

        Returns:
            Optional[T]: The last item, or None if the list is empty.
        """
        return self._data[-1] if self._data else None

    def is_empty(self) -> bool:
        """
        Check if the list has no elements.

        Returns:
            bool: True if the list is empty, False otherwise.
        """
        return len(self._data) == 0

    def size(self) -> int:
        """
        Get the total number of items in the list.

        Returns:
            int: The size of the list.
        """
        return len(self._data)

    def clear(self) -> ArrayList[T]:
        """
        Remove all items from the list.

        Returns:
            ArrayList[T]: The current ArrayList instance to allow method chaining.
        """
        self._data.clear()
        return self

    def sort(self, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> ArrayList[T]:
        """
        Sort the list in place.

        Args:
            key (Optional[Callable[[T], Any]]): A function that serves as a key for the
                sort comparison. Defaults to None.
            reverse (bool): If True, the list elements are sorted as if each comparison
                were reversed (descending). Defaults to False.

        Returns:
            ArrayList[T]: The current sorted ArrayList instance to allow method chaining.
        """
        self._data.sort(key=key, reverse=reverse)
        return self

    def filter(self, predicate: Callable[[T], bool]) -> ArrayList[T]:
        """
        Create a new ArrayList containing only items that match the given predicate.

        Args:
            predicate (Callable[[T], bool]): A function that evaluates each item and
                returns True to keep the item or False to drop it.

        Returns:
            ArrayList[T]: A new ArrayList with the filtered items.
        """
        return ArrayList([item for item in self._data if predicate(item)])

    def map(self, transform: Callable[[T], U]) -> ArrayList[U]:
        """
        Create a new ArrayList with the results of applying the transform function
        to each item.

        Args:
            transform (Callable[[T], U]): A function that takes an item of type T
                and returns a new value of type U.

        Returns:
            ArrayList[U]: A new ArrayList containing the transformed items.
        """
        return ArrayList([transform(item) for item in self._data])

    def for_each(self, action: Callable[[T], None]) -> ArrayList[T]:
        """
        Apply a given action (function) to each item in the list.

        Args:
            action (Callable[[T], None]): A function to execute for each item.

        Returns:
            ArrayList[T]: The current ArrayList instance to allow method chaining.
        """
        for item in self._data:
            action(item)
        return self

    def to_list(self) -> List[T]:
        """
        Convert the ArrayList back into a standard Python list.

        Returns:
            List[T]: A shallow copy of the underlying list.
        """
        return list(self._data)

    def __iter__(self) -> Iterator[T]:
        """
        Iterate over the elements in the list.

        Returns:
            Iterator[T]: An iterator over the list's elements.
        """
        return iter(self._data)

    def __len__(self) -> int:
        """
        Get the number of items in the list (allows `len(array_list)`).

        Returns:
            int: The size of the list.
        """
        return len(self._data)

    def __getitem__(self, index: int) -> T:
        """
        Get an item using square bracket notation (`array_list[index]`).

        Args:
            index (int): The index of the item to retrieve.

        Raises:
            IndexError: If the index is out of bounds.

        Returns:
            T: The item at the specified index.
        """
        return self._data[index]

    def __setitem__(self, index: int, value: T) -> None:
        """
        Set an item using square bracket notation (`array_list[index] = value`).

        Args:
            index (int): The index where the value should be set.
            value (T): The value to store at the given index.

        Raises:
            IndexError: If the index is out of bounds.
        """
        self._data[index] = value

    def __contains__(self, item: Any) -> bool:
        """
        Check if an item is in the list (allows `item in array_list`).

        Args:
            item (Any): The item to check for.

        Returns:
            bool: True if the item exists, False otherwise.
        """
        return item in self._data

    def __repr__(self) -> str:
        """
        Get the string representation of the ArrayList.

        Returns:
            str: A string showing the class name and its underlying list.
        """
        return f"ArrayList({self._data})"