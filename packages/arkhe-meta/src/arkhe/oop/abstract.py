import inspect
import functools


class AbstractMethodError(Exception):
    pass


class InstantiationError(Exception):
    pass


class OverrideError(Exception):
    pass


class FinalClassError(Exception):
    pass


_ABSTRACT_CLASSES: set[type] = set()
_FINAL_CLASSES: set[type] = set()


# ---------------------------------------------------------------------------
# @abstract_class
# ---------------------------------------------------------------------------

def abstract_class(cls: type) -> type:
    """
    Marks a class as abstract.

    Abstract classes:
    - Cannot be instantiated directly.
    - May contain concrete methods, fields, and constructors.
    - Must declare abstract methods using @abstract_method.

    Subclasses are validated at definition time: if any abstract method
    is not implemented, AbstractMethodError is raised immediately.

    Usage:
        @abstract_class
        class Repository:
            @abstract_method
            def save(self, data):
                pass
    """
    if getattr(cls, "__is_abstract__", False):
        return cls

    _ABSTRACT_CLASSES.add(cls)

    original_init_subclass = cls.__dict__.get("__init_subclass__")

    def init_subclass_impl(subclass, **kwargs):
        # Dynamically find the actual class in the MRO that provides this method.
        # This handles cases where AST-based decorators (like @komodo) recompile
        # the class and create a new class object with the same methods.
        actual_cls = cls
        for base in subclass.__mro__:
            meth = base.__dict__.get("__init_subclass__")
            if meth and getattr(meth, "__func__", meth) is init_subclass_impl:
                actual_cls = base
                break

        if original_init_subclass:
            original_init_subclass.__func__(subclass, **kwargs)
        else:
            super(actual_cls, subclass).__init_subclass__(**kwargs)

        # Skip validation if the subclass itself is abstract.
        #
        # We check BOTH the registry and the __is_abstract__ flag because
        # of a timing issue with nested @abstract_class hierarchies:
        #
        #   @abstract_class          <- (1) registers Level1, installs hook
        #   class Level1: ...
        #
        #   @abstract_class          <- (3) decorator runs AFTER (2)
        #   class Level2(Level1):    <- (2) __init_subclass__ fires here,
        #       ...                         before Level2 is in the registry
        #
        # At step (2), Level2 is not yet in _ABSTRACT_CLASSES, so the
        # registry check alone would incorrectly validate it as concrete.
        # The __is_abstract__ flag is set by the decorator at step (3),
        # but that is too late for this hook. We therefore defer to the
        # presence of any @abstract_method in the subclass body as a
        # reliable signal that the class is itself abstract.
        if subclass in _ABSTRACT_CLASSES:
            return

        if _has_abstract_methods_in_body(subclass):
            return

        _validate_abstract_methods(actual_cls, subclass)

        # Validate @override markers
        _validate_overrides(subclass.__bases__, subclass.__dict__)

    cls.__init_subclass__ = classmethod(init_subclass_impl)

    # Prevent direct instantiation
    original_new = cls.__new__

    def new_impl(klass, *args, **kwargs):
        # Dynamically find the actual class to handle AST recompilation
        actual_cls = cls
        for base in klass.__mro__:
            meth = base.__dict__.get("__new__")
            if meth and getattr(meth, "__func__", meth) is new_impl:
                actual_cls = base
                break

        if klass is actual_cls:
            raise InstantiationError(
                f"\nInstantiationError\n\nCannot instantiate abstract class {actual_cls.__name__}"
            )
        if original_new is object.__new__:
            return object.__new__(klass)
        return original_new(klass, *args, **kwargs)

    cls.__new__ = new_impl
    cls.__is_abstract__ = True
    return cls


def _has_abstract_methods_in_body(cls: type) -> bool:
    """Return True if the class directly defines any @abstract_method."""
    for value in cls.__dict__.values():
        if getattr(value, "__is_abstract_method__", False):
            return True
    return False


