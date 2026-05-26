"""
tests/test_json.py
------------------
Basic test suite for Nestify JSON module.
"""

import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nestify.json import Json, JsonError, JsonParseError, JsonValidationError

def test_json_parse_and_stringify():
    data = {"key": "value", "num": 42}
    text = Json.stringify(data)
    assert '"key": "value"' in text
    
    parsed = Json.parse(text)
    assert parsed["key"] == "value"
    assert parsed["num"] == 42

def test_json_parse_as_dotdict():
    text = '{"window": {"width": 800}}'
    parsed = Json.parse_as_dotdict(text)
    assert parsed.window.width == 800

def test_json_merge():
    base = {"a": 1, "b": {"c": 2}}
    override = {"b": {"c": 3, "d": 4}, "e": 5}
    merged = Json.merge(base, override)
    
    assert merged["a"] == 1
    assert merged["b"]["c"] == 3
    assert merged["b"]["d"] == 4
    assert merged["e"] == 5

def test_json_validate():
    config = Json.parse_as_dotdict('{"fps": 60, "title": "Game"}')
    schema = {"fps": int, "title": str}
    assert Json.validate(config, schema)

def test_json_validate_fails():
    config = Json.parse_as_dotdict('{"fps": "sixty", "title": "Game"}')
    schema = {"fps": int, "title": str}
    with pytest.raises(JsonValidationError):
        Json.validate(config, schema)

def test_json_file_io(tmp_path):
    p = tmp_path / "test.json"
    
    data = {"hello": "world", "nested": {"key": "value"}}
    Json.save(p, data)
    assert p.exists()
    assert Json.exists(p)
    
    # Read as dict
    raw = Json.read(p)
    assert isinstance(raw, dict)
    assert raw["hello"] == "world"
    
    # Load as DotDict
    dot = Json.load(p)
    assert dot.nested.key == "value"
    
    # Load with defaults
    dot_defaults = Json.load(p, defaults={"new_key": "new_value"})
    assert dot_defaults.new_key == "new_value"
    assert dot_defaults.hello == "world"

def test_invalid_json_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{bad json")
    
    with pytest.raises(JsonParseError):
        Json.read(p)
