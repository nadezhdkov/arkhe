def Value(key: str, default=None):
    """
    Injects a configuration value from application.yml into a field.

    Usage::

        class MyService:
            db_url: str = Value("database.url")
    """
    # Returns a descriptor-like marker; actual injection is done by the container.
    class _ValueDescriptor:
        def __init__(self):
            self.__arkhe_value_key__ = key
            self.__arkhe_value_default__ = default

        def __set_name__(self, owner, name):
            self._name = f"_value_{name}"

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            val = getattr(obj, self._name, None)
            if val is None:
                from arkhe.ignite.core.boot import get_context
                ctx = get_context()
                if ctx:
                    val = ctx.get_property(key, default)
                    setattr(obj, self._name, val)
            return val

    return _ValueDescriptor()
