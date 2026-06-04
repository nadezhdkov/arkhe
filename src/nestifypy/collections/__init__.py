"""
nestifypy.collections
----------------------
Fluent, Java-inspired data structures and functional utilities for Python.

Quick start::

    from nestifypy.collections import (
        ArrayList, LinkedList, Stack, Queue,
        OrderedSet, HashMap, BiMap, MultiMap,
        PriorityQueue, CircularBuffer,
        Stream, Optional, Result,
    )

    # Fluent pipeline
    result = (
        Stream.range(1, 11)
        .filter(lambda n: n % 2 == 0)
        .map(lambda n: n ** 2)
        .to_list()
    )  # [4, 16, 36, 64, 100]

    # Safe None handling
    value = Optional.of_nullable(some_dict.get("key")).map(str.upper).get_or("default")

    # Explicit error handling
    parsed = Result.of(lambda: int(user_input)).get_or(0)

    # Bidirectional map
    roles = BiMap().put("ADMIN", 1).put("MOD", 2)
    roles.get_key(1)   # "ADMIN"

    # Multi-value map
    params = MultiMap().put("color", "red").put("color", "blue")
    params.get("color")  # ["red", "blue"]

    # Priority queue
    tasks = PriorityQueue()
    tasks.add("Low", priority=10).add("High", priority=1)
    tasks.poll()  # "High"

    # Circular buffer
    logs = CircularBuffer(3)
    logs.add("A").add("B").add("C").add("D")
    logs.to_list()  # ["B", "C", "D"]

Collections
-----------
- :class:`ArrayList`       — dynamic array with functional API
- :class:`LinkedList`      — doubly-linked list (deque-backed)
- :class:`Stack`           — LIFO stack
- :class:`Queue`           — FIFO queue
- :class:`OrderedSet`      — insertion-ordered unique elements
- :class:`HashMap`         — fluent dict wrapper
- :class:`BiMap`           — bidirectional one-to-one map
- :class:`MultiMap`        — map with multiple values per key
- :class:`PriorityQueue`   — heap-backed priority queue
- :class:`CircularBuffer`  — fixed-capacity ring buffer

Functional utilities
--------------------
- :class:`Stream`      — lazy sequential pipeline (Java Streams style)
- :class:`Optional`    — safe None container
- :class:`Result`      — Ok/Err discriminated union for error handling

Exceptions
----------
- :class:`StreamExhaustedException` — raised when a consumed Stream is reused
"""

from nestifypy.collections.array_list import ArrayList
from nestifypy.collections.linked_list import LinkedList
from nestifypy.collections.stack import Stack
from nestifypy.collections.queue import Queue
from nestifypy.collections.ordered_set import OrderedSet
from nestifypy.collections.hash_map import HashMap
from nestifypy.collections.bi_map import BiMap
from nestifypy.collections.multi_map import MultiMap
from nestifypy.collections.priority_queue import PriorityQueue
from nestifypy.collections.circular_buffer import CircularBuffer
from nestifypy.collections.stream import Stream, StreamExhaustedException
from nestifypy.collections.optional import Optional
from nestifypy.collections.result import Result
from nestifypy.collections.immutable_list import ImmutableList
from nestifypy.collections.unmodifiable import unmodifiable

__all__ = [
    # Collections
    "ArrayList",
    "LinkedList",
    "Stack",
    "Queue",
    "OrderedSet",
    "HashMap",
    "BiMap",
    "MultiMap",
    "PriorityQueue",
    "CircularBuffer",
    # Functional utilities
    "Stream",
    "Optional",
    "Result",
    # Exceptions
    "StreamExhaustedException",
    # immutable
    "ImmutableList",
    # unmodifiable
    "unmodifiable",
]
