# arkhe.env

Modern, typed and chainable environment variable management for Python.

`arkhe.env` is a powerful wrapper around `python-dotenv` that combines:

* Lazy environment resolution
* YAML-style attribute chaining
* Automatic namespacing
* Built-in type casting
* Descriptor support
* Dependency injection helpers
* Module-level proxy access

Inspired by the ergonomics of modern frameworks like Spring Boot, NestJS and dynamic configuration systems.

---

# Installation

```bash
pip install arkhe python-dotenv
```

---

# Loading `.env`

Before accessing variables, load your environment file:

```python
from arkhe.env import Env

Env.load()
```

Or specify a custom path:

```python
Env.load("config/.env")
```

---

# Quick Example

`.env`

```env
DB_HOST=localhost
DB_PORT=5432
DB_POOL_MAX_SIZE=10
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
```

Python:

```python
from arkhe import env

host = env.db.host
port = env.db.port.int
pool = env.db.pool.max_size.int
debug = env.debug.bool
hosts = env.allowed_hosts.list
```

---

# What Changed

The new `env` package introduces a completely new way to access environment variables.

Instead of:

```python
Env.get("DB_HOST")
Env.int("DB_PORT")
```

You can now use:

```python
env.db.host
env.db.port.int
```

This is powered by a lazy, chainable proxy called `DotEnv`.

---

# DotEnv — Chainable Environment Proxy

The core feature of the system.

Every attribute access appends a namespace segment until the value is materialized.

---

## How It Works

```python
from arkhe import env

env.db.host
```

Automatically resolves to:

```env
DB_HOST
```

---

## Nested Namespaces

```python
env.db.pool.max_size
```

Resolves to:

```env
DB_POOL_MAX_SIZE
```

---

# Lazy Resolution

Variables are only fetched from `os.environ` when needed.

This means:

```python
proxy = env.db.host
```

does not immediately read the environment.

The value is resolved only when used:

```python
str(proxy)
bool(proxy)
int(proxy)
float(proxy)
```

---

# Automatic Uppercase Conversion

All segments are automatically converted to uppercase.

```python
env.app.secret.key
```

becomes:

```env
APP_SECRET_KEY
```

---

# Type Casting Shortcuts

Instead of calling helper methods manually, you can use attribute-based casting.

---

## Integer

```python
env.db.port.int
```

Equivalent to:

```python
int(os.environ["DB_PORT"])
```

---

## Float

```python
env.pi.float
```

---

## Boolean

```python
env.debug.bool
```

Accepted truthy values:

```text
1
true
yes
on
```

Case-insensitive.

---

## List

```python
env.allowed_hosts.list
```

`.env`

```env
ALLOWED_HOSTS=localhost,127.0.0.1
```

Result:

```python
["localhost", "127.0.0.1"]
```

---

# Required Variables

```python
env.secret_key.required
```

Raises:

```python
ConfigError
```

if the variable does not exist.

---

# Default Values

```python
env.db.host.default("localhost")
```

If the variable is missing:

```python
"localhost"
```

is returned.

---

# Calling the Proxy Directly

You can call the proxy object itself:

```python
env.db.host()
```

Equivalent to:

```python
os.environ.get("DB_HOST")
```

With fallback:

```python
env.db.host("localhost")
```

---

# Env.ns() — Explicit Namespaces

Useful when you want a fixed namespace root.

```python
from arkhe.env import Env

db = Env.ns("DB")

host = db.host
port = db.port.int
```

Result:

```env
DB_HOST
DB_PORT
```

---

# Module-Level Proxy

One of the most advanced parts of the system.

The module dynamically replaces:

```python
sys.modules[__name__].__class__
```

with a custom `_EnvModule`.

This allows:

```python
from arkhe import env

env.db.host
```

to work directly at import level.

The behavior is similar to:

* dynamic YAML loaders
* configuration DSLs
* proxy-based framework APIs

---

# Classic API (Still Supported)

