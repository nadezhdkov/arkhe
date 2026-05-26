# Control Flow (`nestify.flow`)

The `Flow` class is a namespace grouping decorators and utility methods for advanced task scheduling, repetition, throttling, and concurrency.

## Import
```python
from nestify.flow import Flow
```

## Scheduled Execution

- `@Flow.delay(seconds)`: Pauses before executing the wrapped function.
- `Flow.schedule(func, delay, *args)`: Non-blocking equivalent; schedules the function in a background thread and returns the `Timer` handle.

## Repetition & Loops

- `@Flow.repeat(times, interval)`: Automatically invokes the function `times` times, sleeping `interval` seconds between calls. Returns a list of results.
- `@Flow.interval(seconds)`: Runs the function continuously in a background daemon thread every `seconds`. Returns the `Thread` object.
- `Flow.loop(func, fps, until)`: A blocking loop helper that locks execution to a specific framerate (`fps`). Optional `until` callback breaks the loop when `True`.

```python
@Flow.interval(5.0)
def ping_server():
    print("Ping!") # Runs in background every 5 seconds
```

## Resilience

- `@Flow.retry(times, wait, exceptions)`: Retries the function upon encountering specific exceptions, with optional sleep between attempts.
- `@Flow.timeout(seconds)`: Runs the function in a thread and raises `TimeoutError` if it doesn't return within the limit.

## Rate Limiting

- `@Flow.debounce(wait)`: Delays execution until `wait` seconds have elapsed since the *last* invocation. Useful for resize events or search inputs.
- `@Flow.throttle(wait)`: Ensures the function is executed at most once every `wait` seconds. Excess calls are ignored and return `None`.
- `@Flow.once`: Ensures the function only runs once over the lifecycle of the app.
- `@Flow.after(calls)`: The function will only execute after it has been invoked at least `calls` times.

```python
@Flow.throttle(1.0)
def on_mouse_move(x, y):
    # Only processes 1 mouse move event per second max
    pass
```

## Concurrency

- `Flow.parallel(*funcs, timeout)`: Uses a ThreadPoolExecutor to run multiple parameter-less callables concurrently. Returns a list of results.
- `@Flow.threaded`: Decorator equivalent to Python's built-in threading.
- `Flow.run_async(coro)`: Synchronous wrapper around `asyncio.run()`.
