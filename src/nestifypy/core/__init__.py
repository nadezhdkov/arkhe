"""
nestifypy.core
-----------
The heart of the Nestifypy framework.
Provides Logger, Exceptions, Constants, Registry, and Plugin systems.
"""

from __future__ import annotations

import time
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type


# ─────────────────────────────────────────────
#  Log Levels
# ─────────────────────────────────────────────

class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3


# ─────────────────────────────────────────────
#  ANSI Colors
# ─────────────────────────────────────────────

class _Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    BG_RED     = "\033[41m"
    BG_GREEN   = "\033[42m"
    BG_YELLOW  = "\033[43m"
    BG_BLUE    = "\033[44m"


# ─────────────────────────────────────────────
#  Logger
# ─────────────────────────────────────────────

class Logger:
    """Colored, timestamped logger for Nestifypy."""

    _level: LogLevel = LogLevel.DEBUG
    _file_path: Optional[Path] = None
    _prefix: str = "nestifypy"

    @classmethod
    def set_level(cls, level: LogLevel) -> None:
        cls._level = level

    @classmethod
    def set_file(cls, path: str | Path) -> None:
        cls._file_path = Path(path)

    @classmethod
    def set_prefix(cls, prefix: str) -> None:
        cls._prefix = prefix

    @classmethod
    def _timestamp(cls) -> str:
        return datetime.now().strftime("%H:%M:%S")

    @classmethod
    def _write_file(cls, message: str) -> None:
        if cls._file_path:
            with open(cls._file_path, "a", encoding="utf-8") as f:
                f.write(message + "\n")

    @classmethod
    def _log(cls, level: str, color: str, *args: Any) -> None:
        message = " ".join(str(a) for a in args)
        ts = cls._timestamp()
        prefix = f"{_Colors.DIM}[{ts}]{_Colors.RESET}"
        tag = f"{color}{_Colors.BOLD}[{level}]{_Colors.RESET}"
        src = f"{_Colors.DIM}[{cls._prefix}]{_Colors.RESET}"
        line = f"{prefix} {tag} {src} {message}"
        print(line)
        cls._write_file(f"[{ts}] [{level}] [{cls._prefix}] {message}")

    @classmethod
    def debug(cls, *args: Any) -> None:
        if cls._level.value <= LogLevel.DEBUG.value:
            cls._log("DEBUG", _Colors.CYAN, *args)

    @classmethod
    def info(cls, *args: Any) -> None:
        if cls._level.value <= LogLevel.INFO.value:
            cls._log("INFO ", _Colors.GREEN, *args)

    @classmethod
    def warn(cls, *args: Any) -> None:
        if cls._level.value <= LogLevel.WARN.value:
            cls._log("WARN ", _Colors.YELLOW, *args)

    @classmethod
    def error(cls, *args: Any) -> None:
        if cls._level.value <= LogLevel.ERROR.value:
            cls._log("ERROR", _Colors.RED, *args)

    @classmethod
    def success(cls, *args: Any) -> None:
        cls._log("  OK ", _Colors.GREEN, *args)

    @classmethod
    def trace(cls) -> None:
        """Print the current traceback."""
        cls.error(traceback.format_exc())


# ─────────────────────────────────────────────
#  Custom Exceptions
# ─────────────────────────────────────────────

class NestifypyError(Exception):
    """Base exception for all Nestifypy errors."""


class ConfigError(NestifypyError):
    """Raised when configuration is invalid or missing."""


class PluginError(NestifypyError):
    """Raised when a plugin fails to load or register."""


class ValidationError(NestifypyError):
    """Raised when a validation check fails."""


class RegistryError(NestifypyError):
    """Raised when a registry operation fails."""


# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────

class Constants:
    VERSION      = "0.1.0"
    DEFAULT_FPS  = 60
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)


# ─────────────────────────────────────────────
#  Registry System
# ─────────────────────────────────────────────

class Registry:
    """
    Generic registry for commands, events, tasks, plugins, assets.
    Each category has its own isolated namespace.
    """

    _stores: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _store(cls, category: str) -> Dict[str, Any]:
        if category not in cls._stores:
            cls._stores[category] = {}
        return cls._stores[category]

    @classmethod
    def register(cls, category: str, name: str, obj: Any) -> None:
        store = cls._store(category)
        if name in store:
            raise RegistryError(
                f"'{name}' is already registered in category '{category}'"
            )
        store[name] = obj
        Logger.debug(f"Registered [{category}] → {name}")

    @classmethod
    def get(cls, category: str, name: str) -> Any:
        store = cls._store(category)
        if name not in store:
            raise RegistryError(
                f"'{name}' not found in category '{category}'"
            )
        return store[name]

    @classmethod
    def all(cls, category: str) -> Dict[str, Any]:
        return dict(cls._store(category))

    @classmethod
    def exists(cls, category: str, name: str) -> bool:
        return name in cls._store(category)

    @classmethod
    def clear(cls, category: str) -> None:
        cls._stores[category] = {}

    @classmethod
    def categories(cls) -> List[str]:
        return list(cls._stores.keys())


# ─────────────────────────────────────────────
#  Plugin System
# ─────────────────────────────────────────────

class _PluginMeta:
    def __init__(self, name: str, version: str, description: str = "") -> None:
        self.name = name
        self.version = version
        self.description = description

    def __repr__(self) -> str:
        return f"Plugin({self.name} v{self.version})"


class Plugin:
    """Decorator-based plugin system."""

    _plugins: Dict[str, Any] = {}

    @classmethod
    def register(cls, klass: Type) -> Type:
        """Register a class as a plugin."""
        name = getattr(klass, "_plugin_name", klass.__name__)
        cls._plugins[name] = klass
        Registry.register("plugins", name, klass)
        return klass

    @classmethod
    def info(
        cls,
        name: str,
        version: str = "1.0.0",
        description: str = ""
    ) -> Callable:
        """Attach metadata to a plugin class."""
        def decorator(klass: Type) -> Type:
            klass._plugin_name = name
            klass._plugin_meta = _PluginMeta(name, version, description)
            return klass
        return decorator

    @classmethod
    def load(cls, path: str | Path) -> None:
        """Dynamically load a plugin from a file."""
        import importlib.util
        p = Path(path)
        if not p.exists():
            raise PluginError(f"Plugin file not found: {p}")
        spec = importlib.util.spec_from_file_location(p.stem, p)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            Logger.info(f"Loaded plugin from {p}")

    @classmethod
    def all(cls) -> Dict[str, Any]:
        return dict(cls._plugins)


__all__ = [
    "Logger",
    "LogLevel",
    "Registry",
    "Plugin",
    "Constants",
    "NestifypyError",
    "ConfigError",
    "PluginError",
    "ValidationError",
    "RegistryError",
]
