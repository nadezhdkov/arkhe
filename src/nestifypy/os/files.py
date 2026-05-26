"""
nestifypy.os.files
---------------
Clean cross-platform wrappers around file operations.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterator, List

class Files:
    """File operations."""

    @staticmethod
    def create(path: str | Path, content: str = "") -> Path:
        """Create a file (and parent dirs) with optional content."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    @staticmethod
    def delete(path: str | Path) -> None:
        """Delete a file if it exists."""
        p = Path(path)
        if p.is_file():
            p.unlink()

    @staticmethod
    def copy(src: str | Path, dst: str | Path) -> Path:
        """Copy a file to destination."""
        return Path(shutil.copy2(str(src), str(dst)))

    @staticmethod
    def move(src: str | Path, dst: str | Path) -> Path:
        """Move a file to destination."""
        return Path(shutil.move(str(src), str(dst)))

    @staticmethod
    def read(path: str | Path) -> str:
        """Read and return file text."""
        return Path(path).read_text(encoding="utf-8")

    @staticmethod
    def write(path: str | Path, content: str, append: bool = False) -> None:
        """Write text to file."""
        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def exists(path: str | Path) -> bool:
        return Path(path).is_file()

    @staticmethod
    def size(path: str | Path) -> int:
        """Return file size in bytes."""
        return Path(path).stat().st_size

    @staticmethod
    def extension(path: str | Path) -> str:
        return Path(path).suffix

    @staticmethod
    def stem(path: str | Path) -> str:
        return Path(path).stem

    @staticmethod
    def find(pattern: str, directory: str | Path = ".") -> Iterator[Path]:
        """Find files matching a glob pattern recursively."""
        yield from Path(directory).rglob(pattern)

    @staticmethod
    def stream_lines(path: str | Path) -> Iterator[str]:
        """Read file and return an iterator of lines (stripped of newline), saving memory."""
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                yield line.rstrip('\n')
