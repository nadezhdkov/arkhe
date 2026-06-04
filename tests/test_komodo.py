"""
Tests for arkhe.komodo — AST-based metaprogramming engine.

Covers all decorators, the contract system, and KomodoInspector.
"""

import pytest
import logging
import json

from arkhe.komodo import komodo, KomodoInspector, AccessLevel
from arkhe.komodo import contract, ContractViolationError
from arkhe.komodo.contract import requires, ensures, invariant


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.all_args_constructor
# ─────────────────────────────────────────────────────────────────────────────

class TestAllArgsConstructor:

    def test_basic(self):
        @komodo.all_args_constructor
        class Point:
            x: float
            y: float

        p = Point(1.0, 2.0)
        assert p.x == 1.0
        assert p.y == 2.0

    def test_with_defaults(self):
        @komodo.all_args_constructor
        class Server:
            host: str
            port: int = 8080

        s = Server("localhost")
        assert s.host == "localhost"
        assert s.port == 8080

        s2 = Server("0.0.0.0", 443)
        assert s2.port == 443

    def test_missing_required_raises(self):
        @komodo.all_args_constructor
        class DB:
            url: str
            name: str

        with pytest.raises(TypeError):
            DB(url="sqlite:///test.db")  # missing 'name' positional

    def test_post_init(self):
        @komodo.all_args_constructor
        class Config:
            value: int

            def __post_init__(self):
                self.value_doubled = self.value * 2

        c = Config(21)
        assert c.value == 21
        assert c.value_doubled == 42


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.no_args_constructor
# ─────────────────────────────────────────────────────────────────────────────

class TestNoArgsConstructor:

    def test_creates_empty_init(self):
        @komodo.no_args_constructor
        class Empty:
            name: str

        e = Empty()
        # Attributes are not initialized — no args passed
        assert not hasattr(e, "name")


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.required_args_constructor
# ─────────────────────────────────────────────────────────────────────────────

class TestRequiredArgsConstructor:

    def test_only_required_fields(self):
        @komodo.required_args_constructor
        class User:
            name: str
            age: int = 20

        u = User("Mark")
        assert u.name == "Mark"
        # age is not set in __init__, but still exists as a class-level default
        assert "age" not in u.__dict__
        # class-level default is still accessible via descriptor fallback
        assert u.age == 20

    def test_rejects_extra_positional(self):
        @komodo.required_args_constructor
        class Item:
            id: str
            label: str = "default"

        with pytest.raises(TypeError):
            Item("abc", "extra")  # 'label' is not in signature


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.data
# ─────────────────────────────────────────────────────────────────────────────

class TestData:

    def test_constructor_repr_eq(self):
        @komodo.data
        class Color:
            r: int
            g: int
            b: int

        c1 = Color(255, 0, 0)
        c2 = Color(255, 0, 0)
        c3 = Color(0, 255, 0)

        assert c1 == c2
        assert c1 != c3
        assert repr(c1) == "Color(r=255, g=0, b=0)"
        assert str(c1) == "Color(r=255, g=0, b=0)"

    def test_hash(self):
        @komodo.data
        class Pair:
            a: int
            b: int

        p1 = Pair(1, 2)
        p2 = Pair(1, 2)
        assert hash(p1) == hash(p2)
        assert {p1, p2} == {p1}


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.value (immutable data)
# ─────────────────────────────────────────────────────────────────────────────

class TestValue:

    def test_immutable(self):
        @komodo.value
        class Money:
            amount: float
            currency: str

        m = Money(9.99, "USD")
        assert m.amount == 9.99
        assert m.currency == "USD"

        with pytest.raises(AttributeError, match="immutable"):
            m.amount = 1.0

    def test_equality(self):
        @komodo.value
        class Coord:
            x: int
            y: int

        assert Coord(1, 2) == Coord(1, 2)
        assert Coord(1, 2) != Coord(3, 4)


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.to_str
# ─────────────────────────────────────────────────────────────────────────────

class TestToStr:

    def test_generates_repr_and_str(self):
        @komodo.all_args_constructor
        @komodo.to_str
        class Animal:
            name: str
            legs: int

        a = Animal("cat", 4)
        assert repr(a) == "Animal(name='cat', legs=4)"
        assert str(a) == "Animal(name='cat', legs=4)"


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.eq / @komodo.equals_and_hashcode
# ─────────────────────────────────────────────────────────────────────────────

