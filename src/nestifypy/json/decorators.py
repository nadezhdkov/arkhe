"""
nestifypy.json.decorators
-------------------------
Gson / Jackson–style class and field decorators for Python.

Decorators
~~~~~~~~~~
@json_serializable          mark a class for automatic (de)serialisation
@json_field(...)            configure how a specific field is mapped
@json_exclude               exclude a field from (de)serialisation entirely
@json_alias("other_name")   map a field to a different JSON key
@json_validator(fn)         attach a field-level validation callable
@json_post_load(fn)         run a method after deserialisation
@json_pre_dump(fn)          run a method / transform before serialisation

Usage example
~~~~~~~~~~~~~
    from nestifypy.json import (
        json_serializable, json_field, json_exclude,
        json_alias, json_validator, json_post_load,
    )

    @json_serializable
    class User:
        name:  str
        email: str
        age:   int   = json_field(default=0)
        token: str   = json_field(exclude=True)
        joined: str  = json_field(alias="joinedAt")

        @json_validator("age")
        def _validate_age(self, value: int) -> None:
            if value < 0:
                raise ValueError("age must be non-negative")

        @json_post_load
        def _after_load(self) -> None:
            self.email = self.email.lower()

    # De-serialise from a dict
    user = User.from_dict({"name": "Alice", "email": "ALICE@EX.COM", "joinedAt": "2024"})
    print(user.email)      # "alice@ex.com"
    print(user.to_dict())  # {"name": "Alice", "email": "alice@ex.com", "joinedAt": "2024"}
"""
from __future__ import annotations

import dataclasses
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from nestifypy.json.exceptions import JsonMappingError, JsonValidationError

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Internal metadata keys stored on the class
# ---------------------------------------------------------------------------
_FIELDS_ATTR     = "__json_fields__"      # Dict[python_name, FieldMeta]
_POST_LOAD_ATTR  = "__json_post_load__"   # List[method_name]
_PRE_DUMP_ATTR   = "__json_pre_dump__"    # List[method_name]
_VALIDATORS_ATTR = "__json_validators__"  # Dict[python_name, List[method_name]]
_MARKER_ATTR     = "__json_serializable__"
_MISSING         = object()


# ---------------------------------------------------------------------------
# FieldMeta — internal per-field configuration
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class FieldMeta:
    """All configuration for a single serialisable field."""
    python_name: str
    alias:       Optional[str]   = None   # JSON key override
    default:     Any             = _MISSING
    exclude:     bool            = False  # skip in both directions
    exclude_if_none: bool        = False  # skip when value is None
    required:    bool            = False  # raise if missing during from_dict

    @property
    def json_key(self) -> str:
        """The key used in the JSON document."""
        return self.alias if self.alias else self.python_name


# ---------------------------------------------------------------------------
# Sentinel returned by json_field() so the descriptor pattern works
# ---------------------------------------------------------------------------

class _FieldDescriptor:
    """
    Placeholder assigned to a class attribute when ``json_field()`` is used.

    ``@json_serializable`` replaces it with the actual default value (or
    removes it so ``__init__`` / ``__annotations__`` govern the attribute).
    """
    __slots__ = ("meta",)

    def __init__(self, meta: FieldMeta) -> None:
        self.meta = meta


# ---------------------------------------------------------------------------
# Public decorator: @json_field(...)
# ---------------------------------------------------------------------------

def json_field(
    *,
    alias: Optional[str] = None,
    default: Any = _MISSING,
    exclude: bool = False,
    exclude_if_none: bool = False,
    required: bool = False,
) -> Any:
    """
    Configure how a class attribute is (de)serialised.

    Parameters
    ----------
    alias:
        JSON key to use instead of the Python attribute name.
    default:
        Default value when the key is absent during ``from_dict``.
    exclude:
        Skip this field in both serialisation and deserialisation.
    exclude_if_none:
        Omit this field from the serialised output when its value is ``None``.
    required:
        Raise ``JsonMappingError`` if the key is absent during ``from_dict``.

    Example::

        @json_serializable
        class Config:
            host: str
            port: int  = json_field(default=8080)
            secret: str = json_field(exclude=True)
            createdAt: str = json_field(alias="created_at")
    """
    meta = FieldMeta(
        python_name="",  # filled in by @json_serializable
        alias=alias,
        default=default,
        exclude=exclude,
        exclude_if_none=exclude_if_none,
        required=required,
    )
    return _FieldDescriptor(meta)


