"""
arkhe.modifier._caller
-----------------------
Utilities for inspecting the call stack to determine the *calling context*
of a guarded attribute or method access.

This is the piece that makes the Java-style visibility semantics work in
Python: we walk up the interpreter frame stack until we find a frame that
belongs to real user code (i.e. is not inside the modifier machinery itself)
and return its associated class (if any).
"""

from __future__ import annotations

import inspect
import sys
from typing import Optional, Type

# Fully-qualified names of frames that belong to the arkhe modifier machinery.
# Any frame whose __name__ starts with one of these prefixes is skipped when
# walking the stack looking for the "real" caller.
_INTERNAL_MODULES = frozenset({
    "arkhe.modifier",
    "arkhe.modifier.exceptions",
    "arkhe.modifier._caller",
    "arkhe.modifier.core",
    "arkhe.modifier.descriptors",
})


def _is_internal_frame(frame: "inspect.FrameInfo") -> bool:
    """Return True if *frame* belongs to the modifier machinery itself."""
    mod = frame.frame.f_globals.get("__name__", "")
    return any(mod == internal or mod.startswith(internal + ".")
               for internal in _INTERNAL_MODULES)


def get_caller_class(skip_frames: int = 0) -> Optional[Type]:
    """
    Walk up the call stack and return the *class* of the first non-internal
    frame that has an identifiable class context, or ``None`` if no such
    frame exists.

    A frame is considered to have a class context when:
    - Its local variables contain ``self`` and ``self.__class__`` is a type, OR
    - Its local variables contain ``cls`` and it is a type.

    Args:
        skip_frames: Extra frames to skip beyond the internal machinery.
                     Normally 0 — only used in tests.

    Returns:
        The ``type`` object of the calling class, or ``None``.
    """
    stack = inspect.stack()
    skipped = 0

    for frame_info in stack[1:]:  # skip get_caller_class itself
        if _is_internal_frame(frame_info):
            continue
        if skipped < skip_frames:
            skipped += 1
            continue

        local_vars = frame_info.frame.f_locals

        # Instance method: look for 'self'
        self_obj = local_vars.get("self")
        if self_obj is not None and isinstance(type(self_obj), type):
            return type(self_obj)

        # Class method: look for 'cls'
        cls_obj = local_vars.get("cls")
        if isinstance(cls_obj, type):
            return cls_obj

        # Module-level or free function — no class context
        return None

    return None


def get_caller_qualname(skip_frames: int = 0) -> str:
    """
    Return a human-readable qualified name for the first non-internal caller.

    Used in error messages so the developer knows exactly *where* the illegal
    access originated.

    Returns:
        A string like ``"MyClass.my_method"`` or ``"<module>"`` / ``"<unknown>"``.
    """
    stack = inspect.stack()
    skipped = 0

    for frame_info in stack[1:]:
        if _is_internal_frame(frame_info):
            continue
        if skipped < skip_frames:
            skipped += 1
            continue

        local_vars = frame_info.frame.f_locals
        func_name = frame_info.function

        self_obj = local_vars.get("self")
        if self_obj is not None and isinstance(type(self_obj), type):
            return f"{type(self_obj).__qualname__}.{func_name}"

        cls_obj = local_vars.get("cls")
        if isinstance(cls_obj, type):
            return f"{cls_obj.__qualname__}.{func_name}"

        # Module-level code
        mod = frame_info.frame.f_globals.get("__name__", "<unknown>")
        return f"<module '{mod}'>"

    return "<unknown>"


__all__ = ["get_caller_class", "get_caller_qualname"]
