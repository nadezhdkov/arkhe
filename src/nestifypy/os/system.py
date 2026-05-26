"""
nestifypy.os.system
----------------
Clean cross-platform wrappers around system information.
"""

from __future__ import annotations

import os
import platform
from typing import Dict

class System:
    """System information."""

    @staticmethod
    def os_name() -> str:
        return platform.system()

    @staticmethod
    def is_windows() -> bool:
        return platform.system() == "Windows"

    @staticmethod
    def is_linux() -> bool:
        return platform.system() == "Linux"

    @staticmethod
    def is_mac() -> bool:
        return platform.system() == "Darwin"

    @staticmethod
    def cpu_count() -> int:
        return os.cpu_count() or 1

    @staticmethod
    def python_version() -> str:
        return platform.python_version()

    @staticmethod
    def arch() -> str:
        return platform.machine()

    @staticmethod
    def hostname() -> str:
        return platform.node()

    @staticmethod
    def env_vars() -> Dict[str, str]:
        return dict(os.environ)
