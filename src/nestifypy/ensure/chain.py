"""
nestifypy.ensure.chain
-----------------------
API fluente encadeável de validação.

::

    name = (
        Ensure.that(name)
            .not_none()
            .not_blank()
            .min_length(3)
            .max_length(50)
            .unwrap()
    )

    username = (
        Ensure.that(username)
            .not_blank()
            .map(str.strip)
            .map(str.lower)
            .unwrap()
    )
"""

from __future__ import annotations

import re
from typing import Any, Callable, Container, Generic, Iterable, Pattern, Sized, Type, TypeVar, Union

from nestifypy.ensure.exceptions import EnsureValueError, EnsureTypeError

T = TypeVar("T")
U = TypeVar("U")


class EnsureChain(Generic[T]):
    """
    Cadeia de validações fluentes para um único valor.

    Instanciada por ``Ensure.that(value)``.
    Todos os métodos retornam ``self`` para permitir encadeamento.
    Use ``.unwrap()`` para recuperar o valor validado.
    """

    __slots__ = ("_value", "_name")

    def __init__(self, value: T, name: str = "value") -> None:
        self._value = value
        self._name = name

    # ── recuperação ───────────────────────────────────────────────────────

    def unwrap(self) -> T:
        """Retorna o valor validado (possivelmente transformado por .map())."""
        return self._value

    # ── transformação ─────────────────────────────────────────────────────

    def map(self, fn: Callable[[T], U]) -> "EnsureChain[U]":
        """
        Transforma o valor com a função fornecida.

        ::

            Ensure.that("  Hope  ").not_blank().map(str.strip).map(str.lower).unwrap()
            # → "hope"
        """
        self._value = fn(self._value)  # type: ignore[assignment]
        return self  # type: ignore[return-value]

    # ── null ──────────────────────────────────────────────────────────────

    def not_none(self, msg: str | None = None) -> "EnsureChain[T]":
        if self._value is None:
            raise EnsureValueError(msg or f"{self._name} must not be None")
        return self

    def is_none(self, msg: str | None = None) -> "EnsureChain[T]":
        if self._value is not None:
            raise EnsureValueError(msg or f"{self._name} must be None, got {self._value!r}")
        return self

    # ── string ────────────────────────────────────────────────────────────

    def not_empty(self, msg: str | None = None) -> "EnsureChain[T]":
        if isinstance(self._value, Sized):
            if len(self._value) == 0:  # type: ignore[arg-type]
                raise EnsureValueError(msg or f"{self._name} must not be empty")
        return self

    def not_blank(self, msg: str | None = None) -> "EnsureChain[T]":
        if not isinstance(self._value, str):
            raise EnsureTypeError(f"{self._name} must be a str for not_blank, got {type(self._value).__name__}")
        if not self._value.strip():
            raise EnsureValueError(msg or f"{self._name} must not be blank")
        return self

    def min_length(self, length: int, msg: str | None = None) -> "EnsureChain[T]":
        if not isinstance(self._value, Sized):
            raise EnsureTypeError(f"{self._name} does not support len()")
        if len(self._value) < length:  # type: ignore[arg-type]
            raise EnsureValueError(
                msg or f"{self._name} must have at least {length} characters, got {len(self._value)}"  # type: ignore[arg-type]
            )
        return self

    def max_length(self, length: int, msg: str | None = None) -> "EnsureChain[T]":
        if not isinstance(self._value, Sized):
            raise EnsureTypeError(f"{self._name} does not support len()")
        if len(self._value) > length:  # type: ignore[arg-type]
            raise EnsureValueError(
                msg or f"{self._name} must have at most {length} characters, got {len(self._value)}"  # type: ignore[arg-type]
            )
        return self

    def matches(self, pattern: Union[str, "re.Pattern[str]"], msg: str | None = None) -> "EnsureChain[T]":
        if not isinstance(self._value, str):
            raise EnsureTypeError(f"{self._name} must be a str for matches()")
        if not re.fullmatch(pattern, self._value):
            raise EnsureValueError(msg or f"{self._name} does not match the required pattern")
        return self

    def starts_with(self, prefix: str, msg: str | None = None) -> "EnsureChain[T]":
        if not isinstance(self._value, str):
            raise EnsureTypeError(f"{self._name} must be a str for starts_with()")
        if not self._value.startswith(prefix):
            raise EnsureValueError(msg or f"{self._name} must start with {prefix!r}")
        return self

    def ends_with(self, suffix: str, msg: str | None = None) -> "EnsureChain[T]":
        if not isinstance(self._value, str):
            raise EnsureTypeError(f"{self._name} must be a str for ends_with()")
        if not self._value.endswith(suffix):
            raise EnsureValueError(msg or f"{self._name} must end with {suffix!r}")
        return self

    # ── numérico ──────────────────────────────────────────────────────────

    def positive(self, msg: str | None = None) -> "EnsureChain[T]":
        if self._value <= 0:  # type: ignore[operator]
            raise EnsureValueError(msg or f"{self._name} must be positive, got {self._value!r}")
        return self

    def negative(self, msg: str | None = None) -> "EnsureChain[T]":
        if self._value >= 0:  # type: ignore[operator]
            raise EnsureValueError(msg or f"{self._name} must be negative, got {self._value!r}")
        return self

    def non_negative(self, msg: str | None = None) -> "EnsureChain[T]":
        if self._value < 0:  # type: ignore[operator]
            raise EnsureValueError(msg or f"{self._name} must be non-negative, got {self._value!r}")
        return self

    def greater_than(self, threshold: Any, msg: str | None = None) -> "EnsureChain[T]":
        if not (self._value > threshold):  # type: ignore[operator]
            raise EnsureValueError(msg or f"{self._name} must be > {threshold!r}, got {self._value!r}")
        return self

    def greater_or_equal(self, threshold: Any, msg: str | None = None) -> "EnsureChain[T]":
        if not (self._value >= threshold):  # type: ignore[operator]
            raise EnsureValueError(msg or f"{self._name} must be >= {threshold!r}, got {self._value!r}")
        return self

    def less_than(self, threshold: Any, msg: str | None = None) -> "EnsureChain[T]":
        if not (self._value < threshold):  # type: ignore[operator]
            raise EnsureValueError(msg or f"{self._name} must be < {threshold!r}, got {self._value!r}")
        return self

    def less_or_equal(self, threshold: Any, msg: str | None = None) -> "EnsureChain[T]":
        if not (self._value <= threshold):  # type: ignore[operator]
            raise EnsureValueError(msg or f"{self._name} must be <= {threshold!r}, got {self._value!r}")
        return self

    def between(self, low: Any, high: Any, msg: str | None = None) -> "EnsureChain[T]":
        if not (low <= self._value <= high):  # type: ignore[operator]
            raise EnsureValueError(
                msg or f"{self._name} must be between {low!r} and {high!r}, got {self._value!r}"
            )
        return self

    # ── coleção ───────────────────────────────────────────────────────────

    def contains(self, item: Any, msg: str | None = None) -> "EnsureChain[T]":
        if item not in self._value:  # type: ignore[operator]
            raise EnsureValueError(msg or f"{self._name} must contain {item!r}")
        return self

    def not_contains(self, item: Any, msg: str | None = None) -> "EnsureChain[T]":
        if item in self._value:  # type: ignore[operator]
            raise EnsureValueError(msg or f"{self._name} must not contain {item!r}")
        return self

    def unique(self, msg: str | None = None) -> "EnsureChain[T]":
        try:
            items = list(self._value)  # type: ignore[call-overload]
        except TypeError:
            raise EnsureTypeError(f"{self._name} is not iterable")
        if len(items) != len(set(items)):  # type: ignore[arg-type]
            raise EnsureValueError(msg or f"{self._name} must not contain duplicates")
        return self

    # ── tipo ──────────────────────────────────────────────────────────────

    def is_instance(self, type_: type, msg: str | None = None) -> "EnsureChain[T]":
        if not isinstance(self._value, type_):
            raise EnsureTypeError(
                msg or f"{self._name} must be an instance of {type_.__name__}, got {type(self._value).__name__}"
            )
        return self

    def is_subclass(self, parent: type, msg: str | None = None) -> "EnsureChain[T]":
        if not (isinstance(self._value, type) and issubclass(self._value, parent)):  # type: ignore[arg-type]
            raise EnsureTypeError(
                msg or f"{self._name} must be a subclass of {parent.__name__}"
            )
        return self

    def is_callable(self, msg: str | None = None) -> "EnsureChain[T]":
        if not callable(self._value):
            raise EnsureTypeError(msg or f"{self._name} must be callable")
        return self

    # ── estado ────────────────────────────────────────────────────────────

    def is_true(self, msg: str | None = None) -> "EnsureChain[T]":
        if not self._value:
            raise EnsureValueError(msg or f"{self._name} must be True")
        return self

    def is_false(self, msg: str | None = None) -> "EnsureChain[T]":
        if self._value:
            raise EnsureValueError(msg or f"{self._name} must be False")
        return self

    # ── igualdade ─────────────────────────────────────────────────────────

    def equals(self, other: Any, msg: str | None = None) -> "EnsureChain[T]":
        if self._value != other:
            raise EnsureValueError(msg or f"{self._name} must equal {other!r}, got {self._value!r}")
        return self

    def not_equals(self, other: Any, msg: str | None = None) -> "EnsureChain[T]":
        if self._value == other:
            raise EnsureValueError(msg or f"{self._name} must not equal {other!r}")
        return self

    # ── pertencimento ─────────────────────────────────────────────────────

    def one_of(self, options: Container[Any], msg: str | None = None) -> "EnsureChain[T]":
        if self._value not in options:
            raise EnsureValueError(msg or f"{self._name} must be one of {list(options)!r}, got {self._value!r}")
        return self

    def not_one_of(self, options: Container[Any], msg: str | None = None) -> "EnsureChain[T]":
        if self._value in options:
            raise EnsureValueError(msg or f"{self._name} must not be one of {list(options)!r}")
        return self

    # ── repr ──────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"EnsureChain({self._value!r})"


__all__ = ["EnsureChain"]
