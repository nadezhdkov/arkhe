# Decorators (`nestify.decorators`)

Nestify includes a comprehensive suite of utility decorators to add caching, validation, error handling, and event structures to your functions cleanly. All decorators preserve function metadata using `functools.wraps`.

## Import
```python
from nestify.decorators import *
```

## Execution & Performance

- `@benchmark`: Prints the execution time of the function in seconds.
- `@cache`: Memoizes function return values based on positional arguments.
- `@once`: Ensures a function executes only on its first call; subsequent calls return the cached result.
- `@rate_limit(calls_per_second)`: Blocks/sleeps to prevent the function from exceeding the specified rate limit.

```python
@benchmark
@cache
def expensive_calculation(x):
    return sum(i * i for i in range(x))
```

## Error Handling & Resiliency

- `@safe`: Catches all exceptions, prints a safe error message, and returns `None` instead of crashing.
- `@trace`: Prints the full traceback stack on failure before re-raising the exception.
- `@retry(times=3, delay=1.0)`: Automatically retries the function on failure.

```python
@retry(times=3, delay=2.0)
def fetch_api_data():
    pass
```

## Threading & Async

- `@threaded`: Runs the function in a background daemon thread, immediately returning the `Thread` object.
- `@async_task`: A marker to strictly enforce async coroutine signatures.
- `@delay(seconds)`: Sleeps before executing the function.

## Type Validation

- `@not_null`: Raises a `ValueError` if any argument (positional or keyword) is `None`.
- `@validate(min_value, max_value)`: Asserts that the first numeric argument is within the specified bounds.
- `@validate_types`: Enforces runtime type-checking based on the function's Python type hints.

```python
@validate_types
def process_user(age: int, name: str):
    pass # Will raise TypeError if age is not an int
```

## Architecture & Events

- `@singleton`: Class decorator that ensures only one instance of a class ever exists.
- `@observable`: Class decorator that injects `.subscribe(callback)` and `.notify(*args)` methods.
- `@startup` / `@shutdown`: Registers functions to run during the application lifecycle (executed via `run_startup()` / `run_shutdown()`).
- `@event(name)`: Subscribes a function to an internal global event bus. Triggered via `emit(name, *args)`.

```python
@event("user_registered")
def send_welcome_email(user_id):
    pass

# Trigger it from elsewhere
emit("user_registered", 101)
```

## Documentation
- `@deprecated(reason)`: Issues a `DeprecationWarning` upon execution.
- `@experimental`: Attaches metadata tagging the API as unstable for tooling.
