"""
nestifypy.console
--------------
Modern terminal tools: colored printing, tables, progress bars, input helpers.
"""

from __future__ import annotations

import sys
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence


# ─────────────────────────────────────────────
#  ANSI Colors
# ─────────────────────────────────────────────

_COLORS: Dict[str, str] = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "black":   "\033[30m",
    "red":     "\033[31m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "blue":    "\033[34m",
    "magenta": "\033[35m",
    "cyan":    "\033[36m",
    "white":   "\033[37m",
    "gray":    "\033[90m",
}


def _colorize(text: str, color: Optional[str], bold: bool = False) -> str:
    if color and color in _COLORS:
        prefix = _COLORS["bold"] if bold else ""
        return f"{prefix}{_COLORS[color]}{text}{_COLORS['reset']}"
    return text


# ─────────────────────────────────────────────
#  Console
# ─────────────────────────────────────────────

class Console:
    """Rich terminal output utilities."""

    # ── Print ──────────────────────────────────

    @staticmethod
    def print(
        *args: Any,
        color: Optional[str] = None,
        bold: bool = False,
        sep: str = " ",
        end: str = "\n",
    ) -> None:
        """Print with optional color and bold."""
        message = sep.join(str(a) for a in args)
        print(_colorize(message, color, bold), end=end)

    @staticmethod
    def success(*args: Any) -> None:
        Console.print("✓", *args, color="green", bold=True)

    @staticmethod
    def error(*args: Any) -> None:
        Console.print("✗", *args, color="red", bold=True)

    @staticmethod
    def warn(*args: Any) -> None:
        Console.print("⚠", *args, color="yellow")

    @staticmethod
    def info(*args: Any) -> None:
        Console.print("•", *args, color="cyan")

    @staticmethod
    def dim(*args: Any) -> None:
        Console.print(*args, color="gray")

    # ── Separator ─────────────────────────────

    @staticmethod
    def rule(char: str = "─", width: int = 60, color: str = "gray") -> None:
        """Print a horizontal separator line."""
        Console.print(char * width, color=color)

    @staticmethod
    def blank() -> None:
        print()

    # ── Table ─────────────────────────────────

    @staticmethod
    def table(
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        title: Optional[str] = None,
    ) -> None:
        """
        Print a formatted table.

        Example:
            Console.table([
                {"name": "Alice", "age": 30},
                {"name": "Bob",   "age": 25},
            ])
        """
        if not data:
            Console.warn("(empty table)")
            return

        cols = columns or list(data[0].keys())

        # Calculate column widths
        widths = {col: len(col) for col in cols}
        for row in data:
            for col in cols:
                val = str(row.get(col, ""))
                widths[col] = max(widths[col], len(val))

        # Build header
        sep_parts = [("─" * (widths[col] + 2)) for col in cols]
        sep = "┼".join(sep_parts)
        header_parts = [col.center(widths[col] + 2) for col in cols]
        header = "│".join(header_parts)

        top = "┬".join(["─" * (widths[col] + 2) for col in cols])
        bot = "┴".join(["─" * (widths[col] + 2) for col in cols])

        if title:
            Console.print(f"  {title}", color="cyan", bold=True)

        print(f"┌{top}┐")
        print(f"│{_colorize(header, 'white', bold=True)}│")
        print(f"├{sep}┤")

        for row in data:
            row_parts = [
                f" {str(row.get(col, '')).ljust(widths[col])} "
                for col in cols
            ]
            print("│" + "│".join(row_parts) + "│")

        print(f"└{bot}┘")

    # ── Progress Bar ──────────────────────────

    @staticmethod
    def progress(
        iterable: Optional[Iterable] = None,
        total: Optional[int] = None,
        label: str = "Processing",
        width: int = 40,
        color: str = "cyan",
    ) -> "ProgressBar":
        """
        Create a progress bar.

        Usage as context manager:
            with Console.progress(total=100, label="Loading") as bar:
                for i in range(100):
                    bar.update(1)

        Usage as iterator:
            for item in Console.progress(my_list, label="Items"):
                process(item)
        """
        return ProgressBar(
            iterable=iterable,
            total=total,
            label=label,
            width=width,
            color=color,
        )

    # ── Input ─────────────────────────────────

    @staticmethod
    def ask(prompt: str, default: Optional[str] = None) -> str:
        """Prompt the user for input."""
        suffix = f" [{default}]" if default else ""
        raw = input(_colorize(f"? {prompt}{suffix}: ", "cyan"))
        return raw.strip() or (default or "")

    @staticmethod
    def confirm(prompt: str, default: bool = False) -> bool:
        """Ask a yes/no question."""
        hint = "[Y/n]" if default else "[y/N]"
        raw = input(_colorize(f"? {prompt} {hint}: ", "cyan")).strip().lower()
        if not raw:
            return default
        return raw in {"y", "yes"}

    @staticmethod
    def choose(prompt: str, choices: List[str]) -> str:
        """Ask the user to choose from a list."""
        Console.print(f"? {prompt}", color="cyan", bold=True)
        for i, choice in enumerate(choices, 1):
            Console.print(f"  {i}. {choice}", color="white")
        while True:
            raw = input(_colorize("  → ", "gray")).strip()
            try:
                index = int(raw) - 1
                if 0 <= index < len(choices):
                    return choices[index]
            except ValueError:
                if raw in choices:
                    return raw
            Console.error("Invalid choice. Try again.")

    # ── Spinner ───────────────────────────────

    @staticmethod
    def spinner(message: str = "Loading") -> "Spinner":
        """Return a Spinner context manager."""
        return Spinner(message)


