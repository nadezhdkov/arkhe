"""
arkhe.pyunix
----------------
A professional, decorator-driven 2D game framework built on pygame.

Designed to feel like a lightweight blend of Unity and Godot in pure Python.

Quick start:
    from arkhe.pyunix import *

    @Game(title="My Game", size=(960, 540))
    class MyGame:

        @Game.start
        def on_start(self):
            self.player = Player()
            Input.bind_action("jump", "SPACE", "W")
            Input.bind_axis("move", positive="RIGHT", negative="LEFT")

        @Game.update
        def on_update(self, dt):
            self.player._dispatch("update", dt)

        @Game.draw
        def on_draw(self, screen):
            Window.clear((30, 30, 40))
            self.player._dispatch("draw", screen)

    MyGame().run()
"""

# ── Core ──────────────────────────────────────────────────────────────────
from arkhe.pyunix.exceptions import (
    PyunixError,
    WindowError,
    AssetError,
    SceneError,
    InputError,
    AudioError,
    AnimationError,
    ComponentError,
)

# ── Math ─────────────────────────────────────────────────────────────────
from arkhe.pyunix.math import Vector2, Color

# ── Transform ────────────────────────────────────────────────────────────
from arkhe.pyunix.transform import Transform

# ── App / Window ─────────────────────────────────────────────────────────
from arkhe.pyunix.app import Game
from arkhe.pyunix.window import Window

# ── Input ────────────────────────────────────────────────────────────────
from arkhe.pyunix.input import Input

# ── Assets ───────────────────────────────────────────────────────────────
from arkhe.pyunix.assets import Assets
from arkhe.pyunix.fonts import Fonts
from arkhe.pyunix.audio import Audio

# ── Entities, Groups & Components ─────────────────────────────────────────
from arkhe.pyunix.sprite import Entity, Sprite, SpriteGroup
from arkhe.pyunix.entity.component import Component

# ── Animation & Tweening ─────────────────────────────────────────────────
from arkhe.pyunix.animation import Animator, AnimationClip
from arkhe.pyunix.tween import Tween, TweenManager, Ease

# ── Camera ───────────────────────────────────────────────────────────────
from arkhe.pyunix.camera import Camera

# ── Rendering ────────────────────────────────────────────────────────────
from arkhe.pyunix.render.canvas import Canvas
from arkhe.pyunix.render.draw import Draw
from arkhe.pyunix.render.shapes import Rectangle, Circle, Line, Polygon, Capsule, Triangle
from arkhe.pyunix.text import Text
from arkhe.pyunix.particles import ParticleSystem

# ── UI ───────────────────────────────────────────────────────────────────
from arkhe.pyunix.ui import (
    UIView, UI, Column, Row, Stack, Spacer, Label, Button, Panel
)

# ── Tilemap ──────────────────────────────────────────────────────────────
from arkhe.pyunix.tilemap import TileMap, TileSet

# ── Physics ──────────────────────────────────────────────────────────────
from arkhe.pyunix.physics import (
    BodyType,
    BoxCollider,
    CircleCollider,
    Collider,
    CollisionInfo,
    PhysicsMaterial,
    PhysicsWorld,
    Rigidbody,
)

# ── Save ─────────────────────────────────────────────────────────────────
from arkhe.pyunix.save import SaveSystem, Save

# ── Scene management ─────────────────────────────────────────────────────
from arkhe.pyunix.scene import Scene

# ── Events & Timers ──────────────────────────────────────────────────────
from arkhe.pyunix.events import Event
from arkhe.pyunix.timer import Timer


__all__ = [
    # Errors
    "PyunixError", "WindowError", "AssetError", "SceneError",
    "InputError", "AudioError", "AnimationError", "ComponentError",
    # Math
    "Vector2", "Color",
    # Transform
    "Transform",
    # App / Window
    "Game", "Window",
    # Input
    "Input",
    # Assets / Audio
    "Assets", "Fonts", "Audio",
    # Entities & Components
    "Entity", "Sprite", "SpriteGroup", "Component",
    # Animation
    "Animator", "AnimationClip",
    # Tweening
    "Tween", "TweenManager", "Ease",
    # Camera
    "Camera",
    # Rendering
    "Canvas", "Draw", "Rectangle", "Circle", "Line", "Polygon", "Capsule", "Triangle",
    "Text", "ParticleSystem",
    # UI
    "UIView", "UI", "Column", "Row", "Stack", "Spacer", "Label", "Button", "Panel",
    # Tilemap
    "TileMap", "TileSet",
    # Physics
    "BodyType", "BoxCollider", "CircleCollider", "Collider",
    "CollisionInfo", "PhysicsMaterial", "PhysicsWorld", "Rigidbody",
    # Save
    "Save", "SaveSystem",
    # Scenes
    "Scene",
    # Events & Timers
    "Event", "Timer",
]

__version__ = "2.0.1"
