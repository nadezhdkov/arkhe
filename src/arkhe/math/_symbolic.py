"""
arkhe.math._symbolic
------------------------
Matemática simbólica via SymPy.

Expõe Symbol e Expr com API fluente encadeável.
Se SymPy não estiver instalado, lança ImportError com mensagem clara.

::

    x = Symbol("x")
    expr = x**2 + 5*x + 6
    expr.solve()        # [-2, -3]
    expr.derivative()   # 2*x + 5
    expr.integrate()    # x**3/3 + 5*x**2/2 + 6*x
"""

from __future__ import annotations

from typing import Any, List, Optional, Union


def _require_sympy() -> Any:
    try:
        import sympy  # type: ignore
        return sympy
    except ImportError:
        raise ImportError(
            "arkhe.math symbolic features require SymPy. "
            "Install it with: pip install sympy"
        )


class Symbol:
    """
    Símbolo matemático para expressões simbólicas.

    ::

        x = Symbol("x")
        y = Symbol("y")
        expr = x**2 + 3*x*y - y**2
    """

    __slots__ = ("_sym", "_name")

    def __init__(self, name: str) -> None:
        sympy = _require_sympy()
        self._name = name
        self._sym = sympy.Symbol(name)

    # ── operadores para construir expressões ──────────────────────────────

    def __add__(self, other: Any) -> "Expr":
        return Expr(self._sym + _unwrap(other))

    def __radd__(self, other: Any) -> "Expr":
        return Expr(_unwrap(other) + self._sym)

    def __sub__(self, other: Any) -> "Expr":
        return Expr(self._sym - _unwrap(other))

    def __rsub__(self, other: Any) -> "Expr":
        return Expr(_unwrap(other) - self._sym)

    def __mul__(self, other: Any) -> "Expr":
        return Expr(self._sym * _unwrap(other))

    def __rmul__(self, other: Any) -> "Expr":
        return Expr(_unwrap(other) * self._sym)

    def __truediv__(self, other: Any) -> "Expr":
        return Expr(self._sym / _unwrap(other))

    def __rtruediv__(self, other: Any) -> "Expr":
        return Expr(_unwrap(other) / self._sym)

    def __pow__(self, exp: Any) -> "Expr":
        return Expr(self._sym ** _unwrap(exp))

    def __neg__(self) -> "Expr":
        return Expr(-self._sym)

    def __repr__(self) -> str:
        return f"Symbol({self._name!r})"

    def __str__(self) -> str:
        return self._name

    @property
    def _raw(self) -> Any:
        return self._sym


