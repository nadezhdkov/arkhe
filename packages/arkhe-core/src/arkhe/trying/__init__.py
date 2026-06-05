"""
arkhe.trying — Functional error handling with Try/Success/Failure monads.

Usage:
    from arkhe.trying import Try, Success, Failure

    result = Try.of(lambda: int("42"))  # Success(42)
    result = Try.of(lambda: int("abc")) # Failure(ValueError)
"""

from arkhe.trying.trying import (
    Try,
    Success,
    Failure,
    TryError,
    FilterError,
    EmptyValueError,
)

__all__ = [
    "Try",
    "Success",
    "Failure",
    "TryError",
    "FilterError",
    "EmptyValueError",
]
