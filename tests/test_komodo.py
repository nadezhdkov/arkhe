import pytest
from nestifypy.komodo import komodo, KomodoInspector

def test_komodo_constructor():
    @komodo.constructor
    class Point:
        x: float
        y: float

    p = Point(1.0, 2.0)
    assert p.x == 1.0
    assert p.y == 2.0

def test_komodo_constructor_defaults():
    @komodo.constructor
    class Server:
        host: str
        port: int = 8080

    s = Server("localhost")
    assert s.host == "localhost"
    assert s.port == 8080

    s2 = Server("0.0.0.0", 443)
    assert s2.port == 443

def test_komodo_constructor_missing_required():
    @komodo.constructor
    class DB:
        url: str
        name: str

    with pytest.raises(TypeError):
        DB(url="sqlite:///test.db")

def test_komodo_post_init():
    @komodo.constructor
    class Config:
        value: int

        def __post_init__(self):
            self.value_doubled = self.value * 2

    c = Config(21)
    assert c.value_doubled == 42

def test_komodo_data():
    @komodo.data
    class Color:
        r: int
        g: int
        b: int

    c1 = Color(255, 0, 0)
    c2 = Color(255, 0, 0)
    assert c1 == c2
    assert repr(c1) == "Color(r=255, g=0, b=0)"

def test_komodo_value_immutable():
    @komodo.value
    class Money:
        amount: float
        currency: str

    m = Money(9.99, "USD")
    with pytest.raises(AttributeError, match="is immutable"):
        m.amount = 1.0

def test_komodo_builder():
    @komodo.builder
    @komodo.constructor
    class Request:
        url: str
        method: str = "GET"
        timeout: float = 30.0

    req = Request.builder().with_url("https://api.example.com").with_method("POST").build()
    assert req.url == "https://api.example.com"
    assert req.method == "POST"
    assert req.timeout == 30.0

def test_komodo_builder_missing_required():
    @komodo.builder
    @komodo.constructor
    class Payload:
        body: str

    with pytest.raises(ValueError, match="required field 'body' was not set"):
        Payload.builder().build()

def test_komodo_singular():
    @komodo.builder
    @komodo.singular("members")
    @komodo.record
    class Team:
        name: str
        members: list[str]

    team = Team.builder().with_name("Eng").member("Alice").member("Bob").build()
    assert team.name == "Eng"
    assert team.members == ["Alice", "Bob"]

def test_komodo_non_null():
    @komodo.non_null
    @komodo.constructor
    class User:
        name: str

    with pytest.raises(ValueError, match="must not be None"):
        User(None)

    u = User("Alice")
    assert u.name == "Alice"

def test_komodo_copyable():
    @komodo.copyable
    @komodo.data
    class Config:
        host: str = "localhost"
        port: int = 8080

    base = Config()
    prod = base.copy_with(host="prod.com", port=443)
    
    assert prod.host == "prod.com"
    assert prod.port == 443
    assert base.host == "localhost"

def test_komodo_validated():
    @komodo.validated
    @komodo.constructor
    class TypedPoint:
        x: float
        y: float

    with pytest.raises(TypeError, match="expected float"):
        TypedPoint("not_a_float", 1.0)

    p = TypedPoint(1.0, 2.0)
    assert p.x == 1.0

def test_komodo_record_serialization():
    @komodo.record
    class Person:
        name: str
        age: int

    p = Person("Alice", 30)
    data = p.to_dict()
    assert data == {"name": "Alice", "age": 30}
    
    p2 = Person.from_dict(data)
    assert p == p2

def test_komodo_inspector():
    @komodo.data
    @komodo.builder
    class UserInfo:
        name: str
        age: int

    info = KomodoInspector(UserInfo)
    assert "data" in info.features
    assert "builder" in info.features
    assert "name" in info.fields
    
    s = info.summary()
    assert "UserInfo" in s
    assert "Has Builder" in s

def test_komodo_accessors():
    @komodo.copyable
    @komodo.getter
    @komodo.setter
    @komodo.withers
    @komodo.constructor
    class Box:
        width: int
        height: int

    b = Box(10, 20)
    assert b.width == 10
    
    # Setter test
    b.width = 15
    assert b.width == 15
    
    # Wither test
    b2 = b.with_height(30)
    assert b2.width == 15
    assert b2.height == 30
    assert b.height == 20

def test_komodo_fluent_accessors():
    @komodo.accessors(fluent=True)
    class FluentBox:
        size: int
        
        def __init__(self, size: int):
            self._size = size
            
    fb = FluentBox(5)
    # Getter behavior
    assert fb.size() == 5
    
    # Setter fluent behavior
    assert fb.size(10) is fb
    assert fb.size() == 10

def test_komodo_comprehensive():
    """
    Test a class with a combination of many decorators to ensure they compose well.
    """
    import logging
    
    @komodo.logger
    @komodo.builder
    @komodo.singular("tags")
    @komodo.record
    class MasterEntity:
        id: str
        status: str = "pending"
        tags: list[str]

    # Test Logger
    assert isinstance(MasterEntity.logger, logging.Logger)
    
    # Test Builder & Singular
    entity = (MasterEntity.builder()
              .with_id("e-123")
              .tag("urgent")
              .tag("backend")
              .build())
              
    # Test Data
    assert entity.id == "e-123"
    assert entity.tags == ["urgent", "backend"]
    assert entity.status == "pending"
    
    # Test Equality
    entity2 = MasterEntity.builder().with_id("e-123").tag("urgent").tag("backend").build()
    assert entity == entity2
    
    # Test Immutable Properties (since it's a record, it has @komodo.immutable)
    with pytest.raises(AttributeError, match="is immutable"):
        entity.id = "e-999"
        
    # Test Serialization
    data = entity.to_dict()
    assert data == {"id": "e-123", "status": "pending", "tags": ["urgent", "backend"]}
    
    # Test deserialization
    entity3 = MasterEntity.from_dict(data)
    assert entity3 == entity
