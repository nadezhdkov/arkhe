"""
nestifypy/komodo/__init__.pyi
------------------------------
Type stubs for the komodo decorator namespace.

Strategy: each decorator is typed as returning Type[C & <Mixin>] via a
TypeVar-bound overload pattern that IDEs (Pylance, PyCharm) understand,
so generated methods like __init__, builder(), to_dict(), copy_with() etc.
show up in autocomplete without any plugin.
"""

from typing import (
    Any, Callable, ClassVar, Dict, List, Optional, Protocol,
    Set, Tuple, Type, TypeVar, overload, runtime_checkable,
)
import logging

C = TypeVar("C", bound=type)
T = TypeVar("T")

# ---------------------------------------------------------------------------
# Protocol mixins — each describes what a decorator injects
# ---------------------------------------------------------------------------

class _ConstructorProto(Protocol):
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class _ReprProto(Protocol):
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...

class _EqProto(Protocol):
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...

class _ImmutableProto(Protocol):
    def __setattr__(self, name: str, value: object) -> None: ...
    def __delattr__(self, name: str) -> None: ...

class _CopyableProto(Protocol):
    def copy(self) -> Any: ...
    def copy_with(self, **overrides: Any) -> Any: ...

class _SerializationProto(Protocol):
    def to_dict(self) -> Dict[str, Any]: ...
    def to_json(self) -> str: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any: ...
    @classmethod
    def from_json(cls, data: str) -> Any: ...

class _LoggerProto(Protocol):
    logger: ClassVar[logging.Logger]

class _BuilderProto(Protocol):
    """
    Describes the builder() classmethod and the inner Builder class.
    The inner Builder has with_<field>() methods — those are generated
    per-class in the .pyi stubs written next to the decorated module.
    """
    class Builder(Protocol):
        def build(self) -> Any: ...
    @classmethod
    def builder(cls) -> Any: ...  # returns cls.Builder

# ---------------------------------------------------------------------------
# Composite type aliases used as return types for the composite decorators
# ---------------------------------------------------------------------------

class _DataClass(
    _ConstructorProto, _ReprProto, _EqProto,
    _CopyableProto, _SerializationProto, Protocol
): ...

class _ValueClass(
    _DataClass, _ImmutableProto, Protocol
): ...

class _RecordClass(
    _ConstructorProto, _ReprProto, _EqProto,
    _ImmutableProto, _SerializationProto, Protocol
): ...

# ---------------------------------------------------------------------------
# _Komodo — the komodo decorator namespace
# ---------------------------------------------------------------------------

