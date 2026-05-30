def Scheduled(cron: str):
    """
    Marks a method to be run on a cron schedule.

    Usage::

        @Scheduled("*/5 * * * *")
        async def cleanup(self):
            ...
    """
    def decorator(fn):
        fn.__nestifypy_scheduled__ = True
        fn.__nestifypy_cron__ = cron
        return fn

    return decorator
