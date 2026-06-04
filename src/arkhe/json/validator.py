"""
arkhe.json.validator
------------------------
Schema validation for JSON objects and ``@json_serializable`` instances.

Improvements over the original
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Nested schema validation (dicts inside dicts).
* ``Optional[T]`` — field may be absent or ``None``.
* ``List[T]`` — validates every element in an array.
* ``Annotated[T, FieldConstraint(...)]`` — value-level constraints:
    - ``min`` / ``max``   for numbers
    - ``min_len`` / ``max_len`` for strings and lists
    - ``regex``           for strings
    - ``choices``         for any equality-comparable value
* Errors include the full dot-path to the failing field.
* ``validate_instance`` works on ``@json_serializable`` objects directly.
"""
from __future__ import annotations

import re
import typing
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional, Type, Union

from arkhe.json.exceptions import JsonValidationError
from arkhe.json.models import JsonObject


# ---------------------------------------------------------------------------
# FieldConstraint — value-level metadata for Annotated schemas
# ---------------------------------------------------------------------------

@dataclass
class FieldConstraint:
    """
    Attach value constraints to a schema field via ``typing.Annotated``.

    Example::

        from typing import Annotated
        schema = {
            "age":   Annotated[int,   FieldConstraint(min=0, max=150)],
            "name":  Annotated[str,   FieldConstraint(min_len=1, max_len=100)],
            "email": Annotated[str,   FieldConstraint(regex=r".+@.+\\..+")],
            "role":  Annotated[str,   FieldConstraint(choices=["admin", "user"])],
        }
    """
    min:     Optional[float] = None
    max:     Optional[float] = None
    min_len: Optional[int]   = None
    max_len: Optional[int]   = None
    regex:   Optional[str]   = None
    choices: Optional[list]  = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _origin(tp: Any) -> Any:
    return getattr(tp, "__origin__", None)


def _args(tp: Any) -> tuple:
    return getattr(tp, "__args__", ()) or ()


def _is_optional(tp: Any) -> tuple[bool, Any]:
    """Return ``(True, inner_type)`` if *tp* is ``Optional[X]``."""
    if _origin(tp) is Union:
        args = [a for a in _args(tp) if a is not type(None)]
        if len(_args(tp)) == 2 and type(None) in _args(tp):
            return True, args[0]
    return False, tp


def _is_list(tp: Any) -> tuple[bool, Any]:
    """Return ``(True, element_type)`` if *tp* is ``List[X]``."""
    if _origin(tp) in (list, List):
        args = _args(tp)
        return True, args[0] if args else Any
    return False, Any


def _unwrap_annotated(tp: Any) -> tuple[Any, Optional[FieldConstraint]]:
    """
    Return ``(base_type, constraint_or_None)`` for an ``Annotated`` type.
    Falls through unchanged for non-Annotated types.
    """
    if _origin(tp) is typing.Annotated if hasattr(typing, "Annotated") else False:
        base, *metadata = _args(tp)
        constraint = next((m for m in metadata if isinstance(m, FieldConstraint)), None)
        return base, constraint
    # Python 3.8 compatibility path
    try:
        import typing_extensions as te
        if _origin(tp) is te.Annotated:
            base, *metadata = _args(tp)
            constraint = next((m for m in metadata if isinstance(m, FieldConstraint)), None)
            return base, constraint
    except ImportError:
        pass
    return tp, None


def _apply_constraint(
    value: Any,
    constraint: FieldConstraint,
    path: str,
    errors: List[str],
) -> None:
    if constraint.min is not None and isinstance(value, (int, float)):
        if value < constraint.min:
            errors.append(f"'{path}': value {value} is less than minimum {constraint.min}")
    if constraint.max is not None and isinstance(value, (int, float)):
        if value > constraint.max:
            errors.append(f"'{path}': value {value} exceeds maximum {constraint.max}")
    if constraint.min_len is not None and hasattr(value, "__len__"):
        if len(value) < constraint.min_len:
            errors.append(
                f"'{path}': length {len(value)} is less than min_len {constraint.min_len}"
            )
    if constraint.max_len is not None and hasattr(value, "__len__"):
        if len(value) > constraint.max_len:
            errors.append(
                f"'{path}': length {len(value)} exceeds max_len {constraint.max_len}"
            )
    if constraint.regex is not None and isinstance(value, str):
        if not re.fullmatch(constraint.regex, value):
            errors.append(f"'{path}': value {value!r} does not match pattern {constraint.regex!r}")
    if constraint.choices is not None:
        if value not in constraint.choices:
            errors.append(
                f"'{path}': value {value!r} is not one of {constraint.choices}"
            )


