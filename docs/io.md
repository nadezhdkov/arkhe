# arkhe.io

> Beautiful terminal experiences for Python.

`arkhe.io` transforms ordinary terminal applications into visually rich, self-diagnosing environments — without requiring you to change a single line of existing code.

---

## Philosophy

Most terminal libraries force you to learn a new API:

```python
console.print("[red]Error[/red]")
logger.info("Server started")
pretty.pprint(config)
```

Arkhe takes a different approach. The goal is not to replace Python's standard I/O, but to enhance it transparently.

```python
from arkhe.io import install

install()

print("Server started")  # just works
```

After `install()`, Arkhe automatically intercepts and beautifies `print()`, `input()`, exceptions, and tracebacks — without any migration required.

---

## Installation

```python
from arkhe.io import install

install()
```

This single call installs:

- stdout renderer (print hook)
- input renderer (input hook)
- traceback beautifier (excepthook)
- object formatter
- color tag parser

To restore Python's original behavior:

```python
from arkhe.io import uninstall

uninstall()
```

---

## Output Modes

Arkhe automatically selects the most appropriate layout depending on the value being printed.

---

### Inline Log

For plain strings — the default mode. Adds a timestamp, level icon, and separator.

```python
print("Engine initialized")
print("Loading internal modules...")
```

```
[ 15:42:01 ] ✦ INFO    │ Engine initialized
[ 15:42:02 ] ✦ INFO    │ Loading internal modules...
```

---

### Success Panel

```python
from arkhe.io import success

print(success("User created successfully"))
```

```
╭─[ ✓ Success ]──────────────────────────────────────────╮
│                                                        │
│ User created successfully                              │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

---

### Warning Panel

```python
from arkhe.io import warning

print(warning("Response time exceeded 120ms"))
```

```
╭─[ ⚠ Warning ]──────────────────────────────────────────╮
│                                                        │
│ Response time exceeded 120ms                           │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

---

### Error Panel

```python
from arkhe.io import error

print(error("Connection refused by remote host at 192.168.1.100:5432"))
```

```
╭─[ ✖ Error ]────────────────────────────────────────────╮
│                                                        │
│ Connection refused by remote host at 192.168.1.100:5432│
│                                                        │
╰────────────────────────────────────────────────────────╯
```

---

### Info Panel

```python
from arkhe.io import info

print(info("Scheduled maintenance starts in 15 minutes"))
```

```
╭─[ ✦ Info ]─────────────────────────────────────────────╮
│                                                        │
│ Scheduled maintenance starts in 15 minutes             │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

---

## Object Rendering

Arkhe automatically detects Python objects and renders their attributes in a structured panel.

```python
class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age  = age

user = User("Samuel", 15)

print(user)
```

```
╭─[ User ]───────────────────────────────────────────────╮
│                                                        │
│ name  = "Samuel"                                       │
│ age   = 15                                             │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

Private attributes (prefixed with `_`) are hidden automatically.

---

## Dictionary Rendering

```python
config = {
    "port": 25565,
    "debug": True,
    "host": "localhost",
    "modules": ["auth_core", "database_pool"],
    "timeout": None,
}

print(config)
```

```
╭─[ Dictionary ]─────────────────────────────────────────╮
│                                                        │
│ {                                                      │
│    "port": 25565,                                      │
│    "debug": true,                                      │
│    "host": "localhost",                                │
│    "modules": [                                        │
│       "auth_core",                                     │
│       "database_pool"                                  │
│    ],                                                  │
│    "timeout": null                                     │
│ }                                                      │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

**Color rules:**

| Type     | Color   |
|----------|---------|
| Keys     | Cyan    |
| Strings  | Green   |
| Numbers  | Yellow  |
| Booleans | Magenta |
| None     | Gray    |

---

## Color Tags

Arkhe supports lightweight inline color tags inside any string passed to `print()`.

```python
print("{green}Connected{/} to {cyan}arkhe-db-01{/}")
print("{red}CRITICAL{/}: {yellow}disk usage above 90%{/}")
```

**Available tags:**

| Tag         | Effect        |
|-------------|---------------|
| `{red}`     | Bright red    |
| `{green}`   | Bright green  |
| `{yellow}`  | Yellow        |
| `{blue}`    | Blue          |
| `{cyan}`    | Cyan          |
| `{magenta}` | Magenta       |
| `{white}`   | Bright white  |
| `{gray}`    | Dim gray      |
| `{bold}`    | Bold          |
| `{dim}`     | Dimmed        |
| `{/}`       | Reset         |

Tags can be nested freely.

---

## Log Separator

Insert a visual divider between execution cycles or log sections.

```python
from arkhe.io.renderer import log_separator

