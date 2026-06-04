# Collections (`arkhe.collections`)

A suite of Java-inspired, strongly-typed (via hints), fluent data structures and functional utilities for Python.

## Import

```python
from arkhe.collections import (
    ArrayList, LinkedList, Stack, Queue, OrderedSet, HashMap,
    BiMap, MultiMap, PriorityQueue, CircularBuffer,
    Stream, Optional, Result,
)
```

---

## 1. ArrayList

A dynamic array wrapper providing a fluent API, bounds-checking, and strict typing if parameterized.

```python
lista = ArrayList()
lista.add(10).add(20).add(30)
lista.remove(20)
print(lista.size())  # 2
print(lista.get(0))  # 10
```

---

## 2. LinkedList

A doubly-linked list allowing O(1) insertions and deletions at both ends.

```python
ll = LinkedList()
ll.add_first("Start")
ll.add_last("End")
ll.remove_first()
```

---

## 3. Stack (LIFO)

Standard Last-In-First-Out structure.

```python
stack = Stack()
stack.push("Scene1").push("Scene2")
top = stack.peek()    # "Scene2"
active = stack.pop()  # Removes "Scene2"
```

---

## 4. Queue (FIFO)

Standard First-In-First-Out structure built on top of `collections.deque` for performance.

```python
q = Queue()
q.enqueue("Task1").enqueue("Task2")
task = q.dequeue()  # "Task1"
```

---

## 5. OrderedSet

Maintains uniqueness like a `set`, but preserves insertion order. Essential for rendering layers or deterministic systems.

```python
oset = OrderedSet()
oset.add("A").add("B").add("A")
# Contains: ["A", "B"] in that exact order
```

---

## 6. HashMap

A fluent wrapper around the native Python dictionary.

```python
map = HashMap()
map.put("key", "value").put("hero", "Link")
if map.contains_key("hero"):
    print(map.get("hero"))
```

---

## 7. BiMap

A bidirectional map that enforces a one-to-one relationship between keys and values. Allows O(1) lookup in both directions. Inserting a duplicate value automatically removes the old key that held it.

```python
roles = BiMap()
roles.put("ADMIN", 1).put("MOD", 2)

roles.get("ADMIN")   # 1
roles.get_key(2)     # "MOD"

# Invert the entire map
inv = roles.inverse()
inv.get(1)           # "ADMIN"
```

Common use cases: ID ↔ name mappings, aliases, protocol codes, enum constants.

---

## 8. MultiMap

A map that associates each key with a list of values, rather than a single value.

```python
params = MultiMap()
params.put("color", "red").put("color", "blue").put("size", "M")

params.get("color")       # ["red", "blue"]
params.get("size")        # ["M"]
params.get("missing")     # []

params.key_count()        # 2
params.value_count()      # 3

params.remove_value("color", "red")
params.get("color")       # ["blue"]
```

Common use cases: query parameters, groupings, search indices.

---

## 9. PriorityQueue

A heap-backed queue that dequeues elements in priority order. Lower priority numbers are dequeued first by default (min-heap). Pass `reverse=True` for max-heap semantics.

```python
tasks = PriorityQueue()
tasks.add("Low priority task",  priority=10)
tasks.add("High priority task", priority=1)
tasks.add("Medium task",        priority=5)

tasks.peek()   # "High priority task"  (not removed)
tasks.poll()   # "High priority task"
tasks.poll()   # "Medium task"

# Max-heap: highest number first
pq = PriorityQueue(reverse=True)
pq.add("a", priority=3).add("b", priority=10)
pq.poll()  # "b"

# With a key function
jobs = PriorityQueue(key=lambda j: j["urgency"])
jobs.add({"name": "Deploy", "urgency": 1})
jobs.add({"name": "Docs",   "urgency": 9})
jobs.poll()  # {"name": "Deploy", "urgency": 1}
```

Common use cases: task schedulers, AI/pathfinding, event systems.

---

## 10. CircularBuffer

A fixed-capacity ring buffer. When full, adding a new element automatically evicts the oldest one, keeping memory usage constant.

```python
logs = CircularBuffer(3)
logs.add("A").add("B").add("C")
logs.to_list()     # ["A", "B", "C"]
logs.is_full()     # True

logs.add("D")
logs.to_list()     # ["B", "C", "D"]  — "A" was evicted

logs.peek_oldest() # "B"
logs.peek_newest() # "D"
logs.capacity      # 3
```

Common use cases: rolling logs, metrics windows, telemetry, signal processing.

---

## Stream

A lazy sequential pipeline for functional-style data processing, modelled after Java Streams.

Intermediate operations (like `map` and `filter`) are lazy and return a new Stream. Terminal operations (like `to_list` and `reduce`) trigger evaluation. A Stream may only be consumed once.