def _validate_value(
    value: Any,
    expected_type: Any,
    path: str,
    errors: List[str],
) -> None:
    """Recursively validate a single value against its schema type."""
    # 1. Unwrap Annotated
    base_type, constraint = _unwrap_annotated(expected_type)

    # 2. Handle Optional
    is_opt, inner = _is_optional(base_type)
    if is_opt:
        if value is None:
            return  # None is valid for Optional
        base_type = inner
        base_type, constraint2 = _unwrap_annotated(base_type)
        if constraint2 and constraint is None:
            constraint = constraint2

    # 3. Handle List[T]
    is_lst, elem_type = _is_list(base_type)
    if is_lst:
        if not isinstance(value, list):
            errors.append(f"'{path}': expected list, got {type(value).__name__}")
            return
        for i, item in enumerate(value):
            _validate_value(item, elem_type, f"{path}[{i}]", errors)
        if constraint:
            _apply_constraint(value, constraint, path, errors)
        return

    # 4. Handle nested dict schema
    if isinstance(base_type, dict):
        if not isinstance(value, dict):
            errors.append(f"'{path}': expected object, got {type(value).__name__}")
            return
        _validate_dict(value, base_type, path, errors)
        return

    # 5. Primitive / class type check
    if base_type is Any or base_type is typing.Any:
        pass  # no check
    elif not isinstance(value, base_type):
        errors.append(
            f"'{path}': expected {getattr(base_type, '__name__', str(base_type))}, "
            f"got {type(value).__name__}"
        )
        return

    # 6. Apply value constraints
    if constraint:
        _apply_constraint(value, constraint, path, errors)


def _validate_dict(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    prefix: str,
    errors: List[str],
) -> None:
    """Validate *data* against a flat-or-nested *schema* dict."""
    for key, expected_type in schema.items():
        path = f"{prefix}.{key}" if prefix else key

        # Determine if the field is Optional (and thus not required)
        base, _ = _unwrap_annotated(expected_type)
        is_opt, _ = _is_optional(base)

        if key not in data:
            if is_opt:
                continue  # absent Optional is fine
            errors.append(f"'{path}': required field is missing")
            continue

        _validate_value(data[key], expected_type, path, errors)


# ---------------------------------------------------------------------------
# JsonValidator
# ---------------------------------------------------------------------------

class JsonValidator:
    """Schema validation for dicts and ``@json_serializable`` instances."""

    @staticmethod
    def validate(
        data: Union[Dict[str, Any], Any],
        schema: Dict[str, Any],
    ) -> bool:
        """
        Validate *data* against *schema*.

        *schema* values may be:
        * A plain type: ``int``, ``str``, ``bool``, …
        * ``Optional[T]``
        * ``List[T]``
        * ``Annotated[T, FieldConstraint(...)]``
        * A nested ``dict`` (for nested object validation)

        Returns ``True`` on success; raises ``JsonValidationError`` on failure.

        Example::

            from typing import Annotated, List, Optional
            schema = {
                "title":  str,
                "fps":    Annotated[int, FieldConstraint(min=1, max=240)],
                "tags":   List[str],
                "author": Optional[str],
                "meta": {
                    "version": str,
                }
            }
            JsonValidator.validate(data, schema)
        """
        # Accept @json_serializable instances by converting to dict first
        if hasattr(data, "to_dict") and callable(data.to_dict):
            data = data.to_dict()

        if not isinstance(data, dict):
            raise JsonValidationError(
                f"validate() expects a dict or @json_serializable instance, "
                f"got {type(data).__name__}"
            )

        errors: List[str] = []
        _validate_dict(data, schema, "", errors)

        if errors:
            raise JsonValidationError(
                "JSON validation failed:\n" + "\n".join(f"  • {e}" for e in errors),
                errors=errors,
            )

        return True

    @staticmethod
    def validate_instance(instance: Any, schema: Dict[str, Any]) -> bool:
        """Convenience alias — validates a ``@json_serializable`` instance."""
        return JsonValidator.validate(instance, schema)


__all__ = ["JsonValidator", "FieldConstraint"]
