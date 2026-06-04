"""
arkhe.collections._base
---------------------------
Shared protocols, type aliases, and sentinel values used across
the arkhe.collections package.
"""

from __future__ import annotations

from typing import TypeVar, Protocol, runtime_checkable, Any

# ---------------------------------------------------------------------------
# Type variables
# ---------------------------------------------------------------------------

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")
R = TypeVar("R")

# ---------------------------------------------------------------------------
# Sentinel
# ---------------------------------------------------------------------------

class _MissingType:
    """Singleton sentinel used to distinguish 'no value given' from None."""
    _instance: "_MissingType | None" = None

    def __new__(cls) -> "_MissingType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:  # pragma: no cover
        return "MISSING"

MISSING: Any = _MissingType()

# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------

@runtime_checkable
class Sized(Protocol):
    def __len__(self) -> int: ...

@runtime_checkable
class SupportsDunder(Protocol):
    """Protocol for objects that support comparison dunder methods."""
    def __lt__(self, other: Any) -> bool: ...
    def __le__(self, other: Any) -> bool: ...
    def __gt__(self, other: Any) -> bool: ...
    def __ge__(self, other: Any) -> bool: ...
