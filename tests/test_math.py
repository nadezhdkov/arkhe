"""
tests/test_math.py
------------------
Suite de testes para nestifypy.math.

Cobre todos os módulos:
  - _types   : Number, BigNumber, BigDecimal, Fraction, Complex, FailureResult
  - _engine  : Math (eval, estatística, financeiro, probabilidade, métodos numéricos)
  - _linalg  : Vector, Matrix
  - _geometry: Circle, Rectangle, Triangle, Sphere, Cylinder
  - _units   : Distance, Weight, Temperature, Duration
  - _money   : Money v2, Currency, CryptoPrice, Portfolio

Execução
--------
::

    pytest tests/test_math.py -v
    pytest tests/test_math.py -v --tb=short
"""

from __future__ import annotations

import math
import time
import json
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Imports do módulo
# ---------------------------------------------------------------------------

from nestifypy.math._types import (
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
from nestifypy.math._engine import Math
from nestifypy.math._linalg import Vector, Matrix
from nestifypy.math._geometry import Circle, Rectangle, Triangle, Sphere, Cylinder
from nestifypy.math._units import Distance, Weight, Temperature, Duration
from nestifypy.math._money import Money, Currency, Portfolio, _FALLBACK_RATES_FROM_USD, _cache


# ===========================================================================
# _types — Number
# ===========================================================================

class TestNumber:
    def test_int_input(self):
        assert Number(10).value() == 10

    def test_float_converts_to_decimal(self):
        n = Number(0.1)
        assert isinstance(n.value(), Decimal)

    def test_string_integer(self):
        assert Number("42").value() == 42

    def test_string_decimal(self):
        n = Number("19.99")
        assert n.value() == Decimal("19.99")

    def test_string_fraction(self):
        from fractions import Fraction as StdFraction
        n = Number("1/3")
        assert isinstance(n.value(), StdFraction)

    def test_add(self):
        result = Number("0.1").add(Number("0.2"))
        # Deve ser exato, sem imprecisão float
        assert result.value() == Decimal("0.3")

    def test_subtract(self):
        assert Number(10).subtract(3).value() == 7

    def test_multiply(self):
        assert Number("19.99").multiply("0.17").to_float() == pytest.approx(3.3983, rel=1e-4)

    def test_divide(self):
        assert Number(10).divide(4).to_float() == pytest.approx(2.5)

    def test_divide_by_zero_returns_failure(self):
        result = Number(10).divide(0)
        assert isinstance(result, FailureResult)
        assert result.is_failure()

    def test_pow(self):
        assert Number(2).pow(10).value() == 1024

    def test_negate(self):
        assert Number(5).negate().value() == -5

    def test_abs(self):
        assert Number(-7).abs().value() == 7

    def test_mod(self):
        assert Number(10).mod(3).value() == 1

    def test_mod_by_zero_returns_failure(self):
        result = Number(10).mod(0)
        assert isinstance(result, FailureResult)

    def test_to_int(self):
        assert Number("3.7").to_int() == 3

    def test_to_float(self):
        assert Number("2.5").to_float() == 2.5

    def test_to_decimal(self):
        assert Number("1.5").to_decimal() == Decimal("1.5")

    def test_comparison_eq(self):
        assert Number(5) == Number(5)

    def test_comparison_lt(self):
        assert Number(3) < Number(5)

    def test_comparison_gt(self):
        assert Number(10) > Number(2)

    def test_comparison_le(self):
        assert Number(3) <= Number(3)
        assert Number(2) <= Number(3)

    def test_comparison_ge(self):
        assert Number(5) >= Number(5)
        assert Number(6) >= Number(5)

    def test_operator_add(self):
        assert (Number(3) + Number(2)).value() == 5

    def test_operator_sub(self):
        assert (Number(5) - Number(3)).value() == 2

    def test_operator_mul(self):
        assert (Number(4) * Number(3)).value() == 12

    def test_operator_truediv(self):
        assert (Number(10) / Number(2)).to_float() == 5.0

    def test_operator_pow(self):
        assert (Number(2) ** Number(8)).value() == 256

    def test_operator_neg(self):
        assert (-Number(5)).value() == -5

    def test_operator_abs(self):
        assert abs(Number(-9)).value() == 9

    def test_repr(self):
        assert "Number" in repr(Number(42))

    def test_str(self):
        assert str(Number(42)) == "42"

    def test_is_success(self):
        assert Number(1).is_success()
        assert not Number(1).is_failure()

    def test_chaining(self):
        # Usa Number() nos argumentos para evitar ambiguidade de coerção
        # (10 + 5) * 2 - 3 = 27
        result = (
            Number("10")
            .add(Number("5"))
            .multiply(Number("2"))
            .subtract(Number("3"))
        )
        assert result.to_int() == 27


# ===========================================================================
# _types — BigNumber
# ===========================================================================

class TestBigNumber:
    def test_large_integer(self):
        n = BigNumber("999999999999999999999999999999")
        assert n.value() == 999999999999999999999999999999

    def test_pow_large(self):
        result = BigNumber(2).pow(100)
        assert result.value() == 2 ** 100

    def test_factorial(self):
        assert BigNumber(10).factorial().value() == 3628800

    def test_gcd(self):
        assert BigNumber(48).gcd(18).value() == 6

    def test_lcm(self):
        assert BigNumber(4).lcm(6).value() == 12

    def test_is_prime_true(self):
        assert BigNumber(97).is_prime()

    def test_is_prime_false(self):
        assert not BigNumber(100).is_prime()

    def test_digits(self):
        assert BigNumber(12345).digits() == 5

    def test_add(self):
        a = BigNumber("1" + "0" * 30)
        b = BigNumber("1")
        assert (a + b).value() == int("1" + "0" * 30) + 1

    def test_divide_by_zero(self):
        result = BigNumber(10).divide(0)
        assert isinstance(result, FailureResult)


# ===========================================================================
# _types — BigDecimal
# ===========================================================================

class TestBigDecimal:
    def test_precision_no_float_error(self):
        a = BigDecimal("0.1")
        b = BigDecimal("0.2")
        result = a.add(b)
        assert result.value() == Decimal("0.3")

    def test_multiply(self):
        result = BigDecimal("19.99").multiply("0.17")
        assert result.to_float() == pytest.approx(3.3983, rel=1e-4)

    def test_divide(self):
        result = BigDecimal("10").divide("4")
        assert result.to_float() == pytest.approx(2.5)

    def test_divide_by_zero(self):
        result = BigDecimal("10").divide("0")
        assert isinstance(result, FailureResult)

    def test_round(self):
        assert BigDecimal("3.14159").round(2).value() == Decimal("3.14")

    def test_floor(self):
        assert BigDecimal("3.9").floor().value() == Decimal("3")

    def test_ceil(self):
        assert BigDecimal("3.1").ceil().value() == Decimal("4")

    def test_from_decimal(self):
        d = Decimal("1.23456")
        assert BigDecimal(d).value() == d

    def test_from_numeric_base(self):
        n = Number("5.5")
        bd = BigDecimal(n)
        assert bd.to_float() == pytest.approx(5.5)

    def test_to_decimal(self):
        assert isinstance(BigDecimal("1.5").to_decimal(), Decimal)

    def test_is_success(self):
        assert BigDecimal("1").is_success()


# ===========================================================================
# _types — Fraction
# ===========================================================================

class TestFraction:
    def test_from_string(self):
        f = Fraction("1/3")
        assert f.numerator == 1
        assert f.denominator == 3

    def test_add_exact(self):
        result = Fraction("1/3").add("1/6")
        assert result.to_float() == pytest.approx(0.5)

    def test_multiply(self):
        assert Fraction("2/3").multiply("3/4").to_float() == pytest.approx(0.5)

    def test_to_mixed(self):
        whole, rem = Fraction("7/3").to_mixed()
        assert whole == 2
        assert rem.to_float() == pytest.approx(1 / 3)

    def test_simplify(self):
        f = Fraction("4/8")
        assert f.numerator == 1
        assert f.denominator == 2

    def test_comparison(self):
        assert Fraction("1/2") > Fraction("1/3")
        assert Fraction("1/4") < Fraction("1/3")


# ===========================================================================
# _types — Complex
# ===========================================================================

class TestComplex:
    def test_creation(self):
        c = Complex(3, 4)
        assert c.real == 3.0
        assert c.imag == 4.0

    def test_magnitude(self):
        assert Complex(3, 4).magnitude().to_float() == pytest.approx(5.0)

    def test_conjugate(self):
        c = Complex(2, 5).conjugate()
        assert c.real == 2.0
        assert c.imag == -5.0

    def test_phase(self):
        import cmath
        c = Complex(1, 0)
        assert c.phase().to_float() == pytest.approx(cmath.phase(complex(1, 0)))

    def test_add(self):
        result = Complex(1, 2).add(Complex(3, 4))
        assert result.real == pytest.approx(4.0)
        assert result.imag == pytest.approx(6.0)

    def test_multiply(self):
        # (1+2j) * (3+4j) = 3+4j+6j+8j² = -5+10j
        result = Complex(1, 2).multiply(Complex(3, 4))
        assert result.real == pytest.approx(-5.0)
        assert result.imag == pytest.approx(10.0)


# ===========================================================================
# _types — FailureResult
# ===========================================================================

class TestFailureResult:
    def test_is_failure(self):
        fr = FailureResult(DivisionByZeroError("div/0"))
        assert fr.is_failure()
        assert not fr.is_success()

    def test_get_error(self):
        err = DivisionByZeroError("oops")
        fr = FailureResult(err)
        assert fr.get_error() is err

    def test_operations_propagate(self):
        fr = FailureResult(DivisionByZeroError("x"))
        assert fr.add(1).is_failure()
        assert fr.multiply(2).is_failure()
        assert fr.subtract(1).is_failure()
        assert fr.divide(1).is_failure()

    def test_to_float_raises(self):
        fr = FailureResult(DivisionByZeroError("x"))
        with pytest.raises(DivisionByZeroError):
            fr.to_float()

    def test_repr(self):
        fr = FailureResult(DivisionByZeroError("x"))
        assert "FailureResult" in repr(fr)


# ===========================================================================
# _engine — Math
# ===========================================================================

class TestMathEval:
    def test_simple_arithmetic(self):
        assert Math.eval("2 + 3") == 5

    def test_parentheses(self):
        assert Math.eval("(15 + 8) * sqrt(144)") == 276

    def test_variable_substitution(self):
        assert Math.eval("x * y + 10", x=5, y=3) == 25

    def test_pi_constant(self):
        result = Math.eval("pi * 2")
        assert result == pytest.approx(math.pi * 2)

    def test_e_constant(self):
        result = Math.eval("e")
        assert result == pytest.approx(math.e)

    def test_sqrt(self):
        assert Math.eval("sqrt(9)") == 3

    def test_pow(self):
        assert Math.eval("pow(2, 10)") == 1024

    def test_floor_division(self):
        assert Math.eval("10 // 3") == 3

    def test_modulo(self):
        assert Math.eval("10 % 3") == 1

    def test_unary_minus(self):
        assert Math.eval("-5 + 10") == 5

    def test_trig_sin(self):
        assert Math.eval("sin(0)") == pytest.approx(0.0)

    def test_trig_cos(self):
        assert Math.eval("cos(0)") == pytest.approx(1.0)

    def test_log(self):
        assert Math.eval("log(1)") == pytest.approx(0.0)

    def test_log10(self):
        assert Math.eval("log10(1000)") == pytest.approx(3.0)

    def test_exp(self):
        assert Math.eval("exp(0)") == pytest.approx(1.0)

    def test_abs(self):
        assert Math.eval("abs(-42)") == 42

    def test_invalid_expression_raises(self):
        with pytest.raises((ValueError, NameError)):
            Math.eval("import os")

    def test_unknown_name_raises(self):
        with pytest.raises(NameError):
            Math.eval("undefined_var")

    def test_division_by_zero_raises(self):
        with pytest.raises(ZeroDivisionError):
            Math.eval("1 / 0")

    def test_returns_int_when_possible(self):
        result = Math.eval("4.0 + 6.0")
        assert isinstance(result, int)
        assert result == 10

    def test_nested_functions(self):
        result = Math.eval("sqrt(pow(3, 2) + pow(4, 2))")
        assert result == pytest.approx(5.0)


class TestMathStats:
    DATA = [2, 4, 4, 4, 5, 5, 7, 9]

    def test_mean(self):
        assert Math.mean(self.DATA) == pytest.approx(5.0)

    def test_median(self):
        assert Math.median(self.DATA) == pytest.approx(4.5)

    def test_mode(self):
        assert Math.mode(self.DATA) == 4

    def test_variance(self):
        assert Math.variance(self.DATA) == pytest.approx(4.571428, rel=1e-4)

    def test_std(self):
        assert Math.std(self.DATA) == pytest.approx(2.13809, rel=1e-4)

    def test_pvariance(self):
        assert Math.pvariance(self.DATA) == pytest.approx(4.0, rel=1e-4)

    def test_pstd(self):
        assert Math.pstd(self.DATA) == pytest.approx(2.0, rel=1e-4)

    def test_quantiles(self):
        q = Math.quantiles(self.DATA)
        assert len(q) == 3


class TestMathScientific:
    def test_pi_digits(self):
        pi = Math.pi(precision=20)
        assert float(pi) == pytest.approx(math.pi, rel=1e-10)

    def test_sqrt_precision(self):
        result = Math.sqrt(2)
        assert float(result) == pytest.approx(math.sqrt(2), rel=1e-10)

    def test_sqrt_high_precision(self):
        result = Math.sqrt(2, precision=30)
        assert float(result) == pytest.approx(math.sqrt(2), rel=1e-10)

    def test_newton_simple_root(self):
        # f(x) = x^2 - 4 → raiz em x = 2
        root = Math.newton(lambda x: x**2 - 4, x0=1.0)
        assert root == pytest.approx(2.0, rel=1e-6)

    def test_bisection(self):
        root = Math.bisection(lambda x: x**2 - 4, a=0, b=3)
        assert root == pytest.approx(2.0, rel=1e-6)

    def test_secant(self):
        root = Math.secant(lambda x: x**2 - 4, x0=1.0, x1=3.0)
        assert root == pytest.approx(2.0, rel=1e-6)

    def test_bisection_invalid_raises(self):
        with pytest.raises(ValueError):
            Math.bisection(lambda x: x**2 + 1, a=0, b=2)  # sem raiz real


class TestMathFinancial:
    def test_compound_interest(self):
        # 1000 a 5% ao ano por 3 anos
        result = Math.compound_interest(1000, 0.05, 3)
        assert result == pytest.approx(1157.625, rel=1e-4)

    def test_compound_interest_monthly(self):
        # capitalização mensal
        result = Math.compound_interest(1000, 0.12, 1, n=12)
        assert result == pytest.approx(1126.825, rel=1e-3)

    def test_simple_interest(self):
        # 1000 a 5% por 2 anos = 1100
        assert Math.simple_interest(1000, 0.05, 2) == pytest.approx(1100.0)

    def test_loan_monthly_payment(self):
        result = Math.loan(100_000, 0.12, 360)
        assert result["monthly_payment"] == pytest.approx(1028.61, rel=1e-3)
        assert result["total_paid"] > 100_000

    def test_loan_zero_rate(self):
        result = Math.loan(12_000, 0.0, 12)
        assert result["monthly_payment"] == pytest.approx(1000.0)
        assert result["total_interest"] == pytest.approx(0.0)

    def test_present_value(self):
        pv = Math.present_value(1000, 0.1, 1)
        assert pv == pytest.approx(909.09, rel=1e-3)

    def test_future_value(self):
        fv = Math.future_value(1000, 0.1, 1)
        assert fv == pytest.approx(1100.0, rel=1e-4)


class TestMathCombinatorics:
    def test_combinations(self):
        assert Math.combinations(5, 2) == 10

    def test_permutations(self):
        assert Math.permutations(5, 2) == 20

    def test_factorial(self):
        assert Math.factorial(6) == 720

    def test_gcd(self):
        assert Math.gcd(48, 18) == 6

    def test_lcm(self):
        assert Math.lcm(4, 6) == 12

    def test_probability(self):
        assert Math.probability(3, 6) == pytest.approx(0.5)

    def test_probability_zero_total_raises(self):
        with pytest.raises(ValueError):
            Math.probability(1, 0)


# ===========================================================================
# _linalg — Vector
# ===========================================================================

class TestVector:
    def test_creation(self):
        v = Vector(1, 2, 3)
        assert len(v) == 3

    def test_length(self):
        assert Vector(3, 4).length() == pytest.approx(5.0)

    def test_normalize(self):
        n = Vector(3, 4).normalize()
        assert n.length() == pytest.approx(1.0)

    def test_normalize_zero_raises(self):
        with pytest.raises(ValueError):
            Vector(0, 0, 0).normalize()

    def test_dot_product(self):
        v1 = Vector(1, 2, 3)
        v2 = Vector(4, 5, 6)
        assert v1.dot(v2) == pytest.approx(32.0)

    def test_cross_product(self):
        v1 = Vector(1, 0, 0)
        v2 = Vector(0, 1, 0)
        cross = v1.cross(v2)
        assert cross[0] == pytest.approx(0.0)
        assert cross[1] == pytest.approx(0.0)
        assert cross[2] == pytest.approx(1.0)

    def test_cross_non_3d_raises(self):
        with pytest.raises(ValueError):
            Vector(1, 2).cross(Vector(3, 4))

    def test_angle_with(self):
        v1 = Vector(1, 0)
        v2 = Vector(0, 1)
        assert v1.angle_with(v2) == pytest.approx(math.pi / 2)

    def test_projection(self):
        v1 = Vector(3, 4)
        v2 = Vector(1, 0)
        proj = v1.project_onto(v2)
        assert proj[0] == pytest.approx(3.0)
        assert proj[1] == pytest.approx(0.0)

    def test_add(self):
        result = Vector(1, 2) + Vector(3, 4)
        assert result[0] == pytest.approx(4.0)
        assert result[1] == pytest.approx(6.0)

    def test_sub(self):
        result = Vector(5, 3) - Vector(2, 1)
        assert result[0] == pytest.approx(3.0)

    def test_scalar_mul(self):
        result = Vector(1, 2, 3) * 2
        assert list(result) == pytest.approx([2.0, 4.0, 6.0])

    def test_scalar_div(self):
        result = Vector(4, 6) / 2
        assert list(result) == pytest.approx([2.0, 3.0])

    def test_div_by_zero_raises(self):
        with pytest.raises(ZeroDivisionError):
            Vector(1, 2) / 0

    def test_neg(self):
        result = -Vector(1, -2)
        assert list(result) == pytest.approx([-1.0, 2.0])

    def test_equality(self):
        assert Vector(1, 2, 3) == Vector(1, 2, 3)
        assert Vector(1, 2) != Vector(1, 3)

    def test_dimension_mismatch(self):
        with pytest.raises(ValueError):
            Vector(1, 2).dot(Vector(1, 2, 3))

    def test_to_list(self):
        assert Vector(1, 2, 3).to_list() == [1.0, 2.0, 3.0]

    def test_dimensions_property(self):
        assert Vector(1, 2, 3, 4).dimensions == 4

    def test_from_list(self):
        v = Vector([1, 2, 3])
        assert len(v) == 3


# ===========================================================================
# _linalg — Matrix
# ===========================================================================

class TestMatrix:
    M2 = [[1, 2], [3, 4]]
    M3 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    def test_creation(self):
        m = Matrix(self.M2)
        assert m.rows == 2
        assert m.cols == 2

    def test_is_square(self):
        assert Matrix(self.M2).is_square()
        assert not Matrix([[1, 2, 3]]).is_square()

    def test_transpose(self):
        t = Matrix(self.M2).transpose()
        assert t[0][0] == 1.0
        assert t[0][1] == 3.0
        assert t[1][0] == 2.0

    def test_determinant_2x2(self):
        assert Matrix(self.M2).determinant() == pytest.approx(-2.0)

    def test_determinant_3x3(self):
        # Matriz singular (det=0)
        assert Matrix(self.M3).determinant() == pytest.approx(0.0, abs=1e-9)

    def test_inverse(self):
        m = Matrix(self.M2)
        inv = m.inverse()
        identity = m * inv
        for i in range(2):
            for j in range(2):
                expected = 1.0 if i == j else 0.0
                assert identity[i][j] == pytest.approx(expected, abs=1e-9)

    def test_inverse_singular_raises(self):
        with pytest.raises(ValueError):
            Matrix(self.M3).inverse()

    def test_trace(self):
        assert Matrix(self.M2).trace() == pytest.approx(5.0)

    def test_add(self):
        m1 = Matrix([[1, 0], [0, 1]])
        m2 = Matrix([[2, 3], [4, 5]])
        result = m1 + m2
        assert result[0][0] == pytest.approx(3.0)

    def test_sub(self):
        m1 = Matrix([[5, 3], [2, 1]])
        m2 = Matrix([[1, 1], [1, 1]])
        result = m1 - m2
        assert result[0][0] == pytest.approx(4.0)

    def test_mul_scalar(self):
        m = Matrix([[1, 2], [3, 4]]) * 2
        assert m[0][1] == pytest.approx(4.0)

    def test_mul_matrix(self):
        a = Matrix([[1, 2], [3, 4]])
        b = Matrix([[5, 6], [7, 8]])
        c = a * b
        assert c[0][0] == pytest.approx(19.0)
        assert c[1][1] == pytest.approx(50.0)

    def test_mul_incompatible_raises(self):
        with pytest.raises(ValueError):
            Matrix([[1, 2]]) * Matrix([[1, 2]])

    def test_identity(self):
        i = Matrix.identity(3)
        assert i[0][0] == 1.0
        assert i[0][1] == 0.0
        assert i[2][2] == 1.0

    def test_zeros(self):
        z = Matrix.zeros(2, 3)
        assert z.rows == 2
        assert z.cols == 3
        assert z[0][0] == 0.0

    def test_unequal_row_lengths_raises(self):
        with pytest.raises(ValueError):
            Matrix([[1, 2], [3]])

    def test_to_list(self):
        m = Matrix([[1, 2], [3, 4]])
        assert m.to_list() == [[1.0, 2.0], [3.0, 4.0]]


# ===========================================================================
# _geometry
# ===========================================================================

class TestCircle:
    def test_area(self):
        assert Circle(5).area() == pytest.approx(math.pi * 25)

    def test_circumference(self):
        assert Circle(1).circumference() == pytest.approx(2 * math.pi)

    def test_diameter(self):
        assert Circle(4).diameter() == pytest.approx(8.0)

    def test_scale(self):
        assert Circle(3).scale(2).radius == pytest.approx(6.0)

    def test_negative_radius_raises(self):
        with pytest.raises(ValueError):
            Circle(-1)

    def test_repr(self):
        assert "Circle" in repr(Circle(5))


class TestRectangle:
    def test_area(self):
        assert Rectangle(10, 20).area() == pytest.approx(200.0)

    def test_perimeter(self):
        assert Rectangle(10, 20).perimeter() == pytest.approx(60.0)

    def test_diagonal(self):
        assert Rectangle(3, 4).diagonal() == pytest.approx(5.0)

    def test_is_square_true(self):
        assert Rectangle(5, 5).is_square()

    def test_is_square_false(self):
        assert not Rectangle(5, 6).is_square()

    def test_scale(self):
        r = Rectangle(3, 4).scale(2)
        assert r.width == pytest.approx(6.0)
        assert r.height == pytest.approx(8.0)

    def test_negative_dimensions_raises(self):
        with pytest.raises(ValueError):
            Rectangle(-1, 5)


class TestTriangle:
    def test_area_base_height(self):
        assert Triangle(base=10, height=5).area() == pytest.approx(25.0)

    def test_area_heron(self):
        # Triângulo 3-4-5 — área = 6
        assert Triangle(a=3, b=4, c=5).area() == pytest.approx(6.0)

    def test_perimeter(self):
        assert Triangle(a=3, b=4, c=5).perimeter() == pytest.approx(12.0)

    def test_hypotenuse(self):
        assert Triangle(a=3, b=4).hypotenuse() == pytest.approx(5.0)

    def test_is_right_true(self):
        assert Triangle(a=3, b=4, c=5).is_right()

    def test_is_right_false(self):
        assert not Triangle(a=3, b=4, c=6).is_right()

    def test_invalid_sides_raises(self):
        with pytest.raises(ValueError):
            Triangle(a=1, b=2, c=10)

    def test_area_no_data_raises(self):
        with pytest.raises(ValueError):
            Triangle().area()

    def test_perimeter_no_sides_raises(self):
        with pytest.raises(ValueError):
            Triangle(base=5, height=3).perimeter()


class TestSphere:
    def test_volume(self):
        expected = (4 / 3) * math.pi * 27
        assert Sphere(3).volume() == pytest.approx(expected)

    def test_surface_area(self):
        expected = 4 * math.pi * 9
        assert Sphere(3).surface_area() == pytest.approx(expected)


class TestCylinder:
    def test_volume(self):
        expected = math.pi * 4 * 10
        assert Cylinder(2, 10).volume() == pytest.approx(expected)

    def test_surface_area(self):
        expected = 2 * math.pi * 2 * (2 + 10)
        assert Cylinder(2, 10).surface_area() == pytest.approx(expected)


# ===========================================================================
# _units
# ===========================================================================

class TestDistance:
    def test_km_to_m(self):
        assert Distance("10km").to("m") == pytest.approx(10_000.0)

    def test_m_to_km(self):
        assert Distance("1000m").to("km") == pytest.approx(1.0)

    def test_mi_to_km(self):
        assert Distance("1mi").to("km") == pytest.approx(1.609344, rel=1e-4)

    def test_ft_to_m(self):
        assert Distance("1ft").to("m") == pytest.approx(0.3048)

    def test_in_to_cm(self):
        assert Distance("1in").to("cm") == pytest.approx(2.54, rel=1e-4)

    def test_unknown_unit_raises(self):
        with pytest.raises(ValueError):
            Distance("10km").to("parsec")

    def test_from_float(self):
        assert Distance(1.0, "km").to("m") == pytest.approx(1000.0)


class TestWeight:
    def test_kg_to_lb(self):
        assert Weight("1kg").to("lb") == pytest.approx(2.20462, rel=1e-4)

    def test_lb_to_kg(self):
        assert Weight("1lb").to("kg") == pytest.approx(0.453592, rel=1e-4)

    def test_g_to_kg(self):
        assert Weight("1000g").to("kg") == pytest.approx(1.0)

    def test_oz_to_g(self):
        assert Weight("1oz").to("g") == pytest.approx(28.3495, rel=1e-3)

    def test_t_to_kg(self):
        assert Weight("1t").to("kg") == pytest.approx(1000.0)

    def test_unknown_unit_raises(self):
        with pytest.raises(ValueError):
            Weight("1kg").to("furlongs")


class TestTemperature:
    def test_c_to_f(self):
        assert Temperature("0C").to("F") == pytest.approx(32.0)

    def test_f_to_c(self):
        assert Temperature("32F").to("C") == pytest.approx(0.0)

    def test_c_to_k(self):
        assert Temperature("0C").to("K") == pytest.approx(273.15)

    def test_k_to_c(self):
        assert Temperature("273.15K").to("C") == pytest.approx(0.0)

    def test_boiling_point(self):
        assert Temperature("100C").to("F") == pytest.approx(212.0)

    def test_absolute_zero(self):
        assert Temperature("0K").to("C") == pytest.approx(-273.15)

    def test_unknown_unit_raises(self):
        with pytest.raises(ValueError):
            Temperature("100C").to("X")


class TestDuration:
    def test_hours_to_seconds(self):
        assert Duration("2h").to("s") == pytest.approx(7200.0)

    def test_compound(self):
        assert Duration("2h 30m").to("s") == pytest.approx(9000.0)

    def test_compound_full(self):
        assert Duration("1d 4h 30m 15s").to("s") == pytest.approx(
            86400 + 14400 + 1800 + 15
        )

    def test_days_to_hours(self):
        assert Duration("1d").to("h") == pytest.approx(24.0)

    def test_minutes_to_hours(self):
        assert Duration(90, "min").to("h") == pytest.approx(1.5)

    def test_ms_to_s_explicit_unit(self):
        assert Duration(500, "ms").to("s") == pytest.approx(0.5)

    def test_ms_to_s_string(self):
        # Antes do fix o parser cortava "ms" → "m" (minutos); agora funciona corretamente
        assert Duration("500ms").to("s") == pytest.approx(0.5)

    def test_ms_compound(self):
        # Composto com milissegundos via string
        assert Duration("2h 30m 200ms").to("s") == pytest.approx(9000.2)

    def test_us_to_s(self):
        assert Duration("5us").to("s") == pytest.approx(5e-6)

    def test_weeks_to_days(self):
        assert Duration("1w").to("d") == pytest.approx(7.0)

    def test_unknown_unit_raises(self):
        with pytest.raises((ValueError, KeyError)):
            Duration("1h").to("fortnight")


# ===========================================================================
# _money — Currency
# ===========================================================================

class TestCurrency:
    def test_fiat_constants(self):
        assert Currency.USD == "USD"
        assert Currency.BRL == "BRL"
        assert Currency.EUR == "EUR"
        assert Currency.JPY == "JPY"
        assert Currency.GBP == "GBP"

    def test_crypto_constants(self):
        assert Currency.BTC  == "BTC"
        assert Currency.ETH  == "ETH"
        assert Currency.SOL  == "SOL"
        assert Currency.USDT == "USDT"
        assert Currency.USDC == "USDC"
        assert Currency.DOGE == "DOGE"


# ===========================================================================
# _money — Money v2 (sem rede — usa fallback estático)
# ===========================================================================

def _force_fallback():
    """Força o Money a usar taxas de fallback (sem rede, sem cache)."""
    _cache._rates = {}
    _cache._fetched_at = None


@pytest.fixture(autouse=True)
def reset_money_cache():
    """Reseta o cache antes de cada teste de Money."""
    _force_fallback()
    yield
    _force_fallback()


class TestMoneyCreation:
    def test_from_string(self):
        m = Money("19.99", "USD")
        assert isinstance(m.amount(), BigDecimal)
        assert m.currency() == "USD"

    def test_from_int(self):
        m = Money(100, "BRL")
        assert m.amount().to_float() == pytest.approx(100.0)

    def test_from_float(self):
        m = Money(9.99, "EUR")
        assert m.amount().to_float() == pytest.approx(9.99, rel=1e-4)

    def test_from_decimal(self):
        m = Money(Decimal("50.00"), "USD")
        assert m.amount().to_decimal() == Decimal("50.00")

    def test_from_bigdecimal(self):
        bd = BigDecimal("25.50")
        m = Money(bd, "USD")
        assert m.amount() is bd

    def test_currency_uppercased(self):
        assert Money("10", "usd").currency() == "USD"

    def test_from_currency_constant(self):
        m = Money(100, Currency.USD)
        assert m.currency() == "USD"


class TestMoneyConversion:
    def test_same_currency(self):
        m = Money("100", "USD")
        result = m.to("USD")
        assert result.amount().to_float() == pytest.approx(100.0)

    def test_usd_to_brl(self):
        m = Money("100", "USD")
        result = m.to("BRL")
        assert result.currency() == "BRL"
        # Deriva o expected pelo mesmo pipeline BigDecimal que Money usa internamente
        rates = Money._get_rates()
        usd_rate = rates["USD"]
        brl_rate = rates["BRL"]
        expected = BigDecimal("100").divide(usd_rate).multiply(brl_rate)
        assert result.amount().to_float() == pytest.approx(expected.to_float(), rel=1e-6)

    def test_brl_to_usd(self):
        # Converte 100 BRL para USD e verifica o resultado pelo mesmo pipeline
        m = Money("100", "BRL")
        result = m.to("USD")
        assert result.currency() == "USD"
        rates = Money._get_rates()
        brl_rate = rates["BRL"]
        usd_rate = rates["USD"]
        expected = BigDecimal("100").divide(brl_rate).multiply(usd_rate)
        assert result.amount().to_float() == pytest.approx(expected.to_float(), rel=1e-6)

    def test_eur_to_jpy(self):
        m = Money("100", "EUR")
        result = m.to("JPY")
        assert result.currency() == "JPY"
        # Deve ser > 100 (JPY é muito menor que EUR)
        assert result.amount().to_float() > 100

    def test_unknown_from_currency_raises(self):
        with pytest.raises(ValueError):
            Money("10", "XYZ").to("USD")

    def test_unknown_to_currency_raises(self):
        with pytest.raises(ValueError):
            Money("10", "USD").to("XYZ")

    def test_chain_conversion(self):
        # USD → BRL → USD deve aproximar o valor original
        original = Money("100", "USD")
        result = original.to("BRL").to("USD")
        assert result.amount().to_float() == pytest.approx(100.0, rel=1e-4)

    def test_crypto_usd_to_btc(self):
        m = Money("1", "USD")
        btc = m.to("BTC")
        assert btc.currency() == "BTC"
        assert btc.amount().to_float() > 0

    def test_btc_to_usd(self):
        m = Money("1", "BTC")
        result = m.to("USD")
        assert result.currency() == "USD"
        rates = Money._get_rates()
        btc_rate = rates["BTC"]
        usd_rate = rates["USD"]
        expected = BigDecimal("1").divide(btc_rate).multiply(usd_rate)
        assert result.amount().to_float() == pytest.approx(expected.to_float(), rel=1e-6)


class TestMoneyArithmetic:
    def test_add_same_currency(self):
        result = Money("10", "USD").add(Money("5", "USD"))
        assert result.amount().to_float() == pytest.approx(15.0)
        assert result.currency() == "USD"

    def test_add_different_currency(self):
        # Soma USD + USD (convertido de BRL)
        usd = Money("100", "USD")
        brl = Money("0", "BRL")  # 0 BRL = 0 USD
        result = usd.add(brl)
        assert result.amount().to_float() == pytest.approx(100.0, rel=1e-4)

    def test_subtract(self):
        result = Money("20", "USD").subtract(Money("5", "USD"))
        assert result.amount().to_float() == pytest.approx(15.0)

    def test_multiply_by_scalar(self):
        result = Money("100", "USD").multiply("0.17")
        assert result.amount().to_float() == pytest.approx(17.0)

    def test_multiply_int(self):
        result = Money("50", "BRL").multiply(3)
        assert result.amount().to_float() == pytest.approx(150.0)

    def test_divide(self):
        result = Money("100", "USD").divide("4")
        assert result.amount().to_float() == pytest.approx(25.0)

    def test_divide_by_zero_returns_failure(self):
        result = Money("100", "USD").divide("0")
        assert isinstance(result, FailureResult)

    def test_ratio_same_currency(self):
        ratio = Money("100", "USD").ratio(Money("25", "USD"))
        assert ratio.to_float() == pytest.approx(4.0)

    def test_ratio_different_currency(self):
        # Money("100", "USD").ratio(Money("100", "USD")) deve ser exatamente 1.0
        ratio = Money("100", "USD").ratio(Money("100", "USD"))
        assert ratio.to_float() == pytest.approx(1.0, rel=1e-6)

    def test_operator_add(self):
        result = Money("10", "USD") + Money("5", "USD")
        assert result.amount().to_float() == pytest.approx(15.0)

    def test_operator_sub(self):
        result = Money("10", "USD") - Money("3", "USD")
        assert result.amount().to_float() == pytest.approx(7.0)

    def test_operator_mul(self):
        result = Money("10", "USD") * 2
        assert result.amount().to_float() == pytest.approx(20.0)

    def test_operator_rmul(self):
        result = 3 * Money("10", "USD")
        assert result.amount().to_float() == pytest.approx(30.0)

    def test_operator_div(self):
        result = Money("20", "USD") / 4
        assert result.amount().to_float() == pytest.approx(5.0)

    def test_fluent_chain(self):
        # 100 * 0.17 + 10 - 5 = 22
        result = (
            Money("100", "USD")
            .multiply("0.17")
            .add(Money("10", "USD"))
            .subtract(Money("5", "USD"))
        )
        assert result.amount().to_float() == pytest.approx(22.0)


class TestMoneyRounding:
    def test_round(self):
        result = Money("19.999", "USD").round(2)
        assert result.amount().to_float() == pytest.approx(20.0, rel=1e-4)

    def test_floor(self):
        result = Money("19.9", "USD").floor()
        assert result.amount().to_int() == 19

    def test_ceil(self):
        result = Money("19.1", "USD").ceil()
        assert result.amount().to_int() == 20

    def test_round_preserves_currency(self):
        assert Money("1.235", "BRL").round(2).currency() == "BRL"


class TestMoneyComparisons:
    def test_eq_same_currency(self):
        assert Money("100", "USD") == Money("100", "USD")

    def test_neq_same_currency(self):
        assert Money("100", "USD") != Money("101", "USD")

    def test_lt_same_currency(self):
        assert Money("50", "USD") < Money("100", "USD")

    def test_gt_same_currency(self):
        assert Money("100", "USD") > Money("50", "USD")

    def test_le_same_currency(self):
        assert Money("50", "USD") <= Money("100", "USD")
        assert Money("100", "USD") <= Money("100", "USD")

    def test_ge_same_currency(self):
        assert Money("100", "USD") >= Money("50", "USD")
        assert Money("100", "USD") >= Money("100", "USD")

    def test_comparison_different_currencies(self):
        # 100 USD deve ser > 1 BRL (usando taxas de fallback)
        assert Money("100", "USD") > Money("1", "BRL")

    def test_zero_is_not_greater(self):
        assert not (Money("0", "USD") > Money("100", "USD"))


class TestMoneyFormatting:
    def test_str(self):
        s = str(Money("19.99", "USD"))
        assert "USD" in s
        assert "19.99" in s

    def test_repr(self):
        r = repr(Money("10", "USD"))
        assert "Money" in r
        assert "USD" in r

    def test_format_en_us(self):
        result = Money("1234.56", "USD").format(locale="en_US")
        assert "$" in result
        assert "1,234.56" in result

    def test_format_pt_br(self):
        result = Money("1234.56", "BRL").format(locale="pt_BR")
        assert "R$" in result
        assert "1.234,56" in result

    def test_format_de_de(self):
        result = Money("1234.56", "EUR").format(locale="de_DE")
        assert "€" in result
        assert "1.234,56" in result

    def test_format_decimal_places(self):
        result = Money("10", "USD").format(decimal_places=4, locale="en_US")
        assert "10.0000" in result

    def test_to_float(self):
        assert Money("9.99", "USD").to_float() == pytest.approx(9.99)

    def test_to_decimal(self):
        assert Money("9.99", "USD").to_decimal() == Decimal("9.99")


class TestMoneyCache:
    def test_cache_max_age(self):
        # Não deve lançar exceção
        Money.cache(hours=6)

    def test_cache_stores_bigdecimal(self):
        rates = Money._get_rates()
        for key, val in rates.items():
            assert isinstance(val, BigDecimal), f"{key} não é BigDecimal"

    def test_persistent_cache_roundtrip(self, tmp_path, monkeypatch):
        """Cache em disco: salva e recarrega corretamente."""
        from nestifypy.math import _money as money_module
        monkeypatch.setattr(money_module, "_CACHE_DIR", tmp_path)
        monkeypatch.setattr(money_module, "_CACHE_FILE", tmp_path / "currency.json")

        rates = {k: BigDecimal(v) for k, v in list(_FALLBACK_RATES_FROM_USD.items())[:5]}
        _cache._max_age_seconds = 3600
        _cache.store(rates)

        # Simula reinício: zera cache em memória
        _cache._rates = {}
        _cache._fetched_at = None
        _cache._fetched_at = None

        loaded = _cache.load_from_disk()
        assert loaded
        assert "USD" in _cache.get_rates()

    def test_disk_cache_expired(self, tmp_path, monkeypatch):
        """Cache expirado não deve ser carregado."""
        from nestifypy.math import _money as money_module
        cache_file = tmp_path / "currency.json"
        monkeypatch.setattr(money_module, "_CACHE_DIR", tmp_path)
        monkeypatch.setattr(money_module, "_CACHE_FILE", cache_file)

        old_payload = {
            "fetched_at": time.time() - 99999,
            "base": "USD",
            "rates": {"USD": "1.0"},
        }
        cache_file.write_text(json.dumps(old_payload))

        _cache._rates = {}
        _cache._fetched_at = None
        _cache._max_age_seconds = 3600

        loaded = _cache.load_from_disk()
        assert not loaded


class TestMoneyFallbackRates:
    def test_no_float_in_fallback(self):
        """Todas as taxas de fallback devem ser strings, não floats."""
        for symbol, rate in _FALLBACK_RATES_FROM_USD.items():
            assert isinstance(rate, str), f"{symbol}: esperado str, recebeu {type(rate)}"

    def test_fallback_rates_convert_to_bigdecimal(self):
        for symbol, rate in _FALLBACK_RATES_FROM_USD.items():
            bd = BigDecimal(rate)
            assert bd.to_float() > 0, f"Taxa de {symbol} deve ser positiva"


class TestMoneyConversionLog:
    def test_enable_log_flag(self):
        Money.enable_conversion_log(True)
        assert Money._log_conversions is True
        Money.enable_conversion_log(False)
        assert Money._log_conversions is False


class TestMoneyAutoNet:
    def test_set_fetcher_manually(self):
        mock_fetcher = MagicMock()
        Money.set_fetcher(mock_fetcher)
        assert Money._fetcher is mock_fetcher
        Money._fetcher = None  # restaura


# ===========================================================================
# _money — Portfolio
# ===========================================================================

class TestPortfolio:
    def test_add_and_len(self):
        p = Portfolio()
        p.add(Money("100", "USD"))
        p.add(Money("50", "USD"))
        assert len(p) == 2

    def test_total_same_currency(self):
        p = Portfolio()
        p.add(Money("100", "USD"))
        p.add(Money("50", "USD"))
        total = p.total("USD")
        assert total.amount().to_float() == pytest.approx(150.0)
        assert total.currency() == "USD"

    def test_total_empty_portfolio(self):
        p = Portfolio()
        total = p.total("USD")
        assert total.amount().to_float() == pytest.approx(0.0)

    def test_total_different_currencies(self):
        p = Portfolio()
        p.add(Money("0", "BRL"))
        p.add(Money("100", "USD"))
        total = p.total("USD")
        assert total.amount().to_float() == pytest.approx(100.0, rel=1e-3)

    def test_remove(self):
        p = Portfolio()
        m = Money("100", "USD")
        p.add(m)
        p.add(Money("50", "USD"))
        p.remove(m)
        assert len(p) == 1

    def test_positions(self):
        p = Portfolio()
        m1 = Money("100", "USD")
        m2 = Money("200", "USD")
        p.add(m1).add(m2)
        pos = p.positions()
        assert len(pos) == 2

    def test_chaining(self):
        p = Portfolio()
        result = p.add(Money("10", "USD")).add(Money("20", "USD"))
        assert result is p
        assert len(p) == 2

    def test_summary_contains_total(self):
        p = Portfolio()
        p.add(Money("100", "USD"))
        summary = p.summary("USD")
        assert "Total" in summary
        assert "100" in summary

    def test_repr(self):
        p = Portfolio()
        p.add(Money("1", "USD"))
        assert "Portfolio" in repr(p)

    def test_total_converted_currency(self):
        p = Portfolio()
        p.add(Money("100", "USD"))
        total_brl = p.total("BRL")
        assert total_brl.currency() == "BRL"
        # Deriva o expected pelo mesmo pipeline BigDecimal que Money usa internamente
        rates = Money._get_rates()
        expected = BigDecimal("100").divide(rates["USD"]).multiply(rates["BRL"])
        assert total_brl.amount().to_float() == pytest.approx(expected.to_float(), rel=1e-6)


# ===========================================================================
# Integração — Math + tipos numéricos
# ===========================================================================

class TestIntegration:
    def test_number_with_math_eval(self):
        n = Number("5")
        result = Math.eval("x ** 2 + 2 * x + 1", x=n.to_int())
        assert result == 36

    def test_bigdecimal_precision_in_financial_calc(self):
        # 0.1 + 0.2 + 0.3 deve ser exatamente 0.6
        total = BigDecimal("0.1").add("0.2").add("0.3")
        assert total.value() == Decimal("0.6")

    def test_money_fluent_pipeline_precision(self):
        # Cálculo sem float: 100 * 0.17 + 10 - 5 = 22
        result = (
            Money("100", "USD")
            .multiply("0.17")
            .add(Money("10", "USD"))
            .subtract(Money("5", "USD"))
        )
        assert result.amount().to_float() == pytest.approx(22.0)

    def test_vector_math_eval_angle(self):
        v1 = Vector(1, 0)
        v2 = Vector(0, 1)
        angle_rad = v1.angle_with(v2)
        # Deve ser 90 graus
        result = Math.eval("degrees(angle)", angle=angle_rad)
        assert result == pytest.approx(90.0)

    def test_compound_interest_with_bigdecimal(self):
        principal = BigDecimal("1000")
        rate = BigDecimal("0.05")
        periods = 3
        # Compara resultado de Math.compound_interest com cálculo manual BigDecimal
        expected = Math.compound_interest(1000, 0.05, 3)
        manual = principal.multiply(
            BigDecimal("1").add(rate).pow(periods)
        )
        assert manual.to_float() == pytest.approx(expected, rel=1e-4)

    def test_portfolio_total_matches_manual_sum(self):
        amounts = ["100", "200", "50"]
        p = Portfolio()
        expected = 0.0
        for a in amounts:
            p.add(Money(a, "USD"))
            expected += float(a)
        total = p.total("USD")
        assert total.amount().to_float() == pytest.approx(expected)
