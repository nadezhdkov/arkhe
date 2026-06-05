from __future__ import annotations
from typing import Any


class DBResult:
    """
    Returned by execute_safe() — never raises, always inspectable.
    """

    __slots__ = ("is_success", "data", "error", "error_message")

    def __init__(
        self,
        is_success: bool,
        data: Any = None,
        error: Exception | None = None,
        error_message: str | None = None,
    ) -> None:
        self.is_success: bool = is_success
        self.data: Any = data
        self.error: Exception | None = error
        self.error_message: str | None = error_message

    @classmethod
    def success(cls, data: Any = None) -> "DBResult":
        return cls(is_success=True, data=data)

    @classmethod
    def failure(cls, error: Exception) -> "DBResult":
        return cls(
            is_success=False,
            error=error,
            error_message=str(error),
        )

    def __repr__(self) -> str:
        if self.is_success:
            return f"DBResult(success, data={self.data!r})"
        return f"DBResult(failure, error_message={self.error_message!r})"
