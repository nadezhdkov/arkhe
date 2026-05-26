"""
nestifypy.os.dirs
--------------
Clean cross-platform wrappers around directory operations.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterator, List

class Dirs:
    """Directory operations."""

    @staticmethod
    def create(path: str | Path) -> Path:
        """Create directory and all parents."""
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def delete(path: str | Path) -> None:
        """Delete a directory tree."""
        p = Path(path)
        if p.is_dir():
            shutil.rmtree(p)

    @staticmethod
    def copy(src: str | Path, dst: str | Path) -> Path:
        return Path(shutil.copytree(str(src), str(dst)))

    @staticmethod
    def exists(path: str | Path) -> bool:
        return Path(path).is_dir()

    @staticmethod
    def list(path: str | Path = ".") -> List[Path]:
        """List immediate children of a directory."""
        return sorted(Path(path).iterdir())

    @staticmethod
    def empty(path: str | Path) -> bool:
        return not any(Path(path).iterdir())

    @staticmethod
    def size(path: str | Path) -> int:
        """Total size of a directory in bytes."""
        return sum(
            f.stat().st_size
            for f in Path(path).rglob("*")
            if f.is_file()
        )

    @staticmethod
    def walk(path: str | Path) -> Iterator[Path]:
        """Yield all files recursively under path."""
        for p in Path(path).rglob("*"):
            if p.is_file():
                yield p
