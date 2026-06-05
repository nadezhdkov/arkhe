"""
arkhe.utils.optional
------------------------------
A type-safe container for an optional value, inspired by Java's
``Optional<T>`` and Kotlin's nullable types.

Instead of returning ``None`` and risking ``NoneType`` errors, wrap
uncertain values in ``Optional`` and use its fluent API to transform,
filter, or provide defaults — all without a single ``if value is not None``
guard in your application code.

Example::

    from arkhe.utils import Optional

    result = (
        Optional.of_nullable(user_input)
        .map(str.strip)
        .filter(bool)           # discard empty strings
        .map(int)
        .get_or(0)
    )
"""

from __future__ import annotations

from typing import Callable, Generic, Iterator, TypeVar, Union, overload

from arkhe.collections._base import MISSING, U

T = TypeVar("T")


class Optional(Generic[T]):
    """
    An immutable container that either holds a non-``None`` value (*present*)
    or is empty (*absent*).

    Do **not** instantiate directly; use the class-level factory methods:

    * :meth:`Optional.of` — value is guaranteed to be present (raises if None).
    * :meth:`Optional.of_nullable` — value may or may not be None.
    * :meth:`Optional.empty` — explicitly absent.
    """

    __slots__ = ("_value",)

    def __init__(self, value: object) -> None:  # noqa: ANN001
        self._value = value

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def of(cls, value: T) -> "Optional[T]":
        """
        Create a *present* Optional wrapping *value*.

        Args:
            value (T): A non-``None`` value.

        Raises:
            ValueError: If *value* is ``None``.

        Returns:
            Optional[T]: A present Optional.
        """
        if value is None:
            raise ValueError("Optional.of() received None; use Optional.of_nullable() instead.")
        return cls(value)

    @classmethod
    def of_nullable(cls, value: T | None) -> "Optional[T]":
        """
        Create an Optional that is present when *value* is not ``None``,
        and empty otherwise.

        Args:
            value (T | None): Any value, including ``None``.

        Returns:
            Optional[T]: Present Optional or empty Optional.
        """
        return cls(value)

    @classmethod
    def empty(cls) -> "Optional[T]":
        """
        Create an explicitly empty Optional.

        Returns:
            Optional[T]: An empty Optional instance.
        """
        return cls(None)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def is_present(self) -> bool:
        """Return ``True`` if a value is present."""
        return self._value is not None

    def is_empty(self) -> bool:
        """Return ``True`` if no value is present."""
        return self._value is None

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self) -> T:
        """
        Return the contained value.

        Raises:
            ValueError: If the Optional is empty.

        Returns:
            T: The contained value.
        """
        if self._value is None:
            raise ValueError("Optional is empty; use get_or() or get_or_else() for safe access.")
        return self._value  # type: ignore[return-value]

    def get_or(self, default: T) -> T:
        """
        Return the contained value, or *default* if empty.

        Args:
            default (T): Fallback value.

        Returns:
            T: The contained or default value.
        """
        return self._value if self._value is not None else default  # type: ignore[return-value]

    def get_or_else(self, supplier: Callable[[], T]) -> T:
        """
        Return the contained value, or call *supplier* and return its result.

        Args:
            supplier (Callable[[], T]): A zero-argument callable used lazily.

        Returns:
            T: The contained or supplied value.
        """
        return self._value if self._value is not None else supplier()  # type: ignore[return-value]

    def get_or_raise(self, exception: Exception) -> T:
        """
        Return the contained value, or raise *exception* if empty.

        Args:
            exception (Exception): The exception to raise.

        Raises:
            Exception: The provided exception if empty.

        Returns:
            T: The contained value.
        """
        if self._value is None:
            raise exception
        return self._value  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Transformation
    # ------------------------------------------------------------------

    def map(self, transform: Callable[[T], U | None]) -> "Optional[U]":
        """
        Apply *transform* to the value if present, returning a new Optional.

        If the Optional is empty, or *transform* returns ``None``, the result
        is also empty.

        Args:
            transform (Callable[[T], U | None]): Mapping function.

        Returns:
            Optional[U]: Transformed Optional.
        """
        if self._value is None:
            return Optional.empty()
        return Optional.of_nullable(transform(self._value))  # type: ignore[arg-type]

    def flat_map(self, transform: Callable[[T], "Optional[U]"]) -> "Optional[U]":
        """
        Apply *transform*, which itself returns an Optional, and flatten.

        Args:
            transform (Callable[[T], Optional[U]]): Function returning an Optional.

        Returns:
            Optional[U]: Flattened result.
        """
        if self._value is None:
            return Optional.empty()
        return transform(self._value)  # type: ignore[arg-type]

    def filter(self, predicate: Callable[[T], bool]) -> "Optional[T]":
        """
        Return this Optional if the value satisfies *predicate*, else empty.

        Args:
            predicate (Callable[[T], bool]): Test function.

        Returns:
            Optional[T]: This Optional or empty.
        """
        if self._value is not None and predicate(self._value):  # type: ignore[arg-type]
            return self
        return Optional.empty()

    def or_else(self, alternative: "Optional[T]") -> "Optional[T]":
        """
        Return this Optional if present, otherwise return *alternative*.

        Args:
            alternative (Optional[T]): Fallback Optional.

        Returns:
            Optional[T]: This or the alternative.
        """
        return self if self._value is not None else alternative

    def if_present(self, action: Callable[[T], None]) -> "Optional[T]":
        """
        Execute *action* with the value if present; supports chaining.

        Args:
            action (Callable[[T], None]): Side-effecting function.

        Returns:
            Optional[T]: This Optional (unchanged).
        """
        if self._value is not None:
            action(self._value)  # type: ignore[arg-type]
        return self

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[T]:
        """Yield the value once if present, making Optional usable in for-loops."""
        if self._value is not None:
            yield self._value  # type: ignore[misc]

    def __bool__(self) -> bool:
        return self._value is not None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Optional):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        if self._value is None:
            return "Optional.empty()"
        return f"Optional.of({self._value!r})"