class _Komodo:
    """
    Lombok-style annotation-driven metaprogramming for Python.

    Decorators are composable and stackable. Each one generates dunder methods,
    builders, validators, or serializers via AST rewriting at class definition
    time — zero runtime overhead after import.

    IDE support: decorators return typed Protocol intersections so PyCharm,
    Pylance, and mypy resolve generated members without a plugin. Per-class
    .pyi files are also written automatically.
    """

    # -- Composite decorators ------------------------------------------------

    @overload
    @staticmethod
    def data(cls: Type[C]) -> Type[C]: ...  # keeps original class type
    @staticmethod
    def data(cls: Type[C]) -> Type[C]:
        """
        Composite: constructor + to_str + eq + copyable + serialization.

        Generated members:
            __init__(**fields)
            __repr__() / __str__()
            __eq__() / __hash__()
            copy() / copy_with(**overrides)
            to_dict() / from_dict() / to_json() / from_json()
        """
        ...

    @staticmethod
    def value(cls: Type[C]) -> Type[C]:
        """
        Composite: @komodo.data + @komodo.immutable.

        Produces an immutable value type with full equality and serialization.
        """
        ...

    @staticmethod
    def record(cls: Type[C]) -> Type[C]:
        """
        Composite: constructor + repr + eq + immutable + serialization.

        Similar to a frozen dataclass but with JSON/dict serialization built in.
        """
        ...

    # -- Individual decorators -----------------------------------------------

    @staticmethod
    def constructor(cls: Type[C]) -> Type[C]:
        """
        Generates __init__ from annotated fields.

        Required fields come first, optional fields (with defaults) follow.
        Calls __post_init__(self) if defined.
        """
        ...

    @staticmethod
    def no_args_constructor(cls: Type[C]) -> Type[C]:
        """Generates __init__(self) with no parameters."""
        ...

    @staticmethod
    def required_args_constructor(cls: Type[C]) -> Type[C]:
        """Generates __init__ accepting only required (no-default) fields."""
        ...

    @staticmethod
    def all_args_constructor(cls: Type[C]) -> Type[C]:
        """Generates __init__ accepting all fields, with defaults for optional ones."""
        ...

    @staticmethod
    def to_str(cls: Type[C]) -> Type[C]:
        """Generates __repr__ and __str__ in the form ClassName(field=value, ...)."""
        ...

    @staticmethod
    def to_string(cls: Type[C]) -> Type[C]:
        """Alias for @komodo.to_str."""
        ...

    @staticmethod
    def eq(cls: Type[C]) -> Type[C]:
        """
        Generates __eq__ and __hash__ based on all annotated fields.

        __hash__ falls back to id(self) if a field is unhashable.
        """
        ...

    @staticmethod
    def equals_and_hashcode(cls: Type[C]) -> Type[C]:
        """Alias for @komodo.eq."""
        ...

    @staticmethod
    def immutable(cls: Type[C]) -> Type[C]:
        """
        Makes the class read-only after __init__ completes.

        Injects __setattr__ / __delattr__ that raise AttributeError once
        the object is frozen.  The _frozen flag is set at the end of __init__.
        """
        ...

    @staticmethod
    def builder(cls: Type[C]) -> Type[C]:
        """
        Generates a fluent Builder inner class.

        For a class with fields url: str, method: str = "GET":

            HttpRequest.builder()
                .with_url("https://...")
                .with_method("POST")
                .build()

        The inner Builder class and per-field with_<name>() / singular methods
        are documented in the per-class .pyi stub generated next to the source.
        """
        ...

    @staticmethod
    def singular(field_name: str) -> Callable[[Type[C]], Type[C]]:
        """
        Marks a list field for the builder's singular append pattern.

        Example:
            @komodo.singular("tags")
            @komodo.builder
            class Post:
                tags: list[str]

            # Enables: Post.builder().tag("python").tag("ast").build()
        """
        ...

    @staticmethod
    def accessors(
        fluent: bool = False,
        getter: bool = True,
        setter: bool = True,
        withers: bool = False,
    ) -> Callable[[Type[C]], Type[C]]:
        """
        Generates accessor methods.

        fluent=True   → single method acts as getter when called with no args,
                        setter when called with one arg, returns self.
        getter=True   → get_<field>() / @property
        setter=True   → set_<field>() / @property.setter
        withers=True  → with_<field>(value) returning a shallow copy
        """
        ...

    @staticmethod
    def getter(cls: Type[C]) -> Type[C]:
        """Shorthand: accessors(getter=True, setter=False)."""
        ...

    @staticmethod
    def setter(cls: Type[C]) -> Type[C]:
        """Shorthand: accessors(getter=False, setter=True)."""
        ...

    @staticmethod
    def withers(cls: Type[C]) -> Type[C]:
        """
        Shorthand: accessors(withers=True).

        Generates with_<field>(value) that returns a copy of the object
        with that field overridden.
        """
        ...

    @staticmethod
    def logger(cls: Type[C]) -> Type[C]:
        """
        Injects a logging.Logger as a class-level attribute named 'logger'.

            cls.logger.info("Hello from %s", cls.__name__)
        """
        ...

    @staticmethod
    def non_null(cls: Type[C]) -> Type[C]:
        """
        Adds None-checks for all fields in __init__.

        Raises ValueError('<ClassName>: field <name> must not be None').
        """
        ...

    @staticmethod
    def validated(cls: Type[C]) -> Type[C]:
        """
        Adds isinstance type checks for all simple-typed fields in __init__.

        Raises TypeError('<ClassName>: field <name> expected <type>').
        Only validates fields annotated with a plain name (str, int, etc.),
        not generics like list[str].
        """
        ...

    @staticmethod
    def copyable(cls: Type[C]) -> Type[C]:
        """
        Generates copy() and copy_with(**overrides) methods.

        copy()              → shallow copy via copy.copy()
        copy_with(**kw)     → returns a new instance with specified fields replaced
        """
        ...

    @staticmethod
    def to_dict(cls: Type[C]) -> Type[C]:
        """Generates to_dict() → Dict[str, Any] method."""
        ...

    @staticmethod
    def from_dict(cls: Type[C]) -> Type[C]:
        """Generates from_dict(data: dict) classmethod."""
        ...

    @staticmethod
    def json(cls: Type[C]) -> Type[C]:
        """Generates to_json() → str and from_json(data: str) classmethod."""
        ...


