<div align="center">
  <h1>🪺 Nestify Framework</h1>
  <p><strong>A Modern, Declarative Utility and Game Framework for Python 3.10+</strong></p>

  <p>
    <a href="https://github.com/nestify/nestify/actions"><img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build Status"></a>
    <a href="https://pypi.org/project/nestify/"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python Version"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
    <a href="SECURITY.md"><img src="https://img.shields.io/badge/security-policy-lightgrey?style=flat-square" alt="Security"></a>
  </p>
</div>

---

**Nestify** is a production-ready, modular utility and game framework for Python. It provides a highly declarative, decorator-driven approach to application development, focusing on performance, developer ergonomics, and strict type safety.

Whether you are building complex CLI tools, managing intelligent configuration registries, or developing 2D physics-based games, Nestify provides a robust foundation.

## 🚀 Key Features

### 🎮 Pyunix Game Engine (`nestify.pyunix`)
A fully declarative, decorator-driven engine built on top of `pygame`. 
- **No Boilerplate:** Build games using `@Game`, `@Sprite`, and `@Scene` without writing messy `while True` game loops.
- **ECS-Friendly Architecture:** Build isolated entities and manage them easily via `SpriteGroup`.
- **Built-in 2D Physics:** High-performance Rigidbody physics with spatial hashing, `BoxCollider` / `CircleCollider`, and collision event hooks (`@Sprite.on_collision_enter`).
- **Declarative UI & Fonts:** Advanced text rendering system with outlines, shadows, anchors, and caching via the `@Game.text` decorator.
- **Advanced Systems:** Built-in `Camera` with smooth-follow and screenshake, flexible `Audio` management, and robust `Timer` logic tied to game Delta-Time.

### 🛠️ Core Utilities
- **Intelligent YAML Registry (`nestify.yaml`)**: An advanced configuration engine that automatically scans, caches, and indexes your YAML files, providing instant `O(1)` access via dot-notation (e.g., `yaml.get("server.port")`).
- **Declarative Environments (`nestify.env`)**: Bind `.env` variables directly to class properties using the `EnvProperty` descriptor, or inject them into functions using `@Env.inject`.
- **System Tools (`nestify.os`)**: Cross-platform, memory-efficient generators for file scanning, subprocess management, and directory operations.
- **CLI Ecosystem (`nestify cli`)**: Scaffolding tools to generate professional-grade projects instantly with built-in support for `ruff`, `pytest`, and `mypy`.

---

## 📦 Installation

Nestify requires **Python 3.10 or higher**.

To install the core utility framework (without Pygame dependencies):
```bash
pip install nestify
```

To install Nestify with **full Pyunix Game Framework** capabilities:
```bash
pip install "nestify[game]"
```

---

## ⚡ Quick Start

### 1. Initialize a Project
Use the CLI to scaffold a new project complete with a professional `pyproject.toml` and directory structure.
```bash
nestify init --name my_app
```

### 2. Building a Game (Pyunix)
Building a game loop is as simple as decorating a class. 

```python
from nestify.pyunix import Game, Entity, Rigidbody, BoxCollider, BodyType
from nestify.types import Vector2, Color

# 1. Define your Game
@Game(title="My Awesome Game", size=(800, 600), fps=60)
class MyGame:
    @Game.start
    def start(self):
        print("Engine Initialized!")
        self.player = Player(x=400, y=300)

    @Game.update
    def update(self, dt: float):
        # Game logic here
        pass

    @Game.draw
    def draw(self, screen):
        screen.fill(Color.BLACK.to_tuple())

    @Game.text(x=10, y=10, size=24, color="white", outline=True)
    def score_ui(self):
        return f"SCORE: 1000"

# 2. Define your Entities with Physics
class Player(Entity):
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            layer="player",
            rigidbody=Rigidbody(body_type=BodyType.DYNAMIC, mass=1.0),
            collider=BoxCollider(width=32, height=32)
        )

    @Sprite.update
    def movement(self, dt):
        if self.input.is_action_pressed("jump"):
            self.rigidbody.add_impulse(Vector2(0, -500))

# 3. Run!
if __name__ == "__main__":
    game = MyGame()
    game.run()
```

### 3. Smart Configuration & Env
Access parsed configurations instantly across your entire project.

```python
from nestify import yaml
from nestify.env import Env

# Automatically loads .env file
Env.load()
api_key = Env.required("API_KEY")

# Fetches value from any scanned .yml file in the project natively
db_host = yaml.get("database.host") 
```

---

## 📚 Documentation

Detailed guides and API references for each module can be found in the `docs/` directory:

- 🎮 **[Pyunix Game Framework](docs/pyunix.md)** (Includes Physics & UI guides)
- ⚙️ **[YAML Intelligent Registry](docs/yaml.md)**
- 🔒 **[Environment Management](docs/env.md)**
- 📁 **[OS & File Utilities](docs/os.md)**
- 📝 **[JSON Tools](docs/json.md)**
- 🖥️ **[Console Tools](docs/console.md)**
- 🧱 **[Core Systems (Logger/Plugins)](docs/core.md)**
- ✨ **[Decorators](docs/decorators.md)**
- ⏱️ **[Control Flow](docs/flow.md)**
- 🗃️ **[Collections](docs/collections.md)**

---

## 🤝 Contributing

Nestify is built with modern Python tools (`uv`, `ruff`, `pytest`). We welcome contributions!

1. Clone the repository.
2. Install development dependencies using `uv` or `pip`:
   ```bash
   uv pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   pytest
   ```
4. Lint code:
   ```bash
   ruff check .
   ```

---

## 🛡️ Security

Please review our [Security Policy](SECURITY.md) for information on reporting vulnerabilities.

## 📜 License

This project is licensed under the [MIT License](LICENSE).
