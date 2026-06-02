"""
nestifypy.math._types
---------------------
Tipos numéricos universais: Number, BigNumber, BigDecimal, Fraction, Complex.

Cada tipo expõe uma API fluente encadeável e integra-se com o módulo Try
para operações seguras (sem lançar ZeroDivisionError etc.).
"""

from __future__ import annotations

import cmath
import math
import operator
from decimal import Decimal, getcontext, InvalidOperation
from fractions import Fraction as _Fraction
from typing import Any, Union

# Tenta importar mpmath para alta precisão (opcional)
try:
    import mpmath  # type: ignore
    _HAS_MPMATH = True
except ImportError:
    _HAS_MPMATH = False

# Tenta importar sympy para matemática simbólica (opcional)
try:
    import sympy  # type: ignore
    _HAS_SYMPY = True
except ImportError:
    _HAS_SYMPY = False


# ---------------------------------------------------------------------------
# Resultado de falha (sem depender de Try para evitar import circular)
# ---------------------------------------------------------------------------

class MathError(Exception):
    """Erro base para operações matemáticas do NestifyPy."""


class DivisionByZeroError(MathError):
    """Lançado quando se tenta dividir por zero."""


class PrecisionError(MathError):
    """Lançado quando a precisão solicitada é inválida."""


# ---------------------------------------------------------------------------
# _NumericBase — mixin com API fluente compartilhada
# ---------------------------------------------------------------------------

class _NumericBase:
    """Mixin com operações fluentes comuns a todos os tipos numéricos."""

    # Subclasses devem expor _value como o valor Python nativo subjacente.

    # ── aritmética fluente ────────────────────────────────────────────────

    def add(self, other: Any) -> "_NumericBase":
        return self._wrap(self._value + self._coerce(other))

    def subtract(self, other: Any) -> "_NumericBase":
        return self._wrap(self._value - self._coerce(other))

    def multiply(self, other: Any) -> "_NumericBase":
        return self._wrap(self._value * self._coerce(other))

    def divide(self, other: Any) -> "_NumericBase":
        """Divisão segura — retorna FailureResult em vez de lançar exceção."""
        coerced = self._coerce(other)
        if coerced == 0:
            return FailureResult(DivisionByZeroError("Division by zero"))
        return self._wrap(self._value / coerced)

    def mod(self, other: Any) -> "_NumericBase":
        coerced = self._coerce(other)
        if coerced == 0:
            return FailureResult(DivisionByZeroError("Modulo by zero"))
        return self._wrap(self._value % coerced)

    def pow(self, exp: Any) -> "_NumericBase":
        return self._wrap(self._value ** self._coerce(exp))

    def negate(self) -> "_NumericBase":
        return self._wrap(-self._value)

    def abs(self) -> "_NumericBase":
        return self._wrap(abs(self._value))

    # ── precisão ─────────────────────────────────────────────────────────

    def precision(self, digits: int) -> "_NumericBase":
        """Retorna o valor convertido para Decimal com a precisão especificada."""
        ctx = getcontext().copy()
        ctx.prec = digits
        return Number(ctx.create_decimal(str(self._value)))

    # ── comparações ──────────────────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _NumericBase):
            return self._value == other._value
        return self._value == other

    def __lt__(self, other: Any) -> bool:
        return self._value < self._coerce(other)

    def __le__(self, other: Any) -> bool:
        return self._value <= self._coerce(other)

    def __gt__(self, other: Any) -> bool:
        return self._value > self._coerce(other)

    def __ge__(self, other: Any) -> bool:
        return self._value >= self._coerce(other)

    def __hash__(self) -> int:
        return hash(self._value)

    # ── operadores Python nativos ─────────────────────────────────────────

    def __add__(self, other: Any) -> "_NumericBase":
        return self.add(other)

    def __radd__(self, other: Any) -> "_NumericBase":
        return self._wrap(self._coerce(other) + self._value)

    def __sub__(self, other: Any) -> "_NumericBase":
        return self.subtract(other)

    def __rsub__(self, other: Any) -> "_NumericBase":
        return self._wrap(self._coerce(other) - self._value)

    def __mul__(self, other: Any) -> "_NumericBase":
        return self.multiply(other)

    def __rmul__(self, other: Any) -> "_NumericBase":
        return self._wrap(self._coerce(other) * self._value)

    def __truediv__(self, other: Any) -> "_NumericBase":
        return self.divide(other)

    def __rtruediv__(self, other: Any) -> "_NumericBase":
        if self._value == 0:
            return FailureResult(DivisionByZeroError("Division by zero"))
        return self._wrap(self._coerce(other) / self._value)

    def __mod__(self, other: Any) -> "_NumericBase":
        return self.mod(other)

    def __pow__(self, exp: Any) -> "_NumericBase":
        return self.pow(exp)

    def __neg__(self) -> "_NumericBase":
        return self.negate()

    def __abs__(self) -> "_NumericBase":
        return self.abs()

    # ── helpers internos (subclasses devem sobrepor _wrap / _coerce) ──────

    def _coerce(self, other: Any) -> Any:
        if isinstance(other, _NumericBase):
            return other._value
        # Garante que o tipo coerced seja compatível com _value
        if isinstance(self._value, Decimal) and not isinstance(other, Decimal):
            return Decimal(str(other))
        if isinstance(self._value, _Fraction) and not isinstance(other, (_Fraction, int)):
            return _Fraction(str(other))
        return other

    def _wrap(self, value: Any) -> "_NumericBase":
        return Number(value)

    # ── extração ──────────────────────────────────────────────────────────

    def value(self) -> Any:
        """Retorna o valor Python nativo subjacente."""
        return self._value

    def to_int(self) -> int:
        return int(self._value)

    def to_float(self) -> float:
        return float(self._value)

    def to_decimal(self) -> Decimal:
        return Decimal(str(self._value))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._value!r})"

    def __str__(self) -> str:
        return str(self._value)


# ---------------------------------------------------------------------------
# FailureResult — resultado de operação inválida
# ---------------------------------------------------------------------------

class FailureResult(_NumericBase):
    """
    Retornado por operações que falhariam (ex: divisão por zero).
    Compatível com o módulo Try.

    ::

        result = Number(10).divide(0)
        if result.is_failure():
            print(result.get_error())
    """

    __slots__ = ("_error", "_value")

    def __init__(self, error: Exception) -> None:
        self._error = error
        self._value = None  # type: ignore[assignment]

    def is_failure(self) -> bool:
        return True

    def is_success(self) -> bool:
        return False

    def get_error(self) -> Exception:
        return self._error

    # Todas as operações num FailureResult propagam o próprio resultado
    def add(self, other: Any) -> "FailureResult":
        return self

    def subtract(self, other: Any) -> "FailureResult":
        return self

    def multiply(self, other: Any) -> "FailureResult":
        return self

    def divide(self, other: Any) -> "FailureResult":
        return self

    def mod(self, other: Any) -> "FailureResult":
        return self

    def pow(self, exp: Any) -> "FailureResult":
        return self

    def negate(self) -> "FailureResult":
        return self

    def abs(self) -> "FailureResult":
        return self

    def precision(self, digits: int) -> "FailureResult":
        return self

    def to_int(self) -> int:
        raise self._error

    def to_float(self) -> float:
        raise self._error

    def to_decimal(self) -> Decimal:
        raise self._error

    def __repr__(self) -> str:
        return f"FailureResult({self._error!r})"

    def __str__(self) -> str:
        return f"FailureResult: {self._error}"


# ---------------------------------------------------------------------------
# Number — tipo numérico universal
# ---------------------------------------------------------------------------

