"""
arkhe.io — Beautiful terminal experiences for Python.

Intercepts print(), input(), exceptions and tracebacks to render
visually rich, self-diagnosing terminal output without changing
any existing code.

Usage:
    from arkhe.io import install
    install()
"""

from .core import install, uninstall
from .helpers import success, warning, error, info
from .inspect import inspect as inspect_obj
from .watch import watch
from .theme import theme

__all__ = [
    "install",
    "uninstall",
    "success",
    "warning",
    "error",
    "info",
    "inspect_obj",
    "watch",
    "theme",
]
