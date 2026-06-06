"""
arkhe.io.watch — Real-time object watcher.

Observes an object's attributes and refreshes the panel
whenever values change, until the user presses Ctrl-C.

Usage:
    watch(player)               # auto-refresh every 0.5s
    watch(player, interval=1.0) # custom refresh rate
    watch(player, times=10)     # run exactly N cycles
"""

import os
import sys
import time
from typing import Any, Optional

from .renderer import Panel, colorize_value, _terminal_width
from .theme import get_colors


def _render_watch_panel(obj: Any, title: str, width: int) -> str:
    c = get_colors()
    rst = c["reset"]

    attrs = {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    max_k = max((len(k) for k in attrs), default=4) if attrs else 4

    lines = []
    for k, v in attrs.items():
        lines.append(
            f"{c['key']}{k.ljust(max_k)}{rst}  {c['dim']}={rst}  {colorize_value(v)}"
        )

    return Panel(lines, title=title, width=width, padding=1).render()


def watch(
    obj: Any,
    interval: float = 0.5,
    times: Optional[int] = None,
) -> None:
    """
    Watch an object's attributes in real-time.

    The panel redraws in-place whenever a value changes.
    Press Ctrl-C to stop watching.
    """
    cls_name = type(obj).__name__
    width = min(_terminal_width(), 70)

    # Count lines the panel occupies so we can clear it
    previous_rendered = ""
    cycle = 0

    try:
        while True:
            rendered = _render_watch_panel(obj, cls_name, width)

            if rendered != previous_rendered:
                if previous_rendered:
                    # Move cursor up by the number of lines in previous render
                    n_lines = previous_rendered.count("\n") + 1
                    sys.stdout.write(f"\033[{n_lines}A\033[J")
                sys.stdout.write(rendered + "\n")
                sys.stdout.flush()
                previous_rendered = rendered

            cycle += 1
            if times is not None and cycle >= times:
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        # Leave the panel visible, print a newline
        c = get_colors()
        sys.stdout.write(f"\n{c['dim']}(watch stopped){c['reset']}\n")
        sys.stdout.flush()
