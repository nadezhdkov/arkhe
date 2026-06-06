"""
arkhe.text.matcher - Pattern matching and extraction utilities.

All methods are static - StringMatcher is a namespace, not an
instance-based class. No state is maintained between calls.

Usage:
    from arkhe.text import StringMatcher

    StringMatcher.matches("hello123", r"[a-z]+[0-9]+")    # True
    StringMatcher.extract("ID: 1234 and 5678", r"[0-9]+") # ["1234", "5678"]
"""

import re
from typing import Dict, List, Optional, Tuple


class StringMatcher:
    """Static namespace for pattern matching and extraction."""

    # ──────────────────────────────────────────────────
    # Matching
    # ──────────────────────────────────────────────────

    @staticmethod
    def matches(text: str, pattern: str, flags: int = 0) -> bool:
        """True if the entire string matches pattern (re.fullmatch)."""
        return bool(re.fullmatch(pattern, text, flags))

    @staticmethod
    def contains_match(text: str, pattern: str, flags: int = 0) -> bool:
        """True if pattern appears anywhere in text (re.search)."""
        return bool(re.search(pattern, text, flags))

    @staticmethod
    def starts_with_pattern(text: str, pattern: str, flags: int = 0) -> bool:
        """True if text starts with a match for pattern (re.match)."""
        return bool(re.match(pattern, text, flags))

    # ──────────────────────────────────────────────────
    # Extraction
    # ──────────────────────────────────────────────────

    @staticmethod
    def extract(text: str, pattern: str, flags: int = 0) -> List[str]:
        """Return all non-overlapping matches of pattern in text."""
        return re.findall(pattern, text, flags)

    @staticmethod
    def extract_first(text: str, pattern: str, flags: int = 0) -> Optional[str]:
        """Return the first match of pattern, or None."""
        m = re.search(pattern, text, flags)
        return m.group(0) if m else None

    @staticmethod
    def extract_last(text: str, pattern: str, flags: int = 0) -> Optional[str]:
        """Return the last match of pattern, or None."""
        matches = re.findall(pattern, text, flags)
        return matches[-1] if matches else None

    @staticmethod
    def extract_groups(
        text: str, pattern: str, flags: int = 0
    ) -> Optional[Tuple[str, ...]]:
        """Return capture groups of the first match, or None."""
        m = re.search(pattern, text, flags)
        return m.groups() if m else None

    @staticmethod
    def extract_named_groups(
        text: str, pattern: str, flags: int = 0
    ) -> Optional[Dict[str, str]]:
        """Return named capture groups of the first match as a dict, or None."""
        m = re.search(pattern, text, flags)
        return m.groupdict() if m else None

    @staticmethod
    def extract_all_groups(
        text: str, pattern: str, flags: int = 0
    ) -> List[Tuple[str, ...]]:
        """Return all match groups for every occurrence of pattern."""
        return re.findall(pattern, text, flags)

    # ──────────────────────────────────────────────────
    # Replace / transform
    # ──────────────────────────────────────────────────

    @staticmethod
    def replace(text: str, pattern: str, replacement: str, flags: int = 0) -> str:
        """Replace all occurrences of pattern with replacement."""
        return re.sub(pattern, replacement, text, flags=flags)

    @staticmethod
    def replace_first(
        text: str, pattern: str, replacement: str, flags: int = 0
    ) -> str:
        """Replace only the first occurrence of pattern."""
        return re.sub(pattern, replacement, text, count=1, flags=flags)

    @staticmethod
    def split(text: str, pattern: str, flags: int = 0) -> List[str]:
        """Split text by pattern."""
        return re.split(pattern, text, flags=flags)

    # ──────────────────────────────────────────────────
    # Position / span
    # ──────────────────────────────────────────────────

    @staticmethod
    def find_span(
        text: str, pattern: str, flags: int = 0
    ) -> Optional[Tuple[int, int]]:
        """Return the (start, end) span of the first match, or None."""
        m = re.search(pattern, text, flags)
        return m.span() if m else None

    @staticmethod
    def find_all_spans(
        text: str, pattern: str, flags: int = 0
    ) -> List[Tuple[int, int]]:
        """Return all (start, end) spans for every match."""
        return [m.span() for m in re.finditer(pattern, text, flags)]

    @staticmethod
    def count_matches(text: str, pattern: str, flags: int = 0) -> int:
        """Return the total number of matches."""
        return len(re.findall(pattern, text, flags))
