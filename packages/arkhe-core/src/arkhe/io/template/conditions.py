"""
arkhe.io.template.conditions — Condition evaluator.

Supports:
    Boolean presence      {online?Online:Offline}
    Comparisons           {coins > 1000?Rich:Poor}
    Equality              {rank == 'ADMIN'?Admin:Player}
    Not equal             {rank != 'ADMIN'?Player:Admin}
    Greater / less        {level > 50?Veteran:Beginner}
    Compound AND          {online && vip?VIP:Offline}
    Compound OR           {admin || moderator?Staff:Player}
    NOT                   {!banned?Allowed:Blocked}
    Nested groups         {online && (vip || coins > 10000)?Premium:Normal}

Security: no eval() or exec() — conditions are parsed and
evaluated using a small recursive descent parser.
"""

import re
from typing import Any, Callable, Sequence


# ──────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────

def evaluate_condition(
    condition: str,
    context: Any,
    args: Sequence[Any] = (),
) -> bool:
    """
    Parse and evaluate an ATEL condition string.
    Returns True or False.
    """
    tokens = _tokenize(condition.strip())
    parser = _ConditionParser(tokens, context, args)
    return parser.parse()


# ──────────────────────────────────────────────────────
# Tokenizer
# ──────────────────────────────────────────────────────

_TOKEN_RE = re.compile(
    r"""
      (?P<AND>   &&              )
    | (?P<OR>    \|\|            )
    | (?P<NOT>   !(?!=)          )   # ! but not !=
    | (?P<GTE>   >=              )
    | (?P<LTE>   <=              )
    | (?P<NEQ>   !=              )
    | (?P<EQ>    ==              )
    | (?P<GT>    >               )
    | (?P<LT>    <               )
    | (?P<LPAREN>\(              )
    | (?P<RPAREN>\)              )
    | (?P<STR>   '[^']*'         )   # single-quoted string literal
    | (?P<NUM>   -?\d+(?:\.\d+)? )  # number literal
    | (?P<IDENT> [\w.]+(?:\(\))? )   # attribute path or method call
    """,
    re.VERBOSE,
)


def _tokenize(text: str):
    tokens = []
    for m in _TOKEN_RE.finditer(text):
        kind  = m.lastgroup
        value = m.group()
        tokens.append((kind, value))
    return tokens


# ──────────────────────────────────────────────────────
# Recursive descent parser
# Grammar:
#   expr    ::= or_expr
#   or_expr ::= and_expr ('||' and_expr)*
#   and_expr::= not_expr ('&&' not_expr)*
#   not_expr::= '!' not_expr | cmp_expr
#   cmp_expr::= atom (op atom)?
#   atom    ::= '(' expr ')' | IDENT | STR | NUM
# ──────────────────────────────────────────────────────

class _ConditionParser:
    def __init__(self, tokens, context, args):
        self.tokens  = tokens
        self.pos     = 0
        self.context = context
        self.args    = args

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, None)

    def consume(self, kind=None):
        tok = self.tokens[self.pos]
        if kind and tok[0] != kind:
            raise SyntaxError(f"ATEL condition: expected {kind}, got {tok}")
        self.pos += 1
        return tok

    def parse(self) -> bool:
        result = self.or_expr()
        return result

    def or_expr(self) -> bool:
        left = self.and_expr()
        while self.peek()[0] == "OR":
            self.consume("OR")
            right = self.and_expr()
            left = left or right
        return left

    def and_expr(self) -> bool:
        left = self.not_expr()
        while self.peek()[0] == "AND":
            self.consume("AND")
            right = self.not_expr()
            left = left and right
        return left

    def not_expr(self) -> bool:
        if self.peek()[0] == "NOT":
            self.consume("NOT")
            return not self.not_expr()
        return self.cmp_expr()

    def cmp_expr(self) -> bool:
        left_val = self.atom_value()
        op_kind  = self.peek()[0]

        if op_kind in ("EQ", "NEQ", "GT", "GTE", "LT", "LTE"):
            self.consume(op_kind)
            right_val = self.atom_value()
            return _compare(left_val, op_kind, right_val)

        # No operator → boolean truthiness
        return _truthy(left_val)

    def atom_value(self):
        kind, value = self.peek()

        if kind == "LPAREN":
            self.consume("LPAREN")
            result = self.or_expr()
            self.consume("RPAREN")
            return result   # bool result used directly

        if kind == "STR":
            self.consume("STR")
            return value[1:-1]  # strip surrounding quotes

        if kind == "NUM":
            self.consume("NUM")
            return float(value) if "." in value else int(value)

        if kind == "IDENT":
            self.consume("IDENT")
            return self._resolve(value)

        raise SyntaxError(f"ATEL condition: unexpected token {self.peek()}")

    def _resolve(self, expr: str):
        from ..template.resolver import resolve_safe
        return resolve_safe(expr, self.context, self.args)


# ──────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────

def _truthy(value) -> bool:
    if value is None or value == "" or value is False:
        return False
    if isinstance(value, (int, float)) and value == 0:
        return False
    return True


def _compare(left, op: str, right) -> bool:
    # Coerce for numeric comparisons
    try:
        l = float(left)
        r = float(right)
        if   op == "EQ":  return l == r
        elif op == "NEQ": return l != r
        elif op == "GT":  return l >  r
        elif op == "GTE": return l >= r
        elif op == "LT":  return l <  r
        elif op == "LTE": return l <= r
    except (TypeError, ValueError):
        pass

    # String fallback
    ls, rs = str(left), str(right)
    if   op == "EQ":  return ls == rs
    elif op == "NEQ": return ls != rs
    return False
