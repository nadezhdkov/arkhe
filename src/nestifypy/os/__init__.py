"""
nestifypy.os
---------
Clean cross-platform wrappers around os, pathlib, shutil, subprocess, platform.
"""

from nestifypy.os.files import Files
from nestifypy.os.dirs import Dirs
from nestifypy.os.paths import Paths
from nestifypy.os.process import Process
from nestifypy.os.system import System

__all__ = ["Files", "Dirs", "Paths", "Process", "System"]