```python
result = (
    Stream.range(1, 11)
    .filter(lambda n: n % 2 == 0)
    .map(lambda n: n ** 2)
    .take(3)
    .to_list()
)  # [4, 16, 36]
```

### Factories

```python
Stream.of(1, 2, 3)
Stream.from_iterable(my_list)
Stream.range(1, 10)
Stream.iterate(0, lambda n: n + 1)  # infinite
Stream.empty()
```

### Intermediate operations

| Method | Description |
|---|---|
| `map(fn)` | Transform each element |
| `filter(fn)` | Keep elements matching predicate |
| `flat_map(fn)` | Map then flatten one level |
| `flatten()` | Flatten one level |
| `take(n)` | First n elements |
| `drop(n)` | Skip first n elements |
| `take_while(fn)` | Take while predicate holds |
| `drop_while(fn)` | Drop while predicate holds |
| `distinct()` | Remove duplicates (hashable elements) |
| `distinct_by(fn)` | Remove duplicates by custom key |
| `sorted(key, reverse)` | Sort (materializes stream) |
| `peek(fn)` | Side-effect per element, pass through |
| `zip_with(other)` | Pair with another iterable |
| `enumerate(start)` | Pair each element with its index |
| `chunk(size)` | Split into fixed-size lists |
| `window(size)` | Sliding windows of consecutive elements |
| `pairwise()` | Consecutive overlapping pairs |
| `map_not_none(fn)` | Map and discard None results |
| `filter_is_instance(type)` | Keep only elements of given type |

### Terminal operations

| Method | Description |
|---|---|
| `to_list()` | Collect into a list |
| `to_set()` | Collect into a set |
| `to_dict(key_fn, value_fn)` | Collect into a dict |
| `associate_by(key_fn)` | Collect into a `HashMap` keyed by extracted key |
| `associate(key, value)` | Collect into a `HashMap` with custom key and value |
| `group_by(fn)` | Group into a `dict` of lists |
| `partition(fn)` | Split into (matching, non-matching) lists |
| `reduce(fn, initial)` | Fold left |
| `count()` | Number of elements |
| `sum()` | Sum of elements |
| `min(key)` | Minimum element |
| `max(key)` | Maximum element |
| `first()` | First element as `Optional` |
| `last()` | Last element as `Optional` |
| `find_first(fn)` | First matching element as `Optional` |
| `any_match(fn)` | True if any element matches |
| `all_match(fn)` | True if all elements match |
| `none_match(fn)` | True if no element matches |
| `for_each(fn)` | Execute action for each element |

### Examples

```python
# distinct_by — deduplication on complex objects
Stream.of(users).distinct_by(lambda u: u.id).to_list()

# window — sliding windows for time-series
Stream.range(1, 6).window(3).to_list()
# [[1, 2, 3], [2, 3, 4], [3, 4, 5]]

# pairwise — consecutive pairs
Stream.of(1, 2, 3, 4).pairwise().to_list()
# [(1, 2), (2, 3), (3, 4)]

# map_not_none — safe parsing
def parse_int(s):
    try: return int(s)
    except ValueError: return None

Stream.of("1", "2", "x", "3").map_not_none(parse_int).to_list()
# [1, 2, 3]

# filter_is_instance — type narrowing
Stream.of(1, "hello", 2, "world").filter_is_instance(str).to_list()
# ["hello", "world"]

# associate_by — list to map
Stream.of(users).associate_by(lambda u: u.id)
# HashMap({1: user1, 2: user2})

# associate — custom key and value
Stream.of(users).associate(key=lambda u: u.id, value=lambda u: u.name)
# HashMap({1: "Alice", 2: "Bob"})
```

---

## Optional

A type-safe container for an optional value. Eliminates `if value is not None` guards throughout application code.

```python
result = (
    Optional.of_nullable(user_input)
    .map(str.strip)
    .filter(bool)
    .map(int)
    .get_or(0)
)
```

| Factory | Description |
|---|---|
| `Optional.of(value)` | Present; raises if None |
| `Optional.of_nullable(value)` | Present or empty depending on value |
| `Optional.empty()` | Explicitly empty |

---

## Result

A discriminated union for explicit error handling, inspired by Rust's `Result<T, E>`. Functions return either `Ok(value)` or `Err(error)`, making error paths visible without relying on exceptions for control flow.

```python
def parse_int(s: str) -> Result:
    try:
        return Result.ok(int(s))
    except ValueError as e:
        return Result.err(str(e))

value = parse_int("42").map(lambda n: n * 2).get_or(0)  # 84

parse_int("bad").map_err(str.upper).get_or_else(lambda e: f"Error: {e}")
```

| Factory | Description |
|---|---|
| `Result.ok(value)` | Successful result |
| `Result.err(error)` | Failed result |
| `Result.of(fn, catch)` | Run a callable; catch exceptions as Err |
