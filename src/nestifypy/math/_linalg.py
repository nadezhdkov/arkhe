"""
nestifypy.math._linalg
-----------------------
Álgebra linear e estatística: Vector, Matrix.
"""

from __future__ import annotations

import math
import statistics as _stats
from typing import Any, Iterable, List, Optional, Sequence, Union


# ---------------------------------------------------------------------------
# Vector
# ---------------------------------------------------------------------------

class Vector:
    """
    Vetor n-dimensional com API fluente.

    ::

        v = Vector(1, 2, 3)
        v.length()
        v.normalize()
        v.dot(Vector(4, 5, 6))
        v.cross(Vector(4, 5, 6))  # apenas 3D
    """

    __slots__ = ("_components",)

    def __init__(self, *components: Union[int, float]) -> None:
        if len(components) == 1 and isinstance(components[0], (list, tuple)):
            self._components: tuple[float, ...] = tuple(float(x) for x in components[0])
        else:
            self._components = tuple(float(x) for x in components)

    # ── métricas ──────────────────────────────────────────────────────────

    def length(self) -> float:
        """Norma euclidiana (magnitude) do vetor."""
        return math.sqrt(sum(x * x for x in self._components))

    def normalize(self) -> "Vector":
        """Retorna o vetor unitário na mesma direção."""
        mag = self.length()
        if mag == 0:
            raise ValueError("Cannot normalize the zero vector")
        return Vector(*[x / mag for x in self._components])

    # ── produtos ──────────────────────────────────────────────────────────

    def dot(self, other: "Vector") -> float:
        """Produto escalar."""
        self._check_dim(other)
        return sum(a * b for a, b in zip(self._components, other._components))

    def cross(self, other: "Vector") -> "Vector":
        """Produto vetorial (apenas 3D)."""
        if len(self._components) != 3 or len(other._components) != 3:
            raise ValueError("Cross product is only defined for 3D vectors")
        ax, ay, az = self._components
        bx, by, bz = other._components
        return Vector(
            ay * bz - az * by,
            az * bx - ax * bz,
            ax * by - ay * bx,
        )

    def angle_with(self, other: "Vector") -> float:
        """Ângulo entre dois vetores em radianos."""
        self._check_dim(other)
        cos_theta = self.dot(other) / (self.length() * other.length())
        # Clamp para evitar erros de ponto flutuante em acos
        cos_theta = max(-1.0, min(1.0, cos_theta))
        return math.acos(cos_theta)

    def project_onto(self, other: "Vector") -> "Vector":
        """Projeção deste vetor sobre other."""
        scalar = self.dot(other) / other.dot(other)
        return Vector(*[scalar * x for x in other._components])

    # ── operadores ────────────────────────────────────────────────────────

    def __add__(self, other: "Vector") -> "Vector":
        self._check_dim(other)
        return Vector(*[a + b for a, b in zip(self._components, other._components)])

    def __sub__(self, other: "Vector") -> "Vector":
        self._check_dim(other)
        return Vector(*[a - b for a, b in zip(self._components, other._components)])

    def __mul__(self, scalar: float) -> "Vector":
        return Vector(*[x * scalar for x in self._components])

    def __rmul__(self, scalar: float) -> "Vector":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "Vector":
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide vector by zero")
        return Vector(*[x / scalar for x in self._components])

    def __neg__(self) -> "Vector":
        return Vector(*[-x for x in self._components])

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Vector) and self._components == other._components

    def __len__(self) -> int:
        return len(self._components)

    def __getitem__(self, index: int) -> float:
        return self._components[index]

    def __iter__(self):
        return iter(self._components)

    def __repr__(self) -> str:
        return f"Vector({', '.join(str(x) for x in self._components)})"

    def _check_dim(self, other: "Vector") -> None:
        if len(self._components) != len(other._components):
            raise ValueError(
                f"Dimension mismatch: {len(self._components)} vs {len(other._components)}"
            )

    @property
    def dimensions(self) -> int:
        return len(self._components)

    def to_list(self) -> List[float]:
        return list(self._components)


# ---------------------------------------------------------------------------
# Matrix
# ---------------------------------------------------------------------------

