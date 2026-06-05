"""
arkhe.komodo.contract
-----------------------
Design-by-Contract decorators inspired by IntelliJ's ``@Contract`` annotation
and Eiffel's Hoare-triple model.

Provides:
- ``@contract`` decorator — declarative pre/post/invariant conditions
- ``ContractViolationError`` — raised on any contract failure
- DSL helpers: ``requires``, ``ensures``, ``invariant``
"""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


# ─────────────────────────────────────────────────────────────────────────────
#  Exception
# ─────────────────────────────────────────────────────────────────────────────

class ContractViolationError(Exception):
    """
    Raised when a contract precondition, postcondition, or invariant is violated.

    Attributes:
        kind:    One of ``"precondition"``, ``"postcondition"``, ``"invariant"``.
        func:    Name of the function whose contract was violated.
        message: Human-readable description of the violation.
    """
    def __init__(self, kind: str, func: str, message: str) -> None:
        self.kind = kind
        self.func = func
        self.message = message
        super().__init__(
            f"[komodo.contract] {kind} violated in '{func}': {message}"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Condition helpers
# ─────────────────────────────────────────────────────────────────────────────

class _Condition:
    """Internal wrapper for a single contract condition."""

    def __init__(
        self,
        predicate: Callable[..., bool],
        message: str,
        kind: str,  # "precondition" | "postcondition" | "invariant"
    ) -> None:
        self.predicate = predicate
        self.message = message
        self.kind = kind


def requires(
    predicate: Callable[..., bool],
    message: str = "precondition not satisfied",
) -> _Condition:
    """
    Declare a **precondition** — a constraint that must hold *before* the
    function executes.  The predicate receives the same ``*args`` and
    ``**kwargs`` as the decorated function.

    Example::

        @contract(
            requires(lambda x: x > 0, "x must be positive"),
        )
        def square_root(x: float) -> float:
            return x ** 0.5
    """
    return _Condition(predicate, message, "precondition")


def ensures(
    predicate: Callable[..., bool],
    message: str = "postcondition not satisfied",
) -> _Condition:
    """
    Declare a **postcondition** — a constraint on the *return value*.
    The predicate receives the return value as its sole argument.

    Example::

        @contract(
            ensures(lambda result: result >= 0, "result must be non-negative"),
        )
        def abs_value(x: float) -> float:
            return abs(x)
    """
    return _Condition(predicate, message, "postcondition")


def invariant(
    predicate: Callable[..., bool],
    message: str = "invariant violated",
) -> _Condition:
    """
    Declare an **invariant** — a constraint checked both before *and* after
    execution, typically operating on ``self`` for method contracts.

    Example::

        @contract(
            invariant(lambda self: self.balance >= 0, "balance must not be negative"),
        )
        def withdraw(self, amount: float) -> None:
            self.balance -= amount
    """
    return _Condition(predicate, message, "invariant")


# ─────────────────────────────────────────────────────────────────────────────
#  @contract decorator
# ─────────────────────────────────────────────────────────────────────────────

def contract(*conditions: _Condition) -> Callable[[F], F]:
    """
    Apply Design-by-Contract constraints to a function or method.

    Accepts any number of ``requires()``, ``ensures()``, and ``invariant()``
    conditions as positional arguments.  Conditions are evaluated in order;
    the first failure raises a ``ContractViolationError``.

    - ``requires`` predicates receive ``(*args, **kwargs)`` — the call arguments.
    - ``ensures`` predicates receive the return value.
    - ``invariant`` predicates receive ``(*args, **kwargs)`` *twice*: before and
      after execution (useful for checking ``self`` state in methods).

    Args:
        *conditions: One or more ``requires()``, ``ensures()``, ``invariant()``
                     instances.

    Returns:
        A decorator that wraps the target function with contract checks.

    Example::

        from arkhe.komodo import contract, requires, ensures

        @contract(
            requires(lambda x, y: y != 0, "divisor must not be zero"),
            ensures(lambda result: isinstance(result, float), "result must be float"),
        )
        def divide(x: float, y: float) -> float:
            return x / y
    """
    preconditions  = [c for c in conditions if c.kind == "precondition"]
    postconditions = [c for c in conditions if c.kind == "postcondition"]
    invariants     = [c for c in conditions if c.kind == "invariant"]

    def decorator(func: F) -> F:
        is_method = _is_method(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            fname = func.__qualname__

            # ── Pre-conditions ──────────────────────────────────────────────
            for cond in preconditions:
                try:
                    ok = cond.predicate(*args, **kwargs)
                except Exception as e:
                    raise ContractViolationError(
                        "precondition", fname,
                        f"{cond.message} (predicate raised: {e})"
                    ) from e
                if not ok:
                    raise ContractViolationError("precondition", fname, cond.message)

            # ── Invariants (before) ─────────────────────────────────────────
            for cond in invariants:
                try:
                    # Try with all args first, fall back to self only
                    try:
                        ok = cond.predicate(*args, **kwargs)
                    except TypeError:
                        ok = cond.predicate(args[0]) if args else cond.predicate()
                except Exception as e:
                    raise ContractViolationError(
                        "invariant", fname,
                        f"{cond.message} (before call, predicate raised: {e})"
                    ) from e
                if not ok:
                    raise ContractViolationError(
                        "invariant", fname,
                        f"{cond.message} (before call)"
                    )

            # ── Execute ─────────────────────────────────────────────────────
            result = func(*args, **kwargs)

            # ── Post-conditions ─────────────────────────────────────────────
            for cond in postconditions:
                try:
                    ok = cond.predicate(result)
                except Exception as e:
                    raise ContractViolationError(
                        "postcondition", fname,
                        f"{cond.message} (predicate raised: {e})"
                    ) from e
                if not ok:
                    raise ContractViolationError("postcondition", fname, cond.message)

            # ── Invariants (after) ──────────────────────────────────────────
            for cond in invariants:
                try:
                    try:
                        ok = cond.predicate(*args, **kwargs)
                    except TypeError:
                        ok = cond.predicate(args[0]) if args else cond.predicate()
                except Exception as e:
                    raise ContractViolationError(
                        "invariant", fname,
                        f"{cond.message} (after call, predicate raised: {e})"
                    ) from e
                if not ok:
                    raise ContractViolationError(
                        "invariant", fname,
                        f"{cond.message} (after call)"
                    )

            return result

        # Attach contract metadata for introspection
        wrapper.__contracts__ = {  # type: ignore
            "preconditions":  [(c.predicate, c.message) for c in preconditions],
            "postconditions": [(c.predicate, c.message) for c in postconditions],
            "invariants":     [(c.predicate, c.message) for c in invariants],
        }

        return wrapper  # type: ignore

    return decorator


# ─────────────────────────────────────────────────────────────────────────────
#  Utility
# ─────────────────────────────────────────────────────────────────────────────

def _is_method(func: Callable) -> bool:
    """Heuristic: first parameter named 'self' or 'cls' suggests a method."""
    try:
        params = list(inspect.signature(func).parameters)
        return bool(params) and params[0] in ("self", "cls")
    except (ValueError, TypeError):
        return False


__all__ = [
    "contract",
    "requires",
    "ensures",
    "invariant",
    "ContractViolationError",
]
