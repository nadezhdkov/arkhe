"""
arkhe.loom.schema
----------------------
Schema binding system — binds Loom scopes to Python dataclasses.

Implements spec §19 and §19.1:
    - @loom.bind("module", scope="db.main") decorator
    - Automatic fallback to dataclass field defaults
    - LoomSchemaError for required fields with no value and no default
    - Runtime type coercion from LoomValue to declared field type
"""

from __future__ import annotations

import dataclasses
import typing
from typing import Any, Callable, Optional, Type, TypeVar

from arkhe.loom.exceptions import LoomSchemaError

C = TypeVar("C")

# Runtime reference to the active Loom instance (set by LoomRuntime)
_active_runtime: Optional[Any] = None


def _set_active_runtime(runtime: Any) -> None:
    global _active_runtime
    _active_runtime = runtime


# ─────────────────────────────────────────────────────────────────────────────
#  @loom.bind
# ─────────────────────────────────────────────────────────────────────────────

def bind(module: str, scope: str = "") -> Callable[[Type[C]], Type[C]]:
    """
    Bind a dataclass to a Loom module/scope path.

    When the decorated class is instantiated, field values are resolved
    from the active Loom runtime.  Dataclass field defaults act as
    fallbacks when no runtime value is found.

    Raises ``LoomSchemaError`` when:
        - A required field has no runtime value AND no dataclass default.

    Example::

        @loom.bind("database", scope="db.main")
        @dataclasses.dataclass
        class DbConfig:
            host: str = "127.0.0.1"
            port: int = 5432
            debug: bool = False

        # With runtime:
        cfg = DbConfig()
        print(cfg.host)   # value from Loom or "127.0.0.1" fallback
    """
    def decorator(cls: Type[C]) -> Type[C]:
        if not dataclasses.is_dataclass(cls):
            raise TypeError(
                f"@loom.bind can only be applied to dataclasses. "
                f"Add @dataclasses.dataclass before @loom.bind on '{cls.__name__}'."
            )

        # Save original __init__
        original_init = cls.__init__

        def __init__(self: Any, **kwargs: Any) -> None:
            resolved = _resolve_schema(cls, module, scope, kwargs)
            original_init(self, **resolved)

        cls.__init__ = __init__  # type: ignore
        cls.__loom_module__ = module  # type: ignore
        cls.__loom_scope__ = scope    # type: ignore
        return cls

    return decorator


def _resolve_schema(
    cls: type,
    module_name: str,
    scope_path: str,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    """
    Build kwargs for a dataclass __init__ by merging:
        priority 1: explicit kwargs (from user)
        priority 2: Loom runtime values
        priority 3: dataclass field defaults
    """
    fields = {f.name: f for f in dataclasses.fields(cls)}  # type: ignore
    resolved: dict[str, Any] = {}
    hints = typing.get_type_hints(cls)

    for field_name, field in fields.items():
        # Priority 1: explicit kwargs
        if field_name in overrides:
            resolved[field_name] = overrides[field_name]
            continue

        # Priority 2: Loom runtime
        runtime_val = _lookup_runtime(module_name, scope_path, field_name)
        if runtime_val is not None:
            resolved[field_name] = _coerce(runtime_val, hints.get(field_name), field_name, cls.__name__)
            continue

        # Priority 3: dataclass default
        if field.default is not dataclasses.MISSING:
            resolved[field_name] = field.default
            continue
        if field.default_factory is not dataclasses.MISSING:  # type: ignore
            resolved[field_name] = field.default_factory()  # type: ignore
            continue

        # No value anywhere → LoomSchemaError
        raise LoomSchemaError(
            f"Required field '{field_name}' of '{cls.__name__}' has no value "
            f"in Loom scope '{module_name}.{scope_path}' and no default.",
            hint=(
                f"Either add a value to your .loom file under "
                f"@module(\"{module_name}\") ... scope '{scope_path}', "
                f"or define a default: {field_name}: <default_value> in the dataclass."
            ),
        )

    return resolved


def _lookup_runtime(module: str, scope: str, key: str) -> Optional[Any]:
    """Try to fetch a value from the active Loom runtime."""
    if _active_runtime is None:
        return None
    try:
        path_parts = [module] + scope.split(".") + [key] if scope else [module, key]
        result = _active_runtime._resolver.resolve(path_parts)
        from arkhe.loom.scope import LoomValue
        return result._value if isinstance(result, LoomValue) else result
    except Exception:
        return None


def _coerce(value: Any, expected_type: Optional[type], field_name: str, cls_name: str) -> Any:
    """Coerce a raw Loom value to the declared dataclass field type."""
    if expected_type is None or value is None:
        return value

    # Unwrap Optional[X]
    origin = getattr(expected_type, "__origin__", None)
    args = getattr(expected_type, "__args__", ())
    if origin is typing.Union and type(None) in args:
        # Optional — use the non-None type
        non_none = [a for a in args if a is not type(None)]
        expected_type = non_none[0] if len(non_none) == 1 else None

    if expected_type is None:
        return value

    if isinstance(value, expected_type):
        return value

    # Type coercion
    try:
        if expected_type is bool:
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "on", "1")
            return bool(value)
        return expected_type(value)
    except (TypeError, ValueError) as e:
        from arkhe.loom.exceptions import LoomTypeError
        raise LoomTypeError(
            f"Cannot coerce field '{cls_name}.{field_name}' value {value!r} "
            f"to {expected_type.__name__}",
            hint=f"Check the value in your .loom file.",
        ) from e


__all__ = ["bind", "_set_active_runtime"]
