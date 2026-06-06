"""
arkhe.modifier.core
--------------------
Public decorator API for Java-style access modifiers in Python.

Decorators
~~~~~~~~~~
Member-level (applied to fields via class-body annotations or to methods):

    @private   — accessible only within the declaring class
    @protected — accessible within the declaring class and its subclasses
    @public    — no restriction (Python default; explicit annotation only)

Class-level (applied to the class to activate enforcement):

    @modifier  — scans the class body, installs descriptors for annotated
                 fields and wraps methods that carry a visibility marker,
                 then patches ``__init_subclass__`` so subclasses inherit
                 the machinery automatically.

Usage example
~~~~~~~~~~~~~
    from arkhe.modifier import modifier, private, protected, public

    @modifier
    class BankAccount:
        owner:   str          # public by default
        balance: float        # public by default

        @private
        def _validate(self, amount: float) -> None:
            if amount <= 0:
                raise ValueError("amount must be positive")

        @protected
        def _apply(self, amount: float) -> None:
            self._validate(amount)   # OK — same class
            self.balance += amount

        def deposit(self, amount: float) -> None:
            self._apply(amount)      # OK — subclass would be fine too

Design notes
~~~~~~~~~~~~
- Field visibility is declared by adding a ``__arkhe_visibility__`` attribute
  to the *annotation value*.  Because Python type annotations are evaluated
  lazily (PEP 563 / ``from __future__ import annotations``), we instead rely
  on a parallel ``__arkhe_field_visibility__`` dict that ``@private`` /
  ``@protected`` / ``@public`` populate when they are used as *field*
  decorators via the ``@modifier`` class decorator.

- The simpler and more ergonomic approach — which this module implements — is
  to let users mark fields with a ``typing.Annotated`` metadata tag OR to
  place the marker in the class-body assignment:

        balance: float = private.field(0.0)

  Both styles are supported; see ``private.field()``.

- Method visibility is simpler: decorating a method with ``@private`` /
  ``@protected`` attaches ``__arkhe_visibility__`` to the function object.
  ``@modifier`` then wraps those functions in enforcement closures and fills
  in the ``owner`` back-reference once the class is fully built.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Optional, Type, TypeVar

from arkhe.modifier.descriptors import (
    PrivateDescriptor,
    ProtectedDescriptor,
    PublicDescriptor,
    _make_private_method,
    _make_protected_method,
    _MISSING,
)
from arkhe.modifier.exceptions import AccessViolationError

C = TypeVar("C", bound=type)
F = TypeVar("F", bound=Callable)

# ─────────────────────────────────────────────────────────────────────────────
#  Sentinel objects for field default values
# ─────────────────────────────────────────────────────────────────────────────

class _FieldMarker:
    """
    Placed as the class-body value of a field to carry visibility + default.

        balance: float = private.field(0.0)
        name:    str   = protected.field()
    """

    def __init__(self, visibility: str, default: Any = _MISSING) -> None:
        self._visibility = visibility
        self._default = default

    def __repr__(self) -> str:
        return f"<field visibility={self._visibility!r} default={self._default!r}>"


# ─────────────────────────────────────────────────────────────────────────────
#  Visibility marker decorators
# ─────────────────────────────────────────────────────────────────────────────

class _VisibilityMarker:
    """
    Callable decorator object for ``@private``, ``@protected``, ``@public``.

    Can be used in two ways:

    1. **Method decorator**::

           @private
           def _secret(self): ...

    2. **Field marker** (via ``.field()``)::

           balance: float = private.field(0.0)
    """

    def __init__(self, visibility: str) -> None:
        self._visibility = visibility

    # ── method decorator use: @private / @protected / @public ────────────────

    def __call__(self, func: F) -> F:
        if not callable(func):
            raise TypeError(
                f"@{self._visibility} can only decorate callables (methods). "
                f"For fields use {self._visibility}.field(default)."
            )
        # Tag the function; @modifier will wrap it later.
        func.__arkhe_visibility__ = self._visibility  # type: ignore[attr-defined]
        return func

    # ── field marker use: private.field(...) ─────────────────────────────────

    def field(self, default: Any = _MISSING) -> _FieldMarker:
        """
        Create a field-level visibility marker with an optional default value.

        Example::

            @modifier
            class Foo:
                secret: int   = private.field(42)
                shared: str   = protected.field()
                visible: str  = public.field("hello")
        """
        return _FieldMarker(self._visibility, default)

    def __repr__(self) -> str:
        return f"<modifier.{self._visibility}>"


# The three public singletons
private   = _VisibilityMarker("private")
protected = _VisibilityMarker("protected")
public    = _VisibilityMarker("public")


# ─────────────────────────────────────────────────────────────────────────────
#  @modifier  — class-level decorator
# ─────────────────────────────────────────────────────────────────────────────

_DESCRIPTOR_MAP = {
    "private":   PrivateDescriptor,
    "protected": ProtectedDescriptor,
    "public":    PublicDescriptor,
}


def modifier(cls: C) -> C:
    """
    Activate access-modifier enforcement on *cls*.

    Steps performed:

    1. Scan ``cls.__annotations__`` for fields whose class-body value is a
       ``_FieldMarker``; install the appropriate descriptor.
    2. Scan ``cls.__dict__`` for methods tagged with ``__arkhe_visibility__``;
       replace them with enforcement wrappers.
    3. Patch ``__init_subclass__`` so that subclasses automatically inherit
       the enforcement (they do NOT need their own ``@modifier``).
    4. Store visibility metadata in ``cls.__arkhe_visibility_map__`` for
       runtime introspection.

    Args:
        cls: The class to instrument.

    Returns:
        The same class object, mutated in place.
    """
    visibility_map: dict[str, str] = {}  # member_name → visibility

    annotations = getattr(cls, "__annotations__", {})

    # ── Step 1: install field descriptors ────────────────────────────────────
    for field_name, annotation in annotations.items():
        if field_name.startswith("__"):
            continue  # skip dunder attributes

        raw_value = cls.__dict__.get(field_name, _MISSING)

        if isinstance(raw_value, _FieldMarker):
            vis = raw_value._visibility
            default = raw_value._default
        elif isinstance(raw_value, _VisibilityDescriptor_base := (
            PrivateDescriptor, ProtectedDescriptor, PublicDescriptor
        )):
            # Already a descriptor (stacked decorators or re-application)
            visibility_map[field_name] = raw_value._visibility
            continue
        else:
            # No explicit marker → public by default (Python convention)
            # We still install a PublicDescriptor so the storage model is
            # consistent, which also makes ModifierInspector simpler.
            vis = "public"
            default = raw_value  # may be _MISSING if no default

        descriptor_cls = _DESCRIPTOR_MAP[vis]
        descriptor = descriptor_cls(name=field_name, default=default)
        # __set_name__ is called automatically when assigning to the class
        setattr(cls, field_name, descriptor)
        visibility_map[field_name] = vis

    # ── Step 2: wrap visibility-tagged methods ────────────────────────────────
    for attr_name, attr_val in list(cls.__dict__.items()):
        # Unwrap staticmethods / classmethods to peek at the underlying func
        raw = attr_val
        is_static = isinstance(attr_val, staticmethod)
        is_class  = isinstance(attr_val, classmethod)
        if is_static:
            raw = attr_val.__func__
        elif is_class:
            raw = attr_val.__func__

        vis = getattr(raw, "__arkhe_visibility__", None)
        if vis is None:
            continue
        if vis == "public":
            visibility_map[attr_name] = "public"
            continue  # no wrapping needed

        # owner_ref: a mutable one-element list so the wrapper closure can
        # read the owner class after it's been fully constructed.
        owner_ref: list = [cls]

        if vis == "private":
            wrapped = _make_private_method(raw, owner_ref)
        else:  # "protected"
            wrapped = _make_protected_method(raw, owner_ref)

        # Re-apply staticmethod / classmethod shell if needed
        if is_static:
            wrapped = staticmethod(wrapped)
        elif is_class:
            wrapped = classmethod(wrapped)

        setattr(cls, attr_name, wrapped)
        visibility_map[attr_name] = vis

    # ── Step 3: store metadata ────────────────────────────────────────────────
    cls.__arkhe_visibility_map__ = visibility_map  # type: ignore[attr-defined]
    cls.__arkhe_modifier_applied__ = True           # type: ignore[attr-defined]

    # ── Step 4: propagate to subclasses via __init_subclass__ ────────────────
    original_init_subclass = cls.__dict__.get("__init_subclass__")

    @classmethod  # type: ignore[misc]
    def __init_subclass__(subcls, **kwargs):
        if original_init_subclass is not None:
            original_init_subclass.__func__(subcls, **kwargs)
        else:
            super(cls, subcls).__init_subclass__(**kwargs)
        # Apply modifier to the subclass automatically
        if not getattr(subcls, "__arkhe_modifier_applied__", False):
            modifier(subcls)

    cls.__init_subclass__ = __init_subclass__

    return cls


# ─────────────────────────────────────────────────────────────────────────────
#  Convenience: _VisibilityDescriptor_base alias for isinstance checks
# ─────────────────────────────────────────────────────────────────────────────
# (imported elsewhere for isinstance checks)
_VisibilityDescriptor_base = (PrivateDescriptor, ProtectedDescriptor, PublicDescriptor)

__all__ = [
    "modifier",
    "private",
    "protected",
    "public",
    "AccessViolationError",
]
