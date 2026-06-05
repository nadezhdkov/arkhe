"""
arkhe.pyunix.ui.components
------------------------------
Basic UI widgets.
"""
from __future__ import annotations
from typing import Callable, Union, Any

from arkhe.pyunix.math import Color
from arkhe.pyunix.render.draw import Draw
from arkhe.pyunix.ui.view import UIElement
from arkhe.pyunix.text import Text
from arkhe.pyunix.input import Input

class Label(UIElement):
    def __init__(
        self,
        text: Union[str, Callable[[], str]],
        *,
        x: float = 0, y: float = 0,
        font: str = "default",
        size: int = 20,
        color: Union[Color, str] = "white",
        align: str = "left",
        shadow: bool = False,
        outline: bool = False,
    ):
        self.x = x
        self.y = y
        self.text_entity = Text(
            text=text,
            x=x, y=y,
            font_name=font,
            size=size,
            color=color,
            shadow=shadow,
            outline=outline,
            align=align,
        )

    def update(self, dt: float) -> None:
        self.text_entity._dispatch("update", dt)

    def draw(self, offset_x: float = 0, offset_y: float = 0) -> None:
        self.text_entity.x = self.x + offset_x
        self.text_entity.y = self.y + offset_y
        self.text_entity.draw()

class Button(UIElement):
    def __init__(
        self,
        text: str,
        *,
        x: float = 0, y: float = 0,
        width: int = 120, height: int = 40,
        color: Union[Color, str] = "#3060A0",
        text_color: Union[Color, str] = "white",
        hover_color: Union[Color, str] = "#4080C0",
        border_radius: int = 6,
        on_click: Callable[[], None] = None,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.hover_color = hover_color
        self.border_radius = border_radius
        self.on_click = on_click
        
        self.label = Label(text, color=text_color, size=int(height * 0.5))
        self._is_hovered = False

    def update(self, dt: float) -> None:
        mx, my = Input.mouse_position()
        self._is_hovered = (
            self.x <= mx <= self.x + self.width and
            self.y <= my <= self.y + self.height
        )
        if self._is_hovered and Input.get_mouse_button_down(1):
            if self.on_click:
                self.on_click()
        self.label.update(dt)

    def draw(self, offset_x: float = 0, offset_y: float = 0) -> None:
        c = self.hover_color if self._is_hovered else self.color
        dx = self.x + offset_x
        dy = self.y + offset_y
        Draw.rect(dx, dy, self.width, self.height, color=c, border_radius=self.border_radius)
        
        lw = self.label.text_entity.width
        lh = self.label.text_entity.height
        self.label.x = dx + (self.width - lw) / 2
        self.label.y = dy + (self.height - lh) / 2
        self.label.draw(0, 0)

class Panel(UIElement):
    def __init__(
        self,
        children: list[UIElement] = None,
        *,
        x: float = 0, y: float = 0,
        width: int = 300, height: int = 200,
        color: Union[Color, str] = "#1a1a2e",
        border_radius: int = 8,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.border_radius = border_radius
        self.children = children or []

    def update(self, dt: float) -> None:
        for c in self.children:
            c.update(dt)

    def draw(self, offset_x: float = 0, offset_y: float = 0) -> None:
        dx = self.x + offset_x
        dy = self.y + offset_y
        Draw.rect(dx, dy, self.width, self.height, color=self.color, border_radius=self.border_radius)
        for c in self.children:
            c.draw(dx, dy)
