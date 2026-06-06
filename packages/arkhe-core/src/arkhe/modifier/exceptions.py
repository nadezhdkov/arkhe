"""
arkhe.modifier.exceptions
--------------------------
Exceptions raised on access-control violations.
"""

from __future__ import annotations


class AccessViolationError(Exception):
    """
    Raised when code outside the allowed scope tries to access a
    private or protected member.

    Attributes:
        member:     Name of the field or method that was accessed.
        visibility: ``"private"`` or ``"protected"``.
        caller:     Qualified name of the class/function that attempted access.
        owner:      Qualified name of the class that owns the member.
    """

    def __init__(
        self,
        member: str,
        visibility: str,
        caller: str,
        owner: str,
    ) -> None:
        self.member = member
        self.visibility = visibility
        self.caller = caller
        self.owner = owner
        super().__init__(
            f"[arkhe.modifier] {visibility} member '{member}' of '{owner}' "
            f"cannot be accessed from '{caller}'"
        )


class PrivateAccessError(AccessViolationError):
    """Raised when a ``@private`` member is accessed outside its own class."""

    def __init__(self, member: str, caller: str, owner: str) -> None:
        super().__init__(member, "private", caller, owner)


class ProtectedAccessError(AccessViolationError):
    """
    Raised when a ``@protected`` member is accessed from a class that is
    neither the owner nor a subclass of the owner.
    """

    def __init__(self, member: str, caller: str, owner: str) -> None:
        super().__init__(member, "protected", caller, owner)


__all__ = [
    "AccessViolationError",
    "PrivateAccessError",
    "ProtectedAccessError",
]
