"""
arkhe.ignite
================
A Spring Boot-inspired application framework for Python.
Part of the arkhe library ecosystem.

Quick start::

    from arkhe.ignite import Application
    from arkhe.ignite.decorators import Controller, Get

    @Controller("/hello")
    class HelloController:

        @Get("/")
        async def hello(self):
            return {"message": "Hello, World!"}

    app = Application.run()
"""

from arkhe.ignite.core.application import Application
from arkhe.ignite.core.context import ApplicationContext

__version__ = "0.1.0"
__author__ = "Arkhe Contributors"

__all__ = ["Application", "ApplicationContext"]
