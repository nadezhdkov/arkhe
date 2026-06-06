"""
arkhe.io.template.parser — Template string tokenizer.

Splits an ATEL template into a sequence of segments:
    ("text",  "literal string")
    ("expr",  "expression_body")

The expression body is the raw content between { and },
with brace nesting respected so inner braces don't terminate
the expression prematurely.

Example:
    "Hello {name}, you have {coins:number} coins."
    →
    [
        ("text", "Hello "),
        ("expr", "name"),
        ("text", ", you have "),
        ("expr", "coins:number"),
        ("text", " coins."),
    ]

Escaped braces {{ and }} are rendered as literal { and }.
"""

from typing import List, Tuple

Segment = Tuple[str, str]


def tokenize_template(template: str) -> List[Segment]:
    """
    Split a template string into text and expression segments.
    """
    segments: List[Segment] = []
    i     = 0
    n     = len(template)
    buf   = []

    while i < n:
        ch = template[i]

        # ── Escaped braces ──────────────────────────
        if ch == "{" and i + 1 < n and template[i + 1] == "{":
            buf.append("{")
            i += 2
            continue

        if ch == "}" and i + 1 < n and template[i + 1] == "}":
            buf.append("}")
            i += 2
            continue

        # ── Opening brace → start of expression ─────
        if ch == "{":
            if buf:
                segments.append(("text", "".join(buf)))
                buf = []

            i += 1
            depth  = 1
            expr   = []

            while i < n and depth > 0:
                ec = template[i]
                if ec == "{":
                    depth += 1
                    expr.append(ec)
                elif ec == "}":
                    depth -= 1
                    if depth > 0:
                        expr.append(ec)
                else:
                    expr.append(ec)
                i += 1

            segments.append(("expr", "".join(expr)))
            continue

        buf.append(ch)
        i += 1

    if buf:
        segments.append(("text", "".join(buf)))

    return segments
