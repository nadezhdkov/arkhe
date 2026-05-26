# YAML Intelligent Registry

`nestify.yaml` is not just a parser; it is a **Runtime Configuration Engine**. It transforms chaotic, scattered YAML files into a strongly-typed, auto-reloading, `O(1)` virtual registry.

By leveraging an intelligent caching layer, Nestify ensures that parsing YAML only happens when files actually change on disk, keeping your application blazing fast.

---

## 1. Zero-Boilerplate Access

You don't need to manually read, open, or parse `.yml` files. The engine automatically bootstraps itself the first time you request a variable, scanning the current working directory recursively for any `.yml` files.

Assuming a file `config/database.yml`:
```yaml
database:
  host: "localhost"
  port: 5432
  pool:
    min_size: 2
    max_size: 10
```

### Option A: String Path Resolution
The `yaml.get()` method uses deep dot-notation to traverse files and nested dictionaries seamlessly.
```python
from nestify import yaml

# Scans project, caches in .nestify/, and retrieves the value
host = yaml.get("database.host")
max_pool = yaml.get("database.pool.max_size")
```

### Option B: Pythonic Attribute Access (Magic Methods)
Nestify uses module-level `__getattr__` to let you interact with your configuration as if it were a Python object.
```python
from nestify import yaml

# Same as above, but with pure Python syntax!
host = yaml.database.host
max_pool = yaml.database.pool.max_size

# You can even extract a sub-dictionary as an object (DotDict)
pool_cfg = yaml.database.pool
print(pool_cfg.min_size)
```

---

## 2. The Persistence Layer (`.nestify/`)

Why is `nestify.yaml` so fast? Because it acts like a database index.

When Nestify scans your directories, it generates two files inside the hidden `.nestify/` folder:
1. `yaml_index.json`: A flat dictionary mapping every single dot-path to the absolute path of the YAML file that owns it.
2. `yaml_metadata.json`: A state-tracker recording the last modified timestamps (`st_mtime`) of every file.

**The result?** 
- Lookup times are **O(1)**.
- If you restart your application, Nestify loads the cache in milliseconds.
- If a single YAML file is modified, Nestify *only* re-parses that specific file, ignoring the rest of your project.

*(Note: You should add `.nestify/` to your `.gitignore`)*

---

## 3. Hot-Reloading Configurations (Watchers)

For long-running processes (like a web server or a game engine), restarting the app to tweak a configuration value is painful. Nestify solves this with a built-in background watcher.

```python
from nestify import yaml

# Start a lightweight background thread
yaml.watch(True)

def game_loop():
    while True:
        # If you edit 'game.yml' and change 'player.speed',
        # this value updates instantly on the next frame!
        speed = yaml.get("game.player.speed")
        player.move(speed)
```

---

## 4. Manual Lifecycle Management

While the auto-bootstrap is great for rapid development, professional applications usually require explicit initialization (e.g., during a server's boot phase).

```python
from nestify import yaml
from pathlib import Path

# Explicitly scan only a specific directory (prevents scanning node_modules or large folders)
yaml.scan(Path("src/config/"))

# Where did this value come from?
origin_file = yaml.where("database.host")
print(f"Value defined in: {origin_file}") # "/absolute/path/to/database.yml"
```
