"""
nestifypy.os.process
-----------------
Clean cross-platform wrappers around subprocess operations.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

class Process:
    """Subprocess helpers."""

    @staticmethod
    def run(
        command: str,
        cwd: Optional[str | Path] = None,
        capture: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a shell command."""
        return subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=capture,
            text=True,
            check=check,
        )

    @staticmethod
    def output(command: str, cwd: Optional[str | Path] = None) -> str:
        """Run a command and return stdout as string."""
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    @staticmethod
    def which(name: str) -> Optional[str]:
        """Find the path to an executable."""
        return shutil.which(name)

    @staticmethod
    def python() -> str:
        """Return the current Python executable path."""
        return sys.executable
