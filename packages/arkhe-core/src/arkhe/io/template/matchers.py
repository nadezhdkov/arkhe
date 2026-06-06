"""
arkhe.io.template.matchers — Match expression evaluator.

Syntax:
    {rank -> ADMIN:'👑 Admin', MOD:'🛡 Moderator', *:'👤 User'}

Rules:
  - Keys are bare identifiers or quoted strings.
  - Values are single-quoted strings.
  - `*` is the catch-all / default branch.
  - Matching is case-sensitive string comparison.
  - If no branch matches and no `*` exists, returns empty string.
"""

import re
from typing import Any, Dict, Optional, Tuple


# ──────────────────────────────────────────────────────
# Parser
# ──────────────────────────────────────────────────────

_BRANCH_RE = re.compile(
    r"""
    (?P<key>  \*  |  '[^']*'  |  [^,:']+? )   # key: * | 'str' | bare
    \s* : \s*
    (?P<val>  '[^']*'  |  [^,]+? )             # value: 'str' | bare
    \s* (?:,|$)
    """,
    re.VERBOSE,
)


def parse_match(spec: str) -> Dict[Optional[str], str]:
    """
    Parse a match spec string into a dict of key → value.
    The wildcard key is stored as None.

    Example input:
        "ADMIN:'👑 Admin', MOD:'🛡 Moderator', *:'👤 User'"
    """
    branches: Dict[Optional[str], str] = {}

    for m in _BRANCH_RE.finditer(spec):
        raw_key = m.group("key").strip()
        raw_val = m.group("val").strip()

        # Unwrap quotes from value
        if raw_val.startswith("'") and raw_val.endswith("'"):
            val = raw_val[1:-1]
        else:
            val = raw_val

        # Unwrap quotes from key
        if raw_key == "*":
            key = None          # wildcard
        elif raw_key.startswith("'") and raw_key.endswith("'"):
            key = raw_key[1:-1]
        else:
            key = raw_key

        branches[key] = val

    return branches


def evaluate_match(value: Any, spec: str) -> str:
    """
    Evaluate a match expression against a resolved value.

    value  — the resolved context attribute (e.g. player.rank)
    spec   — the raw match spec string after the `->`

    Returns the matched branch value, or "" if nothing matches.
    """
    branches = parse_match(spec)
    str_val  = str(value) if value is not None else ""

    # Exact key match first
    if str_val in branches:
        return branches[str_val]

    # Wildcard fallback
    if None in branches:
        return branches[None]

    return ""
