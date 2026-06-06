"""
arkhe.text.string — Immutable fluent String wrapper.

Wraps a Python str and exposes a chainable, self-documenting API
inspired by Java's String and Kotlin's string extensions.

Every method that transforms the value returns a new String instance,
preserving immutability. Methods that inspect or extract return plain
Python values (bool, int, list, str).

Usage:
    from arkhe.text import String

    result = (
        String("   hello_world   ")
            .trim()
            .to_pascal_case()
            .get()
    )
    # → "HelloWorld"
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Optional


class String:
    """Immutable fluent string wrapper."""

    __slots__ = ("_value",)

    def __init__(self, value: str = "") -> None:
        if not isinstance(value, str):
            value = str(value)
        self._value = value

    # ──────────────────────────────────────────────────
    # Value extraction
    # ──────────────────────────────────────────────────

    def get(self) -> str:
        """Return the raw Python string."""
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"String({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, String):
            return self._value == other._value
        if isinstance(other, str):
            return self._value == other
        return NotImplemented

    def __len__(self) -> int:
        return len(self._value)

    def __contains__(self, item: str) -> bool:
        return item in self._value

    def __add__(self, other) -> "String":
        return String(self._value + str(other))

    # ──────────────────────────────────────────────────
    # Basic transformations
    # ──────────────────────────────────────────────────

    def trim(self) -> "String":
        """Remove leading and trailing whitespace."""
        return String(self._value.strip())

    def trim_start(self) -> "String":
        """Remove leading whitespace."""
        return String(self._value.lstrip())

    def trim_end(self) -> "String":
        """Remove trailing whitespace."""
        return String(self._value.rstrip())

    def upper(self) -> "String":
        """Convert to uppercase."""
        return String(self._value.upper())

    def lower(self) -> "String":
        """Convert to lowercase."""
        return String(self._value.lower())

    def capitalize(self) -> "String":
        """Capitalize first character, lowercase the rest."""
        return String(self._value.capitalize())

    def title(self) -> "String":
        """Title-case every word."""
        return String(self._value.title())

    def reverse(self) -> "String":
        """Reverse the string."""
        return String(self._value[::-1])

    def repeat(self, times: int) -> "String":
        """
        Repeat the string N times.

        >>> String("=").repeat(10).get()
        '=========='
        """
        return String(self._value * times)

    def pad_left(self, width: int, char: str = " ") -> "String":
        """Right-justify within a field of `width`, padding with `char`."""
        return String(self._value.rjust(width, char))

    def pad_right(self, width: int, char: str = " ") -> "String":
        """Left-justify within a field of `width`, padding with `char`."""
        return String(self._value.ljust(width, char))

    def center(self, width: int, char: str = " ") -> "String":
        """Center within a field of `width`, padding with `char`."""
        return String(self._value.center(width, char))

    # ──────────────────────────────────────────────────
    # Inspection / predicates  (return plain Python values)
    # ──────────────────────────────────────────────────

    def is_blank(self) -> bool:
        """True if empty or contains only whitespace."""
        return self._value.strip() == ""

    def is_empty(self) -> bool:
        """True if the string has zero length."""
        return self._value == ""

    def length(self) -> int:
        """Return the number of characters."""
        return len(self._value)

    def contains(self, substring: str) -> bool:
        """True if `substring` is present anywhere in the string."""
        return substring in self._value

    def starts_with(self, prefix: str) -> bool:
        """True if the string begins with `prefix`."""
        return self._value.startswith(prefix)

    def ends_with(self, suffix: str) -> bool:
        """True if the string ends with `suffix`."""
        return self._value.endswith(suffix)

    def equals_ignore_case(self, other: str) -> bool:
        """Case-insensitive equality check."""
        return self._value.lower() == other.lower()

    def index_of(self, substring: str, start: int = 0) -> int:
        """Return the first index of `substring`, or -1 if not found."""
        return self._value.find(substring, start)

    def count_occurrences(self, substring: str) -> int:
        """Count non-overlapping occurrences of `substring`."""
        return self._value.count(substring)

    # ──────────────────────────────────────────────────
    # Substring operations
    # ──────────────────────────────────────────────────

    def substring(self, start: int, end: Optional[int] = None) -> "String":
        """
        Extract a slice from `start` to `end` (exclusive).

        >>> String("Hello World").substring(0, 5).get()
        'Hello'
        """
        return String(self._value[start:end])

    def substring_before(self, delimiter: str) -> "String":
        """
        Return the portion before the first occurrence of `delimiter`.

        >>> String("user@email.com").substring_before("@").get()
        'user'
        """
        idx = self._value.find(delimiter)
        if idx == -1:
            return String(self._value)
        return String(self._value[:idx])

    def substring_after(self, delimiter: str) -> "String":
        """
        Return the portion after the first occurrence of `delimiter`.

        >>> String("user@email.com").substring_after("@").get()
        'email.com'
        """
        idx = self._value.find(delimiter)
        if idx == -1:
            return String("")
        return String(self._value[idx + len(delimiter):])

    def substring_before_last(self, delimiter: str) -> "String":
        """Return the portion before the last occurrence of `delimiter`."""
        idx = self._value.rfind(delimiter)
        if idx == -1:
            return String(self._value)
        return String(self._value[:idx])

    def substring_after_last(self, delimiter: str) -> "String":
        """Return the portion after the last occurrence of `delimiter`."""
        idx = self._value.rfind(delimiter)
        if idx == -1:
            return String("")
        return String(self._value[idx + len(delimiter):])

    def substring_between(self, open_: str, close: str) -> "String":
        """
        Return the portion between the first `open_` and the following `close`.

        >>> String("[value]").substring_between("[", "]").get()
        'value'
        """
        start = self._value.find(open_)
        if start == -1:
            return String("")
        start += len(open_)
        end = self._value.find(close, start)
        if end == -1:
            return String("")
        return String(self._value[start:end])

    # ──────────────────────────────────────────────────
    # Replacement operations
    # ──────────────────────────────────────────────────

    def replace(self, old: str, new: str, count: int = -1) -> "String":
        """
        Replace occurrences of `old` with `new`.
        Pass `count` to limit replacements.
        """
        if count == -1:
            return String(self._value.replace(old, new))
        return String(self._value.replace(old, new, count))

    def replace_regex(self, pattern: str, replacement: str) -> "String":
        """Replace using a regular expression pattern."""
        return String(re.sub(pattern, replacement, self._value))

    def remove(self, substring: str) -> "String":
        """Remove all occurrences of `substring`."""
        return String(self._value.replace(substring, ""))

    def remove_regex(self, pattern: str) -> "String":
        """Remove all substrings matching `pattern`."""
        return String(re.sub(pattern, "", self._value))

    def remove_prefix(self, prefix: str) -> "String":
        """
        Remove `prefix` from the start if present.

        >>> String("Mr. Samuel").remove_prefix("Mr. ").get()
        'Samuel'
        """
        if self._value.startswith(prefix):
            return String(self._value[len(prefix):])
        return String(self._value)

    def remove_suffix(self, suffix: str) -> "String":
        """
        Remove `suffix` from the end if present.

        >>> String("report.pdf").remove_suffix(".pdf").get()
        'report'
        """
        if self._value.endswith(suffix):
            return String(self._value[: -len(suffix)])
        return String(self._value)

    def remove_whitespace(self) -> "String":
        """Remove all whitespace characters."""
        return String(re.sub(r"\s+", "", self._value))

    def collapse_spaces(self) -> "String":
        """Replace consecutive whitespace with a single space and trim."""
        return String(re.sub(r"\s+", " ", self._value).strip())

    # ──────────────────────────────────────────────────
    # Naming convention converters
    # ──────────────────────────────────────────────────

    def _words(self) -> List[str]:
        """Split into words regardless of casing or delimiter style."""
        s = re.sub(r"[-_\s]+", " ", self._value)
        s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
        return [w for w in s.split() if w]

    def to_camel_case(self) -> "String":
        """
        Convert to camelCase.

        >>> String("hello_world").to_camel_case().get()
        'helloWorld'
        """
        words = self._words()
        if not words:
            return String("")
        return String(words[0].lower() + "".join(w.capitalize() for w in words[1:]))

    def to_pascal_case(self) -> "String":
        """
        Convert to PascalCase.

        >>> String("hello_world").to_pascal_case().get()
        'HelloWorld'
        """
        return String("".join(w.capitalize() for w in self._words()))

    def to_snake_case(self) -> "String":
        """
        Convert to snake_case.

        >>> String("HelloWorld").to_snake_case().get()
        'hello_world'
        """
        return String("_".join(w.lower() for w in self._words()))

    def to_kebab_case(self) -> "String":
        """
        Convert to kebab-case.

        >>> String("HelloWorld").to_kebab_case().get()
        'hello-world'
        """
        return String("-".join(w.lower() for w in self._words()))

    def to_constant_case(self) -> "String":
        """
        Convert to CONSTANT_CASE.

        >>> String("HelloWorld").to_constant_case().get()
        'HELLO_WORLD'
        """
        return String("_".join(w.upper() for w in self._words()))

    # ──────────────────────────────────────────────────
    # Normalization
    # ──────────────────────────────────────────────────

    def normalize(self) -> "String":
        """
        Remove accents and diacritics via Unicode NFKD decomposition.

        >>> String("João").normalize().get()
        'Joao'
        """
        nfkd = unicodedata.normalize("NFKD", self._value)
        return String("".join(c for c in nfkd if not unicodedata.combining(c)))

    def normalize_unicode(self, form: str = "NFC") -> "String":
        """Apply a specific Unicode normalization form (NFC, NFD, NFKC, NFKD)."""
        return String(unicodedata.normalize(form, self._value))

    # ──────────────────────────────────────────────────
    # Multiline operations
    # ──────────────────────────────────────────────────

    def lines(self) -> List[str]:
        """
        Split into lines, stripping leading/trailing blank lines.

        >>> String("\\nA\\nB\\nC\\n").lines()
        ['A', 'B', 'C']
        """
        return [ln for ln in self._value.splitlines() if ln.strip()]

    def indent(self, spaces: int, char: str = " ") -> "String":
        """
        Prepend each line with `spaces` copies of `char`.

        >>> String("Hello").indent(4).get()
        '    Hello'
        """
        prefix = char * spaces
        indented = "\n".join(prefix + line for line in self._value.splitlines())
        return String(indented)

    def dedent(self) -> "String":
        """Remove common leading whitespace from all lines."""
        import textwrap
        return String(textwrap.dedent(self._value))

    # ──────────────────────────────────────────────────
    # Split / join
    # ──────────────────────────────────────────────────

    def split(self, delimiter: str, max_split: int = -1) -> List[str]:
        """Split by `delimiter`, returning a plain list."""
        if max_split == -1:
            return self._value.split(delimiter)
        return self._value.split(delimiter, max_split)

    def split_regex(self, pattern: str) -> List["String"]:
        """Split using a regex pattern, returning a list of String instances."""
        return [String(s) for s in re.split(pattern, self._value)]

    # ──────────────────────────────────────────────────
    # Masking
    # ──────────────────────────────────────────────────

    def mask(self, pattern: str) -> "String":
        """
        Apply a mask where '#' represents a digit position.

        >>> String("12345678901").mask("###.###.###-##").get()
        '123.456.789-01'
        """
        digits = re.sub(r"\D", "", self._value)
        result = []
        d_idx = 0
        for ch in pattern:
            if ch == "#":
                result.append(digits[d_idx] if d_idx < len(digits) else "_")
                d_idx += 1
            else:
                result.append(ch)
        return String("".join(result))

    # ──────────────────────────────────────────────────
    # Truncation / ellipsis
    # ──────────────────────────────────────────────────

    def truncate(self, max_length: int, ellipsis: str = "...") -> "String":
        """
        Truncate to `max_length` characters, appending `ellipsis` if cut.

        >>> String("Hello World").truncate(7).get()
        'Hell...'
        """
        if len(self._value) <= max_length:
            return String(self._value)
        cut = max_length - len(ellipsis)
        return String(self._value[:cut] + ellipsis)

    # ──────────────────────────────────────────────────
    # Format helpers
    # ──────────────────────────────────────────────────

    def format(self, *args, **kwargs) -> "String":
        """Apply Python str.format() to the value."""
        return String(self._value.format(*args, **kwargs))

    def template(self, context, *args) -> "String":
        """
        Render this string as an ATEL template against `context`.

        >>> String("{name:title} has {coins:number} coins.").template(player).get()
        'Samuel has 15,000 coins.'
        """
        from arkhe.io.template.engine import render
        return String(render(self._value, context, *args))
