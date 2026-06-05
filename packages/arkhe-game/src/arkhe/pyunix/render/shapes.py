"""
arkhe.pyunix.render.shapes
------------------------------
Object-oriented declarative shapes (Rectangle, Circle, etc).
"""
from __future__ import annotations
from typing import Any, List, Tuple, Union

from arkhe.pyunix.sprite import Entity, Sprite
from arkhe.pyunix.math import Color, Vector2
from arkhe.pyunix.render.draw import Draw

class Shape(Entity):
    def __init__(self, x: float, y: float, layer: str = "default"):
        super().__init__(x=x, y=y, layer=layer)


class Rectangle(Shape):
    def __init__(
        self,
        x: float, y: float,
        width: float, height: float,
        color: Union[Color, str] = "white",
        *,
        filled: bool = True,
        border_radius: int = 0,
        stroke_width: int = 1,
        alpha: int = 255,
        layer: str = "default",
    ):
        super().__init__(x=x, y=y, layer=layer)
        self.width = width
        self.height = height
        self.color = color
        self.filled = filled
        self.border_radius = border_radius
        self.stroke_width = stroke_width
        self.alpha = alpha

    @Sprite.draw
    def draw(self, surface: Any = None) -> None:
        Draw.rect(
            self.x, self.y,
            self.width, self.height,
            self.color,
            filled=self.filled,
            border_radius=self.border_radius,
            stroke_width=self.stroke_width,
            alpha=self.alpha,
        )

class Circle(Shape):
    def __init__(
        self,
        x: float, y: float,
        radius: float,
        color: Union[Color, str] = "white",
        *,
        filled: bool = True,
        stroke_width: int = 1,
        alpha: int = 255,
        layer: str = "default",
    ):
        super().__init__(x=x, y=y, layer=layer)
        self.radius = radius
        self.color = color
        self.filled = filled
        self.stroke_width = stroke_width
        self.alpha = alpha

    @Sprite.draw
    def draw(self, surface: Any = None) -> None:
        Draw.circle(
            self.x, self.y,
            self.radius,
            self.color,
            filled=self.filled,
            stroke_width=self.stroke_width,
            alpha=self.alpha,
        )

class Line(Shape):
    def __init__(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        color: Union[Color, str] = "white",
        width: int = 1,
        layer: str = "default",
    ):
        super().__init__(x=x1, y=y1, layer=layer)
        self.x2 = x2
        self.y2 = y2
        self.color = color
        self.line_width = width

    @Sprite.draw
    def draw(self, surface: Any = None) -> None:
        Draw.line(self.x, self.y, self.x2, self.y2, self.color, self.line_width)

class Polygon(Shape):
    def __init__(
        self,
        points: List[Tuple[float, float]],
        color: Union[Color, str] = "white",
        *,
        filled: bool = True,
        stroke_width: int = 1,
        layer: str = "default",
    ):
        x = points[0][0] if points else 0
        y = points[0][1] if points else 0
        super().__init__(x=x, y=y, layer=layer)
        self.points = points
        self.color = color
        self.filled = filled
        self.stroke_width = stroke_width

    @Sprite.draw
    def draw(self, surface: Any = None) -> None:
        Draw.polygon(
            self.points,
            self.color,
            filled=self.filled,
            stroke_width=self.stroke_width,
        )

Triangle = Polygon

class Capsule(Shape):
    def __init__(self, x: float, y: float, width: float, height: float, color: Union[Color, str]):
        super().__init__(x=x, y=y)
        self.width = width
        self.height = height
        self.color = color

    @Sprite.draw
    def draw(self, surface: Any = None) -> None:
        Draw.rect(self.x, self.y, self.width, self.height, self.color, border_radius=int(min(self.width, self.height)/2))