class Matrix:
    """
    Matriz n×m com API fluente.

    ::

        m = Matrix([[1, 2], [3, 4]])
        m.inverse()
        m.determinant()
        m.transpose()
    """

    __slots__ = ("_rows",)

    def __init__(self, rows: Sequence[Sequence[Union[int, float]]]) -> None:
        self._rows: List[List[float]] = [[float(x) for x in row] for row in rows]
        # Valida que todas as linhas têm o mesmo comprimento
        if self._rows:
            n = len(self._rows[0])
            if any(len(r) != n for r in self._rows):
                raise ValueError("All rows must have the same number of columns")

    # ── dimensões ─────────────────────────────────────────────────────────

    @property
    def rows(self) -> int:
        return len(self._rows)

    @property
    def cols(self) -> int:
        return len(self._rows[0]) if self._rows else 0

    def is_square(self) -> bool:
        return self.rows == self.cols

    # ── operações básicas ─────────────────────────────────────────────────

    def transpose(self) -> "Matrix":
        """Transposta da matriz."""
        if not self._rows:
            return Matrix([])
        return Matrix([[self._rows[r][c] for r in range(self.rows)] for c in range(self.cols)])

    def determinant(self) -> float:
        """Determinante (apenas matrizes quadradas)."""
        if not self.is_square():
            raise ValueError("Determinant is only defined for square matrices")
        return _determinant(self._rows)

    def inverse(self) -> "Matrix":
        """Inversa (apenas matrizes quadradas e não-singulares)."""
        if not self.is_square():
            raise ValueError("Inverse is only defined for square matrices")
        det = self.determinant()
        if abs(det) < 1e-12:
            raise ValueError("Matrix is singular (determinant ≈ 0), cannot invert")
        return _inverse(self._rows)

    def trace(self) -> float:
        """Traço (soma da diagonal principal)."""
        if not self.is_square():
            raise ValueError("Trace is only defined for square matrices")
        return sum(self._rows[i][i] for i in range(self.rows))

    # ── operadores ────────────────────────────────────────────────────────

    def __add__(self, other: "Matrix") -> "Matrix":
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Matrix dimensions must match for addition")
        return Matrix([
            [self._rows[r][c] + other._rows[r][c] for c in range(self.cols)]
            for r in range(self.rows)
        ])

    def __sub__(self, other: "Matrix") -> "Matrix":
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Matrix dimensions must match for subtraction")
        return Matrix([
            [self._rows[r][c] - other._rows[r][c] for c in range(self.cols)]
            for r in range(self.rows)
        ])

    def __mul__(self, other: Union["Matrix", float, int]) -> "Matrix":
        if isinstance(other, (int, float)):
            return Matrix([[x * other for x in row] for row in self._rows])
        if self.cols != other.rows:
            raise ValueError(
                f"Cannot multiply {self.rows}×{self.cols} by {other.rows}×{other.cols}"
            )
        result = []
        for r in range(self.rows):
            row = []
            for c in range(other.cols):
                val = sum(self._rows[r][k] * other._rows[k][c] for k in range(self.cols))
                row.append(val)
            result.append(row)
        return Matrix(result)

    def __getitem__(self, index: int) -> List[float]:
        return self._rows[index]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Matrix) and self._rows == other._rows

    def __repr__(self) -> str:
        rows_str = ", ".join(str(row) for row in self._rows)
        return f"Matrix([{rows_str}])"

    def to_list(self) -> List[List[float]]:
        return [list(row) for row in self._rows]

    @classmethod
    def identity(cls, n: int) -> "Matrix":
        """Matriz identidade n×n."""
        return cls([[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)])

    @classmethod
    def zeros(cls, rows: int, cols: int) -> "Matrix":
        return cls([[0.0] * cols for _ in range(rows)])


# ---------------------------------------------------------------------------
# helpers de álgebra linear
# ---------------------------------------------------------------------------

def _determinant(matrix: List[List[float]]) -> float:
    n = len(matrix)
    if n == 1:
        return matrix[0][0]
    if n == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    det = 0.0
    for col in range(n):
        minor = [row[:col] + row[col + 1:] for row in matrix[1:]]
        sign = (-1) ** col
        det += sign * matrix[0][col] * _determinant(minor)
    return det


def _inverse(matrix: List[List[float]]) -> "Matrix":
    """Gauss-Jordan elimination para calcular a inversa."""
    n = len(matrix)
    # Cria matriz aumentada [A | I]
    aug = [row[:] + ([1.0 if i == j else 0.0 for j in range(n)]) for i, row in enumerate(matrix)]

    for col in range(n):
        # Pivot
        max_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[max_row] = aug[max_row], aug[col]
        pivot = aug[col][col]
        aug[col] = [x / pivot for x in aug[col]]
        for row in range(n):
            if row != col:
                factor = aug[row][col]
                aug[row] = [aug[row][k] - factor * aug[col][k] for k in range(2 * n)]

    result = [row[n:] for row in aug]
    return Matrix(result)


__all__ = ["Vector", "Matrix"]
