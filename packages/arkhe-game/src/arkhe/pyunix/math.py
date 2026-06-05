"""
arkhe.pyunix.math
---------------------
Core math primitives: Vector2 and Color.

These are foundational types used across the entire engine. They support
operator overloading, swizzling-style properties, and common game-math utilities.

Usage:
    v = Vector2(3, 4)
    print(v.magnitude)     # 5.0
    print(v.normalized)    # Vector2(0.6, 0.8)
    print(v + Vector2(1, 2))

    c = Color.from_hex("#FF5733")
    faded = c.lerp(Color(0, 0, 0), 0.5)
"""
from __future__ import annotations

import math
from typing import Iterator, Tuple, Union


# ---------------------------------------------------------------------------
# Vector2
# ---------------------------------------------------------------------------

class Vector2:
    """
    Immutable-friendly 2D vector with full operator support and game-math utilities.

    Supports all standard arithmetic operators, dot/cross products, lerp, clamping,
    reflection, and pygame-compatible tuple conversion.
    """

    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)

    # ── Constructors ─────────────────────────

    @classmethod
    def zero(cls) -> "Vector2":
        """Return a (0, 0) vector."""
        return cls(0.0, 0.0)

    @classmethod
    def one(cls) -> "Vector2":
        """Return a (1, 1) vector."""
        return cls(1.0, 1.0)

    @classmethod
    def up(cls) -> "Vector2":
        """Return a (0, -1) vector (screen-space up)."""
        return cls(0.0, -1.0)

    @classmethod
    def down(cls) -> "Vector2":
        """Return a (0, 1) vector (screen-space down)."""
        return cls(0.0, 1.0)

    @classmethod
    def left(cls) -> "Vector2":
        """Return a (-1, 0) vector."""
        return cls(-1.0, 0.0)

    @classmethod
    def right(cls) -> "Vector2":
        """Return a (1, 0) vector."""
        return cls(1.0, 0.0)

    @classmethod
    def from_angle(cls, angle_degrees: float, magnitude: float = 1.0) -> "Vector2":
        """Create a vector from an angle in degrees and an optional magnitude."""
        rad = math.radians(angle_degrees)
        return cls(math.cos(rad) * magnitude, math.sin(rad) * magnitude)

    @classmethod
    def from_tuple(cls, t: Tuple[float, float]) -> "Vector2":
        return cls(t[0], t[1])

    # ── Arithmetic ───────────────────────────

    def __add__(self, other: Union["Vector2", float]) -> "Vector2":
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        return Vector2(self.x + other, self.y + other)

    def __radd__(self, other: float) -> "Vector2":
        return Vector2(self.x + other, self.y + other)

    def __sub__(self, other: Union["Vector2", float]) -> "Vector2":
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)
        return Vector2(self.x - other, self.y - other)

    def __rsub__(self, other: float) -> "Vector2":
        return Vector2(other - self.x, other - self.y)

    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> "Vector2":
        if scalar == 0:
            return Vector2.zero()
        return Vector2(self.x / scalar, self.y / scalar)

    def __neg__(self) -> "Vector2":
        return Vector2(-self.x, -self.y)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Vector2):
            return math.isclose(self.x, other.x) and math.isclose(self.y, other.y)
        return NotImplemented

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __repr__(self) -> str:
        return f"Vector2({self.x:.3f}, {self.y:.3f})"

    def __hash__(self) -> int:
        return hash((round(self.x, 6), round(self.y, 6)))

    # ── Properties ───────────────────────────

    @property
    def magnitude(self) -> float:
        """Return the length (magnitude) of the vector."""
        return math.hypot(self.x, self.y)

    @property
    def magnitude_squared(self) -> float:
        """Return squared magnitude — cheaper than magnitude for comparisons."""
        return self.x * self.x + self.y * self.y

    @property
    def normalized(self) -> "Vector2":
        """Return a unit vector pointing in the same direction."""
        m = self.magnitude
        if m == 0:
            return Vector2.zero()
        return Vector2(self.x / m, self.y / m)

    @property
    def angle(self) -> float:
        """Return the angle of this vector in degrees (0° = right, clockwise)."""
        return math.degrees(math.atan2(self.y, self.x))

    @property
    def perpendicular(self) -> "Vector2":
        """Return a vector perpendicular to this one (rotated 90° counter-clockwise)."""
        return Vector2(-self.y, self.x)

    # ── Methods ──────────────────────────────

    def dot(self, other: "Vector2") -> float:
        """Return the dot product with another vector."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vector2") -> float:
        """Return the 2D cross product scalar (z-component)."""
        return self.x * other.y - self.y * other.x

    def distance_to(self, other: "Vector2") -> float:
        """Return the Euclidean distance to another vector."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def distance_to_squared(self, other: "Vector2") -> float:
        """Return the squared distance to another vector (faster for comparisons)."""
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy

    def lerp(self, target: "Vector2", t: float) -> "Vector2":
        """Linearly interpolate toward `target` by factor `t` (0.0–1.0)."""
        t = max(0.0, min(1.0, t))
        return Vector2(self.x + (target.x - self.x) * t, self.y + (target.y - self.y) * t)

    def move_towards(self, target: "Vector2", max_delta: float) -> "Vector2":
        """Move toward `target` by at most `max_delta` units."""
        diff = target - self
        dist = diff.magnitude
        if dist <= max_delta or dist == 0:
            return Vector2(target.x, target.y)
        return self + diff.normalized * max_delta

    def reflect(self, normal: "Vector2") -> "Vector2":
        """Reflect this vector off a surface with the given normal."""
        n = normal.normalized
        return self - n * (2 * self.dot(n))

    def clamp_magnitude(self, max_length: float) -> "Vector2":
        """Return a copy clamped to `max_length` magnitude."""
        if self.magnitude > max_length:
            return self.normalized * max_length
        return Vector2(self.x, self.y)

    def rotate(self, degrees: float) -> "Vector2":
        """Return a new vector rotated by `degrees`."""
        rad = math.radians(degrees)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        return Vector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a,
        )

    def angle_to(self, other: "Vector2") -> float:
        """Return signed angle in degrees from this vector to `other`."""
        return math.degrees(math.atan2(
            self.x * other.y - self.y * other.x,
            self.x * other.x + self.y * other.y
        ))

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def to_int_tuple(self) -> Tuple[int, int]:
        return (int(self.x), int(self.y))

    def copy(self) -> "Vector2":
        return Vector2(self.x, self.y)


