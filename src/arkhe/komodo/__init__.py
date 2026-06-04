"""
arkhe.komodo
--------------
Lombok-style annotation-driven metaprogramming for Python.

Eliminates class boilerplate by generating dunder methods, builders,
accessors, validators, and lifecycle hooks — all via decorators.

IDE Support:
    This module can generate .pyi stub files for IDE autocomplete support
    in PyCharm, VS Code/Pylance, and other compatible IDEs.

Usage:
    from arkhe.komodo import komodo

    @komodo.data
    class User:
        name: str
        age: int

    @komodo.builder
    class Config:
        host: str = "localhost"
        port: int = 8080
"""

from arkhe.komodo.core import komodo
from arkhe.komodo.contract import contract, ContractViolationError
from arkhe.komodo.inspect import KomodoInspector

# Optional: import stub generator if available
try:
    from arkhe.komodo.stub_generator import StubGenerator, generate_and_write_stub
    __all__ = [
        "komodo",
        "contract",
        "ContractViolationError",
        "KomodoInspector",
        "StubGenerator",
        "generate_and_write_stub",
    ]
except ImportError:
    # stub_generator not available (OK for basic use)
    __all__ = [
        "komodo",
        "contract",
        "ContractViolationError",
        "KomodoInspector",
    ]

__version__ = "0.2.1"
