# Core Systems (`nestify.core`)

The `core` module provides the backbone for application architecture, including a standardized Logger, a central Registry for state management, and a dynamic Plugin system.

## 1. Logger

A globally accessible, timestamped, and colored logger.

```python
from nestify.core import Logger, LogLevel

# Setup
Logger.set_level(LogLevel.DEBUG)
Logger.set_prefix("MY_APP")
Logger.set_file("app.log") # Automatically writes to file

# Usage
Logger.debug("Tracing variables...")
Logger.info("Application started.")
Logger.warn("Memory usage is high.")
Logger.error("Failed to connect to database.")
Logger.success("Migration complete.")

# Print full stacktrace of current exception
Logger.trace()
```

## 2. Registry

A generic, namespaced registry to hold commands, configurations, singletons, or assets globally.

```python
from nestify.core import Registry

# Register an object in a category namespace
Registry.register("services", "database", db_connection_instance)

# Retrieve later
db = Registry.get("services", "database")

# Check if exists
if Registry.exists("services", "database"):
    print("DB is available")

# Fetch all items in a category
all_services = Registry.all("services")
```

## 3. Plugin System

A decorator-based system for building extensible applications.

```python
from nestify.core import Plugin

# Define a plugin class
@Plugin.info(name="auth_plugin", version="1.0.0", description="OAuth support")
class AuthPlugin:
    def authenticate(self):
        pass

# Register it manually
Plugin.register(AuthPlugin)

# Or load dynamically from a file path
Plugin.load("plugins/custom_auth.py")

# Retrieve all registered plugins
available_plugins = Plugin.all()
```
