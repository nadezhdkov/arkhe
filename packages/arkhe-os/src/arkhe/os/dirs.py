"""
arkhe.os.dirs
-----------------
Complete, cross-platform directory utilities.

Design rules
~~~~~~~~~~~~
* Destructive operations never raise on missing paths unless ``strict=True``.
* Listings are always sorted and return ``Path`` objects.
* ``temp()`` is a context manager — temp dirs are always cleaned up.
* ``tree()`` produces a human-readable directory tree string (like ``tree(1)``).
"""
from __future__ import annotations

import os
import shutil
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Callable, Generator, Iterator, List, Optional


class Dirs:
    """Complete directory utilities."""

    # ------------------------------------------------------------------
    # Creation / deletion
    # ------------------------------------------------------------------

    @staticmethod
    def create(path: str | Path) -> Path:
        """Create *path* and all missing parents.  No-op if already exists."""
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    # Friendlier alias
    ensure = create

    @staticmethod
    def delete(path: str | Path, *, missing_ok: bool = True) -> None:
        """
        Recursively delete *path*.

        Raises ``FileNotFoundError`` only when ``missing_ok=False``.
        """
        p = Path(path)
        if p.is_dir():
            shutil.rmtree(p)
        elif not missing_ok:
            raise FileNotFoundError(f"Directory not found: {p}")

    @staticmethod
    def empty_out(path: str | Path) -> Path:
        """
        Remove all contents of *path* without deleting the directory itself.
        """
        p = Path(path)
        for child in p.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        return p

    # ------------------------------------------------------------------
    # Copy / move / rename
    # ------------------------------------------------------------------

    @staticmethod
    def copy(
        src: str | Path,
        dst: str | Path,
        *,
        overwrite: bool = False,
    ) -> Path:
        """
        Copy an entire directory tree from *src* to *dst*.

        If *overwrite=True* and *dst* exists it is removed first.
        """
        dst_p = Path(dst)
        if overwrite and dst_p.exists():
            shutil.rmtree(dst_p)
        return Path(shutil.copytree(str(src), str(dst_p)))

    @staticmethod
    def move(src: str | Path, dst: str | Path) -> Path:
        """Move *src* to *dst* (cross-device safe)."""
        return Path(shutil.move(str(src), str(dst)))

    @staticmethod
    def rename(src: str | Path, new_name: str) -> Path:
        """
        Rename *src* in-place.

        *new_name* is a bare name, not a full path.
        """
        p = Path(src)
        dst = p.parent / new_name
        return p.rename(dst)

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    @staticmethod
    def list(
        path: str | Path = ".",
        *,
        pattern: str = "*",
        sort_by: str = "name",
        reverse: bool = False,
    ) -> List[Path]:
        """
        List immediate children (files **and** dirs) matching *pattern*.

        *sort_by* accepts: ``"name"`` | ``"size"`` | ``"modified"``.
        """
        children = list(Path(path).glob(pattern))
        if sort_by == "size":
            children.sort(key=lambda p: p.stat().st_size, reverse=reverse)
        elif sort_by == "modified":
            children.sort(key=lambda p: p.stat().st_mtime, reverse=reverse)
        else:
            children.sort(reverse=reverse)
        return children

    @staticmethod
    def list_files(
        path: str | Path = ".",
        *,
        pattern: str = "*",
        sort_by: str = "name",
        reverse: bool = False,
    ) -> List[Path]:
        """Return only files (not sub-directories)."""
        return [
            p for p in Dirs.list(path, pattern=pattern, sort_by=sort_by, reverse=reverse)
            if p.is_file()
        ]

    @staticmethod
    def list_dirs(
        path: str | Path = ".",
        *,
        pattern: str = "*",
        sort_by: str = "name",
        reverse: bool = False,
    ) -> List[Path]:
        """Return only sub-directories."""
        return [
            p for p in Dirs.list(path, pattern=pattern, sort_by=sort_by, reverse=reverse)
            if p.is_dir()
        ]

    # ------------------------------------------------------------------
    # Recursive walk / search
    # ------------------------------------------------------------------

    @staticmethod
    def walk(
        path: str | Path,
        *,
        files_only: bool = True,
    ) -> Iterator[Path]:
        """
        Yield every path under *path* recursively.

        When ``files_only=True`` (default) only files are yielded; set to
        ``False`` to include sub-directories too.
        """
        for p in Path(path).rglob("*"):
            if files_only and not p.is_file():
                continue
            yield p

    @staticmethod
    def find(
        pattern: str,
        directory: str | Path = ".",
        *,
        dirs_only: bool = False,
    ) -> Iterator[Path]:
        """
        Yield entries matching *pattern* (glob) under *directory*.

        Set ``dirs_only=True`` to restrict results to directories.
        """
        for p in Path(directory).rglob(pattern):
            if dirs_only and not p.is_dir():
                continue
            yield p

    @staticmethod
    def filter(
        path: str | Path,
        predicate: Callable[[Path], bool],
        *,
        recursive: bool = False,
    ) -> List[Path]:
        """
        Return all entries for which *predicate* returns ``True``.

        Example — find files larger than 1 MB::

            Dirs.filter(".", lambda p: p.is_file() and p.stat().st_size > 1_000_000)
        """
        glob = Path(path).rglob("*") if recursive else Path(path).iterdir()
        return sorted(p for p in glob if predicate(p))

    # ------------------------------------------------------------------
    # Predicates / metadata
    # ------------------------------------------------------------------

    @staticmethod
    def exists(path: str | Path) -> bool:
        """Return ``True`` if *path* is an existing directory."""
        return Path(path).is_dir()

    @staticmethod
    def is_empty(path: str | Path) -> bool:
        """Return ``True`` if the directory has no children."""
        return not any(Path(path).iterdir())

    @staticmethod
    def size(path: str | Path) -> int:
        """Return the total size of all files under *path* in bytes."""
        return sum(
            f.stat().st_size for f in Path(path).rglob("*") if f.is_file()
        )

    @staticmethod
    def size_human(path: str | Path) -> str:
        """Return a human-readable total size (e.g. ``"12.3 MB"``)."""
        n: float = Dirs.size(path)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"

    @staticmethod
    def file_count(path: str | Path, *, recursive: bool = True) -> int:
        """Count files under *path*."""
        glob = Path(path).rglob("*") if recursive else Path(path).iterdir()
        return sum(1 for p in glob if p.is_file())

    @staticmethod
    def last_modified(path: str | Path) -> datetime:
        """Return the most-recently modified timestamp across all files."""
        ts = max(
            (f.stat().st_mtime for f in Path(path).rglob("*") if f.is_file()),
            default=Path(path).stat().st_mtime,
        )
        return datetime.fromtimestamp(ts)

    # ------------------------------------------------------------------
    # Visualisation
    # ------------------------------------------------------------------

    @staticmethod
    def tree(
        path: str | Path = ".",
        *,
        max_depth: Optional[int] = None,
        show_hidden: bool = False,
        _prefix: str = "",
        _depth: int = 0,
    ) -> str:
        """
        Return a ``tree(1)``-style directory listing as a string.

        Example output::

            project/
            ├── src/
            │   ├── main.py
            │   └── utils.py
            └── tests/
                └── test_main.py

        Parameters
        ----------
        max_depth:
            Stop recursing beyond this depth.  ``None`` = unlimited.
        show_hidden:
            Include entries whose name starts with ``.``.
        """
        p = Path(path)
        lines: List[str] = []

        if _depth == 0:
            lines.append(f"{p.name}/")

        if max_depth is not None and _depth >= max_depth:
            return "\n".join(lines)

        try:
            entries = sorted(p.iterdir())
        except PermissionError:
            return "\n".join(lines)

        if not show_hidden:
            entries = [e for e in entries if not e.name.startswith(".")]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{_prefix}{connector}{entry.name}{suffix}")

            if entry.is_dir():
                extension = "    " if is_last else "│   "
                sub = Dirs.tree(
                    entry,
                    max_depth=max_depth,
                    show_hidden=show_hidden,
                    _prefix=_prefix + extension,
                    _depth=_depth + 1,
                )
                if sub:
                    lines.append(sub)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Context managers
    # ------------------------------------------------------------------

    @staticmethod
    @contextmanager
    def temp(
        suffix: str = "",
        prefix: str = "nestify_",
    ) -> Generator[Path, None, None]:
        """
        Context manager: create a temporary directory, yield its ``Path``,
        and delete it (with all contents) on exit.

        Example::

            with Dirs.temp() as tmp:
                (tmp / "data.json").write_text("{}")
                process(tmp)
            # tmp is gone here
        """
        with tempfile.TemporaryDirectory(suffix=suffix, prefix=prefix) as td:
            yield Path(td)

    @staticmethod
    @contextmanager
    def cd(path: str | Path) -> Generator[Path, None, None]:
        """
        Context manager: temporarily change the working directory to *path*.

        Example::

            with Dirs.cd("src"):
                subprocess.run(["python", "main.py"])
            # cwd is restored here
        """
        origin = Path.cwd()
        try:
            os.chdir(path)
            yield Path(path).resolve()
        finally:
            os.chdir(origin)


__all__ = ["Dirs"]