def _validate_abstract_methods(abstract_cls: type, subclass: type) -> None:
    """Ensure the subclass implements every @abstract_method from abstract_cls."""
    missing: list[str] = []

    for name, member in inspect.getmembers(abstract_cls):
        if getattr(member, "__is_abstract_method__", False):
            # Check if subclass provides a concrete implementation
            impl = _get_own_member(subclass, name)
            if impl is None or getattr(impl, "__is_abstract_method__", False):
                sig = _format_signature(name, member)
                missing.append(sig)

    if missing:
        items = "\n".join(f" - {m}" for m in missing)
        raise AbstractMethodError(
            f"\nAbstractMethodError\n\n"
            f"Class {subclass.__name__} must implement:\n\n{items}"
        )


# ---------------------------------------------------------------------------
# @abstract_method
# ---------------------------------------------------------------------------

class abstract_method:
    """
    Marks a method inside an @abstract_class as abstract.

    Subclasses must override this method. Validation is done at class
    definition time via __init_subclass__.

    Usage:
        @abstract_method
        def save(self, data):
            pass
    """
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)
        self.__is_abstract_method__ = True

    def __set_name__(self, owner, name):
        if not getattr(owner, "__is_abstract__", False):
            abstract_class(owner)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if hasattr(self.func, "__get__"):
            return self.func.__get__(instance, owner)
        return self.func

    def __call__(self, *args, **kwargs):
        raise NotImplementedError(
            f"Abstract method '{self.func.__name__}' must be implemented by a subclass."
        )


# ---------------------------------------------------------------------------
# @override
# ---------------------------------------------------------------------------

class override:
    """
    Marks a method as intentionally overriding a parent class method.

    Raises OverrideError at class creation time if no parent defines
    a method with the same name.

    Usage:
        @override
        def save(self, data):
            ...
    """
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)
        self.__is_override__ = True

    def __set_name__(self, owner, name):
        _validate_overrides(owner.__bases__, {name: self})

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if hasattr(self.func, "__get__"):
            return self.func.__get__(instance, owner)
        return self.func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class _OverrideValidatingMeta(type):
    """
    Metaclass that validates @override methods at class definition time.

    Use this as the metaclass for any base class hierarchy that needs
    @override validation without depending on @abstract_class.
    """
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        if bases:  # skip the base class itself
            _validate_overrides(bases, namespace)
        return cls


def _validate_overrides(bases: tuple, namespace: dict) -> None:
    """Raise OverrideError if any @override method has no parent counterpart."""
    parent_method_names: set[str] = set()
    for base in bases:
        for klass in base.__mro__:
            parent_method_names.update(klass.__dict__.keys())

    for method_name, member in namespace.items():
        if callable(member) and getattr(member, "__is_override__", False):
            if method_name not in parent_method_names:
                raise OverrideError(
                    f"\nOverrideError\n\nMethod {method_name} does not override any parent method"
                )


# ---------------------------------------------------------------------------
# @final
# ---------------------------------------------------------------------------

def final(cls: type) -> type:
    """
    Marks a class as non-inheritable.

    Any attempt to subclass a @final class raises FinalClassError
    at class definition time.

    Usage:
        @final
        class Logger:
            pass
    """
    _FINAL_CLASSES.add(cls)

    original_init_subclass = cls.__dict__.get("__init_subclass__")

    @classmethod  # type: ignore[misc]
    def __init_subclass__(subclass, **kwargs):
        raise FinalClassError(
            f"\nFinalClassError\n\nClass {cls.__name__} cannot be extended"
        )

    cls.__init_subclass__ = __init_subclass__
    cls.__is_final__ = True
    return cls


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_own_member(cls: type, name: str):
    """Return a member defined in the class itself (or non-abstract ancestors)."""
    for klass in cls.__mro__:
        if klass is object:
            continue
        if name in klass.__dict__:
            return klass.__dict__[name]
    return None


def _format_signature(name: str, method) -> str:
    """Format a method signature for error messages."""
    try:
        sig = inspect.signature(method)
        params = []
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            annotation = param.annotation
            if annotation is inspect.Parameter.empty:
                params.append(param_name)
            else:
                type_name = getattr(annotation, "__name__", str(annotation))
                params.append(f"{param_name}: {type_name}")
        return f"{name}({', '.join(params)})"
    except (ValueError, TypeError):
        return name
