"""
nestifypy.pyunix.scene
-------------------
Scene and state management system.

This module provides a stack-based scene manager, allowing isolated game
or application states to be pushed, popped, and switched smoothly.
It supports load and unload lifecycle hooks via decorators.

Usage:
    @Scene("menu")
    class MenuScene:
        @Scene.load
        def setup(self):
            print("Menu loaded")

        @Scene.unload
        def cleanup(self):
            print("Menu unloaded")

    Scene.push("menu")
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from nestifypy.pyunix.exceptions import SceneError


class SceneManager:
    """
    Manages isolated game scenes using a stack architecture.

    Attributes:
        _scenes (Dict[str, Any]): A registry mapping scene names to their classes.
        _stack (List[str]): The stack of currently active scene names.
        _instances (Dict[str, Any]): A cache of instantiated scene objects.
    """

    __slots__ = ("_scenes", "_stack", "_instances")

    def __init__(self) -> None:
        """Initialize an empty SceneManager."""
        self._scenes: Dict[str, Any] = {}
        self._stack: List[str] = []
        self._instances: Dict[str, Any] = {}

    def register(self, name: str) -> Callable:
        """
        Decorator to register a scene class under a specific name.

        Args:
            name (str): The unique string identifier for the scene.

        Returns:
            Callable: The class decorator.
        """
        def decorator(cls: Any) -> Any:
            self._scenes[name] = cls
            return cls
        return decorator

    def load_hook(self, func: Callable) -> Callable:
        """
        Decorator to mark a method as the scene's load hook.

        The load hook is automatically called when the scene is pushed
        onto the stack or becomes the active scene again.

        Args:
            func (Callable): The method to decorate.

        Returns:
            Callable: The decorated method with a special metadata attribute.
        """
        func._pyunix_scene = "load"
        return func

    def unload_hook(self, func: Callable) -> Callable:
        """
        Decorator to mark a method as the scene's unload hook.

        The unload hook is automatically called when the scene is popped
        from the stack or hidden by another scene being pushed.

        Args:
            func (Callable): The method to decorate.

        Returns:
            Callable: The decorated method with a special metadata attribute.
        """
        func._pyunix_scene = "unload"
        return func

    def push(self, name: str) -> None:
        """
        Push a scene onto the stack and transition to it.

        This will trigger the `unload` hook of the current scene (if any),
        instantiate the new scene if it hasn't been created yet, and trigger
        the `load` hook of the new scene.

        Args:
            name (str): The name of the scene to push.

        Raises:
            SceneError: If the requested scene name has not been registered.
        """
        if name not in self._scenes:
            raise SceneError(f"Scene not found: {name}")

        # Unload current scene if any
        if self._stack:
            current_name = self._stack[-1]
            if current_name in self._instances:
                self._dispatch(self._instances[current_name], "unload")

        self._stack.append(name)

        # Create instance if needed
        if name not in self._instances:
            self._instances[name] = self._scenes[name]()

        # Load new scene
        self._dispatch(self._instances[name], "load")

    def pop(self) -> None:
        """
        Pop the current scene off the stack and return to the previous one.

        This will trigger the `unload` hook of the current scene, remove it
        from the stack, and then trigger the `load` hook of the scene beneath it.
        Does nothing if the stack is empty.
        """
        if not self._stack:
            return

        current_name = self._stack.pop()
        if current_name in self._instances:
            self._dispatch(self._instances[current_name], "unload")

        if self._stack:
            prev_name = self._stack[-1]
            if prev_name in self._instances:
                self._dispatch(self._instances[prev_name], "load")

    def switch(self, name: str) -> None:
        """
        Replace the current scene with a new one.

        This effectively calls `pop()` followed by `push()`, maintaining the
        same stack depth.

        Args:
            name (str): The name of the new scene to switch to.
        """
        if self._stack:
            self.pop()
        self.push(name)

    @property
    def current(self) -> Any:
        """
        Get the currently active scene instance.

        Returns:
            Any: The instance of the scene currently at the top of the stack,
                 or None if the stack is empty.
        """
        if not self._stack:
            return None
        return self._instances.get(self._stack[-1])

    def _dispatch(self, instance: Any, hook_name: str) -> None:
        """
        Find and call a decorated hook method on an instance.

        Args:
            instance (Any): The scene instance to inspect.
            hook_name (str): The type of hook to look for ("load" or "unload").
        """
        for attr_name in dir(instance):
            if attr_name.startswith("__"):
                continue
            try:
                attr = getattr(instance, attr_name)
                if getattr(attr, "_pyunix_scene", None) == hook_name:
                    attr()
            except AttributeError:
                pass


class _SceneAPI:
    """
    A unified facade allowing `Scene` to be used both as a class decorator
    and as a namespace for scene management methods.
    """

    def __init__(self, manager: SceneManager) -> None:
        """
        Initialize the SceneAPI facade.

        Args:
            manager (SceneManager): The underlying scene manager instance.
        """
        self._manager = manager

    def __call__(self, name: str) -> Callable:
        """
        Enable using `@Scene("name")` to register a class.

        Args:
            name (str): The name to register the scene under.

        Returns:
            Callable: The class decorator.
        """
        return self._manager.register(name)

    @property
    def load(self) -> Callable:
        """
        Access the load hook decorator (`@Scene.load`).

        Returns:
            Callable: The load hook decorator.
        """
        return self._manager.load_hook

    @property
    def unload(self) -> Callable:
        """
        Access the unload hook decorator (`@Scene.unload`).

        Returns:
            Callable: The unload hook decorator.
        """
        return self._manager.unload_hook

    def push(self, name: str) -> None:
        """
        Push a scene onto the stack.

        Args:
            name (str): The name of the scene to push.
        """
        self._manager.push(name)

    def pop(self) -> None:
        """Pop the current scene off the stack."""
        self._manager.pop()

    def switch(self, name: str) -> None:
        """
        Replace the current scene with a new one.

        Args:
            name (str): The name of the scene to switch to.
        """
        self._manager.switch(name)

    @property
    def current(self) -> Any:
        """
        Get the currently active scene instance.

        Returns:
            Any: The active scene instance or None.
        """
        return self._manager.current


# Global singleton
# Hack to allow both Scene("name") and Scene.load decorators
_manager = SceneManager()
Scene = _SceneAPI(_manager)