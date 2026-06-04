import asyncio
import inspect
from typing import List, Optional

from arkhe.ignite.core.context import ApplicationContext
from arkhe.ignite.core.lifecycle import run_post_construct, run_pre_destroy
from arkhe.ignite.core.boot import set_context
from arkhe.ignite.decorators.component import _COMPONENT_REGISTRY
from arkhe.ignite.events.application_events import (
    ApplicationStartedEvent,
    ApplicationReadyEvent,
    ApplicationStoppingEvent,
)
from arkhe.ignite.scheduler.tasks import TaskRegistry, ScheduledTask
from arkhe.ignite.scheduler.executor import SchedulerExecutor


class Application:
    """
    The main entry point for a arkhe.ignite application.

    Usage::

        app = Application.run()

    With web server::

        app = Application.run(web=True)
    """

    def __init__(self, config_dir: str = ".", starters: List[str] = None):
        self._config_dir = config_dir
        self._starters = starters or []
        self._context: Optional[ApplicationContext] = None
        self._scheduler: Optional[SchedulerExecutor] = None

    @classmethod
    def run(
        cls,
        config_dir: str = ".",
        web: bool = False,
        starters: List[str] = None,
    ) -> "Application":
        app = cls(config_dir=config_dir, starters=starters or [])
        asyncio.run(app._boot(web=web))
        return app

    async def _boot(self, web: bool = False):
        print("\n  🔥 arkhe.ignite — Starting...\n")

        # 1. Build application context
        self._context = ApplicationContext(config_dir=self._config_dir)
        set_context(self._context)

        # 2. Register all auto-discovered components
        self._register_components()

        # 3. Run @Bean factory methods from @Configuration classes
        self._process_configurations()

        # 4. Run starters / auto-configuration
        self._run_starters()

        # 5. Instantiate all beans and run @PostConstruct
        await self._initialize_beans()

        # 6. Wire @EventListener functions
        self._wire_event_listeners()

        # 7. Start scheduler
        await self._start_scheduler()

        # 8. Publish lifecycle events
        await self._context.event_bus.publish(ApplicationStartedEvent())
        await self._context.event_bus.publish(ApplicationReadyEvent())

        props = self._context.properties
        port = props.get_int("server.port", 8080)
        print(f"  ✅ Application started successfully on port {port}\n")

        # 9. Start web server (blocking)
        if web:
            from arkhe.ignite.web.server import WebServer
            if self._context.container.has(WebServer):
                server = self._context.get_bean(WebServer)
                await server.run()

    def _register_components(self):
        for cls in _COMPONENT_REGISTRY:
            scope = getattr(cls, "__arkhe_scope__", "singleton")
            meta = getattr(cls, "__arkhe_metadata__", {})
            self._context.container.register(cls, scope=scope, metadata=meta)

    def _process_configurations(self):
        """Instantiate @Configuration classes and register their @Bean methods."""
        for cls, definition in list(self._context.container.registry.all_definitions().items()):
            meta = definition.get("metadata", {})
            if meta.get("stereotype") != "configuration":
                continue
            instance = self._context.get_bean(cls)
            for name in dir(instance):
                method = getattr(instance, name, None)
                if callable(method) and getattr(method, "__arkhe_bean__", False):
                    bean_instance = method()
                    self._context.container.register_instance(type(bean_instance), bean_instance)

    def _run_starters(self):
        starter_map = {
            "web": "arkhe.ignite.starter.web_starter",
            "security": "arkhe.ignite.starter.security_starter",
            "data": "arkhe.ignite.starter.data_starter",
            "cache": "arkhe.ignite.starter.cache_starter",
        }
        for name in self._starters:
            module_path = starter_map.get(name)
            if module_path:
                import importlib
                mod = importlib.import_module(module_path)
                mod.configure(self._context)

    async def _initialize_beans(self):
        for cls in list(self._context.container.registry.all_definitions()):
            instance = self._context.get_bean(cls)
            await run_post_construct(instance)

    def _wire_event_listeners(self):
        for cls in self._context.container.registry.all_definitions():
            instance = self._context.get_bean(cls)
            for name in dir(instance):
                method = getattr(instance, name, None)
                if callable(method) and getattr(method, "__arkhe_event_listener__", False):
                    event_type = method.__arkhe_event_type__
                    self._context.event_bus.subscribe(event_type, method)

    async def _start_scheduler(self):
        registry = TaskRegistry()
        for cls in self._context.container.registry.all_definitions():
            instance = self._context.get_bean(cls)
            for name in dir(instance):
                method = getattr(instance, name, None)
                if callable(method) and getattr(method, "__arkhe_scheduled__", False):
                    task = ScheduledTask(method, method.__arkhe_cron__)
                    registry.register(task)

        if registry.all():
            self._scheduler = SchedulerExecutor(registry)
            await self._scheduler.start()

    async def stop(self):
        if self._scheduler:
            await self._scheduler.stop()
        for cls in self._context.container.registry.all_definitions():
            instance = self._context.get_bean(cls)
            await run_pre_destroy(instance)
        await self._context.event_bus.publish(ApplicationStoppingEvent())

    @property
    def context(self) -> ApplicationContext:
        return self._context
