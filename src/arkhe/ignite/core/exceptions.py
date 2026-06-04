class ArkheException(Exception):
    """Base exception for arkhe.ignite framework."""
    pass


class BeanNotFoundException(ArkheException):
    """Raised when a requested bean is not found in the container."""
    def __init__(self, bean_type):
        super().__init__(
            f"Bean of type '{bean_type}' not found in the application context."
        )


class CircularDependencyException(ArkheException):
    """Raised when a circular dependency is detected."""
    def __init__(self, chain: list):
        path = " -> ".join(str(c) for c in chain)
        super().__init__(f"Circular dependency detected: {path}")


class ConfigurationException(ArkheException):
    """Raised when configuration loading or resolution fails."""
    pass


class BeanInitializationException(ArkheException):
    """Raised when a bean fails to initialize."""
    def __init__(self, bean_type, cause: Exception):
        super().__init__(f"Failed to initialize bean '{bean_type}': {cause}")
        self.__cause__ = cause


class ProfileNotFoundException(ArkheException):
    """Raised when the specified profile config file is not found."""
    def __init__(self, profile: str):
        super().__init__(
            f"Profile configuration not found: application-{profile}.yml"
        )


class ValueInjectionException(ArkheException):
    """Raised when a @Value injection key is missing."""
    def __init__(self, key: str):
        super().__init__(
            f"Configuration key '{key}' not found. Check your application.yml."
        )