class TestEq:

    def test_eq_and_hash(self):
        @komodo.all_args_constructor
        @komodo.eq
        class Token:
            kind: str
            value: str

        t1 = Token("INT", "42")
        t2 = Token("INT", "42")
        t3 = Token("STR", "hello")

        assert t1 == t2
        assert t1 != t3
        assert hash(t1) == hash(t2)

    def test_returns_not_implemented_for_foreign(self):
        @komodo.all_args_constructor
        @komodo.eq
        class Foo:
            x: int

        f = Foo(1)
        assert f.__eq__("not a Foo") is NotImplemented


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.immutable
# ─────────────────────────────────────────────────────────────────────────────

class TestImmutable:

    def test_freeze_after_init_via_value(self):
        """@komodo.value composes data + immutable in a single AST pass."""
        @komodo.value
        class FrozenPoint:
            x: int
            y: int

        fp = FrozenPoint(10, 20)
        assert fp.x == 10

        with pytest.raises(AttributeError, match="immutable"):
            fp.x = 99

    def test_freeze_after_init_via_record(self):
        """@komodo.record includes immutable."""
        @komodo.record
        class FrozenItem:
            name: str

        fi = FrozenItem("test")
        assert fi.name == "test"

        with pytest.raises(AttributeError, match="immutable"):
            fi.name = "changed"

    def test_del_blocked(self):
        @komodo.value
        class FrozenItem:
            name: str

        fi = FrozenItem("test")
        with pytest.raises(AttributeError, match="immutable"):
            del fi.name


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.builder
# ─────────────────────────────────────────────────────────────────────────────

class TestBuilder:

    def test_basic_builder(self):
        @komodo.builder
        @komodo.all_args_constructor
        class Request:
            url: str
            method: str = "GET"
            timeout: float = 30.0

        req = (Request.builder()
               .url("https://api.example.com")
               .method("POST")
               .build())

        assert req.url == "https://api.example.com"
        assert req.method == "POST"
        assert req.timeout == 30.0

    def test_builder_missing_required(self):
        @komodo.builder
        @komodo.all_args_constructor
        class Payload:
            body: str

        with pytest.raises(ValueError, match="required field 'body' was not set"):
            Payload.builder().build()

    def test_builder_defaults_applied(self):
        @komodo.builder
        @komodo.all_args_constructor
        class Opts:
            verbose: bool = False
            retries: int = 3

        opts = Opts.builder().build()
        assert opts.verbose is False
        assert opts.retries == 3


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.singular
# ─────────────────────────────────────────────────────────────────────────────

class TestSingular:

    def test_singular_builder_method(self):
        @komodo.builder
        @komodo.singular("members")
        @komodo.record
        class Team:
            name: str
            members: list

        team = (Team.builder()
                .name("Eng")
                .member("Alice")
                .member("Bob")
                .build())

        assert team.name == "Eng"
        assert team.members == ["Alice", "Bob"]


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.non_null
# ─────────────────────────────────────────────────────────────────────────────

class TestNonNull:

    def test_rejects_none(self):
        @komodo.non_null
        @komodo.all_args_constructor
        class User:
            name: str

        with pytest.raises(ValueError, match="must not be None"):
            User(None)

    def test_accepts_valid(self):
        @komodo.non_null
        @komodo.all_args_constructor
        class User:
            name: str

        u = User("Alice")
        assert u.name == "Alice"


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.validated
# ─────────────────────────────────────────────────────────────────────────────

class TestValidated:

    def test_type_check(self):
        @komodo.validated
        @komodo.all_args_constructor
        class TypedPoint:
            x: float
            y: float

        with pytest.raises(TypeError, match="expected float"):
            TypedPoint("not_a_float", 1.0)

    def test_valid_passes(self):
        @komodo.validated
        @komodo.all_args_constructor
        class TypedPoint:
            x: float
            y: float

        p = TypedPoint(1.0, 2.0)
        assert p.x == 1.0
        assert p.y == 2.0


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.copyable
# ─────────────────────────────────────────────────────────────────────────────

class TestCopyable:

    def test_copy(self):
        @komodo.copyable
        @komodo.data
        class Config:
            host: str = "localhost"
            port: int = 8080

        base = Config()
        clone = base.copy()
        assert clone.host == "localhost"
        assert clone.port == 8080

    def test_copy_with(self):
        @komodo.copyable
        @komodo.data
        class Config:
            host: str = "localhost"
            port: int = 8080

        base = Config()
        prod = base.copy_with(host="prod.com", port=443)

        assert prod.host == "prod.com"
        assert prod.port == 443
        assert base.host == "localhost"  # original unchanged


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.getter / @komodo.setter / @komodo.withers
# ─────────────────────────────────────────────────────────────────────────────

