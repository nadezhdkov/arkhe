"""
arkhe.io.helpers — Message-type wrappers.

These are returned by success(), warning(), error(), info()
and detected by the custom print() hook to render the
appropriate panel layout.
"""


class _ArkheMessage:
    __slots__ = ("message", "level")

    def __init__(self, message: str, level: str):
        self.message = message
        self.level = level

    def __repr__(self):
        return f"<ArkheMessage level={self.level!r} message={self.message!r}>"


def success(message: str) -> _ArkheMessage:
    """Mark a message for Success panel rendering."""
    return _ArkheMessage(message, "success")


def warning(message: str) -> _ArkheMessage:
    """Mark a message for Warning panel rendering."""
    return _ArkheMessage(message, "warning")


def error(message: str) -> _ArkheMessage:
    """Mark a message for Error panel rendering."""
    return _ArkheMessage(message, "error")


def info(message: str) -> _ArkheMessage:
    """Mark a message for Info panel rendering."""
    return _ArkheMessage(message, "info")
