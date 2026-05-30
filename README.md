# 🪺 Nestifypy Framework

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)](https://github.com/nestifypy/nestifypy/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/nestifypy/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Security Policy](https://img.shields.io/badge/security-policy-lightgrey?style=flat-square)](SECURITY.md)

**Nestifypy** is a modern, declarative utility and game framework for Python 3.10+. It provides a highly declarative, decorator-driven approach to application development, focusing on performance, developer ergonomics, and strict type safety.

Whether you are building complex CLI tools, managing intelligent configuration registries, or developing 2D physics-based games, Nestifypy provides a robust foundation.

## 📖 The Nestifypy Ecosystem

Nestifypy is a modular framework composed of several distinct, high-performance packages:

1. **Komodo (`nestifypy.komodo`)**: Lombok-style annotation-driven metaprogramming. Eliminates Python boilerplate using decorators like `@komodo.data`, `@komodo.builder`, and provides robust Design-by-Contract constraints (`@contract`).
2. **Ignite (`nestifypy.ignite`)**: A Spring Boot-inspired enterprise application framework featuring advanced Dependency Injection, a robust Event Bus, and auto-configuration.
3. **Pyunix Game Engine (`nestifypy.pyunix`)**: A fully declarative, decorator-driven 2D game engine built on top of `pygame`, featuring built-in physics (Rigidbodies, Colliders), ECS-friendly architecture, and declarative UI.
4. **Core Utilities**: A suite of tools for intelligent configuration (YAML), declarative environment variable binding, cross-platform OS tasks, and CLI project scaffolding.

## 📦 Installation

Nestifypy requires **Python 3.10 or higher**.

**Core Framework Only (No Pygame dependencies):**
```bash
pip install nestifypy
```

**Full Framework (Includes Pyunix Game Engine):**
```bash
pip install "nestifypy[game]"
```

## 🚀 Usage Guide

### 1. Initializing a Project

Nestifypy comes with a CLI to scaffold a professional-grade project structure instantly:
```bash
nestifypy init --name my_app
```

### 2. Smart Configuration & Environment

Access parsed configurations instantly across your entire project.

```python
from nestifypy import yaml
from nestifypy.env import Env

# Automatically load .env file
Env.load()
api_key = Env.required("API_KEY")

# Fetch values natively from any scanned .yml file using dot-notation
db_host = yaml.get("database.host") 
```

### 3. Building a Game (Pyunix)

Building a game loop is as simple as decorating a class. No messy `while True` loops.

```python
from nestifypy.pyunix import Game, Entity, Rigidbody, BoxCollider, BodyType
from nestifypy.types import Vector2, Color

# Define your Game using decorators
@Game(title="My Awesome Game", size=(800, 600), fps=60)
class MyGame:
    @Game.start
    def start(self):
        print("Engine Initialized!")
        self.player = Player(x=400, y=300)

    @Game.update
    def update(self, dt: float):
        # Frame-by-frame game logic here
        pass

    @Game.draw
    def draw(self, screen):
        screen.fill(Color.BLACK.to_tuple())

    @Game.text(x=10, y=10, size=24, color="white", outline=True)
    def score_ui(self):
        return "SCORE: 1000"

# Define your Entities with Physics
class Player(Entity):
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            layer="player",
            rigidbody=Rigidbody(body_type=BodyType.DYNAMIC, mass=1.0),
            collider=BoxCollider(width=32, height=32)
        )

    @Entity.update
    def movement(self, dt):
        if self.input.is_action_pressed("jump"):
            self.rigidbody.add_impulse(Vector2(0, -500))

if __name__ == "__main__":
    game = MyGame()
    game.run()
```

### 4. Metaprogramming with Komodo

Eliminate class boilerplate and enforce runtime contracts instantly.

```python
from nestifypy.komodo import komodo, contract, requires

@komodo.builder
@komodo.data
class DatabaseConfig:
    host: str
    port: int = 5432
    
@contract(requires(lambda config: config.port > 1024, "Port must be > 1024"))
def connect(config: DatabaseConfig):
    print(f"Connecting to {config.host}:{config.port}")

# Using the generated Builder
conf = DatabaseConfig.Builder().with_host("localhost").build()
connect(conf)
```

### 5. Enterprise Apps with Ignite

Build Spring Boot-style applications with Auto-Configuration and Dependency Injection.

```python
from nestifypy.ignite import Application
from nestifypy.ignite.decorators import Component, Autowired

@Component
class EmailService:
    def send(self, msg: str):
        print(f"Sending: {msg}")

@Component
class UserService:
    email_service: EmailService = Autowired()

    def register(self, user: str):
        self.email_service.send(f"Welcome {user}!")

if __name__ == "__main__":
    app = Application.run()
    app.context.get_bean(UserService).register("Alice")
```

## ✨ Features

- **Komodo Metaprogramming:** `@komodo.data`, `@komodo.builder`, `@komodo.singleton`, and `@contract` constraints for clean, boilerplate-free data structures.
- **Ignite Framework:** Spring Boot-inspired IoC container, Dependency Injection, Lifecycle hooks (`@PostConstruct`), Web integration (FastAPI), Scheduled Cron tasks (`@Scheduled`), EventBus, and TestContainers.
- **No Boilerplate Game Loops:** Build Pyunix games using `@Game`, `@Entity`, and `@Scene`.
- **Built-in 2D Physics:** High-performance Rigidbody physics, spatial hashing, `BoxCollider` / `CircleCollider`, and collision hooks.
- **Intelligent YAML Registry:** Caches and indexes YAML files for `O(1)` dot-notation access.
- **Declarative Environments:** Bind `.env` variables directly to class properties.
- **CLI Scaffolding:** Generate robust projects with built-in support for `ruff`, `pytest`, and `mypy`.

## 📝 Changelog

### v0.2.2
- **Pyunix Fixes**: Fixed physics bounding box discrepancies (`rect.topleft` vs `rect.center` alignment) ensuring pixel-perfect `BoxCollider` interactions in 2D space.
- **FlappyBird Demo**: Refactored `examples/flappybird.py` to fully utilize Pyunix's modern Physics engine, Animator, and Trigger zones. Fixed ghost pipe collider issues on reset.
- **Ignite Documentation**: Published comprehensive documentation for the Ignite framework (`ignite.md`) covering DI, FastAPI, EventBus, Scheduled Tasks, and TestContainers.

### v0.2.1
- **Ignite Core Integration**: Rebranded and refactored the legacy `bolt` container into the advanced `ignite` application framework.
- **EventBus**: Added a powerful Publish/Subscribe event bus within Ignite.
- **Web module**: Seamless integration with FastAPI for RESTful APIs.
- **Cron Jobs**: Introduced `@Scheduled` decorators utilizing `croniter`.
- **Testing**: Added `TestContainer` for robust dependency-isolated integration testing.

## 📚 Documentation

For detailed guides, please check the `docs/` directory in our GitHub repository:
- 🦎 [Komodo Metaprogramming](https://github.com/nestifypy/nestifypy/tree/main/docs/komodo.md)
- 🎮 [Pyunix Game Framework](https://github.com/nestifypy/nestifypy/tree/main/docs/pyunix.md)
- ⚙️ [YAML Intelligent Registry](https://github.com/nestifypy/nestifypy/tree/main/docs/yaml.md)
- 🔒 [Environment Management](https://github.com/nestifypy/nestifypy/tree/main/docs/env.md)
- 📁 [OS & File Utilities](https://github.com/nestifypy/nestifypy/tree/main/docs/os.md)

*(Note: Documentation links assume you are browsing on GitHub. More modules available in the repository.)*

## 🤝 Contributing

We welcome contributions! Please review our repository if you are interested in helping out.
1. Clone the repository.
2. Install development dependencies using `uv` or `pip`: `uv pip install -e ".[dev]"`
3. Run tests: `pytest`
4. Lint code: `ruff check .`

## 🛡️ Security

Please review our [Security Policy](SECURITY.md) for information on reporting vulnerabilities.

## 📜 License

This project is licensed under the [MIT License](LICENSE).