# ---------------------------------------------------------------------------
# Public decorator: @json_exclude
# ---------------------------------------------------------------------------

def json_exclude(attr_name: str) -> Callable[[Type[T]], Type[T]]:
    """
    Class-level decorator that marks one attribute as excluded.

    Prefer ``json_field(exclude=True)`` when possible; use this decorator
    when you cannot modify the attribute definition directly.

    Example::

        @json_serializable
        @json_exclude("internal_cache")
        class MyModel:
            name: str
            internal_cache: dict
    """
    def decorator(cls: Type[T]) -> Type[T]:
        _ensure_fields(cls)
        fields: Dict[str, FieldMeta] = getattr(cls, _FIELDS_ATTR)
        if attr_name in fields:
            fields[attr_name].exclude = True
        else:
            fields[attr_name] = FieldMeta(python_name=attr_name, exclude=True)
        return cls
    return decorator


# ---------------------------------------------------------------------------
# Public decorator: @json_alias("json_key")
# ---------------------------------------------------------------------------

def json_alias(json_key: str) -> Callable[[Any], Any]:
    """
    Field-level decorator that maps a Python attribute to a different JSON key.

    Can be used on the attribute itself (as a descriptor) **or** as a
    standalone decorator on a class (see ``json_exclude`` for the pattern).

    Typical use — annotate a property::

        @json_serializable
        class Event:
            user_id: str = json_alias("userId")   # JSON key = "userId"
    """
    meta = FieldMeta(python_name="", alias=json_key)
    return _FieldDescriptor(meta)


# ---------------------------------------------------------------------------
# Public decorator: @json_validator("field_name")
# ---------------------------------------------------------------------------

def json_validator(field_name: str) -> Callable[[Callable], Callable]:
    """
    Mark a method as a field-level validator.  The method is called after
    ``from_dict`` assigns the value and receives ``(self, value)``.

    Raise ``ValueError`` (or any exception) to signal a validation failure.

    Example::

        @json_serializable
        class Product:
            price: float

            @json_validator("price")
            def _check_price(self, value: float) -> None:
                if value < 0:
                    raise ValueError("price must be >= 0")
    """
    def decorator(fn: Callable) -> Callable:
        fn.__json_validates__ = field_name
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Public decorator: @json_post_load
# ---------------------------------------------------------------------------

def json_post_load(fn: Callable) -> Callable:
    """
    Mark a method to be called after ``from_dict`` finishes mapping all fields.

    Use for derived-field computation, normalisation, or cross-field validation.

    Example::

        @json_serializable
        class User:
            first_name: str
            last_name:  str
            full_name:  str = json_field(exclude=True)

            @json_post_load
            def _build_full_name(self) -> None:
                self.full_name = f"{self.first_name} {self.last_name}"
    """
    fn.__json_post_load__ = True
    return fn


# ---------------------------------------------------------------------------
# Public decorator: @json_pre_dump
# ---------------------------------------------------------------------------

def json_pre_dump(fn: Callable) -> Callable:
    """
    Mark a method to be called before ``to_dict`` serialises the object.

    The method receives no arguments (only ``self``) and may mutate
    the instance in-place or return ``None``.

    Example::

        @json_serializable
        class Report:
            generated_at: str

            @json_pre_dump
            def _stamp_time(self) -> None:
                from datetime import datetime, timezone
                self.generated_at = datetime.now(timezone.utc).isoformat()
    """
    fn.__json_pre_dump__ = True
    return fn


# ---------------------------------------------------------------------------
# Main class decorator: @json_serializable
# ---------------------------------------------------------------------------

