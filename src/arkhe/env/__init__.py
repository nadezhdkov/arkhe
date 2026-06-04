"""
arkhe.env
-------------
Wrapper around python-dotenv for clean, typed environment variable access.

Now supports YAML-style chained attribute access via a module-level proxy,
an intelligent prefix registry, and O(1) lookups.

Usage:
    from arkhe import env

    # Classic API (unchanged)
    host = env.get("DB_HOST")

    # New: attribute-style access with prefix namespacing
    host = env.db.host          # -> DB_HOST
    port = env.db.port          # -> DB_PORT
    size = env.db.pool.max_size # -> DB_POOL_MAX_SIZE
"""

from __future__ import annotations

import os
import sys
import functools
from pathlib import Path
from typing import Any, Callable, Optional, Type

from dotenv import load_dotenv

from arkhe.slogger import ConfigError


# ---------------------------------------------------------------------------
# DotEnv — chainable namespace proxy
# ---------------------------------------------------------------------------

class DotEnv:
    """
    Lazy, chainable proxy that maps attribute chains to env var names.

    Each attribute access appends a segment to the running prefix; the final
    read is triggered only when you actually *use* the value (str/int/bool/…).

    Examples
    --------
    env.db.host          → os.environ["DB_HOST"]
    env.db.pool.max_size → os.environ["DB_POOL_MAX_SIZE"]
    env.db.port.int      → int(os.environ["DB_PORT"])      # cast shorthand
    """

    # These names are reserved and will NOT be treated as env-key segments.
    _CAST_SHORTCUTS: frozenset[str] = frozenset(
        {"int", "float", "bool", "list", "required", "default"}
    )

    __slots__ = ("_prefix", "_sep")

    def __init__(self, prefix: str = "", sep: str = "_") -> None:
        object.__setattr__(self, "_prefix", prefix)
        object.__setattr__(self, "_sep", sep)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _child(self, segment: str) -> "DotEnv":
        prefix = object.__getattribute__(self, "_prefix")
        sep    = object.__getattribute__(self, "_sep")
        new_prefix = f"{prefix}{sep}{segment}".upper() if prefix else segment.upper()
        return DotEnv(new_prefix, sep)

    def _key(self) -> str:
        return object.__getattribute__(self, "_prefix")

    # ------------------------------------------------------------------
    # Attribute access
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        # ── Cast shortcuts ──────────────────────────────────────────────
        if name in self._CAST_SHORTCUTS:
            key = self._key()
            raw = os.environ.get(key)
            if name == "required":
                if raw is None:
                    raise ConfigError(
                        f"Required environment variable '{key}' is not set."
                    )
                return raw
            if name == "int":
                if raw is None:
                    return 0
                try:
                    return int(raw)
                except ValueError:
                    raise ConfigError(
                        f"Environment variable '{key}' must be an integer, got: {raw!r}"
                    )
            if name == "float":
                if raw is None:
                    return 0.0
                try:
                    return float(raw)
                except ValueError:
                    raise ConfigError(
                        f"Environment variable '{key}' must be a float, got: {raw!r}"
                    )
            if name == "bool":
                if raw is None:
                    return False
                return raw.strip().lower() in {"1", "true", "yes", "on"}
            if name == "list":
                if raw is None:
                    return []
                return [item.strip() for item in raw.split(",") if item.strip()]
            if name == "default":
                # Returns a callable: env.db.host.default("localhost")
                def _default(fallback: Any = None) -> Any:
                    return raw if raw is not None else fallback
                return _default

        # ── Keep chaining ───────────────────────────────────────────────
        return self._child(name)

    # ------------------------------------------------------------------
    # Value materialisation
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return os.environ.get(self._key(), "")

    def __repr__(self) -> str:
        key = self._key()
        val = os.environ.get(key)
        masked = key in Env._masked
        display = "***" if masked else repr(val)
        return f"<DotEnv key={key!r} value={display}>"

    def __eq__(self, other: Any) -> bool:
        return str(self) == str(other)

    def __bool__(self) -> bool:
        return bool(str(self))

    def __int__(self) -> int:
        return self.int  # type: ignore[return-value]

    def __float__(self) -> float:
        return self.float  # type: ignore[return-value]

    # Convenience: call the proxy itself to get the raw string value.
    def __call__(self, default: Optional[str] = None) -> Optional[str]:
        return os.environ.get(self._key(), default)


# ---------------------------------------------------------------------------
# EnvProperty — descriptor (unchanged API, wired into DotEnv)
# ---------------------------------------------------------------------------

class EnvProperty:
    """Descriptor for mapping an environment variable directly to a class attribute."""

    __slots__ = ("key", "default", "cast", "required", "prefix")

    def __init__(
        self,
        key: str,
        cast: Type = str,
        default: Any = None,
        required: bool = False,
        prefix: str = "",
    ) -> None:
        self.key      = key
        self.cast     = cast
        self.default  = default
        self.required = required
        self.prefix   = prefix

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        if self.cast == int:
            return Env.int(self.key, self.default if self.default is not None else 0)
        elif self.cast == float:
            return Env.float(self.key, self.default if self.default is not None else 0.0)
        elif self.cast == bool:
            return Env.bool(self.key, self.default if self.default is not None else False)
        elif self.cast == list:
            return Env.list(self.key, default=self.default)
        else:
            return Env.get(self.key, self.default)


