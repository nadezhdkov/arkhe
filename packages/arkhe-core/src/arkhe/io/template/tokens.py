"""
arkhe.io.template.tokens — Built-in system tokens.

These tokens resolve to runtime-generated values
and are available in any ATEL template without
needing to pass an explicit context object.

Reserved for future releases (not yet resolved):
    env, cwd, project, git.branch, git.commit,
    process.id, thread.id
"""

import datetime
import os
import platform
import sys
import socket
import uuid as _uuid_mod

# ──────────────────────────────────────────────────────
# Token registry
# Names here are matched before attribute resolution.
# ──────────────────────────────────────────────────────

def _resolve_system_token(name: str):
    """
    Return the value for a known system token, or
    raise KeyError if the name is not a system token.
    """
    now = datetime.datetime.now()

    _tokens = {
        "date":     now.strftime("%Y-%m-%d"),
        "time":     now.strftime("%H:%M:%S"),
        "now":      now.strftime("%Y-%m-%d %H:%M:%S"),
        "uuid":     str(_uuid_mod.uuid4()),
        "hostname": socket.gethostname(),
        "user":     os.getenv("USER") or os.getenv("USERNAME") or "unknown",
        "os":       platform.system(),
        "python":   f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }

    if name in _tokens:
        return _tokens[name]
    raise KeyError(name)


# Future-reserved token names — recognized but not yet resolved.
_FUTURE_TOKENS = frozenset({
    "env", "cwd", "project",
    "git.branch", "git.commit",
    "process.id", "thread.id",
})


def is_system_token(name: str) -> bool:
    """True if the name is a known system token."""
    try:
        _resolve_system_token(name)
        return True
    except KeyError:
        return False


def resolve_system_token(name: str):
    """Resolve a system token. Raises KeyError if not found."""
    return _resolve_system_token(name)
