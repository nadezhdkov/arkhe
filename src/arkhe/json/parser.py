"""
arkhe.json.parser
---------------------
Parsing logic: JSON string / file / URL / JSONL → Python objects.

Improvements over the original
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* ``parse_as(text, MyClass)`` — deserialise directly into a typed class.
* ``read_file_as(path, MyClass)`` — load a file straight into a typed class.
* ``read_url(url)`` — fetch and parse a remote JSON endpoint.
* ``read_jsonl(path)`` — stream a JSON Lines / NDJSON file.
* ``write_jsonl(path, rows)`` — write a JSON Lines file.
* Custom decoder support via ``JsonParser.register_decoder``.
* Detailed ``JsonParseError`` messages that include the file path or URL.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Type, TypeVar, Union
from urllib.request import Request, urlopen
from urllib.error import URLError

from arkhe.json.exceptions import JsonMappingError, JsonParseError
from arkhe.json.models import JsonObject

T = TypeVar("T")


class JsonParser:
    """Parse JSON from strings, files, URLs, and JSON Lines streams."""

    # Class-level registry: key → callable(value) → Python object
    # Used inside object_hook to post-process specific keys.
    _decoders: Dict[str, Callable[[Any], Any]] = {}

    # ------------------------------------------------------------------
    # Decoder registration
    # ------------------------------------------------------------------

    @classmethod
    def register_decoder(cls, key: str, fn: Callable[[Any], Any]) -> None:
        """
        Register a per-key post-processor called by ``object_hook``.

        Example — parse a ``"created_at"`` string back to ``datetime``::

            from datetime import datetime
            JsonParser.register_decoder(
                "created_at",
                lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
            )
        """
        cls._decoders[key] = fn

    @classmethod
    def _object_hook(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        if not cls._decoders:
            return d
        return {
            k: cls._decoders[k](v) if k in cls._decoders else v
            for k, v in d.items()
        }

    # ------------------------------------------------------------------
    # Core: string
    # ------------------------------------------------------------------

    @classmethod
    def parse(cls, text: str) -> Any:
        """Parse a JSON string into raw Python objects."""
        try:
            return json.loads(
                text,
                object_hook=cls._object_hook if cls._decoders else None,
            )
        except json.JSONDecodeError as exc:
            raise JsonParseError(
                f"Failed to parse JSON string at line {exc.lineno}, col {exc.colno}: {exc.msg}"
            ) from exc

    @classmethod
    def parse_as(cls, text: str, target: Type[T]) -> T:
        """
        Parse a JSON string and map the result directly to *target*.

        *target* must be decorated with ``@json_serializable``.

        Example::

            user = JsonParser.parse_as('{"name": "Alice"}', User)
        """
        data = cls.parse(text)
        return cls._coerce(data, target)

    # ------------------------------------------------------------------
    # Core: file
    # ------------------------------------------------------------------

    @classmethod
    def read_file(cls, path: Union[str, Path]) -> Any:
        """Read and parse a JSON file into raw Python objects."""
        p = Path(path)
        if not p.is_file():
            raise JsonParseError(f"JSON file not found: {p}")
        try:
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(
                    fh,
                    object_hook=cls._object_hook if cls._decoders else None,
                )
        except json.JSONDecodeError as exc:
            raise JsonParseError(
                f"Failed to parse '{p}' at line {exc.lineno}, col {exc.colno}: {exc.msg}"
            ) from exc

    @classmethod
    def read_file_as(cls, path: Union[str, Path], target: Type[T]) -> T:
        """
        Read a JSON file and map it directly to *target*.

        *target* must be decorated with ``@json_serializable``.

        Example::

            config = JsonParser.read_file_as("config.json", AppConfig)
        """
        data = cls.read_file(path)
        return cls._coerce(data, target)

    # ------------------------------------------------------------------
    # Remote: URL
    # ------------------------------------------------------------------

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

            data = JsonParser.read_url("https://api.example.com/status")
        """
        req = Request(url, headers=headers or {})
        try:
            with urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
        except URLError as exc:
            raise JsonParseError(f"Failed to fetch '{url}': {exc}") from exc
        try:
            return json.loads(
                raw,
                object_hook=cls._object_hook if cls._decoders else None,
            )
        except json.JSONDecodeError as exc:
            raise JsonParseError(
                f"Failed to parse JSON from '{url}': {exc.msg}"
            ) from exc

    @classmethod
    def read_url_as(
        cls,
        url: str,
        target: Type[T],
        *,
        timeout: float = 10.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> T:
        """
        Fetch a remote JSON endpoint and map it to *target*.
        """
        data = cls.read_url(url, timeout=timeout, headers=headers)
        return cls._coerce(data, target)

    # ------------------------------------------------------------------
    # JSON Lines (NDJSON)
    # ------------------------------------------------------------------

    @classmethod
    def read_jsonl(
        cls,
        path: Union[str, Path],
        *,
        skip_errors: bool = False,
    ) -> Iterator[Any]:
        """
        Stream a JSON Lines file (one JSON object per line).

        Parameters
        ----------
        skip_errors:
            When ``True``, malformed lines are silently skipped instead of
            raising ``JsonParseError``.

        Example::

            for record in JsonParser.read_jsonl("events.jsonl"):
                process(record)
        """
        p = Path(path)
        if not p.is_file():
            raise JsonParseError(f"JSONL file not found: {p}")
        with open(p, "r", encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    if skip_errors:
                        continue
                    raise JsonParseError(
                        f"JSONL parse error in '{p}' at line {lineno}: {exc.msg}"
                    ) from exc

    @classmethod
    def read_jsonl_as(
        cls,
        path: Union[str, Path],
        target: Type[T],
        *,
        skip_errors: bool = False,
    ) -> Iterator[T]:
        """
        Stream a JSONL file, mapping each record to *target*.
        """
        for record in cls.read_jsonl(path, skip_errors=skip_errors):
            yield cls._coerce(record, target)

    @staticmethod
    def write_jsonl(
        path: Union[str, Path],
        rows: List[Any],
        *,
        append: bool = False,
    ) -> Path:
        """
        Write a list of objects to a JSON Lines file.

        Each object is serialised with ``NestifyEncoder`` so that
        ``datetime``, ``UUID``, ``Enum``, etc. are handled automatically.
        """
        from arkhe.json.serializer import NestifyEncoder
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(p, mode, encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, cls=NestifyEncoder, ensure_ascii=False) + "\n")
        return p

    # ------------------------------------------------------------------
    # Internal coercion helper
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce(data: Any, target: Type[T]) -> T:
        """Map *data* (dict or list) onto *target* using its ``from_dict``."""
        if not hasattr(target, "from_dict"):
            raise JsonMappingError(
                f"{target.__name__} is not decorated with @json_serializable. "
                "Add @json_serializable to enable typed deserialisation."
            )
        if not isinstance(data, dict):
            raise JsonMappingError(
                f"Cannot map {type(data).__name__} to {target.__name__}: expected a JSON object."
            )
        return target.from_dict(data)


__all__ = ["JsonParser"]
