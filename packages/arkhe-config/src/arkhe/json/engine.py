"""
arkhe.json.engine
---------------------
Main orchestrator — ``Json`` is the single entry point for all JSON operations.

Improvements over the original
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* ``from_dict`` / ``from_json`` / ``from_file`` / ``from_url``
  — typed deserialisation into ``@json_serializable`` classes.
* ``to_dict`` / ``to_json``
  — serialise any ``@json_serializable`` instance.
* ``safe_save``
  — atomic file write (sibling temp file + ``os.replace``).
* ``flatten`` / ``unflatten``
  — convert between nested dicts and dot-path dicts.
* ``diff`` / ``patch``
  — compare and apply RFC 7396 merge patches.
* ``pick`` / ``omit`` / ``rename_keys``
  — lightweight dict transforms.
* ``stream_jsonl`` / ``write_jsonl``
  — JSON Lines (NDJSON) support.
* ``register_encoder`` / ``register_decoder``
  — plug in custom type handlers without subclassing.
* All backwards-compatible aliases preserved.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Type, TypeVar, Union

from arkhe.json.exceptions import JsonError, JsonParseError, JsonValidationError
from arkhe.json.models import JsonArray, JsonObject, JsonType
from arkhe.json.parser import JsonParser
from arkhe.json.serializer import JsonSerializer
from arkhe.json.utils import (
    deep_merge, diff, flatten, omit, patch, pick, rename_keys, unflatten,
)
from arkhe.json.validator import FieldConstraint, JsonValidator

T = TypeVar("T")


class Json:
    """
    Arkhe JSON engine — the single import you need for all JSON work.

    Sections
    --------
    * **Parse / load**      — string, file, URL, JSONL
    * **Typed mapping**     — ``from_dict``, ``from_file``, ``from_url``
    * **Serialise / save**  — ``stringify``, ``save``, ``safe_save``
    * **Dict utilities**    — ``merge``, ``diff``, ``patch``, ``flatten`` …
    * **Validation**        — ``validate``
    * **Registration**      — ``register_encoder``, ``register_decoder``
    """

    # ==================================================================
    # Parse / Load
    # ==================================================================

    @classmethod
    def parse(cls, text: str) -> Any:
        """
        Parse a JSON string into raw Python objects (dict, list, …).

        Example::

            data = Json.parse('{"key": "value"}')
        """
        return JsonParser.parse(text)

    @classmethod
    def read(cls, path: Union[str, Path]) -> Any:
        """
        Read and parse a JSON file into raw Python objects.

        Example::

            data = Json.read("config.json")
            print(data["database"]["host"])
        """
        return JsonParser.read_file(path)

    @classmethod
    def load(
        cls,
        path: Union[str, Path],
        defaults: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Read a JSON file with optional *defaults* merged underneath.

        Unlike the original, returns a plain ``dict`` (no hidden DotDict
        dependency).  Use ``from_file`` for typed class mapping.

        Example::

            cfg = Json.load("config.json", defaults={"debug": False, "port": 8080})
        """
        data = JsonParser.read_file(path)
        if defaults and isinstance(data, dict):
            data = deep_merge(defaults, data)
        return data

    @classmethod
    def read_url(
        cls,
        url: str,
        *,
        timeout: float = 10.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Fetch and parse a remote JSON endpoint.

        Example::

            status = Json.read_url("https://api.example.com/health")
        """
        return JsonParser.read_url(url, timeout=timeout, headers=headers)

    # ==================================================================
    # Typed mapping  (Gson / Jackson–style)
    # ==================================================================

    @classmethod
    def from_dict(cls, data: Dict[str, Any], target: Type[T]) -> T:
        """
        Map a plain dict to a ``@json_serializable`` class instance.

        Example::

            user = Json.from_dict({"name": "Alice", "age": 30}, User)
        """
        return JsonParser._coerce(data, target)

    @classmethod
    def from_json(cls, text: str, target: Type[T]) -> T:
        """
        Parse a JSON string and map it directly to *target*.

        Example::

            user = Json.from_json('{"name": "Alice"}', User)
        """
        return JsonParser.parse_as(text, target)

    @classmethod
    def from_file(cls, path: Union[str, Path], target: Type[T]) -> T:
        """
        Read a JSON file and map it directly to *target*.

        Example::

            config = Json.from_file("config.json", AppConfig)
        """
        return JsonParser.read_file_as(path, target)

    @classmethod
    def from_url(
        cls,
        url: str,
        target: Type[T],
        *,
        timeout: float = 10.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> T:
        """
        Fetch a remote JSON endpoint and map it directly to *target*.

        Example::

            repo = Json.from_url("https://api.github.com/repos/org/name", Repo)
        """
        return JsonParser.read_url_as(url, target, timeout=timeout, headers=headers)

    @classmethod
    def to_dict(cls, instance: Any) -> Dict[str, Any]:
        """
        Serialise a ``@json_serializable`` instance to a plain dict.

        Example::

            d = Json.to_dict(user)
        """
        if not hasattr(instance, "to_dict"):
            raise JsonError(
                f"{type(instance).__name__} is not decorated with @json_serializable."
            )
        return instance.to_dict()

    @classmethod
    def to_json(cls, instance: Any, *, pretty: bool = False) -> str:
        """
        Serialise a ``@json_serializable`` instance to a JSON string.

        Example::

            text = Json.to_json(user, pretty=True)
        """
        if hasattr(instance, "to_json"):
            return instance.to_json(pretty=pretty)
        return JsonSerializer.stringify(instance, pretty=pretty)

    # ==================================================================
    # Serialise / Save
    # ==================================================================

    @classmethod
    def stringify(cls, data: Any, *, sort_keys: bool = False) -> str:
        """
        Serialise *data* to a compact JSON string.

        Handles ``datetime``, ``UUID``, ``Enum``, ``Path``, ``dataclass``,
        ``set``, ``@json_serializable`` instances, and more via
        ``NestifyEncoder``.

        Example::

            Json.stringify({"ts": datetime.now()})
        """
        return JsonSerializer.stringify(data, pretty=False, sort_keys=sort_keys)

    @classmethod
    def pretty(cls, data: Any, *, sort_keys: bool = False) -> str:
        """
        Serialise *data* to a pretty-printed (2-space) JSON string.

        Example::

            print(Json.pretty({"key": "value"}))
        """
        return JsonSerializer.stringify(data, pretty=True, sort_keys=sort_keys)

    @classmethod
    def save(
        cls,
        path: Union[str, Path],
        data: Any,
        *,
        pretty: bool = True,
        sort_keys: bool = False,
    ) -> None:
        """
        Serialise *data* and write it to *path*.

        Parent directories are created automatically.

        Example::

            Json.save("output/results.json", results)
        """
        JsonSerializer.save(path, data, pretty=pretty, sort_keys=sort_keys)

    @classmethod
    def safe_save(
        cls,
        path: Union[str, Path],
        data: Any,
        *,
        pretty: bool = True,
        sort_keys: bool = False,
    ) -> None:
        """
        **Atomically** serialise *data* and write it to *path*.

        Uses a sibling temp file + ``os.replace()`` so the destination is
        never left in a partially-written state, even if the process is
        interrupted.

        Example::

            Json.safe_save("config/settings.json", settings)
        """
        JsonSerializer.safe_save(path, data, pretty=pretty, sort_keys=sort_keys)

    # ==================================================================
    # JSON Lines (NDJSON)
    # ==================================================================

    @classmethod
    def stream_jsonl(
        cls,
        path: Union[str, Path],
        *,
        skip_errors: bool = False,
    ) -> Iterator[Any]:
        """
        Stream a JSON Lines file, yielding one parsed object per line.

        Example::

            for event in Json.stream_jsonl("events.jsonl"):
                process(event)
        """
        return JsonParser.read_jsonl(path, skip_errors=skip_errors)

    @classmethod
    def stream_jsonl_as(
        cls,
        path: Union[str, Path],
        target: Type[T],
        *,
        skip_errors: bool = False,
    ) -> Iterator[T]:
        """
        Stream a JSONL file, mapping each record to *target*.

        Example::

            for event in Json.stream_jsonl_as("events.jsonl", Event):
                print(event.name)
        """
        return JsonParser.read_jsonl_as(path, target, skip_errors=skip_errors)

    @classmethod
    def write_jsonl(
        cls,
        path: Union[str, Path],
        rows: List[Any],
        *,
        append: bool = False,
    ) -> Path:
        """
        Write a list of objects to a JSON Lines file.

        Example::

            Json.write_jsonl("events.jsonl", [e.to_dict() for e in events])
        """
        return JsonParser.write_jsonl(path, rows, append=append)

    # ==================================================================
    # Dict utilities
    # ==================================================================

    @classmethod
    def merge(
        cls,
        base: Dict[str, Any],
        override: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Deep-merge *override* into *base* and return a new dict.

        ``None`` values in *override* delete the key (RFC 7396).

        Example::

            merged = Json.merge(defaults, user_config)
        """
        return deep_merge(base, override)

    @classmethod
    def diff(
        cls,
        a: Dict[str, Any],
        b: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Return a list of change records describing what changed from *a* to *b*.

        Each record has ``"op"`` (``"add"`` | ``"remove"`` | ``"change"``),
        ``"path"`` (dot-notation), and ``"value"`` / ``"from"`` / ``"to"``.

        Example::

            changes = Json.diff(old_config, new_config)
            for c in changes:
                print(c["op"], c["path"])
        """
        return diff(a, b)

    @classmethod
    def patch(
        cls,
        document: Dict[str, Any],
        merge_patch: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply a JSON Merge Patch (RFC 7396) to *document*.

        Example::

            updated = Json.patch(config, {"debug": True, "legacy_key": None})
        """
        return patch(document, merge_patch)

    @classmethod
    def flatten(cls, data: Dict[str, Any], *, sep: str = ".") -> Dict[str, Any]:
        """
        Flatten a nested dict to single-level dot-path keys.

        Example::

            Json.flatten({"a": {"b": 1}})   # → {"a.b": 1}
        """
        return flatten(data, sep=sep)

    @classmethod
    def unflatten(cls, data: Dict[str, Any], *, sep: str = ".") -> Dict[str, Any]:
        """
        Reconstruct a nested dict from dot-path keys.

        Example::

            Json.unflatten({"a.b": 1})   # → {"a": {"b": 1}}
        """
        return unflatten(data, sep=sep)

    @classmethod
    def pick(cls, data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        """
        Return a new dict containing only *keys*.

        Example::

            Json.pick(user, ["id", "name"])
        """
        return pick(data, keys)

    @classmethod
    def omit(cls, data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        """
        Return a new dict with *keys* removed.

        Example::

            Json.omit(user, ["password", "token"])
        """
        return omit(data, keys)

    @classmethod
    def rename_keys(
        cls,
        data: Dict[str, Any],
        mapping: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Return a new dict with keys renamed per *mapping*.

        Example::

            Json.rename_keys(row, {"userId": "user_id", "createdAt": "created_at"})
        """
        return rename_keys(data, mapping)

    # ==================================================================
    # Validation
    # ==================================================================

    @classmethod
    def validate(
        cls,
        data: Union[Dict[str, Any], Any],
        schema: Dict[str, Any],
    ) -> bool:
        """
        Validate *data* against *schema*.

        Schema values support:
        * Plain types: ``int``, ``str``, ``bool``, …
        * ``Optional[T]``
        * ``List[T]``
        * ``Annotated[T, FieldConstraint(min=…, max=…, regex=…, choices=…)]``
        * Nested ``dict`` for nested object schemas

        Raises ``JsonValidationError`` on failure with full dot-path error messages.

        Example::

            from typing import Annotated, List, Optional
            from arkhe.json import Json, FieldConstraint

            Json.validate(data, {
                "title":  str,
                "fps":    Annotated[int, FieldConstraint(min=1, max=240)],
                "tags":   List[str],
                "author": Optional[str],
            })
        """
        return JsonValidator.validate(data, schema)

    # ==================================================================
    # File utilities
    # ==================================================================

    @classmethod
    def exists(cls, path: Union[str, Path]) -> bool:
        """Return ``True`` if the JSON file at *path* exists."""
        return Path(path).is_file()

    # ==================================================================
    # Registration
    # ==================================================================

    @classmethod
    def register_encoder(cls, typ: Type, fn: Callable[[Any], Any]) -> None:
        """
        Register a custom serialiser for *typ*.

        The function receives a value of *typ* and must return a
        JSON-serialisable object.

        Example::

            import numpy as np
            Json.register_encoder(np.ndarray, lambda a: a.tolist())
            Json.register_encoder(np.integer, int)
        """
        JsonSerializer.register_encoder(typ, fn)

    @classmethod
    def register_decoder(cls, key: str, fn: Callable[[Any], Any]) -> None:
        """
        Register a per-key post-processor for deserialisation.

        The function is called with the raw JSON value for every object that
        contains *key*, and its return value replaces the raw value.

        Example::

            from datetime import datetime
            Json.register_decoder(
                "created_at",
                lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
            )
        """
        JsonParser.register_decoder(key, fn)

    # ==================================================================
    # Backwards-compatible aliases (original API)
    # ==================================================================

    #: Alias for ``save`` — keeps original callers working unchanged.
    @classmethod
    def save_file(cls, path: Union[str, Path], data: Any, pretty: bool = True) -> None:
        cls.save(path, data, pretty=pretty)

    @classmethod
    def parse_as_dotdict(cls, text: str) -> Any:
        """Deprecated — use ``parse`` and wrap manually if needed."""
        from arkhe.yaml import DotDict
        data = cls.parse(text)
        if isinstance(data, dict):
            return DotDict(data)
        return data


__all__ = ["Json"]
