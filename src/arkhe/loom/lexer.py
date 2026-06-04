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
    STRING      "hello"  or  unquoted_word
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
from typing import Iterator, Optional

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
    STRING     = auto()   # "..." or bare word
    INTEGER    = auto()   # 123
    FLOAT      = auto()   # 1.23
    BOOL       = auto()   # true / false
    NULL       = auto()   # null
    NEWLINE    = auto()   # \n (used as statement terminator)
    EOF        = auto()


@dataclass
class Token:
    type: TT
    value: object          # raw Python value (str, int, float, bool, None)
    line: int
    column: int
    raw: str = ""          # original source text

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


# ─────────────────────────────────────────────────────────────────────────────
#  Lexer
# ─────────────────────────────────────────────────────────────────────────────

# Patterns evaluated in order; first match wins.
_PATTERNS: list[tuple[str, TT | None]] = [
    (r"[ \t]+",                        None),        # horizontal whitespace — skip
    (r"#[^\n]*",                       None),        # comment — skip
    (r"\n",                            TT.NEWLINE),
    (r"\{",                            TT.LBRACE),
    (r"\}",                            TT.RBRACE),
    (r",",                             TT.COMMA),
    (r":",                             TT.COLON),
    (r"\(",                            TT.LPAREN),
    (r"\)",                            TT.RPAREN),
    (r"\[",                            TT.LBRACKET),
    (r"\]",                            TT.RBRACKET),
    # Directive: @word(.word)*[*]? — must come before bare strings
    (r"@[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\*?", TT.DIRECTIVE),
    # Quoted string
    (r'"(?:[^"\\]|\\.)*"',             TT.STRING),
    # Numeric
    (r"-?\d+\.\d+",                    TT.FLOAT),
    (r"-?\d+",                         TT.INTEGER),
    # Boolean / null / bare word — order matters: bool/null before bare STRING
    (r"(?i:true|false|yes|no|on|off)", TT.BOOL),    # spec v0.1 allows all; patch restricts to true/false
    (r"null",                          TT.NULL),
    # Bare word (unquoted alphanumeric value, e.g. driver: postgres)
    (r"[A-Za-z_][A-Za-z0-9_\-\.]*",   TT.STRING),
]

_MASTER = re.compile(
    "|".join(f"({p})" for p, _ in _PATTERNS),
    re.UNICODE,
)

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
    pos = 0
    line_num = 1
    line_start = 0
    last_type: Optional[TT] = None

    while pos < len(source):
        m = _MASTER.match(source, pos)
        if not m:
            col = pos - line_start + 1
            char = source[pos]
            raise LoomSyntaxError(
                f"Unexpected character {char!r}",
                filename=filename,
                line=line_num,
                column=col,
                source_lines=[l.rstrip("\n") for l in lines],
                got=repr(char),
                expected="a valid token",
                hint="Check for typos, stray characters, or unsupported syntax.",
            )

        raw = m.group(0)
        col = pos - line_start + 1

        # Find which pattern matched
        matched_type: Optional[TT] = None
        for i, (_, tt) in enumerate(_PATTERNS):
            if m.group(i + 1) is not None:
                matched_type = tt
                break

        pos += len(raw)

        if matched_type is None:
            # Skip (whitespace, comments)
            if "\n" in raw:
                line_num += raw.count("\n")
                line_start = pos - (len(raw) - raw.rfind("\n") - 1)
            continue

        # Track line numbers
        if matched_type == TT.NEWLINE:
            line_num += 1
            line_start = pos
            # Collapse consecutive newlines
            if last_type == TT.NEWLINE:
                continue

        # Build token value
        value: object
        if matched_type == TT.STRING:
            if raw.startswith('"'):
                # Unescape basic sequences
                value = raw[1:-1].replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")
            else:
                value = raw
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

    tokens.append(Token(type=TT.EOF, value=None, line=line_num, column=0, raw=""))
    return tokens


__all__ = ["TT", "Token", "tokenize"]
