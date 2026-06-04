"""
arkhe.pyunix.entity.component
---------------------------------
Base Component class for the Entity-Component System (ECS-lite).
Inspired by Unity's MonoBehaviour.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from arkhe.pyunix.sprite import Entity
    from arkhe.pyunix.physics import CollisionInfo

class Component:
    """
    Base class for all custom components.
    Components add behavior to Entities without inheritance.
    """
    def __init__(self) -> None:
        self._entity: Any = None

    @property
    def entity(self) -> 'Entity':
        """Reference back to the owning entity."""
        return self._entity

    # ── Hooks (override in subclasses) ────────────────

    def on_attach(self) -> None:
        """Called when the component is added to an entity."""
        pass

    def on_detach(self) -> None:
        """Called when the component is removed from an entity."""
        pass

    def on_update(self, dt: float) -> None:
        """Called every frame."""
        pass

    def on_fixed_update(self) -> None:
        """Called at a fixed physics time step."""
        pass

    def on_draw(self) -> None:
        """Called during the render frame."""
        pass

    def on_collision_enter(self, info: 'CollisionInfo') -> None:
        pass

    def on_collision_stay(self, info: 'CollisionInfo') -> None:
        pass

    def on_collision_exit(self, info: 'CollisionInfo') -> None:
        pass

    def on_trigger_enter(self, info: 'CollisionInfo') -> None:
        pass

    def on_trigger_exit(self, info: 'CollisionInfo') -> None:
        pass

    def on_destroy(self) -> None:
        """Called right before the entity is destroyed."""
        pass

    def on_pause(self) -> None:
        pass

    def on_resume(self) -> None:
        pass

# ── Built-in engine components ───────────────────────

class AutoDestroy(Component):
    """Destroys the entity after N seconds."""
    def __init__(self, after: float):
        super().__init__()
        self.timer = after

    def on_update(self, dt: float) -> None:
        self.timer -= dt
        if self.timer <= 0:
            self.entity.destroy()

class Floater(Component):
    """Makes the entity float up and down."""
    def __init__(self, amplitude: float = 8.0, speed: float = 2.0):
        super().__init__()
        self.amplitude = amplitude
        self.speed = speed
        self._time = 0.0
        self._base_y = 0.0

    def on_attach(self) -> None:
        self._base_y = self.entity.y

    def on_update(self, dt: float) -> None:
        import math
        self._time += dt
        self.entity.y = self._base_y + math.sin(self._time * self.speed) * self.amplitude