# ─────────────────────────────────────────────
#  ProgressBar
# ─────────────────────────────────────────────

class ProgressBar:

    def __init__(
        self,
        iterable: Optional[Iterable],
        total: Optional[int],
        label: str,
        width: int,
        color: str,
    ) -> None:
        self._iterable = iterable
        self._total = total or (len(iterable) if hasattr(iterable, "__len__") else 100)  # type: ignore
        self._current = 0
        self._label = label
        self._width = width
        self._color = color
        self._start = time.monotonic()

    def update(self, n: int = 1) -> None:
        self._current = min(self._current + n, self._total)
        self._render()

    def _render(self) -> None:
        pct = self._current / max(self._total, 1)
        filled = int(self._width * pct)
        bar = "█" * filled + "░" * (self._width - filled)
        elapsed = time.monotonic() - self._start
        label_str = _colorize(self._label, self._color)
        pct_str = _colorize(f"{pct * 100:5.1f}%", "white", bold=True)
        elapsed_str = _colorize(f"{elapsed:.1f}s", "gray")
        sys.stdout.write(
            f"\r{label_str} [{bar}] {pct_str} {elapsed_str}"
        )
        sys.stdout.flush()
        if self._current >= self._total:
            print()

    def __enter__(self) -> "ProgressBar":
        return self

    def __exit__(self, *args: Any) -> None:
        if self._current < self._total:
            self._current = self._total
            self._render()

    def __iter__(self) -> "ProgressBar":
        return self

    def __next__(self) -> Any:
        if self._iterable is None:
            raise StopIteration
        try:
            val = next(self._iter)  # type: ignore
            self.update(1)
            return val
        except StopIteration:
            raise

    def __enter_iter__(self) -> "ProgressBar":
        if self._iterable is not None:
            self._iter = iter(self._iterable)
        return self


# ─────────────────────────────────────────────
#  Spinner
# ─────────────────────────────────────────────

class Spinner:

    _FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str) -> None:
        self._message = message
        self._running = False
        self._thread = None

    def __enter__(self) -> "Spinner":
        import threading
        self._running = True

        def _spin() -> None:
            i = 0
            while self._running:
                frame = self._FRAMES[i % len(self._FRAMES)]
                sys.stdout.write(
                    f"\r{_colorize(frame, 'cyan')} {self._message}"
                )
                sys.stdout.flush()
                time.sleep(0.08)
                i += 1

        self._thread = threading.Thread(target=_spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self._running = False
        if self._thread:
            self._thread.join()
        sys.stdout.write(f"\r{_colorize('✓', 'green')} {self._message}\n")
        sys.stdout.flush()


__all__ = ["Console", "ProgressBar", "Spinner"]
