import asyncio
import functools


def AsyncTask(fn):
    """
    Runs the decorated method as a background asyncio task (fire-and-forget).

    Usage::

        @AsyncTask
        async def send_email(self, to: str):
            ...
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.create_task(fn(*args, **kwargs))

    wrapper.__nestifypy_async_task__ = True
    return wrapper
