"""
arkhe.collections.unmodifiable
------------------------------------
Runtime unmodifiable wrappers for arkhe collections.

This module provides :func:`unmodifiable` — a factory that wraps **any**
arkhe collection in a read-only proxy at runtime, identical to Java's

    Collections.unmodifiableList(list)
    Collections.unmodifiableSet(set)
    Collections.unmodifiableMap(map)

Unlike :class:`~arkhe.collections.immutable_list.ImmutableList` and
:class:`~arkhe.collections.immutable_array.ImmutableArray` (which are
*immutable by construction*), an ``UnmodifiableWrapper`` wraps an *existing
mutable object*. The underlying collection may still be mutated through the
original reference — the wrapper merely prevents callers who only hold the
wrapper from doing so.

This is exactly the Java semantics::

    List<String> mutable   = new ArrayList<>(List.of("a", "b"));
    List<String> readOnly  = Collections.unmodifiableList(mutable);

    readOnly.add("c");  // ✗  UnsupportedOperationException
    mutable.add("c");   // ✓  readOnly now reflects {"a", "b", "c"}

Usage::

    from arkhe.collections import ArrayList, HashMap
    from arkhe.collections.unmodifiable import unmodifiable

    data = ArrayList([1, 2, 3])
    view = unmodifiable(data)

    view.get(0)      # 1  — reads pass through
    view.size()      # 3
    view.add(4)      # ✗  UnsupportedOperationException

    data.add(4)      # mutates the original
    view.size()      # 4  — view reflects the change (live view semantics)

    # HashMap example
    scores = HashMap({"alice": 95, "bob": 80})
    read_only_scores = unmodifiable(scores)
    read_only_scores.put("carol", 70)  # ✗  UnsupportedOperationException

Supported collection types
--------------------------
- :class:`~arkhe.collections.array_list.ArrayList`
- :class:`~arkhe.collections.linked_list.LinkedList`
- :class:`~arkhe.collections.stack.Stack`
- :class:`~arkhe.collections.queue.Queue`
- :class:`~arkhe.collections.ordered_set.OrderedSet`
- :class:`~arkhe.collections.hash_map.HashMap`
- :class:`~arkhe.collections.bi_map.BiMap`
- :class:`~arkhe.collections.multi_map.MultiMap`
- :class:`~arkhe.collections.priority_queue.PriorityQueue`
- :class:`~arkhe.collections.circular_buffer.CircularBuffer`
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from arkhe.collections.immutable_list import UnsupportedOperationException

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MUTATION_METHODS = frozenset({
    # ArrayList / LinkedList
    "add", "add_all", "add_first", "add_last", "add_all_last",
    "insert", "remove", "remove_at", "remove_first", "remove_last",
    "remove_if", "remove_value", "set", "sort", "reverse", "clear",
    # Stack
    "push", "push_all", "pop", "pop_or",
    # Queue
    "enqueue", "enqueue_all", "dequeue", "dequeue_or",
    # OrderedSet
    "discard",
    # HashMap / BiMap / MultiMap
    "put", "put_if_absent", "put_all", "put_all_keys", "replace",
    "map_values", "map_keys", "map_entries",   # mutating transforms on maps
    # PriorityQueue
    "poll",
    # CircularBuffer
    # (add / add_all already listed above)
    # Generic extras
    "extend", "append",
})


class UnmodifiableWrapper(Generic[T]):
    """
    A transparent read-only proxy around any arkhe collection.

    All *read* operations are forwarded to the underlying collection.
    All *write* operations raise :class:`UnsupportedOperationException`.

    The wrapper holds a **live reference** — if the underlying collection
    is mutated via the original reference, those changes are visible
    through the wrapper. This mirrors ``Collections.unmodifiable*()``.

    Do not instantiate directly; use :func:`unmodifiable`.
    """

    __slots__ = ("__wrapped__",)

    def __init__(self, collection: Any) -> None:
        object.__setattr__(self, "__wrapped__", collection)

    # ------------------------------------------------------------------
    # Prevent attribute mutation on the wrapper itself
    # ------------------------------------------------------------------

    def __setattr__(self, name: str, value: Any) -> None:  # type: ignore[override]
        if name == "__wrapped__":
            # Allow only during __init__ (already handled via object.__setattr__)
            raise UnsupportedOperationException(
                "UnmodifiableWrapper cannot be reassigned after construction."
            )
        raise UnsupportedOperationException(
            f"UnmodifiableWrapper does not allow attribute assignment ('{name}')."
        )

    # ------------------------------------------------------------------
    # Dynamic dispatch
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        wrapped = object.__getattribute__(self, "__wrapped__")
        attr = getattr(wrapped, name)

        if name in _MUTATION_METHODS:
            def _blocked(*args: Any, **kwargs: Any) -> None:
                raise UnsupportedOperationException(
                    f"'{type(wrapped).__name__}' wrapped by UnmodifiableWrapper "
                    f"does not permit mutating operation '{name}'."
                )
            _blocked.__name__ = name
            _blocked.__qualname__ = f"UnmodifiableWrapper.{name}"
            return _blocked

        return attr

    # ------------------------------------------------------------------
    # Dunder forwarding (Python doesn't route these through __getattr__)
    # ------------------------------------------------------------------

    def __iter__(self):  # type: ignore[override]
        return iter(object.__getattribute__(self, "__wrapped__"))

    def __len__(self) -> int:
        return len(object.__getattribute__(self, "__wrapped__"))

    def __contains__(self, item: Any) -> bool:
        return item in object.__getattribute__(self, "__wrapped__")

    def __getitem__(self, index: Any) -> Any:
        return object.__getattribute__(self, "__wrapped__")[index]

    def __setitem__(self, index: Any, value: Any) -> None:
        wrapped = object.__getattribute__(self, "__wrapped__")
        raise UnsupportedOperationException(
            f"'{type(wrapped).__name__}' wrapped by UnmodifiableWrapper "
            "does not permit item assignment."
        )

    def __delitem__(self, index: Any) -> None:
        wrapped = object.__getattribute__(self, "__wrapped__")
        raise UnsupportedOperationException(
            f"'{type(wrapped).__name__}' wrapped by UnmodifiableWrapper "
            "does not permit item deletion."
        )

    def __bool__(self) -> bool:
        return bool(object.__getattribute__(self, "__wrapped__"))

    def __eq__(self, other: object) -> bool:
        wrapped = object.__getattribute__(self, "__wrapped__")
        if isinstance(other, UnmodifiableWrapper):
            return wrapped == object.__getattribute__(other, "__wrapped__")
        return wrapped == other

    def __hash__(self) -> int:
        return hash(object.__getattribute__(self, "__wrapped__"))

    def __repr__(self) -> str:
        wrapped = object.__getattribute__(self, "__wrapped__")
        return f"UnmodifiableWrapper({wrapped!r})"


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------

def unmodifiable(collection: T) -> "UnmodifiableWrapper[T]":
    """
    Wrap *collection* in a read-only proxy.

    Any call to a mutating method on the returned wrapper raises
    :class:`~arkhe.collections.immutable_list.UnsupportedOperationException`.
    Read operations are forwarded transparently, so the wrapper always
    reflects the current state of the underlying collection.

    Args:
        collection: Any arkhe collection instance.

    Returns:
        UnmodifiableWrapper: A read-only view of *collection*.

    Example::

        from arkhe.collections import ArrayList
        from arkhe.collections.unmodifiable import unmodifiable

        items = ArrayList([1, 2, 3])
        view  = unmodifiable(items)

        view.size()      # 3
        view.get(0)      # 1
        list(view)       # [1, 2, 3]

        view.add(4)      # ✗  UnsupportedOperationException

        items.add(4)     # mutate original
        view.size()      # 4  — live view
    """
    return UnmodifiableWrapper(collection)
