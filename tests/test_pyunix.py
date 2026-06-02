"""
tests/test_pyunix.py
--------------------
Tests for the Pyunix game framework logic.
Since many of these features rely on pygame display (which requires a window), 
we will mock or only test the logical infrastructure (events, timers, registries).
"""

import pytest

from nestifypy.pyunix import Event, Timer, Scene, Input
from nestifypy.pyunix.sprite import Entity, Sprite, SpriteGroup


def test_event_bus():
    Event.clear()
    
    received_data = []

    @Event.on("test_event")
    def handle(data):
        received_data.append(data)

    Event.emit("test_event", "hello")
    assert received_data == ["hello"]
    
    Event.emit("test_event", "world")
    assert received_data == ["hello", "world"]


def test_timer_manager():
    Timer.clear()
    
    fired = []
    Timer.after(1.0, lambda: fired.append("after"))
    Timer.every(0.5, lambda: fired.append("every"))

    # Initial tick
    Timer.tick(0.1)
    assert fired == []

    # Tick to 0.5s -> every should fire
    Timer.tick(0.4)
    assert fired == ["every"]

    # Tick to 1.0s -> both should fire
    Timer.tick(0.5)
    assert fired == ["every", "after", "every"]


def test_scene_manager():
    # Because Scene is a global API wrapper around SceneManager
    # Let's test the stack logic
    
    # Use a fresh SceneManager to avoid state leaking from other tests
    from nestifypy.pyunix.scene import SceneManager, _SceneAPI
    mgr = SceneManager()
    sc = _SceneAPI(mgr)

    loaded = []
    unloaded = []
    paused = []
    resumed = []

    @sc("menu")
    class MenuScene:
        @sc.load
        def on_load(self):
            loaded.append("menu")

        @sc.unload
        def on_unload(self):
            unloaded.append("menu")

        @sc.pause
        def on_pause(self):
            paused.append("menu")

        @sc.resume
        def on_resume(self):
            resumed.append("menu")

    @sc("game")
    class GameScene:
        @sc.load
        def on_load(self):
            loaded.append("game")

        @sc.unload
        def on_unload(self):
            unloaded.append("game")

    sc.push("menu")
    assert loaded == ["menu"]
    assert paused == []

    # Pushing "game" should pause "menu", then load "game"
    sc.push("game")
    assert loaded == ["menu", "game"]
    assert paused == ["menu"]
    assert unloaded == []        # push pauses, not unloads

    # Popping "game" should unload "game" and resume "menu"
    sc.pop()
    assert unloaded == ["game"]
    assert resumed == ["menu"]


def test_sprite_hooks():
    hooks_fired = []

    class MyEntity(Entity):
        @Sprite.ready
        def on_ready(self):
            hooks_fired.append("ready")

        @Sprite.update
        def on_update(self, dt):
            hooks_fired.append(("update", dt))

    e = MyEntity()
    # Ready is called during __init__
    assert hooks_fired == ["ready"]

    group = SpriteGroup()
    group.add(e)
    group.update(0.16)

    assert hooks_fired == ["ready", ("update", 0.16)]


def test_input_action_mapping():
    # Verify binding logic
    Input.bind_action("jump", "SPACE")
    Input.bind_action("jump", "W")
    
    from nestifypy.pyunix.input import _ACTION_MAP
    assert _ACTION_MAP["jump"] == ["SPACE", "W"]
