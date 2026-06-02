"""
nestifypy.promise — JavaScript-style Promises for Python.

Usage:
    from nestifypy.promise import Promise

    p = Promise(lambda resolve, reject: resolve(42))
    p.then(print)
"""

from nestifypy.promise.promise import (
    Promise,
    PromiseError,
    PromiseTimeoutError,
    PromiseCancelledError,
    PromiseAllError,
    PromiseAnyError,
)

__all__ = [
    "Promise",
    "PromiseError",
    "PromiseTimeoutError",
    "PromiseCancelledError",
    "PromiseAllError",
    "PromiseAnyError",
]
