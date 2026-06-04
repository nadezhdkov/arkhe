"""
arkhe.os.paths
------------------
Clean, cross-platform path manipulation.  Every method is a pure transform —
no I/O, no side-effects.  I/O lives in ``files.py`` and ``dirs.py``.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Iterator, List, Optional, Sequence


class Paths:
    """
    Stateless path-manipulation utilities.

    All methods accept ``str | Path`` and return ``Path`` (or a primitive
    where a ``Path`` would be meaningless).  Nothing touches the filesystem.
    """

    # ------------------------------------------------------------------
    # Construction / joining
    # ------------------------------------------------------------------

    @staticmethod
    def join(*parts: str | Path) -> Path:
        """Join path segments, regardless of leading slashes in later parts."""
        result = Path(parts[0])
        for part in parts[1:]:
            result = result / part
        return result

    @staticmethod
    def resolve(path: str | Path) -> Path:
        """Return the absolute, symlink-resolved path."""
        return Path(path).resolve()

    @staticmethod
    def expand(path: str | Path) -> Path:
        """Expand ``~`` and ``$VAR`` / ``%VAR%`` in *path*."""
        return Path(os.path.expandvars(os.path.expanduser(str(path))))

    @staticmethod
    def normalize(path: str | Path) -> Path:
        """Collapse redundant separators and ``.`` / ``..`` components."""
        return Path(os.path.normpath(str(path)))

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @staticmethod
    def home() -> Path:
        """Return the current user's home directory."""
        return Path.home()

    @staticmethod
    def cwd() -> Path:
        """Return the current working directory."""
        return Path.cwd()

    @staticmethod
    def parent(path: str | Path, levels: int = 1) -> Path:
        """
        Return the parent directory *levels* steps up.

        >>> Paths.parent("/a/b/c/d", levels=2)  # → /a/b
        """
        p = Path(path)
        for _ in range(levels):
            p = p.parent
        return p

    @staticmethod
    def parents(path: str | Path) -> List[Path]:
        """Return every ancestor from immediate parent up to root."""
        return list(Path(path).parents)

    @staticmethod
    def parts(path: str | Path) -> tuple[str, ...]:
        """Return the path split into its individual components."""
        return Path(path).parts

    @staticmethod
    def common(paths: Sequence[str | Path]) -> Path:
        """Return the longest common sub-path of *paths*."""
        return Path(os.path.commonpath([str(p) for p in paths]))

    # ------------------------------------------------------------------
    # Predicates
    # ------------------------------------------------------------------

    @staticmethod
    def is_absolute(path: str | Path) -> bool:
        return Path(path).is_absolute()

    @staticmethod
    def is_relative_to(path: str | Path, base: str | Path) -> bool:
        """Return ``True`` if *path* is relative to *base*."""
        try:
            Path(path).relative_to(base)
            return True
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Name / extension manipulation
    # ------------------------------------------------------------------

    @staticmethod
    def name(path: str | Path) -> str:
        """Final component, including suffix: ``"file.txt"``."""
        return Path(path).name

    @staticmethod
    def stem(path: str | Path) -> str:
        """Final component without suffix: ``"file"``."""
        return Path(path).stem

    @staticmethod
    def suffix(path: str | Path) -> str:
        """Last suffix including dot: ``".txt"``."""
        return Path(path).suffix

    @staticmethod
    def suffixes(path: str | Path) -> List[str]:
        """All suffixes: ``[".tar", ".gz"]``."""
        return list(Path(path).suffixes)

    @staticmethod
    def with_name(path: str | Path, name: str) -> Path:
        """Return *path* with the final component replaced by *name*."""
        return Path(path).with_name(name)

    @staticmethod
    def with_stem(path: str | Path, stem: str) -> Path:
        """Return *path* with the stem replaced (suffix preserved)."""
        return Path(path).with_stem(stem)

    @staticmethod
    def with_suffix(path: str | Path, suffix: str) -> Path:
        """
        Return *path* with suffix replaced.

        Pass ``""`` to remove the suffix entirely.
        """
        return Path(path).with_suffix(suffix)

    # ------------------------------------------------------------------
    # Relative / absolute conversion
    # ------------------------------------------------------------------

    @staticmethod
    def relative(path: str | Path, base: str | Path) -> Path:
        """Return *path* relative to *base*."""
        return Path(path).relative_to(base)

    @staticmethod
    def relative_cwd(path: str | Path) -> Path:
        """Return *path* relative to the current working directory."""
        return Path(path).resolve().relative_to(Path.cwd())

    # ------------------------------------------------------------------
    # URI / string helpers
    # ------------------------------------------------------------------

    @staticmethod
    def to_uri(path: str | Path) -> str:
        """Convert an absolute path to a ``file://`` URI."""
        return Path(path).resolve().as_uri()

    @staticmethod
    def to_posix(path: str | Path) -> str:
        """Return the path as a POSIX string (forward slashes)."""
        return Path(path).as_posix()

    # ------------------------------------------------------------------
    # Temp helpers (pure path construction — no I/O)
    # ------------------------------------------------------------------

    @staticmethod
    def temp_dir() -> Path:
        """Return the OS temporary directory."""
        return Path(tempfile.gettempdir())

    @staticmethod
    def temp_path(suffix: str = "", prefix: str = "nestify_") -> Path:
        """
        Return a unique temp file *path* without creating it.

        The caller is responsible for creation and cleanup.
        """
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)
        Path(path).unlink(missing_ok=True)
        return Path(path)


__all__ = ["Paths"]
