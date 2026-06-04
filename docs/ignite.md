# arkhe.ignite

> A Spring Boot-inspired application framework for Python — part of the **arkhe** ecosystem.

`arkhe.ignite` brings the developer experience of Spring Boot to Python: dependency injection, auto-configuration, lifecycle hooks, event bus, scheduled tasks, and a web layer — all wired together through a single `Application.run()` call.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Layout](#project-layout)
- [Core Concepts](#core-concepts)
  - [Application Bootstrap](#application-bootstrap)
  - [ApplicationContext](#applicationcontext)
  - [IOC Container & Dependency Injection](#ioc-container--dependency-injection)
  - [Bean Scopes](#bean-scopes)
- [Decorators](#decorators)
  - [Stereotype Decorators](#stereotype-decorators)
  - [@Configuration and @Bean](#configuration-and-bean)
  - [@Value](#value)
  - [@PostConstruct and @PreDestroy](#postconstruct-and-predestroy)
  - [@EventListener](#eventlistener)
  - [@Scheduled](#scheduled)
  - [@AsyncTask](#asynctask)
- [Web Layer](#web-layer)
  - [@Controller and HTTP Methods](#controller-and-http-methods)
  - [Web Starter](#web-starter)
  - [Accessing the FastAPI App](#accessing-the-fastapi-app)
- [Configuration](#configuration)
  - [application.yml](#applicationyml)
  - [Profiles](#profiles)
  - [Properties API](#properties-api)
- [Events](#events)
  - [Built-in Application Events](#built-in-application-events)
  - [Custom Events](#custom-events)
  - [EventBus API](#eventbus-api)
- [Lifecycle](#lifecycle)
- [Security — JwtService](#security--jwtservice)
- [Scheduler](#scheduler)
- [Testing](#testing)
- [Exceptions Reference](#exceptions-reference)
- [Package Map](#package-map)
- [Optional Dependencies](#optional-dependencies)

---

## Installation

```bash
pip install arkhe-ignite

# With web server support (FastAPI + uvicorn)
pip install arkhe-ignite[web]

# With JWT support
pip install arkhe-ignite[jwt]

# With scheduled tasks
pip install arkhe-ignite[scheduler]

# Everything
pip install arkhe-ignite[all]
```

---

## Quick Start

```python
from arkhe.ignite import Application
from arkhe.ignite.decorators import Service, Controller, PostConstruct
from arkhe.ignite.web.rest import Get, Post

@Service
class UserService:
    def get_users(self) -> list[str]:
        return ["Hope", "Alex"]

    def create_user(self, name: str) -> dict:
        return {"id": 1, "name": name}


@Controller("/users")
class UserController:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    @Get("/")
    async def list_users(self):
        return self.user_service.get_users()

    @Post("/")
    async def create_user(self, name: str):
        return self.user_service.create_user(name)

    @PostConstruct
    async def on_start(self):
        print("UserController ready!")


app = Application.run(web=True, starters=["web"])
```

---

## Project Layout

Recommended structure for an ignite application:

```
myapp/
├── application.yml          # configuration
├── main.py                  # entry point
└── src/
    ├── controllers/
    │   └── user_controller.py
    ├── services/
    │   └── user_service.py
    ├── repositories/
    │   └── user_repository.py
    └── config/
        └── app_config.py
```

`main.py`:

```python
from arkhe.ignite import Application

app = Application.run(config_dir=".", web=True, starters=["web"])
```

---

## Core Concepts

### Application Bootstrap

`Application.run()` is the single entry point. It orchestrates the full boot sequence:

1. Builds the `ApplicationContext`
2. Registers all `@Component` / `@Service` / `@Controller` / `@Repository` beans
3. Processes `@Configuration` classes and their `@Bean` factory methods
4. Runs any activated starters (e.g. `"web"`)
5. Instantiates all beans and runs `@PostConstruct` hooks
6. Wires all `@EventListener` methods
7. Starts the `@Scheduled` task executor
8. Publishes `ApplicationStartedEvent` and `ApplicationReadyEvent`
9. Optionally starts the web server (blocking)

```python
from arkhe.ignite import Application

# Minimal
app = Application.run()

# With web server
app = Application.run(web=True, starters=["web"])

# Custom config directory and starters
app = Application.run(config_dir="/etc/myapp", web=True, starters=["web", "security"])

# Graceful shutdown
await app.stop()
```

| Parameter    | Type        | Default | Description                              |
|-------------|-------------|---------|------------------------------------------|
| `config_dir` | `str`       | `"."`   | Directory containing `application.yml`   |
| `web`        | `bool`      | `False` | Start the web server after boot          |
| `starters`   | `list[str]` | `[]`    | Auto-configuration modules to activate  |

---

### ApplicationContext

The central hub of the application. Available anywhere via `get_context()` or through constructor injection.

```python
from arkhe.ignite.core.boot import get_context

ctx = get_context()
user_service = ctx.get_bean(UserService)
port = ctx.get_property("server.port", 8080)
```

| Method                              | Description                                      |
|------------------------------------|--------------------------------------------------|
| `get_bean(cls)`                    | Retrieve a registered bean by type               |
| `register_bean(cls, **kwargs)`     | Programmatically register a bean                 |
| `get_property(key, default=None)`  | Read a config value by dot-notation key          |
| `get_value(key, required=True)`    | Read a config value, raises if missing           |
| `context.event_bus`                | Access the `EventBus`                            |
| `context.container`                | Access the raw `Container`                       |
| `context.properties`               | Access the `Properties` object                   |

---

### IOC Container & Dependency Injection

Ignite uses **constructor injection** by default. Declare your dependencies as typed constructor parameters — the container resolves them automatically.

```python
@Service
class EmailService:
    def send(self, to: str, body: str): ...


@Service
class NotificationService:
    # EmailService is injected automatically
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    def notify(self, user: str):
        self.email_service.send(user, "Hello!")
```

The container uses `inspect.signature` and `get_type_hints` to resolve dependencies at instantiation time. Circular dependencies are detected and raise `CircularDependencyException`.

---

### Bean Scopes

| Scope       | Behaviour                                          | Declaration                      |
|-------------|----------------------------------------------------|----------------------------------|
| `SINGLETON` | One instance shared across the entire application  | Default for all stereotypes      |
| `PROTOTYPE` | New instance created every time it is requested   | `@Service(scope="prototype")`    |

```python
from arkhe.ignite.decorators import Service

@Service(scope="prototype")
class RequestContext:
    def __init__(self):
        self.data = {}
```

---

## Decorators

All decorators are importable from the top-level `arkhe.ignite.decorators` package:

```python
from arkhe.ignite.decorators import (
    Component, Service, Repository, Controller, Configuration,
    Bean, Inject, Value, EventListener, Scheduled, AsyncTask,
    PostConstruct, PreDestroy,
)
```

---

### Stereotype Decorators

These mark a class as a managed bean and add it to the component registry. All support an optional `scope` keyword argument.

| Decorator        | Stereotype      | Typical Use                                |
|-----------------|-----------------|---------------------------------------------|
| `@Component`    | `component`     | Generic managed bean                        |
| `@Service`      | `service`       | Business logic layer                        |
| `@Repository`   | `repository`    | Data-access layer                           |
| `@Controller`   | `controller`    | HTTP request handler (takes a path prefix)  |

```python
@Component
class CacheManager: ...

@Service
class OrderService: ...

@Repository
class ProductRepository: ...

@Controller("/products")
class ProductController: ...
```

---

### @Configuration and @Bean

Use `@Configuration` to declare a class that provides beans via factory methods, and `@Bean` to mark each factory method.

```python
from arkhe.ignite.decorators import Configuration, Bean
from arkhe.ignite.security import JwtService

@Configuration
class SecurityConfig:

    @Bean
    def jwt_service(self) -> JwtService:
        return JwtService(secret="super-secret", expiry_minutes=30)
```

The return type (or the actual returned instance type) is used as the bean key in the container.

---

### @Value

Injects a configuration value from `application.yml` as a class field descriptor.

```python
from arkhe.ignite.decorators import Service, Value

@Service
class DatabaseService:
    db_url: str = Value("database.url")
    pool_size: int = Value("database.pool_size", default=5)

    def connect(self):
        print(f"Connecting to {self.db_url} (pool: {self.pool_size})")
```

`@Value` reads values lazily on first access, resolving them from the active `ApplicationContext`.

---

### @PostConstruct and @PreDestroy

Lifecycle hooks called automatically by the framework.

```python
from arkhe.ignite.decorators import Service, PostConstruct, PreDestroy

@Service
class CacheService:

    @PostConstruct
    async def warm_up(self):
        print("Loading cache...")

    @PreDestroy
    async def flush(self):
        print("Flushing cache before shutdown...")
```

Both sync and async methods are supported. Multiple methods can be annotated on the same class.

---

### @EventListener

Subscribe a method to a specific event type published on the `EventBus`.

```python
from arkhe.ignite.decorators import Service, EventListener
from arkhe.ignite.events.application_events import ApplicationReadyEvent

@Service
class StartupLogger:

    @EventListener(ApplicationReadyEvent)
    async def on_ready(self, event: ApplicationReadyEvent):
        print(f"Application ready at {event.timestamp}")
```

---

### @Scheduled

Run a method on a cron schedule. Requires `croniter` (`pip install arkhe-ignite[scheduler]`).

```python
from arkhe.ignite.decorators import Service, Scheduled

@Service
class CleanupJob:

    @Scheduled("0 2 * * *")   # every day at 02:00
    async def purge_old_records(self):
        print("Purging old records...")

    @Scheduled("*/30 * * * *")  # every 30 minutes
    def heartbeat(self):
        print("Heartbeat")
```

Standard 5-field cron expressions are supported (`minute hour day month weekday`).

---

### @AsyncTask

Wraps a method so it runs as a background `asyncio` task (fire-and-forget).

```python
from arkhe.ignite.decorators import Service, AsyncTask

@Service
class EmailService:

    @AsyncTask
    async def send_welcome_email(self, user_email: str):
        # Runs in background, does not block the caller
        await self._smtp_client.send(user_email, "Welcome!")
```

---

## Web Layer

### @Controller and HTTP Methods

Combine `@Controller` with the HTTP decorators from `arkhe.ignite.web.rest`:

```python
from arkhe.ignite.decorators import Controller
from arkhe.ignite.web.rest import Get, Post, Put, Patch, Delete

@Controller("/articles")
class ArticleController:

    def __init__(self, article_service: ArticleService):
        self.article_service = article_service

    @Get("/")
    async def list_articles(self):
        return self.article_service.find_all()

    @Get("/{article_id}")
    async def get_article(self, article_id: int):
        return self.article_service.find_by_id(article_id)

    @Post("/")
    async def create_article(self, title: str, body: str):
        return self.article_service.create(title, body)

    @Put("/{article_id}")
    async def update_article(self, article_id: int, title: str):
        return self.article_service.update(article_id, title)

    @Delete("/{article_id}")
    async def delete_article(self, article_id: int):
        return self.article_service.delete(article_id)
```

| Decorator    | HTTP Method |
|-------------|-------------|
| `@Get`      | GET         |
| `@Post`     | POST        |
| `@Put`      | PUT         |
| `@Patch`    | PATCH       |
| `@Delete`   | DELETE      |

All decorators accept a path string. Paths are relative to the controller's base path.

---

### Web Starter

Activate the web layer by passing `starters=["web"]` and `web=True`:

```python
app = Application.run(web=True, starters=["web"])
```

The web starter (`arkhe.ignite.starter.web_starter`) scans all `@Controller` beans registered at that point and mounts their routes on a FastAPI application using `APIRouter`.

Configure the server in `application.yml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8080
  reload: false
```

---

### Accessing the FastAPI App

You can access the underlying FastAPI instance for advanced use (custom middleware, testing with `TestClient`, etc.):

```python
from arkhe.ignite.web.server import WebServer

app = Application.run(web=False, starters=["web"])
web_server = app.context.get_bean(WebServer)
fastapi_app = web_server.app

# Use with httpx TestClient in tests
from fastapi.testclient import TestClient
client = TestClient(fastapi_app)
response = client.get("/users/")
assert response.status_code == 200
```

---

## Configuration

### application.yml

Place `application.yml` in the directory passed as `config_dir` (default: current directory).

```yaml
server:
  host: "0.0.0.0"
  port: 8080
  reload: false

database:
  url: "postgresql://localhost/mydb"
  pool_size: 10

jwt:
  secret: "change-me-in-production"
  expiry_minutes: 60

app:
  name: "My Ignite App"
  debug: false
```

Access values using dot-notation:

```python
ctx.get_property("database.url")         # "postgresql://localhost/mydb"
ctx.get_property("server.port", 8080)    # 8080 (with default)
```

---

### Profiles

Override configuration per environment using profile files:

```
application.yml            # base config (always loaded)
application-dev.yml        # merged on top when profile is "dev"
application-prod.yml       # merged on top when profile is "prod"
```

Activate a profile via environment variable:

```bash
ARKHE_PROFILE=dev python main.py
# or Spring-compatible:
SPRING_PROFILES_ACTIVE=prod python main.py
```

Profile values deep-merge over the base, so you only need to override what changes:

```yaml
# application-dev.yml
server:
  reload: true
database:
  url: "postgresql://localhost/mydb_dev"
```

---

### Properties API

The `Properties` object provides typed accessors:

```python
props = app.context.properties

props.get("server.port")                    # Any
props.get_int("server.port", 8080)          # int
props.get_bool("app.debug", False)          # bool
props.get_str("app.name", "default")        # str
props.require("jwt.secret")                 # Any — raises ConfigurationException if missing
```

---

## Events

### Built-in Application Events

| Event                      | Published when                                         |
|---------------------------|--------------------------------------------------------|
| `ApplicationStartedEvent`  | All beans initialized, scheduler started               |
| `ApplicationReadyEvent`    | Application fully ready to serve                       |
| `ApplicationStoppingEvent` | `app.stop()` called — before `@PreDestroy` hooks       |

All events carry a `timestamp: datetime` field.

---

### Custom Events

Define your own event as a plain dataclass and publish it on the bus:

```python
from dataclasses import dataclass

@dataclass
class UserCreatedEvent:
    user_id: int
    email: str
```

Publish from a service:

```python
from arkhe.ignite.core.boot import get_context

@Service
class UserService:
    async def create(self, email: str) -> dict:
        user = {"id": 42, "email": email}
        ctx = get_context()
        await ctx.event_bus.publish(UserCreatedEvent(user_id=42, email=email))
        return user
```

Subscribe in any bean:

```python
@Service
class WelcomeEmailSender:

    @EventListener(UserCreatedEvent)
    async def on_user_created(self, event: UserCreatedEvent):
        print(f"Sending welcome email to {event.email}")
```

---

### EventBus API

```python
from arkhe.ignite.events.event_bus import EventBus

bus = app.context.event_bus

# Subscribe manually
bus.subscribe(MyEvent, my_handler)

# Unsubscribe
bus.unsubscribe(MyEvent, my_handler)

# Async publish (awaitable)
await bus.publish(MyEvent(data="hello"))

# Sync publish (fire-and-forget for async handlers)
bus.publish_sync(MyEvent(data="hello"))

# Clear all listeners
bus.clear()
```

---

## Lifecycle

The full lifecycle of a bean:

```
Container.register(cls)
        ↓
BeanProvider._create(cls)       ← constructor injection resolved
        ↓
@PostConstruct methods called   ← after instantiation
        ↓
[ Bean is active and in use ]
        ↓
app.stop() called
        ↓
@PreDestroy methods called      ← before teardown
        ↓
ApplicationStoppingEvent published
```

Both `@PostConstruct` and `@PreDestroy` support sync and async methods, and multiple hooks per class.

---

## Security — JwtService

```python
from arkhe.ignite.security import JwtService

# Typically declared as a @Bean in a @Configuration class
jwt = JwtService(secret="my-secret", algorithm="HS256", expiry_minutes=60)

# Encode a payload
token = jwt.encode({"sub": "user-42", "role": "admin"})

# Decode (returns None if expired or invalid)
payload = jwt.decode(token)
# → {"sub": "user-42", "role": "admin", "exp": ...}

# Quick validity check
is_valid = jwt.is_valid(token)  # True / False
```

Requires `PyJWT`: `pip install arkhe-ignite[jwt]`

Recommended wiring:

```python
@Configuration
class SecurityConfig:

    @Bean
    def jwt_service(self) -> JwtService:
        secret = get_context().get_value("jwt.secret")
        expiry = get_context().properties.get_int("jwt.expiry_minutes", 60)
        return JwtService(secret=secret, expiry_minutes=expiry)
```

---

## Scheduler

Tasks marked with `@Scheduled` are picked up automatically during boot. The executor runs a 1-second polling loop comparing the current time against each task's cron expression.

```python
@Service
class ReportJob:

    @Scheduled("0 8 * * 1")     # every Monday at 08:00
    async def weekly_report(self):
        ...

    @Scheduled("*/5 * * * *")   # every 5 minutes
    def poll_queue(self):
        ...
```

Requires `croniter`: `pip install arkhe-ignite[scheduler]`

The scheduler is started automatically as part of `Application.run()` if any `@Scheduled` methods are found. It is cleanly stopped on `app.stop()`.

---

## Testing

Use `TestContainer` to isolate beans with mocks or stubs without booting the full application:

```python
from arkhe.ignite.testing import TestContainer
from unittest.mock import MagicMock

def test_user_controller_lists_users():
    container = TestContainer()

    mock_service = MagicMock()
    mock_service.get_users.return_value = ["Hope", "Alex"]

    container.override(UserService, mock_service)
    container.register(UserController)

    controller = container.get(UserController)
    result = controller.user_service.get_users()

    assert result == ["Hope", "Alex"]
    mock_service.get_users.assert_called_once()
```

`TestContainer` API:

| Method                          | Description                                      |
|---------------------------------|--------------------------------------------------|
| `override(cls, instance)`       | Replace a type with a specific mock or stub      |
| `register(cls, scope=SINGLETON)`| Register a real class                            |
| `get(cls)`                      | Resolve a bean (returns override if present)     |
| `clear()`                       | Reset all definitions and overrides              |

For integration tests using the web layer, use FastAPI's `TestClient`:

```python
from fastapi.testclient import TestClient

def test_list_users_endpoint():
    app = Application.run(web=False, starters=["web"])
    web_server = app.context.get_bean(WebServer)
    client = TestClient(web_server.app)

    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## Exceptions Reference

All exceptions extend `ArkheException` (itself extending `Exception`) and are importable from `arkhe.ignite.core.exceptions`.

| Exception                     | Raised when                                                         |
|------------------------------|---------------------------------------------------------------------|
| `BeanNotFoundException`       | A requested type is not registered in the container                 |
| `CircularDependencyException` | A cycle is detected in the dependency graph                         |
| `BeanInitializationException` | A bean's constructor raises an exception                            |
| `ConfigurationException`      | A required configuration key is missing or loading fails            |
| `ProfileNotFoundException`    | A profile-specific YAML file does not exist                         |
| `ValueInjectionException`     | A required `@Value` key is not set in `application.yml`             |

```python
from arkhe.ignite.core.exceptions import BeanNotFoundException

try:
    service = ctx.get_bean(UnregisteredService)
except BeanNotFoundException as e:
    print(e)  # Bean of type 'UnregisteredService' not found in the application context.
```

---

## Package Map

```
arkhe/ignite/
├── __init__.py                  Application, ApplicationContext
│
├── core/
│   ├── application.py           Application (bootstrap + boot sequence)
│   ├── boot.py                  get_context() / set_context()
│   ├── container.py             Container (IOC facade)
│   ├── context.py               ApplicationContext
│   ├── exceptions.py            All framework exceptions
│   └── lifecycle.py             @PostConstruct, @PreDestroy, run_* helpers
│
├── decorators/
│   ├── component.py             @Component + _COMPONENT_REGISTRY
│   ├── service.py               @Service
│   ├── repository.py            @Repository
│   ├── controller.py            @Controller + _CONTROLLER_REGISTRY
│   ├── configuration.py         @Configuration
│   ├── bean.py                  @Bean
│   ├── inject.py                @Inject
│   ├── value.py                 @Value (descriptor)
│   ├── event_listener.py        @EventListener
│   ├── scheduled.py             @Scheduled
│   └── async_task.py            @AsyncTask
│
├── di/
│   ├── registry.py              BeanRegistry
│   ├── provider.py              BeanProvider (resolution + circular dep check)
│   ├── injector.py              Injector (field injection)
│   └── scopes.py                Scope enum (SINGLETON / PROTOTYPE)
│
├── config/
│   ├── yaml_loader.py           YamlLoader (deep-merge, dot-access)
│   ├── properties.py            Properties (typed accessors)
│   ├── profiles.py              ProfileResolver (env var)
│   └── resolver.py              ValueResolver (@Value backend)
│
├── events/
│   ├── event_bus.py             EventBus (subscribe/publish sync+async)
│   └── application_events.py   ApplicationStartedEvent, ApplicationReadyEvent, ApplicationStoppingEvent
│
├── web/
│   ├── rest.py                  @Get, @Post, @Put, @Patch, @Delete
│   └── server.py                WebServer (FastAPI + uvicorn integration)
│
├── scheduler/
│   ├── tasks.py                 ScheduledTask, TaskRegistry
│   └── executor.py              SchedulerExecutor (croniter-backed loop)
│
├── security/
│   └── jwt.py                   JwtService (encode / decode / is_valid)
│
├── starter/
│   └── web_starter.py           "web" starter — registers WebServer bean
│
└── testing/
    └── container.py             TestContainer (mock-friendly DI for tests)
```

---

## Optional Dependencies

| Extra          | Packages installed                          | Enables                        |
|---------------|---------------------------------------------|--------------------------------|
| `[web]`        | `fastapi>=0.111`, `uvicorn[standard]>=0.29` | Web server, `@Controller`      |
| `[jwt]`        | `PyJWT>=2.8`                                | `JwtService`                   |
| `[scheduler]`  | `croniter>=2.0`                             | `@Scheduled` task executor     |
| `[all]`        | All of the above                            | Full feature set               |
| `[dev]`        | `pytest`, `pytest-asyncio`, `httpx`         | Running tests                  |

```bash
pip install arkhe-ignite[all]
```
