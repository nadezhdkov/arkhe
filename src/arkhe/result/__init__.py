"""
arkhe.result
----------------------------
A discriminated-union type for explicit error handling, inspired by
Rust's ``Result<T, E>`` and Kotlin's ``kotlin.Result``.

Instead of relying on exceptions for control flow, functions return a
``Result`` that is either:

* **Ok(value)** — the computation succeeded and holds the output.
* **Err(error)** — the computation failed and holds the error.

Callers inspect which variant they received and handle it explicitly,
making error paths visible at the type level.

Example::

    from arkhe.result import Result

    def parse_int(s: str) -> Result[int, str]:
        try:
            return Result.ok(int(s))
        except ValueError as exc:
            return Result.err(str(exc))

    value = (
        parse_int("42")
        .map(lambda n: n * 2)
        .get_or(0)
    )  # → 84

    parse_int("bad")
        .map_err(str.upper)
        .get_or_else(lambda e: f"Fallback because: {e}")
    # → "Fallback because: INVALID LITERAL FOR INT()..."
"""

from __future__ import annotations

from typing import Callable, Generic, Iterator, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")


class Result(Generic[T, E]):
    """
    An immutable container representing either success (``Ok``) or
    failure (``Err``).

    Use the factory methods :meth:`Result.ok` and :meth:`Result.err`
    to construct instances.
    """

    __slots__ = ("_value", "_error", "_is_ok")

    def __init__(self, *, value: object, error: object, is_ok: bool) -> None:
        self._value = value
        self._error = error
        self._is_ok = is_ok

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        """
        Create a successful Result wrapping *value*.

        Args:
            value (T): The success value.

        Returns:
            Result[T, E]: An Ok variant.
        """
        return cls(value=value, error=None, is_ok=True)

    @classmethod
    def err(cls, error: E) -> "Result[T, E]":
        """
        Create a failed Result wrapping *error*.

        Args:
            error (E): The error value.

        Returns:
            Result[T, E]: An Err variant.
        """
        return cls(value=None, error=error, is_ok=False)

    @classmethod
    def of(cls, fn: Callable[[], T], catch: type[Exception] | tuple[type[Exception], ...] = Exception) -> "Result[T, Exception]":
        """
        Run *fn* and wrap its outcome, catching *catch* exception types as Err.

        Args:
            fn (Callable[[], T]): Zero-argument callable to execute.
            catch: Exception type(s) to catch. Defaults to ``Exception``.

        Returns:
            Result[T, Exception]: Ok if *fn* succeeds, Err with the exception otherwise.
        """
        try:
            return cls.ok(fn())  # type: ignore[arg-type]
        except catch as exc:  # type: ignore[misc]
            return cls.err(exc)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def is_ok(self) -> bool:
        """Return ``True`` if this is an Ok variant."""
        return self._is_ok

    def is_err(self) -> bool:
        """Return ``True`` if this is an Err variant."""
        return not self._is_ok

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self) -> T:
        """
        Return the contained Ok value.

        Raises:
            ValueError: If this is an Err variant.

        Returns:
            T: The success value.
        """
        if not self._is_ok:
            raise ValueError(f"Result is Err({self._error!r}); cannot call get().")
        return self._value  # type: ignore[return-value]

    def get_err(self) -> E:
        """
        Return the contained Err value.

        Raises:
            ValueError: If this is an Ok variant.

        Returns:
            E: The error value.
        """
        if self._is_ok:
            raise ValueError(f"Result is Ok({self._value!r}); cannot call get_err().")
        return self._error  # type: ignore[return-value]

    def get_or(self, default: T) -> T:
        """
        Return the Ok value, or *default* if Err.

        Args:
            default (T): Fallback value.

        Returns:
            T: Ok value or default.
        """
        return self._value if self._is_ok else default  # type: ignore[return-value]

    def get_or_else(self, fn: Callable[[E], T]) -> T:
        """
        Return the Ok value, or call *fn* with the error and return its result.

        Args:
            fn (Callable[[E], T]): Error-handling function.

        Returns:
            T: Ok value or computed fallback.
        """
        if self._is_ok:
            return self._value  # type: ignore[return-value]
        return fn(self._error)  # type: ignore[arg-type]

    def get_or_raise(self) -> T:
        """
        Return the Ok value, or re-raise the Err value if it is an exception.

        Raises:
            Exception: The contained error if it is an Exception instance.
            ValueError: If the error is not an Exception instance.

        Returns:
            T: The Ok value.
        """
        if self._is_ok:
            return self._value  # type: ignore[return-value]
        if isinstance(self._error, BaseException):
            raise self._error
        raise ValueError(self._error)

    # ------------------------------------------------------------------
    # Transformation
    # ------------------------------------------------------------------

    def map(self, transform: Callable[[T], U]) -> "Result[U, E]":
        """
        Apply *transform* to the Ok value; propagate Err unchanged.

        Args:
            transform (Callable[[T], U]): Mapping function.

        Returns:
            Result[U, E]: Transformed Result.
        """
        if self._is_ok:
            return Result.ok(transform(self._value))  # type: ignore[arg-type]
        return Result.err(self._error)  # type: ignore[arg-type]

    def map_err(self, transform: Callable[[E], F]) -> "Result[T, F]":
        """
        Apply *transform* to the Err value; propagate Ok unchanged.

        Args:
            transform (Callable[[E], F]): Error mapping function.

        Returns:
            Result[T, F]: Transformed Result.
        """
        if not self._is_ok:
            return Result.err(transform(self._error))  # type: ignore[arg-type]
        return Result.ok(self._value)  # type: ignore[arg-type]

    def flat_map(self, transform: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """
        Apply *transform* which returns a Result, and flatten.

        Args:
            transform (Callable[[T], Result[U, E]]): Chaining function.

        Returns:
            Result[U, E]: Chained Result.
        """
        if self._is_ok:
            return transform(self._value)  # type: ignore[arg-type]
        return Result.err(self._error)  # type: ignore[arg-type]

    def recover(self, transform: Callable[[E], T]) -> "Result[T, E]":
        """
        Attempt to recover from an Err by applying *transform*.

        Args:
            transform (Callable[[E], T]): Recovery function.

        Returns:
            Result[T, E]: Ok with recovered value, or this Ok unchanged.
        """
        if not self._is_ok:
            return Result.ok(transform(self._error))  # type: ignore[arg-type]
        return self

    def if_ok(self, action: Callable[[T], None]) -> "Result[T, E]":
        """Execute *action* if Ok; supports chaining."""
        if self._is_ok:
            action(self._value)  # type: ignore[arg-type]
        return self

    def if_err(self, action: Callable[[E], None]) -> "Result[T, E]":
        """Execute *action* if Err; supports chaining."""
        if not self._is_ok:
            action(self._error)  # type: ignore[arg-type]
        return self

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __bool__(self) -> bool:
        return self._is_ok

    def __iter__(self) -> Iterator[T]:
        """Yield the Ok value once, enabling ``value, = result`` unpacking."""
        if self._is_ok:
            yield self._value  # type: ignore[misc]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Result):
            return self._is_ok == other._is_ok and self._value == other._value and self._error == other._error
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._is_ok, self._value, self._error))

    def __repr__(self) -> str:
        if self._is_ok:
            return f"Result.ok({self._value!r})"
        return f"Result.err({self._error!r})"