print("Boot sequence complete")
print(log_separator())
print("Starting main loop")
```

```
[ 15:42:05 ] ✦ INFO    │ Boot sequence complete
──────────────────────────────────────────────────────────
[ 15:42:05 ] ✦ INFO    │ Starting main loop
```

---

## Automatic Traceback Beautifier

Arkhe replaces Python's default traceback renderer with a structured, readable panel that shows the exact error location, surrounding source code, and local variable values at the point of failure.

```python
def connect(host_ip):
    db_timeout = 30
    result = int(host_ip)  # raises TypeError

connect(None)
```

Instead of the standard wall of text, Arkhe renders:

```
╭─[ ✖ TypeError ]────────────────────────────────────────╮
│                                                        │
│ int() argument must be a string, a bytes-like object   │
│ or a real number, not 'NoneType'                       │
│                                                        │
╰────────────────────────────────────────────────────────╯

╭─[ Stack Frame ]────────────────────────────────────────╮
│ 📁 demo.py:91  in <module>                             │
│                                                        │
│       88 │ db_timeout = 30                             │
│       89 │ result = int(host_ip)                       │
│       90 │                                             │
│  ❯   91 │ connect(None)                               │
╰────────────────────────────────────────────────────────╯

╭─[ Stack Frame ]────────────────────────────────────────╮
│ 📁 demo.py:89  in connect                              │
│                                                        │
│       87 │ def connect(host_ip):                       │
│       88 │     db_timeout = 30                         │
│  ❯   89 │     result = int(host_ip)                   │
│       90 │                                             │
│                                                        │
│ ↳ Local variables                                      │
│    host_ip    = null                                   │
│    db_timeout = 30                                     │
╰────────────────────────────────────────────────────────╯
```

Each stack frame is shown separately. The innermost frame includes all local variables captured at the moment of the crash.

`KeyboardInterrupt` is passed through to Python's default handler and not intercepted.

---

## inspect()

Inspect any Python class or instance to see its structure.

```python
from arkhe.io import inspect_obj

inspect_obj(User)
```

```
╭─[ User ]───────────────────────────────────────────────╮
│ Class Definition                                       │
│                                                        │
├─ Attributes ───────────────────────────────────────────┤
│  name  :  str                                          │
│  age   :  int                                          │
│                                                        │
├─ Methods ──────────────────────────────────────────────┤
│  login(self)                                           │
│  logout(self)                                          │
│  save(self)                                            │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

Passing an **instance** instead of the class shows live attribute values alongside their types.

```python
inspect_obj(user)
```

```
╭─[ User ]───────────────────────────────────────────────╮
│ Instance                                               │
│                                                        │
├─ Attributes ───────────────────────────────────────────┤
│  name  :  str  =  'Samuel'                             │
│  age   :  int  =  15                                   │
│                                                        │
├─ Methods ──────────────────────────────────────────────┤
│  login(self)                                           │
│  logout(self)                                          │
│  save(self)                                            │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

> `inspect_obj` is exported as `inspect` in the module — rename on import to avoid shadowing Python's built-in `inspect` module.

---

## watch()

Observe an object's attributes in real time. The panel redraws in-place whenever a value changes.

```python
from arkhe.io import watch

watch(player)
```

```
╭─[ Player ]─────────────────────────────────────────────╮
│                                                        │
│ health  =  20                                          │
│ coins   =  150                                         │
│ level   =  12                                          │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

