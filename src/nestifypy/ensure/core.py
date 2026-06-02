"""
nestifypy.ensure.core
----------------------
API estática de validação — métodos de classe prontos para uso direto.

::

    from nestifypy.ensure import Ensure

    name  = Ensure.not_blank(name)
    age   = Ensure.positive(age)
    user  = Ensure.not_none(user)
    email = Ensure.matches(email, EMAIL_REGEX)
"""

from __future__ import annotations

import re
from typing import Any, Callable, Container, Iterable, Sized, Type, TypeVar, Union

from nestifypy.ensure.exceptions import EnsureValueError, EnsureTypeError
from nestifypy.ensure.chain import EnsureChain

T = TypeVar("T")


class Ensure:
    """
    Ponto de entrada único para todas as validações.

    Dois estilos de uso:

    **Estático** — retorna o valor validado::

        name  = Ensure.not_blank(name)
        price = Ensure.positive(price)

    **Fluente** — cadeia encadeável::

        name = (
            Ensure.that(name)
                .not_none()
                .not_blank()
                .min_length(3)
                .unwrap()
        )
    """

    # ── fluent entry-point ────────────────────────────────────────────────

    @classmethod
    def that(cls, value: T, name: str = "value") -> EnsureChain[T]:
        """
        Inicia uma cadeia fluente de validações.

        ::

            result = Ensure.that(username).not_blank().min_length(3).unwrap()
        """
        return EnsureChain(value, name)

    # ── null ──────────────────────────────────────────────────────────────

    @staticmethod
    def not_none(value: T, msg: str | None = None) -> T:
        """Garante que value não é None."""
        if value is None:
            raise EnsureValueError(msg or "Value must not be None")
        return value

    @staticmethod
    def is_none(value: Any, msg: str | None = None) -> None:
        """Garante que value é None."""
        if value is not None:
            raise EnsureValueError(msg or f"Value must be None, got {value!r}")

    # ── string ────────────────────────────────────────────────────────────

    @staticmethod
    def not_empty(value: T, msg: str | None = None) -> T:
        """Garante que value tem len() > 0. Funciona com str, list, dict, set, tuple."""
        if isinstance(value, Sized) and len(value) == 0:  # type: ignore[arg-type]
            raise EnsureValueError(msg or "Value must not be empty")
        return value

    @staticmethod
    def not_blank(value: str, msg: str | None = None) -> str:
        """Garante que a string não é vazia nem composta só de espaços."""
        if not isinstance(value, str):
            raise EnsureTypeError(f"not_blank requires str, got {type(value).__name__}")
        if not value.strip():
            raise EnsureValueError(msg or "Value must not be blank")
        return value

    @staticmethod
    def min_length(value: T, length: int, msg: str | None = None) -> T:
        if not isinstance(value, Sized):
            raise EnsureTypeError("min_length requires a Sized type")
        if len(value) < length:  # type: ignore[arg-type]
            raise EnsureValueError(
                msg or f"Value must have at least {length} characters, got {len(value)}"  # type: ignore[arg-type]
            )
        return value

    @staticmethod
    def max_length(value: T, length: int, msg: str | None = None) -> T:
        if not isinstance(value, Sized):
            raise EnsureTypeError("max_length requires a Sized type")
        if len(value) > length:  # type: ignore[arg-type]
            raise EnsureValueError(
                msg or f"Value must have at most {length} characters, got {len(value)}"  # type: ignore[arg-type]
            )
        return value

    @staticmethod
    def matches(value: str, pattern: Union[str, "re.Pattern[str]"], msg: str | None = None) -> str:
        if not isinstance(value, str):
            raise EnsureTypeError(f"matches requires str, got {type(value).__name__}")
        if not re.fullmatch(pattern, value):
            raise EnsureValueError(msg or f"Value does not match the required pattern")
        return value

    @staticmethod
    def starts_with(value: str, prefix: str, msg: str | None = None) -> str:
        if not isinstance(value, str):
            raise EnsureTypeError(f"starts_with requires str, got {type(value).__name__}")
        if not value.startswith(prefix):
            raise EnsureValueError(msg or f"Value must start with {prefix!r}")
        return value

    @staticmethod
    def ends_with(value: str, suffix: str, msg: str | None = None) -> str:
        if not isinstance(value, str):
            raise EnsureTypeError(f"ends_with requires str, got {type(value).__name__}")
        if not value.endswith(suffix):
            raise EnsureValueError(msg or f"Value must end with {suffix!r}")
        return value

    # ── numérico ──────────────────────────────────────────────────────────

    @staticmethod
    def positive(value: T, msg: str | None = None) -> T:
        if value <= 0:  # type: ignore[operator]
            raise EnsureValueError(msg or f"Value must be positive, got {value!r}")
        return value

    @staticmethod
    def negative(value: T, msg: str | None = None) -> T:
        if value >= 0:  # type: ignore[operator]
            raise EnsureValueError(msg or f"Value must be negative, got {value!r}")
        return value

    @staticmethod
    def non_negative(value: T, msg: str | None = None) -> T:
        if value < 0:  # type: ignore[operator]
            raise EnsureValueError(msg or f"Value must be non-negative, got {value!r}")
        return value

    @staticmethod
    def greater_than(value: T, threshold: Any, msg: str | None = None) -> T:
        if not (value > threshold):  # type: ignore[operator]
            raise EnsureValueError(msg or f"Value must be > {threshold!r}, got {value!r}")
        return value

    @staticmethod
    def greater_or_equal(value: T, threshold: Any, msg: str | None = None) -> T:
        if not (value >= threshold):  # type: ignore[operator]
            raise EnsureValueError(msg or f"Value must be >= {threshold!r}, got {value!r}")
        return value

    @staticmethod
    def less_than(value: T, threshold: Any, msg: str | None = None) -> T:
        if not (value < threshold):  # type: ignore[operator]
            raise EnsureValueError(msg or f"Value must be < {threshold!r}, got {value!r}")
        return value

    @staticmethod
    def less_or_equal(value: T, threshold: Any, msg: str | None = None) -> T:
        if not (value <= threshold):  # type: ignore[operator]
            raise EnsureValueError(msg or f"Value must be <= {threshold!r}, got {value!r}")
        return value

    @staticmethod
    def between(value: T, low: Any, high: Any, msg: str | None = None) -> T:
        if not (low <= value <= high):  # type: ignore[operator]
            raise EnsureValueError(
                msg or f"Value must be between {low!r} and {high!r}, got {value!r}"
            )
        return value

    # ── coleção ───────────────────────────────────────────────────────────

    @staticmethod
    def contains(value: Any, item: Any, msg: str | None = None) -> Any:
        if item not in value:
            raise EnsureValueError(msg or f"Value must contain {item!r}")
        return value

    @staticmethod
    def not_contains(value: Any, item: Any, msg: str | None = None) -> Any:
        if item in value:
            raise EnsureValueError(msg or f"Value must not contain {item!r}")
        return value

    @staticmethod
    def unique(value: T, msg: str | None = None) -> T:
        try:
            items = list(value)  # type: ignore[call-overload]
        except TypeError:
            raise EnsureTypeError("unique requires an iterable")
        if len(items) != len(set(items)):  # type: ignore[arg-type]
            raise EnsureValueError(msg or "Value must not contain duplicates")
        return value

    # ── tipo ──────────────────────────────────────────────────────────────

    @staticmethod
    def is_instance(value: Any, type_: Type[T], msg: str | None = None) -> T:
        if not isinstance(value, type_):
            raise EnsureTypeError(
                msg or f"Value must be an instance of {type_.__name__}, got {type(value).__name__}"
            )
        return value  # type: ignore[return-value]

    @staticmethod
    def is_subclass(value: Any, parent: type, msg: str | None = None) -> Any:
        if not (isinstance(value, type) and issubclass(value, parent)):
            raise EnsureTypeError(
                msg or f"Value must be a subclass of {parent.__name__}"
            )
        return value

    @staticmethod
    def is_callable(value: T, msg: str | None = None) -> T:
        if not callable(value):
            raise EnsureTypeError(msg or "Value must be callable")
        return value

    # ── estado ────────────────────────────────────────────────────────────

    @staticmethod
    def is_true(value: Any, msg: str | None = None) -> Any:
        if not value:
            raise EnsureValueError(msg or "Value must be True")
        return value

    @staticmethod
    def is_false(value: Any, msg: str | None = None) -> Any:
        if value:
            raise EnsureValueError(msg or "Value must be False")
        return value

    # ── igualdade ─────────────────────────────────────────────────────────

    @staticmethod
    def equals(value: T, other: Any, msg: str | None = None) -> T:
        if value != other:
            raise EnsureValueError(msg or f"Value must equal {other!r}, got {value!r}")
        return value

    @staticmethod
    def not_equals(value: T, other: Any, msg: str | None = None) -> T:
        if value == other:
            raise EnsureValueError(msg or f"Value must not equal {other!r}")
        return value

    # ── pertencimento ─────────────────────────────────────────────────────

    @staticmethod
    def one_of(value: T, options: Container[Any], msg: str | None = None) -> T:
        if value not in options:
            raise EnsureValueError(
                msg or f"Value must be one of {list(options)!r}, got {value!r}"
            )
        return value

    @staticmethod
    def not_one_of(value: T, options: Container[Any], msg: str | None = None) -> T:
        if value in options:
            raise EnsureValueError(
                msg or f"Value must not be one of {list(options)!r}"
            )
        return value


__all__ = ["Ensure"]
