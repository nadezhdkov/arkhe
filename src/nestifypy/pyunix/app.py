"""
nestifypy.pyunix.app
-----------------
The core engine runtime and Game decorator.

This module provides the core game loop and lifecycle management for Pyunix.
It uses a decorator-based approach (`@Game`) to transform a standard Python class
into a fully functional game application with automatic event dispatching,
fixed/variable timesteps, and layered rendering.

Usage:
    @Game(title="My Game", size=(800, 600))
    class MyGame:
        @Game.update
        def tick(self, dt): ...

    game = MyGame()
    game.run()
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from nestifypy.pyunix.camera import Camera
from nestifypy.pyunix.physics import PhysicsWorld
from nestifypy.pyunix.events import Event
from nestifypy.pyunix.input import (
    _ACTION_HANDLERS,
    _ACTION_MAP,
    _KEY_DOWN_HANDLERS,
    _KEY_HELD_HANDLERS,
    _KEY_UP_HANDLERS,
    _MOUSE_CLICK_HANDLERS,
    _MOUSE_MOTION_HANDLERS,
    _resolve_key,
)
from nestifypy.pyunix.scene import Scene
from nestifypy.pyunix.text import Text
from nestifypy.pyunix.timer import Timer
from nestifypy.pyunix.window import Window

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class _GameRuntime:
    """
    The internal engine loop and event dispatcher.

    This class runs behind the scenes of a class decorated with `@Game`.
    It manages the Pygame initialization, the delta time (`dt`) calculation,
    the fixed physics accumulator, and dispatches calls to the registered hooks.
    """

    def __init__(self, target_instance: Any, fps: int) -> None:
        """
        Initialize the GameRuntime.

        Args:
            target_instance (Any): The instance of the user's game class.
            fps (int): Target frames per second to lock the frame rate.
        """
        self.target = target_instance
        self.fps = fps
        self.running = False
        self.clock: Any = None
        self.fixed_timestep = 1.0 / 60.0  # 60Hz fixed update

        # Registries mapping lifecycle hook names to lists of callables
        self._hooks: Dict[str, List[Callable]] = {
            "start": [],
            "stop": [],
            "pause": [],
            "resume": [],
            "update": [],
            "fixed_update": [],
            "draw": []
        }

        # Layered rendering support: layer_name -> list of (priority, callable)
        self._layers: Dict[str, List[Tuple[int, Callable]]] = {}

        # Managed UI elements
        self._ui_elements: List[Any] = []

        self._scan_methods()

    def _scan_methods(self) -> None:
        """
        Scan the target instance for Pyunix lifecycle and layer decorators.

        Maps decorated methods to the internal `_hooks` and `_layers` dictionaries
        to be called automatically during the game loop.
        """
        for attr_name in dir(self.target):
            # Skip magic methods to prevent unintended property execution
            if attr_name.startswith("__"):
                continue
            try:
                attr = getattr(self.target, attr_name)
                # Standard lifecycle hooks
                if hasattr(attr, "_pyunix_game_hook"):
                    hook = attr._pyunix_game_hook
                    if hook in self._hooks:
                        self._hooks[hook].append(attr)
                # Render layers
                if hasattr(attr, "_pyunix_layer"):
                    layer_name, priority = attr._pyunix_layer
                    if layer_name not in self._layers:
                        self._layers[layer_name] = []
                    self._layers[layer_name].append((priority, attr))
                # Dynamic text labels
                if hasattr(attr, "_pyunix_text_kwargs"):
                    kwargs = attr._pyunix_text_kwargs
                    text_entity = Text(text="", **kwargs)
                    # We store the bound method and the text entity together
                    self._ui_elements.append((attr, text_entity))
            except AttributeError:
                pass

        # Sort layers internally by priority (lower number = drawn first)
        for layer in self._layers.values():
            layer.sort(key=lambda x: x[0])

    def _dispatch(self, hook: str, *args: Any, **kwargs: Any) -> None:
        """
        Execute all methods registered to a specific lifecycle hook.

        Args:
            hook (str): The name of the hook (e.g., "update", "draw").
            *args (Any): Positional arguments to pass to the user's methods.
            **kwargs (Any): Keyword arguments to pass to the user's methods.
        """
        for func in self._hooks[hook]:
            func(*args, **kwargs)

    def _draw_layers(self, screen: Any) -> None:
        """
        Execute draw methods assigned to specific layers in order.

        Args:
            screen (Any): The Pygame surface to draw onto.
        """
        # For Phase 1, just execute everything in self._layers sorted alphabetically
        # In the future, this can be customized with explicit layer ordering
        for layer_name in sorted(self._layers.keys()):
            for _, func in self._layers[layer_name]:
                func(screen)

    def _dispatch_input(self, event: Any) -> None:
        """
        Route raw Pygame events to the registered Pyunix input decorators.

        Args:
            event (pygame.event.Event): The Pygame event object.
        """
        if not _HAS_PYGAME:
            return

        match event.type:
            case pygame.KEYDOWN:
                for func, key_str in _KEY_DOWN_HANDLERS:
                    if event.key == _resolve_key(key_str):
                        func(self.target)
                for func, action_name in _ACTION_HANDLERS:
                    keys = _ACTION_MAP.get(action_name, [])
                    for k in keys:
                        if event.key == _resolve_key(k):
                            func(self.target)

            case pygame.KEYUP:
                for func, key_str in _KEY_UP_HANDLERS:
                    if event.key == _resolve_key(key_str):
                        func(self.target)

            case pygame.MOUSEBUTTONDOWN:
                btn_map = {1: "left", 2: "middle", 3: "right"}
                btn_name = btn_map.get(event.button, "")
                for func, btn in _MOUSE_CLICK_HANDLERS:
                    if btn == btn_name:
                        func(self.target)

            case pygame.MOUSEMOTION:
                for func in _MOUSE_MOTION_HANDLERS:
                    func(self.target, event.pos, event.rel)

    def _process_held_keys(self) -> None:
        """
        Process keyboard keys that fire continuously while being held down.
        """
        if not _HAS_PYGAME:
            return
        keys = pygame.key.get_pressed()
        for func, key_str in _KEY_HELD_HANDLERS:
            code = _resolve_key(key_str)
            if code and keys[code]:
                func(self.target)

    def run(self) -> None:
        """
        The main engine loop.

        Handles timing (`dt`), event pumping, input dispatching, the fixed
        physics accumulator, variable updates, and rendering.
        """
        if not _HAS_PYGAME:
            print("Warning: pygame is not installed. Game loop cannot run.")
            return

        self.clock = pygame.time.Clock()
        self.running = True

        self._dispatch("start")

        accumulator = 0.0
        last_time = time.perf_counter()

        while self.running:
            # 1. Calculate dt
            current_time = time.perf_counter()
            dt = current_time - last_time
            last_time = current_time

            # Prevent death spiral (cap dt if the game lags heavily)
            if dt > 0.25:
                dt = 0.25

            accumulator += dt

            # 2. Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self._dispatch_input(event)

            self._process_held_keys()

            # 3. Fixed Update (Physics/Logic)
            # Runs at a constant rate (e.g., 60 times a second), regardless of framerate
            while accumulator >= self.fixed_timestep:
                PhysicsWorld.step()
                self._dispatch("fixed_update")
                accumulator -= self.fixed_timestep

            # 4. Variable Update
            # Runs exactly once per frame, passing the elapsed time
            self._dispatch("update", dt)
            Timer.tick(dt)
            Camera.update(dt, Window.width, Window.height)

            # Update managed UI elements
            for func, text_entity in self._ui_elements:
                new_text = str(func())
                text_entity.set_text(new_text)

            # 5. Draw
            if Window.surface:
                self._dispatch("draw", Window.surface)
                self._draw_layers(Window.surface)
                # Draw managed UI elements (on top)
                for _, text_entity in self._ui_elements:
                    text_entity.draw(Window.surface)
                pygame.display.flip()

            # 6. Tick
            self.clock.tick(self.fps)

        self._dispatch("stop")
        pygame.quit()


class GameAPI:
    """
    The `@Game` class decorator and associated method lifecycle decorators.

    Provides the frontend API for users to define their game classes and
    register methods to the engine's main loop.
    """

    def __call__(self, title: str = "Nestifypy Game", size: Tuple[int, int] = (800, 600), fps: int = 60, **kwargs: Any) -> Callable:
        """
        Class decorator that transforms a standard class into a runnable game.

        Automatically creates the window and injects `.run()` and `.quit()`
        methods into the decorated class.

        Args:
            title (str): The window title. Defaults to "Nestifypy Game".
            size (Tuple[int, int]): Window resolution (width, height). Defaults to (800, 600).
            fps (int): Target frames per second. Defaults to 60.
            **kwargs (Any): Additional arguments passed to Pygame window creation (e.g., flags).

        Returns:
            Callable: The modified class wrapper.
        """
        def decorator(cls: type) -> type:
            original_init = cls.__init__

            def new_init(self_obj: Any, *args: Any, **kw: Any) -> None:
                Window.create(title, size, **kwargs)
                self_obj._runtime = _GameRuntime(self_obj, fps)
                # Call original init
                if original_init is not object.__init__:
                    original_init(self_obj, *args, **kw)

            def run(self_obj: Any) -> None:
                """Start the game loop."""
                self_obj._runtime.run()

            def quit(self_obj: Any) -> None:
                """Flag the game loop to exit gracefully on the next frame."""
                self_obj._runtime.running = False

            cls.__init__ = new_init  # type: ignore
            cls.run = run            # type: ignore
            cls.quit = quit          # type: ignore
            return cls

        return decorator

    # ── Lifecycle Decorators ──────────────────

    @staticmethod
    def start(func: Callable) -> Callable:
        """
        Decorator for a method called once right before the game loop begins.
        """
        func._pyunix_game_hook = "start"
        return func

    @staticmethod
    def stop(func: Callable) -> Callable:
        """
        Decorator for a method called once right after the game loop exits.
        """
        func._pyunix_game_hook = "stop"
        return func

    @staticmethod
    def update(func: Callable) -> Callable:
        """
        Decorator for a method called every frame.
        The decorated method must accept a `dt` (delta time) float argument.
        """
        func._pyunix_game_hook = "update"
        return func

    @staticmethod
    def fixed_update(func: Callable) -> Callable:
        """
        Decorator for a method called at a fixed timestep (e.g., 60 times a second).
        Best used for deterministic physics or rigid movement calculations.
        """
        func._pyunix_game_hook = "fixed_update"
        return func

    @staticmethod
    def draw(func: Callable) -> Callable:
        """
        Decorator for a method called every frame to handle rendering.
        The decorated method must accept a `screen` (Surface) argument.
        """
        func._pyunix_game_hook = "draw"
        return func

    @staticmethod
    def layer(name: str, priority: int = 0) -> Callable:
        """
        Register a draw method to a specific rendering layer.

        Layers are drawn alphabetically by default, and by priority within
        the same layer name.

        Args:
            name (str): The name of the layer.
            priority (int): Draw order priority (lower numbers draw first/beneath). Defaults to 0.

        Returns:
            Callable: The layer method decorator.
        """
        def decorator(func: Callable) -> Callable:
            func._pyunix_layer = (name, priority)
            return func
        return decorator

    @staticmethod
    def text(**kwargs: Any) -> Callable:
        """
        Decorator to auto-render a dynamic text label every frame.
        The decorated method must return a string.
        kwargs are passed directly to the Text entity constructor (e.g., x, y, font, size).
        """
        def decorator(func: Callable) -> Callable:
            func._pyunix_text_kwargs = kwargs
            return func
        return decorator

# Global singleton
Game = GameAPI()