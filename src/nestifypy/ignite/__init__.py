"""
nestifypy.ignite
================
A Spring Boot-inspired application framework for Python.
Part of the nestifypy library ecosystem.

Quick start::

    from nestifypy.ignite import Application
    from nestifypy.ignite.decorators import Controller, Get

    @Controller("/hello")
    class HelloController:

        @Get("/")
        async def hello(self):
            return {"message": "Hello, World!"}

    app = Application.run()
"""

from nestifypy.ignite.core.application import Application
from nestifypy.ignite.core.context import ApplicationContext

__version__ = "0.1.0"
__author__ = "Nestifypy Contributors"

__all__ = ["Application", "ApplicationContext"]
