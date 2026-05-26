"""
nestifypy.collections.queue
------------------------
A fluent FIFO queue implementation.

This module provides a `Queue` class that wraps Python's highly optimized
`collections.deque` to offer a First-In-First-Out (FIFO) data structure
with a chainable, object-oriented API.
"""

from __future__ import annotations

import collections
from typing import Any, Generic, Iterable, Iterator, Optional, TypeVar

T = TypeVar("T")

class Queue(Generic[T]):
    """
    A FIFO (First-In-First-Out) queue wrapping Python's collections.deque.

    Provides an easy-to-use interface for queue operations while allowing
    method chaining for fluent data manipulation.
    """

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        """
        Initialize a new Queue.

        Args:
            items (Optional[Iterable[T]]): An iterable of elements to populate
                the queue initially. The first element of the iterable becomes
                the front of the queue. If None, an empty queue is created. Defaults to None.
        """
        self._data: collections.deque[T] = collections.deque(items if items is not None else [])

    def enqueue(self, item: T) -> Queue[T]:
        """
        Add an item to the back of the queue.

        Args:
            item (T): The item to add to the queue.

        Returns:
            Queue[T]: The current Queue instance to allow method chaining.
        """
        self._data.append(item)
        return self

    def dequeue(self) -> T:
        """
        Remove and return the item at the front of the queue.

        Raises:
            IndexError: If the queue is empty when dequeue is called.

        Returns:
            T: The item that was at the front of the queue.
        """
        if not self._data:
            raise IndexError("dequeue from empty Queue")
        return self._data.popleft()

    def peek(self) -> Optional[T]:
        """
        Return the item at the front of the queue without removing it.

        Returns:
            Optional[T]: The item at the front of the queue, or None if the queue is empty.
        """
        return self._data[0] if self._data else None

    def is_empty(self) -> bool:
        """
        Check if the queue has no items.

        Returns:
            bool: True if the queue is empty, False otherwise.
        """
        return len(self._data) == 0

    def size(self) -> int:
        """
        Get the total number of items currently in the queue.

        Returns:
            int: The size of the queue.
        """
        return len(self._data)

    def clear(self) -> Queue[T]:
        """
        Remove all items from the queue.

        Returns:
            Queue[T]: The current Queue instance to allow method chaining.
        """
        self._data.clear()
        return self

    def to_list(self) -> list[T]:
        """
        Convert the queue into a standard list.

        Returns:
            list[T]: A copy of the underlying items, ordered from front to back.
        """
        return list(self._data)

    def __iter__(self) -> Iterator[T]:
        """
        Iterate over the items in the queue from front to back.

        Returns:
            Iterator[T]: An iterator over the queue's elements.
        """
        return iter(self._data)

    def __len__(self) -> int:
        """
        Get the number of items in the queue (allows `len(queue)`).

        Returns:
            int: The size of the queue.
        """
        return len(self._data)

    def __contains__(self, item: Any) -> bool:
        """
        Check if an item is in the queue (allows `item in queue`).

        Args:
            item (Any): The item to check for.

        Returns:
            bool: True if the item exists in the queue, False otherwise.
        """
        return item in self._data

    def __repr__(self) -> str:
        """
        Get the string representation of the Queue.

        Returns:
            str: A string showing the class name and its elements from front to back.
        """
        return f"Queue({list(self._data)})"