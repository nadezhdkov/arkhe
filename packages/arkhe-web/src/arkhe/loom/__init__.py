"""
arkhe.loom
--------------
The Loom configuration system — a modern, runtime-oriented alternative
to .env / python-dotenv for the arkhe ecosystem.

Key features (per Loom Spec v0.1):
    - Hierarchical, modular .loom files
    - Environment-profile-aware loading
    - Smart Resolution with 4-level namespace flattening
    - Typed values with automatic inference
    - Schema binding with dataclass integration
    - Design-by-Contract style runtime errors
    - Extensible provider system

Quick start::

    # app.loom
    @module("app")
    @server {
        host: "localhost"
        port: 8080
        debug: true
    }

    # Python
    from arkhe.loom import Loom, env

    Loom.load("app.loom")

    host  = env.server.host          # LoomValue → "localhost"
    port  = env.server.port.int      # 8080
    debug = env.server.debug.bool    # True
    scope = env.server               # ScopeObject
"""

from arkhe.loom.runtime import Loom, LoomRuntime, env, reset
from arkhe.loom.providers import FileProvider, OverrideProvider, SystemEnvProvider
from arkhe.loom.scope import LoomValue, ScopeObject
from arkhe.loom.exceptions import (
    LoomAmbiguityError,
    LoomError,
    LoomImportError,
    LoomResolutionError,
    LoomSchemaError,
    LoomScopeConflictError,
    LoomSyntaxError,
    LoomTypeError,
)
from arkhe.loom.parser import parse
from arkhe.loom.ast_nodes import ModuleNode

__version__ = "0.1.0"

__all__ = [
    # Runtime
    "Loom",
    "LoomRuntime",
    "env",
    "reset",
    # Providers
    "FileProvider",
    "SystemEnvProvider",
    "OverrideProvider",
    # Values
    "LoomValue",
    "ScopeObject",
    # Parser
    "parse",
    "ModuleNode",
    # Exceptions
    "LoomError",
    "LoomSyntaxError",
    "LoomTypeError",
    "LoomResolutionError",
    "LoomAmbiguityError",
    "LoomImportError",
    "LoomSchemaError",
    "LoomScopeConflictError",
]
