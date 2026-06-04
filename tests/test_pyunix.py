"""
tests/test_pyunix.py
--------------------
Tests for the Pyunix v2.0 game framework logic.

Since many features rely on a pygame display window, we test only the
logical infrastructure: events, timers, scenes, entities, components,
render systems, and UI.
"""

import pytest
from arkhe.pyunix import Event, Timer, Scene, Input
from arkhe.pyunix.sprite import Entity, Sprite, SpriteGroup
from arkhe.pyunix.entity.component import Component, AutoDestroy, Floater
from arkhe.pyunix.ui.view import UIView, UIElement
from arkhe.pyunix.ui.layout import Column, Row, Stack, Spacer
from arkhe.pyunix.math import Vector2, Color


# ────────────────────────────────────────────────────────────
# Event System
# ────────────────────────────────────────────────────────────

def test_event_emit_and_receive():
    Event.clear()
    received = []

    @Event.on("test_event")
    def handle(data):
        received.append(data)

    Event.emit("test_event", "hello")
    assert received == ["hello"]

    Event.emit("test_event", "world")
    assert received == ["hello", "world"]


def test_event_once():
    Event.clear()
    fired = []

    @Event.once("once_event")
    def handle():
        fired.append(True)

    Event.emit("once_event")
    Event.emit("once_event")

    # Should only fire once
    assert len(fired) == 1


def test_event_clear():
    Event.clear()
    fired = []

    @Event.on("removable")
    def handle():
        fired.append(True)

    Event.clear("removable")
    Event.emit("removable")
    assert fired == []


# ────────────────────────────────────────────────────────────
# Timer System
# ────────────────────────────────────────────────────────────

def test_timer_after():
    Timer.clear()
    fired = []
    Timer.after(1.0, lambda: fired.append("after"))

    Timer.tick(0.5)
    assert fired == []

    Timer.tick(0.5)
    assert fired == ["after"]


def test_timer_every():
    Timer.clear()
    fired = []
    Timer.every(0.5, lambda: fired.append("tick"))

    Timer.tick(0.5)
    assert fired == ["tick"]

    Timer.tick(0.5)
    assert fired == ["tick", "tick"]


def test_timer_combined():
    Timer.clear()
    fired = []

    Timer.after(1.0, lambda: fired.append("after"))
    Timer.every(0.5, lambda: fired.append("every"))

    Timer.tick(0.5)
    assert fired == ["every"]

    Timer.tick(0.5)
    assert fired == ["every", "after", "every"]


# ────────────────────────────────────────────────────────────
# Scene Manager
# ────────────────────────────────────────────────────────────

def test_scene_push_pop_lifecycle():
    from arkhe.pyunix.scene import SceneManager, _SceneAPI
    mgr = SceneManager()
    sc = _SceneAPI(mgr)

    loaded, unloaded, paused, resumed = [], [], [], []

    @sc("menu")
    class MenuScene:
        @sc.load
        def on_load(self): loaded.append("menu")

        @sc.unload
        def on_unload(self): unloaded.append("menu")

        @sc.pause
        def on_pause(self): paused.append("menu")

        @sc.resume
        def on_resume(self): resumed.append("menu")

    @sc("game")
    class GameScene:
        @sc.load
        def on_load(self): loaded.append("game")

        @sc.unload
        def on_unload(self): unloaded.append("game")

    sc.push("menu")
    assert loaded == ["menu"]
    assert paused == []

    # Pushing "game" should pause "menu" then load "game"
    sc.push("game")
    assert loaded == ["menu", "game"]
    assert paused == ["menu"]
    assert unloaded == []

    # Popping "game" should unload "game" and resume "menu"
    sc.pop()
    assert unloaded == ["game"]
    assert resumed == ["menu"]


# ────────────────────────────────────────────────────────────
# Entity & Sprite Hooks
# ────────────────────────────────────────────────────────────

def test_sprite_ready_called_on_init():
    hooks = []

    class MyEntity(Entity):
        @Sprite.ready
        def on_ready(self):
            hooks.append("ready")

    MyEntity()
    assert hooks == ["ready"]


def test_sprite_update_via_group():
    hooks = []

    class MyEntity(Entity):
        @Sprite.ready
        def on_ready(self):
            hooks.append("ready")

        @Sprite.update
        def on_update(self, dt):
            hooks.append(("update", dt))

    e = MyEntity()
    assert hooks == ["ready"]

    group = SpriteGroup()
    group.add(e)
    group.update(0.16)

    assert hooks == ["ready", ("update", 0.16)]


def test_sprite_draw_has_no_surface_param():
    """@Sprite.draw methods should NOT receive a surface param in v2.0."""
    hooks = []

    class MyEntity(Entity):
        @Sprite.draw
        def on_draw(self):
            hooks.append("draw")

    e = MyEntity()
    e._dispatch("draw")
    assert hooks == ["draw"]


def test_entity_active_toggle():
    updated = []

    class MyEntity(Entity):
        @Sprite.update
        def on_update(self, dt):
            updated.append(dt)

    e = MyEntity()
    e.active = False
    e._dispatch("update", 0.1)
    assert updated == []

    e.active = True
    e._dispatch("update", 0.1)
    assert updated == [0.1]


# ────────────────────────────────────────────────────────────
# Component System (v2.0)
# ────────────────────────────────────────────────────────────

def test_component_attach_and_get():
    class Health(Component):
        def __init__(self, max_hp: int = 100):
            super().__init__()
            self.hp = max_hp

    entity = Entity()
    entity.add_component(Health(50))

    comp = entity.get_component(Health)
    assert comp is not None
    assert comp.hp == 50


def test_component_entity_reference():
    class MyComp(Component):
        pass

    entity = Entity()
    comp = MyComp()
    entity.add_component(comp)

    assert comp.entity is entity


