"""
tests/test_env.py
-----------------
Tests for the Nestify Env module, including new decorators.
"""

import os
import pytest
from nestify.env import Env

@pytest.fixture(autouse=True)
def clean_env():
    # Store old env
    old_env = dict(os.environ)
    yield
    # Restore
    os.environ.clear()
    os.environ.update(old_env)

def test_env_basic():
    Env.set("TEST_VAR", "hello")
    assert Env.get("TEST_VAR") == "hello"

def test_env_property():
    Env.set("DB_HOST", "localhost")
    Env.set("DB_PORT", "5432")
    Env.set("DB_ACTIVE", "true")

    class AppConfig:
        host = Env.property("DB_HOST")
        port = Env.property("DB_PORT", cast_type=int)
        active = Env.property("DB_ACTIVE", cast_type=bool)
        missing = Env.property("DB_MISSING", default="fallback")

    cfg = AppConfig()
    
    assert cfg.host == "localhost"
    assert cfg.port == 5432
    assert cfg.active is True
    assert cfg.missing == "fallback"

def test_env_inject():
    Env.set("API_KEY", "secret_key")
    Env.set("TIMEOUT", "30")

    @Env.inject(api_key="API_KEY", timeout="TIMEOUT")
    def connect(api_key: str = None, timeout: str = None):
        return api_key, timeout

    # Both injected
    assert connect() == ("secret_key", "30")
    
    # One overridden
    assert connect(api_key="custom") == ("custom", "30")
    
    # Both overridden
    assert connect(api_key="custom", timeout="10") == ("custom", "10")
