"""
arkhe.text.validator — String validation helpers.

All methods are static — StringValidator is a pure namespace.

Usage:
    from arkhe.text import StringValidator

    StringValidator.is_email("user@example.com")   # True
    StringValidator.is_url("https://arkhe.dev")    # True
    StringValidator.is_uuid(value)                 # True / False
    StringValidator.is_numeric("123.45")           # True
"""

import re
import unicodedata
from typing import Optional


class StringValidator:
    """Static namespace for common string validation checks."""

    # ──────────────────────────────────────────────────
    # Network / identity
    # ──────────────────────────────────────────────────

    @staticmethod
    def is_email(value: str) -> bool:
        """
        True if `value` is a plausibly valid email address.

        Uses an RFC-5321-inspired pattern — catches common mistakes
        without being overly strict.

        >>> StringValidator.is_email("user@example.com")
        True
        >>> StringValidator.is_email("not-an-email")
        False
        """
        pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        return bool(re.fullmatch(pattern, value.strip()))

    @staticmethod
    def is_url(value: str) -> bool:
        """
        True if `value` looks like a valid http/https URL.

        >>> StringValidator.is_url("https://arkhe.dev")
        True
        >>> StringValidator.is_url("ftp://example.com")
        False
        """
        pattern = (
            r"^https?://"                       # scheme
            r"(?:[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+)"  # rest
            r"$"
        )
        return bool(re.fullmatch(pattern, value.strip()))

    @staticmethod
    def is_uuid(value: str) -> bool:
        """
        True if `value` is a valid UUID (any version, lowercase or uppercase).

        >>> StringValidator.is_uuid("550e8400-e29b-41d4-a716-446655440000")
        True
        """
        pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        return bool(re.fullmatch(pattern, value.strip()))

    @staticmethod
    def is_ip_v4(value: str) -> bool:
        """
        True if `value` is a valid IPv4 address.

        >>> StringValidator.is_ip_v4("192.168.0.1")
        True
        >>> StringValidator.is_ip_v4("999.0.0.1")
        False
        """
        pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
        m = re.fullmatch(pattern, value.strip())
        if not m:
            return False
        return all(0 <= int(g) <= 255 for g in m.groups())

    @staticmethod
    def is_ip_v6(value: str) -> bool:
        """True if `value` is a valid IPv6 address (basic check)."""
        pattern = r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
        return bool(re.fullmatch(pattern, value.strip()))

    # ──────────────────────────────────────────────────
    # Numeric
    # ──────────────────────────────────────────────────

    @staticmethod
    def is_numeric(value: str) -> bool:
        """
        True if `value` represents a number (integer or float,
        with optional leading sign and optional decimal point).

        >>> StringValidator.is_numeric("123")
        True
        >>> StringValidator.is_numeric("-45.67")
        True
        >>> StringValidator.is_numeric("12e3")
        True
        >>> StringValidator.is_numeric("abc")
        False
        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_integer(value: str) -> bool:
        """
        True if `value` represents a whole integer (no decimal part).

        >>> StringValidator.is_integer("123")
        True
        >>> StringValidator.is_integer("12.0")
        False
        """
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_positive(value: str) -> bool:
        """True if `value` is numeric and greater than zero."""
        try:
            return float(value) > 0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_in_range(value: str, min_val: float, max_val: float) -> bool:
        """True if `value` is numeric and within [min_val, max_val] inclusive."""
        try:
            n = float(value)
            return min_val <= n <= max_val
        except (ValueError, TypeError):
            return False

    # ──────────────────────────────────────────────────
    # Length
    # ──────────────────────────────────────────────────

    @staticmethod
    def has_min_length(value: str, min_length: int) -> bool:
        """True if `value` has at least `min_length` characters."""
        return len(value) >= min_length

    @staticmethod
    def has_max_length(value: str, max_length: int) -> bool:
        """True if `value` has at most `max_length` characters."""
        return len(value) <= max_length

    @staticmethod
    def has_length(value: str, min_length: int, max_length: int) -> bool:
        """True if len(value) is within [min_length, max_length] inclusive."""
        return min_length <= len(value) <= max_length

    # ──────────────────────────────────────────────────
    # Character composition
    # ──────────────────────────────────────────────────

    @staticmethod
    def is_alpha(value: str) -> bool:
        """True if `value` contains only letters (no digits, spaces, or symbols)."""
        return bool(value) and value.isalpha()

    @staticmethod
    def is_alphanumeric(value: str) -> bool:
        """True if `value` contains only letters and digits."""
        return bool(value) and value.isalnum()

    @staticmethod
    def is_digits_only(value: str) -> bool:
        """True if `value` contains only digit characters."""
        return bool(value) and value.isdigit()

    @staticmethod
    def has_uppercase(value: str) -> bool:
        """True if `value` contains at least one uppercase letter."""
        return any(c.isupper() for c in value)

    @staticmethod
    def has_lowercase(value: str) -> bool:
        """True if `value` contains at least one lowercase letter."""
        return any(c.islower() for c in value)

    @staticmethod
    def has_digit(value: str) -> bool:
        """True if `value` contains at least one digit."""
        return any(c.isdigit() for c in value)

    @staticmethod
    def has_special_char(value: str) -> bool:
        """True if `value` contains at least one non-alphanumeric character."""
        return bool(re.search(r"[^a-zA-Z0-9]", value))

    # ──────────────────────────────────────────────────
    # Password strength
    # ──────────────────────────────────────────────────

    @staticmethod
    def is_strong_password(
        value: str,
        min_length: int = 8,
        require_upper: bool = True,
        require_lower: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
    ) -> bool:
        """
        Check whether `value` meets common password strength requirements.

        >>> StringValidator.is_strong_password("Arkhe@2024")
        True
        >>> StringValidator.is_strong_password("weak")
        False
        """
        if len(value) < min_length:
            return False
        if require_upper and not StringValidator.has_uppercase(value):
            return False
        if require_lower and not StringValidator.has_lowercase(value):
            return False
        if require_digit and not StringValidator.has_digit(value):
            return False
        if require_special and not StringValidator.has_special_char(value):
            return False
        return True

    # ──────────────────────────────────────────────────
    # Document numbers (Brazil)
    # ──────────────────────────────────────────────────

    @staticmethod
    def is_cpf(value: str) -> bool:
        """
        Validate a Brazilian CPF number (with or without formatting).

        Checks both the format and the two verification digits.

        >>> StringValidator.is_cpf("123.456.789-09")
        True
        >>> StringValidator.is_cpf("111.111.111-11")
        False
        """
        digits = re.sub(r"\D", "", value)
        if len(digits) != 11:
            return False
        if len(set(digits)) == 1:
            return False  # all same digit (e.g. 000...0)

        def _check(d, n):
            total = sum(int(d[i]) * (n - i) for i in range(n - 1))
            rem   = (total * 10) % 11
            return rem if rem < 10 else 0

        return (
            _check(digits, 10) == int(digits[9]) and
            _check(digits, 11) == int(digits[10])
        )

    @staticmethod
    def is_cnpj(value: str) -> bool:
        """
        Validate a Brazilian CNPJ number (with or without formatting).

        >>> StringValidator.is_cnpj("11.222.333/0001-81")
        True
        """
        digits = re.sub(r"\D", "", value)
        if len(digits) != 14:
            return False
        if len(set(digits)) == 1:
            return False

        def _check(d, weights):
            total = sum(int(d[i]) * weights[i] for i in range(len(weights)))
            rem   = total % 11
            return 0 if rem < 2 else 11 - rem

        w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        return (
            _check(digits, w1) == int(digits[12]) and
            _check(digits, w2) == int(digits[13])
        )

    # ──────────────────────────────────────────────────
    # General
    # ──────────────────────────────────────────────────

    @staticmethod
    def matches_pattern(value: str, pattern: str, flags: int = 0) -> bool:
        """True if `value` fully matches `pattern`."""
        return bool(re.fullmatch(pattern, value, flags))

    @staticmethod
    def is_blank(value: str) -> bool:
        """True if `value` is empty or contains only whitespace."""
        return not value or not value.strip()

    @staticmethod
    def is_json(value: str) -> bool:
        """True if `value` is valid JSON."""
        import json
        try:
            json.loads(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_slug(value: str) -> bool:
        """True if `value` is a valid URL slug (lowercase alphanumeric + hyphens)."""
        return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value))
