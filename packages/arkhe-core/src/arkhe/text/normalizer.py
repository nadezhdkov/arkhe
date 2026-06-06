"""
arkhe.text.normalizer — Text cleanup and normalization utilities.

All methods are static — StringNormalizer is a pure namespace.

Usage:
    from arkhe.text import StringNormalizer

    StringNormalizer.normalize("João")          # "Joao"
    StringNormalizer.collapse_spaces("a  b  c") # "a b c"
    StringNormalizer.slugify("Hello World!")    # "hello-world"
"""

import re
import unicodedata
from typing import Optional


class StringNormalizer:
    """Static namespace for string normalization and cleanup."""

    # ──────────────────────────────────────────────────
    # Unicode normalization
    # ──────────────────────────────────────────────────

    @staticmethod
    def normalize(text: str) -> str:
        """
        Remove accents and diacritics via NFKD decomposition.

        >>> StringNormalizer.normalize("João")
        'Joao'
        >>> StringNormalizer.normalize("Ñoño")
        'Nono'
        """
        nfkd = unicodedata.normalize("NFKD", text)
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    @staticmethod
    def normalize_unicode(text: str, form: str = "NFC") -> str:
        """
        Apply a Unicode normalization form: NFC, NFD, NFKC, or NFKD.

        NFC  — Canonical Decomposition, Canonical Composition (default web form)
        NFD  — Canonical Decomposition
        NFKC — Compatibility Decomposition, Canonical Composition
        NFKD — Compatibility Decomposition
        """
        return unicodedata.normalize(form, text)

    @staticmethod
    def to_ascii(text: str) -> str:
        """
        Convert to ASCII, replacing non-ASCII characters with their
        closest ASCII equivalents and dropping the rest.

        >>> StringNormalizer.to_ascii("Héllo Wörld")
        'Hello World'
        """
        normalized = unicodedata.normalize("NFKD", text)
        return normalized.encode("ascii", "ignore").decode("ascii")

    # ──────────────────────────────────────────────────
    # Whitespace normalization
    # ──────────────────────────────────────────────────

    @staticmethod
    def remove_whitespace(text: str) -> str:
        """
        Remove all whitespace characters (spaces, tabs, newlines).

        >>> StringNormalizer.remove_whitespace("a b c")
        'abc'
        """
        return re.sub(r"\s+", "", text)

    @staticmethod
    def collapse_spaces(text: str) -> str:
        """
        Replace consecutive whitespace sequences with a single space,
        then strip leading and trailing whitespace.

        >>> StringNormalizer.collapse_spaces("hello     world")
        'hello world'
        """
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def normalize_newlines(text: str, newline: str = "\n") -> str:
        """
        Normalize all line endings (\\r\\n, \\r, \\n) to a uniform style.
        Default output is Unix-style \\n.
        """
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if newline != "\n":
            text = text.replace("\n", newline)
        return text

    @staticmethod
    def strip_lines(text: str) -> str:
        """Strip leading and trailing whitespace from every line."""
        return "\n".join(line.strip() for line in text.splitlines())

    @staticmethod
    def remove_blank_lines(text: str) -> str:
        """Remove lines that are empty or contain only whitespace."""
        lines = [ln for ln in text.splitlines() if ln.strip()]
        return "\n".join(lines)

    # ──────────────────────────────────────────────────
    # Character-level cleanup
    # ──────────────────────────────────────────────────

    @staticmethod
    def digits_only(text: str) -> str:
        """
        Keep only digit characters.

        >>> StringNormalizer.digits_only("+55 (88) 99999-9999")
        '558899999999'
        """
        return re.sub(r"\D", "", text)

    @staticmethod
    def letters_only(text: str) -> str:
        """
        Keep only letter characters (Unicode-aware).

        >>> StringNormalizer.letters_only("abc123def")
        'abcdef'
        """
        return re.sub(r"[^a-zA-Z]", "", text)

    @staticmethod
    def alphanumeric_only(text: str) -> str:
        """Keep only alphanumeric characters."""
        return re.sub(r"[^a-zA-Z0-9]", "", text)

    @staticmethod
    def remove_punctuation(text: str) -> str:
        """Remove all punctuation characters."""
        return re.sub(r"[^\w\s]", "", text)

    @staticmethod
    def remove_special_chars(text: str, keep: str = "") -> str:
        """
        Remove non-alphanumeric, non-space characters.
        Pass `keep` to preserve specific extra characters.

        >>> StringNormalizer.remove_special_chars("hello@world.com", keep="@.")
        'hello@world.com'
        """
        safe = re.escape(keep)
        pattern = rf"[^a-zA-Z0-9\s{safe}]"
        return re.sub(pattern, "", text)

    # ──────────────────────────────────────────────────
    # Slug / URL-safe
    # ──────────────────────────────────────────────────

    @staticmethod
    def slugify(text: str, separator: str = "-") -> str:
        """
        Convert text to a URL-safe slug.

        Steps: normalize accents → lowercase → keep alphanumeric + spaces
        → replace spaces with separator → collapse duplicates.

        >>> StringNormalizer.slugify("Hello World! Olá Mundo")
        'hello-world-ola-mundo'
        """
        text = StringNormalizer.normalize(text)
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", separator, text.strip())
        text = re.sub(re.escape(separator) + r"+", separator, text)
        return text

    @staticmethod
    def truncate_words(text: str, max_words: int, ellipsis: str = "...") -> str:
        """
        Truncate to at most `max_words` words, appending `ellipsis` if cut.

        >>> StringNormalizer.truncate_words("one two three four", 2)
        'one two...'
        """
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + ellipsis

    # ──────────────────────────────────────────────────
    # HTML / Markdown cleanup
    # ──────────────────────────────────────────────────

    @staticmethod
    def strip_html(text: str) -> str:
        """
        Remove HTML/XML tags from text.

        >>> StringNormalizer.strip_html("<b>Hello</b> <i>World</i>")
        'Hello World'
        """
        return re.sub(r"<[^>]+>", "", text)

    @staticmethod
    def escape_html(text: str) -> str:
        """Escape &, <, >, ", ' for safe HTML insertion."""
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )
