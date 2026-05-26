"""
tests/test_yaml.py
------------------
Basic test suite for Nestify YAML module.
"""

import pytest
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nestify import yaml
from nestify.yaml import YamlPathError
from nestify.yaml.runtime import YamlRuntime

@pytest.fixture(autouse=True)
def reset_yaml_runtime():
    """Ensure tests start with a clean, uninitialized runtime."""
    yaml.shutdown()
    YamlRuntime._instance = None
    yield
    yaml.shutdown()
    YamlRuntime._instance = None

@pytest.fixture
def temp_yaml_files(tmp_path):
    # Create test configurations
    db_file = tmp_path / "database.yml"
    db_file.write_text("database:\n  host: localhost\n  port: 5432")
    
    app_file = tmp_path / "app.yml"
    app_file.write_text("app:\n  name: nestify\n  debug: true")
    
    # We don't manually scan! We let auto-bootstrap do it by setting CWD to tmp_path
    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    yield tmp_path
    
    os.chdir(old_cwd)

def test_lazy_bootstrap(temp_yaml_files):
    # Runtime should not be initialized
    assert not yaml.runtime().is_initialized
    
    # First access should bootstrap
    assert yaml.get("database.host") == "localhost"
    assert yaml.runtime().is_initialized
    
    # Registry should have paths
    assert "database.host" in yaml.paths()

def test_explicit_api(temp_yaml_files):
    assert yaml.get("database.host") == "localhost"
    assert yaml.get("app.debug") is True
    assert yaml.get("app.missing", default="fallback") == "fallback"
    
    cfg = yaml.file(temp_yaml_files / "database.yml")
    assert cfg.database.port == 5432

def test_module_getattr(temp_yaml_files):
    # Test yaml.database.host syntax
    assert yaml.database.host == "localhost"
    assert yaml.app.name == "nestify"

def test_module_getitem(temp_yaml_files):
    # Test yaml["database.host"] syntax
    assert yaml["database.host"] == "localhost"
    assert yaml["app"]["debug"] is True

def test_invalid_namespace(temp_yaml_files):
    with pytest.raises(YamlPathError):
        yaml.invalid_path
        
    with pytest.raises(YamlPathError):
        yaml["another_invalid_path"]

def test_persistent_metadata(temp_yaml_files):
    # Trigger bootstrap
    assert yaml.get("database.port") == 5432
    
    nestify_dir = temp_yaml_files / ".nestify"
    assert nestify_dir.exists()
    assert (nestify_dir / "yaml_index.json").exists()
    assert (nestify_dir / "yaml_metadata.json").exists()
    
    # Check content of metadata
    with open(nestify_dir / "yaml_metadata.json") as f:
        meta = json.load(f)
    assert str((temp_yaml_files / "database.yml").resolve()) in meta

def test_cache_invalidation(temp_yaml_files):
    assert yaml.get("database.port") == 5432
    
    db_file = temp_yaml_files / "database.yml"
    db_file.write_text("database:\n  host: remote\n  port: 9999")
    
    assert yaml.get("database.port") == 5432
    
    # Reload should trigger the scanner internally for that file
    yaml.reload(db_file)
    assert yaml.get("database.port") == 9999

def test_registry_where(temp_yaml_files):
    db_file = temp_yaml_files / "database.yml"
    assert yaml.where("database.host") == str(db_file.resolve())

def test_manual_lifecycle():
    yaml.bootstrap()
    assert yaml.runtime().is_initialized
    yaml.shutdown()
    assert not yaml.runtime().is_initialized
