import inspect


def EventListener(event_type):
    """
    Marks a method as a listener for a specific event type.

    Usage::

        @EventListener(ApplicationReadyEvent)
        async def on_ready(self, event: ApplicationReadyEvent):
            print("App is ready!")
    """
    def decorator(fn):
        fn.__arkhe_event_listener__ = True
        fn.__arkhe_event_type__ = event_type
        return fn

    return decorator
