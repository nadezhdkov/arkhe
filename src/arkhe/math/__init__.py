"""
arkhe.math
--------------
Framework matemático avançado para o ecossistema NestifyPy.

Unifica aritmética de precisão arbitrária, matemática simbólica,
conversão de unidades, moedas, vetores, matrizes, estatística,
geometria e avaliação de expressões em uma única API consistente.

Uso rápido
----------
::

    from arkhe.math import *

    # Tipos numéricos
    Number("0.1").add(Number("0.2"))      # sem imprecisão float
    BigNumber("99999999999").pow(1000)
    BigDecimal("19.99").multiply("0.17")
    Fraction("1/3").add("1/6")
    Complex(2, 5).magnitude()

    # Motor de expressões
    Math.eval("(15 + 8) * sqrt(144)")     # 276
    Math.eval("x**2 + 2*x", x=3)         # 15
    Math.pi(precision=100)

    # Estatística
    Math.mean([1, 2, 3, 4, 5])
    Math.std([10, 20, 30])

    # Álgebra linear
    v = Vector(1, 2, 3)
    v.dot(Vector(4, 5, 6))

    m = Matrix([[1, 2], [3, 4]])
    m.inverse()

    # Geometria
    Circle(radius=5).area()
    Rectangle(10, 20).perimeter()
    Triangle(a=3, b=4, c=5).area()

    # Conversão de unidades
    Distance("10km").to("mi")
    Weight("70kg").to("lb")
    Temperature("100C").to("F")
    Duration("2h 30m").to("s")

    # Moeda v2 — precisão arbitrária, criptoativos, portfolio
    Money("19.99", "USD").multiply("0.17").add(Money("5.00", "USD")).to("BRL")
    Money(100, Currency.USD) > Money(50, Currency.USD)
    Money("0.5", "BTC").to("USD").to("BRL")

    portfolio = Portfolio()
    portfolio.add(Money("0.5", "BTC"))
    portfolio.total("USD")

    btc = CryptoPrice.of("BTC")
    print(btc.price_usd)

    # Matemática simbólica (requer sympy)
    x = Symbol("x")
    (x**2 + 5*x + 6).solve()             # [-2, -3]
    (x**3).derivative()                   # 3*x**2
"""

from arkhe.math._types import (
    Number,
    BigNumber,
    BigDecimal,
    Fraction,
    Complex,
    FailureResult,
    MathError,
    DivisionByZeroError,
    PrecisionError,
)

from arkhe.math._engine import Math

from arkhe.math._symbolic import Symbol, Expr

from arkhe.math._linalg import Vector, Matrix

from arkhe.math._geometry import Circle, Rectangle, Triangle, Sphere, Cylinder

from arkhe.math._units import Distance, Weight, Temperature, Duration

from arkhe.math._money import Money, Currency, CryptoPrice, Portfolio


__all__ = [
    # Tipos numéricos
    "Number",
    "BigNumber",
    "BigDecimal",
    "Fraction",
    "Complex",
    "FailureResult",
    # Erros
    "MathError",
    "DivisionByZeroError",
    "PrecisionError",
    # Motor
    "Math",
    # Simbólico
    "Symbol",
    "Expr",
    # Álgebra linear
    "Vector",
    "Matrix",
    # Geometria
    "Circle",
    "Rectangle",
    "Triangle",
    "Sphere",
    "Cylinder",
    # Unidades
    "Distance",
    "Weight",
    "Temperature",
    "Duration",
    # Moeda v2
    "Money",
    "Currency",
    "CryptoPrice",
    "Portfolio",
]
