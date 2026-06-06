"""
arkhe.io.template.transformers — Value transformers.

Transformers are applied after resolution via the pipe syntax:
    {name:upper}
    {name:trim|capitalize}
    {price:decimal(2)}
    {players:join(', ')}

Transformer chaining is left-to-right:
    {username:trim|lower}  →  trim first, then lower.
"""

import re
import unicodedata
from datetime import datetime, date
from typing import Any, List, Tuple


# ──────────────────────────────────────────────────────
# Transformer registry
# ──────────────────────────────────────────────────────

def apply_transformer(value: Any, spec: str) -> Any:
    """
    Apply a single transformer spec to value.
    spec may include arguments: 'decimal(2)', 'mask(###-##)', 'join(, )'
    """
    # Parse name and optional argument: name(arg)
    m = re.match(r"^(\w+)\((.+)\)$", spec.strip())
    if m:
        name = m.group(1)
        arg  = m.group(2)
        # Strip surrounding single quotes from string args: ', ' → ,+space
        if arg.startswith("'") and arg.endswith("'"):
            arg = arg[1:-1]
    else:
        name = spec.strip()
        arg  = None

    fn = _REGISTRY.get(name)
    if fn is None:
        raise ValueError(f"ATEL: unknown transformer '{name}'")
    return fn(value, arg)


def apply_chain(value: Any, chain: str) -> Any:
    """
    Apply a chain of transformers separated by `|`.
    Example: 'trim|lower'
    """
    specs = chain.split("|")
    for spec in specs:
        value = apply_transformer(value, spec.strip())
    return value


# ──────────────────────────────────────────────────────
# String transformers
# ──────────────────────────────────────────────────────

def _upper(v, _):    return str(v).upper()
def _lower(v, _):    return str(v).lower()
def _capitalize(v, _): return str(v).capitalize()
def _title(v, _):    return str(v).title()
def _reverse(v, _):  return str(v)[::-1]
def _trim(v, _):     return str(v).strip()
def _length(v, _):   return len(str(v))


def _repeat(v, arg):
    n = int(arg) if arg else 2
    return str(v) * n


def _substring(v, arg):
    if not arg:
        return str(v)
    parts = [p.strip() for p in arg.split(",")]
    start = int(parts[0]) if parts[0] else 0
    end   = int(parts[1]) if len(parts) > 1 and parts[1] else None
    return str(v)[start:end]


def _pad_left(v, arg):
    width = int(arg) if arg else 10
    return str(v).rjust(width)


def _pad_right(v, arg):
    width = int(arg) if arg else 10
    return str(v).ljust(width)


def _center(v, arg):
    width = int(arg) if arg else 10
    return str(v).center(width)


# ──────────────────────────────────────────────────────
# Case converters
# ──────────────────────────────────────────────────────

def _to_words(s: str) -> List[str]:
    """Split a string into words regardless of case/delimiter style."""
    s = re.sub(r"[-_\s]+", " ", s)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    return [w for w in s.split() if w]


def _camel_case(v, _):
    words = _to_words(str(v))
    if not words:
        return ""
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def _pascal_case(v, _):
    return "".join(w.capitalize() for w in _to_words(str(v)))


def _snake_case(v, _):
    return "_".join(w.lower() for w in _to_words(str(v)))


def _kebab_case(v, _):
    return "-".join(w.lower() for w in _to_words(str(v)))


def _constant_case(v, _):
    return "_".join(w.upper() for w in _to_words(str(v)))


# ──────────────────────────────────────────────────────
# Text normalization
# ──────────────────────────────────────────────────────

def _normalize(v, _):
    """Remove accents and diacritics. João → Joao"""
    nfkd = unicodedata.normalize("NFKD", str(v))
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ──────────────────────────────────────────────────────
# Character filters
# ──────────────────────────────────────────────────────

def _digits(v, _):  return re.sub(r"\D", "", str(v))
def _letters(v, _): return re.sub(r"[^a-zA-Z]", "", str(v))


# ──────────────────────────────────────────────────────
# Numeric transformers
# ──────────────────────────────────────────────────────