def json_serializable(cls: Type[T]) -> Type[T]:
    """
    Enable automatic JSON (de)serialisation for a class.

    Injects two instance methods:
    * ``from_dict(data)``  — class method: ``MyClass.from_dict({...})``
    * ``to_dict()``        — instance method: ``instance.to_dict()``

    Also accepts ``from_json(text)`` and ``to_json(pretty=False)`` for
    direct string I/O.

    How field discovery works
    ~~~~~~~~~~~~~~~~~~~~~~~~~
    1. Every annotated attribute (``__annotations__``) becomes a field.
    2. Attributes assigned a ``json_field(...)`` / ``json_alias(...)``
       descriptor gain extra metadata.
    3. Methods decorated with ``@json_validator``, ``@json_post_load``,
       and ``@json_pre_dump`` are registered automatically.

    Example::

        @json_serializable
        class Config:
            host: str
            port: int = json_field(default=8080)

        cfg = Config.from_dict({"host": "localhost"})
        print(cfg.port)         # 8080
        print(cfg.to_dict())    # {"host": "localhost", "port": 8080}
    """
    _ensure_fields(cls)
    _collect_field_metadata(cls)
    _collect_hooks(cls)
    _inject_methods(cls)
    setattr(cls, _MARKER_ATTR, True)
    return cls


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_fields(cls: Type) -> None:
    """Initialise the ``__json_fields__`` dict if not present."""
    if not hasattr(cls, _FIELDS_ATTR) or _FIELDS_ATTR not in cls.__dict__:
        # Don't share a parent's dict
        setattr(cls, _FIELDS_ATTR, {})


def _collect_field_metadata(cls: Type) -> None:
    """
    Walk ``__annotations__`` and class-level assignments to build
    ``__json_fields__``.
    """
    fields: Dict[str, FieldMeta] = getattr(cls, _FIELDS_ATTR)
    annotations: Dict[str, Any] = {}

    # Accumulate annotations from base classes (MRO order, skip object)
    for base in reversed(cls.__mro__):
        if base is object:
            continue
        annotations.update(getattr(base, "__annotations__", {}))

    for python_name in annotations:
        if python_name.startswith("_"):
            continue  # skip private/dunder

        class_val = cls.__dict__.get(python_name, _MISSING)

        if isinstance(class_val, _FieldDescriptor):
            meta = class_val.meta
            meta.python_name = python_name
            fields[python_name] = meta
            # Replace the descriptor with the default value (or remove it)
            if meta.default is not _MISSING:
                setattr(cls, python_name, meta.default)
            else:
                try:
                    delattr(cls, python_name)
                except AttributeError:
                    pass
        elif python_name not in fields:
            # Plain annotation — create a default FieldMeta
            default = class_val if class_val is not _MISSING else _MISSING
            fields[python_name] = FieldMeta(
                python_name=python_name,
                default=default,
            )


def _collect_hooks(cls: Type) -> None:
    """Register post-load, pre-dump, and per-field validator methods."""
    post_load:  List[str] = []
    pre_dump:   List[str] = []
    validators: Dict[str, List[str]] = {}

    for name, val in inspect.getmembers(cls, predicate=inspect.isfunction):
        if getattr(val, "__json_post_load__", False):
            post_load.append(name)
        if getattr(val, "__json_pre_dump__", False):
            pre_dump.append(name)
        field_name = getattr(val, "__json_validates__", None)
        if field_name:
            validators.setdefault(field_name, []).append(name)

    setattr(cls, _POST_LOAD_ATTR, post_load)
    setattr(cls, _PRE_DUMP_ATTR, pre_dump)
    setattr(cls, _VALIDATORS_ATTR, validators)


