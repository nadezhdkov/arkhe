# `arkhe.json` — JSON Engine

A complete JSON engine for NestifyPy. Far beyond a thin `json.loads` wrapper — it provides typed class mapping (Gson / Jackson–style), atomic file writes, schema validation with value constraints, JSON Lines streaming, deep dict utilities, and automatic handling of Python types the stdlib encoder rejects.

> **Zero third-party dependencies** — stdlib only.

---

## Table of Contents

- [Installation & Import](#installation--import)
- [Package Layout](#package-layout)
- [Quick Start](#quick-start)
- [Decorator System](#decorator-system)
  - [`@json_serializable`](#json_serializable)
  - [`json_field(...)`](#json_field)
  - [`@json_exclude`](#json_exclude)
  - [`@json_alias`](#json_alias)
  - [`@json_validator`](#json_validator)
  - [`@json_post_load`](#json_post_load)
  - [`@json_pre_dump`](#json_pre_dump)
  - [Injected methods: `from_dict`, `to_dict`, `from_json`, `to_json`](#injected-methods)
  - [Inheritance](#inheritance)
- [`Json` — Core Engine](#json--core-engine)
  - [Parse & Load](#parse--load)
  - [Typed Mapping](#typed-mapping)
  - [Serialise & Save](#serialise--save)
  - [JSON Lines (NDJSON)](#json-lines-ndjson)
  - [Dict Utilities](#dict-utilities)
  - [Validation](#validation)
  - [Registration](#registration)
  - [File Utilities](#file-utilities)
- [`FieldConstraint` — Value Constraints](#fieldconstraint--value-constraints)
- [`NestifyEncoder` — Custom Type Handling](#nestifyencoder--custom-type-handling)
- [Exceptions](#exceptions)
- [Type Aliases](#type-aliases)
- [Design Rules](#design-rules)

---

## Installation & Import

```python
# Everything you need from one import
from arkhe.json import Json

# Decorator system
from arkhe.json import (
    json_serializable,
    json_field,
    json_exclude,
    json_alias,
    json_validator,
    json_post_load,
    json_pre_dump,
)

# Validation
from arkhe.json import FieldConstraint

# Standalone utilities (also available as Json.*)
from arkhe.json import deep_merge, flatten, unflatten, diff, patch, pick, omit

# Exceptions
from arkhe.json import JsonParseError, JsonValidationError, JsonMappingError
```

---

## Package Layout

```
arkhe/json/
├── __init__.py      ← public API surface
├── engine.py        ← Json  (single orchestrator class)
├── decorators.py    ← @json_serializable, json_field, …
├── serializer.py    ← JsonSerializer, NestifyEncoder
├── parser.py        ← JsonParser  (string, file, URL, JSONL)
├── validator.py     ← JsonValidator, FieldConstraint
├── utils.py         ← deep_merge, flatten, diff, patch, …
├── models.py        ← JsonType, JsonObject, JsonArray
└── exceptions.py    ← JsonError hierarchy
```

---

## Quick Start

```python
from arkhe.json import Json, json_serializable, json_field, FieldConstraint
from typing import Annotated, List, Optional

# ── 1. Raw read / write ───────────────────────────────────────────────
data = Json.read("config.json")
Json.save("output.json", data, pretty=True)

# ── 2. Typed class ────────────────────────────────────────────────────
@json_serializable
class ServerConfig:
    host:  str
    port:  int  = json_field(default=8080)
    debug: bool = json_field(default=False)

cfg = Json.from_file("server.json", ServerConfig)
print(cfg.host, cfg.port)
Json.safe_save("server.json", cfg.to_dict())

# ── 3. Validation ─────────────────────────────────────────────────────
Json.validate(data, {
    "host": str,
    "port": Annotated[int, FieldConstraint(min=1, max=65535)],
    "tags": List[str],
})

# ── 4. Dict utilities ─────────────────────────────────────────────────
merged = Json.merge(defaults, overrides)
flat   = Json.flatten({"database": {"host": "localhost"}})  # {"database.host": "localhost"}

# ── 5. JSON Lines ─────────────────────────────────────────────────────
for event in Json.stream_jsonl("events.jsonl"):
    process(event)
```

---

## Decorator System

The decorator system enables Gson / Jackson–style typed (de)serialisation. Once a class is annotated with `@json_serializable`, it gains automatic `from_dict`, `to_dict`, `from_json`, and `to_json` methods with zero boilerplate.

---

### `@json_serializable`

Marks a class for automatic JSON (de)serialisation. Works with plain classes, dataclasses, and classes with custom `__init__`.

```python
from arkhe.json import json_serializable

@json_serializable
class User:
    name:  str
    email: str
    age:   int
```

What it does internally:

1. Discovers all annotated fields (via `__annotations__`, MRO-aware).
2. Processes any `json_field(...)` / `json_alias(...)` descriptors.
3. Registers `@json_validator`, `@json_post_load`, `@json_pre_dump` methods.
4. Injects `from_dict`, `to_dict`, `from_json`, `to_json`, `__repr__`.

---

### `json_field(...)`

Configure a field's mapping behaviour. Assigned as a default value.

```python
from arkhe.json import json_serializable, json_field

@json_serializable
class Product:
    name:        str
    price:       float = json_field(default=0.0)
    internal_id: str   = json_field(exclude=True)
    created_at:  str   = json_field(alias="createdAt")
    description: str   = json_field(exclude_if_none=True)
    sku:         str   = json_field(required=True)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `alias` | `str \| None` | `None` | JSON key to use instead of the Python name |
| `default` | `Any` | `MISSING` | Default value when the key is absent in `from_dict` |
| `exclude` | `bool` | `False` | Skip this field in both directions (read and write) |
| `exclude_if_none` | `bool` | `False` | Omit from serialised output when value is `None` |
| `required` | `bool` | `False` | Raise `JsonMappingError` if the key is absent in `from_dict` |

`default` also accepts a **callable** (e.g. `list`, `dict`, a lambda) — it is called once per instance to avoid the shared-mutable-default pitfall:

```python
@json_serializable
class Config:
    tags: list = json_field(default=list)       # new [] per instance
    meta: dict = json_field(default=dict)       # new {} per instance
    ids:  list = json_field(default=lambda: [1, 2, 3])
```

---

### `@json_exclude`

Class-level decorator that excludes a field without modifying the attribute definition. Useful when you can't add `json_field(exclude=True)` inline (e.g. inherited or third-party attributes).

```python
from arkhe.json import json_serializable, json_exclude

@json_serializable
@json_exclude("_cache")
@json_exclude("_session")
class Model:
    name:     str
    _cache:   dict
    _session: object
```

---

### `@json_alias`

Shorthand to map a field to a different JSON key, without the full `json_field(...)` syntax.

```python
from arkhe.json import json_serializable, json_alias

@json_serializable
class Event:
    user_id:    str = json_alias("userId")      # JSON key = "userId"
    created_at: str = json_alias("createdAt")
```

---

### `@json_validator`

Attach a validation method to a specific field. Called after `from_dict` assigns the value. Raise any exception to signal failure — it is caught and reported as a `JsonValidationError`.

```python
from arkhe.json import json_serializable, json_field, json_validator

@json_serializable
class Order:
    quantity: int  = json_field(default=1)
    price:    float

    @json_validator("quantity")
    def _check_quantity(self, value: int) -> None:
        if value <= 0:
            raise ValueError("quantity must be greater than 0")

    @json_validator("price")
    def _check_price(self, value: float) -> None:
        if value < 0:
            raise ValueError("price must be non-negative")
```

Multiple validators can be attached to the same field — they are all called in definition order.

---

### `@json_post_load`

Mark a method to be called after `from_dict` finishes mapping all fields. Use for derived-field computation, normalisation, or cross-field validation.

```python
from arkhe.json import json_serializable, json_field, json_post_load

@json_serializable
class User:
    first_name: str
    last_name:  str
    full_name:  str = json_field(exclude=True)  # computed, never read from JSON

    @json_post_load
    def _build_full_name(self) -> None:
        self.full_name = f"{self.first_name} {self.last_name}"

    @json_post_load
    def _normalize_names(self) -> None:
        self.first_name = self.first_name.strip().title()
        self.last_name  = self.last_name.strip().title()
```

Multiple `@json_post_load` methods are all called, in definition order.

---

### `@json_pre_dump`

Mark a method to be called before `to_dict` serialises the object. The method may mutate the instance in-place.

```python
from arkhe.json import json_serializable, json_pre_dump
from datetime import datetime, timezone

@json_serializable
class Report:
    title:        str
    generated_at: str = ""

    @json_pre_dump
    def _stamp_time(self) -> None:
        self.generated_at = datetime.now(timezone.utc).isoformat()
```

---

### Injected Methods

Every `@json_serializable` class gains these four methods automatically.

#### `MyClass.from_dict(data: dict) → MyClass`

Deserialise from a plain dictionary. Keys are matched by alias first, then by Python name.

```python
user = User.from_dict({
    "name": "Alice",
    "email": "ALICE@EXAMPLE.COM",
    "joinedAt": "2024-01-15",
})
```

Behaviour on missing keys:

| Situation | Result |
|---|---|
| Key has a `default` | Default value is used |
| Key is `required=True` and absent | `JsonMappingError` raised |
| Key is neither — no default | Field set to `None` |

#### `instance.to_dict() → dict`

Serialise to a plain dictionary. Respects `exclude`, `exclude_if_none`, and `alias`. Nested `@json_serializable` objects are recursively serialised.

```python
d = user.to_dict()
# {"name": "Alice", "email": "alice@example.com", "joinedAt": "2024-01-15"}
```

#### `MyClass.from_json(text: str) → MyClass`

Parse a JSON string and map it to the class. Equivalent to `MyClass.from_dict(json.loads(text))`.

```python
user = User.from_json('{"name": "Alice", "email": "alice@example.com"}')
```

#### `instance.to_json(*, pretty=False) → str`

Serialise to a JSON string.

```python
print(user.to_json(pretty=True))
```

---

### Inheritance

`@json_serializable` is MRO-aware. Fields defined in parent classes are inherited by children. Child decorators override parent field metadata for the same attribute name.

```python
@json_serializable
class Base:
    id:   int
    name: str

@json_serializable
class Admin(Base):
    role: str = json_field(default="admin")
    # inherits id and name from Base

admin = Admin.from_dict({"id": 1, "name": "Root"})
print(admin.role)   # "admin"
print(admin.to_dict())  # {"id": 1, "name": "Root", "role": "admin"}
```

---

## `Json` — Core Engine

```python
from arkhe.json import Json
```

The single orchestrator. Every operation in the package is accessible through `Json`.

---

### Parse & Load

#### `Json.parse(text) → Any`

Parse a JSON string into raw Python objects.

```python
data = Json.parse('{"key": "value", "count": 42}')
```

#### `Json.read(path) → Any`

Read and parse a JSON file.

```python
config = Json.read("config/app.json")
print(config["database"]["host"])
```

#### `Json.load(path, defaults=None) → Any`

Read a JSON file with optional `defaults` merged underneath (file values win on conflict). Useful for configuration with fallback values.

```python
cfg = Json.load("config.json", defaults={
    "debug": False,
    "port": 8080,
    "log_level": "INFO",
})
```

#### `Json.read_url(url, *, timeout=10.0, headers=None) → Any`

Fetch and parse a remote JSON endpoint. Uses `urllib` — no third-party HTTP library required.

```python
status = Json.read_url("https://api.example.com/health")
data   = Json.read_url(
    "https://api.github.com/repos/org/repo",
    headers={"Authorization": "Bearer token"},
    timeout=5.0,
)
```

---

### Typed Mapping

#### `Json.from_dict(data, target) → T`

Map a plain dict to a `@json_serializable` class instance.

```python
user = Json.from_dict({"name": "Alice", "age": 30}, User)
```

#### `Json.from_json(text, target) → T`

Parse a JSON string and map it to *target*.

```python
user = Json.from_json('{"name": "Alice"}', User)
```

#### `Json.from_file(path, target) → T`

Read a JSON file and map it directly to *target*.

```python
config = Json.from_file("config/app.json", AppConfig)
print(config.database.host)
```

#### `Json.from_url(url, target, *, timeout=10.0, headers=None) → T`

Fetch a remote JSON endpoint and map it to *target*.

```python
repo = Json.from_url("https://api.github.com/repos/org/name", GithubRepo)
print(repo.stargazers_count)
```

#### `Json.to_dict(instance) → dict`

Serialise a `@json_serializable` instance to a plain dict.

```python
d = Json.to_dict(user)
```

#### `Json.to_json(instance, *, pretty=False) → str`

Serialise a `@json_serializable` instance to a JSON string.

```python
text = Json.to_json(user, pretty=True)
```

---

### Serialise & Save

#### `Json.stringify(data, *, sort_keys=False) → str`

Serialise *data* to a compact JSON string. Handles all extended types via `NestifyEncoder`.

```python
from datetime import datetime
from uuid import uuid4

Json.stringify({
    "id":         uuid4(),
    "created_at": datetime.now(),
    "tags":       {"python", "json"},
})
# → '{"id": "...", "created_at": "2024-...", "tags": ["json", "python"]}'
```

#### `Json.pretty(data, *, sort_keys=False) → str`

Serialise *data* to a 2-space indented JSON string.

```python
print(Json.pretty({"a": 1, "b": [1, 2, 3]}))
```

#### `Json.save(path, data, *, pretty=True, sort_keys=False) → None`

Write *data* to a JSON file. Parent directories are created automatically.

```python
Json.save("output/results.json", results)
Json.save("compact.json", data, pretty=False)
```

#### `Json.safe_save(path, data, *, pretty=True, sort_keys=False) → None`

**Atomic write.** Writes to a sibling temp file first, then swaps it in with `os.replace()`. The destination is never left partially written, even if the process is killed mid-write.

```python
# Safe for config files and any data that must never be corrupted
Json.safe_save("config/settings.json", settings)
```

Use `safe_save` over `save` whenever the file is critical — config files, state files, checkpoints.

---

### JSON Lines (NDJSON)

JSON Lines format stores one JSON object per line. It is the standard format for log streams, event exports, and large dataset files.

#### `Json.stream_jsonl(path, *, skip_errors=False) → Iterator[Any]`

Stream a JSON Lines file, yielding one parsed object per line. Memory-efficient — the file is never fully loaded.

```python
for event in Json.stream_jsonl("events.jsonl"):
    process(event)
```

Set `skip_errors=True` to silently ignore malformed lines instead of raising.

#### `Json.stream_jsonl_as(path, target, *, skip_errors=False) → Iterator[T]`

Stream a JSONL file, mapping each record to a `@json_serializable` class.

```python
for order in Json.stream_jsonl_as("orders.jsonl", Order):
    print(order.total)
```

#### `Json.write_jsonl(path, rows, *, append=False) → Path`

Write a list of objects to a JSON Lines file. `NestifyEncoder` is used so `datetime`, `UUID`, etc. are handled automatically.

```python
Json.write_jsonl("export.jsonl", [u.to_dict() for u in users])

# Append mode — add new rows to an existing file
Json.write_jsonl("events.jsonl", new_events, append=True)
```

---

### Dict Utilities

All utilities are also importable as standalone functions from `arkhe.json`.

#### `Json.merge(base, override) → dict`

Recursively merge *override* into *base*. Dict keys are merged deeply; all other types are replaced. `None` values in *override* **delete** the key (RFC 7396 semantics).

```python
result = Json.merge(
    {"db": {"host": "localhost", "port": 5432}, "debug": False},
    {"db": {"port": 5433},                      "debug": True},
)
# → {"db": {"host": "localhost", "port": 5433}, "debug": True}

# Delete a key by setting it to None
Json.merge(config, {"legacy_key": None})
# → legacy_key is removed from the result
```

#### `Json.diff(a, b) → list[dict]`

Compute the difference between two dicts. Returns a list of change records with `"op"` (`"add"` | `"remove"` | `"change"`), `"path"` (dot-notation), and `"value"` / `"from"` / `"to"`.

```python
changes = Json.diff(
    {"version": "1.0", "debug": False, "old_key": "x"},
    {"version": "2.0", "debug": False, "new_key": "y"},
)
# → [
#     {"op": "change", "path": "version", "from": "1.0", "to": "2.0"},
#     {"op": "remove", "path": "old_key"},
#     {"op": "add",    "path": "new_key", "value": "y"},
# ]
```

#### `Json.patch(document, merge_patch) → dict`

Apply a JSON Merge Patch (RFC 7396). Same semantics as `merge` — `None` values delete keys. Returns a new dict; *document* is never mutated.

```python
updated = Json.patch(
    {"a": 1, "b": {"c": 2, "d": 3}, "e": 5},
    {"b": {"d": None, "f": 4}, "e": 99},
)
# → {"a": 1, "b": {"c": 2, "f": 4}, "e": 99}
```

#### `Json.flatten(data, *, sep=".") → dict`

Flatten a nested dict to single-level dot-path keys.

```python
Json.flatten({
    "database": {"host": "localhost", "pool": {"size": 10}},
    "debug": True,
})
# → {
#     "database.host":       "localhost",
#     "database.pool.size":  10,
#     "debug":               True,
# }
```

#### `Json.unflatten(data, *, sep=".") → dict`

Reconstruct a nested dict from dot-path keys. The inverse of `flatten`.

```python
Json.unflatten({
    "database.host":      "localhost",
    "database.pool.size": 10,
    "debug":              True,
})
# → {"database": {"host": "localhost", "pool": {"size": 10}}, "debug": True}
```

#### `Json.pick(data, keys) → dict`

Return a new dict containing only the specified keys.

```python
Json.pick(user, ["id", "name", "email"])
```

#### `Json.omit(data, keys) → dict`

Return a new dict with the specified keys removed.

```python
Json.omit(user, ["password", "token", "internal_id"])
```

#### `Json.rename_keys(data, mapping) → dict`

Return a new dict with keys renamed according to *mapping*. Keys not in *mapping* are kept as-is.

```python
Json.rename_keys(
    {"userId": 1, "createdAt": "2024-01-15", "name": "Alice"},
    {"userId": "user_id", "createdAt": "created_at"},
)
# → {"user_id": 1, "created_at": "2024-01-15", "name": "Alice"}
```

---

### Validation

#### `Json.validate(data, schema) → bool`

Validate *data* against *schema*. Returns `True` on success; raises `JsonValidationError` on failure with full dot-path error messages.

Schema values support the full Python type system:

```python
from typing import Annotated, List, Optional
from arkhe.json import Json, FieldConstraint

Json.validate(data, {
    # Plain types
    "title":   str,
    "enabled": bool,

    # Optional — field may be absent or None
    "author":  Optional[str],

    # List with typed elements
    "tags":    List[str],
    "scores":  List[float],

    # Value constraints via Annotated
    "fps":     Annotated[int,   FieldConstraint(min=1, max=240)],
    "name":    Annotated[str,   FieldConstraint(min_len=1, max_len=100)],
    "email":   Annotated[str,   FieldConstraint(regex=r".+@.+\..+")],
    "role":    Annotated[str,   FieldConstraint(choices=["admin", "user", "guest"])],

    # Nested object schema
    "database": {
        "host": str,
        "port": Annotated[int, FieldConstraint(min=1, max=65535)],
    },
})
```

---

### Registration

#### `Json.register_encoder(typ, fn) → None`

Register a custom serialiser for a type. The function receives a value of *typ* and must return a JSON-serialisable object. Registered encoders take priority over all built-ins.

```python
import numpy as np

Json.register_encoder(np.ndarray,  lambda a: a.tolist())
Json.register_encoder(np.integer,  int)
Json.register_encoder(np.floating, float)
Json.register_encoder(np.bool_,    bool)
```

#### `Json.register_decoder(key, fn) → None`

Register a per-key post-processor for deserialisation. The function is called with the raw JSON value for every parsed object that contains *key*. Its return value replaces the raw value.

```python
from datetime import datetime

Json.register_decoder(
    "created_at",
    lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
)
Json.register_decoder(
    "updated_at",
    lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
)

# Now any Json.read / Json.parse call will auto-convert these keys
data = Json.read("records.json")
print(type(data["created_at"]))  # <class 'datetime.datetime'>
```

---

### File Utilities

#### `Json.exists(path) → bool`

Return `True` if the JSON file at *path* exists.

```python
if not Json.exists("config/app.json"):
    Json.save("config/app.json", DEFAULT_CONFIG)
```

---

## `FieldConstraint` — Value Constraints

Used with `typing.Annotated` in schemas passed to `Json.validate`.

```python
from typing import Annotated
from arkhe.json import FieldConstraint

# All parameters are optional — combine freely
Annotated[int,   FieldConstraint(min=0, max=100)]
Annotated[float, FieldConstraint(min=0.0)]
Annotated[str,   FieldConstraint(min_len=1, max_len=255)]
Annotated[str,   FieldConstraint(regex=r"[a-zA-Z0-9_]+")]
Annotated[str,   FieldConstraint(choices=["active", "inactive", "pending"])]
Annotated[list,  FieldConstraint(min_len=1, max_len=100)]
```

| Parameter | Applies to | Description |
|---|---|---|
| `min` | `int`, `float` | Value must be ≥ `min` |
| `max` | `int`, `float` | Value must be ≤ `max` |
| `min_len` | `str`, `list` | Length must be ≥ `min_len` |
| `max_len` | `str`, `list` | Length must be ≤ `max_len` |
| `regex` | `str` | Must match `re.fullmatch(regex, value)` |
| `choices` | any | Must be in `choices` list |

---

## `NestifyEncoder` — Custom Type Handling

`NestifyEncoder` is the custom `json.JSONEncoder` used by all serialisation paths. It handles the following types **automatically**, with no configuration:

| Python type | JSON output |
|---|---|
| `datetime` | ISO 8601 string (`"2024-01-15T12:00:00"`) |
| `date` | ISO 8601 string (`"2024-01-15"`) |
| `UUID` | String (`"550e8400-e29b-41d4-a716-446655440000"`) |
| `Enum` | `.value` |
| `Path` | POSIX string (`"path/to/file.txt"`) |
| `dataclass` | `dataclasses.asdict()` |
| `set` / `frozenset` | Sorted list |
| `bytes` | Base-64 ASCII string |
| `@json_serializable` | `.to_dict()` |

Extend via `Json.register_encoder` — registered encoders always take priority.

---

## Exceptions

All exceptions inherit from `JsonError` → `ConfigError`.

```
JsonError
├── JsonParseError          — parsing / decoding failure
├── JsonValidationError     — schema or field-level validation failure
│     .errors: list[str]    — individual error messages with dot-paths
├── JsonSerializationError  — serialisation failure (unserializable type)
└── JsonMappingError        — from_dict / typed mapping failure
```

```python
from arkhe.json import JsonParseError, JsonValidationError, JsonMappingError

try:
    config = Json.from_file("config.json", AppConfig)
except JsonParseError as e:
    print(f"Bad JSON: {e}")
except JsonMappingError as e:
    print(f"Schema mismatch: {e}")

try:
    Json.validate(data, schema)
except JsonValidationError as e:
    print("Validation errors:")
    for err in e.errors:
        print(f"  {err}")
```

---

## Type Aliases

| Alias | Equivalent | Description |
|---|---|---|
| `JsonType` | `dict \| list \| str \| int \| float \| bool \| None` | Any value in a parsed JSON document |
| `JsonObject` | `dict[str, Any]` | A JSON object (dict at root) |
| `JsonArray` | `list[Any]` | A JSON array (list at root) |

---

## Design Rules

These principles are consistent across the entire package:

1. **One import, full access** — `from arkhe.json import Json` is enough for everything. Sub-modules are internal implementation details.
2. **Opt-in complexity** — raw `parse` / `read` / `save` work with zero setup. Typed mapping, validation, and constraints are all opt-in layers on top.
3. **Never partially write** — `safe_save` is available for every file write. Use it for any file that matters.
4. **Informative errors** — `JsonValidationError.errors` always includes the full dot-path to the failing field and a description of what was expected.
5. **Extended types by default** — `datetime`, `UUID`, `Enum`, `Path`, `dataclass`, `set`, and `bytes` are all serialisable without any registration.
6. **RFC 7396 semantics** — `merge` and `patch` follow the JSON Merge Patch standard: `None` values delete keys, not set them to null.
7. **Zero third-party dependencies** — the entire package uses the Python standard library only.
8. **Backwards compatible** — the original `Json` API (`load`, `read`, `parse`, `save`, `stringify`, `pretty`, `merge`, `validate`, `exists`) is fully preserved.
