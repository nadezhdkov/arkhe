"""
arkhe.io.core — install() / uninstall() hooks.

Intercepts builtins.print, builtins.input, and sys.excepthook
to render Arkhe-styled output.

Nothing is changed until install() is explicitly called.
"""

import builtins
import datetime
import inspect
import re
import sys
import traceback
from typing import Any

from .helpers import _ArkheMessage
from .renderer import (
    Panel,
    colorize_json,
    colorize_value,
    format_log,
    log_separator,
    section_line,
    _parse_color_tags,
    _terminal_width,
    _visible_len,
    _strip_ansi,
)
from .theme import get_colors

# ──────────────────────────────────────────────────────
# State
# ──────────────────────────────────────────────────────

_original_print = builtins.print
_original_input = builtins.input
_original_excepthook = sys.excepthook
_installed = False

# ──────────────────────────────────────────────────────
# Timestamp helper
# ──────────────────────────────────────────────────────

def _now() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


# ──────────────────────────────────────────────────────
# Object detection
# ──────────────────────────────────────────────────────

def _is_user_object(obj: Any) -> bool:
    """True for non-primitive, non-stdlib objects that have __dict__."""
    if isinstance(obj, (str, int, float, bool, bytes, type(None))):
        return False
    if isinstance(obj, (list, tuple, set, frozenset, dict)):
        return False
    if isinstance(obj, type):
        return False
    return hasattr(obj, "__dict__")


# ──────────────────────────────────────────────────────
# Renderers for each value type
# ──────────────────────────────────────────────────────

def _render_arkhe_message(msg: _ArkheMessage) -> str:
    c = get_colors()
    icons = {
        "success": ("✓ Success",  c["success"]),
        "warning": ("⚠ Warning",  c["warning"]),
        "error":   ("✖ Error",    c["error"]),
        "info":    ("✦ Info",     c["info"]),
    }
    label, color = icons.get(msg.level, icons["info"])
    lines = [msg.message]
    return Panel(
        lines,
        title=label,
        title_color=color,
        border_color=color,
    ).render()


def _render_object(obj: Any) -> str:
    c = get_colors()
    cls_name = type(obj).__name__
    attrs = {
        k: v for k, v in vars(obj).items()
        if not k.startswith("_")
    }
    rst = c["reset"]
    lines = []
    max_key = max((len(k) for k in attrs), default=4)
    for k, v in attrs.items():
        padded = k.ljust(max_key)
        lines.append(f"{c['key']}{padded}{rst} = {colorize_value(v)}")
    return Panel(lines, title=cls_name).render()


def _render_dict(obj: dict, title: str = "Dictionary") -> str:
    lines = colorize_json(obj)
    return Panel(lines, title=title).render()


def _render_list(obj: list) -> str:
    lines = colorize_json(obj)
    return Panel(lines, title="List").render()


def _render_inline(value: Any) -> str:
    """Plain inline log for primitive values."""
    text = str(value)
    return format_log(_parse_color_tags(text), level="info", timestamp=_now())


# ──────────────────────────────────────────────────────
# Custom print
# ──────────────────────────────────────────────────────

def _arkhe_print(*args, sep=" ", end="\n", file=None, flush=False):
    out = file or sys.stdout

    if len(args) == 1:
        value = args[0]

        if isinstance(value, _ArkheMessage):
            _original_print(_render_arkhe_message(value), file=out, flush=flush)
            return

        if isinstance(value, dict):
            _original_print(_render_dict(value), file=out, flush=flush)
            return

        if isinstance(value, list):
            _original_print(_render_list(value), file=out, flush=flush)
            return

        if _is_user_object(value):
            _original_print(_render_object(value), file=out, flush=flush)
            return

    # Fallback: inline log
    text = sep.join(str(a) for a in args)
    _original_print(_render_inline(text), end=end, file=out, flush=flush)


# ──────────────────────────────────────────────────────
# Custom input
# ──────────────────────────────────────────────────────

def _arkhe_input(prompt: str = "") -> str:
    c = get_colors()
    rst = c["reset"]
    styled = f"{c['info']}❯{rst} {_parse_color_tags(prompt)}"
    return _original_input(styled)