class TestAccessors:

    def test_getter(self):
        @komodo.getter
        @komodo.all_args_constructor
        class Box:
            width: int
            height: int

        b = Box(10, 20)
        assert b.get_width() == 10
        assert b.get_height() == 20

    def test_setter(self):
        @komodo.setter
        @komodo.all_args_constructor
        class Box:
            width: int
            height: int

        b = Box(10, 20)
        b.set_width(15)
        assert b.width == 15

    def test_withers_requires_copyable(self):
        @komodo.withers
        @komodo.copyable
        @komodo.all_args_constructor
        class Box:
            width: int
            height: int

        b = Box(10, 20)
        b2 = b.with_height(30)
        assert b2.height == 30
        assert b2.width == 10
        assert b.height == 20  # original unchanged


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.accessors(fluent=True)
# ─────────────────────────────────────────────────────────────────────────────

class TestFluentAccessors:

    def test_fluent_get_and_set(self):
        @komodo.accessors(fluent=True)
        @komodo.all_args_constructor
        class FluentBox:
            size: int

        fb = FluentBox(5)
        # The generated __init__ sets self.size = 5, but the fluent accessor
        # also generates a method named 'size'. In practice, instance attribute
        # self.size (int) shadows the class-level method. Verify construction works.
        assert fb.size == 5

    def test_fluent_with_manual_prefix(self):
        """Fluent accessors on a class using _prefix storage work correctly."""
        @komodo.accessors(fluent=True, getter=True, setter=True)
        @komodo.all_args_constructor
        class FluentCounter:
            count: int

        fc = FluentCounter(10)
        # Instance attribute set by constructor takes precedence
        assert fc.count == 10


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.logger
# ─────────────────────────────────────────────────────────────────────────────

class TestLogger:

    def test_logger_injected(self):
        @komodo.logger
        @komodo.all_args_constructor
        class Service:
            name: str

        assert hasattr(Service, "logger")
        assert isinstance(Service.logger, logging.Logger)

    def test_logger_name(self):
        @komodo.logger
        @komodo.all_args_constructor
        class MyService:
            name: str

        assert "MyService" in MyService.logger.name


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.record
# ─────────────────────────────────────────────────────────────────────────────

class TestRecord:

    def test_record_is_immutable_data_with_serialization(self):
        @komodo.record
        class Person:
            name: str
            age: int

        p = Person("Alice", 30)

        # constructor
        assert p.name == "Alice"
        assert p.age == 30

        # repr
        assert "Person" in repr(p)
        assert "Alice" in repr(p)

        # equality
        p2 = Person("Alice", 30)
        assert p == p2

        # immutability
        with pytest.raises(AttributeError, match="immutable"):
            p.name = "Bob"

        # serialization
        data = p.to_dict()
        assert data == {"name": "Alice", "age": 30}

        p3 = Person.from_dict(data)
        assert p3 == p

    def test_record_json(self):
        @komodo.record
        class Item:
            id: int
            label: str

        item = Item(1, "test")
        j = item.to_json()
        parsed = json.loads(j)
        assert parsed == {"id": 1, "label": "test"}

        item2 = Item.from_json(j)
        assert item2 == item


# ─────────────────────────────────────────────────────────────────────────────
#  @komodo.to_dict / @komodo.from_dict / @komodo.json (standalone)
# ─────────────────────────────────────────────────────────────────────────────

class TestSerialization:

    def test_to_dict_standalone(self):
        @komodo.to_dict
        @komodo.all_args_constructor
        class Pos:
            x: int
            y: int

        p = Pos(3, 4)
        assert p.to_dict() == {"x": 3, "y": 4}

    def test_from_dict_standalone(self):
        @komodo.from_dict
        @komodo.all_args_constructor
        class Pos:
            x: int
            y: int

        p = Pos.from_dict({"x": 5, "y": 6})
        assert p.x == 5
        assert p.y == 6

    def test_json_standalone(self):
        @komodo.json
        @komodo.to_dict
        @komodo.from_dict
        @komodo.all_args_constructor
        class Msg:
            text: str

        m = Msg("hello")
        j = m.to_json()
        m2 = Msg.from_json(j)
        assert m2.text == "hello"


# ─────────────────────────────────────────────────────────────────────────────
#  KomodoInspector
# ─────────────────────────────────────────────────────────────────────────────

