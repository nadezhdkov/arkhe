"""
arkhe.pyunix.ui.layout
--------------------------
Containers for layout management (Column, Row, Stack).
"""
from __future__ import annotations
from typing import List

from arkhe.pyunix.ui.view import UIElement

class Column(UIElement):
    def __init__(
        self,
        children: List[UIElement],
        *,
        x: float = 0, y: float = 0,
        gap: int = 8,
    ):
        self.x = x
        self.y = y
        self.gap = gap
        self.children = children

    def update(self, dt: float) -> None:
        for c in self.children:
            c.update(dt)

    def draw(self, offset_x: float = 0, offset_y: float = 0) -> None:
        dx = self.x + offset_x
        dy = self.y + offset_y
        cy = 0
        for c in self.children:
            c.x = dx
            c.y = dy + cy
            c.draw(0, 0)
            
            h = getattr(c, 'height', 20)
            if hasattr(c, 'text_entity'):
                h = getattr(c, 'text_entity').height
            cy += h + self.gap

class Row(UIElement):
    def __init__(
        self,
        children: List[UIElement],
        *,
        x: float = 0, y: float = 0,
        gap: int = 8,
    ):
        self.x = x
        self.y = y
        self.gap = gap
        self.children = children

    def update(self, dt: float) -> None:
        for c in self.children:
            c.update(dt)

    def draw(self, offset_x: float = 0, offset_y: float = 0) -> None:
        dx = self.x + offset_x
        dy = self.y + offset_y
        cx = 0
        for c in self.children:
            c.x = dx + cx
            c.y = dy
            c.draw(0, 0)
            
            w = getattr(c, 'width', 20)
            if hasattr(c, 'text_entity'):
                w = getattr(c, 'text_entity').width
            cx += w + self.gap
            
class Stack(UIElement):
    """Draws children on top of each other at the same coordinate."""
    def __init__(
        self,
        children: List[UIElement],
        *,
        x: float = 0, y: float = 0,
    ):
        self.x = x
        self.y = y
        self.children = children

    def update(self, dt: float) -> None:
        for c in self.children:
            c.update(dt)

    def draw(self, offset_x: float = 0, offset_y: float = 0) -> None:
        dx = self.x + offset_x
        dy = self.y + offset_y
        for c in self.children:
            c.x = dx
            c.y = dy
            c.draw(0, 0)
            
class Spacer(UIElement):
    """Empty space to fill layouts."""
    def __init__(self, width: float = 0, height: float = 0):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        
    def draw(self, offset_x: float = 0, offset_y: float = 0) -> None:
        pass
