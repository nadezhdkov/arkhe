"""
nestifypy.komodo.core
-------------------
The `komodo` namespace — all class-level annotation decorators live here.
"""

from typing import TypeVar, Callable, Any
from nestifypy.komodo.ast_engine import apply_generator
from nestifypy.komodo.ast_generators.constructor import generate_constructor
from nestifypy.komodo.ast_generators.repr import generate_to_str
from nestifypy.komodo.ast_generators.eq_hash import generate_eq_hash
from nestifypy.komodo.ast_generators.record import generate_record
from nestifypy.komodo.ast_generators.immutable import generate_immutable
from nestifypy.komodo.ast_generators.builder import generate_builder
from nestifypy.komodo.ast_generators.accessors import generate_accessors
from nestifypy.komodo.ast_generators.validation import generate_non_null, generate_validated
from nestifypy.komodo.ast_generators.logger import generate_logger
from nestifypy.komodo.ast_generators.copyable import generate_copyable
from nestifypy.komodo.ast_generators.serialization import generate_to_dict, generate_from_dict, generate_json

C = TypeVar("C", bound=type)

class _Komodo:

    @staticmethod
    def data(cls: C) -> C:
        cls = _Komodo.constructor(cls)
        cls = _Komodo.to_str(cls)
        cls = _Komodo.eq(cls)
        from nestifypy.komodo.ast_generators.utils import mark_komodo_meta
        mark_komodo_meta(cls, "data")
        return cls

    @staticmethod
    def value(cls: C) -> C:
        cls = _Komodo.data(cls)
        cls = _Komodo.immutable(cls)
        from nestifypy.komodo.ast_generators.utils import mark_komodo_meta
        mark_komodo_meta(cls, "value")
        return cls

    @staticmethod
    def constructor(cls: C) -> C:
        return apply_generator(cls, lambda c, t: generate_constructor(c, t, "all"))

    @staticmethod
    def no_args_constructor(cls: C) -> C:
        return apply_generator(cls, lambda c, t: generate_constructor(c, t, "no_args"))

    @staticmethod
    def required_args_constructor(cls: C) -> C:
        return apply_generator(cls, lambda c, t: generate_constructor(c, t, "required"))

    @staticmethod
    def all_args_constructor(cls: C) -> C:
        return apply_generator(cls, lambda c, t: generate_constructor(c, t, "all"))

    @staticmethod
    def to_str(cls: C) -> C:
        return apply_generator(cls, generate_to_str)

    @staticmethod
    def eq(cls: C) -> C:
        return apply_generator(cls, generate_eq_hash)

    @staticmethod
    def immutable(cls: C) -> C:
        return apply_generator(cls, generate_immutable)

    @staticmethod
    def builder(cls: C) -> C:
        return apply_generator(cls, generate_builder)

    @staticmethod
    def singular(field_name: str) -> Callable[[C], C]:
        def decorator(cls: C) -> C:
            if not hasattr(cls, "__komodo_singulars__"):
                setattr(cls, "__komodo_singulars__", [])
            getattr(cls, "__komodo_singulars__").append(field_name)
            return cls
        return decorator

    @staticmethod
    def accessors(fluent: bool = False, getter: bool = True, setter: bool = True, withers: bool = False) -> Callable[[C], C]:
        def decorator(cls: C) -> C:
            return apply_generator(cls, lambda c, t: generate_accessors(c, t, fluent, getter, setter, withers))
        return decorator
        
    @staticmethod
    def getter(cls: C) -> C:
        return apply_generator(cls, lambda c, t: generate_accessors(c, t, False, True, False, False))
        
    @staticmethod
    def setter(cls: C) -> C:
        return apply_generator(cls, lambda c, t: generate_accessors(c, t, False, False, True, False))
        
    @staticmethod
    def withers(cls: C) -> C:
        return apply_generator(cls, lambda c, t: generate_accessors(c, t, False, False, False, True))

    @staticmethod
    def logger(cls: C) -> C:
        return apply_generator(cls, generate_logger)

    @staticmethod
    def non_null(cls: C) -> C:
        return apply_generator(cls, generate_non_null)

    @staticmethod
    def validated(cls: C) -> C:
        return apply_generator(cls, generate_validated)

    @staticmethod
    def copyable(cls: C) -> C:
        return apply_generator(cls, generate_copyable)

    @staticmethod
    def to_dict(cls: C) -> C:
        return apply_generator(cls, generate_to_dict)

    @staticmethod
    def from_dict(cls: C) -> C:
        return apply_generator(cls, generate_from_dict)

    @staticmethod
    def json(cls: C) -> C:
        return apply_generator(cls, generate_json)

    @staticmethod
    def record(cls: C) -> C:
        return apply_generator(cls, generate_record)

    @staticmethod
    def equals_and_hashcode(cls: C) -> C:
        return apply_generator(cls, generate_eq_hash)

    @staticmethod
    def to_string(cls: C) -> C:
        return apply_generator(cls, generate_to_str)

komodo = _Komodo()
__all__ = ["komodo"]
