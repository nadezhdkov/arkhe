import inspect
from typing import Any


class InterfaceImplementationError(Exception):
    pass


_INTERFACE_REGISTRY: dict[type, set[str]] = {}


def interface(cls: type) -> type:
    """
    Marks a class as an interface.

    An interface defines a contract: method signatures and/or attributes
    that any implementing class must provide. Interfaces may inherit from
    other interfaces, accumulating all requirements.

    Usage:
        @interface
        class ILogger:
            def log(self, message: str) -> None:
                pass
    """
    required_methods: set[str] = set()
    required_attrs: set[str] = set()

    # Collect requirements from parent interfaces
    for base in cls.__mro__[1:]:
        if base in _INTERFACE_REGISTRY:
            required_methods.update(_INTERFACE_REGISTRY[base].get("methods", set()))
            required_attrs.update(_INTERFACE_REGISTRY[base].get("attrs", set()))

    # Collect methods defined in this interface (excluding dunder)
    for name, member in inspect.getmembers(cls):
        if name.startswith("__"):
            continue
        if callable(member):
            required_methods.add(name)

    # Collect annotated attributes.
    # Exclude entries that are actually declared as methods in the class body.
    for name, annotation in cls.__annotations__.items():
        if name not in required_methods:
            required_attrs.add(name)

    _INTERFACE_REGISTRY[cls] = {
        "methods": required_methods,
        "attrs": required_attrs,
    }

    cls.__is_interface__ = True
    return cls


def implements(*interfaces: type) -> type:
    """
    Declares that a class implements one or more interfaces.

    Validates immediately at class definition time (fail-fast) that all
    required methods and attributes are present. Raises
    InterfaceImplementationError with a descriptive message if any are missing.

    Usage:
        @implements(ILogger)
        class ConsoleLogger:
            def log(self, message: str) -> None:
                print(message)
    """
    def decorator(cls: type) -> type:
        missing: list[str] = []

        for iface in interfaces:
            if iface not in _INTERFACE_REGISTRY:
                raise TypeError(
                    f"{iface.__name__} is not decorated with @interface"
                )

            requirements = _INTERFACE_REGISTRY[iface]

            # Validate required methods
            for method_name in requirements.get("methods", set()):
                member = _get_member(cls, method_name)
                if member is None or not callable(member):
                    # Build signature from interface for the error message
                    iface_method = _get_member(iface, method_name)
                    sig = _format_signature(method_name, iface_method)
                    missing.append(sig)

            # Validate required attributes
            all_annotations: dict = {}
            for klass in reversed(cls.__mro__):
                all_annotations.update(getattr(klass, "__annotations__", {}))

            for attr_name in requirements.get("attrs", set()):
                if attr_name not in all_annotations:
                    # Try to retrieve annotation from interface for type hint
                    annotation = iface.__annotations__.get(attr_name, Any)
                    type_name = getattr(annotation, "__name__", str(annotation))
                    missing.append(f"{attr_name}: {type_name}")

        if missing:
            items = "\n".join(f" - {m}" for m in missing)
            raise InterfaceImplementationError(
                f"\nInterfaceImplementationError\n\n"
                f"Class {cls.__name__} does not implement:\n\n{items}"
            )

        cls.__implements__ = getattr(cls, "__implements__", []) + list(interfaces)
        return cls

    return decorator


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_member(cls: type, name: str):
    """Return a member from the class dict (not inherited from object)."""
    for klass in cls.__mro__:
        if klass is object:
            continue
        if name in klass.__dict__:
            return klass.__dict__[name]
    return None


def _format_signature(name: str, method) -> str:
    """Format a method signature for error messages."""
    if method is None:
        return name
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
        param_str = ", ".join(params)
        # Return annotation
        ret = sig.return_annotation
        if ret is inspect.Parameter.empty:
            return f"{name}({param_str})"
        ret_name = getattr(ret, "__name__", str(ret))
        return f"{name}({param_str}) -> {ret_name}"
    except (ValueError, TypeError):
        return name