# ──────────────────────────────────────────────────────
# Traceback beautifier
# ──────────────────────────────────────────────────────

def _render_traceback(exc_type, exc_value, exc_tb) -> str:
    c = get_colors()
    rst = c["reset"]
    width = min(_terminal_width(), 72)
    bc = c["error"]

    # ── Header panel ────────────────────────────────
    exc_name = exc_type.__name__
    message  = str(exc_value)

    header_panel = Panel(
        [message],
        title=f"✖ {exc_name}",
        title_color=c["error"],
        border_color=c["error"],
        width=width,
    )

    output_parts = [header_panel.render()]

    # ── Stack frames ────────────────────────────────
    frames = traceback.extract_tb(exc_tb)

    for frame in frames:
        filename  = frame.filename
        lineno    = frame.lineno
        func      = frame.name
        line_text = (frame.line or "").strip()

        loc_label = f"{filename}:{lineno}  in {c['dim']}{func}{rst}"

        # Try to get surrounding context lines
        context_lines = _get_context(filename, lineno, context=3)

        frame_lines = []
        frame_lines.append(
            f"{c['dim']}📁{rst} {c['text']}{loc_label}"
        )
        frame_lines.append("")

        if context_lines:
            for ln, txt, is_error in context_lines:
                lno_str = f"{ln:4d}"
                if is_error:
                    arrow = f"{c['arrow']}❯{rst}"
                    frame_lines.append(
                        f" {arrow} {c['lineno']}{lno_str}{rst} {c['border']}│{rst} "
                        f"{c['highlight']}{txt}{rst}"
                    )
                else:
                    frame_lines.append(
                        f"    {c['lineno']}{lno_str}{rst} {c['border']}│{rst} "
                        f"{c['dim']}{txt}{rst}"
                    )
        else:
            frame_lines.append(
                f"    {c['lineno']}???{rst} {c['border']}│{rst} {line_text}"
            )

        # Local variables from innermost frame only
        if frame is frames[-1] and exc_tb is not None:
            local_vars = _get_locals(exc_tb)
            if local_vars:
                frame_lines.append("")
                frame_lines.append(f"{c['dim']}↳ Local variables{rst}")
                for k, v in local_vars.items():
                    frame_lines.append(
                        f"   {c['key']}{k}{rst} = {colorize_value(v)}"
                    )

        output_parts.append(
            Panel(
                frame_lines,
                title="Stack Frame",
                title_color=c["dim"],
                border_color=c["dim"],
                width=width,
                padding=0,
            ).render()
        )

    return "\n".join(output_parts)


def _get_context(filename: str, lineno: int, context: int = 3):
    """Return list of (lineno, text, is_error) around the target line."""
    try:
        with open(filename, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        start = max(0, lineno - context - 1)
        end   = min(len(all_lines), lineno + context)
        result = []
        for i in range(start, end):
            ln = i + 1
            txt = all_lines[i].rstrip()
            result.append((ln, txt, ln == lineno))
        return result
    except Exception:
        return []


def _get_locals(tb):
    """Walk to the innermost frame and return local variables."""
    while tb.tb_next:
        tb = tb.tb_next
    frame = tb.tb_frame
    return {
        k: v for k, v in frame.f_locals.items()
        if not k.startswith("__") and not callable(v)
    }


def _arkhe_excepthook(exc_type, exc_value, exc_tb):
    if exc_type is KeyboardInterrupt:
        _original_excepthook(exc_type, exc_value, exc_tb)
        return
    rendered = _render_traceback(exc_type, exc_value, exc_tb)
    _original_print(rendered, file=sys.stderr)


# ──────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────

def install():
    """
    Install Arkhe I/O hooks.

    Intercepts:
    - builtins.print
    - builtins.input
    - sys.excepthook (tracebacks)
    """
    global _installed
    if _installed:
        return

    builtins.print    = _arkhe_print
    builtins.input    = _arkhe_input
    sys.excepthook    = _arkhe_excepthook
    _installed        = True


def uninstall():
    """Restore Python's original print, input, and excepthook."""
    global _installed
    if not _installed:
        return

    builtins.print = _original_print
    builtins.input = _original_input
    sys.excepthook = _original_excepthook
    _installed     = False
