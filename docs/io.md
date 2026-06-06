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

## Template Engine — ATEL

`arkhe.io` ships with a built-in template engine called ATEL (Arkhe Template Expression Language). It powers `printf()` and can be used standalone anywhere dynamic string rendering is needed.

ATEL is reflection-based, dependency-free, and safe by default — no `eval()` or `exec()` is ever called.

```python
from arkhe.io import printf

printf("{name:title} has {coins:number} coins.", player)
# → Samuel has 15,000 coins.
```

---

### printf()

Renders an ATEL template against a context object and prints the result. Multi-line templates are dedented automatically.

```python
from arkhe.io import printf

printf("""
    {online?🟢 Online:🔴 Offline}

    User   : {name:title}
    Rank   : {rank -> ADMIN:'👑 Admin', MOD:'🛡 Moderator', *:'👤 User'}
    Coins  : {coins:number}
    Phone  : {phone:mask((##) #####-####)}
    Status : {!banned?Allowed:Blocked}
    City   : {address.city}
    Nick   : {nickname ?? username ?? guest}
""", player)
```

```
🟢 Online

User   : Samuel
Rank   : 👑 Admin
Coins  : 15,000
Phone  : (88) 99999-9999
Status : Allowed
City   : Quixadá
Nick   : samueldev
```

---

### Expression Syntax

Every expression lives between `{` and `}`. The engine resolves expressions in this priority order:

```
{ expr -> match_spec }          match expression      (highest)
{ expr ?? fallback ?? literal } fallback chain
{ condition ? true : false }    conditional
{ expr : transformer|chain }    transformer           (lowest)
```

---

### Attribute Resolution

```python
"{name}"                # direct attribute
"{address.city}"        # dotted path — nested objects
"{display_name()}"      # no-arg method call
"{}"   "{0}"   "{1}"    # positional arguments
```

---

### System Tokens

Available in any template without a context object.

| Token       | Value                        |
|-------------|------------------------------|
| `{date}`    | Current date — `YYYY-MM-DD`  |
| `{time}`    | Current time — `HH:MM:SS`    |
| `{now}`     | Current datetime             |
| `{uuid}`    | Random UUID v4               |
| `{hostname}`| Machine hostname             |
| `{user}`    | Current OS user              |
| `{os}`      | Operating system name        |
| `{python}`  | Python version string        |

```python
printf("Deployed at {now} on {hostname} running Python {python}")
# → Deployed at 2024-06-05 15:42:01 on arkhe-server running Python 3.12.3
```

---

### Fallback Operator `??`

Returns the first non-null, non-empty value in the chain. The last segment is always treated as a literal string fallback.

```python
"{nickname ?? Anonymous}"              # None → Anonymous
"{nickname ?? username ?? guest}"      # chain — tries each in order
```

---

### Conditional Expressions

```python
"{online?Online:Offline}"             # boolean presence
"{coins > 1000?Rich:Poor}"            # greater than
"{rank == 'ADMIN'?Admin:Player}"      # equality
"{rank != 'MOD'?Player:Moderator}"    # not equal
"{level >= 50?Veteran:Beginner}"      # greater than or equal
"{ping < 100?Stable:Unstable}"        # less than
"{!banned?Allowed:Blocked}"           # NOT
```

**Compound conditions:**

```python
"{online && vip?VIP Online:Offline}"
"{admin || moderator?Staff:Player}"
"{online && (vip || coins > 10000)?Premium:Normal}"
```

---

### Match Expression

Inline switch-like branching. `*` is the catch-all default.

```python
"{rank -> ADMIN:'👑 Admin', MOD:'🛡 Moderator', *:'👤 User'}"
```

---

### Transformers

Applied after resolution with `:`. Chain multiple with `|`.

```python
"{name:upper}"              # SAMUEL
"{name:trim|capitalize}"    # chained — trim first, then capitalize
"{price:decimal(2)}"        # with argument
```

**String:**

| Transformer       | Example input | Result          |
|-------------------|---------------|-----------------|
| `upper`           | `hello`       | `HELLO`         |
| `lower`           | `HELLO`       | `hello`         |
| `capitalize`      | `hello world` | `Hello world`   |
| `title`           | `hello world` | `Hello World`   |
| `reverse`         | `hello`       | `olleh`         |
| `trim`            | `  hi  `      | `hi`            |
| `length`          | `hello`       | `5`             |
| `repeat(3)`       | `ab`          | `ababab`        |
| `substring(0,3)`  | `Samuel`      | `Sam`           |
| `pad_left(10)`    | `hi`          | `        hi`    |
| `pad_right(10)`   | `hi`          | `hi        `    |
| `center(10)`      | `hi`          | `    hi    `    |

