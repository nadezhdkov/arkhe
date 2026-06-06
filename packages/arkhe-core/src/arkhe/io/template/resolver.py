"""
arkhe.io.template.resolver — Attribute and value resolver.

Handles:
  - Positional placeholders  ({0}, {1})
  - Attribute access         ({name})
  - Nested attribute paths   ({address.city})
  - No-arg method calls      ({display_name()})
  - System token lookup      ({date}, {uuid}, ...)

Resolution order:
  1. System token
  2. Positional index (if expression is a digit)
  3. Direct attribute / dict key on context
  4. Nested dotted path
  5. No-arg method call (expression ends with `()`)
"""

from .tokens import resolve_system_token, is_system_token
from typing import Any, Sequence, Optional

_MISSING = object()


def resolve(
    expression: str,
    context: Any,
    args: Sequence[Any] = (),
) -> Any:
    """
    Resolve an ATEL expression against a context object and
    optional positional args.

    Returns the resolved value, or raises AttributeError /
    IndexError if not found.
    """
    expr = expression.strip()

    # ── 1. System token ────────────────────────────────
    if is_system_token(expr):
        return resolve_system_token(expr)

    # ── 2. Positional index ─────────────────────────────
    if expr.isdigit():
        idx = int(expr)
        if idx < len(args):
            return args[idx]
        raise IndexError(f"ATEL: positional index {idx} out of range (got {len(args)} args)")

    # ── 3. Empty placeholder → next positional ──────────
    if expr == "":
        if args:
            return args[0]
        raise IndexError("ATEL: empty placeholder but no positional args supplied")

    # ── 4. Method call  display_name() ──────────────────
    if expr.endswith("()"):
        attr_name = expr[:-2]
        val = _resolve_attr(attr_name, context)
        if callable(val):
            return val()
        raise TypeError(f"ATEL: '{attr_name}' is not callable")

    # ── 5. Dotted attribute path  address.city ──────────
    if "." in expr:
        return _resolve_dotted(expr, context)

    # ── 6. Direct attribute / dict key ──────────────────
    return _resolve_attr(expr, context)


def _resolve_attr(name: str, obj: Any) -> Any:
    """Resolve a single attribute name against obj."""
    if obj is None:
        raise AttributeError(f"ATEL: cannot resolve '{name}' on None")

    # Dict-style access first
    if isinstance(obj, dict):
        if name in obj:
            return obj[name]
        raise AttributeError(f"ATEL: key '{name}' not found in dict")

    # Object attribute
    val = getattr(obj, name, _MISSING)
    if val is not _MISSING:
        return val

    raise AttributeError(f"ATEL: '{name}' not found on {type(obj).__name__}")


def _resolve_dotted(path: str, obj: Any) -> Any:
    """Walk a dotted path like 'address.city' on obj."""
    parts = path.split(".")
    current = obj
    for part in parts:
        current = _resolve_attr(part, current)
    return current


def resolve_safe(
    expression: str,
    context: Any,
    args: Sequence[Any] = (),
    default: Any = None,
) -> Any:
    """Like resolve(), but returns `default` instead of raising."""
    try:
        return resolve(expression, context, args)
    except (AttributeError, IndexError, TypeError, KeyError):
        return default
