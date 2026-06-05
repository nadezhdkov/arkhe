"""
arkhe.json
--------------
Complete JSON engine for NestifyPy.

Quick start
~~~~~~~~~~~
**1. Raw parsing and serialisation (no setup needed)**::

    from arkhe.json import Json

    data = Json.read("config.json")
    Json.save("output.json", data, pretty=True)
    text = Json.stringify({"ts": datetime.now()})   # datetime handled automatically

**2. Typed classes (Gson / Jackson style)**::

    from arkhe.json import Json, json_serializable, json_field, json_validator

    @json_serializable
    class Config:
        host: str
        port: int  = json_field(default=8080)
        debug: bool = json_field(default=False)

    cfg = Json.from_file("config.json", Config)
    print(cfg.host, cfg.port)
    Json.safe_save("config.json", cfg.to_dict())

**3. Schema validation**::

    from typing import Annotated, List, Optional
    from arkhe.json import Json, FieldConstraint

    Json.validate(data, {
        "title": str,
        "fps":   Annotated[int, FieldConstraint(min=1, max=240)],
        "tags":  List[str],
        "meta":  {"version": str},
    })

**4. Dict utilities**::

    merged  = Json.merge(defaults, overrides)
    changes = Json.diff(old, new)
    updated = Json.patch(doc, {"debug": True, "legacy": None})
    flat    = Json.flatten({"a": {"b": 1}})     # → {"a.b": 1}
    nested  = Json.unflatten({"a.b": 1})        # → {"a": {"b": 1}}
    subset  = Json.pick(user, ["id", "name"])
    clean   = Json.omit(user, ["password"])

**5. JSON Lines**::

    for event in Json.stream_jsonl("events.jsonl"):
        process(event)

    Json.write_jsonl("out.jsonl", rows)

**6. Custom type handlers**::

    import numpy as np
    Json.register_encoder(np.ndarray, lambda a: a.tolist())

    from datetime import datetime
    Json.register_decoder("created_at", lambda v: datetime.fromisoformat(v))
"""

from arkhe.json.engine import Json
from arkhe.json.exceptions import (
    JsonError,
    JsonMappingError,
    JsonParseError,
    JsonSerializationError,
    JsonValidationError,
)
from arkhe.json.models import JsonArray, JsonObject, JsonType
from arkhe.json.decorators import (
    FieldMeta,
    is_json_serializable,
    json_alias,
    json_exclude,
    json_field,
    json_post_load,
    json_pre_dump,
    json_serializable,
    json_validator,
)
from arkhe.json.validator import FieldConstraint
from arkhe.json.utils import (
    deep_merge,
    diff,
    flatten,
    omit,
    patch,
    pick,
    rename_keys,
    unflatten,
)

__all__ = [
    # ── Core engine ────────────────────────────────────────────────────
    "Json",

    # ── Decorators ─────────────────────────────────────────────────────
    "json_serializable",
    "json_field",
    "json_exclude",
    "json_alias",
    "json_validator",
    "json_post_load",
    "json_pre_dump",
    "FieldMeta",
    "is_json_serializable",

    # ── Validation ─────────────────────────────────────────────────────
    "FieldConstraint",

    # ── Exceptions ─────────────────────────────────────────────────────
    "JsonError",
    "JsonParseError",
    "JsonValidationError",
    "JsonSerializationError",
    "JsonMappingError",

    # ── Type aliases ───────────────────────────────────────────────────
    "JsonType",
    "JsonObject",
    "JsonArray",

    # ── Standalone utilities (also on Json.*) ──────────────────────────
    "deep_merge",
    "flatten",
    "unflatten",
    "diff",
    "patch",
    "pick",
    "omit",
    "rename_keys",
]
