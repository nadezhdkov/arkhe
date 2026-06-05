from typing import Optional

_current_context = None


def set_context(ctx) -> None:
    global _current_context
    _current_context = ctx


def get_context():
    return _current_context