komodo: _Komodo

# ---------------------------------------------------------------------------
# contract DSL
# ---------------------------------------------------------------------------

class ContractViolationError(Exception):
    """Raised when a @contract condition is violated."""
    kind: str    # "precondition" | "postcondition" | "invariant"
    func: str    # qualified name of the function
    message: str # human-readable description

def contract(*conditions: Any) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Apply Design-by-Contract conditions to a function or method.

    Example:
        @contract(
            requires(lambda x: x > 0, "x must be positive"),
            ensures(lambda r: r >= 0, "result non-negative"),
        )
        def sqrt(x: float) -> float: ...
    """
    ...

def requires(predicate: Callable[..., bool], message: str = ...) -> Any:
    """Precondition: checked before the function runs."""
    ...

def ensures(predicate: Callable[..., bool], message: str = ...) -> Any:
    """Postcondition: predicate receives the return value."""
    ...

def invariant(predicate: Callable[..., bool], message: str = ...) -> Any:
    """Invariant: checked before and after execution (useful on methods)."""
    ...

# ---------------------------------------------------------------------------
# KomodoInspector
# ---------------------------------------------------------------------------

class KomodoInspector:
    """
    Runtime introspection for komodo-decorated classes.

    Example:
        info = KomodoInspector(User)
        print(info.features)          # {'data', 'builder', ...}
        print(info.fields)            # {'name': str, 'age': int}
        print(info.summary())         # pretty table
        print(info.contract_info("save"))  # contract conditions dict
    """
    def __init__(self, cls: type) -> None: ...

    @property
    def features(self) -> Set[str]: ...

    @property
    def fields(self) -> Dict[str, Any]: ...

    @property
    def defaults(self) -> Dict[str, Any]: ...

    @property
    def generated_methods(self) -> List[str]: ...

    @property
    def has_builder(self) -> bool: ...

    @property
    def is_immutable(self) -> bool: ...

    @property
    def is_record(self) -> bool: ...

    def contract_info(self, method_name: str) -> Optional[Dict[str, Any]]: ...
    def summary(self) -> str: ...

# ---------------------------------------------------------------------------
# Stub generation utilities
# ---------------------------------------------------------------------------

class StubGenerator:
    """
    Generates .pyi stub content for a single Komodo-decorated class.

    Usually called automatically.  Use manually when you want to inspect
    or write stub content yourself:

        gen = StubGenerator(MyClass)
        print(gen.generate_stub())
    """
    def __init__(self, cls: type) -> None: ...
    def generate_stub(self) -> str: ...

def generate_and_write_stub(cls: type, output_dir: Optional[str] = None) -> str:
    """Write a .pyi stub for cls and return the path to the created file."""
    ...