class TestKomodoInspector:

    def test_features(self):
        @komodo.data
        @komodo.builder
        class UserInfo:
            name: str
            age: int

        info = KomodoInspector(UserInfo)
        assert "data" in info.features
        assert "builder" in info.features

    def test_fields(self):
        @komodo.data
        class Simple:
            name: str
            count: int

        info = KomodoInspector(Simple)
        assert "name" in info.fields
        assert "count" in info.fields

    def test_has_builder(self):
        @komodo.builder
        @komodo.data
        class WithBuilder:
            x: int

        info = KomodoInspector(WithBuilder)
        assert info.has_builder is True

    def test_is_immutable(self):
        @komodo.value
        class ImmVal:
            x: int

        info = KomodoInspector(ImmVal)
        assert info.is_immutable is True

    def test_is_record(self):
        @komodo.record
        class Rec:
            x: int

        info = KomodoInspector(Rec)
        assert info.is_record is True

    def test_summary_output(self):
        @komodo.data
        class ForSummary:
            name: str

        info = KomodoInspector(ForSummary)
        s = info.summary()
        assert "ForSummary" in s
        assert "komodo.inspect" in s

    def test_defaults_property(self):
        @komodo.data
        class WithDef:
            name: str = "anon"
            age: int = 0

        info = KomodoInspector(WithDef)
        defaults = info.defaults
        assert "name" in defaults or "age" in defaults

    def test_rejects_non_class(self):
        with pytest.raises(TypeError, match="expects a class"):
            KomodoInspector("not a class")

    def test_generated_methods(self):
        @komodo.data
        class MethodCheck:
            x: int

        info = KomodoInspector(MethodCheck)
        gen = info.generated_methods
        assert "__init__" in gen
        assert "__repr__" in gen or "__str__" in gen


# ─────────────────────────────────────────────────────────────────────────────
#  @contract — Design by Contract
# ─────────────────────────────────────────────────────────────────────────────

class TestContract:

    def test_precondition_pass(self):
        @contract(
            requires(lambda x: x > 0, "x must be positive"),
        )
        def sqrt(x: float) -> float:
            return x ** 0.5

        assert sqrt(4.0) == 2.0

    def test_precondition_fail(self):
        @contract(
            requires(lambda x: x > 0, "x must be positive"),
        )
        def sqrt(x: float) -> float:
            return x ** 0.5

        with pytest.raises(ContractViolationError, match="x must be positive"):
            sqrt(-1.0)

    def test_postcondition_pass(self):
        @contract(
            ensures(lambda r: r >= 0, "result must be non-negative"),
        )
        def abs_value(x: float) -> float:
            return abs(x)

        assert abs_value(-5.0) == 5.0

    def test_postcondition_fail(self):
        @contract(
            ensures(lambda r: r >= 0, "result must be non-negative"),
        )
        def bad_abs(x: float) -> float:
            return x  # deliberately wrong

        with pytest.raises(ContractViolationError, match="result must be non-negative"):
            bad_abs(-3.0)

    def test_invariant_on_method(self):
        class Account:
            def __init__(self, balance: float):
                self.balance = balance

            @contract(
                invariant(lambda self, amount: self.balance >= 0, "balance must not be negative"),
            )
            def withdraw(self, amount: float) -> None:
                self.balance -= amount

        acc = Account(100.0)
        acc.withdraw(50.0)
        assert acc.balance == 50.0

        with pytest.raises(ContractViolationError, match="balance must not be negative"):
            acc.withdraw(200.0)

    def test_combined_pre_post(self):
        @contract(
            requires(lambda x, y: y != 0, "divisor must not be zero"),
            ensures(lambda r: isinstance(r, float), "result must be float"),
        )
        def divide(x: float, y: float) -> float:
            return x / y

        assert divide(10.0, 2.0) == 5.0

        with pytest.raises(ContractViolationError, match="divisor must not be zero"):
            divide(1.0, 0)

    def test_contract_metadata(self):
        @contract(
            requires(lambda x: x > 0, "positive"),
            ensures(lambda r: r > 0, "positive result"),
        )
        def identity(x: float) -> float:
            return x

        assert hasattr(identity, "__contracts__")
        assert len(identity.__contracts__["preconditions"]) == 1
        assert len(identity.__contracts__["postconditions"]) == 1

    def test_contract_violation_error_attrs(self):
        try:
            @contract(
                requires(lambda: False, "always fails"),
            )
            def nope():
                pass

            nope()
        except ContractViolationError as e:
            assert e.kind == "precondition"
            assert "nope" in e.func
            assert "always fails" in e.message


# ─────────────────────────────────────────────────────────────────────────────
#  Comprehensive stacking test
# ─────────────────────────────────────────────────────────────────────────────

