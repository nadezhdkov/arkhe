"""
arkhe.ensure.exceptions
----------------------------
Exceções personalizadas do módulo Ensure.

Herdam de ValueError / TypeError nativos, então blocos
``except ValueError`` continuam funcionando normalmente.
Ao mesmo tempo, ``except EnsureError`` captura qualquer falha de validação.
"""

from __future__ import annotations


class EnsureError(Exception):
    """Base de todas as exceções do módulo Ensure."""


class EnsureValueError(ValueError, EnsureError):
    """Violação de validação de valor (None, blank, fora de range, etc.)."""


class EnsureTypeError(TypeError, EnsureError):
    """Violação de validação de tipo."""


__all__ = ["EnsureError", "EnsureValueError", "EnsureTypeError"]
