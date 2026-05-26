"""
nestifypy.collections.stack
------------------------
A fluent LIFO stack implementation.

This module provides a `Stack` class that wraps Python's built-in `list`
to offer a Last-In-First-Out (LIFO) data structure. It features an
object-oriented API with support for method chaining.
"""

from __future__ import annotations

from typing import Any, Generic, Iterable, Iterator, List, Optional, TypeVar

T = TypeVar("T")

class Stack(Generic[T]):
    """
    A LIFO (Last-In-First-Out) stack wrapping Python's list.

    Provides standard stack operations (push, pop, peek) while allowing
    method chaining for fluent data manipulation. The end of the underlying
    list represents the top of the stack.
    """

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        """
        Initialize a new Stack.

        Args:
            items (Optional[Iterable[T]]): An iterable of elements to populate
                the stack initially. The elements are pushed in iteration order,
                so the last element yielded becomes the top of the stack.
                If None, an empty stack is created. Defaults to None.
        """
        self._data: List[T] = list(items) if items is not None else []

    def push(self, item: T) -> Stack[T]:
        """
        Push an item onto the top of the stack.

        Args:
            item (T): The item to add to the stack.

        Returns:
            Stack[T]: The current Stack instance to allow method chaining.
        """
        self._data.append(item)
        return self

    def pop(self) -> T:
        """
        Remove and return the item at the top of the stack.

        Raises:
            IndexError: If the stack is empty when pop is called.

        Returns:
            T: The item that was at the top of the stack.
        """
        if not self._data:
            raise IndexError("pop from empty Stack")
        return self._data.pop()

    def peek(self) -> Optional[T]:
        """
        Return the item at the top of the stack without removing it.

        Returns:
            Optional[T]: The item at the top of the stack, or None if the stack is empty.
        """
        return self._data[-1] if self._data else None

    def is_empty(self) -> bool:
        """
        Check if the stack has no items.

        Returns:
            bool: True if the stack is empty, False otherwise.
        """
        return len(self._data) == 0

    def size(self) -> int:
        """
        Get the total number of items currently in the stack.

        Returns:
            int: The size of the stack.
        """
        return len(self._data)

    def clear(self) -> Stack[T]:
        """
        Remove all items from the stack.

        Returns:
            Stack[T]: The current Stack instance to allow method chaining.
        """
        self._data.clear()
        return self

    def to_list(self) -> List[T]:
        """
        Convert the stack into a standard list.

        Returns:
            List[T]: A copy of the underlying items, ordered from bottom to top.
        """
        return list(self._data)

    def __iter__(self) -> Iterator[T]:
        """
        Iterate over the items in the stack from bottom to top.

        Returns:
            Iterator[T]: An iterator over the stack's elements.
        """
        return iter(self._data)

    def __len__(self) -> int:
        """
        Get the number of items in the stack (allows `len(stack)`).

        Returns:
            int: The size of the stack.
        """
        return len(self._data)

    def __contains__(self, item: Any) -> bool:
        """
        Check if an item is in the stack (allows `item in stack`).

        Args:
            item (Any): The item to check for.

        Returns:
            bool: True if the item exists in the stack, False otherwise.
        """
        return item in self._data

    def __repr__(self) -> str:
        """
        Get the string representation of the Stack.

        Returns:
            str: A string showing the class name and its elements from bottom to top.
        """
        return f"Stack({self._data})"