class Expr:
    """
    Expressão simbólica construída a partir de Symbols.

    ::

        x = Symbol("x")
        expr = x**2 + 5*x + 6
        expr.solve()         # [-2, -3]
        expr.derivative()    # Expr(2*x + 5)
        expr.integrate()     # Expr(x**3/3 + 5*x**2/2 + 6*x)
        expr.simplify()
        expr.expand()
        expr.factor()
        expr.substitute(x=2) # 20
    """

    __slots__ = ("_expr",)

    def __init__(self, expr: Any) -> None:
        self._expr = expr

    # ── resolução ─────────────────────────────────────────────────────────

    def solve(self, symbol: Optional[Symbol] = None) -> List[Any]:
        """
        Resolve a expressão igualada a zero.
        Retorna lista de soluções.

        ::

            (x**2 + 5*x + 6).solve()  # [-2, -3]
        """
        sympy = _require_sympy()
        sym = symbol._raw if symbol else None
        if sym is None:
            free = self._expr.free_symbols
            if not free:
                return []
            sym = next(iter(free))
        solutions = sympy.solve(self._expr, sym)
        return [_to_python(s) for s in solutions]

    # ── cálculo diferencial e integral ────────────────────────────────────

    def derivative(self, symbol: Optional[Symbol] = None, order: int = 1) -> "Expr":
        """
        Calcula a derivada da expressão.

        ::

            expr.derivative()      # derivada primeira
            expr.derivative(order=2)  # derivada segunda
        """
        sympy = _require_sympy()
        sym = symbol._raw if symbol else None
        if sym is None:
            free = self._expr.free_symbols
            sym = next(iter(free)) if free else None
        result = sympy.diff(self._expr, sym, order)
        return Expr(result)

    def integrate(
        self,
        symbol: Optional[Symbol] = None,
        lower: Optional[Any] = None,
        upper: Optional[Any] = None,
    ) -> "Expr":
        """
        Calcula a integral da expressão.
        Se lower e upper forem fornecidos, calcula integral definida.

        ::

            expr.integrate()               # indefinida
            expr.integrate(lower=0, upper=1)  # definida
        """
        sympy = _require_sympy()
        sym = symbol._raw if symbol else None
        if sym is None:
            free = self._expr.free_symbols
            sym = next(iter(free)) if free else None
        if lower is not None and upper is not None:
            result = sympy.integrate(self._expr, (sym, lower, upper))
        else:
            result = sympy.integrate(self._expr, sym)
        return Expr(result)

    # ── simplificação ─────────────────────────────────────────────────────

    def simplify(self) -> "Expr":
        """Simplifica a expressão."""
        sympy = _require_sympy()
        return Expr(sympy.simplify(self._expr))

    def expand(self) -> "Expr":
        """Expande a expressão."""
        sympy = _require_sympy()
        return Expr(sympy.expand(self._expr))

    def factor(self) -> "Expr":
        """Fatoriza a expressão."""
        sympy = _require_sympy()
        return Expr(sympy.factor(self._expr))

    def collect(self, symbol: Symbol) -> "Expr":
        """Agrupa termos pelo símbolo dado."""
        sympy = _require_sympy()
        return Expr(sympy.collect(self._expr, symbol._raw))

    # ── substituição e avaliação ──────────────────────────────────────────

    def substitute(self, **kwargs: Any) -> Any:
        """
        Substitui símbolos por valores.

        ::

            expr.substitute(x=2, y=3)
        """
        sympy = _require_sympy()
        subs = {sympy.Symbol(k): v for k, v in kwargs.items()}
        result = self._expr.subs(subs)
        return _to_python(result)

    def evaluate(self, precision: int = 15) -> float:
        """Avalia numericamente a expressão."""
        sympy = _require_sympy()
        return float(sympy.N(self._expr, precision))

    # ── operadores ────────────────────────────────────────────────────────

    def __add__(self, other: Any) -> "Expr":
        return Expr(self._expr + _unwrap(other))

    def __radd__(self, other: Any) -> "Expr":
        return Expr(_unwrap(other) + self._expr)

    def __sub__(self, other: Any) -> "Expr":
        return Expr(self._expr - _unwrap(other))

    def __rsub__(self, other: Any) -> "Expr":
        return Expr(_unwrap(other) - self._expr)

    def __mul__(self, other: Any) -> "Expr":
        return Expr(self._expr * _unwrap(other))

    def __rmul__(self, other: Any) -> "Expr":
        return Expr(_unwrap(other) * self._expr)

    def __truediv__(self, other: Any) -> "Expr":
        return Expr(self._expr / _unwrap(other))

    def __pow__(self, exp: Any) -> "Expr":
        return Expr(self._expr ** _unwrap(exp))

    def __neg__(self) -> "Expr":
        return Expr(-self._expr)

    def __repr__(self) -> str:
        return f"Expr({self._expr!r})"

    def __str__(self) -> str:
        return str(self._expr)

    @property
    def _raw(self) -> Any:
        return self._expr


# ---------------------------------------------------------------------------
# helpers internos
# ---------------------------------------------------------------------------

def _unwrap(obj: Any) -> Any:
    """Extrai o valor sympy de Symbol ou Expr, ou retorna como está."""
    if isinstance(obj, (Symbol, Expr)):
        return obj._raw
    return obj


def _to_python(value: Any) -> Any:
    """Converte resultado sympy para tipo Python nativo quando possível."""
    try:
        import sympy  # type: ignore
        if isinstance(value, sympy.Integer):
            return int(value)
        if isinstance(value, sympy.Float):
            return float(value)
        if isinstance(value, sympy.Rational):
            from fractions import Fraction
            return Fraction(int(value.p), int(value.q))
        return value
    except Exception:
        return value


__all__ = ["Symbol", "Expr"]
