"""
arkhe.slogger — Structured, colorful system logger.

Usage:
    from arkhe.slogger import SLogger, get_logger, LogLevel

    log = get_logger("myapp")
    log.info("Server started")
"""

from arkhe.slogger.slogger import (
    SLogger,
    get_logger,
    LogLevel,
    Formatter,
    SimpleFormatter,
    JSONFormatter,
    ConfigError,
    Logger,
)

__all__ = [
    "SLogger",
    "get_logger",
    "LogLevel",
    "Formatter",
    "SimpleFormatter",
    "JSONFormatter",
    "ConfigError",
    "Logger",
]
