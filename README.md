<div align="center">

# 🪺 Arkhe

> A modern, modular Python framework built for developers who believe in clean, expressive, zero-boilerplate code.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)](https://github.com/arkhe/arkhe/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/arkhe/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI](https://img.shields.io/pypi/v/arkhe?style=flat-square)](https://pypi.org/project/arkhe/)

Arkhe is a **modular, batteries-included Python framework** that brings together the ergonomics of Spring Boot, Lombok, and Kotlin into a cohesive ecosystem — covering everything from AST-based metaprogramming and enterprise dependency injection to functional error handling, fluent HTTP clients, and a declarative 2D game engine.

Every module is **independent and composable** — use exactly what you need.

[Installation](#-installation) · [Ecosystem](#-ecosystem) · [Quick Start](#-quick-start) · [Documentation](#-documentation) · [Contributing](#-contributing)

</div>

---

## 📦 Installation

Arkhe is distributed as a set of independent, modular **Namespace Packages**. Install exactly what you need.

**Core & Metaprogramming:**
```bash
pip install arkhe-core arkhe-meta
```

**Web, Net & Config:**
```bash
pip install arkhe-web arkhe-net arkhe-config
```

**Game Engine & Math:**
```bash
pip install arkhe-game arkhe-math
```

**Enterprise Utilities:**
```bash
pip install arkhe-db arkhe-scheduler arkhe-log arkhe-os
```

> Requires **Python 3.10 or higher**. Combine packages freely — they all seamlessly integrate into the `arkhe.*` namespace.

---

## 🌐 Ecosystem

> Each package is independent. Install only what you need — they all share the `arkhe.*` namespace.

| Package (`pip install`) | Modules | Description |
|---|---|---|
| **`arkhe-core`** | `types`, `utils`, `ensure`, `result`, `promise`, `trying` | Foundation types, functional error handling, utilities |
| **`arkhe-meta`** | [`komodo`](#-komodo--metaprogramming), [`oop`](#-oop--object-oriented-utilities), `decorators`, `patterns` | AST metaprogramming, interfaces, abstract classes |
| **`arkhe-config`** | [`yaml`](#-yaml--intelligent-config-registry), `json`, [`env`](#-env--environment-management) | Configuration management (YAML, JSON, dotenv) |
| **`arkhe-web`** | [`ignite`](#-ignite--enterprise-application-framework), [`loom`](#-loom--configuration-engine) | Enterprise DI framework, FastAPI integration, config engine |
| **`arkhe-net`** | [`net`](#-net--http-client) | Fluent HTTP client — zero external dependencies |
| **`arkhe-math`** | [`math`](#-math) | BigDecimal, Money, game-ready math primitives |
| **`arkhe-game`** | [`pyunix`](#-pyunix--2d-game-engine) | Declarative 2D game engine built on Pygame |
| **`arkhe-db`** | [`database`](#-database--sqlite-toolkit), [`collections`](#-collections) | SQLite toolkit, strongly-typed data structures |
| **`arkhe-scheduler`** | [`scheduler`](#-scheduler), [`flow`](#-flow--control-flow) | Cron-style task scheduler, throttling, debouncing |
| **`arkhe-log`** | [`slogger`](#-slogger--system-logger) | Professional logger with colours and formatters |
| **`arkhe-os`** | [`os`](#-os--file-utilities), [`console`](#-console--terminal-utilities), [`input`](#-input), `cli` | File utilities, terminal UI, interactive CLI inputs |

---

## 🚀 Quick Start

### Metaprogramming with Komodo

```python
from arkhe.komodo import komodo

@komodo.logger
@komodo.copyable
@komodo.builder
@komodo.data
class Product:
    id: int
    name: str
    price: float
    active: bool = True

# All generated via AST — native bytecode, zero runtime overhead
p  = Product(1, "Widget", 9.99)
p2 = p.copy_with(price=7.99)
Product.logger.info("Price updated")

req = (
    Product.builder()
        .with_id(1)
        .with_name("Widget")
        .with_price(9.99)
        .build()
)
```

### SQLite with Database

```python
from dataclasses import dataclass
from arkhe.database import DB, db_entity, db_column

DB.connect("app.db")

@db_entity("users")
@dataclass
class User:
    id:    int = db_column(primary_key=True)
    email: str = db_column(unique=True)
    name:  str = db_column()

DB.create_table(User)
DB.insert_into("users").values(name="Alice", email="alice@example.com").execute()

users: list[User] = DB.select("*").from_table("users").into(User)
```

### Smart Configuration

```python
from arkhe import yaml, env
from arkhe.env import Env

Env.load()

db_host  = yaml.database.host          # attribute access on any .yml file
db_port  = env.db.port.int             # → int(DB_PORT)
debug    = env.debug.bool              # → bool(DEBUG)
secret   = env.secret_key.required     # raises ConfigError if missing
```

### Enterprise App with Ignite

```python
from arkhe.ignite import Application
from arkhe.ignite.decorators import Service, Controller, PostConstruct
from arkhe.ignite.web.rest import Get, Post

@Service
class UserService:
    def get_users(self) -> list[str]:
        return ["Hope", "Alex"]

@Controller("/users")
class UserController:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    @Get("/")
    async def list_users(self):
        return self.user_service.get_users()

    @PostConstruct
    async def on_start(self):
        print("UserController ready!")

app = Application.run(web=True, starters=["web"])
```

### 2D Game with Pyunix

```python
from arkhe.pyunix import Game, Entity, Rigidbody, BoxCollider, BodyType
from arkhe.pyunix.math import Vector2, Color

@Game(title="My Game", size=(800, 600), fps=60)
class MyGame:

    @Game.start
    def start(self):
        self.player = Player(x=400, y=300)

    @Game.update
    def update(self, dt: float):
        pass

    @Game.draw
    def draw(self, screen):
        screen.fill(Color.BLACK.to_tuple())

    @Game.text(x=10, y=10, size=24, color="white")
    def score_ui(self):
        return "SCORE: 1000"

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            rigidbody=Rigidbody(body_type=BodyType.DYNAMIC, mass=1.0),
            collider=BoxCollider(width=32, height=32),
        )

    @Entity.update
    def movement(self, dt):
        if self.input.is_action_pressed("jump"):
            self.rigidbody.add_impulse(Vector2(0, -500))

if __name__ == "__main__":
    MyGame().run()
```

---

## 🔥 Ignite — Enterprise Application Framework

> A Spring Boot-inspired framework for production Python applications.

**Features:** IoC container, constructor injection, lifecycle hooks, EventBus, FastAPI integration, cron scheduling, JWT security, profile-aware configuration, and a `TestContainer` for mocking.

### Dependency Injection

```python
from arkhe.ignite.decorators import Service, Repository

@Repository
class UserRepository:
    def find(self, id: int) -> dict:
        return {"id": id, "name": "Alice"}

@Service
class UserService:
    def __init__(self, repo: UserRepository):  # injected automatically by type
        self.repo = repo

    def get_user(self, id: int):
        return self.repo.find(id)
```

### Configuration & Profiles

```yaml
# application.yml
server:
  port: 8080
database:
  url: "postgresql://localhost/myapp"
jwt:
  secret: "my-secret"
  expiry_minutes: 60
```

```python
from arkhe.ignite.decorators import Value

@Service
class AppConfig:
    @Value("server.port")
    port: int

    @Value("database.url")
    db_url: str
```

### EventBus

```python
from arkhe.ignite.decorators import EventListener
from arkhe.ignite.events import EventBus
import dataclasses

@dataclasses.dataclass
class UserRegistered:
    user_id: int
    email: str

@Service
class NotificationService:
    @EventListener(UserRegistered)
    async def on_user_registered(self, event: UserRegistered):
        print(f"Welcome email sent to {event.email}")

await app.context.event_bus.publish(UserRegistered(user_id=1, email="alice@example.com"))
```

### Scheduled Tasks

```python
from arkhe.ignite.decorators import Scheduled

@Service
class ReportJob:
    @Scheduled("0 8 * * 1")    # every Monday at 08:00
    async def weekly_report(self):
        ...

    @Scheduled("*/5 * * * *")  # every 5 minutes
    def poll_queue(self):
        ...
```

### Testing

```python
from arkhe.ignite.testing import TestContainer
from unittest.mock import MagicMock

def test_user_service():
    container = TestContainer()
    mock_repo = MagicMock()
    mock_repo.find.return_value = {"id": 1, "name": "Alice"}

    container.override(UserRepository, mock_repo)
    container.register(UserService)

    service = container.get(UserService)
    assert service.get_user(1)["name"] == "Alice"
```

**Installation extras:**

```bash
pip install arkhe-ignite[web]       # FastAPI + uvicorn
pip install arkhe-ignite[jwt]       # PyJWT
pip install arkhe-ignite[scheduler] # croniter
pip install arkhe-ignite[all]       # everything
```

---

## 🦎 Komodo — Metaprogramming

> Lombok-style, annotation-driven metaprogramming via AST. Eliminates class boilerplate with composable decorators — no metaclasses, no runtime proxies, no wrappers. Methods are generated as native bytecode.

### Constructor Decorators

| Decorator | Generated `__init__` | Lombok equivalent |
|---|---|---|
| `@komodo.all_args_constructor` | All annotated fields as parameters | `@AllArgsConstructor` |
| `@komodo.required_args_constructor` | Only fields without defaults | `@RequiredArgsConstructor` |
| `@komodo.no_args_constructor` | No parameters (uses defaults) | `@NoArgsConstructor` |

### Core Decorators

| Decorator | What it generates | Lombok equivalent |
|---|---|---|
| `@komodo.data` | `__init__`, `__repr__`, `__eq__`, `__hash__` | `@Data` |
| `@komodo.value` | Immutable data object — `data` + `immutable` | `@Value` |
| `@komodo.record` | `data` + `immutable` + full serialization | `@Value` + extras |
| `@komodo.builder` | Fluent `.Builder` inner class with `.build()` | `@Builder` |
| `@komodo.immutable` | `__setattr__`/`__delattr__` freeze after construction | — |
| `@komodo.logger` | Injects a stdlib `logger` class attribute | `@Slf4j` |
| `@komodo.copyable` | `.copy()` and `.copy_with(**overrides)` | `@With` |
| `@komodo.getter` | `get_<field>()` methods for all fields | `@Getter` |
| `@komodo.setter` | `set_<field>(value)` methods for all fields | `@Setter` |
| `@komodo.withers` | `with_<field>(value)` — returns new instance | `@With` |
| `@komodo.non_null` | `ValueError` if any arg is `None` | `@NonNull` |
| `@komodo.validated` | Runtime type-checking from annotations | — |
| `@komodo.to_dict` | `.to_dict() -> dict` | — |
| `@komodo.json` | `.to_json()` and `.from_json()` | — |

### Examples

```python
from arkhe.komodo import komodo

# Data class — auto __init__, __repr__, __eq__, __hash__
@komodo.logger
@komodo.copyable
@komodo.data
class Product:
    id: int
    name: str
    price: float
    active: bool = True

p  = Product(1, "Widget", 9.99)
p2 = p.copy_with(price=7.99)
Product.logger.info("Price updated")

# Fluent builder with validation
@komodo.builder
@komodo.validated
@komodo.all_args_constructor
class CreateUserRequest:
    username: str
    email: str
    role: str = "viewer"

req = (
    CreateUserRequest.builder()
        .with_username("alice")
        .with_email("alice@example.com")
        .with_role("admin")
        .build()
)

# Immutable value object
@komodo.value
class Money:
    amount: float
    currency: str

m = Money(9.99, "USD")
m.amount = 0.0  # AttributeError: Money is immutable
```

### Design by Contract

```python
from arkhe.komodo import contract
from arkhe.komodo.contract import requires, ensures, invariant

@komodo.all_args_constructor
class BankAccount:
    balance: float

    @contract(
        requires(lambda self, amount: amount > 0, "amount must be positive"),
        invariant(lambda self: self.balance >= 0, "balance must never be negative"),
    )
    def withdraw(self, amount: float) -> None:
        self.balance -= amount
```

### KomodoInspector

```python
from arkhe.komodo import KomodoInspector

info = KomodoInspector(Product)
print(info.features)          # {'data', 'all_args_constructor', 'to_str', 'eq', ...}
print(info.fields)            # {'id': int, 'name': str, 'price': float, 'active': bool}
print(info.summary())         # formatted ASCII table
```

---

## 🗄 Database — SQLite Toolkit

> A fluent, lightweight SQLite query builder with entity mapping, transactions, and safe result types. Zero external dependencies.

```python
from dataclasses import dataclass
from arkhe.database import DB, db_entity, db_column

DB.connect("app.db", wal=True)

@db_entity("users")
@dataclass
class User:
    id:    int = db_column(primary_key=True)
    email: str = db_column(unique=True)
    name:  str = db_column(nullable=False)

DB.create_table(User)

# INSERT
row_id = DB.insert_into("users").values(name="Alice", email="alice@example.com").execute()

# SELECT — mapped to objects
users: list[User] = DB.select("*").from_table("users").into(User)

# SELECT — fluent filtering
active = (
    DB.select("id", "name")
      .from_table("users")
      .where("active = ?", True)
      .order_by("name", "ASC")
      .limit(10)
      .execute()
)

# UPDATE / DELETE
DB.update("users").set(name="Alice Smith").where("id = ?", 1).execute()
DB.delete_from("users").where("id = ?", 99).execute()

# Transactions — re-entrant safe
with DB.transaction():
    DB.update("accounts").set(balance=400).where("id = ?", 1).execute()
    DB.update("accounts").set(balance=1100).where("id = ?", 2).execute()

# Safe execution — never raises
result = DB.insert_into("users").values(email="dup@example.com").execute_safe()
if result.is_success:
    print(f"rowid: {result.data}")
else:
    print(result.error_message)
```

**Python → SQLite type mapping:** `int` → `INTEGER`, `float` → `REAL`, `str` → `TEXT`, `bytes` → `BLOB`, `bool` → `INTEGER`.

---

## 🏛 OOP — Object-Oriented Utilities

> Explicit interfaces, abstract classes, `@override` and `@final` with **fail-fast validation at class definition time** — not at instantiation. Errors are caught when the module is loaded.

```python
from arkhe.oop import interface, implements, abstract_class, abstract_method, override, final

@interface
class ILogger:
    def log(self, message: str) -> None:
        pass

@interface
class IHealthCheck:
    def is_healthy(self) -> bool:
        pass

@abstract_class
class BaseService:
    def startup(self):
        print("Service started")

    @abstract_method
    def execute(self):
        pass

@implements(ILogger, IHealthCheck)
class UserService(BaseService):
    def log(self, message: str) -> None:
        print(f"[UserService] {message}")

    def is_healthy(self) -> bool:
        return True

    @override
    def execute(self):
        print("Executing user logic")

@final
class AppConfig:
    debug: bool = False
    version: str = "1.0.0"
```

**Missing implementation → immediate error at class definition:**

```
InterfaceImplementationError

Class UserService does not implement:

 - log(message: str) -> None
```

| Feature | `arkhe.oop` | Python `abc` |
|---|---|---|
| Explicit interfaces | `@interface` | No equivalent |
| Implementation validation | `@implements` — at class definition | Only at instantiation |
| Descriptive errors with signatures | Yes | Basic |
| Interface inheritance | Yes, accumulative | No equivalent |
| Interface attributes | Yes | No equivalent |
| `@override` with validation | Yes | No equivalent |
| `@final` | Yes | No equivalent |

---

## 🎮 Pyunix — 2D Game Engine

> A fully declarative game engine built on top of Pygame — inspired by Unity and Godot. No messy `while True` loops.

### Game Loop

```python
from arkhe.pyunix.app import Game

@Game(title="My Game", size=(800, 600), fps=60, vsync=True)
class MyGame:

    @Game.start
    def on_start(self):
        pass  # load resources, create entities

    @Game.update
    def on_update(self, dt: float):
        pass  # frame logic

    @Game.draw
    def on_draw(self, screen):
        screen.fill((30, 30, 40))

    @Game.text(x=10, y=10, size=20, color="yellow")
    def score_label(self):
        return f"Score: {self.score}"

MyGame().run()
```

### Entities & Physics

```python
from arkhe.pyunix.sprite import Entity
from arkhe.pyunix.physics import Rigidbody, BoxCollider, BodyType, PhysicsWorld
from arkhe.pyunix.input import Input
from arkhe.pyunix.math import Vector2

PhysicsWorld.set_gravity(0, 900)

class Player(Entity):
    def __init__(self):
        super().__init__(
            x=200, y=300,
            rigidbody=Rigidbody(body_type=BodyType.DYNAMIC, gravity_scale=1.0),
            collider=BoxCollider(28, 48),
        )

    @Entity.update
    def move(self, dt):
        h = Input.get_axis("horizontal")
        self.rigidbody.velocity.x = h * 200
        if Input.action_just_pressed("jump"):
            self.rigidbody.add_impulse(Vector2(0, -450))

    @Entity.on_collision_enter
    def on_hit(self, info):
        if info.normal.y < -0.5:
            self.on_ground = True
```

### Sprite Lifecycle Hooks

| Hook | When it fires |
|---|---|
| `@Sprite.ready` | Once, on construction |
| `@Sprite.update` | Every frame (receives `dt`) |
| `@Sprite.fixed_update` | Fixed physics timestep |
| `@Sprite.draw` | Every frame (receives `surface`) |
| `@Sprite.destroy` | Before entity is removed |
| `@Sprite.on_collision_enter` | First frame of collision |
| `@Sprite.on_collision_stay` | Each frame while colliding |
| `@Sprite.on_collision_exit` | When collision ends |
| `@Sprite.on_trigger_enter` | On entering a trigger zone |
| `@Sprite.pause` / `@Sprite.resume` | On game pause/resume |

### Included Systems

- **Camera** — smooth follow, world bounds, shake, offset
- **Audio** — music streaming, SFX with pitch variation
- **Assets** — preloading, caching, image/audio/font management
- **Animation** — spritesheet-based with state machine
- **Particles** — burst and continuous emitters
- **Tween** — property animation with easing functions
- **TileMap** — tile-based map rendering with auto-culling
- **Timer** — `Timer.after()`, `Timer.every()` callbacks
- **Scene** — scene manager with push/pop stack
- **Events** — pub/sub event system between entities

> **Debug:** Press `F3` at runtime for an overlay showing FPS, physics bodies, camera position, and time scale.

---

## ⚙️ YAML — Intelligent Config Registry

> Not just a parser — a runtime configuration engine with O(1) lookup and hot-reload.

```yaml
# config/database.yml
database:
  host: "localhost"
  port: 5432
  pool:
    min_size: 2
    max_size: 10
```

```python
from arkhe import yaml

# Zero-boilerplate: auto-scans all .yml files in your project
host     = yaml.get("database.host")      # string dot-path
max_pool = yaml.database.pool.max_size    # Pythonic attribute access

# Watch for changes in long-running processes
yaml.watch(True)

# Explicit scan for a specific directory
from pathlib import Path
yaml.scan(Path("src/config/"))

# Trace where a value comes from
print(yaml.where("database.host"))  # "/absolute/path/to/database.yml"
```

**How it works:** on first access, Arkhe scans your project and generates a `.arkhe/yaml_index.json` flat index — every dot-path mapped to its source file. Subsequent lookups are O(1). Only changed files are re-parsed.

> Add `.arkhe/` to your `.gitignore`.

---

## 🔒 Env — Environment Management

> Modern, typed, chainable `.env` variable management. Inspired by NestJS and Spring Boot.

```python
from arkhe import env
from arkhe.env import Env

Env.load()  # or Env.load("config/.env")

# Chainable attribute access — auto-uppercases all segments
host  = env.db.host             # → DB_HOST
port  = env.db.port.int         # → int(DB_PORT)
debug = env.debug.bool          # → bool(DEBUG)
hosts = env.allowed_hosts.list  # → ["localhost", "127.0.0.1"]

# Guards and defaults
secret = env.secret_key.required          # raises ConfigError if missing
db_pw  = env.db.password.default("root")  # fallback value
```

**Resolution flow:** `env.db.pool.max_size.int` → `int(os.environ["DB_POOL_MAX_SIZE"])`.

```python
# Descriptor API
class Config:
    host = Env.property("DB_HOST", default="localhost")
    port = Env.property("DB_PORT", cast_type=int, default=5432)

# Injection decorator
@Env.inject(api_key="API_KEY", host="DB_HOST")
def connect(api_key=None, host=None):
    ...
```

---

## 🧵 Loom — Configuration Engine

> A structured alternative to `.env` — hierarchical, typed, modular config files. Zero external dependencies.

```loom
# app.loom
@module("app")

@server {
    host: "localhost"
    port: 8080
    debug: true
}

@database {
    host: "127.0.0.1"
    port: 5432
    name: "myapp"
    pool: { min: 2, max: 10 }
}
```

```python
from arkhe.loom import Loom, env

Loom.load("app.loom")

host  = env.app.server.host     # fully qualified
port  = env.server.port.int     # scope-level flattening
debug = env.debug.bool          # global flattening (if unique)

# Schema binding to dataclasses
@Loom.bind("database", scope="database")
@dataclasses.dataclass
class DbConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "myapp"

# Hot-reload watchers
@Loom.watch("server.port")
def on_port_change(new_value):
    restart_http_server(int(new_value))
```

**Rust-style diagnostics:**

```
🚨 LoomSyntaxError in 'database.loom' (Line 4)

    3 | @db.main {
    4 |     host = "localhost"
                ^
    5 | }

Error:   Property 'host' uses '=' instead of ':'
Hint:    Replace with: host: "localhost"
```

---

## 🌐 Net — HTTP Client

> Fluent HTTP client for the Arkhe ecosystem. No external dependencies — pure stdlib (`urllib`).

```python
from arkhe.net import request, API

# Before (standard Python)
import urllib.request, json
req = urllib.request.Request(url, headers={"Authorization": "Bearer token"})
with urllib.request.urlopen(req, timeout=5) as r:
    data = json.loads(r.read())

# After (Arkhe Net)
r = request(url).auth_bearer(token).timeout(5).get()
if r.success:
    print(r.json)
```

### Fluent Builder

```python
result = (
    request("https://api.example.com/users/42")
    .auth_bearer("my-token")
    .timeout(10)
    .retry(attempts=3, delay=1, exponential=True)
    .cache(minutes=5)
    .expect(200)
    .on_success(lambda r: print(f"Loaded in {r.elapsed_ms:.0f}ms"))
    .get()
)
```

### Reusable Session with `API`

```python
api = (
    API("https://api.github.com")
    .auth_bearer(token)
    .timeout(10)
    .retry(3)
)

octocat = api.get("/users/octocat").json
repos   = api.get("/users/octocat/repos").json
api.post("/repos", json={"name": "new-repo", "private": False})
```

### Response

| Property | Description |
|---|---|
| `r.status` | HTTP status code |
| `r.success` / `r.ok` | `True` if `200 ≤ status < 300` |
| `r.json` | Deserialised body |
| `r.text` | Body as UTF-8 string |
| `r.bytes` | Body as raw bytes |
| `r.elapsed_ms` | Execution time in ms |
| `r.headers` | Response headers dict |
| `r.cookies` | Cookies from `Set-Cookie` |

---

## 🗂 Collections

> Java-inspired, fluent data structures with type hint support.

```python
from arkhe.collections import (
    ArrayList, LinkedList, Stack, Queue,
    OrderedSet, HashMap, BiMap, MultiMap,
    PriorityQueue, CircularBuffer, Stream, Optional, Result,
)

# Lazy Stream pipeline — functional-style data processing
result = (
    Stream.range(1, 11)
    .filter(lambda n: n % 2 == 0)
    .map(lambda n: n ** 2)
    .take(3)
    .to_list()
)  # [4, 16, 36]

# Fixed-capacity ring buffer — evicts oldest on overflow
logs = CircularBuffer(3)
logs.add("A").add("B").add("C").add("D")
logs.to_list()  # ["B", "C", "D"]

# Priority queue — min-heap by default
tasks = PriorityQueue()
tasks.add("High priority", priority=1)
tasks.add("Low priority",  priority=10)
tasks.poll()  # "High priority"

# BiMap — bidirectional one-to-one mapping
roles = BiMap()
roles.put("ADMIN", 1).put("MOD", 2)
roles.get("ADMIN")   # 1
roles.get_key(2)     # "MOD"
```

| Structure | Description |
|---|---|
| `ArrayList` | Dynamic array with fluent API and bounds-checking |
| `LinkedList` | Doubly-linked list, O(1) insertions at both ends |
| `Stack` | LIFO — backed by Python list |
| `Queue` | FIFO — backed by `collections.deque` |
| `OrderedSet` | Unique elements preserving insertion order |
| `HashMap` | Fluent dict wrapper |
| `BiMap` | Bidirectional one-to-one map |
| `MultiMap` | One key → many values |
| `PriorityQueue` | Heap-backed, min or max, custom key function |
| `CircularBuffer` | Fixed-capacity ring buffer — evicts oldest |
| `Stream` | Lazy functional pipeline — map, filter, reduce, group, window… |
| `Optional` | Null-safe container — eliminates `if x is not None` |
| `Result` | Discriminated union — `Ok(value)` / `Err(error)` |

---

## ✨ Promise

> Asynchronous execution without asyncio, event loops, or futures. Inspired by JavaScript Promises, Java `CompletableFuture`, and C# Tasks.

```python
from arkhe.promise import Promise

# Chain transformations
Promise.of(load_user) \
       .map(lambda user: user.name) \
       .map(str.upper) \
       .then(print) \
       .catch(log_error) \
       .finally_(cleanup)

# Parallel execution — all in parallel, return ordered results
results = Promise.all(load_users, load_orders, load_products).join(timeout=30)

# Race — first to finish wins
Promise.race(server1, server2, server3).then(use_fastest)

# Any — first success wins (only fails if ALL fail)
Promise.any(api1, api2, api3).then(use_first_success)

# Built-in options in .of()
Promise.of(api_request, delay=1, timeout=10, retry=3)
```

**Internals:** `concurrent.futures.ThreadPoolExecutor` with a shared global pool. No asyncio exposed.

---

## 🛡 Trying

> Functional error handling without `try/except` scattered across your code. Inspired by Kotlin `Try`, Rust `Result`, and Scala `Either`.

```python
from arkhe.trying import Try

# Before
try:
    user = load_user()
    if not user.active:
        raise Exception("Inactive")
    print(user.name)
except Exception:
    print("Guest")

# After
Try.of(load_user) \
   .filter(lambda u: u.active, "Inactive user") \
   .map(lambda u: u.name) \
   .recover(lambda ex: "Guest") \
   .on_success(print)
```

| Method | `Success` | `Failure` |
|---|---|---|
| `.map(fn)` | Transforms value | Passes through |
| `.flat_map(fn)` | `fn` returns Try | Passes through |
| `.filter(pred, msg)` | Fails if pred=False | Passes through |
| `.recover(fn)` | Passes through | Converts to Success |
| `.recover_if(type, fn)` | Passes through | Recovers only on matching type |
| `.on_success(fn)` | Executes `fn(value)` | Ignored |
| `.on_failure(fn)` | Ignored | Executes `fn(error)` |
| `.tap(fn)` | Side-effect, returns self | Ignored |
| `.or_else(default)` | Returns value | Returns default |
| `.to_optional()` | Returns value | Returns `None` |
| `.to_promise()` | `Promise.resolved(v)` | `Promise.rejected(e)` |

---

## 🗓 Scheduler

> Fluent cron-style task scheduler — thread-safe, no asyncio, no external dependencies.

```python
from arkhe.scheduler import Scheduler

Scheduler.every(30).seconds(sync_cache)

Scheduler.every(5).minutes(
    lambda: request("https://api.example.com/health").get()
).log()

Scheduler.every(1).hours(generate_report) \
         .name("daily-report") \
         .on_error(lambda ex: log.error(ex))

Scheduler.start()
```

---

## ⏱ Flow — Control Flow

> Advanced task scheduling, throttling, concurrency, and rate limiting.

```python
from arkhe.flow import Flow

@Flow.interval(5.0)
def ping_server():
    print("Ping!")

@Flow.throttle(1.0)
def on_mouse_move(x, y):
    pass

@Flow.retry(times=3, wait=2.0)
def fetch_api():
    pass

@Flow.debounce(wait=0.3)
def on_search_input(query):
    search(query)

results = Flow.parallel(task_a, task_b, task_c)
```

**Available utilities:** `@Flow.delay`, `@Flow.repeat`, `@Flow.interval`, `@Flow.retry`, `@Flow.timeout`, `@Flow.debounce`, `@Flow.throttle`, `@Flow.once`, `@Flow.after`, `Flow.parallel`, `@Flow.threaded`, `Flow.run_async`, `Flow.schedule`, `Flow.loop`.

---

## 🎛 Input

> Interactive CLI inputs, forms, and validation.

```python
from arkhe.input import Input

name  = Input.text("What is your name?", default="Guest")
age   = Input.integer("Age?", min=0, max=120)
email = Input.email("Email address?")
tags  = Input.multi_select("Topics", ["Python", "Games", "Web"])
```

---

## ✨ Decorators

> A comprehensive suite of utility decorators. All preserve function metadata via `functools.wraps`.

```python
from arkhe.decorators import benchmark, cache, retry, validate_types, event, emit

@benchmark
@cache
def expensive_calculation(x):
    return sum(i * i for i in range(x))

@retry(times=3, delay=2.0)
def fetch_api_data():
    pass

@validate_types
def process_user(age: int, name: str):
    pass  # raises TypeError if types don't match

@event("user_registered")
def send_welcome_email(user_id):
    pass

emit("user_registered", 101)
```

| Category | Decorators |
|---|---|
| Execution | `@benchmark`, `@cache`, `@once`, `@rate_limit` |
| Resiliency | `@safe`, `@trace`, `@retry` |
| Threading | `@threaded`, `@async_task`, `@delay` |
| Validation | `@not_null`, `@validate`, `@validate_types` |
| Architecture | `@singleton`, `@observable`, `@startup`, `@shutdown`, `@event` |
| Documentation | `@deprecated`, `@experimental` |

---

## 📋 SLogger — System Logger

> A professional, colourised, extensible logger — from `"Hello, World!"` to production.

```python
from arkhe.slogger import get_logger, SLogger, LogLevel

log = get_logger("server", level=LogLevel.DEBUG, file="server.log")

log.info("Server starting on port 8080")
log.success("Database connected!")
log.warn("Memory usage above 80%")
log.error("Failed to reach upstream service")
log.fatal("Unrecoverable error — shutting down")

# Decorators
@log.log_calls(show_return=True, show_time=True)
def calculate(x, y):
    return x + y

@log.catch_errors(ConnectionError, default=None)
def connect_database(host: str):
    ...

@log.time_it(label="startup sequence")
def boot():
    ...
```

| Level | Colour | Use |
|---|---|---|
| `TRACE` | Dim cyan | Detailed flow tracing |
| `DEBUG` | Cyan | Internal variables, states |
| `INFO` | Blue | Normal application events |
| `SUCCESS` | Bright green | Completed operations |
| `WARN` | Bright yellow | Unusual, non-critical situations |
| `ERROR` | Bright red | Recoverable errors |
| `FATAL` | Red background | Unrecoverable failures |

```python
# Formatters
# Default: [14:32:01] [INFO ] [server] Message
# Simple:  [INFO ] Message
# JSON:    {"ts": "14:32:01", "level": "INFO", "prefix": "server", "msg": "Message"}

from arkhe.slogger import JSONFormatter
log = get_logger("api", formatter=JSONFormatter())
```

---

## 🖥 Console — Terminal Utilities

> Rich terminal output for modern CLI applications.

```python
from arkhe.console import Console

Console.success("Migration complete!")
Console.error("Failed to connect.")
Console.warn("Memory usage high.")
Console.info("Server starting...")
Console.print("Custom", color="magenta", bold=True)

# Interactive prompts
name = Console.ask("Your name?", default="Guest")
go   = Console.confirm("Proceed?", default=True)
env  = Console.choose("Environment", ["dev", "staging", "prod"])

# Progress tracking
with Console.progress(total=100, label="Downloading") as bar:
    for _ in range(100):
        bar.update(1)

# Animated spinner
with Console.spinner("Fetching data..."):
    time.sleep(2)

# Structured table
Console.table([
    {"ID": 1, "Name": "Alice", "Role": "Admin"},
    {"ID": 2, "Name": "Bob",   "Role": "User"},
], title="User Directory")
```

---

## 🧮 Math

> Game-ready math primitives — vectors, matrices, easing functions, and geometry utilities.

```python
from arkhe.pyunix.math import Vector2, Vector3, Matrix4, Color

v  = Vector2(3, 4)
v2 = v.normalised()          # (0.6, 0.8)
d  = v.dot(Vector2(1, 0))

red   = Color.RED
faded = red.lerp(Color.BLACK, 0.5)
```

---

## 📁 OS & File Utilities

> Fluent file and directory interaction helpers.

```python
from arkhe.os import File, Dir

content = File("config.json").read()
File("output.txt").write("Hello, World!")
File("data.json").copy_to("backup/data.json")

Dir("src/").list()     # list all entries
Dir("logs/").ensure()  # create if not exists
Dir("old/").delete()
```

---

## 🏗 CLI Scaffolding

Bootstrap a professional project structure in one command:

```bash
arkhe init --name my_app
```

Generated structure includes pre-configured support for `ruff`, `pytest`, and `mypy`.

---

## 📝 Changelog

### v0.3.0 — Workspace Architecture
- **Breaking:** Migrated from monolithic `pip install arkhe` to **11 independent Namespace Packages** (`arkhe-core`, `arkhe-meta`, `arkhe-net`, etc.).
- **Tooling:** Adopted `uv` workspaces for monorepo management and `hatchling` as the modern build backend.
- **Architecture:** Each package has its own `pyproject.toml` with explicit dependencies — no more accidental cross-module coupling.
- **Compatibility:** All existing `arkhe.*` imports continue to work unchanged thanks to Python Namespace Packages.

### v0.2.3
- **Database:** Added `arkhe.database` — fluent SQLite toolkit with entity mapping, transactions, and `DBResult` safe execution.
- **OOP:** Added `arkhe.oop` — interfaces, abstract classes, `@override`, and `@final` with fail-fast validation at class definition time.
- **Komodo:** Replaced `@komodo.constructor` with three explicit constructors: `@komodo.no_args_constructor`, `@komodo.required_args_constructor`, `@komodo.all_args_constructor` — aligned with Lombok's naming. Updated `@komodo.getter` and `@komodo.setter` to generate explicit `get_<field>()`/`set_<field>(value)` methods instead of Python properties.
- **Trying:** Added `Try` monad for fluent, functional error handling without `try/except`.
- **Promise:** Implemented modern Promise API for async execution (`then`, `catch`, `all`, `race`, `any`) without asyncio.
- **Input:** Added comprehensive module for interactive CLI inputs, form handling, and data sanitisation.
- **SLogger:** Upgraded core logger — colours, formatters, decorators, context managers.

### v0.2.2
- **Pyunix:** Fixed physics bounding box discrepancies (`rect.topleft` vs `rect.center`) ensuring pixel-perfect `BoxCollider` interactions.
- **FlappyBird Demo:** Refactored `examples/flappybird.py` to use Pyunix's modern physics engine, Animator, and Trigger zones.
- **Ignite Docs:** Published comprehensive documentation covering DI, FastAPI, EventBus, Scheduled Tasks, and TestContainers.

### v0.2.1
- **Ignite Core:** Rebranded and refactored the legacy `bolt` container into the `ignite` application framework.
- **EventBus:** Added publish/subscribe event bus.
- **Web module:** Seamless FastAPI integration.
- **Cron Jobs:** Introduced `@Scheduled` decorators via `croniter`.
- **Testing:** Added `TestContainer` for dependency-isolated integration testing.

---

## 📚 Documentation

Full documentation is available in the `docs/` directory:

| Module | Doc |
|---|---|
| 🔥 Ignite Framework | [docs/ignite.md](docs/ignite.md) |
| 🦎 Komodo Metaprogramming | [docs/komodo.md](docs/komodo.md) |
| 🗄 Database Toolkit | [docs/database.md](docs/database.md) |
| 🏛 OOP Utilities | [docs/oop.md](docs/oop.md) |
| 🎮 Pyunix Game Engine | [docs/pyunix.md](docs/pyunix.md) |
| ⚙️ YAML Intelligent Registry | [docs/yaml.md](docs/yaml.md) |
| 🔒 Environment Management | [docs/env.md](docs/env.md) |
| 🧵 Loom Configuration | [docs/loom.md](docs/loom.md) |
| 🌐 Net HTTP Client | [docs/net.md](docs/net.md) |
| 🗂 Collections | [docs/collections.md](docs/collections.md) |
| ✨ Promise | [docs/promise.md](docs/promise.md) |
| 🛡 Trying | [docs/trying.md](docs/trying.md) |
| 🗓 Scheduler | [docs/scheduler.md](docs/scheduler.md) |
| ⏱ Flow Control | [docs/flow.md](docs/flow.md) |
| 🎛 Input | [docs/input.md](docs/input.md) |
| ✨ Decorators | [docs/decorators.md](docs/decorators.md) |
| 📋 SLogger | [docs/slogger.md](docs/slogger.md) |
| 🖥 Console Utilities | [docs/console.md](docs/console.md) |
| 🧮 Math | [docs/math.md](docs/math.md) |
| 📁 OS & File Utilities | [docs/os.md](docs/os.md) |

---

## 🏗 Project Structure

Arkhe uses a **monorepo** managed by [`uv`](https://docs.astral.sh/uv/) workspaces:

```text
arkhe/
├── pyproject.toml          # Workspace root
├── packages/
│   ├── arkhe-core/         # Foundation types & utilities
│   ├── arkhe-meta/         # Komodo, OOP, decorators
│   ├── arkhe-config/       # YAML, JSON, Env
│   ├── arkhe-web/          # Ignite, Loom
│   ├── arkhe-net/          # HTTP client
│   ├── arkhe-math/         # BigDecimal, Money
│   ├── arkhe-game/         # Pyunix game engine
│   ├── arkhe-db/           # Database, Collections
│   ├── arkhe-scheduler/    # Scheduler, Flow
│   ├── arkhe-log/          # SLogger
│   └── arkhe-os/           # OS, Console, Input, CLI
└── tests/
```

---

## 🤝 Contributing

Contributions are welcome!

1. Clone the repository
2. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already
3. Sync the workspace: `uv sync --all-packages`
4. Run tests: `uv run pytest`
5. Lint code: `ruff check .`

---

## 🛡 Security

Please review our [Security Policy](SECURITY.md) for information on reporting vulnerabilities.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Built with ❤️ for Pythonistas who believe in clean, expressive code.</sub>
</div>
