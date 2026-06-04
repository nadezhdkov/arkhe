from arkhe.ignite.di.provider import BeanProvider


class Injector:
    """
    Handles field-level injection for beans that use @Inject.
    Works alongside BeanProvider for constructor injection.
    """

    def __init__(self, provider: BeanProvider):
        self._provider = provider

    def inject_fields(self, instance) -> None:
        """Inject any @Inject-annotated fields on the given instance."""
        for attr_name in dir(type(instance)):
            descriptor = getattr(type(instance), attr_name, None)
            if descriptor and getattr(descriptor, "__arkhe_inject__", False):
                target_type = descriptor.__arkhe_inject_type__
                value = self._provider.get(target_type)
                setattr(instance, attr_name, value)
