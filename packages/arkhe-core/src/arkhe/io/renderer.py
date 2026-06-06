"""
arkhe.io.renderer — Core layout engine.

Provides the building blocks for all Arkhe visual layouts:
Panel, Log, Table, Tree, and more.

Box-drawing vocabulary:
    ╭ ╮ ╰ ╯ │ ─ ├ ┤
"""

import os
import re
import shutil
from typing import List, Optional, Sequence

from .theme import get_colors

# ──────────────────────────────────────────────────────
# Terminal helpers
# ──────────────────────────────────────────────────────

def _terminal_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes to measure visible length."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _visible_len(text: str) -> int:
    return len(_strip_ansi(text))


def _parse_color_tags(text: str) -> str:
    """
    Translate lightweight color tags to ANSI.
    Supports: {red} {green} {yellow} {blue} {cyan} {magenta} {white} {gray} {/}
    """
    c = get_colors()
    tag_map = {
        "red":     "\033[91m",
        "green":   "\033[92m",
        "yellow":  "\033[93m",
        "blue":    "\033[94m",
        "magenta": "\033[95m",
        "cyan":    "\033[96m",
        "white":   "\033[97m",
        "gray":    "\033[38;5;244m",
        "bold":    "\033[1m",
        "dim":     c["dim"],
        "/":       c["reset"],
    }
    def replace(m):
        key = m.group(1)
        return tag_map.get(key, m.group(0))
    return re.sub(r"\{(\w+|/)\}", replace, text)


# ──────────────────────────────────────────────────────
# Panel layout
# ──────────────────────────────────────────────────────

class Panel:
    """
    Renders a rounded box with an optional title.

    ╭─[ Title ]──────────────────────╮
    │                                │
    │  content here                  │
    │                                │
    ╰────────────────────────────────╯
    """

    def __init__(
        self,
        lines: List[str],
        title: str = "",
        title_color: Optional[str] = None,
        border_color: Optional[str] = None,
        width: Optional[int] = None,
        padding: int = 1,
    ):
        self.lines = lines
        self.title = title
        self.title_color = title_color
        self.border_color = border_color
        self.width = width or min(_terminal_width(), 70)
        self.padding = padding

    def render(self) -> str:
        c = get_colors()
        bc = self.border_color or c["border"]
        tc = self.title_color or c["title"]
        rst = c["reset"]

        inner = self.width - 2  # subtract border chars

        # Build title segment
        if self.title:
            raw_title = f" {self.title} "
            title_seg = f"{bc}─[{rst}{tc}{raw_title}{rst}{bc}]"
            title_len = 4 + len(raw_title)  # ─[ + title + ]
        else:
            title_seg = ""
            title_len = 0

        fill = inner - title_len
        top    = f"{bc}╭{title_seg}{'─' * fill}╮{rst}"
        bottom = f"{bc}╰{'─' * inner}╯{rst}"
        pad    = f"{bc}│{rst}{' ' * inner}{bc}│{rst}"

        body_lines = []
        if self.padding:
            body_lines.append(pad)

        for line in self.lines:
            parsed = _parse_color_tags(line)
            visible = _visible_len(parsed)
            space = max(0, inner - 2 - visible)  # 1-char indent each side
            body_lines.append(
                f"{bc}│{rst} {parsed}{' ' * space} {bc}│{rst}"
            )

        if self.padding:
            body_lines.append(pad)

        return "\n".join([top, *body_lines, bottom])


# ──────────────────────────────────────────────────────
# Section divider inside a panel
# ──────────────────────────────────────────────────────

def section_line(title: str, width: int) -> str:
    c = get_colors()
    bc = c["border"]
    tc = c["title"]
    rst = c["reset"]
    inner = width - 2
    raw = f" {title}"
    fill = max(0, inner - len(raw) - 1)
    return f"{bc}├{tc}{raw}{bc}{'─' * fill}┤{rst}"


def section_divider(width: int) -> str:
    c = get_colors()
    bc = c["border"]
    rst = c["reset"]
    return f"{bc}├{'─' * (width - 2)}┤{rst}"


# ──────────────────────────────────────────────────────
# Inline log layout
# ──────────────────────────────────────────────────────

_LOG_LEVELS = {
    "info":    ("✦ INFO   ", "info"),
    "warning": ("⚠ WARNING", "warning"),
    "error":   ("✖ ERROR  ", "error"),
    "success": ("✓ SUCCESS", "success"),
    "debug":   ("⚙ DEBUG  ", "dim"),
}


def format_log(message: str, level: str = "info", timestamp: str = "") -> str:
    """Format a single log line."""
    c = get_colors()
    rst = c["reset"]
    ts_color = c["timestamp"]
    parsed = _parse_color_tags(message)

    label, color_key = _LOG_LEVELS.get(level, _LOG_LEVELS["info"])
    lc = c[color_key]

    ts = f"{ts_color}[ {timestamp} ]{rst} " if timestamp else ""
    return f"{ts}{lc}{label}{rst}  {c['border']}│{rst} {parsed}"


def log_separator(width: Optional[int] = None) -> str:
    w = width or min(_terminal_width(), 70)
    c = get_colors()
    return f"{c['dim']}{'─' * w}{c['reset']}"


# ──────────────────────────────────────────────────────
# Value colorizer (for dicts, objects)
# ──────────────────────────────────────────────────────

def colorize_value(value) -> str:
    c = get_colors()
    rst = c["reset"]

    if isinstance(value, bool):
        return f"{c['boolean']}{'true' if value else 'false'}{rst}"
    if isinstance(value, (int, float)):
        return f"{c['number']}{value}{rst}"
    if isinstance(value, str):
        return f"{c['string']}\"{value}\"{rst}"
    if value is None:
        return f"{c['null']}null{rst}"
    return f"{c['text']}{repr(value)}{rst}"


def colorize_json(obj, indent: int = 0) -> List[str]:
    """Recursively colorize a dict/list into lines."""
    c = get_colors()
    rst = c["reset"]
    pad = "   " * indent
    lines = []

    if isinstance(obj, dict):
        lines.append(f"{pad}{c['border']}{{" + rst)
        items = list(obj.items())
        for i, (k, v) in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}   {c['key']}\"{k}\"{rst}: ")
                lines.extend(colorize_json(v, indent + 1))
                if comma:
                    lines[-1] += comma
            else:
                lines.append(
                    f"{pad}   {c['key']}\"{k}\"{rst}: {colorize_value(v)}{comma}"
                )
        lines.append(f"{pad}{c['border']}}}"+rst)
    elif isinstance(obj, list):
        lines.append(f"{pad}{c['border']}["+rst)
        for i, v in enumerate(obj):
            comma = "," if i < len(obj) - 1 else ""
            if isinstance(v, (dict, list)):
                lines.extend(colorize_json(v, indent + 1))
                if comma:
                    lines[-1] += comma
            else:
                lines.append(f"{pad}   {colorize_value(v)}{comma}")
        lines.append(f"{pad}{c['border']}]"+rst)
    else:
        lines.append(f"{pad}{colorize_value(obj)}")

    return lines
