"""
Tests for arkhe.oop

Run with:  python -m pytest tests/test_oop.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from arkhe.oop import (
    interface,
    implements,
    abstract_class,
    abstract_method,
    override,
    final,
    InterfaceImplementationError,
    AbstractMethodError,
    InstantiationError,
    OverrideError,
    FinalClassError,
)


# ===========================================================================
# @interface + @implements
# ===========================================================================

class TestInterface:

    def test_valid_implementation(self):
        @interface
        class ILogger:
            def log(self, message: str) -> None:
                pass

        @implements(ILogger)
        class ConsoleLogger:
            def log(self, message: str) -> None:
                print(message)

        obj = ConsoleLogger()
        assert callable(obj.log)

    def test_missing_method_raises(self):
        @interface
        class IRunner:
            def run(self) -> None:
                pass

        with pytest.raises(InterfaceImplementationError) as exc:
            @implements(IRunner)
            class BadRunner:
                pass

        assert "run" in str(exc.value)
        assert "BadRunner" in str(exc.value)

    def test_multiple_interfaces(self):
        @interface
        class Serializable:
            def serialize(self) -> str:
                pass

        @interface
        class Validatable:
            def validate(self) -> bool:
                pass

        @implements(Serializable, Validatable)
        class User:
            def serialize(self) -> str:
                return "{}"
            def validate(self) -> bool:
                return True

        u = User()
        assert u.serialize() == "{}"
        assert u.validate() is True

    def test_multiple_interfaces_partial_raises(self):
        @interface
        class IA:
            def a(self): pass

        @interface
        class IB:
            def b(self): pass

        with pytest.raises(InterfaceImplementationError) as exc:
            @implements(IA, IB)
            class Partial:
                def a(self): pass
            # 'b' is missing

        assert "b" in str(exc.value)

    def test_interface_inheritance(self):
        @interface
        class Entity:
            def get_id(self) -> int:
                pass

        @interface
        class IUser(Entity):
            def get_name(self) -> str:
                pass

        @implements(IUser)
        class User:
            def get_id(self) -> int:
                return 1
            def get_name(self) -> str:
                return "Alice"

        u = User()
        assert u.get_id() == 1

    def test_interface_inheritance_missing_parent_method(self):
        @interface
        class IBase:
            def base_method(self): pass

        @interface
        class IChild(IBase):
            def child_method(self): pass

        with pytest.raises(InterfaceImplementationError) as exc:
            @implements(IChild)
            class Impl:
                def child_method(self): pass
                # base_method missing

        assert "base_method" in str(exc.value)

    def test_interface_attributes(self):
        @interface
        class IUser:
            id: int
            username: str

        @implements(IUser)
        class User:
            id: int
            username: str

    def test_interface_attributes_missing_raises(self):
        @interface
        class IRecord:
            record_id: int

        with pytest.raises(InterfaceImplementationError) as exc:
            @implements(IRecord)
            class Record:
                pass

        assert "record_id" in str(exc.value)

    def test_implements_non_interface_raises(self):
        class NotAnInterface:
            pass

        with pytest.raises(TypeError):
            @implements(NotAnInterface)
            class Impl:
                pass


# ===========================================================================
# @abstract_class + @abstract_method
# ===========================================================================

class TestAbstractClass:

    def test_valid_subclass(self):
        @abstract_class
        class Base:
            @abstract_method
            def execute(self):
                pass

        class Concrete(Base):
            def execute(self):
                return "done"

        obj = Concrete()
        assert obj.execute() == "done"

    def test_missing_implementation_raises(self):
        @abstract_class
        class Base:
            @abstract_method
            def run(self):
                pass

        with pytest.raises(AbstractMethodError) as exc:
            class Bad(Base):
                pass

        assert "run" in str(exc.value)
        assert "Bad" in str(exc.value)

    def test_cannot_instantiate_abstract_class(self):
        @abstract_class
        class Repo:
            @abstract_method
            def save(self, data):
                pass

        with pytest.raises(InstantiationError) as exc:
            Repo()

        assert "Repo" in str(exc.value)

    def test_concrete_methods_available(self):
        @abstract_class
        class Service:
            def startup(self):
                return "started"

            @abstract_method
            def execute(self):
                pass

        class MyService(Service):
            def execute(self):
                return "running"

        obj = MyService()
        assert obj.startup() == "started"
        assert obj.execute() == "running"

    def test_abstract_method_raises_if_called_directly(self):
        @abstract_class
        class Base:
            @abstract_method
            def do_thing(self):
                pass

        class Concrete(Base):
            def do_thing(self):
                # Intentionally call super to trigger the abstract stub
                return "ok"

        # The abstract stub should raise NotImplementedError if reached
        stub = Base.__dict__["do_thing"]
        with pytest.raises(NotImplementedError):
            stub(None)

    def test_nested_abstract_inheritance(self):
        @abstract_class
        class Level1:
            @abstract_method
            def method_a(self):
                pass

        @abstract_class
        class Level2(Level1):
            @abstract_method
            def method_b(self):
                pass

        class Concrete(Level2):
            def method_a(self):
                return "a"
            def method_b(self):
                return "b"

        obj = Concrete()
        assert obj.method_a() == "a"
        assert obj.method_b() == "b"


# ===========================================================================
# @override
# ===========================================================================

class TestOverride:

    def test_valid_override(self):
        @abstract_class
        class Base:
            @abstract_method
            def save(self, data):
                pass

        class Concrete(Base):
            @override
            def save(self, data):
                return data

        obj = Concrete()
        assert obj.save("x") == "x"

    def test_override_no_parent_raises(self):
        @abstract_class
        class Base:
            @abstract_method
            def save(self, data):
                pass

        with pytest.raises(OverrideError) as exc:
            class Concrete(Base):
                @override
                def save(self, data):
                    return data

                @override
                def delete(self):   # does NOT exist on Base
                    pass

        assert "delete" in str(exc.value)


# ===========================================================================
# @final
# ===========================================================================

class TestFinal:

    def test_final_class_cannot_be_subclassed(self):
        @final
        class Config:
            pass

        with pytest.raises(FinalClassError) as exc:
            class ExtendedConfig(Config):
                pass

        assert "Config" in str(exc.value)

    def test_final_class_can_be_instantiated(self):
        @final
        class Singleton:
            def value(self):
                return 42

        obj = Singleton()
        assert obj.value() == 42


# ===========================================================================
# Combined usage
# ===========================================================================

class TestCombined:

    def test_interface_and_abstract_class_together(self):
        @interface
        class ILogger:
            def log(self, message: str) -> None:
                pass

        @abstract_class
        class BaseService:
            def startup(self):
                return "started"

            @abstract_method
            def execute(self):
                pass

        @implements(ILogger)
        class ConsoleLogger:
            def log(self, message: str) -> None:
                pass

        class UserService(BaseService):
            @override
            def execute(self):
                return "executing"

        svc = UserService()
        assert svc.startup() == "started"
        assert svc.execute() == "executing"