The original API remains fully compatible.

---

## Get String

```python
Env.get("DB_HOST")
```

---

## Integer

```python
Env.int("DB_PORT")
```

---

## Float

```python
Env.float("APP_VERSION")
```

---

## Boolean

```python
Env.bool("DEBUG")
```

---

## List

```python
Env.list("ALLOWED_HOSTS")
```

---

## Required Variable

```python
Env.required("SECRET_KEY")
```

---

# Runtime Environment Mutation

---

## Set Variable

```python
Env.set("DEBUG", "true")
```

---

## Get All Variables

```python
Env.all()
```

---

# Sensitive Variable Masking

Mark variables as sensitive:

```python
Env.mask("SECRET_KEY")
```

Now:

```python
repr(env.secret_key)
```

shows:

```python
***
```

instead of the actual value.

---

# EnvProperty — Descriptor API

Map environment variables directly into class attributes.

---

## Example

```python
from arkhe.env import Env

class Config:
    host = Env.property(
        "DB_HOST",
        default="localhost"
    )

    port = Env.property(
        "DB_PORT",
        cast_type=int,
        default=5432
    )
```

Usage:

```python
cfg = Config()

print(cfg.host)
print(cfg.port)
```

---

# Environment Injection Decorator

Automatically inject environment variables into function parameters.

---

## Example

```python
from arkhe.env import Env

@Env.inject(
    api_key="API_KEY",
    host="DB_HOST"
)
def connect(api_key=None, host=None):
    print(api_key, host)
```

If arguments are not manually provided, values are loaded from the environment.

---

# Internal Architecture

The package consists of four main components:

| Component     | Purpose                        |
| ------------- | ------------------------------ |
| `DotEnv`      | Lazy chainable proxy           |
| `Env`         | Classic API and helpers        |
| `EnvProperty` | Descriptor-based configuration |
| `_EnvModule`  | Module-level dynamic proxy     |

---

# Example Resolution Flow

```python
env.db.pool.max_size.int
```

Flow:

```text
env
 └── db
      └── pool
           └── max_size
                └── int
```

Generated key:

```text
DB_POOL_MAX_SIZE
```

Final operation:

```python
int(os.environ["DB_POOL_MAX_SIZE"])
```

---

# Error Handling

Invalid casts raise `ConfigError`.

Example:

```env
DB_PORT=abc
```

```python
env.db.port.int
```

Raises:

```python
ConfigError:
Environment variable 'DB_PORT' must be an integer
```

---

# Performance Notes

The system is lightweight and efficient:

* Attribute chaining is lazy
* Lookups are O(1)
* No reflection-heavy processing
* Minimal allocations
* `__slots__` used internally

---

# Recommended Usage

---

## Good

```python
env.db.host
env.db.port.int
env.jwt.secret.required
```

---

## Avoid

```python
Env.get("DB_HOST")
Env.get("DB_PORT")
```

unless compatibility is needed.

---

# Full Example

`.env`

```env
DB_HOST=localhost
DB_PORT=5432
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20
DEBUG=true
SECRET_KEY=my-secret
ALLOWED_HOSTS=localhost,127.0.0.1
```

Python:

```python
from arkhe import env
from arkhe.env import Env

Env.load()

print(env.db.host)
print(env.db.port.int)

print(env.db.pool.min_size.int)
print(env.db.pool.max_size.int)

print(env.debug.bool)

print(env.allowed_hosts.list)

print(env.secret_key.required)

print(env.db.password.default("root"))
```

---

# Exported Symbols

```python
__all__ = [
    "Env",
    "EnvProperty",
    "DotEnv"
]
```

---

# Summary

`arkhe.env` provides:

* Elegant attribute-based access
* Lazy environment resolution
* Built-in type casting
* Dynamic namespacing
* Descriptor integration
* Runtime injection
* Full backward compatibility
* Module-level proxy magic

Designed for modern Python applications that want cleaner configuration management without sacrificing performance or flexibility.
