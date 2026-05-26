"""
nestifypy.decorators
-----------------
A comprehensive decorator toolkit for Nestifypy.
All decorators preserve metadata via functools.wraps.
"""

from __future__ import annotations

import asyncio
import time
import traceback
import warnings
from functools import wraps
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


# ─────────────────────────────────────────────
#  Internal Event Registry
# ─────────────────────────────────────────────

_EVENTS: Dict[str, List[Callable]] = {}
_REGISTRY: List[Any] = []
_SINGLETONS: Dict[type, Any] = {}


# ─────────────────────────────────────────────
#  Metadata Helper (Adicionado para suporte)
# ─────────────────────────────────────────────

def attach_metadata(func: F, *args: Any, **kwargs: Any) -> F:
    """
    Attach arbitrary metadata to a function.

    Args:
        func (F): The function to decorate.
        *args: Positional string tags to attach as `_tags`.
        **kwargs: Key-value metadata attributes to attach.

    Returns:
        F: The original function with new metadata attributes.
    """
    setattr(func, "_tags", args)
    for key, value in kwargs.items():
        setattr(func, f"_{key}", value)
    return func


# ─────────────────────────────────────────────
#  debug
# ─────────────────────────────────────────────

def debug(func: F) -> F:
    """
    Log function calls, arguments, results, and errors.

    Args:
        func (F): The function to be debugged.

    Returns:
        F: A wrapped function that prints debug information during execution.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"  → calling  : {func.__name__}")
        print(f"  → args     : {args}")
        print(f"  → kwargs   : {kwargs}")
        try:
            result = func(*args, **kwargs)
            print(f"  ← result   : {result}")
            return result
        except Exception as e:
            print(f"  ✗ error    : {e}")
            raise

    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  benchmark
# ─────────────────────────────────────────────

def benchmark(func: F) -> F:
    """
    Measure and print the execution time of a function.

    Args:
        func (F): The function to benchmark.

    Returns:
        F: A wrapped function that prints its execution time.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  ⏱  {func.__name__} → {elapsed:.6f}s")
        return result

    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  safe
# ─────────────────────────────────────────────

def safe(func: F) -> F:
    """
    Catch and print any exception, preventing the application from crashing.

    Args:
        func (F): The function to wrap.

    Returns:
        F: A wrapped function that returns None if an exception occurs.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Optional[Any]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"  [safe] caught exception in {func.__name__}: {e}")
            return None

    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  trace
# ─────────────────────────────────────────────

def trace(func: F) -> F:
    """
    Print the full traceback if an exception is raised in the function.

    Args:
        func (F): The function to trace.

    Returns:
        F: A wrapped function that prints stack traces on failure before raising.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception:
            traceback.print_exc()
            raise

    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  retry
# ─────────────────────────────────────────────

def retry(times: int = 3, delay: float = 0.0) -> Callable[[F], F]:
    """
    Retry a function up to `times` if an exception is raised.

    Args:
        times (int): Maximum number of attempts. Defaults to 3.
        delay (float): Delay in seconds between attempts. Defaults to 0.0.

    Returns:
        Callable[[F], F]: The retry decorator.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Optional[Exception] = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    print(f"  [retry] attempt {attempt}/{times} failed: {e}")
                    if delay > 0:
                        time.sleep(delay)
            raise last_error  # type: ignore

        return wrapper  # type: ignore
    return decorator


# ─────────────────────────────────────────────
#  delay
# ─────────────────────────────────────────────

def delay(seconds: float) -> Callable[[F], F]:
    """
    Wait `seconds` before executing the function.

    Args:
        seconds (float): Time in seconds to sleep before calling the function.

    Returns:
        Callable[[F], F]: The delay decorator.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            time.sleep(seconds)
            return func(*args, **kwargs)

        return wrapper  # type: ignore
    return decorator


# ─────────────────────────────────────────────
#  threaded
# ─────────────────────────────────────────────

def threaded(func: F) -> F:
    """
    Run the function in a background thread.

    Args:
        func (F): The function to execute.

    Returns:
        F: A wrapped function that returns the Thread object instead of the result.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Thread:
        t = Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        t.start()
        return t

    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  async_task
# ─────────────────────────────────────────────

def async_task(func: F) -> F:
    """
    Ensure an asynchronous function is properly defined and awaited.

    Args:
        func (F): The async function to wrap.

    Returns:
        F: An asynchronous wrapper for the target function.
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await func(*args, **kwargs)

    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  cache