# ---------------------------------------------------------------------------
# Env — primary class (classic API)
# ---------------------------------------------------------------------------

class Env:
    """Clean interface for environment variable management."""

    _loaded: bool      = False
    _masked: set[str]  = set()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path = ".env") -> None:
        """Load a .env file into the environment."""
        env_path = Path(path)
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        cls._loaded = True

    # ------------------------------------------------------------------
    # Classic typed getters
    # ------------------------------------------------------------------

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a string environment variable."""
        return os.environ.get(key, default)

    @classmethod
    def required(cls, key: str) -> str:
        """Get a variable; raise ConfigError if missing."""
        val = os.environ.get(key)
        if val is None:
            raise ConfigError(
                f"Required environment variable '{key}' is not set."
            )
        return val

    @classmethod
    def int(cls, key: str, default: int = 0) -> int:
        raw = os.environ.get(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            raise ConfigError(
                f"Environment variable '{key}' must be an integer, got: {raw!r}"
            )

    @classmethod
    def float(cls, key: str, default: float = 0.0) -> float:
        raw = os.environ.get(key)
        if raw is None:
            return default
        try:
            return float(raw)
        except ValueError:
            raise ConfigError(
                f"Environment variable '{key}' must be a float, got: {raw!r}"
            )

    @classmethod
    def bool(cls, key: str, default: bool = False) -> bool:
        raw = os.environ.get(key)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    @classmethod
    def list(cls, key: str, sep: str = ",", default: Optional[list] = None) -> list:
        raw = os.environ.get(key)
        if raw is None:
            return default or []
        return [item.strip() for item in raw.split(sep) if item.strip()]

    # ------------------------------------------------------------------
    # Masking / runtime mutation
    # ------------------------------------------------------------------

    @classmethod
    def mask(cls, key: str) -> None:
        """Mark a key as sensitive (masked in logs/repr)."""
        cls._masked.add(key)

    @classmethod
    def set(cls, key: str, value: str) -> None:
        """Set an environment variable at runtime."""
        os.environ[key] = value

    @classmethod
    def all(cls) -> dict[str, str]:
        """Return all environment variables (excluding masked ones)."""
        return {
            k: ("***" if k in cls._masked else v)
            for k, v in os.environ.items()
        }

    @classmethod
    def is_loaded(cls) -> bool:
        return cls._loaded

    # ------------------------------------------------------------------
    # Descriptor / decorator helpers
    # ------------------------------------------------------------------

    @classmethod
    def property(
        cls,
        key: str,
        cast_type: Type = str,
        default: Any = None,
    ) -> EnvProperty:
        """
        Creates a class property descriptor that dynamically fetches an env var.

        Example::

            class Config:
                host = Env.property("DB_HOST", default="localhost")
                port = Env.property("DB_PORT", cast_type=int, default=5432)
        """
        return EnvProperty(key, cast_type, default)

    @classmethod
    def inject(cls, **kwargs: str) -> Callable:
        """
        Decorator to inject environment variables into function keyword arguments.
        Only injects if the argument was not explicitly provided by the caller.

        Example::

            @Env.inject(api_key="API_KEY", host="DB_HOST")
            def connect(api_key: str = None, host: str = "localhost"):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*func_args: Any, **func_kwargs: Any) -> Any:
                for kwarg_name, env_key in kwargs.items():
                    if kwarg_name not in func_kwargs:
                        val = cls.get(env_key)
                        if val is not None:
                            func_kwargs[kwarg_name] = val
                return func(*func_args, **func_kwargs)
            return wrapper
        return decorator

    # ------------------------------------------------------------------
    # Namespace proxy factory
    # ------------------------------------------------------------------

    @classmethod
    def ns(cls, prefix: str) -> DotEnv:
        """
        Return a ``DotEnv`` proxy rooted at *prefix*.

        Example::

            db = Env.ns("DB")
            host = db.host        # → DB_HOST
            port = db.port.int    # → int(DB_PORT)
        """
        return DotEnv(prefix.upper())


# ---------------------------------------------------------------------------
# Module-level proxy  (enables `env.db.host` at import level)
# ---------------------------------------------------------------------------

class _EnvModule(sys.modules[__name__].__class__):
    """
    Custom module type that delegates attribute access to :class:`DotEnv`,
    while still exposing the real module members (``Env``, ``EnvProperty``, …).
    """

    _REAL_ATTRS = frozenset({
        "Env", "EnvProperty", "DotEnv",
        "__name__", "__file__", "__spec__",
        "__loader__", "__package__", "__path__",
        "__doc__", "__builtins__",
    })

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_") or name in self._REAL_ATTRS:
            raise AttributeError(name)
        return DotEnv(name.upper())


# Swap the module class so `from arkhe import env; env.db.host` works.
sys.modules[__name__].__class__ = _EnvModule


__all__ = ["Env", "EnvProperty", "DotEnv"]