"""
arkhe.os
------------
Clean, cross-platform OS utilities.

Sub-modules
~~~~~~~~~~~
* :mod:`arkhe.os.files`   — file I/O (read, write, hash, JSON, CSV, …)
* :mod:`arkhe.os.dirs`    — directory operations (list, tree, temp, cd, …)
* :mod:`arkhe.os.paths`   — pure path manipulation (join, expand, uri, …)
* :mod:`arkhe.os.process` — subprocess helpers (run, stream, pipe, …)
* :mod:`arkhe.os.system`  — system info (CPU, memory, disk, uptime, …)

All five classes are available directly from ``arkhe.os``::

    from arkhe import os as nos

    nos.files.read("config.json")
    nos.dirs.tree("src/")
    nos.paths.expand("~/data")
    nos.process.output("git rev-parse HEAD")
    nos.system.info()

Convenience flat API
~~~~~~~~~~~~~~~~~~~~
The most frequently used operations are also re-exported at package level
so you can skip the sub-module name in common cases::

    from arkhe.os import read, write, exists, run, tree

Flat aliases
------------
files:   read, write, safe_write, read_json, write_json, read_csv, write_csv,
         read_bytes, write_bytes, copy_file, move_file, delete_file, touch,
         file_exists, file_size, file_hash, find_files, grep, zip_file, unzip_file

dirs:    list_dir, list_files, list_dirs, make_dir, delete_dir, copy_dir,
         move_dir, walk, find_dirs, tree, dir_exists, dir_size, empty_dir,
         temp_dir

paths:   join, resolve, expand, normalize, home, cwd, parent, stem, suffix,
         with_suffix, with_name, to_uri, to_posix, temp_path

process: run, output, stream, pipe, which, is_installed, python_path

system:  cpu_count, memory, disk_usage, uptime, hostname, os_name, info
"""
from __future__ import annotations

from arkhe.os.files   import Files
from arkhe.os.dirs    import Dirs
from arkhe.os.paths   import Paths
from arkhe.os.process import Process, ProcessResult
from arkhe.os.system  import System, DiskUsage, MemoryInfo

# ---------------------------------------------------------------------------
# Flat convenience aliases — files
# ---------------------------------------------------------------------------
read         = Files.read
write        = Files.write
safe_write   = Files.safe_write
read_bytes   = Files.read_bytes
write_bytes  = Files.write_bytes
read_json    = Files.read_json
write_json   = Files.write_json
read_csv     = Files.read_csv
write_csv    = Files.write_csv
touch        = Files.touch
delete_file  = Files.delete
copy_file    = Files.copy
move_file    = Files.move
rename_file  = Files.rename
file_exists  = Files.exists
file_size    = Files.size
file_hash    = Files.hash
lines        = Files.lines
line_count   = Files.line_count
stream_lines = Files.stream_lines
head         = Files.head
tail         = Files.tail
grep         = Files.grep
find_files   = Files.find
zip_file     = Files.zip
unzip_file   = Files.unzip
open_file    = Files.open_default

# ---------------------------------------------------------------------------
# Flat convenience aliases — dirs
# ---------------------------------------------------------------------------
make_dir    = Dirs.create
ensure_dir  = Dirs.create       # alias
delete_dir  = Dirs.delete
copy_dir    = Dirs.copy
move_dir    = Dirs.move
rename_dir  = Dirs.rename
list_dir    = Dirs.list
list_files  = Dirs.list_files
list_dirs   = Dirs.list_dirs
walk        = Dirs.walk
find_dirs   = Dirs.find
tree        = Dirs.tree
dir_exists  = Dirs.exists
dir_size    = Dirs.size
empty_dir   = Dirs.is_empty
file_count  = Dirs.file_count

# ---------------------------------------------------------------------------
# Flat convenience aliases — paths
# ---------------------------------------------------------------------------
join        = Paths.join
resolve     = Paths.resolve
expand      = Paths.expand
normalize   = Paths.normalize
home        = Paths.home
cwd         = Paths.cwd
parent      = Paths.parent
stem        = Paths.stem
suffix      = Paths.suffix
with_suffix = Paths.with_suffix
with_name   = Paths.with_name
with_stem   = Paths.with_stem
to_uri      = Paths.to_uri
to_posix    = Paths.to_posix
temp_path   = Paths.temp_path
is_absolute = Paths.is_absolute

# ---------------------------------------------------------------------------
# Flat convenience aliases — process
# ---------------------------------------------------------------------------
run          = Process.run
output       = Process.output
ok           = Process.ok
stream       = Process.stream
pipe         = Process.pipe
which        = Process.which
is_installed = Process.is_installed
python_path  = Process.python

# ---------------------------------------------------------------------------
# Flat convenience aliases — system
# ---------------------------------------------------------------------------
cpu_count  = System.cpu_count
memory     = System.memory
disk_usage = System.disk_usage
uptime     = System.uptime
hostname   = System.hostname
os_name    = System.os_name
info       = System.info


__all__ = [
    # Sub-modules / classes
    "Files", "Dirs", "Paths", "Process", "ProcessResult",
    "System", "DiskUsage", "MemoryInfo",
    # files
    "read", "write", "safe_write", "read_bytes", "write_bytes",
    "read_json", "write_json", "read_csv", "write_csv",
    "touch", "delete_file", "copy_file", "move_file", "rename_file",
    "file_exists", "file_size", "file_hash",
    "lines", "line_count", "stream_lines", "head", "tail",
    "grep", "find_files", "zip_file", "unzip_file", "open_file",
    # dirs
    "make_dir", "ensure_dir", "delete_dir", "copy_dir", "move_dir",
    "rename_dir", "list_dir", "list_files", "list_dirs",
    "walk", "find_dirs", "tree", "dir_exists", "dir_size", "empty_dir",
    "file_count",
    # paths
    "join", "resolve", "expand", "normalize",
    "home", "cwd", "parent", "stem", "suffix",
    "with_suffix", "with_name", "with_stem",
    "to_uri", "to_posix", "temp_path", "is_absolute",
    # process
    "run", "output", "ok", "stream", "pipe",
    "which", "is_installed", "python_path",
    # system
    "cpu_count", "memory", "disk_usage", "uptime",
    "hostname", "os_name", "info",
]