def _inject_methods(cls: Type[T]) -> None:
    """Inject ``from_dict``, ``to_dict``, ``from_json``, ``to_json``."""

    # ------------------------------------------------------------------
    # from_dict
    # ------------------------------------------------------------------
    @classmethod  # type: ignore[misc]
    def from_dict(klass: Type[T], data: Dict[str, Any]) -> T:
        """
        Create an instance from a plain dictionary.

        Keys are matched by Python name first, then by ``alias``.
        """
        if not isinstance(data, dict):
            raise JsonMappingError(
                f"{klass.__name__}.from_dict() expects a dict, got {type(data).__name__}"
            )

        fields: Dict[str, FieldMeta] = getattr(klass, _FIELDS_ATTR, {})
        instance = klass.__new__(klass)

        # Build reverse alias map: json_key → python_name
        alias_map: Dict[str, str] = {
            m.json_key: m.python_name
            for m in fields.values()
            if not m.exclude
        }

        errors: List[str] = []

        for python_name, meta in fields.items():
            if meta.exclude:
                continue

            # Look up by alias first, then by python name
            json_key = meta.json_key
            if json_key in data:
                raw = data[json_key]
            elif python_name in data:
                raw = data[python_name]
            elif meta.default is not _MISSING:
                raw = meta.default() if callable(meta.default) else meta.default
            elif meta.required:
                errors.append(f"Required field '{json_key}' is missing.")
                continue
            else:
                raw = None

            setattr(instance, python_name, raw)

            # Run per-field validators
            validators: Dict[str, List[str]] = getattr(klass, _VALIDATORS_ATTR, {})
            for method_name in validators.get(python_name, []):
                try:
                    getattr(instance, method_name)(raw)
                except Exception as exc:
                    errors.append(f"Field '{python_name}': {exc}")

        if errors:
            raise JsonValidationError(
                f"{klass.__name__} validation failed:\n" + "\n".join(f"  • {e}" for e in errors),
                errors=errors,
            )

        # Run post-load hooks
        for method_name in getattr(klass, _POST_LOAD_ATTR, []):
            getattr(instance, method_name)()

        return instance

    # ------------------------------------------------------------------
    # to_dict
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Serialise the instance to a plain dictionary."""
        # Run pre-dump hooks
        for method_name in getattr(self.__class__, _PRE_DUMP_ATTR, []):
            getattr(self, method_name)()

        fields: Dict[str, FieldMeta] = getattr(self.__class__, _FIELDS_ATTR, {})
        result: Dict[str, Any] = {}

        for python_name, meta in fields.items():
            if meta.exclude:
                continue
            value = getattr(self, python_name, None)
            if meta.exclude_if_none and value is None:
                continue
            # Recursively serialise nested @json_serializable objects
            if hasattr(value, "to_dict") and callable(value.to_dict):
                value = value.to_dict()
            result[meta.json_key] = value

        return result

    # ------------------------------------------------------------------
    # from_json / to_json
    # ------------------------------------------------------------------
    @classmethod  # type: ignore[misc]
    def from_json(klass: Type[T], text: str) -> T:
        """Deserialise from a JSON string."""
        import json as _json
        from nestifypy.json.exceptions import JsonParseError
        try:
            data = _json.loads(text)
        except _json.JSONDecodeError as exc:
            raise JsonParseError(f"Invalid JSON: {exc}") from exc
        return klass.from_dict(data)

    def to_json(self, *, pretty: bool = False) -> str:
        """Serialise to a JSON string."""
        import json as _json
        return _json.dumps(self.to_dict(), indent=2 if pretty else None, ensure_ascii=False)

    # ------------------------------------------------------------------
    # __repr__
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        fields: Dict[str, FieldMeta] = getattr(self.__class__, _FIELDS_ATTR, {})
        parts = [
            f"{m.python_name}={getattr(self, m.python_name, None)!r}"
            for m in fields.values()
            if not m.exclude
        ]
        return f"{self.__class__.__name__}({', '.join(parts)})"

    cls.from_dict = from_dict  # type: ignore[attr-defined]
    cls.to_dict   = to_dict    # type: ignore[attr-defined]
    cls.from_json = from_json  # type: ignore[attr-defined]
    cls.to_json   = to_json    # type: ignore[attr-defined]
    if "__repr__" not in cls.__dict__:
        cls.__repr__ = __repr__  # type: ignore[method-assign]


def is_json_serializable(cls: type) -> bool:
    """Return ``True`` if *cls* has been decorated with ``@json_serializable``."""
    return bool(getattr(cls, _MARKER_ATTR, False))


__all__ = [
    "json_serializable",
    "json_field",
    "json_exclude",
    "json_alias",
    "json_validator",
    "json_post_load",
    "json_pre_dump",
    "FieldMeta",
    "is_json_serializable",
]
