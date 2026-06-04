"""
arkhe.pyunix.ui.view
------------------------
Declarative UI Views.
"""
from __future__ import annotations
from typing import Callable, Any, Optional

class UIElement:
    """Base class for all UI elements."""
    def draw(self, offset_x: float = 0, offset_y: float = 0) -> None:
        pass
        
    def update(self, dt: float) -> None:
        pass
        
    def handle_event(self, event: Any) -> bool:
        return False

class UIView(UIElement):
    """
    Base class for declarative UI Views.
    Rebuilds the UI when state changes (dirty).
    """
    def __init__(self) -> None:
        self._root: Optional[UIElement] = None
        self._dirty: bool = True

    def rebuild(self) -> UIElement:
        """Override to define the UI structure."""
        raise NotImplementedError

    def set_dirty(self) -> None:
        """Mark the view for rebuilding next frame."""
        self._dirty = True

    def _ensure_built(self) -> None:
        if self._dirty or self._root is None:
            self._root = self.rebuild()
            self._dirty = False

    def draw(self, offset_x: float = 0, offset_y: float = 0) -> None:
        self._ensure_built()
        if self._root:
            self._root.draw(offset_x, offset_y)

    def update(self, dt: float) -> None:
        self._ensure_built()
        if self._root:
            self._root.update(dt)

    def handle_event(self, event: Any) -> bool:
        self._ensure_built()
        if self._root:
            return self._root.handle_event(event)
        return False

class UIDecorators:
    @staticmethod
    def build(func: Callable) -> Callable:
        """
        Decorator for Scene methods to render UI via a rebuild function.
        Useful when you don't want to subclass UIView but want a reactive method.
        """
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> None:
            if not hasattr(self, "_ui_root") or getattr(self, "_ui_dirty", True):
                self._ui_root = func(self, *args, **kwargs)
                self._ui_dirty = False
            if self._ui_root:
                self._ui_root.draw(0, 0)
        wrapper._pyunix_sprite = "draw"
        return wrapper

UI = UIDecorators()
