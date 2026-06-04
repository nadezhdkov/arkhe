"""
arkhe.pyunix.transform
--------------------------
Transform component — the spatial backbone of every Entity.

Every Entity owns exactly one Transform. It stores and manages world-space
position, rotation, and scale, and provides a Unity-style parent/child
hierarchy so child entities automatically inherit their parent's transformation.

Usage:
    entity.transform.position = Vector2(100, 200)
    entity.transform.rotation = 45.0          # degrees
    entity.transform.scale    = Vector2(2, 2) # 2× uniform scale

    # Parenting
    child.transform.set_parent(parent.transform)
    # child now moves with parent automatically
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from arkhe.pyunix.math import Vector2


class Transform:
    """
    Spatial component attached to every Entity.

    Provides local/world position, rotation, and scale plus parent/child
    hierarchy. Local values are relative to the parent; world values are
    calculated by composing the parent chain.
    """

    __slots__ = (
        "_local_position", "_local_rotation", "_local_scale",
        "_parent", "_children", "_entity_ref",
    )

    def __init__(
        self,
        position: Vector2 = None,
        rotation: float = 0.0,
        scale: Vector2 = None,
    ) -> None:
        self._local_position: Vector2 = position or Vector2.zero()
        self._local_rotation: float = rotation        # degrees
        self._local_scale: Vector2 = scale or Vector2.one()
        self._parent: Optional["Transform"] = None
        self._children: List["Transform"] = []
        self._entity_ref = None  # back-reference set by Entity

    # ── Local Space ──────────────────────────

    @property
    def local_position(self) -> Vector2:
        return self._local_position

    @local_position.setter
    def local_position(self, value: Vector2) -> None:
        self._local_position = value

    @property
    def local_rotation(self) -> float:
        return self._local_rotation

    @local_rotation.setter
    def local_rotation(self, value: float) -> None:
        self._local_rotation = value % 360.0

    @property
    def local_scale(self) -> Vector2:
        return self._local_scale

    @local_scale.setter
    def local_scale(self, value: Vector2) -> None:
        self._local_scale = value

    # ── World Space (composed up the hierarchy) ──

    @property
    def position(self) -> Vector2:
        """World-space position (accounts for parent chain)."""
        if self._parent is None:
            return self._local_position
        # Rotate local position by parent's world rotation, then add parent's world position
        parent_world = self._parent.position
        parent_rot   = self._parent.rotation
        parent_scale = self._parent.scale
        # Scale first
        scaled = Vector2(
            self._local_position.x * parent_scale.x,
            self._local_position.y * parent_scale.y,
        )
        # Then rotate around parent origin
        rotated = scaled.rotate(parent_rot)
        return parent_world + rotated

    @position.setter
    def position(self, world_pos: Vector2) -> None:
        """Set world position; converts to local space if parented."""
        if self._parent is None:
            self._local_position = world_pos
        else:
            parent_world = self._parent.position
            parent_rot   = self._parent.rotation
            parent_scale = self._parent.scale
            diff = world_pos - parent_world
            local_rotated = diff.rotate(-parent_rot)
            self._local_position = Vector2(
                local_rotated.x / parent_scale.x if parent_scale.x != 0 else 0,
                local_rotated.y / parent_scale.y if parent_scale.y != 0 else 0,
            )

    @property
    def rotation(self) -> float:
        """World-space rotation in degrees."""
        if self._parent is None:
            return self._local_rotation
        return (self._parent.rotation + self._local_rotation) % 360.0

    @rotation.setter
    def rotation(self, world_rot: float) -> None:
        if self._parent is None:
            self._local_rotation = world_rot % 360.0
        else:
            self._local_rotation = (world_rot - self._parent.rotation) % 360.0

    @property
    def scale(self) -> Vector2:
        """World-space scale (multiplied up the parent chain)."""
        if self._parent is None:
            return self._local_scale
        ps = self._parent.scale
        return Vector2(self._local_scale.x * ps.x, self._local_scale.y * ps.y)

    @scale.setter
    def scale(self, world_scale: Vector2) -> None:
        if self._parent is None:
            self._local_scale = world_scale
        else:
            ps = self._parent.scale
            self._local_scale = Vector2(
                world_scale.x / ps.x if ps.x != 0 else 0,
                world_scale.y / ps.y if ps.y != 0 else 0,
            )

    # Convenience aliases matching Unity muscle memory
    @property
    def x(self) -> float:
        return self.position.x

    @x.setter
    def x(self, value: float) -> None:
        self.position = Vector2(value, self.position.y)

    @property
    def y(self) -> float:
        return self.position.y

    @y.setter
    def y(self, value: float) -> None:
        self.position = Vector2(self.position.x, value)

    # ── Hierarchy ────────────────────────────

    def set_parent(self, parent: Optional["Transform"], keep_world_position: bool = True) -> None:
        """
        Attach this transform to a parent.

        Args:
            parent: The new parent Transform, or None to detach.
            keep_world_position: If True, adjusts local position so the entity
                stays at the same world-space position after re-parenting.
        """
        if self._parent is parent:
            return

        world_pos = self.position if keep_world_position else None
        world_rot = self.rotation if keep_world_position else None

        # Remove from old parent
        if self._parent is not None:
            self._parent._children = [c for c in self._parent._children if c is not self]

        self._parent = parent

        if parent is not None:
            parent._children.append(self)

        # Restore world position in new parent space
        if keep_world_position and world_pos is not None:
            self.position = world_pos
            self.rotation = world_rot  # type: ignore

    @property
    def parent(self) -> Optional["Transform"]:
        return self._parent

    @property
    def children(self) -> List["Transform"]:
        return list(self._children)

    @property
    def root(self) -> "Transform":
        """Walk up the hierarchy to find the root transform."""
        t = self
        while t._parent is not None:
            t = t._parent
        return t

    # ── Helpers ──────────────────────────────

    def translate(self, delta: Vector2) -> None:
        """Move by `delta` in world space."""
        self.position = self.position + delta

    def look_at(self, target: Vector2) -> None:
        """Rotate to face `target` world position."""
        diff = target - self.position
        self.rotation = math.degrees(math.atan2(diff.y, diff.x))

    def forward(self) -> Vector2:
        """Return the unit vector pointing in the entity's facing direction."""
        return Vector2.from_angle(self.rotation)

    def to_local(self, world_point: Vector2) -> Vector2:
        """Convert a world-space point to local space."""
        diff = world_point - self.position
        return diff.rotate(-self.rotation)

    def to_world(self, local_point: Vector2) -> Vector2:
        """Convert a local-space point to world space."""
        return self.position + local_point.rotate(self.rotation)

    def __repr__(self) -> str:
        return (f"Transform(pos={self.position}, "
                f"rot={self.rotation:.1f}°, scale={self.scale})")
