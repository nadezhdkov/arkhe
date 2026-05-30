"""
nestifypy.ignite.starter.web_starter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Auto-configuration for the web layer.
Activated when ``starters=["web"]`` is passed to ``Application.run()``.

Registers:
- WebServer bean (scans @Controller beans and mounts routes)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nestifypy.ignite.core.context import ApplicationContext


def configure(context: "ApplicationContext"):
    from nestifypy.ignite.web.server import WebServer
    from nestifypy.ignite.di.scopes import Scope

    # Register WebServer as a singleton bean, injecting the context
    instance = WebServer(context)
    instance.build()
    context.container.register_instance(WebServer, instance)
