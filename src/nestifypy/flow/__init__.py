"""
nestifypy.flow
-----------
Control flow and task system: timers, scheduled repeats, async helpers,
retry logic, delayed calls, and parallel execution.
"""

from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


# ─────────────────────────────────────────────
#  Internal task registry
# ─────────────────────────────────────────────

_tasks: List[Dict[str, Any]] = []
_executor = ThreadPoolExecutor(max_workers=8)


# ─────────────────────────────────────────────
#  Flow
# ─────────────────────────────────────────────

class Flow:
    """Decorator-based control flow and task system."""

    # ── async_task ────────────────────────────

    @staticmethod
    def async_task(func: F) -> F:
        """
        Mark a coroutine as an async task.
        Preserves async signature.
        """
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)
        return wrapper  # type: ignore

    # ── threaded ──────────────────────────────

    @staticmethod
    def threaded(func: F) -> F:
        """Run a function in a background daemon thread."""
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> threading.Thread:
            t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
            t.start()
            return t
        return wrapper  # type: ignore

    # ── delay ─────────────────────────────────

    @staticmethod
    def delay(seconds: float) -> Callable[[F], F]:
        """Wait before calling the function."""
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                time.sleep(seconds)
                return func(*args, **kwargs)
            return wrapper  # type: ignore
        return decorator

    # ── retry ─────────────────────────────────

    @staticmethod
    def retry(
        times: int = 3,
        wait: float = 0.0,
        exceptions: tuple = (Exception,),
    ) -> Callable[[F], F]:
        """Retry a function up to `times` on failure."""
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                last: Optional[Exception] = None
                for attempt in range(1, times + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last = e
                        print(
                            f"  [Flow.retry] {func.__name__} "
                            f"attempt {attempt}/{times}: {e}"
                        )
                        if wait > 0:
                            time.sleep(wait)
                raise last  # type: ignore
            return wrapper  # type: ignore
        return decorator

    # ── timeout ───────────────────────────────

    @staticmethod
    def timeout(seconds: float) -> Callable[[F], F]:
        """
        Raise TimeoutError if function doesn't complete in time.
        Uses threading for compatibility with non-async functions.
        """
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                result: List[Any] = []
                error: List[Exception] = []

                def target() -> None:
                    try:
                        result.append(func(*args, **kwargs))
                    except Exception as e:
                        error.append(e)

                t = threading.Thread(target=target, daemon=True)
                t.start()
                t.join(seconds)

                if t.is_alive():
                    raise TimeoutError(
                        f"{func.__name__} timed out after {seconds}s"
                    )
                if error:
                    raise error[0]
                return result[0] if result else None

            return wrapper  # type: ignore
        return decorator

    # ── repeat ────────────────────────────────

    @staticmethod
    def repeat(
        times: int,
        interval: float = 0.0,
    ) -> Callable[[F], F]:
        """Call the function `times` times, with optional interval."""
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> List[Any]:
                results = []
                for _ in range(times):
                    results.append(func(*args, **kwargs))
                    if interval > 0:
                        time.sleep(interval)
                return results
            return wrapper  # type: ignore
        return decorator

    # ── interval (background repeat loop) ────

    @staticmethod
    def interval(seconds: float) -> Callable[[F], F]:
        """
        Run a function repeatedly every `seconds` in a background thread.
        Returns the thread for control.
        """
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> threading.Thread:
                def loop() -> None:
                    while True:
                        func(*args, **kwargs)
                        time.sleep(seconds)
                t = threading.Thread(target=loop, daemon=True)
                t.start()
                return t
            return wrapper  # type: ignore
        return decorator

    # ── parallel ──────────────────────────────

    @staticmethod
    def parallel(*funcs: Callable, timeout: Optional[float] = None) -> List[Any]:
        """
        Run multiple callables in parallel and return their results.

        Example:
            results = Flow.parallel(task_a, task_b, task_c)
        """
        futures = [_executor.submit(f) for f in funcs]
        return [f.result(timeout=timeout) for f in futures]

    # ── once ──────────────────────────────────

    @staticmethod
    def once(func: F) -> F:
        """Ensure a function is only called once; subsequent calls are no-ops."""
        called = {"value": False}

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not called["value"]:
                called["value"] = True
                return func(*args, **kwargs)
            return None

        return wrapper  # type: ignore

    # ── debounce ──────────────────────────────

    @staticmethod
    def debounce(wait: float) -> Callable[[F], F]:
        """
        Delay function execution; reset timer if called again within `wait` seconds.
        Useful for events like resize or search.
        """
        def decorator(func: F) -> F:
            timer: Dict[str, Any] = {"handle": None}

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> None:
                if timer["handle"] is not None:
                    timer["handle"].cancel()

                def call() -> None:
                    func(*args, **kwargs)

                handle = threading.Timer(wait, call)
                handle.daemon = True
                handle.start()
                timer["handle"] = handle

            return wrapper  # type: ignore
        return decorator

    # ── throttle ──────────────────────────────

    @staticmethod
    def throttle(wait: float) -> Callable[[F], F]:
        """Allow function to be called at most once per `wait` seconds."""
        def decorator(func: F) -> F:
            last: Dict[str, float] = {"time": 0.0}

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Optional[Any]:
                now = time.monotonic()
                if now - last["time"] >= wait:
                    last["time"] = now
                    return func(*args, **kwargs)
                return None

            return wrapper  # type: ignore
        return decorator

    # ── after ─────────────────────────────────

    @staticmethod
    def after(calls: int) -> Callable[[F], F]:
        """Only call the function after it has been invoked `calls` times."""
        def decorator(func: F) -> F:
            counter = {"n": 0}

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Optional[Any]:
                counter["n"] += 1
                if counter["n"] >= calls:
                    return func(*args, **kwargs)
                return None

            return wrapper  # type: ignore
        return decorator

    # ── schedule ──────────────────────────────

    @staticmethod
    def schedule(
        func: Callable,
        delay: float = 0.0,
        *args: Any,
        **kwargs: Any,
    ) -> threading.Timer:
        """Schedule a function call after a delay (non-blocking)."""
        t = threading.Timer(delay, func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
        return t

    # ── loop ──────────────────────────────────

    @staticmethod
    def loop(
        func: Callable,
        fps: int = 60,
        until: Optional[Callable[[], bool]] = None,
    ) -> None:
        """
        Run `func` in a loop at a given FPS rate (blocking).
        Stops when `until()` returns True, or on KeyboardInterrupt.
        """
        interval = 1.0 / fps
        try:
            while True:
                start = time.perf_counter()
                func()
                if until and until():
                    break
                elapsed = time.perf_counter() - start
                sleep_for = interval - elapsed
                if sleep_for > 0:
                    time.sleep(sleep_for)
        except KeyboardInterrupt:
            pass

    # ── run_async ─────────────────────────────

    @staticmethod
    def run_async(coro: Any) -> Any:
        """Run a coroutine synchronously."""
        return asyncio.run(coro)


__all__ = ["Flow"]