# ─────────────────────────────────────────────

def cache(func: F) -> F:
    """
    Simple memoization cache keyed purely on positional arguments.

    Args:
        func (F): The function to cache.

    Returns:
        F: A wrapped function that returns cached results for identical inputs.
    """
    _cache: Dict[tuple, Any] = {}

    @wraps(func)
    def wrapper(*args: Any) -> Any:
        if args not in _cache:
            _cache[args] = func(*args)
        return _cache[args]

    wrapper._cache = _cache  # type: ignore
    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  singleton (class decorator)
# ─────────────────────────────────────────────

def singleton(cls: Type) -> Type:
    """
    Ensure only one instance of a class exists across the application.

    Args:
        cls (Type): The class to turn into a singleton.

    Returns:
        Type: A wrapped class that always returns the same instance.
    """
    @wraps(cls)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if cls not in _SINGLETONS:
            _SINGLETONS[cls] = cls(*args, **kwargs)
        return _SINGLETONS[cls]

    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  register
# ─────────────────────────────────────────────

def register(obj: Any) -> Any:
    """
    Add a function or class to the global registry.

    Args:
        obj (Any): The object (function or class) to register.

    Returns:
        Any: The unchanged object.
    """
    _REGISTRY.append(obj)
    return obj


# ─────────────────────────────────────────────
#  event
# ─────────────────────────────────────────────

