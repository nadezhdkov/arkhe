"""
arkhe.math._engine
-----------------------
Motor matemático principal: Math.eval(), estatística, computação científica,
finanças e probabilidade.
"""

from __future__ import annotations

import ast
import math
import operator
import statistics as _stats
from decimal import Decimal, getcontext
from typing import Any, List, Optional, Sequence, Union


# ---------------------------------------------------------------------------
# Tabela de constantes e funções permitidas no avaliador de expressões
# ---------------------------------------------------------------------------

_SAFE_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "phi": (1 + math.sqrt(5)) / 2,    # razão áurea
    "inf": math.inf,
}

_SAFE_FUNCTIONS: dict[str, Any] = {
    "sqrt": math.sqrt,
    "pow": pow,
    "abs": abs,
    "round": round,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "min": min,
    "max": max,
    "factorial": math.factorial,
    "gcd": math.gcd,
    "hypot": math.hypot,
    "degrees": math.degrees,
    "radians": math.radians,
}


# ---------------------------------------------------------------------------
# Avaliador de expressões seguro
# ---------------------------------------------------------------------------

class _SafeEvalVisitor(ast.NodeVisitor):
    """Avaliador AST que só permite operações matemáticas seguras."""

    _BINOPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.FloorDiv: operator.floordiv,
    }
    _UNOPS = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def __init__(self, variables: dict[str, Any]) -> None:
        self._vars = {**_SAFE_CONSTANTS, **_SAFE_FUNCTIONS, **variables}

    def visit(self, node: ast.AST) -> Any:
        method = f"visit_{type(node).__name__}"
        handler = getattr(self, method, self.generic_visit)
        return handler(node)

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    # Python < 3.8 compat
    def visit_Num(self, node: Any) -> Any:  # type: ignore[override]
        return node.n

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self._vars:
            return self._vars[node.id]
        raise NameError(f"Unknown name: {node.id!r}")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        op_type = type(node.op)
        if op_type not in self._BINOPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = self.visit(node.left)
        right = self.visit(node.right)
        if op_type is ast.Div and right == 0:
            raise ZeroDivisionError("Division by zero in expression")
        return self._BINOPS[op_type](left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        op_type = type(node.op)
        if op_type not in self._UNOPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return self._UNOPS[op_type](self.visit(node.operand))

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are allowed")
        fname = node.func.id
        if fname not in _SAFE_FUNCTIONS:
            raise ValueError(f"Function not allowed: {fname!r}")
        args = [self.visit(a) for a in node.args]
        return _SAFE_FUNCTIONS[fname](*args)

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        cond = self.visit(node.test)
        return self.visit(node.body) if cond else self.visit(node.orelse)

    def visit_Compare(self, node: ast.Compare) -> Any:
        _CMPS = {
            ast.Eq: operator.eq, ast.NotEq: operator.ne,
            ast.Lt: operator.lt, ast.LtE: operator.le,
            ast.Gt: operator.gt, ast.GtE: operator.ge,
        }
        left = self.visit(node.left)
        for cmp_op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if not _CMPS[type(cmp_op)](left, right):
                return False
            left = right
        return True


def _safe_eval(expression: str, **variables: Any) -> Any:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {e}") from e
    visitor = _SafeEvalVisitor(variables)
    return visitor.visit(tree)


# ---------------------------------------------------------------------------
# Métodos numéricos
# ---------------------------------------------------------------------------

def _newton(
    f: Any,
    x0: float,
    tol: float = 1e-9,
    max_iter: int = 1000,
    h: float = 1e-7,
) -> float:
    """Método de Newton-Raphson."""
    x = x0
    for _ in range(max_iter):
        fx = f(x)
        if abs(fx) < tol:
            return x
        dfx = (f(x + h) - f(x - h)) / (2 * h)
        if abs(dfx) < 1e-15:
            raise ValueError("Derivative too close to zero in Newton's method")
        x -= fx / dfx
    raise ValueError(f"Newton's method did not converge after {max_iter} iterations")


def _bisection(
    f: Any,
    a: float,
    b: float,
    tol: float = 1e-9,
    max_iter: int = 1000,
) -> float:
    """Método da bisseção."""
    if f(a) * f(b) > 0:
        raise ValueError("f(a) and f(b) must have opposite signs")
    for _ in range(max_iter):
        mid = (a + b) / 2
        if abs(b - a) < tol or f(mid) == 0:
            return mid
        if f(a) * f(mid) < 0:
            b = mid
        else:
            a = mid
    return (a + b) / 2


def _secant(
    f: Any,
    x0: float,
    x1: float,
    tol: float = 1e-9,
    max_iter: int = 1000,
) -> float:
    """Método da secante."""
    for _ in range(max_iter):
        fx0, fx1 = f(x0), f(x1)
        if abs(fx1 - fx0) < 1e-15:
            raise ValueError("Denominator too small in secant method")
        x2 = x1 - fx1 * (x1 - x0) / (fx1 - fx0)
        if abs(x2 - x1) < tol:
            return x2
        x0, x1 = x1, x2
    raise ValueError(f"Secant method did not converge after {max_iter} iterations")


# ---------------------------------------------------------------------------
# Math — ponto de entrada principal
# ---------------------------------------------------------------------------

class Math:
    """
    Motor matemático unificado do NestifyPy.

    Todos os métodos são classmethod — não é necessário instanciar.

    ::

        Math.eval("(15 + 8) * sqrt(144)")  # 276
        Math.mean([1, 2, 3, 4, 5])         # 3.0
        Math.pi(precision=100)
    """

    _precision: int = 28  # precisão global padrão

    # ── precisão global ───────────────────────────────────────────────────

    @classmethod
    def precision(cls, digits: int) -> None:
        """Define a precisão global de operações decimais."""
        cls._precision = digits
        getcontext().prec = digits

    # ── avaliador de expressões ───────────────────────────────────────────

    @classmethod
    def eval(cls, expression: str, **variables: Any) -> Any:
        """
        Avalia uma expressão matemática de forma segura.

        ::

            Math.eval("(15 + 8) * sqrt(144)")   # 276.0
            Math.eval("x * y + 10", x=5, y=3)  # 25
            Math.eval("pi * 2")                  # 6.283...
        """
        result = _safe_eval(expression, **variables)
        # Tenta devolver int quando o resultado é inteiro
        if isinstance(result, float) and result == int(result):
            return int(result)
        return result

    # ── estatística ───────────────────────────────────────────────────────

    @classmethod
    def mean(cls, data: Sequence[Union[int, float]]) -> float:
        return _stats.mean(data)

    @classmethod
    def median(cls, data: Sequence[Union[int, float]]) -> float:
        return _stats.median(data)

    @classmethod
    def mode(cls, data: Sequence[Any]) -> Any:
        return _stats.mode(data)

    @classmethod
    def variance(cls, data: Sequence[Union[int, float]]) -> float:
        return _stats.variance(data)

    @classmethod
    def std(cls, data: Sequence[Union[int, float]]) -> float:
        return _stats.stdev(data)

    @classmethod
    def pvariance(cls, data: Sequence[Union[int, float]]) -> float:
        """Variância populacional."""
        return _stats.pvariance(data)

    @classmethod
    def pstd(cls, data: Sequence[Union[int, float]]) -> float:
        """Desvio padrão populacional."""
        return _stats.pstdev(data)

    @classmethod
    def quantiles(cls, data: Sequence[Union[int, float]], n: int = 4) -> List[float]:
        return _stats.quantiles(data, n=n)

    # ── computação científica ─────────────────────────────────────────────

    @classmethod
    def pi(cls, precision: int = 50) -> Decimal:
        """
        Calcula Pi com a precisão especificada.

        ::

            Math.pi(precision=100)
        """
        try:
            import mpmath  # type: ignore
            mpmath.mp.dps = precision
            return Decimal(str(mpmath.pi))
        except ImportError:
            # Fallback: usa fórmula de Machin
            getcontext().prec = precision + 10
            return _machin_pi(precision)

    @classmethod
    def sqrt(cls, value: Union[int, float, Decimal], precision: Optional[int] = None) -> Decimal:
        """
        Raiz quadrada de alta precisão.

        ::

            Math.sqrt(2, precision=50)
        """
        if precision:
            try:
                import mpmath  # type: ignore
                mpmath.mp.dps = precision
                return Decimal(str(mpmath.sqrt(value)))
            except ImportError:
                getcontext().prec = precision + 10
        return Decimal(value).sqrt()

    @classmethod
    def newton(
        cls,
        f: Any,
        x0: float,
        tol: float = 1e-9,
        max_iter: int = 1000,
    ) -> float:
        """Método de Newton-Raphson para encontrar raízes."""
        return _newton(f, x0, tol=tol, max_iter=max_iter)

    @classmethod
    def bisection(
        cls,
        f: Any,
        a: float,
        b: float,
        tol: float = 1e-9,
        max_iter: int = 1000,
    ) -> float:
        """Método da bisseção para encontrar raízes."""
        return _bisection(f, a, b, tol=tol, max_iter=max_iter)

    @classmethod
    def secant(
        cls,
        f: Any,
        x0: float,
        x1: float,
        tol: float = 1e-9,
        max_iter: int = 1000,
    ) -> float:
        """Método da secante para encontrar raízes."""
        return _secant(f, x0, x1, tol=tol, max_iter=max_iter)

    # ── matemática financeira ─────────────────────────────────────────────

    @classmethod
    def compound_interest(
        cls,
        principal: float,
        rate: float,
        periods: float,
        n: int = 1,
    ) -> float:
        """
        Juros compostos.

        Args:
            principal: Capital inicial.
            rate: Taxa anual (ex: 0.05 para 5%).
            periods: Número de anos.
            n: Número de capitalizações por ano (padrão: 1).

        Returns:
            Montante final.
        """
        return principal * (1 + rate / n) ** (n * periods)

    @classmethod
    def simple_interest(
        cls,
        principal: float,
        rate: float,
        time: float,
    ) -> float:
        """
        Juros simples.

        Returns:
            Montante total (principal + juros).
        """
        return principal * (1 + rate * time)

    @classmethod
    def loan(
        cls,
        principal: float,
        annual_rate: float,
        months: int,
    ) -> dict[str, float]:
        """
        Cálculo de prestação de empréstimo (sistema Price/SAF).

        Returns:
            dict com 'monthly_payment', 'total_paid', 'total_interest'.
        """
        if annual_rate == 0:
            monthly = principal / months
            return {
                "monthly_payment": monthly,
                "total_paid": monthly * months,
                "total_interest": 0.0,
            }
        r = annual_rate / 12
        payment = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
        total = payment * months
        return {
            "monthly_payment": payment,
            "total_paid": total,
            "total_interest": total - principal,
        }

    @classmethod
    def present_value(
        cls,
        future_value: float,
        rate: float,
        periods: float,
    ) -> float:
        """Valor presente de um montante futuro."""
        return future_value / (1 + rate) ** periods

    @classmethod
    def future_value(
        cls,
        present_value: float,
        rate: float,
        periods: float,
    ) -> float:
        """Valor futuro de um investimento."""
        return present_value * (1 + rate) ** periods

    # ── probabilidade e combinatória ──────────────────────────────────────

    @classmethod
    def combinations(cls, n: int, k: int) -> int:
        """C(n, k) — combinações sem repetição."""
        return math.comb(n, k)

    @classmethod
    def permutations(cls, n: int, k: Optional[int] = None) -> int:
        """P(n, k) — permutações."""
        return math.perm(n, k)

    @classmethod
    def probability(
        cls,
        favorable: int,
        total: int,
    ) -> float:
        """Probabilidade clássica: favorable / total."""
        if total == 0:
            raise ValueError("Total outcomes cannot be zero")
        return favorable / total

    @classmethod
    def factorial(cls, n: int) -> int:
        return math.factorial(n)

    @classmethod
    def gcd(cls, *args: int) -> int:
        return math.gcd(*args)

    @classmethod
    def lcm(cls, *args: int) -> int:
        result = args[0]
        for a in args[1:]:
            result = abs(result * a) // math.gcd(result, a)
        return result


# ---------------------------------------------------------------------------
# Cálculo de Pi via fórmula de Machin (fallback sem mpmath)
# ---------------------------------------------------------------------------

def _machin_pi(precision: int) -> Decimal:
    """Calcula Pi usando a fórmula de Machin: π/4 = 4·arctan(1/5) - arctan(1/239)."""
    getcontext().prec = precision + 10
    one = Decimal(1)
    four = Decimal(4)

    def arctan(x: Decimal) -> Decimal:
        total = x
        term = x
        x_sq = x * x
        n = 3
        while True:
            term *= x_sq
            delta = term / n
            total -= delta
            term *= x_sq
            n += 2
            delta = term / n
            total += delta
            n += 2
            if abs(delta) < Decimal(10) ** (-(precision + 5)):
                break
        return total

    pi = four * (four * arctan(one / 5) - arctan(one / 239))
    getcontext().prec = precision
    return +pi  # arredonda para a precisão pedida


__all__ = ["Math"]
