import pytest
import os as std_os
from pathlib import Path
from arkhe import os as nos

def test_paths_join():
    p = nos.join("a", "b", "c")
    assert str(p).endswith(std_os.path.join("a", "b", "c"))

def test_paths_cwd():
    assert nos.cwd() == Path.cwd()

def test_files_read_write(tmp_path):
    file_path = tmp_path / "test.txt"
    nos.write(file_path, "hello world")
    assert nos.file_exists(file_path)
    assert nos.read(file_path) == "hello world"

def test_dirs_make_delete(tmp_path):
    new_dir = tmp_path / "new_dir"
    nos.make_dir(new_dir)
    assert nos.dir_exists(new_dir)
    nos.delete_dir(new_dir)
    assert not nos.dir_exists(new_dir)

def test_process_run():
    # Echo should be available on unix
    result = nos.run(["echo", "hello"])
    assert result.returncode == 0
    assert result.stdout.strip() == "hello"

def test_process_output():
    out = nos.output("echo hello")
    assert out.strip() == "hello"

def test_system_info():
    mem = nos.memory()
    assert mem.total > 0
    
    cpu = nos.cpu_count()
    assert cpu > 0
    
    info = nos.info()
    assert "os" in info
    assert "cpu_logical" in info
