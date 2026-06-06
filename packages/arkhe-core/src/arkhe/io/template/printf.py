"""
arkhe.io.printf — ATEL-powered formatted print.

printf() renders an ATEL template string against a context
object and optional positional arguments, then prints the
result through Arkhe's output pipeline.

Usage:
    printf("{name:title} has {coins:number} coins.", player)
    printf("Hello {}!", "World")
    printf("{1} {0}", "World", "Hello")
    printf("{online?🟢 Online:🔴 Offline}", player)
    printf("{rank -> ADMIN:'👑 Admin', *:'👤 User'}", player)

Multi-line templates are dedented automatically.
"""

import sys
import textwrap
from typing import Any

from .engine import render


def printf(template: str, context: Any = None, *args: Any, **kwargs) -> None:
    """
    Render an ATEL template and print the result.

    Args:
        template : ATEL template string.
        context  : Primary context object (attribute source).
        *args    : Additional positional values for {} / {N} placeholders.
        **kwargs : Passed through to the underlying print call
                   (file=, end=, flush=).
    """
    file  = kwargs.get("file",  sys.stdout)
    end   = kwargs.get("end",   "\n")
    flush = kwargs.get("flush", False)

    # Dedent multi-line templates so indented triple-quoted strings look correct
    dedented = textwrap.dedent(template)

    # Strip a single leading newline (common with triple-quote style)
    if dedented.startswith("\n"):
        dedented = dedented[1:]

    rendered = render(dedented, context, *args)

    # Use the real builtin print to avoid double-rendering by Arkhe's hook
    try:
        from .core import _original_print
        _original_print(rendered, end=end, file=file, flush=flush)
    except ImportError:
        print(rendered, end=end, file=file, flush=flush)
