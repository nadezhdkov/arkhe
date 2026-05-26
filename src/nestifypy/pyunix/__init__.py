"""
nestifypy.pyunix
-------------
A lightweight, declarative, decorator-driven game framework built on pygame.
"""

from nestifypy.pyunix.app import Game
from nestifypy.pyunix.assets import Assets
from nestifypy.pyunix.audio import Audio
from nestifypy.pyunix.camera import Camera
from nestifypy.pyunix.events import Event
from nestifypy.pyunix.exceptions import PyunixError
from nestifypy.pyunix.input import Input
from nestifypy.pyunix.physics import (
    BodyType,
    BoxCollider,
    CircleCollider,
    Collider,
    CollisionInfo,
    PhysicsMaterial,
    PhysicsWorld,
    Rigidbody,
)
from nestifypy.pyunix.scene import Scene
from nestifypy.pyunix.sprite import Entity, Sprite, SpriteGroup
from nestifypy.pyunix.fonts import Fonts
from nestifypy.pyunix.text import Text
from nestifypy.pyunix.timer import Timer
from nestifypy.pyunix.window import Window

__all__ = [
    "Game",
    "Assets",
    "Audio",
    "Camera",
    "Event",
    "Input",
    "Scene",
    "Entity",
    "Sprite",
    "SpriteGroup",
    "Timer",
    "Window",
    "PyunixError",
    "BodyType",
    "BoxCollider",
    "CircleCollider",
    "Collider",
    "CollisionInfo",
    "PhysicsMaterial",
    "PhysicsWorld",
    "Rigidbody",
    "Fonts",
    "Text",
]
