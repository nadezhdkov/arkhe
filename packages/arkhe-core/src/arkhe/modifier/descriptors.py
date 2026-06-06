"""
arkhe.modifier.descriptors
---------------------------
Python descriptor objects that enforce Java-style visibility at the point
of attribute *read* and *write*.

How it works
~~~~~~~~~~~~
When you annotate a field with ``@private`` or ``@protected``, the class
decorator replaces the plain class-level annotation with one of these
descriptors.  Every ``__get__`` / ``__set__`` / ``__delete__`` call then
asks ``_caller.get_caller_class()`` who is trying to access the value and
raises the appropriate error if the caller is outside the permitted scope.

Visibility rules (mirrors Java):
- **public**:    anyone can read/write — this is the Python default.
- **protected**: only the *owning class* and its *subclasses* may access.
- **private**:   only the *owning class* itself may access (no subclasses).
"""

from __future__ import annotations

from typing import Any, Optional, Type

from arkhe.modifier._caller import get_caller_class, get_caller_qualname
from arkhe.modifier.exceptions import PrivateAccessError, ProtectedAccessError

# Sentinel — distinguishes "no value stored" from None
_MISSING = object()


class _VisibilityDescriptor:
    """
    Base class for visibility-enforcing descriptors.

    Stores the actual field value inside the *instance* ``__dict__`` under a
    mangled key (``_arkhe__<name>``) so it never conflicts with normal
    attribute access patterns.
    """

    _visibility: str  # "private" | "protected" | "public"

    def __init__(self, name: str, default: Any = _MISSING) -> None:
        self._name = name
        self._storage_key = f"_arkhe__{name}"
        self._default = default
        self._owner: Optional[Type] = None  # set by __set_name__

    # ── descriptor protocol ──────────────────────────────────────────────────

    def __set_name__(self, owner: Type, name: str) -> None:
        self._owner = owner
        self._name = name
        self._storage_key = f"_arkhe__{name}"

    def __get__(self, obj: Any, objtype: Optional[Type] = None) -> Any:
        # Class-level access (e.g. MyClass.field) — allow for introspection
        if obj is None:
            return self

        self._check_access(operation="read")

        value = obj.__dict__.get(self._storage_key, _MISSING)
        if value is _MISSING:
            if self._default is not _MISSING:
                return self._default
            raise AttributeError(
                f"'{type(obj).__name__}' field '{self._name}' has not been set"
            )
        return value

    def __set__(self, obj: Any, value: Any) -> None:
        self._check_access(operation="write")
        obj.__dict__[self._storage_key] = value

    def __delete__(self, obj: Any) -> None:
        self._check_access(operation="delete")
        obj.__dict__.pop(self._storage_key, None)

    # ── access check — implemented by subclasses ─────────────────────────────

    def _check_access(self, operation: str) -> None:
        raise NotImplementedError

    # ── helpers ──────────────────────────────────────────────────────────────

    def _caller_info(self):
        """Return (caller_class, caller_qualname) for error messages."""
        return get_caller_class(), get_caller_qualname()

    def __repr__(self) -> str:
        owner_name = self._owner.__name__ if self._owner else "?"
        return (
            f"<{self.__class__.__name__} '{owner_name}.{self._name}' "
            f"default={self._default!r}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Concrete visibility descriptors
# ─────────────────────────────────────────────────────────────────────────────

class PublicDescriptor(_VisibilityDescriptor):
    """No-op descriptor — exists so every field is consistently a descriptor."""

    _visibility = "public"

    def _check_access(self, operation: str) -> None:
        pass  # always allowed


class ProtectedDescriptor(_VisibilityDescriptor):
    """
    Allows access only from the *owning class* and its *subclasses*.

    Raises ``ProtectedAccessError`` for any access originating from a class
    that is not related to the owner via inheritance.
    """

    _visibility = "protected"

    def _check_access(self, operation: str) -> None:
        if self._owner is None:
            return  # descriptor not yet bound — allow during class construction

        caller_cls, caller_qualname = self._caller_info()

        # No class context → module-level or free function → deny
        if caller_cls is None:
            raise ProtectedAccessError(
                member=self._name,
                caller=caller_qualname,
                owner=self._owner.__qualname__,
            )

        # Allow if caller IS the owner or a subclass of the owner
        if issubclass(caller_cls, self._owner):
            return

        raise ProtectedAccessError(
            member=self._name,
            caller=caller_qualname,
            owner=self._owner.__qualname__,
        )


class PrivateDescriptor(_VisibilityDescriptor):
    """
    Allows access **only** from the *exact* owning class.

    Even subclasses are denied — matching Java's ``private`` semantics.
    Raises ``PrivateAccessError`` otherwise.
    """

    _visibility = "private"

    def _check_access(self, operation: str) -> None:
        if self._owner is None:
            return  # during class construction, allow

        caller_cls, caller_qualname = self._caller_info()

        # Exact class match required — subclasses are NOT allowed
        if caller_cls is self._owner:
            return

        raise PrivateAccessError(
            member=self._name,
            caller=caller_qualname,
            owner=self._owner.__qualname__,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Method wrappers
# ─────────────────────────────────────────────────────────────────────────────

def _make_protected_method(func, owner_ref: list):
    """
    Wrap *func* so that each call checks whether the caller is the owner
    or a subclass before executing.

    ``owner_ref`` is a one-element list whose single item is filled in after
    the class is fully constructed (avoids a forward-reference problem).
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        owner = owner_ref[0]
        if owner is not None:
            caller_cls = get_caller_class()
            caller_qualname = get_caller_qualname()
            if caller_cls is None or not issubclass(caller_cls, owner):
                raise ProtectedAccessError(
                    member=func.__name__,
                    caller=caller_qualname,
                    owner=owner.__qualname__,
                )
        return func(*args, **kwargs)

    wrapper.__arkhe_visibility__ = "protected"
    wrapper.__arkhe_wrapped__ = func
    return wrapper


def _make_private_method(func, owner_ref: list):
    """
    Wrap *func* so that each call checks whether the caller is *exactly* the
    owner class (subclasses excluded).
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        owner = owner_ref[0]
        if owner is not None:
            caller_cls = get_caller_class()
            caller_qualname = get_caller_qualname()
            if caller_cls is not owner:
                raise PrivateAccessError(
                    member=func.__name__,
                    caller=caller_qualname,
                    owner=owner.__qualname__,
                )
        return func(*args, **kwargs)

    wrapper.__arkhe_visibility__ = "private"
    wrapper.__arkhe_wrapped__ = func
    return wrapper


__all__ = [
    "PublicDescriptor",
    "ProtectedDescriptor",
    "PrivateDescriptor",
    "_make_protected_method",
    "_make_private_method",
    "_MISSING",
]
