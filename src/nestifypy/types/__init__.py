"""
nestifypy.types
------------
Custom reusable data structures: Vector2, Color, Position, Rect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterator, Tuple

@dataclass(slots=True)
class Vector2:
    """2D vector with common math operations."""

    x: float = 0.0
    y: float = 0.0

    @classmethod
    def zero(cls) -> "Vector2":
        return cls(0, 0)

    @classmethod
    def one(cls) -> "Vector2":
        return cls(1, 1)

    @classmethod
    def up(cls) -> "Vector2":
        return cls(0, -1)

    @classmethod
    def down(cls) -> "Vector2":
        return cls(0, 1)

    @classmethod
    def left(cls) -> "Vector2":
        return cls(-1, 0)

    @classmethod
    def right(cls) -> "Vector2":
        return cls(1, 0)

    def length(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def normalized(self) -> "Vector2":
        mag = self.length()
        if mag == 0:
            return Vector2.zero()
        return Vector2(self.x / mag, self.y / mag)

    def dot(self, other: "Vector2") -> float:
        return self.x * other.x + self.y * other.y

    def distance_to(self, other: "Vector2") -> float:
        return math.sqrt((other.x - self.x) ** 2 + (other.y - self.y) ** 2)

    def lerp(self, other: "Vector2", t: float) -> "Vector2":
        return Vector2(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
        )

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def to_int_tuple(self) -> Tuple[int, int]:
        return (int(self.x), int(self.y))

    def __add__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> "Vector2":
        return Vector2(self.x / scalar, self.y / scalar)

    def __neg__(self) -> "Vector2":
        return Vector2(-self.x, -self.y)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        return False

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __repr__(self) -> str:
        return f"Vector2({self.x}, {self.y})"


@dataclass(slots=True)
class Color:
    """RGBA color value with utilities."""

    r: int
    g: int
    b: int
    a: int = 255

    def __post_init__(self) -> None:
        self.r = max(0, min(255, self.r))
        self.g = max(0, min(255, self.g))
        self.b = max(0, min(255, self.b))
        self.a = max(0, min(255, self.a))

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 6:
            r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            return cls(r, g, b)
        elif len(hex_str) == 8:
            r, g, b, a = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), int(hex_str[6:8], 16)
            return cls(r, g, b, a)
        raise ValueError(f"Invalid hex color: {hex_str}")

    # Presets
    RED     = None
    GREEN   = None
    BLUE    = None
    WHITE   = None
    BLACK   = None
    YELLOW  = None
    CYAN    = None
    MAGENTA = None

    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.r, self.g, self.b, self.a)

    def to_rgb(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def lerp(self, other: "Color", t: float) -> "Color":
        return Color(
            int(self.r + (other.r - self.r) * t),
            int(self.g + (other.g - self.g) * t),
            int(self.b + (other.b - self.b) * t),
            int(self.a + (other.a - self.a) * t),
        )

    def with_alpha(self, a: int) -> "Color":
        return Color(self.r, self.g, self.b, a)

    def __repr__(self) -> str:
        return f"Color(r={self.r}, g={self.g}, b={self.b}, a={self.a})"


# Set presets after class definition
Color.RED     = Color(255, 0, 0)       # type: ignore
Color.GREEN   = Color(0, 255, 0)       # type: ignore
Color.BLUE    = Color(0, 0, 255)       # type: ignore
Color.WHITE   = Color(255, 255, 255)   # type: ignore
Color.BLACK   = Color(0, 0, 0)         # type: ignore
Color.YELLOW  = Color(255, 255, 0)     # type: ignore
Color.CYAN    = Color(0, 255, 255)     # type: ignore
Color.MAGENTA = Color(255, 0, 255)     # type: ignore


@dataclass(slots=True)
class Position:
    """Named 2D position."""

    x: float = 0.0
    y: float = 0.0

    def to_vector(self) -> Vector2:
        return Vector2(self.x, self.y)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def offset(self, dx: float, dy: float) -> "Position":
        return Position(self.x + dx, self.y + dy)




@dataclass(slots=True)
class Rect:
    """Axis-aligned rectangle."""

    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    @property
    def area(self) -> float:
        return self.width * self.height

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.top <= y <= self.bottom

    def intersects(self, other: "Rect") -> bool:
        return not (
            other.left > self.right
            or other.right < self.left
            or other.top > self.bottom
            or other.bottom < self.top
        )

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.width, self.height)




__all__ = ["Vector2", "Color", "Position", "Rect"]
