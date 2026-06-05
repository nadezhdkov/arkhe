"""
arkhe.komodo.access_level
---------------------------
Enum representing access modifiers for generated AST methods and classes.
"""

from enum import Enum


class AccessLevel(Enum):
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"
    NONE = "none"