# ---------------------------------------------------------------------------
# Color
# ---------------------------------------------------------------------------

class Color:
    """
    RGBA color type with lerp, HSV conversion, and operator support.

    Colors can be constructed from RGB tuples, hex strings, or HSV values.
    All channels are stored as floats in 0–255 range internally.

    Usage:
        red   = Color(255, 0, 0)
        green = Color.from_hex("#00FF00")
        mixed = red.lerp(green, 0.5)
        rgb   = red.to_rgb()     # (255, 0, 0)
        rgba  = red.to_rgba()    # (255, 0, 0, 255)
    """

    __slots__ = ("r", "g", "b", "a")

    # Named colors
    WHITE   = None  # set below
    BLACK   = None
    RED     = None
    GREEN   = None
    BLUE    = None
    YELLOW  = None
    CYAN    = None
    MAGENTA = None
    TRANSPARENT = None

    def __init__(self, r: float = 255, g: float = 255, b: float = 255, a: float = 255) -> None:
        self.r = float(r)
        self.g = float(g)
        self.b = float(b)
        self.a = float(a)

    # ── Constructors ─────────────────────────

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        """Parse a CSS hex string (#RGB, #RRGGBB, or #RRGGBBAA)."""
        h = hex_str.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        a = int(h[6:8], 16) if len(h) == 8 else 255
        return cls(r, g, b, a)

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float, a: float = 255) -> "Color":
        """Create a color from HSV values. h: 0–360, s/v: 0.0–1.0."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
        return cls(r * 255, g * 255, b * 255, a)

    @classmethod
    def from_normalized(cls, r: float, g: float, b: float, a: float = 1.0) -> "Color":
        """Create a color from 0.0–1.0 normalized float values."""
        return cls(r * 255, g * 255, b * 255, a * 255)

    # ── Conversion ───────────────────────────

    def to_rgb(self) -> Tuple[int, int, int]:
        return (int(self.r), int(self.g), int(self.b))

    def to_rgba(self) -> Tuple[int, int, int, int]:
        return (int(self.r), int(self.g), int(self.b), int(self.a))

    def to_normalized(self) -> Tuple[float, float, float, float]:
        return (self.r / 255, self.g / 255, self.b / 255, self.a / 255)

    def to_hex(self) -> str:
        return "#{:02X}{:02X}{:02X}".format(int(self.r), int(self.g), int(self.b))

    def to_hsv(self) -> Tuple[float, float, float]:
        import colorsys
        h, s, v = colorsys.rgb_to_hsv(self.r / 255, self.g / 255, self.b / 255)
        return (h * 360, s, v)

    # ── Manipulation ─────────────────────────

    def lerp(self, other: "Color", t: float) -> "Color":
        """Linearly interpolate toward `other` by `t` (0.0–1.0)."""
        t = max(0.0, min(1.0, t))
        return Color(
            self.r + (other.r - self.r) * t,
            self.g + (other.g - self.g) * t,
            self.b + (other.b - self.b) * t,
            self.a + (other.a - self.a) * t,
        )

    def with_alpha(self, alpha: float) -> "Color":
        """Return a copy with the given alpha (0–255)."""
        return Color(self.r, self.g, self.b, alpha)

    def brighten(self, amount: float) -> "Color":
        """Return a brighter version (add `amount` to each channel, 0–255 clamped)."""
        return Color(
            min(255, self.r + amount),
            min(255, self.g + amount),
            min(255, self.b + amount),
            self.a,
        )

    def darken(self, amount: float) -> "Color":
        """Return a darker version."""
        return Color(
            max(0, self.r - amount),
            max(0, self.g - amount),
            max(0, self.b - amount),
            self.a,
        )

    def __repr__(self) -> str:
        return f"Color({int(self.r)}, {int(self.g)}, {int(self.b)}, {int(self.a)})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Color):
            return self.to_rgba() == other.to_rgba()
        return NotImplemented

    def __iter__(self) -> Iterator[int]:
        """Allow tuple unpacking: r, g, b, a = color"""
        yield int(self.r)
        yield int(self.g)
        yield int(self.b)
        yield int(self.a)


# Assign named colors after class definition
Color.WHITE       = Color(255, 255, 255)
Color.BLACK       = Color(0, 0, 0)
Color.RED         = Color(255, 0, 0)
Color.GREEN       = Color(0, 255, 0)
Color.BLUE        = Color(0, 0, 255)
Color.YELLOW      = Color(255, 255, 0)
Color.CYAN        = Color(0, 255, 255)
Color.MAGENTA     = Color(255, 0, 255)
Color.TRANSPARENT = Color(0, 0, 0, 0)
