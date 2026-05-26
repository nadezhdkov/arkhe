# JSON Utilities

`nestify.json` is a simple wrapper for JSON processing, providing dot-notation access to dictionaries (similar to `nestify.yaml`) and robust file I/O operations.

## 1. Quick Start

```python
from nestify.json import Json

# Read a JSON file
data = Json.load("data/users.json")

# Write a JSON file (automatically indented)
Json.save("data/output.json", {"status": "success", "code": 200})
```

## 2. DotDict Usage

Nestify uses a `DotDict` wrapper allowing you to access nested dictionary keys as object attributes.

```python
from nestify.json import DotDict

user_data = {
    "user": {
        "profile": {
            "name": "Alice",
            "age": 30
        }
    }
}

dot_data = DotDict(user_data)

# Access via dot notation
print(dot_data.user.profile.name) # "Alice"

# Standard dict access still works
print(dot_data["user"]["profile"]["age"]) # 30
```

## 3. Serialization and Deserialization

If you need to serialize Python objects (e.g. Dataclasses, Enum) to JSON, use the `dump` method.

```python
from dataclasses import dataclass
from nestify.json import Json

@dataclass
class Config:
    host: str
    port: int

cfg = Config(host="localhost", port=8080)

# Dumps the dataclass to a JSON string
json_str = Json.dumps(cfg)
```
