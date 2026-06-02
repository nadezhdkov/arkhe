"""
nestifypy.slogger — Structured, colorful system logger.

Usage:
    from nestifypy.slogger import SLogger, get_logger, LogLevel

    log = get_logger("myapp")
    log.info("Server started")
"""

from nestifypy.slogger.slogger import (
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
