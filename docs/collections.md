# Collections (`nestify.collections`)

A suite of Java-inspired, strongly-typed (via hints), fluent data structures optimized for game development and specific architectural patterns.

## Import
```python
from nestify.collections import ArrayList, LinkedList, Stack, Queue, OrderedSet, HashMap
```

## 1. ArrayList
A dynamic array wrapper providing a fluent API, bounds-checking, and strict typing if parameterized.

```python
lista = ArrayList()
lista.add(10).add(20).add(30)
lista.remove(20)

print(lista.size()) # 2
print(lista.get(0)) # 10
```

## 2. LinkedList
A standard doubly-linked list allowing `O(1)` insertions and deletions at both ends.

```python
ll = LinkedList()
ll.add_first("Start")
ll.add_last("End")
ll.remove_first()
```

## 3. Stack (LIFO)
Standard Last-In-First-Out structure.

```python
stack = Stack()
stack.push("Scene1").push("Scene2")

top = stack.peek() # "Scene2"
active = stack.pop() # Removes "Scene2"
```

## 4. Queue (FIFO)
Standard First-In-First-Out structure built on top of `collections.deque` for performance.

```python
q = Queue()
q.enqueue("Task1").enqueue("Task2")
task = q.dequeue() # "Task1"
```

## 5. OrderedSet
Maintains uniqueness like a `set`, but preserves insertion order. Essential for rendering layers or deterministic systems.

```python
oset = OrderedSet()
oset.add("A").add("B").add("A")
# Contains: ["A", "B"] in that exact order
```

## 6. HashMap
A fluent wrapper around the native Python dictionary.

```python
map = HashMap()
map.put("key", "value").put("hero", "Link")

if map.contains_key("hero"):
    print(map.get("hero"))
```
