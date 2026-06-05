"""
arkhe.os.files
------------------
Complete, cross-platform file I/O utilities.

Design rules
~~~~~~~~~~~~
* Every method is a pure static — no hidden state.
* Text encoding defaults to ``utf-8`` everywhere.
* Destructive operations (delete, overwrite) are explicit, never silent.
* Atomic writes go through a sibling temp file then ``os.replace()``.
* Binary / JSON / TOML / CSV helpers live here so callers never need to
  import ``json``, ``csv``, etc. directly.
"""
from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import os
import shutil
import stat
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Union


class Files:
    """Complete file-I/O utilities."""

    # ------------------------------------------------------------------
    # Creation / deletion
    # ------------------------------------------------------------------

    @staticmethod
    def create(path: str | Path, content: str = "", encoding: str = "utf-8") -> Path:
        """
        Create a text file (and all parent dirs) with optional *content*.

        If the file already exists it is **overwritten**.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)
        return p

    @staticmethod
    def touch(path: str | Path) -> Path:
        """
        Create an empty file if it doesn't exist; update mtime if it does.
        Parent dirs are created automatically.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()
        return p

    @staticmethod
    def delete(path: str | Path, missing_ok: bool = True) -> None:
        """Delete a file.  Raises ``FileNotFoundError`` if ``missing_ok=False``."""
        Path(path).unlink(missing_ok=missing_ok)

    @staticmethod
    def rename(src: str | Path, new_name: str) -> Path:
        """
        Rename *src* to *new_name* inside the same directory.

        *new_name* is a bare name (``"report.txt"``), not a full path.
        """
        p = Path(src)
        dst = p.with_name(new_name)
        return p.rename(dst)

    # ------------------------------------------------------------------
    # Copy / move
    # ------------------------------------------------------------------

    @staticmethod
    def copy(src: str | Path, dst: str | Path, *, overwrite: bool = True) -> Path:
        """
        Copy *src* to *dst*, preserving metadata.

        If *dst* is a directory the file is placed inside it.
        Raises ``FileExistsError`` when *overwrite=False* and *dst* exists.
        """
        dst_p = Path(dst)
        if not overwrite and dst_p.exists():
            raise FileExistsError(f"Destination already exists: {dst_p}")
        return Path(shutil.copy2(str(src), str(dst)))

    @staticmethod
    def move(src: str | Path, dst: str | Path) -> Path:
        """Move *src* to *dst*.  *dst* may be a directory or full path."""
        return Path(shutil.move(str(src), str(dst)))

    # ------------------------------------------------------------------
    # Text read / write
    # ------------------------------------------------------------------

    @staticmethod
    def read(path: str | Path, encoding: str = "utf-8") -> str:
        """Read and return the entire file as a string."""
        return Path(path).read_text(encoding=encoding)

    @staticmethod
    def write(
        path: str | Path,
        content: str,
        *,
        append: bool = False,
        encoding: str = "utf-8",
        newline: Optional[str] = None,
    ) -> Path:
        """
        Write (or append) *content* to *path*.  Parent dirs are created.
        Returns the resolved ``Path``.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(p, mode, encoding=encoding, newline=newline) as fh:
            fh.write(content)
        return p

    @staticmethod
    def safe_write(path: str | Path, content: str, encoding: str = "utf-8") -> Path:
        """
        Atomically write *content* to *path*.

        The content is written to a sibling temp file first, then
        ``os.replace()`` swaps it in — so the destination is never
        partially written even if the process is interrupted.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=p.parent, prefix=".tmp_")
        try:
            with os.fdopen(tmp_fd, "w", encoding=encoding) as fh:
                fh.write(content)
            os.replace(tmp_path, p)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        return p

    @staticmethod
    def lines(path: str | Path, encoding: str = "utf-8") -> List[str]:
        """Return all lines as a list (newlines stripped)."""
        return Path(path).read_text(encoding=encoding).splitlines()

    @staticmethod
    def line_count(path: str | Path, encoding: str = "utf-8") -> int:
        """Count lines without loading the entire file into memory."""
        count = 0
        with open(path, "r", encoding=encoding) as fh:
            for _ in fh:
                count += 1
        return count

    @staticmethod
    def stream_lines(path: str | Path, encoding: str = "utf-8") -> Iterator[str]:
        """Yield lines one at a time (memory-efficient).  Newlines stripped."""
        with open(path, "r", encoding=encoding) as fh:
            for line in fh:
                yield line.rstrip("\r\n")

    @staticmethod
    def head(path: str | Path, n: int = 10, encoding: str = "utf-8") -> List[str]:
        """Return the first *n* lines."""
        result: List[str] = []
        with open(path, "r", encoding=encoding) as fh:
            for i, line in enumerate(fh):
                if i >= n:
                    break
                result.append(line.rstrip("\r\n"))
        return result

    @staticmethod
    def tail(path: str | Path, n: int = 10, encoding: str = "utf-8") -> List[str]:
        """Return the last *n* lines (reads full file once)."""
        lines = Path(path).read_text(encoding=encoding).splitlines()
        return lines[-n:]

    # ------------------------------------------------------------------
    # Binary read / write
    # ------------------------------------------------------------------

    @staticmethod
    def read_bytes(path: str | Path) -> bytes:
        """Read and return raw bytes."""
        return Path(path).read_bytes()

    @staticmethod
    def write_bytes(path: str | Path, data: bytes) -> Path:
        """Write raw *data* to *path*.  Parent dirs are created."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p

    # ------------------------------------------------------------------
    # Structured formats
    # ------------------------------------------------------------------

    @staticmethod
    def read_json(path: str | Path, encoding: str = "utf-8") -> Any:
        """Parse and return JSON from *path*."""
        with open(path, "r", encoding=encoding) as fh:
            return json.load(fh)

    @staticmethod
    def write_json(
        path: str | Path,
        data: Any,
        *,
        indent: int = 2,
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
    ) -> Path:
        """Serialise *data* to JSON and write to *path*."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding=encoding) as fh:
            json.dump(data, fh, indent=indent, ensure_ascii=ensure_ascii)
        return p

    @staticmethod
    def read_csv(
        path: str | Path,
        *,
        delimiter: str = ",",
        has_header: bool = True,
        encoding: str = "utf-8",
    ) -> List[Dict[str, str]] | List[List[str]]:
        """
        Parse a CSV file.

        * ``has_header=True``  → list of ``dict`` (keys from first row).
        * ``has_header=False`` → list of ``list[str]``.
        """
        with open(path, "r", encoding=encoding, newline="") as fh:
            if has_header:
                return list(csv.DictReader(fh, delimiter=delimiter))
            return list(csv.reader(fh, delimiter=delimiter))

    @staticmethod
    def write_csv(
        path: str | Path,
        rows: List[Dict[str, Any]] | List[List[Any]],
        *,
        fieldnames: Optional[List[str]] = None,
        delimiter: str = ",",
        encoding: str = "utf-8",
    ) -> Path:
        """
        Write *rows* to a CSV file.

        Accepts either a list of dicts (keys become the header) or a list
        of lists (raw rows, no automatic header).
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding=encoding, newline="") as fh:
            if rows and isinstance(rows[0], dict):
                keys = fieldnames or list(rows[0].keys())  # type: ignore[union-attr]
                writer = csv.DictWriter(fh, fieldnames=keys, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(rows)  # type: ignore[arg-type]
            else:
                writer_raw = csv.writer(fh, delimiter=delimiter)
                writer_raw.writerows(rows)  # type: ignore[arg-type]
        return p

    # ------------------------------------------------------------------
    # Metadata / inspection
    # ------------------------------------------------------------------

    @staticmethod
    def exists(path: str | Path) -> bool:
        """Return ``True`` if *path* points to a regular file."""
        return Path(path).is_file()

    @staticmethod
    def is_empty(path: str | Path) -> bool:
        """Return ``True`` if the file exists and has zero bytes."""
        p = Path(path)
        return p.is_file() and p.stat().st_size == 0

    @staticmethod
    def is_binary(path: str | Path, sample_bytes: int = 8192) -> bool:
        """
        Heuristic: return ``True`` if the file likely contains binary data.

        Reads at most *sample_bytes* and checks for null bytes (same approach
        used by ``git``).
        """
        with open(path, "rb") as fh:
            chunk = fh.read(sample_bytes)
        return b"\x00" in chunk

    @staticmethod
    def size(path: str | Path) -> int:
        """Return file size in bytes."""
        return Path(path).stat().st_size

    @staticmethod
    def size_human(path: str | Path) -> str:
        """Return a human-readable file size (e.g. ``"1.4 MB"``)."""
        n = Path(path).stat().st_size
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024  # type: ignore[assignment]
        return f"{n:.1f} PB"

    @staticmethod
    def mime_type(path: str | Path) -> Optional[str]:
        """Return the MIME type guessed from the file extension, or ``None``."""
        mime, _ = mimetypes.guess_type(str(path))
        return mime

    @staticmethod
    def last_modified(path: str | Path) -> datetime:
        """Return the last-modified time as a ``datetime`` (local timezone)."""
        return datetime.fromtimestamp(Path(path).stat().st_mtime)

    @staticmethod
    def created_at(path: str | Path) -> datetime:
        """
        Return the creation time as a ``datetime``.

        On Linux this is the *metadata-change* time (``st_ctime``), which is
        the closest available equivalent.
        """
        st = Path(path).stat()
        ts = getattr(st, "st_birthtime", st.st_ctime)
        return datetime.fromtimestamp(ts)

    @staticmethod
    def hash(path: str | Path, algorithm: str = "sha256") -> str:
        """
        Return the hex digest of *path* computed with *algorithm*.

        Reads in 64 KB chunks to handle large files without loading them fully.
        """
        h = hashlib.new(algorithm)
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    @staticmethod
    def chmod(path: str | Path, mode: int) -> None:
        """
        Change file permissions.

        Example::

            Files.chmod("script.sh", 0o755)   # rwxr-xr-x
        """
        Path(path).chmod(mode)

    @staticmethod
    def is_executable(path: str | Path) -> bool:
        """Return ``True`` if the file is executable by the current user."""
        return os.access(str(path), os.X_OK)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    @staticmethod
    def find(pattern: str, directory: str | Path = ".") -> Iterator[Path]:
        """Yield all files matching *pattern* (glob) under *directory*."""
        yield from (p for p in Path(directory).rglob(pattern) if p.is_file())

    @staticmethod
    def grep(
        path: str | Path,
        substring: str,
        *,
        case_sensitive: bool = True,
        encoding: str = "utf-8",
    ) -> List[tuple[int, str]]:
        """
        Search for *substring* in a text file.

        Returns a list of ``(line_number, line)`` tuples (1-indexed).
        """
        needle = substring if case_sensitive else substring.lower()
        results = []
        with open(path, "r", encoding=encoding) as fh:
            for i, raw in enumerate(fh, start=1):
                line = raw.rstrip("\r\n")
                haystack = line if case_sensitive else line.lower()
                if needle in haystack:
                    results.append((i, line))
        return results

    # ------------------------------------------------------------------
    # Archive helpers
    # ------------------------------------------------------------------

    @staticmethod
    def zip(
        source: str | Path,
        destination: Optional[str | Path] = None,
    ) -> Path:
        """
        Zip a single file or an entire directory tree.

        If *destination* is omitted the archive is placed next to *source*
        with a ``.zip`` extension.
        """
        src = Path(source)
        dst = Path(destination) if destination else src.with_suffix(".zip")
        shutil.make_archive(
            str(dst.with_suffix("")),
            "zip",
            root_dir=str(src.parent) if src.is_file() else str(src),
            base_dir=src.name if src.is_file() else ".",
        )
        return dst

    @staticmethod
    def unzip(archive: str | Path, destination: Optional[str | Path] = None) -> Path:
        """
        Extract a zip archive.

        If *destination* is omitted the contents are extracted next to the
        archive in a folder with the same stem.
        """
        arc = Path(archive)
        dst = Path(destination) if destination else arc.parent / arc.stem
        shutil.unpack_archive(str(arc), str(dst), "zip")
        return dst

    # ------------------------------------------------------------------
    # Context managers
    # ------------------------------------------------------------------

    @staticmethod
    @contextmanager
    def temp(
        suffix: str = "",
        prefix: str = "nestify_",
        encoding: str = "utf-8",
    ) -> Generator[Path, None, None]:
        """
        Context manager that yields a temporary file path and deletes it on exit.

        Example::

            with Files.temp(suffix=".json") as tmp:
                Files.write_json(tmp, {"key": "value"})
                data = Files.read_json(tmp)
        """
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)
        tmp = Path(path)
        try:
            yield tmp
        finally:
            tmp.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # OS integration
    # ------------------------------------------------------------------

    @staticmethod
    def open_default(path: str | Path) -> None:
        """
        Open *path* with the default OS application (Finder / Explorer / xdg-open).
        """
        import subprocess, sys  # noqa: PLC0415
        p = str(Path(path).resolve())
        if sys.platform == "win32":
            os.startfile(p)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", p], check=True)
        else:
            subprocess.run(["xdg-open", p], check=True)


__all__ = ["Files"]
