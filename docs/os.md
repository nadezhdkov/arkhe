# `arkhe.os` — OS & Filesystem Utilities

A complete, cross-platform abstraction over Python's `pathlib`, `shutil`, `subprocess`, `os`, and `platform` modules. Every operation lives in a focused sub-module; the most common ones are also re-exported at package level for convenience.

> **Zero third-party dependencies** — stdlib only.

---

## Table of Contents

- [Installation & Import](#installation--import)
- [Package Layout](#package-layout)
- [Flat API (Quick Access)](#flat-api-quick-access)
- [`Files` — File I/O](#files--file-io)
  - [Create & Delete](#create--delete)
  - [Copy, Move & Rename](#copy-move--rename)
  - [Read & Write Text](#read--write-text)
  - [Read & Write Bytes](#read--write-bytes)
  - [Structured Formats](#structured-formats)
  - [Metadata & Inspection](#metadata--inspection)
  - [Permissions](#permissions)
  - [Search](#search)
  - [Archives](#archives)
  - [Context Managers](#context-managers-files)
  - [OS Integration](#os-integration)
- [`Dirs` — Directory Operations](#dirs--directory-operations)
  - [Create & Delete](#create--delete-1)
  - [Copy, Move & Rename](#copy-move--rename-1)
  - [Listing](#listing)
  - [Recursive Walk & Search](#recursive-walk--search)
  - [Metadata](#metadata)
  - [Visualisation](#visualisation)
  - [Context Managers](#context-managers-dirs)
- [`Paths` — Pure Path Manipulation](#paths--pure-path-manipulation)
  - [Construction & Joining](#construction--joining)
  - [Navigation](#navigation)
  - [Predicates](#predicates)
  - [Name & Extension](#name--extension)
  - [Relative & Absolute](#relative--absolute)
  - [URI & String Helpers](#uri--string-helpers)
  - [Temp Helpers](#temp-helpers)
- [`Process` — Subprocess Utilities](#process--subprocess-utilities)
  - [Core Execution](#core-execution)
  - [Streaming](#streaming)
  - [Piping](#piping)
  - [Executable Discovery](#executable-discovery)
  - [Context Managers](#context-managers-process)
  - [`ProcessResult`](#processresult)
- [`System` — System Information](#system--system-information)
  - [OS & Platform](#os--platform)
  - [Python Runtime](#python-runtime)
  - [CPU](#cpu)
  - [Memory](#memory)
  - [Disk](#disk)
  - [Uptime](#uptime)
  - [Environment](#environment)
  - [Summary](#summary)
  - [Dataclasses](#dataclasses)
- [Design Rules](#design-rules)

---

## Installation & Import

```python
# Full sub-module style
from arkhe.os import Files, Dirs, Paths, Process, System

# Namespaced (recommended for scripts)
from arkhe import os as nos
nos.files.read("config.json")
nos.dirs.tree("src/")

# Flat imports for the most common operations
from arkhe.os import read, write, run, tree, make_dir
```

---

## Package Layout

```
arkhe/os/
├── __init__.py   ← flat aliases + re-exports
├── files.py      ← Files   (36 methods)
├── dirs.py       ← Dirs    (22 methods)
├── paths.py      ← Paths   (20 methods, pure — no I/O)
├── process.py    ← Process (10 methods) + ProcessResult
└── system.py     ← System  (20 methods) + DiskUsage, MemoryInfo
```

---

## Flat API (Quick Access)

The most common operations are available directly from `arkhe.os` so you can skip the sub-module name:

| Flat name | Maps to |
|---|---|
| `read` | `Files.read` |
| `write` | `Files.write` |
| `safe_write` | `Files.safe_write` |
| `read_json` / `write_json` | `Files.read_json` / `Files.write_json` |
| `read_csv` / `write_csv` | `Files.read_csv` / `Files.write_csv` |
| `touch` | `Files.touch` |
| `delete_file` | `Files.delete` |
| `file_exists` | `Files.exists` |
| `file_size` | `Files.size` |
| `file_hash` | `Files.hash` |
| `lines` / `stream_lines` | `Files.lines` / `Files.stream_lines` |
| `head` / `tail` | `Files.head` / `Files.tail` |
| `grep` / `find_files` | `Files.grep` / `Files.find` |
| `zip_file` / `unzip_file` | `Files.zip` / `Files.unzip` |
| `make_dir` / `ensure_dir` | `Dirs.create` |
| `delete_dir` | `Dirs.delete` |
| `list_dir` / `list_files` / `list_dirs` | `Dirs.list` / `Dirs.list_files` / `Dirs.list_dirs` |
| `walk` | `Dirs.walk` |
| `tree` | `Dirs.tree` |
| `dir_exists` / `dir_size` | `Dirs.exists` / `Dirs.size` |
| `join` / `resolve` / `expand` | `Paths.join` / `Paths.resolve` / `Paths.expand` |
| `home` / `cwd` | `Paths.home` / `Paths.cwd` |
| `run` / `output` / `stream` / `pipe` | `Process.run` / … |
| `which` / `is_installed` | `Process.which` / `Process.is_installed` |
| `cpu_count` / `memory` / `disk_usage` | `System.cpu_count` / … |
| `info` | `System.info` |

---

## `Files` — File I/O

```python
from arkhe.os import Files
```

All methods are `@staticmethod`. Text encoding defaults to `utf-8` everywhere.

---

### Create & Delete

#### `Files.create(path, content="", encoding="utf-8") → Path`
Create a text file and all missing parent directories. Overwrites if the file already exists.

```python
Files.create("logs/app.log")
Files.create("config/settings.json", content='{"debug": true}')
```

#### `Files.touch(path) → Path`
Create an empty file if it doesn't exist; update its modification time if it does. Parent directories are created automatically.

```python
Files.touch("data/.gitkeep")
```

#### `Files.delete(path, missing_ok=True) → None`
Delete a file. Silently does nothing if the file is absent (set `missing_ok=False` to raise `FileNotFoundError` instead).

```python
Files.delete("temp/cache.bin")
Files.delete("must_exist.txt", missing_ok=False)
```

#### `Files.rename(src, new_name) → Path`
Rename a file inside its own directory. `new_name` is a bare filename, not a path.

```python
Files.rename("report_draft.docx", "report_final.docx")
```

---

### Copy, Move & Rename

#### `Files.copy(src, dst, *, overwrite=True) → Path`
Copy a file to `dst`, preserving metadata. If `dst` is a directory, the file is placed inside it. Raises `FileExistsError` when `overwrite=False` and `dst` already exists.

```python
Files.copy("src/main.py", "backup/main.py")
Files.copy("icon.png", "dist/", overwrite=False)
```

#### `Files.move(src, dst) → Path`
Move a file. `dst` may be a full path or a destination directory.

```python
Files.move("downloads/archive.zip", "projects/archive.zip")
```

---

### Read & Write Text

#### `Files.read(path, encoding="utf-8") → str`
Read the entire file and return it as a string.

```python
content = Files.read("README.md")
```

#### `Files.write(path, content, *, append=False, encoding="utf-8", newline=None) → Path`
Write (or append) text to a file. Parent directories are created automatically.

```python
Files.write("output.txt", "Hello, world!\n")
Files.write("output.txt", "Second line\n", append=True)
```

#### `Files.safe_write(path, content, encoding="utf-8") → Path`
**Atomic write.** Content is written to a sibling temp file first, then `os.replace()` swaps it in. The destination is never partially written, even if the process is interrupted.

```python
# Safe for config files and any data that must never be half-written
Files.safe_write("config/db.json", json.dumps(config))
```

#### `Files.lines(path, encoding="utf-8") → list[str]`
Return all lines as a list with newlines stripped.

```python
rows = Files.lines("data.csv")
```

#### `Files.line_count(path, encoding="utf-8") → int`
Count lines without loading the entire file into memory.

```python
n = Files.line_count("access.log")
```

#### `Files.stream_lines(path, encoding="utf-8") → Iterator[str]`
Yield lines one at a time. Efficient for large files. Newlines stripped (cross-platform safe).

```python
for line in Files.stream_lines("huge.log"):
    process(line)
```

#### `Files.head(path, n=10, encoding="utf-8") → list[str]`
Return the first `n` lines without reading the whole file.

```python
preview = Files.head("dataset.csv", n=5)
```

#### `Files.tail(path, n=10, encoding="utf-8") → list[str]`
Return the last `n` lines.

```python
recent = Files.tail("app.log", n=50)
```

---

### Read & Write Bytes

#### `Files.read_bytes(path) → bytes`
Read and return raw bytes.

```python
data = Files.read_bytes("image.png")
```

#### `Files.write_bytes(path, data) → Path`
Write raw bytes to a file. Parent directories are created automatically.

```python
Files.write_bytes("output/result.bin", bytes_data)
```

---

### Structured Formats

#### `Files.read_json(path, encoding="utf-8") → Any`
Parse and return a JSON file.

```python
config = Files.read_json("config.json")
```

#### `Files.write_json(path, data, *, indent=2, encoding="utf-8", ensure_ascii=False) → Path`
Serialise a Python object to JSON and write it to disk.

```python
Files.write_json("output/results.json", {"score": 0.98, "labels": ["a", "b"]})
```

#### `Files.read_csv(path, *, delimiter=",", has_header=True, encoding="utf-8") → list`
Parse a CSV file. With `has_header=True` (default) returns a list of `dict`; with `has_header=False` returns a list of `list[str]`.

```python
rows = Files.read_csv("users.csv")           # [{"name": "Alice", "age": "30"}, …]
rows = Files.read_csv("matrix.csv", has_header=False)  # [["1","2"], ["3","4"], …]
```

#### `Files.write_csv(path, rows, *, fieldnames=None, delimiter=",", encoding="utf-8") → Path`
Write rows to a CSV. Accepts a list of dicts (auto-header) or a list of lists (raw rows).

```python
Files.write_csv("out.csv", [{"name": "Alice", "score": 99}, {"name": "Bob", "score": 87}])
```

---

### Metadata & Inspection

#### `Files.exists(path) → bool`
Return `True` if `path` points to a regular file.

#### `Files.is_empty(path) → bool`
Return `True` if the file exists and has zero bytes.

#### `Files.is_binary(path, sample_bytes=8192) → bool`
Heuristic detection: reads up to `sample_bytes` and checks for null bytes (same approach used by Git).

```python
if Files.is_binary("upload.dat"):
    handle_binary()
```

#### `Files.size(path) → int`
Return file size in bytes.

#### `Files.size_human(path) → str`
Return a human-readable size string like `"1.4 MB"`.

```python
print(Files.size_human("video.mp4"))  # "238.5 MB"
```

#### `Files.mime_type(path) → str | None`
Return the MIME type guessed from the file extension, or `None`.

```python
Files.mime_type("photo.jpg")   # "image/jpeg"
Files.mime_type("data.csv")    # "text/csv"
```

#### `Files.last_modified(path) → datetime`
Return the last-modified time as a `datetime` object (local timezone).

#### `Files.created_at(path) → datetime`
Return the creation time. On Linux this is the metadata-change time (`st_ctime`), the closest available equivalent.

#### `Files.hash(path, algorithm="sha256") → str`
Return the hex digest. Reads in 64 KB chunks — safe for large files.

```python
Files.hash("release.tar.gz")                    # sha256 (default)
Files.hash("release.tar.gz", algorithm="md5")   # md5
```

---

### Permissions

#### `Files.chmod(path, mode) → None`
Change file permissions using an octal mode.

```python
Files.chmod("deploy.sh", 0o755)   # rwxr-xr-x
Files.chmod("secrets.env", 0o600) # rw-------
```

#### `Files.is_executable(path) → bool`
Return `True` if the current user can execute the file.

---

### Search

#### `Files.find(pattern, directory=".") → Iterator[Path]`
Yield all files matching a glob pattern recursively.

```python
for f in Files.find("*.py", "src/"):
    print(f)
```

#### `Files.grep(path, substring, *, case_sensitive=True, encoding="utf-8") → list[tuple[int, str]]`
Search for a substring in a text file. Returns a list of `(line_number, line)` tuples (1-indexed).

```python
hits = Files.grep("server.log", "ERROR")
# [(42, "2024-01-15 ERROR connection refused"), …]
```

---

### Archives

#### `Files.zip(source, destination=None) → Path`
Zip a file or an entire directory tree. If `destination` is omitted, the archive is placed next to `source` with a `.zip` extension.

```python
Files.zip("dist/")             # → dist.zip
Files.zip("dist/", "release/build.zip")
```

#### `Files.unzip(archive, destination=None) → Path`
Extract a zip archive. If `destination` is omitted, contents are extracted into a folder with the archive's stem.

```python
Files.unzip("build.zip")               # → build/
Files.unzip("build.zip", "extracted/")
```

---

### Context Managers (Files)

#### `Files.temp(suffix="", prefix="nestify_") → ContextManager[Path]`
Create a temporary file, yield its path, and delete it on exit — even if an exception is raised.

```python
with Files.temp(suffix=".json") as tmp:
    Files.write_json(tmp, {"key": "value"})
    result = process(tmp)
# file is deleted here
```

---

### OS Integration

#### `Files.open_default(path) → None`
Open a file with the default OS application (`xdg-open` on Linux, `open` on macOS, `os.startfile` on Windows).

```python
Files.open_default("report.pdf")
```

---

## `Dirs` — Directory Operations

```python
from arkhe.os import Dirs
```

---

### Create & Delete

#### `Dirs.create(path) → Path`  *(alias: `Dirs.ensure`)*
Create a directory and all missing parents. No-op if it already exists.

```python
Dirs.create("logs/2024/january")
Dirs.ensure("cache/")  # friendlier alias
```

#### `Dirs.delete(path, *, missing_ok=True) → None`
Recursively delete a directory tree. Silent if absent (set `missing_ok=False` to raise `FileNotFoundError`).

```python
Dirs.delete("build/")
Dirs.delete("must_exist/", missing_ok=False)
```

#### `Dirs.empty_out(path) → Path`
Remove all contents of a directory without deleting the directory itself.

```python
Dirs.empty_out("cache/")
```

---

### Copy, Move & Rename

#### `Dirs.copy(src, dst, *, overwrite=False) → Path`
Copy an entire directory tree. Set `overwrite=True` to remove `dst` before copying.

```python
Dirs.copy("src/", "backup/src/")
Dirs.copy("old_build/", "new_build/", overwrite=True)
```

#### `Dirs.move(src, dst) → Path`
Move a directory (cross-device safe).

```python
Dirs.move("staging/assets/", "production/assets/")
```

#### `Dirs.rename(src, new_name) → Path`
Rename a directory in-place. `new_name` is a bare name, not a full path.

```python
Dirs.rename("feature_branch/", "feature_complete/")
```

---

### Listing

#### `Dirs.list(path=".", *, pattern="*", sort_by="name", reverse=False) → list[Path]`
List immediate children (files and directories) matching `pattern`.

`sort_by` accepts `"name"` | `"size"` | `"modified"`.

```python
Dirs.list("src/")
Dirs.list("downloads/", pattern="*.zip", sort_by="modified", reverse=True)
```

#### `Dirs.list_files(path=".", *, pattern="*", sort_by="name", reverse=False) → list[Path]`
Same as `list()` but returns only files.

```python
python_files = Dirs.list_files("src/", pattern="*.py")
```

#### `Dirs.list_dirs(path=".", *, pattern="*", sort_by="name", reverse=False) → list[Path]`
Same as `list()` but returns only sub-directories.

```python
modules = Dirs.list_dirs("arkhe/")
```

---

### Recursive Walk & Search

#### `Dirs.walk(path, *, files_only=True) → Iterator[Path]`
Yield every path under `path` recursively. Set `files_only=False` to include sub-directories.

```python
for f in Dirs.walk("project/"):
    print(f)
```

#### `Dirs.find(pattern, directory=".", *, dirs_only=False) → Iterator[Path]`
Yield entries matching a glob pattern recursively. Set `dirs_only=True` to restrict to directories.

```python
list(Dirs.find("*.md", "docs/"))
list(Dirs.find("__pycache__", dirs_only=True))
```

#### `Dirs.filter(path, predicate, *, recursive=False) → list[Path]`
Return all entries for which `predicate(path)` returns `True`.

```python
# Files larger than 1 MB
large = Dirs.filter(".", lambda p: p.is_file() and p.stat().st_size > 1_000_000, recursive=True)

# Directories modified today
import time
today = Dirs.filter("logs/", lambda p: p.is_dir() and p.stat().st_mtime > time.time() - 86400)
```

---

### Metadata

#### `Dirs.exists(path) → bool`
Return `True` if `path` is an existing directory.

#### `Dirs.is_empty(path) → bool`
Return `True` if the directory has no children.

#### `Dirs.size(path) → int`
Return the total size of all files under `path` in bytes.

#### `Dirs.size_human(path) → str`
Return a human-readable total size like `"12.3 MB"`.

```python
print(Dirs.size_human("node_modules/"))  # "342.1 MB"
```

#### `Dirs.file_count(path, *, recursive=True) → int`
Count files. Set `recursive=False` to count only immediate children.

```python
Dirs.file_count("src/")           # all files recursively
Dirs.file_count("src/", recursive=False)  # only direct children
```

#### `Dirs.last_modified(path) → datetime`
Return the most recently modified timestamp across all files under `path`.

---

### Visualisation

#### `Dirs.tree(path=".", *, max_depth=None, show_hidden=False) → str`
Return a `tree(1)`-style directory listing as a printable string.

```python
print(Dirs.tree("arkhe/", max_depth=2))
```

```
arkhe/
├── os/
│   ├── __init__.py
│   ├── dirs.py
│   ├── files.py
│   ├── paths.py
│   ├── process.py
│   └── system.py
└── yaml/
    └── __init__.py
```

Parameters:

| Parameter | Default | Description |
|---|---|---|
| `max_depth` | `None` | Stop recursing beyond this depth |
| `show_hidden` | `False` | Include dotfiles and dot-directories |

---

### Context Managers (Dirs)

#### `Dirs.temp(suffix="", prefix="nestify_") → ContextManager[Path]`
Create a temporary directory, yield its `Path`, and delete it (with all contents) on exit.

```python
with Dirs.temp() as tmp:
    Files.write_json(tmp / "data.json", payload)
    result = process(tmp)
# directory is fully removed here
```

#### `Dirs.cd(path) → ContextManager[Path]`
Temporarily change the working directory. The original `cwd` is restored on exit, even if an exception is raised.

```python
with Dirs.cd("src/"):
    Process.run("python main.py")
# cwd restored
```

---

## `Paths` — Pure Path Manipulation

```python
from arkhe.os import Paths
```

`Paths` is purely computational — **no filesystem access**. Every method is a transformation on path strings, safe to call without the path actually existing.

---

### Construction & Joining

#### `Paths.join(*parts) → Path`
Join path segments. Unlike `os.path.join`, a leading `/` in a later segment does not reset the path.

```python
Paths.join("base", "sub", "file.txt")  # base/sub/file.txt
```

#### `Paths.resolve(path) → Path`
Return the absolute, symlink-resolved path. *(Does touch the filesystem to resolve symlinks.)*

#### `Paths.expand(path) → Path`
Expand `~` (home dir) and `$VAR` / `%VAR%` environment variables.

```python
Paths.expand("~/projects/$PROJECT_NAME/src")
```

#### `Paths.normalize(path) → Path`
Collapse redundant separators and `.` / `..` components.

```python
Paths.normalize("a/b/../c/./d")  # a/c/d
```

---

### Navigation

#### `Paths.home() → Path`
Return the current user's home directory.

#### `Paths.cwd() → Path`
Return the current working directory.

#### `Paths.parent(path, levels=1) → Path`
Return the parent directory, optionally `levels` steps up.

```python
Paths.parent("/a/b/c/d", levels=2)  # /a/b
```

#### `Paths.parents(path) → list[Path]`
Return every ancestor from immediate parent up to the root.

#### `Paths.parts(path) → tuple[str, ...]`
Return the path split into its individual components.

```python
Paths.parts("/usr/local/bin")  # ('/', 'usr', 'local', 'bin')
```

#### `Paths.common(paths) → Path`
Return the longest common sub-path of a sequence of paths.

```python
Paths.common(["src/a/x.py", "src/a/y.py", "src/b/z.py"])  # src
```

---

### Predicates

#### `Paths.is_absolute(path) → bool`

#### `Paths.is_relative_to(path, base) → bool`
Return `True` if `path` is relative to `base`.

```python
Paths.is_relative_to("/usr/local/bin/python", "/usr/local")  # True
```

---

### Name & Extension

#### `Paths.name(path) → str`
Final component including suffix: `"file.txt"`.

#### `Paths.stem(path) → str`
Final component without suffix: `"file"`.

#### `Paths.suffix(path) → str`
Last suffix including dot: `".txt"`.

#### `Paths.suffixes(path) → list[str]`
All suffixes: `[".tar", ".gz"]`.

#### `Paths.with_name(path, name) → Path`
Return `path` with the final component replaced by `name`.

#### `Paths.with_stem(path, stem) → Path`
Return `path` with the stem replaced, preserving the suffix.

```python
Paths.with_stem("report_draft.pdf", "report_final")  # report_final.pdf
```

#### `Paths.with_suffix(path, suffix) → Path`
Return `path` with the suffix replaced. Pass `""` to remove it entirely.

```python
Paths.with_suffix("script.py", ".txt")   # script.txt
Paths.with_suffix("archive.tar.gz", "") # archive.tar
```

---

### Relative & Absolute

#### `Paths.relative(path, base) → Path`
Return `path` relative to `base`. Raises `ValueError` if not possible.

#### `Paths.relative_cwd(path) → Path`
Return `path` relative to the current working directory.

---

### URI & String Helpers

#### `Paths.to_uri(path) → str`
Convert an absolute path to a `file://` URI.

```python
Paths.to_uri("/home/user/doc.pdf")  # "file:///home/user/doc.pdf"
```

#### `Paths.to_posix(path) → str`
Return the path as a string with forward slashes (useful on Windows).

```python
Paths.to_posix(r"C:\Users\alice\file.txt")  # "C:/Users/alice/file.txt"
```

---

### Temp Helpers

#### `Paths.temp_dir() → Path`
Return the OS temporary directory path (no creation).

#### `Paths.temp_path(suffix="", prefix="nestify_") → Path`
Return a unique temp file path without creating it. The caller is responsible for creation and cleanup.

---

## `Process` — Subprocess Utilities

```python
from arkhe.os import Process
```

---

### Core Execution

#### `Process.run(command, *, cwd=None, env=None, extra_env=None, capture=True, check=True, shell=None, timeout=None, input=None) → ProcessResult`

The primary entry point. Accepts a shell string or a list of arguments.

| Parameter | Default | Description |
|---|---|---|
| `command` | — | Shell string `"ls -la"` or arg list `["ls", "-la"]` |
| `cwd` | `None` | Working directory for the subprocess |
| `env` | `None` | Full replacement environment dict |
| `extra_env` | `None` | Merged on top of `os.environ` |
| `capture` | `True` | Capture stdout/stderr |
| `check` | `True` | Raise `CalledProcessError` on non-zero exit |
| `shell` | auto | Defaults to `True` for strings, `False` for lists |
| `timeout` | `None` | Kill and raise `TimeoutExpired` after N seconds |
| `input` | `None` | Text piped to stdin |

```python
result = Process.run("git status")
result = Process.run(["git", "commit", "-m", "feat: new feature"])
result = Process.run("make build", cwd="project/", timeout=120)
result = Process.run("cat", input="hello\nworld")
```

#### `Process.output(command, *, cwd=None, extra_env=None, timeout=None) → str`
Run a command and return stripped stdout. Raises on non-zero exit.

```python
branch = Process.output("git rev-parse --abbrev-ref HEAD")
commit = Process.output("git rev-parse HEAD")
```

#### `Process.ok(command, *, cwd=None) → bool`
Return `True` if the command exits with code 0. Never raises.

```python
if Process.ok("docker info"):
    print("Docker is running")
```

---

### Streaming

#### `Process.stream(command, *, cwd=None, extra_env=None, shell=None) → Iterator[str]`
Yield stdout lines in real time without buffering. Stderr is merged into stdout.

```python
for line in Process.stream("pip install -r requirements.txt"):
    print(f"[pip] {line}")
```

---

### Piping

#### `Process.pipe(*commands, cwd=None) → ProcessResult`
Chain multiple commands by piping stdout of each into stdin of the next. Works cross-platform without relying on shell pipe characters.

```python
result = Process.pipe("cat access.log", "grep 404", "wc -l")
print(result.stdout)  # number of 404 lines

# List args are also accepted
result = Process.pipe(["cat", "log.txt"], ["grep", "ERROR"])
```

---

### Executable Discovery

#### `Process.which(name) → str | None`
Return the absolute path to an executable on `PATH`, or `None`.

```python
Process.which("python3")   # "/usr/bin/python3"
Process.which("doesntexist")  # None
```

#### `Process.is_installed(name) → bool`
Return `True` if an executable is available on `PATH`.

```python
if not Process.is_installed("ffmpeg"):
    raise RuntimeError("ffmpeg is required")
```

#### `Process.python() → str`
Return the absolute path of the current Python interpreter.

#### `Process.python_run(script, *args, cwd=None, capture=True) → ProcessResult`
Run a Python script with the current interpreter.

```python
result = Process.python_run("scripts/migrate.py", "--dry-run")
```

---

### Context Managers (Process)

#### `Process.background(command, *, cwd=None, extra_env=None, shell=None) → ContextManager[Popen]`
Start a background process and guarantee termination when the block exits (via `terminate()`, falling back to `kill()` after 5 s).

```python
with Process.background("python -m http.server 8080") as server:
    response = requests.get("http://localhost:8080/")
    assert response.status_code == 200
# server is terminated here
```

---

### `ProcessResult`

Returned by `Process.run()`, `Process.pipe()`, and `Process.python_run()`.

| Attribute / Method | Description |
|---|---|
| `.returncode` | Exit code as `int` |
| `.stdout` | Captured stdout, stripped |
| `.stderr` | Captured stderr, stripped |
| `.ok` | `True` when exit code is `0` |
| `.lines` | stdout split into non-empty lines |
| `.raise_on_error()` | Raise `CalledProcessError` if non-zero; returns `self` otherwise |
| `bool(result)` | Equivalent to `.ok` |

```python
result = Process.run("pytest tests/", check=False)

if not result.ok:
    print(f"Tests failed (code {result.returncode})")
    for line in result.lines:
        print(line)
```

---

## `System` — System Information

```python
from arkhe.os import System
```

All methods are read-only and have no side-effects. Methods that rely on platform-specific APIs return `None` gracefully when unavailable.

---

### OS & Platform

#### `System.os_name() → str`
Human-readable OS name: `"Windows"`, `"Linux"`, or `"Darwin"`.

#### `System.os_version() → str`
Full OS version string.

#### `System.os_release() → str`
Short release identifier (e.g. `"22.04"` on Ubuntu, `"11"` on Windows).

#### `System.is_windows() → bool`
#### `System.is_linux() → bool`
#### `System.is_mac() → bool`
#### `System.is_64bit() → bool`

#### `System.arch() → str`
Machine architecture: `"x86_64"`, `"arm64"`, etc.

#### `System.hostname() → str`
Network hostname of the machine.

#### `System.user() → str`
Login name of the current user.

#### `System.shell() → str | None`
Current shell path (`$SHELL` on POSIX, `$COMSPEC` on Windows). `None` if not set.

---

### Python Runtime

#### `System.python_version() → str`
Current Python version string: `"3.12.2"`.

#### `System.python_version_tuple() → tuple[int, int, int]`
Return `(major, minor, micro)` as integers.

```python
major, minor, _ = System.python_version_tuple()
if (major, minor) < (3, 11):
    raise RuntimeError("Python 3.11+ required")
```

#### `System.python_implementation() → str`
`"CPython"`, `"PyPy"`, etc.

#### `System.python_path() → str`
Absolute path of the current interpreter.

#### `System.python_paths() → list[str]`
`sys.path` — the ordered list of directories searched for imports.

---

### CPU

#### `System.cpu_count() → int`
Total logical CPU count (hyperthreading included).

#### `System.cpu_count_physical() → int | None`
Physical core count. Returns `None` if unavailable without third-party packages.

---

### Memory

#### `System.memory() → MemoryInfo | None`
Return memory statistics. Works on Linux (via `/proc/meminfo`) and macOS (via `sysctl`). Returns `None` on unsupported platforms.

```python
mem = System.memory()
if mem:
    print(f"RAM: {mem.used_human} / {mem.total_human} ({mem.percent_used}% used)")
```

---

### Disk

#### `System.disk_usage(path="/") → DiskUsage`
Return disk usage statistics for the partition containing `path`.

```python
disk = System.disk_usage("/")
print(f"Disk: {disk.used_human} / {disk.total_human} ({disk.percent_used}% used)")
print(f"Free: {disk.free_human}")
```

---

### Uptime

#### `System.uptime() → timedelta | None`
Return system uptime. Works on Linux and macOS. Returns `None` elsewhere.

```python
up = System.uptime()
if up:
    print(f"Up for {up.days}d {up.seconds // 3600}h")
```

---

### Environment

#### `System.env_vars() → dict[str, str]`
Return a copy of all current environment variables.

#### `System.env_var(key, default=None) → str | None`
Return a single environment variable.

---

### Summary

#### `System.info() → dict`
Return a summary of the most useful system properties in a single dict. Useful for logging at application startup.

```python
import json
print(json.dumps(System.info(), indent=2, default=str))
```

```json
{
  "os": "Linux",
  "os_version": "#1 SMP ...",
  "arch": "x86_64",
  "hostname": "prod-server-01",
  "user": "deploy",
  "python": "3.12.2",
  "python_impl": "CPython",
  "cpu_logical": 8,
  "memory_total": "15.5 GB",
  "memory_used_pct": 42.3,
  "disk_total": "500.1 GB",
  "disk_used_pct": 61.0,
  "uptime": "5 days, 14:22:01"
}
```

---

### Dataclasses

#### `DiskUsage`

| Field / Property | Type | Description |
|---|---|---|
| `.path` | `str` | Queried path |
| `.total` | `int` | Total bytes |
| `.used` | `int` | Used bytes |
| `.free` | `int` | Free bytes |
| `.total_human` | `str` | e.g. `"500.1 GB"` |
| `.used_human` | `str` | e.g. `"305.2 GB"` |
| `.free_human` | `str` | e.g. `"194.9 GB"` |
| `.percent_used` | `float` | e.g. `61.0` |

#### `MemoryInfo`

| Field / Property | Type | Description |
|---|---|---|
| `.total` | `int` | Total RAM bytes |
| `.available` | `int` | Available bytes |
| `.used` | `int` | Used bytes |
| `.total_human` | `str` | e.g. `"15.5 GB"` |
| `.available_human` | `str` | e.g. `"9.0 GB"` |
| `.used_human` | `str` | e.g. `"6.5 GB"` |
| `.percent_used` | `float` | e.g. `42.3` |

---

## Design Rules

These principles are consistent across every sub-module:

1. **Stateless** — every method is a `@staticmethod`. No hidden global state, no surprises between calls.
2. **`str | Path` everywhere** — all path parameters accept both types; all path return values are `Path` objects.
3. **Parent-dir creation** — any method that writes a file or creates a directory creates missing parent directories automatically.
4. **Explicit destructive ops** — methods that overwrite or delete data have a clear name (`delete`, `safe_write`) and/or a keyword argument (`overwrite=`, `missing_ok=`). Nothing destructive is silent by surprise.
5. **Graceful degradation** — system metrics that are unavailable on a platform return `None` rather than raising.
6. **Zero third-party dependencies** — the entire package uses the Python standard library only.
7. **Cross-platform** — all methods behave identically on Windows, macOS, and Linux unless explicitly documented otherwise.
