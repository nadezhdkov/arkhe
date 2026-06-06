"""
arkhe.text — High-performance string construction, transformation,
analysis and validation utilities for Python.

Classes:
    String           — Immutable fluent string wrapper
    StringBuilder    — Mutable string construction (fragment-based)
    StringMatcher    — Pattern matching and extraction
    StringNormalizer — Text cleanup and normalization
    StringValidator  — Validation helpers

Usage:
    from arkhe.text import String, StringBuilder, StringMatcher
    from arkhe.text import StringNormalizer, StringValidator

    result = (
        String("   hello_world   ")
            .trim()
            .to_pascal_case()
            .get()
    )
    # → "HelloWorld"

    log = (
        StringBuilder()
            .append("[INFO] ")
            .append_template("{name} joined.", player)
            .build()
    )
"""

from .string    import String
from .builder   import StringBuilder
from .matcher   import StringMatcher
from .normalizer import StringNormalizer
from .validator  import StringValidator

__all__ = [
    "String",
    "StringBuilder",
    "StringMatcher",
    "StringNormalizer",
    "StringValidator",
]
