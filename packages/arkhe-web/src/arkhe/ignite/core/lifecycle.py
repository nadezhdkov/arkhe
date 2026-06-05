import asyncio
import inspect
from typing import Any

_POST_CONSTRUCT_ATTR = "__arkhe_post_construct__"
_PRE_DESTROY_ATTR = "__arkhe_pre_destroy__"


def PostConstruct(fn):
    """
    Marks an async or sync method to be called after bean initialization.

    Usage::

        @PostConstruct
        async def init(self):
            ...
    """
    setattr(fn, _POST_CONSTRUCT_ATTR, True)
    return fn


def PreDestroy(fn):
    """
    Marks an async or sync method to be called before the application shuts down.

    Usage::

        @PreDestroy
        async def destroy(self):
            ...
    """
    setattr(fn, _PRE_DESTROY_ATTR, True)
    return fn


async def run_lifecycle_hooks(instance: Any, attr: str):
    """Find and invoke all methods on instance marked with the given lifecycle attr."""
    for name in dir(instance):
        try:
            method = getattr(instance, name)
        except AttributeError:
            continue
        if callable(method) and getattr(method, attr, False):
            if inspect.iscoroutinefunction(method):
                await method()
            else:
                method()


async def run_post_construct(instance: Any):
    await run_lifecycle_hooks(instance, _POST_CONSTRUCT_ATTR)


async def run_pre_destroy(instance: Any):
    await run_lifecycle_hooks(instance, _PRE_DESTROY_ATTR)