The panel refreshes every 0.5 seconds by default. Press `Ctrl-C` to stop watching.

**Parameters:**

| Parameter  | Type    | Default | Description                              |
|------------|---------|---------|------------------------------------------|
| `obj`      | `Any`   | —       | The object to observe                    |
| `interval` | `float` | `0.5`   | Refresh rate in seconds                  |
| `times`    | `int`   | `None`  | Stop after N refresh cycles (None = ∞)   |

```python
watch(player, interval=1.0)       # slower refresh
watch(player, times=20)           # run exactly 20 cycles
```

---

## Themes

Arkhe ships with six built-in themes.

```python
from arkhe.io import theme

theme("dracula")
theme("nord")
theme("catppuccin")
theme("gruvbox")
theme("github")
theme("default")
```

Themes affect all panels, log lines, color tags, and traceback output. Switching themes mid-execution takes effect immediately on the next print call.

**Available themes:**

| Name         | Character                         |
|--------------|-----------------------------------|
| `default`    | Dark neutral — cyan, gray, white  |
| `dracula`    | Purple tones with vivid accents   |
| `nord`       | Cool arctic blues and greens      |
| `catppuccin` | Soft pastels — lavender and peach |
| `gruvbox`    | Warm retro — amber and olive      |
| `github`     | Clean light-style palette         |

---

## API Reference

### `install()`

Installs Arkhe's I/O hooks. Must be called before any output is rendered.

```python
from arkhe.io import install
install()
```

Idempotent — calling it multiple times has no effect.

---

### `uninstall()`

Restores Python's original `print`, `input`, and `sys.excepthook`.

```python
from arkhe.io import uninstall
uninstall()
```

---

### `success(message) / warning(message) / error(message) / info(message)`

Wrap a string in a typed message sentinel. Pass the result to `print()` to render the corresponding panel.

```python
print(success("Deployment complete"))
print(warning("Memory usage high"))
print(error("Service unreachable"))
print(info("Version 2.1.0 available"))
```

These functions return an `_ArkheMessage` object — they do not print on their own.

---

### `inspect_obj(obj)`

Render a structured panel showing the class definition, attributes, and methods of any object or class.

```python
from arkhe.io import inspect_obj

inspect_obj(MyClass)
inspect_obj(my_instance)
```

---

### `watch(obj, interval=0.5, times=None)`

Observe an object in real time, refreshing the panel in-place on every change.

```python
from arkhe.io import watch

watch(game_state, interval=0.25)
```

---

### `theme(name)`

Switch the active color theme.

```python
from arkhe.io import theme

theme("nord")
```

Raises `ValueError` if the theme name is not recognized.

---

### `log_separator(width=None)`

Returns a full-width horizontal rule string for use as a section divider in log output.

```python
from arkhe.io.renderer import log_separator

print(log_separator())
print(log_separator(width=40))
```

---

## Internal Architecture

```
arkhe/io/
├── __init__.py     Public API surface
├── core.py         install() / uninstall() — print, input, excepthook hooks
├── renderer.py     Layout engine — Panel, log formatter, JSON colorizer
├── theme.py        Theme registry and active theme state
├── helpers.py      _ArkheMessage sentinel type and factory functions
├── inspect.py      inspect() implementation
└── watch.py        watch() implementation — in-place terminal refresh
```

`install()` is the only entry point that mutates global state (`builtins.print`, `builtins.input`, `sys.excepthook`). Everything else is pure output logic.

---

## Design Principles

**Native First** — existing `print()` calls continue working with no changes.

**Visual Clarity** — colors, alignment, and icons are chosen to guide the eye, not decorate.

**Beautiful Defaults** — applications look professional without any configuration.

**Zero Boilerplate** — no `Console.print()`, no `Logger.info()`, no `PrettyPrinter.render()`.

---

## Roadmap

- Progress bars
- Live dashboards
- Interactive prompts
- Syntax-highlighted code blocks
- Async live views
- Remote log streaming
- Multi-terminal synchronization
