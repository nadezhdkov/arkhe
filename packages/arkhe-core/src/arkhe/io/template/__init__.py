"""
arkhe.io.template — Arkhe Template Expression Language (ATEL).

A lightweight, reflection-powered template engine with zero dependencies.

─────────────────────────────────────────────
Quick start
─────────────────────────────────────────────

    from arkhe.io.template import render

    render("{name:title} has {coins:number} coins.", player)
    # → "Samuel has 15,000 coins."

    render("Hello {}!", "World")
    # → "Hello World!"

─────────────────────────────────────────────
Expression syntax
─────────────────────────────────────────────

    {attr}                      attribute resolution
    {attr.nested}               dotted path
    {method()}                  no-arg method call
    {}  {0}  {1}                positional arguments
    {date} {time} {uuid} ...    system tokens

    {attr:transformer}          transformer
    {attr:trim|upper}           transformer chain
    {attr:decimal(2)}           transformer with argument

    {attr ?? fallback}          fallback if None / empty
    {a ?? b ?? literal}         fallback chain

    {cond?true:false}           conditional
    {coins > 1000?Rich:Poor}    comparison conditional
    {a && b?X:Y}                compound condition

    {rank -> A:'x', *:'y'}      match expression

─────────────────────────────────────────────
Public API
─────────────────────────────────────────────

    render(template, context, *args) → str
        Main entry point. Render a template string.

    evaluate_condition(condition, context, args) → bool
        Evaluate a standalone ATEL condition string.

    evaluate_match(value, spec) → str
        Evaluate a standalone match spec against a value.

    apply_transformer(value, spec) → Any
        Apply a single transformer to a value.

    apply_chain(value, chain) → Any
        Apply a pipe-separated transformer chain.

    resolve(expression, context, args) → Any
        Resolve an ATEL expression against a context object.

    resolve_safe(expression, context, args, default) → Any
        Like resolve(), but returns default instead of raising.

    resolve_system_token(name) → Any
        Resolve a built-in system token by name.

    is_system_token(name) → bool
        True if name is a known system token.

    tokenize_template(template) → List[Segment]
        Low-level: split a template into text/expr segments.

─────────────────────────────────────────────
Available transformers
─────────────────────────────────────────────

    String       upper, lower, capitalize, title, reverse,
                 trim, length, repeat(n), substring(s,e),
                 pad_left(n), pad_right(n), center(n)

    Case         camel_case, pascal_case, snake_case,
                 kebab_case, constant_case

    Normalize    normalize, digits, letters

    Numeric      number, decimal(n), percent, currency

    Date         date, time, datetime, date(%format)

    Mask         mask(###.###-##)

    Collection   size, empty, first, last, join(sep)

─────────────────────────────────────────────
System tokens
─────────────────────────────────────────────

    {date}      current date        (YYYY-MM-DD)
    {time}      current time        (HH:MM:SS)
    {now}       current datetime    (YYYY-MM-DD HH:MM:SS)
    {uuid}      random UUID v4
    {hostname}  machine hostname
    {user}      current OS user
    {os}        operating system name
    {python}    Python version string
"""

from .engine      import render
from .conditions  import evaluate_condition
from .matchers    import evaluate_match, parse_match
from .transformers import apply_transformer, apply_chain
from .resolver    import resolve, resolve_safe
from .tokens      import resolve_system_token, is_system_token
from .parser      import tokenize_template

__all__ = [
    # Core
    "render",
    # Conditions
    "evaluate_condition",
    # Match
    "evaluate_match",
    "parse_match",
    # Transformers
    "apply_transformer",
    "apply_chain",
    # Resolver
    "resolve",
    "resolve_safe",
    # Tokens
    "resolve_system_token",
    "is_system_token",
    # Parser (low-level)
    "tokenize_template",
]