def event(name: str) -> Callable[[F], F]:
    """
    Register a function as an event handler for a specific event name.

    Args:
        name (str): The name of the event to listen for.

    Returns:
        Callable[[F], F]: The event registration decorator.
    """
    def decorator(func: F) -> F:
        if name not in _EVENTS:
            _EVENTS[name] = []
        _EVENTS[name].append(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper  # type: ignore
    return decorator


def emit(name: str, *args: Any, **kwargs: Any) -> None:
    """
    Emit an event and synchronously call all registered handlers.

    Args:
        name (str): The name of the event to emit.
        *args: Positional arguments to pass to the handlers.
        **kwargs: Keyword arguments to pass to the handlers.
    """
    for handler in _EVENTS.get(name, []):
        handler(*args, **kwargs)


# ─────────────────────────────────────────────
#  validate
# ─────────────────────────────────────────────

def validate(
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> Callable[[F], F]:
    """
    Validate that the first numeric argument of a function falls within a range.

    Args:
        min_value (Optional[float]): The minimum allowed value (inclusive).
        max_value (Optional[float]): The maximum allowed value (inclusive).

    Returns:
        Callable[[F], F]: The validation decorator.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(value: Any, *args: Any, **kwargs: Any) -> Any:
            if min_value is not None and value < min_value:
                raise ValueError(
                    f"{func.__name__}: value {value} is below minimum {min_value}"
                )
            if max_value is not None and value > max_value:
                raise ValueError(
                    f"{func.__name__}: value {value} exceeds maximum {max_value}"
                )
            return func(value, *args, **kwargs)

        return wrapper  # type: ignore
    return decorator


# ─────────────────────────────────────────────
#  not_null
# ─────────────────────────────────────────────

def not_null(func: F) -> F:
    """
    Raise ValueError if any positional or keyword argument is None.

    Args:
        func (F): The function to validate.

    Returns:
        F: A wrapped function that strictly prohibits None values.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        for i, arg in enumerate(args):
            if arg is None:
                raise ValueError(
                    f"{func.__name__}: argument at position {i} must not be None"
                )
        for k, v in kwargs.items():
            if v is None:
                raise ValueError(
                    f"{func.__name__}: keyword argument '{k}' must not be None"
                )
        return func(*args, **kwargs)

    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  validate_types
# ─────────────────────────────────────────────

def validate_types(func: F) -> F:
    """
    Validate argument types at runtime against type annotations.

    Args:
        func (F): The function whose arguments will be type-checked.

    Returns:
        F: A wrapped function that enforces type hints strictly.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        hints = func.__annotations__
        params = list(hints.keys())
        for i, (val, param) in enumerate(zip(args, params)):
            expected = hints.get(param)
            if expected and not isinstance(val, expected):
                raise TypeError(
                    f"{func.__name__}: arg '{param}' expected {expected.__name__}, "
                    f"got {type(val).__name__}"
                )
        return func(*args, **kwargs)

    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  rate_limit
# ─────────────────────────────────────────────

def rate_limit(calls_per_second: float) -> Callable[[F], F]:
    """
    Limit how often a function can be called per second. Blocks if exceeded.

    Args:
        calls_per_second (float): Maximum allowed calls in one second.

    Returns:
        Callable[[F], F]: The rate limit decorator.
    """
    min_interval = 1.0 / calls_per_second
    last_called: Dict[str, float] = {}

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = time.monotonic()
            last = last_called.get(func.__name__, 0.0)
            elapsed = now - last
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_called[func.__name__] = time.monotonic()
            return func(*args, **kwargs)

        return wrapper  # type: ignore
    return decorator


# ─────────────────────────────────────────────
#  startup / shutdown
# ─────────────────────────────────────────────

_STARTUP_HOOKS: List[Callable] = []
_SHUTDOWN_HOOKS: List[Callable] = []

def startup(func: F) -> F:
    """
    Register a function to run on application startup.

    Args:
        func (F): The function to execute on startup.

    Returns:
        F: The original function.
    """
    _STARTUP_HOOKS.append(func)
    return func


def shutdown(func: F) -> F:
    """
    Register a function to run on application shutdown.

    Args:
        func (F): The function to execute on shutdown.

    Returns:
        F: The original function.
    """
    _SHUTDOWN_HOOKS.append(func)
    return func


def run_startup() -> None:
    """Execute all registered startup hooks."""
    for hook in _STARTUP_HOOKS:
        hook()


def run_shutdown() -> None:
    """Execute all registered shutdown hooks."""
    for hook in _SHUTDOWN_HOOKS:
        hook()


# ─────────────────────────────────────────────
#  observable
# ─────────────────────────────────────────────

def observable(cls: Type) -> Type:
    """
    Add observer pattern methods (`subscribe` and `notify`) to a class.

    Args:
        cls (Type): The class to modify.

    Returns:
        Type: The modified class supporting subscriptions.
    """
    cls._observers: List[Callable] = []  # type: ignore

    def subscribe(self: Any, callback: Callable) -> None:
        self._observers.append(callback)

    def notify(self: Any, *args: Any, **kwargs: Any) -> None:
        for obs in self._observers:
            obs(*args, **kwargs)

    cls.subscribe = subscribe  # type: ignore
    cls.notify = notify  # type: ignore
    return cls


# ─────────────────────────────────────────────
#  once
# ─────────────────────────────────────────────

def once(func: F) -> F:
    """
    Execute a function only once. Subsequent calls return the cached result.

    Args:
        func (F): The function to wrap.

    Returns:
        F: A wrapped function that guarantees single execution.
    """
    has_run = False
    result = None

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        nonlocal has_run, result
        if not has_run:
            result = func(*args, **kwargs)
            has_run = True
        return result

    return wrapper  # type: ignore


# ─────────────────────────────────────────────
#  deprecated
# ─────────────────────────────────────────────

def deprecated(reason: str = "This API is deprecated and will be removed.") -> Callable[[F], F]:
    """
    Emit a deprecation warning when the decorated function is called.

    Args:
        reason (str): The explanation message to show in the warning.

    Returns:
        Callable[[F], F]: A decorator that issues a DeprecationWarning.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"Call to deprecated function {func.__name__}. {reason}",
                category=DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper  # type: ignore
    return decorator


# ─────────────────────────────────────────────
#  experimental
# ─────────────────────────────────────────────

def experimental(func: F) -> F:
    """
    Mark an API as unstable and attach metadata for tooling.

    Args:
        func (F): The experimental function.

    Returns:
        F: The wrapped function with associated metadata attributes.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    # Tooling (like an IDE plugin or documentation generator)
    # can now easily inspect this function at runtime.
    return attach_metadata(wrapper, "experimental", is_stable=False, version="alpha")


__all__ = [
    "debug",
    "benchmark",
    "safe",
    "trace",
    "retry",
    "delay",
    "threaded",
    "async_task",
    "cache",
    "singleton",
    "register",
    "event",
    "emit",
    "validate",
    "not_null",
    "validate_types",
    "rate_limit",
    "startup",
    "shutdown",
    "run_startup",
    "run_shutdown",
    "observable",
    "deprecated",
    "once",
    "experimental",
    "attach_metadata",
    "_EVENTS",
    "_REGISTRY",
]