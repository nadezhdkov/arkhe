"""
arkhe.text.builder — High-performance mutable string builder.

Inspired by Java's StringBuilder. Internally accumulates fragments
in a list and joins them only on build(), avoiding repeated
string concatenation.

Usage:
    from arkhe.text import StringBuilder

    result = (
        StringBuilder()
            .append("[INFO] ")
            .append_template("{name} joined the server.", player)
            .append_line()
            .append_repeat("-", 40)
            .build()
    )
"""

from __future__ import annotations

from typing import Any, Iterable, Optional


class StringBuilder:
    """
    Mutable, chainable string builder.

    All append_* methods return `self` for fluent chaining.
    Call build() to obtain the final str.
    """

    __slots__ = ("_parts",)

    def __init__(self, initial: str = "") -> None:
        self._parts: list[str] = []
        if initial:
            self._parts.append(initial)

    # ──────────────────────────────────────────────────
    # Core append operations
    # ──────────────────────────────────────────────────

    def append(self, value: Any = "") -> "StringBuilder":
        """
        Append `value` converted to str.

        >>> StringBuilder().append("Hello").append(", World").build()
        'Hello, World'
        """
        self._parts.append(str(value))
        return self

    def append_line(self, value: Any = "") -> "StringBuilder":
        """
        Append `value` followed by a newline.

        >>> StringBuilder().append_line("Hello").append_line("World").build()
        'Hello\\nWorld\\n'
        """
        self._parts.append(str(value) + "\n")
        return self

    def append_repeat(self, value: str, times: int) -> "StringBuilder":
        """
        Append `value` repeated `times` times.

        >>> StringBuilder().append_repeat("=", 5).build()
        '====='
        """
        self._parts.append(value * times)
        return self

    def append_join(self, separator: str, items: Iterable[Any]) -> "StringBuilder":
        """
        Append items joined by `separator`.

        >>> StringBuilder().append_join(", ", ["A", "B", "C"]).build()
        'A, B, C'
        """
        self._parts.append(separator.join(str(i) for i in items))
        return self

    def append_if(self, condition: bool, value: Any, else_value: Any = "") -> "StringBuilder":
        """
        Append `value` if `condition` is True, else `else_value`.

        >>> StringBuilder().append_if(True, "yes", "no").build()
        'yes'
        """
        self._parts.append(str(value) if condition else str(else_value))
        return self

    def append_each(self, items: Iterable[Any], separator: str = "") -> "StringBuilder":
        """
        Append each item individually, separated by `separator`.

        >>> StringBuilder().append_each(["a", "b", "c"], " | ").build()
        'a | b | c'
        """
        parts = [str(i) for i in items]
        self._parts.append(separator.join(parts))
        return self

    def append_template(self, template: str, context: Any, *args: Any) -> "StringBuilder":
        """
        Render an ATEL template and append the result.

        Integrates directly with Arkhe's Template Engine (arkhe.io.template).

        >>> StringBuilder().append_template("{name} joined.", player).build()
        'Samuel joined.'
        """
        from arkhe.io.template.engine import render
        self._parts.append(render(template, context, *args))
        return self

    def append_lines(self, *lines: Any) -> "StringBuilder":
        """
        Append multiple values, each on its own line.

        >>> StringBuilder().append_lines("A", "B", "C").build()
        'A\\nB\\nC\\n'
        """
        for line in lines:
            self.append_line(line)
        return self

    def prepend(self, value: Any) -> "StringBuilder":
        """Insert `value` at the beginning."""
        self._parts.insert(0, str(value))
        return self

    def insert(self, index: int, value: Any) -> "StringBuilder":
        """
        Insert `value` at position `index` in the internal fragment list.

        Note: index refers to fragment position, not character position.
        For character-level insertion, use build() and manipulate the str.
        """
        self._parts.insert(index, str(value))
        return self

    # ──────────────────────────────────────────────────
    # State queries
    # ──────────────────────────────────────────────────

    def length(self) -> int:
        """Return the current total character count."""
        return sum(len(p) for p in self._parts)

    def is_empty(self) -> bool:
        """True if no content has been appended."""
        return self.length() == 0

    def fragment_count(self) -> int:
        """Return the number of internal fragments (useful for debugging)."""
        return len(self._parts)

    # ──────────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────────

    def clear(self) -> "StringBuilder":
        """Remove all content."""
        self._parts.clear()
        return self

    def build(self) -> str:
        """
        Join all fragments and return the final string.

        This is the only point where string concatenation occurs.
        """
        return "".join(self._parts)

    def to_string(self) -> "String":
        """Return the result wrapped in an arkhe.text.String instance."""
        from arkhe.text.string import String
        return String(self.build())

    # ──────────────────────────────────────────────────
    # Dunder helpers
    # ──────────────────────────────────────────────────

    def __str__(self) -> str:
        return self.build()

    def __repr__(self) -> str:
        return f"StringBuilder(length={self.length()}, fragments={self.fragment_count()})"

    def __len__(self) -> int:
        return self.length()

    def __iadd__(self, value: Any) -> "StringBuilder":
        """Support: builder += 'text'"""
        return self.append(value)