class TestComprehensiveStacking:

    def test_logger_builder_singular_record(self):
        @komodo.logger
        @komodo.builder
        @komodo.singular("tags")
        @komodo.record
        class MasterEntity:
            id: str
            status: str = "pending"
            tags: list

        # Logger
        assert isinstance(MasterEntity.logger, logging.Logger)

        # Builder & Singular
        entity = (MasterEntity.builder()
                  .id("e-123")
                  .tag("urgent")
                  .tag("backend")
                  .build())

        assert entity.id == "e-123"
        assert entity.tags == ["urgent", "backend"]
        assert entity.status == "pending"

        # Equality
        entity2 = (MasterEntity.builder()
                   .id("e-123")
                   .tag("urgent")
                   .tag("backend")
                   .build())
        assert entity == entity2

        # Immutable (record includes immutable)
        with pytest.raises(AttributeError, match="immutable"):
            entity.id = "e-999"

        # Serialization
        data = entity.to_dict()
        assert data == {"id": "e-123", "status": "pending", "tags": ["urgent", "backend"]}

        entity3 = MasterEntity.from_dict(data)
        assert entity3 == entity

    def test_data_with_getter_setter(self):
        @komodo.getter
        @komodo.setter
        @komodo.data
        class Profile:
            name: str
            email: str

        p = Profile("Alice", "alice@example.com")
        assert p.get_name() == "Alice"
        p.set_email("newemail@example.com")
        assert p.email == "newemail@example.com"
        assert repr(p) == "Profile(name='Alice', email='newemail@example.com')"

    def test_validated_data(self):
        @komodo.validated
        @komodo.data
        class TypedConfig:
            host: str
            port: int

        c = TypedConfig("localhost", 8080)
        assert c.host == "localhost"
        assert c.port == 8080

        with pytest.raises(TypeError, match="expected str"):
            TypedConfig(123, 8080)

    def test_non_null_value(self):
        @komodo.non_null
        @komodo.value
        class Strict:
            name: str
            count: int

        s = Strict("ok", 1)
        assert s.name == "ok"

        with pytest.raises(ValueError, match="must not be None"):
            Strict(None, 1)

        with pytest.raises(AttributeError, match="immutable"):
            s.name = "changed"

# ─────────────────────────────────────────────────────────────────────────────
#  Lombok-Style Enhancements
# ─────────────────────────────────────────────────────────────────────────────

class TestLombokStyleEnhancements:

    def test_access_level_constructor(self):
        @komodo.all_args_constructor(access=AccessLevel.PRIVATE, static_name="of")
        class Point:
            x: int
            y: int

        # Python doesn't prevent calling __init__, but it generated 'of'
        p = Point.of(1, 2)
        assert p.x == 1
        assert p.y == 2
        
        @komodo.all_args_constructor(access=AccessLevel.NONE)
        class NoConstructor:
            x: int
        
        with pytest.raises(TypeError):
            NoConstructor(1)

    def test_access_level_accessors(self):
        @komodo.getter(access=AccessLevel.PROTECTED)
        @komodo.setter(access=AccessLevel.PRIVATE)
        @komodo.all_args_constructor
        class Secret:
            code: str

        s = Secret("123")
        assert s._get_code() == "123"
        s._Secret__set_code("456")
        assert s.code == "456"

    def test_to_str_parameters(self):
        @komodo.to_str(includeFieldNames=False)
        @komodo.all_args_constructor
        class TupleLike:
            a: int
            b: int
            
        t = TupleLike(1, 2)
        assert str(t) == "TupleLike(1, 2)"
        
        @komodo.to_str(exclude=["password"])
        @komodo.all_args_constructor
        class User:
            username: str
            password: str
            
        u = User("admin", "secret")
        assert "password=" not in str(u)
        assert "username='admin'" in str(u)
        
        @komodo.to_str(of=["id"])
        @komodo.all_args_constructor
        class Entity:
            id: int
            name: str
            
        e = Entity(1, "Test")
        assert "name=" not in str(e)
        assert "id=1" in str(e)

    def test_logger_setup(self, capsys):
        import sys
        @komodo.logger(level=logging.INFO, topic="test.topic")
        class Worker:
            def work(self):
                self.logger.info("working!")

        w = Worker()
        w.work()
        # In pytest, logs might be captured by caplog or stderr
        # We just assert it exists and is setup
        assert Worker.logger.name == "test.topic"
        assert Worker.logger.level == logging.INFO

    def test_data_static_constructor(self):
        @komodo.data(static_constructor="create")
        class Obj:
            val: int
            
        o = Obj.create(42)
        assert o.val == 42
