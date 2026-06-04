"""
arkhe.math._geometry
------------------------
Formas geométricas com API fluente.

::

    Circle(radius=5).area()
    Rectangle(10, 20).perimeter()
    Triangle(base=10, height=5).area()
"""

from __future__ import annotations

import math
from typing import Optional


class Circle:
    """
    Círculo.

    ::

        c = Circle(radius=5)
        c.area()           # 78.539...
        c.circumference()  # 31.415...
    """

    def __init__(self, radius: float) -> None:
        if radius < 0:
            raise ValueError("Radius cannot be negative")
        self._radius = float(radius)

    def area(self) -> float:
        return math.pi * self._radius ** 2

    def circumference(self) -> float:
        return 2 * math.pi * self._radius

    def diameter(self) -> float:
        return 2 * self._radius

    @property
    def radius(self) -> float:
        return self._radius

    def scale(self, factor: float) -> "Circle":
        return Circle(self._radius * factor)

    def __repr__(self) -> str:
        return f"Circle(radius={self._radius!r})"


class Rectangle:
    """
    Retângulo.

    ::

        r = Rectangle(10, 20)
        r.area()       # 200
        r.perimeter()  # 60
        r.diagonal()
    """

    def __init__(self, width: float, height: float) -> None:
        if width < 0 or height < 0:
            raise ValueError("Width and height cannot be negative")
        self._width = float(width)
        self._height = float(height)

    def area(self) -> float:
        return self._width * self._height

    def perimeter(self) -> float:
        return 2 * (self._width + self._height)

    def diagonal(self) -> float:
        return math.sqrt(self._width ** 2 + self._height ** 2)

    def is_square(self) -> bool:
        return self._width == self._height

    def scale(self, factor: float) -> "Rectangle":
        return Rectangle(self._width * factor, self._height * factor)

    @property
    def width(self) -> float:
        return self._width

    @property
    def height(self) -> float:
        return self._height

    def __repr__(self) -> str:
        return f"Rectangle({self._width!r}, {self._height!r})"


class Triangle:
    """
    Triângulo. Pode ser criado por base+altura ou pelos três lados.

    ::

        # Base e altura
        Triangle(base=10, height=5).area()

        # Três lados (fórmula de Heron)
        Triangle(a=3, b=4, c=5).area()
    """

    def __init__(
        self,
        base: Optional[float] = None,
        height: Optional[float] = None,
        a: Optional[float] = None,
        b: Optional[float] = None,
        c: Optional[float] = None,
    ) -> None:
        self._base = base
        self._height = height
        self._a = a
        self._b = b
        self._c = c

        if a is not None and b is not None and c is not None:
            if a + b <= c or a + c <= b or b + c <= a:
                raise ValueError("The given sides do not form a valid triangle")

    def area(self) -> float:
        if self._base is not None and self._height is not None:
            return 0.5 * self._base * self._height
        if self._a is not None and self._b is not None and self._c is not None:
            # Fórmula de Heron
            s = (self._a + self._b + self._c) / 2
            return math.sqrt(s * (s - self._a) * (s - self._b) * (s - self._c))
        raise ValueError("Insufficient data to compute area. Provide base+height or a+b+c.")

    def perimeter(self) -> float:
        if self._a is not None and self._b is not None and self._c is not None:
            return self._a + self._b + self._c
        raise ValueError("Perimeter requires all three sides (a, b, c).")

    def hypotenuse(self) -> float:
        """Hipotenusa assumindo triângulo retângulo (a² + b²)."""
        if self._a is None or self._b is None:
            raise ValueError("Requires sides a and b.")
        return math.sqrt(self._a ** 2 + self._b ** 2)

    def is_right(self) -> bool:
        """Verifica se é um triângulo retângulo."""
        if self._a is None or self._b is None or self._c is None:
            raise ValueError("Requires all three sides.")
        sides = sorted([self._a, self._b, self._c])
        return math.isclose(sides[0] ** 2 + sides[1] ** 2, sides[2] ** 2, rel_tol=1e-9)

    def __repr__(self) -> str:
        if self._a is not None:
            return f"Triangle(a={self._a!r}, b={self._b!r}, c={self._c!r})"
        return f"Triangle(base={self._base!r}, height={self._height!r})"


class Sphere:
    """Esfera 3D."""

    def __init__(self, radius: float) -> None:
        self._radius = float(radius)

    def volume(self) -> float:
        return (4 / 3) * math.pi * self._radius ** 3

    def surface_area(self) -> float:
        return 4 * math.pi * self._radius ** 2

    def __repr__(self) -> str:
        return f"Sphere(radius={self._radius!r})"


class Cylinder:
    """Cilindro."""

    def __init__(self, radius: float, height: float) -> None:
        self._radius = float(radius)
        self._height = float(height)

    def volume(self) -> float:
        return math.pi * self._radius ** 2 * self._height

    def surface_area(self) -> float:
        return 2 * math.pi * self._radius * (self._radius + self._height)

    def __repr__(self) -> str:
        return f"Cylinder(radius={self._radius!r}, height={self._height!r})"


__all__ = ["Circle", "Rectangle", "Triangle", "Sphere", "Cylinder"]
