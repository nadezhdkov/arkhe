# Console Tools (`arkhe.console`)

The `Console` module provides modern, rich terminal output utilities including colored printing, structured tables, progress bars, interactive input helpers, and animated spinners.

## Import
```python
from arkhe.console import Console
```

## 1. Colored Printing

Print colored and formatted text to the terminal effortlessly.

```python
Console.success("Process completed successfully!")
Console.error("Failed to load configuration.")
Console.warn("Database connection is slow.")
Console.info("Starting background worker...")
Console.dim("This is a less important message.")

# Custom printing
Console.print("Custom Text", color="magenta", bold=True)
```

## 2. Interactive Input

Interactive prompt helpers for CLI applications.

```python
# Ask for text with a default value
name = Console.ask("What is your name?", default="Guest")

# Ask a yes/no question
if Console.confirm("Do you want to proceed?", default=True):
    pass

# Choice menu
option = Console.choose("Select an environment", ["dev", "staging", "prod"])
```

## 3. Progress Bars

Track progress for iterable tasks or manual increments.

```python
# As a context manager
with Console.progress(total=100, label="Downloading") as bar:
    for _ in range(100):
        bar.update(1)

# As an iterator wrapper
items = [1, 2, 3, 4, 5]
for item in Console.progress(items, label="Processing"):
    # Do work
    pass
```

## 4. Animated Spinners

Display an animated spinner for indeterminate loading tasks.

```python
with Console.spinner("Fetching data from API..."):
    # Simulated work
    import time
    time.sleep(2)
```

## 5. Formatted Tables

Print structured dictionaries as aligned ASCII tables.

```python
data = [
    {"ID": 1, "Name": "Alice", "Role": "Admin"},
    {"ID": 2, "Name": "Bob", "Role": "User"},
]

Console.table(data, title="User Directory")
```
