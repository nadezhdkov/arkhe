# Environment Variables (`nestify.env`)

`nestify.env` provides a clean, typed wrapper around `python-dotenv`. It lets you load `.env` files easily, cast variables safely, and use descriptors for a declarative configuration architecture.

## 1. Quick Start

Loading the environment and grabbing variables:

```python
from nestify.env import Env

# Loads .env from the current directory
Env.load()

# Get a string (returns None if missing)
api_key = Env.get("API_KEY")

# Get an integer with a default value of 8080
port = Env.int("PORT", default=8080)

# Get a boolean. Understands 'true', '1', 'yes', 'on'
debug = Env.bool("DEBUG_MODE", default=False)
```

## 2. Declarative Config (`EnvProperty`)

Instead of fetching variables inline, you can define your application configuration declaratively using the `EnvProperty` descriptor. This maps an environment variable directly to a class attribute.

```python
from nestify.env import Env

class DatabaseConfig:
    host = Env.property("DB_HOST", default="localhost")
    port = Env.property("DB_PORT", cast=int, default=5432)
    use_ssl = Env.property("DB_SSL", cast=bool, default=True)

# Usage
cfg = DatabaseConfig()
print(f"Connecting to {cfg.host}:{cfg.port} (SSL: {cfg.use_ssl})")
```

## 3. Dependency Injection (`@Env.inject`)

You can automatically inject environment variables into function arguments using the `@Env.inject` decorator. It only injects the variable if the caller doesn't provide it.

```python
from nestify.env import Env

@Env.inject(api_token="SECRET_TOKEN")
def connect_to_service(api_token: str = None):
    if api_token is None:
        raise ValueError("Missing Token!")
    print(f"Connecting with token: {api_token}")

# Will use the SECRET_TOKEN from the environment
connect_to_service()

# Will override the environment
connect_to_service(api_token="my_custom_token")
```