def test_component_on_attach_called():
    attached = []

    class MyComp(Component):
        def on_attach(self):
            attached.append(True)

    entity = Entity()
    entity.add_component(MyComp())
    assert attached == [True]


def test_component_on_detach_called():
    detached = []

    class MyComp(Component):
        def on_detach(self):
            detached.append(True)

    entity = Entity()
    entity.add_component(MyComp())
    entity.remove_component(MyComp)
    assert detached == [True]


def test_component_update_dispatched():
    """Ensure that entity._dispatch('update', dt) propagates to components."""
    updates = []

    class Counter(Component):
        def on_update(self, dt: float):
            updates.append(dt)

    entity = Entity()
    entity.add_component(Counter())
    entity._dispatch("update", 0.5)

    assert updates == [0.5]


def test_component_one_per_type():
    """Only one component of the same type is allowed."""

    class MyComp(Component):
        def __init__(self, val):
            super().__init__()
            self.val = val

    entity = Entity()
    entity.add_component(MyComp(1))
    entity.add_component(MyComp(2))  # should overwrite

    assert entity.get_component(MyComp).val == 2


def test_has_component():
    class MyComp(Component):
        pass

    entity = Entity()
    assert not entity.has_component(MyComp)
    entity.add_component(MyComp())
    assert entity.has_component(MyComp)


def test_auto_destroy_component():
    """AutoDestroy should deactivate the entity after its timer expires."""
    entity = Entity()
    entity.add_component(AutoDestroy(after=0.5))

    entity._dispatch("update", 0.3)
    assert entity.active  # not yet

    entity._dispatch("update", 0.3)
    assert not entity.active  # should be destroyed


def test_floater_component_modifies_y():
    entity = Entity(x=0, y=100)
    entity.add_component(Floater(amplitude=10, speed=1000))

    initial_y = entity.y
    entity._dispatch("update", 0.1)

    # y should have moved from its original position
    assert entity.y != initial_y


# ────────────────────────────────────────────────────────────
# SpriteGroup
# ────────────────────────────────────────────────────────────

def test_sprite_group_find_by_tag():
    group = SpriteGroup()

    e1 = Entity(tag="enemy")
    e2 = Entity(tag="player")
    e3 = Entity(tag="enemy")
    group.add(e1, e2, e3)

    enemies = group.find_by_tag("enemy")
    assert len(enemies) == 2
    assert e2 not in enemies


def test_sprite_group_purge_destroyed():
    group = SpriteGroup()

    e1 = Entity()
    e2 = Entity()
    group.add(e1, e2)

    e1.active = False
    group.purge_destroyed()

    assert len(group) == 1
    assert e2 in group


# ────────────────────────────────────────────────────────────
# UI System (v2.0)
# ────────────────────────────────────────────────────────────

def test_uielement_base():
    el = UIElement()
    el.update(0.1)       # should not raise
    el.draw(0, 0)        # should not raise
    assert el.handle_event(None) is False


def test_uiview_dirty_rebuild():
    rebuilt = []

    class MyView(UIView):
        def rebuild(self):
            rebuilt.append(True)
            return UIElement()

    view = MyView()
    view.draw(0, 0)  # triggers initial build
    assert len(rebuilt) == 1

    view.draw(0, 0)  # no rebuild needed
    assert len(rebuilt) == 1

    view.set_dirty()
    view.draw(0, 0)  # should rebuild again
    assert len(rebuilt) == 2


def test_uiview_subclass_flexibility():
    """UIView subclasses should support both rebuild() override and state management."""

    class CounterView(UIView):
        def __init__(self):
            super().__init__()
            self.count = 0

        def increment(self):
            self.count += 1
            self.set_dirty()

        def rebuild(self):
            return UIElement()

    view = CounterView()
    view.draw(0, 0)

    view.increment()
    assert view._dirty is True


def test_layout_column_children():
    children = [UIElement(), UIElement()]
    col = Column(children, gap=10)
    assert len(col.children) == 2
    col.update(0.0)  # should not raise


def test_layout_row_children():
    children = [UIElement(), UIElement(), UIElement()]
    row = Row(children, gap=8)
    assert len(row.children) == 3
    row.update(0.0)


def test_layout_stack():
    children = [UIElement(), UIElement()]
    stack = Stack(children)
    assert len(stack.children) == 2
    stack.update(0.0)


def test_spacer():
    spacer = Spacer(width=50, height=20)
    assert spacer.width == 50
    assert spacer.height == 20
    spacer.draw(0, 0)  # should not raise


# ────────────────────────────────────────────────────────────
# Math
# ────────────────────────────────────────────────────────────

def test_vector2_operations():
    v1 = Vector2(3, 4)
    assert v1.magnitude == pytest.approx(5.0)
    assert v1.normalized.magnitude == pytest.approx(1.0, abs=1e-6)

    v2 = Vector2(1, 2)
    result = v1 + v2
    assert result.x == 4 and result.y == 6


def test_color_from_hex():
    c = Color.from_hex("#FF0000")
    r, g, b = c.to_rgb()
    assert r == 255 and g == 0 and b == 0


def test_color_lerp():
    black = Color(0, 0, 0)
    white = Color(255, 255, 255)
    mid = black.lerp(white, 0.5)
    r, g, b = mid.to_rgb()
    assert 120 <= r <= 135


# ────────────────────────────────────────────────────────────
# Input
# ────────────────────────────────────────────────────────────

def test_input_action_mapping():
    Input.bind_action("jump", "SPACE")
    Input.bind_action("jump", "W")

    from arkhe.pyunix.input import _ACTION_MAP
    assert _ACTION_MAP["jump"] == ["SPACE", "W"]
