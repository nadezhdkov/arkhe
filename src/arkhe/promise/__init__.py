"""
arkhe.promise — JavaScript-style Promises for Python.

Usage:
    from arkhe.promise import Promise

    p = Promise(lambda resolve, reject: resolve(42))
    p.then(print)
"""

from arkhe.promise.promise import (
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
