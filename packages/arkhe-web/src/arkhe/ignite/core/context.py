from typing import Any, Type

from arkhe.ignite.core.container import Container
from arkhe.ignite.config.yaml_loader import YamlLoader
from arkhe.ignite.config.properties import Properties
from arkhe.ignite.config.profiles import ProfileResolver
from arkhe.ignite.config.resolver import ValueResolver
from arkhe.ignite.events.event_bus import EventBus


class ApplicationContext:
    """
    The central application context — equivalent to Spring's ApplicationContext.

    Responsibilities:

    - Manages the IOC container
    - Loads and exposes configuration
    - Exposes the event bus
    - Provides bean access
    """

    def __init__(self, config_dir: str = "."):
        self._container = Container()
        self._event_bus = EventBus()

        # Config
        profile = ProfileResolver.resolve()
        self._yaml_loader = YamlLoader(config_dir)
        self._yaml_loader.load(profile=profile)
        self._properties = Properties(self._yaml_loader)
        self._value_resolver = ValueResolver(self._properties)

        # Self-register
        self._container.register_instance(ApplicationContext, self)
        self._container.register_instance(EventBus, self._event_bus)
        self._container.register_instance(Properties, self._properties)

    def get_bean(self, cls: Type) -> Any:
        return self._container.get(cls)

    def register_bean(self, cls: Type, **kwargs):
        from arkhe.ignite.di.scopes import Scope
        scope = kwargs.get("scope", Scope.SINGLETON)
        metadata = kwargs.get("metadata", {})
        self._container.register(cls, scope=scope, metadata=metadata)

    def get_property(self, key: str, default: Any = None) -> Any:
        return self._properties.get(key, default)

    def get_value(self, key: str, required: bool = True) -> Any:
        return self._value_resolver.resolve(key, required=required)

    @property
    def event_bus(self) -> "EventBus":
        return self._event_bus

    @property
    def container(self) -> Container:
        return self._container

    @property
    def properties(self) -> Properties:
        return self._properties
