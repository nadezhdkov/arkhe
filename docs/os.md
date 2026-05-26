# System Utilities (`nestify.os`)

The `nestify.os` module provides clean, cross-platform wrappers for common operating system tasks, splitting functionality into logical submodules: `Files`, `Dirs`, `Paths`, `System`, and `Process`.

## 1. Filesystem (`Files` and `Dirs`)

Perform common file manipulations safely and without boilerplate.

```python
from nestify.os import Files, Dirs

# Create a file and write content (creates parent directories automatically!)
Files.create("output/data.txt", "Hello World")

# Read content
text = Files.read("output/data.txt")

# Recursively find files using glob patterns (returns a Memory-Efficient Generator)
for py_file in Files.find("*.py", directory="src/"):
    print(py_file.name)

# Iterate over lines of a huge file without loading it all into memory
for line in Files.stream_lines("huge_dataset.csv"):
    process(line)

# Make directory trees
Dirs.create("cache/tmp/images")
```

## 2. Path Resolutions (`Paths`)

Resolve common directories easily.

```python
from nestify.os import Paths

print(Paths.cwd())    # Current working directory
print(Paths.home())   # User's home directory
```

## 3. Subprocesses (`Process`)

Run shell commands synchronously or asynchronously without messing with `subprocess` directly.

```python
from nestify.os import Process

# Run a command and capture output
result = Process.run("echo Hello Nestify")
print(result) # "Hello Nestify"

# Run a command in the background (fire and forget)
Process.spawn("python script.py")
```

## 4. System Info (`System`)

Query hardware and OS info.

```python
from nestify.os import System

print(System.os_name()) # "Linux", "Windows", "Darwin"
print(System.is_linux()) # True/False
print(System.cpu_count()) # 8
```
