"""
nestifypy.pyunix.physics
---------------------
Rigidbody physics system for 2D games, supporting dynamic, kinematic, and static bodies,
collision detection, sensor queries, and physics materials.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from nestifypy.types import Vector2

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class BodyType(Enum):
    """Defines the movement behavior of a Rigidbody."""
    STATIC = 0      # Never moves, infinite mass, doesn't integrate velocity
    KINEMATIC = 1   # Moves manually, infinite mass, ignores forces
    DYNAMIC = 2     # Moved by forces and velocity integration


@dataclass(slots=True)
class PhysicsMaterial:
    """Defines surface properties for a collider."""
    friction: float = 0.5
    bounciness: float = 0.0


@dataclass(slots=True)
class CollisionInfo:
    """Information about a collision event between two bodies."""
    other: Any  # The other Entity
    normal: Vector2
    depth: float
    is_trigger: bool = False


class Collider:
    """Base class for collision shapes."""
    __slots__ = ("offset", "is_trigger", "material")

    def __init__(self, offset: Vector2 = None, is_trigger: bool = False, material: PhysicsMaterial = None):
        self.offset: Vector2 = offset or Vector2.zero()
        self.is_trigger: bool = is_trigger
        self.material: PhysicsMaterial = material or PhysicsMaterial()


class BoxCollider(Collider):
    """An Axis-Aligned Bounding Box (AABB) collider."""
    __slots__ = ("width", "height")

    def __init__(self, width: float, height: float, offset: Vector2 = None, is_trigger: bool = False, material: PhysicsMaterial = None):
        super().__init__(offset, is_trigger, material)
        self.width = width
        self.height = height

    def get_bounds(self, entity_pos: Vector2) -> Tuple[float, float, float, float]:
        """Returns (left, top, right, bottom)."""
        center_x = entity_pos.x + self.offset.x
        center_y = entity_pos.y + self.offset.y
        half_w = self.width / 2
        half_h = self.height / 2
        return (center_x - half_w, center_y - half_h, center_x + half_w, center_y + half_h)


class CircleCollider(Collider):
    """A circle collider."""
    __slots__ = ("radius",)

    def __init__(self, radius: float, offset: Vector2 = None, is_trigger: bool = False, material: PhysicsMaterial = None):
        super().__init__(offset, is_trigger, material)
        self.radius = radius


class Rigidbody:
    """
    Physical body component attached to an Entity.
    """
    __slots__ = (
        "entity", "body_type", "velocity", "acceleration", "mass",
        "drag", "gravity_scale", "layer", "mask", "freeze_x", "freeze_y"
    )

    def __init__(
        self,
        body_type: BodyType = BodyType.DYNAMIC,
        mass: float = 1.0,
        drag: float = 0.0,
        gravity_scale: float = 1.0,
        layer: str = "default",
        mask: Set[str] = None,
        freeze_x: bool = False,
        freeze_y: bool = False
    ):
        self.entity: Any = None  # Set when attached to Entity
        self.body_type = body_type
        self.velocity = Vector2.zero()
        self.acceleration = Vector2.zero()
        self.mass = mass
        self.drag = drag
        self.gravity_scale = gravity_scale
        self.layer = layer
        self.mask = mask if mask is not None else {"default"}
        self.freeze_x = freeze_x
        self.freeze_y = freeze_y

    def add_force(self, force: Vector2) -> None:
        """Apply an instantaneous force, affected by mass."""
        if self.body_type != BodyType.DYNAMIC:
            return
        if self.mass > 0:
            self.velocity.x += force.x / self.mass
            self.velocity.y += force.y / self.mass

    def add_impulse(self, impulse: Vector2) -> None:
        """Apply an instantaneous velocity change, ignoring mass."""
        if self.body_type != BodyType.DYNAMIC:
            return
        self.velocity.x += impulse.x
        self.velocity.y += impulse.y


class PhysicsWorldSystem:
    """Global manager for physics simulation."""

    def __init__(self):
        self.gravity = Vector2(0, 980.0)
        self.fixed_dt = 1.0 / 60.0
        self.debug_draw = False
        self._bodies: List[Any] = []  # List of Entities with rigidbodies/colliders
        # Store active collisions to track stay/exit events
        # format: (entity1_id, entity2_id) -> bool
        self._active_collisions: Set[Tuple[int, int]] = set()

    def set_gravity(self, x: float, y: float) -> None:
        self.gravity = Vector2(x, y)

    def register(self, entity: Any) -> None:
        if entity not in self._bodies:
            self._bodies.append(entity)

    def unregister(self, entity: Any) -> None:
        if entity in self._bodies:
            self._bodies.remove(entity)
            # Cleanup active collisions involving this entity
            eid = id(entity)
            to_remove = [pair for pair in self._active_collisions if pair[0] == eid or pair[1] == eid]
            for pair in to_remove:
                self._active_collisions.discard(pair)

    def step(self) -> None:
        """Integrate velocities and resolve collisions."""
        dt = self.fixed_dt
        current_collisions: Set[Tuple[int, int]] = set()

        # 1. Integration (Velocity & Position)
        for entity in self._bodies:
            rb = getattr(entity, "rigidbody", None)
            if not rb or rb.body_type == BodyType.STATIC:
                continue

            # Apply gravity to dynamic bodies
            if rb.body_type == BodyType.DYNAMIC:
                rb.velocity.x += self.gravity.x * rb.gravity_scale * dt
                rb.velocity.y += self.gravity.y * rb.gravity_scale * dt
                
                # Apply drag
                if rb.drag > 0:
                    rb.velocity.x *= (1.0 - rb.drag * dt)
                    rb.velocity.y *= (1.0 - rb.drag * dt)

            # Move entity
            if not rb.freeze_x:
                entity.x += rb.velocity.x * dt
            if not rb.freeze_y:
                entity.y += rb.velocity.y * dt

        # 2. Collision Detection & Resolution (Brute force for now)
        n = len(self._bodies)
        for i in range(n):
            e1 = self._bodies[i]
            rb1 = getattr(e1, "rigidbody", None)
            col1 = getattr(e1, "collider", None)

            if not col1:
                continue

            for j in range(i + 1, n):
                e2 = self._bodies[j]
                rb2 = getattr(e2, "rigidbody", None)
                col2 = getattr(e2, "collider", None)

                if not col2:
                    continue
                
                # Layer Mask check
                can_collide = False
                if rb1 and rb2:
                     can_collide = (rb2.layer in rb1.mask) or (rb1.layer in rb2.mask)
                elif rb1:
                     can_collide = getattr(e2, "layer", "default") in rb1.mask
                elif rb2:
                     can_collide = getattr(e1, "layer", "default") in rb2.mask
                else:
                    can_collide = True # Neither has rigidbody, just colliders
                    
                if not can_collide:
                    continue

                # Box vs Box only for now
                if isinstance(col1, BoxCollider) and isinstance(col2, BoxCollider):
                    b1 = col1.get_bounds(Vector2(e1.x, e1.y))
                    b2 = col2.get_bounds(Vector2(e2.x, e2.y))

                    # AABB Check
                    if b1[0] < b2[2] and b1[2] > b2[0] and b1[1] < b2[3] and b1[3] > b2[1]:
                        # Collision occurred!
                        is_trigger = col1.is_trigger or col2.is_trigger
                        
                        # Calculate penetration
                        overlap_x = min(b1[2], b2[2]) - max(b1[0], b2[0])
                        overlap_y = min(b1[3], b2[3]) - max(b1[1], b2[1])

                        normal = Vector2.zero()
                        depth = 0.0

                        if overlap_x < overlap_y:
                            depth = overlap_x
                            if b1[0] < b2[0]:
                                normal = Vector2(-1, 0)
                            else:
                                normal = Vector2(1, 0)
                        else:
                            depth = overlap_y
                            if b1[1] < b2[1]:
                                normal = Vector2(0, -1)
                            else:
                                normal = Vector2(0, 1)

                        ci1 = CollisionInfo(e2, normal, depth, is_trigger)
                        ci2 = CollisionInfo(e1, -normal, depth, is_trigger)

                        pair_id = tuple(sorted((id(e1), id(e2))))
                        current_collisions.add(pair_id)

                        # Trigger callbacks
                        if pair_id not in self._active_collisions:
                            e1._dispatch("on_collision_enter", ci1)
                            e2._dispatch("on_collision_enter", ci2)
                        else:
                            e1._dispatch("on_collision_stay", ci1)
                            e2._dispatch("on_collision_stay", ci2)

                        # Physical Resolution
                        if not is_trigger:
                            self._resolve_collision(e1, rb1, col1, e2, rb2, col2, normal, depth)

        # 3. Handle Exit callbacks
        exited = self._active_collisions - current_collisions
        for pair in exited:
            id1, id2 = pair
            e1 = next((e for e in self._bodies if id(e) == id1), None)
            e2 = next((e for e in self._bodies if id(e) == id2), None)
            
            if e1 and e2:
                # We don't have full normal/depth info for exit, so use zeros
                ci1 = CollisionInfo(e2, Vector2.zero(), 0.0)
                ci2 = CollisionInfo(e1, Vector2.zero(), 0.0)
                e1._dispatch("on_collision_exit", ci1)
                e2._dispatch("on_collision_exit", ci2)

        self._active_collisions = current_collisions

    def _resolve_collision(
        self, e1: Any, rb1: Rigidbody, col1: BoxCollider, 
        e2: Any, rb2: Rigidbody, col2: BoxCollider, 
        normal: Vector2, depth: float
    ):
        """Resolves penetration and calculates bounce."""
        # Determine movement capability
        movable1 = rb1 and rb1.body_type == BodyType.DYNAMIC
        movable2 = rb2 and rb2.body_type == BodyType.DYNAMIC
        
        if not movable1 and not movable2:
            return # Both static/kinematic

        # 1. Positional Correction (prevent sinking)
        correction_percent = 0.8
        slop = 0.01
        correction = max(depth - slop, 0.0) * correction_percent

        if movable1 and movable2:
            # Distribute based on mass (assuming equal mass for now if 0)
            total_mass = (rb1.mass or 1) + (rb2.mass or 1)
            ratio1 = (rb2.mass or 1) / total_mass
            ratio2 = (rb1.mass or 1) / total_mass
            
            if not rb1.freeze_x: e1.x += normal.x * correction * ratio1
            if not rb1.freeze_y: e1.y += normal.y * correction * ratio1
            if not rb2.freeze_x: e2.x -= normal.x * correction * ratio2
            if not rb2.freeze_y: e2.y -= normal.y * correction * ratio2
        elif movable1:
            if not rb1.freeze_x: e1.x += normal.x * correction
            if not rb1.freeze_y: e1.y += normal.y * correction
        elif movable2:
            if not rb2.freeze_x: e2.x -= normal.x * correction
            if not rb2.freeze_y: e2.y -= normal.y * correction

        # 2. Velocity Resolution (Bounce)
        v1 = rb1.velocity if rb1 else Vector2.zero()
        v2 = rb2.velocity if rb2 else Vector2.zero()
        
        rel_vel = v1 - v2
        vel_along_normal = rel_vel.dot(normal)

        # Do not resolve if separating
        if vel_along_normal > 0:
            return

        bounciness = min(col1.material.bounciness, col2.material.bounciness)
        j = -(1 + bounciness) * vel_along_normal
        
        # In a real engine, divide by inverse masses
        # For simple 2D, we distribute
        
        if movable1 and movable2:
            j /= 2.0
            if not rb1.freeze_x: v1.x += j * normal.x
            if not rb1.freeze_y: v1.y += j * normal.y
            if not rb2.freeze_x: v2.x -= j * normal.x
            if not rb2.freeze_y: v2.y -= j * normal.y
        elif movable1:
            if not rb1.freeze_x: v1.x += j * normal.x
            if not rb1.freeze_y: v1.y += j * normal.y
        elif movable2:
            if not rb2.freeze_x: v2.x -= j * normal.x
            if not rb2.freeze_y: v2.y -= j * normal.y

    # --- Sensor Queries ---
    def overlap_rect(self, rect: Tuple[float, float, float, float], mask: Set[str] = None) -> List[Any]:
        """Returns all entities whose bounds overlap the given AABB (left, top, right, bottom)."""
        hits = []
        rx1, ry1, rx2, ry2 = rect
        for e in self._bodies:
            if mask and getattr(e, "layer", "default") not in mask:
                continue
            col = getattr(e, "collider", None)
            if isinstance(col, BoxCollider):
                b = col.get_bounds(Vector2(e.x, e.y))
                if rx1 < b[2] and rx2 > b[0] and ry1 < b[3] and ry2 > b[1]:
                    hits.append(e)
        return hits


PhysicsWorld = PhysicsWorldSystem()
