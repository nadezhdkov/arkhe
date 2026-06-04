"""
arkhe.json.utils
--------------------
Internal and public utility functions for the JSON module.

Public surface
~~~~~~~~~~~~~~
* ``deep_merge``    — recursive dict merge (RFC 7396 semantics)
* ``flatten``       — nested dict → ``{"a.b.c": value}``
* ``unflatten``     — ``{"a.b.c": value}`` → nested dict
* ``diff``          — compute the difference between two dicts
* ``patch``         — apply a JSON Merge Patch (RFC 7396)
* ``pick``          — extract a subset of keys
* ``omit``          — remove specific keys
* ``rename_keys``   — rename keys via a mapping
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# deep_merge
# ---------------------------------------------------------------------------

def deep_merge(
    base: Dict[str, Any],
    override: Dict[str, Any],
    *,
    in_place: bool = False,
) -> Dict[str, Any]:
    """
    Recursively merge *override* into *base*.

    * Dicts are merged recursively.
    * All other types: *override* value wins.
    * ``None`` values in *override* delete the key (RFC 7396 semantics).

    Parameters
    ----------
    in_place:
        Mutate *base* directly instead of returning a copy.
    """
    result = base if in_place else base.copy()
    for key, val in override.items():
        if val is None:
            result.pop(key, None)
        elif key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = val
    return result


# ---------------------------------------------------------------------------
# flatten / unflatten
# ---------------------------------------------------------------------------

def flatten(
    data: Dict[str, Any],
    *,
    sep: str = ".",
    prefix: str = "",
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary to a single-level dict with dot-path keys.

    Example::

        flatten({"a": {"b": {"c": 1}}})
        # → {"a.b.c": 1}
    """
    result: Dict[str, Any] = {}
    for key, val in data.items():
        full_key = f"{prefix}{sep}{key}" if prefix else key
        if isinstance(val, dict) and val:
            result.update(flatten(val, sep=sep, prefix=full_key))
        else:
            result[full_key] = val
    return result


def unflatten(
    data: Dict[str, Any],
    *,
    sep: str = ".",
) -> Dict[str, Any]:
    """
    Reconstruct a nested dict from a flat dict with dot-path keys.

    Example::

        unflatten({"a.b.c": 1})
        # → {"a": {"b": {"c": 1}}}
    """
    result: Dict[str, Any] = {}
    for key, val in data.items():
        parts = key.split(sep)
        node = result
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = val
    return result


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------

def diff(
    a: Dict[str, Any],
    b: Dict[str, Any],
    *,
    path: str = "",
) -> List[Dict[str, Any]]:
    """
    Compute the difference between two dicts.

    Returns a list of change records::

        [
            {"op": "add",    "path": "b",     "value": 2},
            {"op": "remove", "path": "c"},
            {"op": "change", "path": "a",     "from": 1, "to": 10},
        ]

    Nested dicts are compared recursively; the ``"path"`` field uses
    dot-notation.

    Example::

        diff({"a": 1, "c": 3}, {"a": 10, "b": 2})
        # → [
        #     {"op": "change", "path": "a", "from": 1, "to": 10},
        #     {"op": "remove", "path": "c"},
        #     {"op": "add",    "path": "b", "value": 2},
        # ]
    """
    changes: List[Dict[str, Any]] = []
    all_keys = set(a) | set(b)

    for key in sorted(all_keys):
        full_path = f"{path}.{key}" if path else key
        in_a, in_b = key in a, key in b

        if in_a and not in_b:
            changes.append({"op": "remove", "path": full_path})
        elif in_b and not in_a:
            changes.append({"op": "add", "path": full_path, "value": b[key]})
        else:
            va, vb = a[key], b[key]
            if isinstance(va, dict) and isinstance(vb, dict):
                changes.extend(diff(va, vb, path=full_path))
            elif va != vb:
                changes.append({"op": "change", "path": full_path, "from": va, "to": vb})

    return changes


# ---------------------------------------------------------------------------
# patch  (JSON Merge Patch — RFC 7396)
# ---------------------------------------------------------------------------

def patch(
    document: Dict[str, Any],
    merge_patch: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply a JSON Merge Patch (RFC 7396) to *document*.

    Rules:
    * If a patch key maps to ``None``, that key is removed from the document.
    * If a patch key maps to a dict and the document's value is also a dict,
      they are merged recursively.
    * Otherwise the patch value replaces the document value.

    A new dict is returned; *document* is never mutated.

    Example::

        patch(
            {"a": 1, "b": {"c": 2, "d": 3}},
            {"b": {"d": None, "e": 4}, "f": 5},
        )
        # → {"a": 1, "b": {"c": 2, "e": 4}, "f": 5}
    """
    return deep_merge(document, merge_patch)


# ---------------------------------------------------------------------------
# pick / omit
# ---------------------------------------------------------------------------

def pick(
    data: Dict[str, Any],
    keys: Iterable[str],
) -> Dict[str, Any]:
    """
    Return a new dict containing only the specified *keys*.

    Example::

        pick({"a": 1, "b": 2, "c": 3}, ["a", "c"])
        # → {"a": 1, "c": 3}
    """
    return {k: data[k] for k in keys if k in data}


def omit(
    data: Dict[str, Any],
    keys: Iterable[str],
) -> Dict[str, Any]:
    """
    Return a new dict with the specified *keys* removed.

    Example::

        omit({"a": 1, "b": 2, "c": 3}, ["b"])
        # → {"a": 1, "c": 3}
    """
    excluded = set(keys)
    return {k: v for k, v in data.items() if k not in excluded}


# ---------------------------------------------------------------------------
# rename_keys
# ---------------------------------------------------------------------------

def rename_keys(
    data: Dict[str, Any],
    mapping: Dict[str, str],
) -> Dict[str, Any]:
    """
    Return a new dict with keys renamed according to *mapping*.

    Keys not present in *mapping* are kept as-is.

    Example::

        rename_keys({"userId": 1, "name": "Alice"}, {"userId": "user_id"})
        # → {"user_id": 1, "name": "Alice"}
    """
    return {mapping.get(k, k): v for k, v in data.items()}


__all__ = [
    "deep_merge",
    "flatten",
    "unflatten",
    "diff",
    "patch",
    "pick",
    "omit",
    "rename_keys",
]
