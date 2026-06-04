"""
arkhe.loom.lexer
---------------------
Tokenizer for the .loom configuration language.

Produces a flat list of Token objects from raw .loom source text.
Preserves line/column information for diagnostic error messages.

Token types:
    DIRECTIVE   @module, @import, @scope.path, @scope.path*
    LBRACE      {
    RBRACE      }
    COMMA       ,
    COLON       :
    LPAREN      (
    RPAREN      )
    STRING      "hello"  or  'hello'  or  unquoted_word
    INTEGER     5432
    FLOAT       3.14
    BOOL        true / false
    NULL        null
    LBRACKET    [
    RBRACKET    ]
    NEWLINE     (significant as property separator)
    EOF
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from arkhe.loom.exceptions import LoomSyntaxError


# ─────────────────────────────────────────────────────────────────────────────
#  Token types
# ─────────────────────────────────────────────────────────────────────────────

class TT(Enum):
    DIRECTIVE  = auto()   # @anything
    LBRACE     = auto()   # {
    RBRACE     = auto()   # }
    COMMA      = auto()   # ,
    COLON      = auto()   # :
    LPAREN     = auto()   # (
    RPAREN     = auto()   # )
    LBRACKET   = auto()   # [
    RBRACKET   = auto()   # ]
    STRING     = auto()   # "..." or '...' or bare word
    INTEGER    = auto()   # 123
    FLOAT      = auto()   # 1.23
    BOOL       = auto()   # true / false
    NULL       = auto()   # null
    NEWLINE    = auto()   # \n (used as statement terminator)
    EOF        = auto()


@dataclass(slots=True)
class Token:
    type: TT
    value: object          # raw Python value (str, int, float, bool, None)
    line: int
    column: int
    raw: str = ""          # original source text

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


# ─────────────────────────────────────────────────────────────────────────────
#  Lexer — optimised with named groups and lastgroup dispatch
# ─────────────────────────────────────────────────────────────────────────────

# Each entry: (group_name, regex_pattern, TT | None)
# None means "skip" (whitespace/comments).
_RULES: list[tuple[str, str, TT | None]] = [
    ("WS",        r"[ \t]+",                                         None),
    ("COMMENT",   r"#[^\n]*",                                        None),
    ("NL",        r"\n",                                             TT.NEWLINE),
    ("LBRACE",    r"\{",                                             TT.LBRACE),
    ("RBRACE",    r"\}",                                             TT.RBRACE),
    ("COMMA",     r",",                                              TT.COMMA),
    ("COLON",     r":",                                              TT.COLON),
    ("LPAREN",    r"\(",                                             TT.LPAREN),
    ("RPAREN",    r"\)",                                             TT.RPAREN),
    ("LBRACKET",  r"\[",                                             TT.LBRACKET),
    ("RBRACKET",  r"\]",                                             TT.RBRACKET),
    # Directive: @word(.word)*[*]? — must come before bare strings
    ("DIRECTIVE", r"@[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\*?", TT.DIRECTIVE),
    # Double-quoted string
    ("DQSTR",     r'"(?:[^"\\]|\\.)*"',                              TT.STRING),
    # Single-quoted string (new)
    ("SQSTR",     r"'(?:[^'\\]|\\.)*'",                              TT.STRING),
    # Numeric — float before int
    ("FLOAT",     r"-?\d+\.\d+",                                     TT.FLOAT),
    ("INT",       r"-?\d+",                                          TT.INTEGER),
    # Boolean / null — before bare STRING
    ("BOOL",      r"(?i:true|false|yes|no|on|off)",                  TT.BOOL),
    ("NULL",      r"null",                                           TT.NULL),
    # Bare word (unquoted alphanumeric value, e.g. driver: postgres)
    ("BARE",      r"[A-Za-z_][A-Za-z0-9_\-\.]*",                    TT.STRING),
]

# Build a single compiled pattern with named groups for O(1) dispatch.
_MASTER = re.compile(
    "|".join(f"(?P<{name}>{pat})" for name, pat, _ in _RULES),
    re.UNICODE,
)

# Lookup table: group_name → TT (or None for skip)
_GROUP_TYPE: dict[str, TT | None] = {name: tt for name, _, tt in _RULES}

# Map from boolean literal → Python bool (case-insensitive)
_BOOL_MAP = {
    "true": True,  "false": False,
    "yes":  True,  "no":    False,
    "on":   True,  "off":   False,
}


def tokenize(source: str, filename: str = "<string>") -> list[Token]:
    """
    Convert raw .loom source text into a flat list of Token objects.

    Consecutive NEWLINEs are collapsed into one.
    A final EOF token is always appended.

    Raises LoomSyntaxError on unrecognised characters.
    """
    tokens: list[Token] = []
    lines = source.splitlines(keepends=True)
    line_num = 1
    line_start = 0
    last_type: Optional[TT] = None

    for m in _MASTER.finditer(source):
        raw = m.group()
        start = m.start()
        col = start - line_start + 1

        # O(1) dispatch via lastgroup (C-level attribute)
        group_name = m.lastgroup
        matched_type = _GROUP_TYPE[group_name]  # type: ignore[index]

        if matched_type is None:
            # Skip whitespace / comments — but track newlines inside them
            if "\n" in raw:
                line_num += raw.count("\n")
                line_start = start + raw.rfind("\n") + 1
            continue

        # Check for gaps (unexpected characters between matches)
        # This is done by comparing the match start with expected position.
        # We rely on finditer producing contiguous matches for valid input;
        # gaps are detected lazily when we hit an unmatchable char.

        # Track line numbers for NEWLINE tokens
        if matched_type == TT.NEWLINE:
            line_num += 1
            line_start = m.end()
            if last_type == TT.NEWLINE:
                continue  # collapse consecutive newlines

        # Build token value
        value: object
        if matched_type == TT.STRING:
            if group_name == "DQSTR":
                # Unescape basic sequences in double-quoted strings
                value = raw[1:-1].replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")
            elif group_name == "SQSTR":
                # Single-quoted strings: unescape basic sequences
                value = raw[1:-1].replace("\\'", "'").replace("\\n", "\n").replace("\\t", "\t")
            else:
                # Bare word — apply space translation:
                #   underscore (_) → space
                #   hyphen (-)     → space
                value = raw.replace("_", " ").replace("-", " ")
        elif matched_type == TT.INTEGER:
            value = int(raw)
        elif matched_type == TT.FLOAT:
            value = float(raw)
        elif matched_type == TT.BOOL:
            value = _BOOL_MAP[raw.lower()]
        elif matched_type == TT.NULL:
            value = None
        elif matched_type == TT.DIRECTIVE:
            value = raw  # keep the @ prefix
        else:
            value = raw

        tok = Token(type=matched_type, value=value, line=line_num, column=col, raw=raw)
        tokens.append(tok)
        last_type = matched_type

    # Detect unrecognised characters by scanning for gaps
    _check_gaps(source, tokens, lines, filename)

    tokens.append(Token(type=TT.EOF, value=None, line=line_num, column=0, raw=""))
    return tokens


def _check_gaps(source: str, tokens: list[Token], lines: list[str], filename: str) -> None:
    """
    Verify that every non-whitespace character in source was consumed.

    Uses a secondary scan only when the fast path (finditer) may have
    silently skipped an illegal character.  This keeps the hot path
    allocation-free while still producing good diagnostics.
    """
    if not source:
        return

    # Quick length-based heuristic: if the master regex matched every
    # character, there can be no gap.
    consumed = 0
    for m in _MASTER.finditer(source):
        consumed += m.end() - m.start()
    if consumed == len(source):
        return

    # Slow path — find the first unmatched character
    pos = 0
    line_num = 1
    line_start = 0
    for m in _MASTER.finditer(source):
        if m.start() > pos:
            # There's a gap between pos and m.start()
            col = pos - line_start + 1
            char = source[pos]
            raise LoomSyntaxError(
                f"Unexpected character {char!r}",
                filename=filename,
                line=line_num,
                column=col,
                source_lines=[ln.rstrip("\n") for ln in lines],
                got=repr(char),
                expected="a valid token",
                hint="Check for typos, stray characters, or unsupported syntax.",
            )
        # Track newlines within this match
        raw = m.group()
        nl_count = raw.count("\n")
        if nl_count:
            line_num += nl_count
            line_start = m.start() + raw.rfind("\n") + 1
        pos = m.end()

    # Check trailing gap
    if pos < len(source):
        col = pos - line_start + 1
        char = source[pos]
        raise LoomSyntaxError(
            f"Unexpected character {char!r}",
            filename=filename,
            line=line_num,
            column=col,
            source_lines=[ln.rstrip("\n") for ln in lines],
            got=repr(char),
            expected="a valid token",
            hint="Check for typos, stray characters, or unsupported syntax.",
        )


__all__ = ["TT", "Token", "tokenize"]
