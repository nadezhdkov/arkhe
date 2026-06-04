from typing import Type
from arkhe.ignite.decorators.component import _register


def Configuration(cls: Type = None):
    """
    Marks a class as a configuration source that may declare @Bean methods.

    Usage::

        @Configuration
        class AppConfig:
            @Bean
            def my_service(self) -> MyService:
                return MyService()
    """
    if cls is not None:
        return _register(cls, "configuration")

    def decorator(c: Type) -> Type:
        return _register(c, "configuration")

    return decorator
