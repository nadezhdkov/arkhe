import pytest
from arkhe.ignite.di.registry import BeanRegistry
from arkhe.ignite.di.provider import BeanProvider
from arkhe.ignite.di.scopes import Scope
from arkhe.ignite.core.exceptions import BeanNotFoundException, CircularDependencyException


class ServiceA:
    pass


class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a


class ServiceC:
    pass


def make_provider(*classes, scope=Scope.SINGLETON):
    registry = BeanRegistry()
    for cls in classes:
        registry.register(cls, scope=scope)
    return BeanProvider(registry)


def test_simple_singleton():
    provider = make_provider(ServiceA)
    instance1 = provider.get(ServiceA)
    instance2 = provider.get(ServiceA)
    assert instance1 is instance2


def test_prototype_creates_new():
    provider = make_provider(ServiceA, scope=Scope.PROTOTYPE)
    instance1 = provider.get(ServiceA)
    instance2 = provider.get(ServiceA)
    assert instance1 is not instance2


def test_dependency_injection():
    provider = make_provider(ServiceA, ServiceB)
    b = provider.get(ServiceB)
    assert isinstance(b.a, ServiceA)


def test_bean_not_found():
    provider = make_provider()
    with pytest.raises(BeanNotFoundException):
        provider.get(ServiceC)


def test_circular_dependency():
    class X:
        def __init__(self, y: "Y"): ...

    class Y:
        def __init__(self, x: X): ...

    provider = make_provider(X, Y)
    with pytest.raises(CircularDependencyException):
        provider.get(X)