class Number(_NumericBase):
    """
    Tipo numérico universal. Seleciona automaticamente a melhor representação.

    ::

        Number(10)
        Number("0.1")
        Number("999999999999999999999999999")
    """

    __slots__ = ("_value",)

    def __init__(self, value: Union[int, float, str, Decimal, _Fraction]) -> None:
        if isinstance(value, _NumericBase):
            self._value = value._value
        elif isinstance(value, (int, Decimal, _Fraction)):
            self._value = value
        elif isinstance(value, float):
            # Converte float para Decimal para evitar imprecisão
            self._value = Decimal(str(value))
        elif isinstance(value, str):
            value = value.strip()
            if "/" in value:
                self._value = _Fraction(value)
            elif "." in value or "e" in value.lower():
                self._value = Decimal(value)
            else:
                self._value = int(value)
        else:
            self._value = value  # tipo desconhecido — aceita assim mesmo

    def _wrap(self, value: Any) -> "Number":
        return Number(value)

    def is_failure(self) -> bool:
        return False

    def is_success(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# BigNumber — inteiros muito grandes
# ---------------------------------------------------------------------------

class BigNumber(_NumericBase):
    """
    Otimizado para inteiros extremamente grandes.

    ::

        n = BigNumber("999999999999999999999999999999")
        n.pow(1000)
    """

    __slots__ = ("_value",)

    def __init__(self, value: Union[int, str]) -> None:
        if isinstance(value, _NumericBase):
            self._value = int(value._value)
        else:
            self._value = int(value)

    def _wrap(self, value: Any) -> "BigNumber":
        return BigNumber(int(value))

    def factorial(self) -> "BigNumber":
        return BigNumber(math.factorial(self._value))

    def gcd(self, other: Any) -> "BigNumber":
        return BigNumber(math.gcd(self._value, self._coerce(other)))

    def lcm(self, other: Any) -> "BigNumber":
        a, b = self._value, int(self._coerce(other))
        return BigNumber(abs(a * b) // math.gcd(a, b))

    def is_prime(self) -> bool:
        n = self._value
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True

    def digits(self) -> int:
        """Número de dígitos decimais."""
        return len(str(abs(self._value)))

    def is_failure(self) -> bool:
        return False

    def is_success(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# BigDecimal — decimais de alta precisão
# ---------------------------------------------------------------------------

class BigDecimal(_NumericBase):
    """
    Cálculos decimais de alta precisão.

    ::

        price = BigDecimal("19.99")
        tax = BigDecimal("0.17")
        price.multiply(tax)
    """

    __slots__ = ("_value",)

    def __init__(self, value: Union[str, Decimal, float, int]) -> None:
        if isinstance(value, _NumericBase):
            self._value = Decimal(str(value._value))
        elif isinstance(value, Decimal):
            self._value = value
        else:
            self._value = Decimal(str(value))

    def _wrap(self, value: Any) -> "BigDecimal":
        return BigDecimal(Decimal(str(value)))

    def round(self, places: int) -> "BigDecimal":
        return BigDecimal(round(self._value, places))

    def floor(self) -> "BigDecimal":
        return BigDecimal(math.floor(self._value))

    def ceil(self) -> "BigDecimal":
        return BigDecimal(math.ceil(self._value))

    def is_failure(self) -> bool:
        return False

    def is_success(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Fraction — aritmética racional exata
# ---------------------------------------------------------------------------

class Fraction(_NumericBase):
    """
    Aritmética racional exata. Sem arredondamento de ponto flutuante.

    ::

        Fraction("1/3")
        Fraction("5/7")
    """

    __slots__ = ("_value",)

    def __init__(self, value: Union[str, int, float, _Fraction]) -> None:
        if isinstance(value, _NumericBase):
            self._value = _Fraction(str(value._value))
        elif isinstance(value, _Fraction):
            self._value = value
        else:
            self._value = _Fraction(str(value))

    def _wrap(self, value: Any) -> "Fraction":
        return Fraction(_Fraction(value))

    @property
    def numerator(self) -> int:
        return self._value.numerator

    @property
    def denominator(self) -> int:
        return self._value.denominator

    def simplify(self) -> "Fraction":
        """Retorna a fração já simplificada (Python faz isso automaticamente)."""
        return Fraction(self._value)

    def to_mixed(self) -> tuple[int, "Fraction"]:
        """Retorna (parte inteira, fração própria)."""
        whole = int(self._value)
        remainder = self._value - whole
        return whole, Fraction(remainder)

    def is_failure(self) -> bool:
        return False

    def is_success(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Complex — números complexos
# ---------------------------------------------------------------------------

class Complex(_NumericBase):
    """
    Números complexos.

    ::

        Complex(2, 5)   # 2 + 5j
    """

    __slots__ = ("_value",)

    def __init__(self, real: Union[float, int, complex], imag: float = 0.0) -> None:
        if isinstance(real, complex):
            self._value = real
        elif isinstance(real, _NumericBase):
            self._value = complex(float(real._value), imag)
        else:
            self._value = complex(real, imag)

    def _wrap(self, value: Any) -> "Complex":
        return Complex(complex(value))

    @property
    def real(self) -> float:
        return self._value.real

    @property
    def imag(self) -> float:
        return self._value.imag

    def conjugate(self) -> "Complex":
        return Complex(self._value.conjugate())

    def magnitude(self) -> Number:
        return Number(abs(self._value))

    def phase(self) -> Number:
        return Number(cmath.phase(self._value))

    def is_failure(self) -> bool:
        return False

    def is_success(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"Complex({self._value.real!r}, {self._value.imag!r})"

    def __str__(self) -> str:
        return str(self._value)


__all__ = [
    "Number",
    "BigNumber",
    "BigDecimal",
    "Fraction",
    "Complex",
    "FailureResult",
    "MathError",
    "DivisionByZeroError",
    "PrecisionError",
    "_HAS_MPMATH",
    "_HAS_SYMPY",
]