**Case converters:**

| Transformer     | Input           | Result          |
|-----------------|-----------------|-----------------|
| `camel_case`    | `hello_world`   | `helloWorld`    |
| `pascal_case`   | `hello_world`   | `HelloWorld`    |
| `snake_case`    | `HelloWorld`    | `hello_world`   |
| `kebab_case`    | `HelloWorld`    | `hello-world`   |
| `constant_case` | `HelloWorld`    | `HELLO_WORLD`   |

**Normalization & filters:**

| Transformer | Result                                    |
|-------------|-------------------------------------------|
| `normalize` | Removes accents — `João` → `Joao`        |
| `digits`    | Keeps only digits — `+55 (88) 9` → `558` |
| `letters`   | Keeps only letters — `abc123` → `abc`    |

**Numeric:**

| Transformer   | Input   | Result    |
|---------------|---------|-----------|
| `number`      | `15000` | `15,000`  |
| `decimal(2)`  | `10.5`  | `10.50`   |
| `percent`     | `0.75`  | `75%`     |
| `currency`    | `10.5`  | `$10.50`  |

**Date:**

| Transformer         | Result                   |
|---------------------|--------------------------|
| `date`              | `2024-06-05`             |
| `time`              | `15:42:01`               |
| `datetime`          | `2024-06-05 15:42:01`    |
| `date(%d/%m/%Y)`    | `05/06/2024`             |

**Mask:**

```python
"{cpf:mask(###.###.###-##)}"       # 123.456.789-01
"{phone:mask((##) #####-####)}"    # (88) 99999-9999
```

**Collection:**

| Transformer  | Description                          |
|--------------|--------------------------------------|
| `size`       | Number of elements                   |
| `empty`      | `"true"` or `"false"`                |
| `first`      | First element                        |
| `last`       | Last element                         |
| `join(', ')` | Join with separator                  |

---

### Using render() directly

`printf()` is a convenience wrapper. The engine is available standalone:

```python
from arkhe.io.template import render

result = render("{name:title} has {coins:number} coins.", player)
# → "Samuel has 15,000 coins."
```

---

### Advanced imports

The template subpackage exposes its full internal API for building on top of ATEL:

```python
from arkhe.io.template import (
    render,                # main entry point
    evaluate_condition,    # parse and evaluate a condition string
    evaluate_match,        # evaluate a match spec against a value
    apply_transformer,     # apply a single transformer
    apply_chain,           # apply a pipe-separated transformer chain
    resolve,               # resolve an expression (raises on failure)
    resolve_safe,          # resolve an expression (returns default)
    resolve_system_token,  # resolve a system token by name
    is_system_token,       # check if a name is a system token
    tokenize_template,     # low-level: split template into segments
)
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

### `printf(template, context, *args)`

Render an ATEL template string and print the result. Multi-line templates are dedented automatically.

```python
from arkhe.io import printf

printf("{name:title} connected from {address.city}.", player)
printf("Hello {}!", "World")
printf("{rank -> ADMIN:'👑 Admin', *:'👤 User'}", player)
```

---

### `render(template, context, *args)` — `arkhe.io.template`

Render an ATEL template and return the result as a plain `str`, without printing.

```python
from arkhe.io.template import render

message = render("{name} has {coins:number} coins.", player)
```

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
├── __init__.py         Public API surface
├── core.py             install() / uninstall() — print, input, excepthook hooks
├── renderer.py         Layout engine — Panel, log formatter, JSON colorizer
├── theme.py            Theme registry and active theme state
├── helpers.py          _ArkheMessage sentinel type and factory functions
├── inspect.py          inspect() implementation
├── watch.py            watch() implementation — in-place terminal refresh
├── printf.py           printf() — ATEL-powered formatted print
└── template/
    ├── __init__.py     Public surface for the template subpackage
    ├── engine.py       render() — orchestrates all expression types
    ├── parser.py       Template tokenizer — splits text and {expr} segments
    ├── resolver.py     Attribute, path, method and positional resolution
    ├── conditions.py   Recursive descent condition parser — no eval()
    ├── matchers.py     Match expression evaluator
    ├── transformers.py 30+ value transformers with chaining support
    └── tokens.py       Built-in system tokens (date, uuid, hostname, …)
```

`install()` is the only entry point that mutates global state (`builtins.print`, `builtins.input`, `sys.excepthook`). Everything else is pure output logic. The `template/` subpackage is entirely stateless — `render()` and all helpers are safe to call from multiple threads without synchronization.

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
