"""
arkhe.yaml.bootstrap
---------------------
Lazy initialization orchestrator and project discovery.
"""

import os
from pathlib import Path
from typing import Optional

def discover_project_root(start_dir: Path) -> Path:
    """
    Search upwards for indicators of a project root:
    pyproject.toml, .git, setup.py, .arkhe
    Fallback to current working directory if not found.
    """
    current = start_dir.resolve()
    while True:
        if (current / "pyproject.toml").exists() or \
           (current / ".git").exists() or \
           (current / "setup.py").exists() or \
           (current / ".arkhe").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path(os.getcwd()).resolve()
