"""
arkhe.io.inspect — Object and class inspector.

Usage:
    from arkhe.io import inspect_obj as inspect
    inspect(MyClass)
    inspect(my_instance)
"""

import inspect as _inspect
from typing import Any

from .renderer import Panel, section_line, _terminal_width
from .theme import get_colors


def inspect(obj: Any) -> None:
    """
    Render a structured inspection panel for any object or class.

    ╭─[ ClassName ]────────────────────────────────────╮
    │                                                  │
    │  Class Definition                                │
    │                                                  │
    ├─ Attributes ─────────────────────────────────────┤
    │  name : str                                      │
    │  age  : int                                      │
    │                                                  │
    ├─ Methods ────────────────────────────────────────┤
    │  save()                                          │
    │  login()                                         │
    ╰──────────────────────────────────────────────────╯
    """
    import builtins as _builtins
    c = get_colors()
    rst = c["reset"]
    width = min(_terminal_width(), 70)
    inner = width - 2

    is_class = isinstance(obj, type)
    cls = obj if is_class else type(obj)
    cls_name = cls.__name__

    lines = []

    # ── Header ──────────────────────────────────────
    kind = "Class Definition" if is_class else "Instance"
    lines.append(f"{c['dim']}{kind}{rst}")
    lines.append("")

    # ── Docstring ────────────────────────────────────
    doc = _inspect.getdoc(cls)
    if doc:
        first_line = doc.split("\n")[0]
        lines.append(f"{c['text']}{first_line}{rst}")
        lines.append("")

    # ── Separator: Attributes ─────────────────────────
    lines.append(section_line("Attributes", width))

    hints = {}
    try:
        hints = _inspect.get_annotations(cls) if hasattr(_inspect, "get_annotations") else {}
    except Exception:
        pass

    if not hints and hasattr(cls, "__annotations__"):
        hints = cls.__annotations__

    if not is_class and hasattr(obj, "__dict__"):
        # Show live values for instances
        attrs = {k: v for k, v in vars(obj).items() if not k.startswith("_")}
        max_k = max((len(k) for k in attrs), default=1)
        for k, v in attrs.items():
            type_hint = hints.get(k, type(v).__name__)
            hint_str  = getattr(type_hint, "__name__", str(type_hint))
            lines.append(
                f" {c['key']}{k.ljust(max_k)}{rst}  {c['dim']}:{rst}  "
                f"{c['number']}{hint_str}{rst}  {c['dim']}={rst}  {c['string']}{v!r}{rst}"
            )
    elif hints:
        max_k = max((len(k) for k in hints), default=1)
        for k, t in hints.items():
            type_name = getattr(t, "__name__", str(t))
            lines.append(
                f" {c['key']}{k.ljust(max_k)}{rst}  {c['dim']}:{rst}  "
                f"{c['number']}{type_name}{rst}"
            )
    else:
        lines.append(f" {c['dim']}(no annotations found){rst}")

    lines.append("")

    # ── Separator: Methods ────────────────────────────
    lines.append(section_line("Methods", width))

    methods = [
        name for name, _ in _inspect.getmembers(cls, predicate=_inspect.isfunction)
        if not name.startswith("__")
    ]
    # Also catch classmethod/staticmethod
    methods += [
        name for name, val in vars(cls).items()
        if not name.startswith("__") and isinstance(val, (classmethod, staticmethod))
        and name not in methods
    ]

    if methods:
        for name in sorted(methods):
            try:
                sig = _inspect.signature(getattr(cls, name))
                sig_str = str(sig)
            except (ValueError, TypeError):
                sig_str = "(...)"
            lines.append(f" {c['info']}{name}{rst}{c['dim']}{sig_str}{rst}")
    else:
        lines.append(f" {c['dim']}(no public methods){rst}")

    lines.append("")

    panel = Panel(lines, title=cls_name, width=width, padding=0)
    # Use the real original print to avoid recursion if installed
    try:
        from .core import _original_print
        _original_print(panel.render())
    except ImportError:
        print(panel.render())
