"""
nestifypy.loom.exceptions
--------------------------
All Loom runtime exception types with Rust-style diagnostic formatting.

Every exception carries structured context (file, line, column, token)
and renders a developer-friendly snippet with correction hints.
"""

from __future__ import annotations

from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
#  ANSI helpers (graceful degradation on non-TTY)
# ─────────────────────────────────────────────────────────────────────────────

import sys

_USE_COLOR = sys.stderr.isatty() if hasattr(sys.stderr, "isatty") else False


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def _red(t: str) -> str:    return _c("31;1", t)
def _yellow(t: str) -> str: return _c("33;1", t)
def _cyan(t: str) -> str:   return _c("36;1", t)
def _bold(t: str) -> str:   return _c("1", t)
def _dim(t: str) -> str:    return _c("2", t)


# ─────────────────────────────────────────────────────────────────────────────
#  Diagnostic formatter
# ─────────────────────────────────────────────────────────────────────────────

def _format_diagnostic(
    kind: str,
    name: str,
    message: str,
    filename: Optional[str] = None,
    line: Optional[int] = None,
    column: Optional[int] = None,
    source_lines: Optional[list[str]] = None,
    got: Optional[str] = None,
    expected: Optional[str] = None,
    hint: Optional[str] = None,
) -> str:
    parts: list[str] = []

    # Header
    icon = "🚨" if kind == "error" else "⚠️"
    loc = ""
    if filename:
        loc = f" in '{filename}'"
        if line is not None:
            loc += f" (Line {line})"
    parts.append(f"{icon} {_red(name)}{loc}\n")

    # Code snippet — show 2 lines before + culprit + 2 lines after
    if source_lines and line is not None:
        start = max(0, line - 3)
        end = min(len(source_lines), line + 2)
        for i in range(start, end):
            lineno = i + 1
            src = source_lines[i].rstrip()
            prefix = f"  {lineno:>3} | "
            if lineno == line:
                parts.append(_bold(prefix) + src)
                if column is not None:
                    pointer = " " * (len(prefix) + column - 1) + _red("^")
                    parts.append(pointer)
            else:
                parts.append(_dim(prefix) + src)
        parts.append("")

    # Error description
    parts.append(_bold("Error:"))
    parts.append(f"  {message}\n")

    # Got / Expected
    if got:
        parts.append(_bold("Found:"))
        parts.append(f"  {got}\n")
    if expected:
        parts.append(_bold("Expected:"))
        parts.append(f"  {expected}\n")

    # Hint
    if hint:
        parts.append(_yellow("Hint:"))
        parts.append(f"  {hint}\n")

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
#  Base
# ─────────────────────────────────────────────────────────────────────────────

class LoomError(Exception):
    """Base class for all Loom exceptions."""

    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        source_lines: Optional[list[str]] = None,
        got: Optional[str] = None,
        expected: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> None:
        self.filename = filename
        self.line = line
        self.column = column
        self.source_lines = source_lines
        self.got = got
        self.expected = expected
        self.hint = hint

        diagnostic = _format_diagnostic(
            kind="error",
            name=self.__class__.__name__,
            message=message,
            filename=filename,
            line=line,
            column=column,
            source_lines=source_lines,
            got=got,
            expected=expected,
            hint=hint,
        )
        super().__init__(diagnostic)


# ─────────────────────────────────────────────────────────────────────────────
#  Concrete exception types
# ─────────────────────────────────────────────────────────────────────────────

class LoomSyntaxError(LoomError):
    """Raised when the parser encounters invalid syntax."""


class LoomTypeError(LoomError):
    """Raised when a value cannot be coerced to the expected type."""


class LoomResolutionError(LoomError):
    """Raised when a path cannot be resolved in the runtime tree."""


class LoomAmbiguityError(LoomError):
    """
    Raised when a flattened path resolves to multiple candidates
    and no Default Scope resolves the conflict.
    """


class LoomImportError(LoomError):
    """Raised when an @import directive fails."""


class LoomSchemaError(LoomError):
    """
    Raised when a required schema field has no runtime value
    and no schema default is defined.
    """


class LoomScopeConflictError(LoomError):
    """Raised when multiple Default Scopes exist at the same hierarchy level."""


__all__ = [
    "LoomError",
    "LoomSyntaxError",
    "LoomTypeError",
    "LoomResolutionError",
    "LoomAmbiguityError",
    "LoomImportError",
    "LoomSchemaError",
    "LoomScopeConflictError",
]
