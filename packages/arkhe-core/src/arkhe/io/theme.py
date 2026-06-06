"""
arkhe.io.theme — Built-in themes for Arkhe I/O.
"""

from typing import Dict

_THEMES: Dict[str, Dict[str, str]] = {
    "default": {
        "border":      "\033[38;5;240m",   # gray
        "title":       "\033[97m",          # bright white
        "text":        "\033[37m",          # white
        "timestamp":   "\033[38;5;244m",   # mid-gray
        "info":        "\033[36m",          # cyan
        "warning":     "\033[33m",          # yellow
        "error":       "\033[91m",          # bright red
        "success":     "\033[92m",          # bright green
        "key":         "\033[36m",          # cyan
        "string":      "\033[32m",          # green
        "number":      "\033[33m",          # yellow
        "boolean":     "\033[35m",          # magenta
        "null":        "\033[38;5;244m",   # gray
        "dim":         "\033[38;5;240m",   # dim gray
        "highlight":   "\033[38;5;203m",   # soft red highlight
        "lineno":      "\033[38;5;244m",   # gray line numbers
        "arrow":       "\033[91m",          # red arrow
        "reset":       "\033[0m",
    },
    "dracula": {
        "border":      "\033[38;5;61m",
        "title":       "\033[97m",
        "text":        "\033[38;5;253m",
        "timestamp":   "\033[38;5;244m",
        "info":        "\033[38;5;141m",   # purple
        "warning":     "\033[38;5;228m",   # yellow
        "error":       "\033[38;5;203m",   # red
        "success":     "\033[38;5;84m",    # green
        "key":         "\033[38;5;141m",
        "string":      "\033[38;5;84m",
        "number":      "\033[38;5;228m",
        "boolean":     "\033[38;5;212m",   # pink
        "null":        "\033[38;5;244m",
        "dim":         "\033[38;5;61m",
        "highlight":   "\033[38;5;203m",
        "lineno":      "\033[38;5;244m",
        "arrow":       "\033[38;5;203m",
        "reset":       "\033[0m",
    },
    "nord": {
        "border":      "\033[38;5;67m",
        "title":       "\033[38;5;153m",
        "text":        "\033[38;5;188m",
        "timestamp":   "\033[38;5;109m",
        "info":        "\033[38;5;110m",
        "warning":     "\033[38;5;179m",
        "error":       "\033[38;5;167m",
        "success":     "\033[38;5;108m",
        "key":         "\033[38;5;110m",
        "string":      "\033[38;5;108m",
        "number":      "\033[38;5;179m",
        "boolean":     "\033[38;5;139m",
        "null":        "\033[38;5;109m",
        "dim":         "\033[38;5;67m",
        "highlight":   "\033[38;5;167m",
        "lineno":      "\033[38;5;109m",
        "arrow":       "\033[38;5;167m",
        "reset":       "\033[0m",
    },
    "catppuccin": {
        "border":      "\033[38;5;105m",
        "title":       "\033[38;5;183m",
        "text":        "\033[38;5;189m",
        "timestamp":   "\033[38;5;147m",
        "info":        "\033[38;5;111m",
        "warning":     "\033[38;5;221m",
        "error":       "\033[38;5;210m",
        "success":     "\033[38;5;114m",
        "key":         "\033[38;5;111m",
        "string":      "\033[38;5;114m",
        "number":      "\033[38;5;221m",
        "boolean":     "\033[38;5;183m",
        "null":        "\033[38;5;147m",
        "dim":         "\033[38;5;105m",
        "highlight":   "\033[38;5;210m",
        "lineno":      "\033[38;5;147m",
        "arrow":       "\033[38;5;210m",
        "reset":       "\033[0m",
    },
    "gruvbox": {
        "border":      "\033[38;5;137m",
        "title":       "\033[38;5;229m",
        "text":        "\033[38;5;223m",
        "timestamp":   "\033[38;5;243m",
        "info":        "\033[38;5;108m",
        "warning":     "\033[38;5;214m",
        "error":       "\033[38;5;167m",
        "success":     "\033[38;5;142m",
        "key":         "\033[38;5;108m",
        "string":      "\033[38;5;142m",
        "number":      "\033[38;5;214m",
        "boolean":     "\033[38;5;175m",
        "null":        "\033[38;5;243m",
        "dim":         "\033[38;5;137m",
        "highlight":   "\033[38;5;167m",
        "lineno":      "\033[38;5;243m",
        "arrow":       "\033[38;5;167m",
        "reset":       "\033[0m",
    },
    "github": {
        "border":      "\033[38;5;250m",
        "title":       "\033[38;5;18m",
        "text":        "\033[38;5;235m",
        "timestamp":   "\033[38;5;244m",
        "info":        "\033[38;5;26m",
        "warning":     "\033[38;5;136m",
        "error":       "\033[38;5;160m",
        "success":     "\033[38;5;28m",
        "key":         "\033[38;5;26m",
        "string":      "\033[38;5;28m",
        "number":      "\033[38;5;136m",
        "boolean":     "\033[38;5;92m",
        "null":        "\033[38;5;244m",
        "dim":         "\033[38;5;250m",
        "highlight":   "\033[38;5;160m",
        "lineno":      "\033[38;5;244m",
        "arrow":       "\033[38;5;160m",
        "reset":       "\033[0m",
    },
}

_active_theme: str = "default"


def theme(name: str) -> None:
    """Switch the active Arkhe theme."""
    global _active_theme
    if name not in _THEMES:
        raise ValueError(
            f"Unknown theme '{name}'. Available: {', '.join(_THEMES)}"
        )
    _active_theme = name


def get_colors() -> Dict[str, str]:
    """Return the current theme's color codes."""
    return _THEMES[_active_theme]
