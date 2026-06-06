"""
arkhe.io.template.engine — ATEL template engine.

Entry point:

    from arkhe.io.template.engine import render

    render("{name:title} has {coins:number} coins.", player)
    render("Hello {}!", "World")
    render("{rank -> ADMIN:'👑 Admin', *:'👤 User'}", player)
    render("{online?🟢 Online:🔴 Offline}", player)

Expression anatomy:

    { expr_part ?? fallback_chain }
    { expr_part : transformer_chain }
    { condition ? true_val : false_val }
    { expr -> match_spec }

Where expr_part is one of:
    - empty                    → positional arg 0
    - digit(s)                 → positional arg N
    - attribute name           → context.name
    - dotted path              → context.a.b.c
    - method call              → context.method()
    - system token             → date, time, uuid, …

Operator precedence (parsed left-to-right in the expression body):
    1.  -> (match)         highest priority — no transformer/fallback
    2.  ?  (conditional)   may include transformer on branches
    3.  ?? (fallback)      applied before transformer
    4.  :  (transformer)   applied last
"""

import re
from typing import Any, List, Sequence

from .parser      import tokenize_template
from .resolver    import resolve, resolve_safe
from .transformers import apply_chain
from .conditions  import evaluate_condition
from .matchers    import evaluate_match


# ──────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────

def render(template: str, context: Any = None, *args: Any) -> str:
    """
    Render an ATEL template string.

    Args:
        template : The template string containing {expressions}.
        context  : Object (or dict) providing attribute values.
        *args    : Additional positional arguments for {} and {0} placeholders.

    Returns:
        The rendered string.
    """
    # Collect all positional args (context counts as args[0] if it's a plain value)
    positional: List[Any] = []
    if context is not None:
        positional.append(context)
    positional.extend(args)

    segments = tokenize_template(template)
    parts: List[str] = []

    for kind, body in segments:
        if kind == "text":
            parts.append(body)
        else:
            parts.append(_eval_expression(body, context, positional))

    return "".join(parts)


# ──────────────────────────────────────────────────────
# Expression evaluator
# ──────────────────────────────────────────────────────

def _eval_expression(body: str, context: Any, args: Sequence[Any]) -> str:
    """
    Evaluate a single expression body (the content between { and }).
    Returns a string.
    """
    body = body.strip()

    # ── 1. Match expression:  expr -> ADMIN:'...', *:'...' ──
    if " -> " in body or body.endswith("->"):
        return _eval_match(body, context, args)

    # ── 3. Fallback:  expr ?? default ?? ... ────────────────
    # Must check before conditional because ?? contains ?
    if " ?? " in body or body.startswith("??"):
        return _eval_fallback(body, context, args)

    # ── 2. Conditional:  condition?true:false ───────────────
    if "?" in body:
        return _eval_conditional(body, context, args)

    # ── 4. Transformer:  expr:chain ─────────────────────────
    if ":" in body:
        return _eval_transformer(body, context, args)

    # ── 5. Plain resolution ─────────────────────────────────
    value = resolve_safe(body, context, args)
    return "" if value is None else str(value)


# ──────────────────────────────────────────────────────
# Match  {rank -> ADMIN:'Admin', *:'User'}
# ──────────────────────────────────────────────────────

def _eval_match(body: str, context, args) -> str:
    left, _, spec = body.partition(" -> ")
    attr  = left.strip()
    value = resolve_safe(attr, context, args)
    return evaluate_match(value, spec.strip())


# ──────────────────────────────────────────────────────
# Conditional  {condition?true_branch:false_branch}
# ──────────────────────────────────────────────────────

def _eval_conditional(body: str, context, args) -> str:
    # Split on the first unquoted `?`
    q_idx = _find_unquoted(body, "?")
    if q_idx == -1:
        return resolve_safe(body, context, args) or ""

    condition_str  = body[:q_idx].strip()
    branches_str   = body[q_idx + 1:]

    # Split true and false branch on first unquoted `:`
    # Be careful: the false branch may itself contain `:` (transformers)
    c_idx = _find_unquoted(branches_str, ":")
    if c_idx == -1:
        true_branch  = branches_str.strip()
        false_branch = ""
    else:
        true_branch  = branches_str[:c_idx].strip()
        false_branch = branches_str[c_idx + 1:].strip()

    from .conditions import evaluate_condition
    result = evaluate_condition(condition_str, context, args)

    chosen = true_branch if result else false_branch
    # Render the chosen branch as a sub-expression if it contains {}
    if "{" in chosen:
        return render(chosen, context, *args[1:])
    return chosen


# ──────────────────────────────────────────────────────
# Fallback  {nickname ?? username ?? Anonymous}
# ──────────────────────────────────────────────────────

def _eval_fallback(body: str, context, args) -> str:
    """
    Evaluate a fallback chain:  expr ?? expr2 ?? literal
    Walk left to right. Return the first non-null/non-empty resolved value.
    The last segment is always returned as a literal string if nothing else
    resolved — this allows bare words like Anonymous as the final fallback.
    """
    parts = [p.strip() for p in body.split("??")]

    for i, part in enumerate(parts):
        if not part:
            continue
        is_last = i == len(parts) - 1

        # Try context resolution
        raw = resolve_safe(part, context, args)

        if raw is not None and raw != "":
            # Has a transformer — apply it
            if ":" in part:
                return _eval_expression(part, context, args)
            return str(raw)

        # Last segment: if resolution returned nothing, treat as a literal fallback
        if is_last:
            return part

    return ""


# ──────────────────────────────────────────────────────
# Transformer  {name:trim|capitalize}
# ──────────────────────────────────────────────────────

def _eval_transformer(body: str, context, args) -> str:
    # Split attribute from transformer chain on first `:`
    # But be careful about colons inside parentheses: decimal(2)
    colon = _find_unquoted_outside_parens(body, ":")
    if colon == -1:
        return str(resolve_safe(body, context, args) or "")

    attr_part  = body[:colon].strip()
    chain_part = body[colon + 1:].strip()

    value = resolve_safe(attr_part, context, args)
    if value is None:
        return ""

    try:
        return str(apply_chain(value, chain_part))
    except Exception as e:
        return f"[transformer error: {e}]"


# ──────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────

def _find_unquoted(s: str, char: str) -> int:
    """Find the index of `char` that is not inside single quotes."""
    in_q = False
    for i, c in enumerate(s):
        if c == "'":
            in_q = not in_q
        elif c == char and not in_q:
            return i
    return -1


def _find_unquoted_outside_parens(s: str, char: str) -> int:
    """Find char that is not inside single quotes or parentheses."""
    in_q  = False
    depth = 0
    for i, c in enumerate(s):
        if c == "'" and depth == 0:
            in_q = not in_q
        elif c == "(" and not in_q:
            depth += 1
        elif c == ")" and not in_q:
            depth -= 1
        elif c == char and not in_q and depth == 0:
            return i
    return -1