def _number(v, _):
    """Format with thousands separator. 15000 → 15,000"""
    try:
        return f"{float(v):,.0f}".replace(".0", "")
    except (ValueError, TypeError):
        return str(v)


def _decimal(v, arg):
    """Format with fixed decimal places. decimal(2) → 10.50"""
    places = int(arg) if arg else 2
    try:
        return f"{float(v):.{places}f}"
    except (ValueError, TypeError):
        return str(v)


def _percent(v, _):
    """Format as percentage. 0.75 → 75%  or  75 → 75%"""
    try:
        n = float(v)
        if n <= 1.0:
            n *= 100
        return f"{n:.0f}%"
    except (ValueError, TypeError):
        return str(v)


def _currency(v, _):
    """Format as currency. 10.5 → $10.50"""
    try:
        return f"${float(v):.2f}"
    except (ValueError, TypeError):
        return str(v)


# ──────────────────────────────────────────────────────
# Date transformers
# ──────────────────────────────────────────────────────

def _parse_dt(v):
    """Try to coerce v to a datetime object."""
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v)
    if isinstance(v, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(v, fmt)
            except ValueError:
                pass
    raise ValueError(f"ATEL: cannot parse '{v}' as a date")


def _date(v, arg):
    fmt = arg if arg else "%Y-%m-%d"
    return _parse_dt(v).strftime(fmt)


def _time_t(v, _):
    return _parse_dt(v).strftime("%H:%M:%S")


def _datetime_t(v, _):
    return _parse_dt(v).strftime("%Y-%m-%d %H:%M:%S")


# ──────────────────────────────────────────────────────
# Mask transformer
# ──────────────────────────────────────────────────────

def _mask(v, arg):
    """
    Apply a mask pattern using # as digit placeholder.
    {cpf:mask(###.###.###-##)}
    {phone:mask((##) #####-####)}
    """
    if not arg:
        return str(v)
    digits = re.sub(r"\D", "", str(v))
    result = []
    d_idx = 0
    for ch in arg:
        if ch == "#":
            if d_idx < len(digits):
                result.append(digits[d_idx])
                d_idx += 1
            else:
                result.append("_")
        else:
            result.append(ch)
    return "".join(result)


# ──────────────────────────────────────────────────────
# Collection transformers
# ──────────────────────────────────────────────────────

def _size(v, _):
    try:
        return len(v)
    except TypeError:
        return 0


def _empty(v, _):
    try:
        return "true" if len(v) == 0 else "false"
    except TypeError:
        return "true" if not v else "false"


def _first(v, _):
    try:
        if isinstance(v, dict):
            return next(iter(v.values()))
        return v[0]
    except (IndexError, StopIteration, TypeError):
        return None


def _last(v, _):
    try:
        if isinstance(v, dict):
            return list(v.values())[-1]
        return v[-1]
    except (IndexError, TypeError):
        return None


def _join(v, arg):
    sep = arg if arg is not None else ", "
    try:
        return sep.join(str(x) for x in v)
    except TypeError:
        return str(v)


# ──────────────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────────────

_REGISTRY = {
    # String
    "upper":         _upper,
    "lower":         _lower,
    "capitalize":    _capitalize,
    "title":         _title,
    "reverse":       _reverse,
    "trim":          _trim,
    "length":        _length,
    "repeat":        _repeat,
    "substring":     _substring,
    "pad_left":      _pad_left,
    "pad_right":     _pad_right,
    "center":        _center,
    # Case
    "camel_case":    _camel_case,
    "pascal_case":   _pascal_case,
    "snake_case":    _snake_case,
    "kebab_case":    _kebab_case,
    "constant_case": _constant_case,
    # Normalization
    "normalize":     _normalize,
    # Filters
    "digits":        _digits,
    "letters":       _letters,
    # Numeric
    "number":        _number,
    "decimal":       _decimal,
    "percent":       _percent,
    "currency":      _currency,
    # Date
    "date":          _date,
    "time":          _time_t,
    "datetime":      _datetime_t,
    # Mask
    "mask":          _mask,
    # Collections
    "size":          _size,
    "empty":         _empty,
    "first":         _first,
    "last":          _last,
    "join":          _join,
}
