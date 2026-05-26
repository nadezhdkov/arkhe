"""
nestifypy.os.paths
---------------
Clean cross-platform wrappers around path utilities.
"""

from __future__ import annotations

from pathlib import Path

class Paths:
    """Path utilities."""

    @staticmethod
    def join(*parts: str | Path) -> Path:
        result = Path(parts[0])
        for part in parts[1:]:
            result = result / part
        return result

    @staticmethod
    def resolve(path: str | Path) -> Path:
        return Path(path).resolve()

    @staticmethod
    def home() -> Path:
        return Path.home()

    @staticmethod
    def cwd() -> Path:
        return Path.cwd()

    @staticmethod
    def parent(path: str | Path) -> Path:
        return Path(path).parent

    @staticmethod
    def relative(path: str | Path, base: str | Path) -> Path:
        return Path(path).relative_to(base)

    @staticmethod
    def is_absolute(path: str | Path) -> bool:
        return Path(path).is_absolute()
