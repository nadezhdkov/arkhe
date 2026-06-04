"""
arkhe.collections
----------------------
Fluent, Java-inspired data structures and functional utilities for Python.

Quick start::

    from arkhe.collections import (
        ArrayList, LinkedList, Stack, Queue,
        OrderedSet, HashMap, BiMap, MultiMap,
        PriorityQueue, CircularBuffer,
        Stream,
    )

    # Fluent pipeline
    result = (
        Stream.range(1, 11)
        .filter(lambda n: n % 2 == 0)
        .map(lambda n: n ** 2)
        .to_list()
    )  # [4, 16, 36, 64, 100]

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

Exceptions
----------
- :class:`StreamExhaustedException` — raised when a consumed Stream is reused
"""

from arkhe.collections.array_list import ArrayList
from arkhe.collections.linked_list import LinkedList
from arkhe.collections.stack import Stack
from arkhe.collections.queue import Queue
from arkhe.collections.ordered_set import OrderedSet
from arkhe.collections.hash_map import HashMap
from arkhe.collections.bi_map import BiMap
from arkhe.collections.multi_map import MultiMap
from arkhe.collections.priority_queue import PriorityQueue
from arkhe.collections.circular_buffer import CircularBuffer
from arkhe.collections.stream import Stream, StreamExhaustedException
from arkhe.collections.immutable_list import ImmutableList
from arkhe.collections.unmodifiable import unmodifiable

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
    # Exceptions
    "StreamExhaustedException",
    # immutable
    "ImmutableList",
    # unmodifiable
    "unmodifiable",
]
