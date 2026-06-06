"""
demo.py — Arkhe I/O feature showcase.
Run from the arkhe/ parent directory:
    python demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from arkhe.io import install, success, warning, error, info, inspect_obj, theme
from arkhe.io.renderer import log_separator

install()

# ──────────────────────────────────────────────────────
# 1. Inline logs
# ──────────────────────────────────────────────────────
print("Engine initialized")
print("Loading internal modules...")
print(warning("Response time exceeded 120ms"))
print("Connection stabilized")
print(log_separator())

# ──────────────────────────────────────────────────────
# 2. Status panels
# ──────────────────────────────────────────────────────
print(success("User created successfully"))
print(warning("High latency detected on database pool"))
print(error("Connection refused by remote host at 192.168.1.100:5432"))
print(info("Scheduled maintenance window starts in 15 minutes"))

# ──────────────────────────────────────────────────────
# 3. Color tags
# ──────────────────────────────────────────────────────
print("{green}Connected{/} to {cyan}arkhe-db-01{/}")
print("{red}CRITICAL{/}: {yellow}disk usage above 90%{/}")

# ──────────────────────────────────────────────────────
# 4. Dictionary rendering
# ──────────────────────────────────────────────────────
config = {
    "port": 25565,
    "debug": True,
    "host": "localhost",
    "modules": ["auth_core", "database_pool"],
    "timeout": None,
}
print(config)

# ──────────────────────────────────────────────────────
# 5. Object rendering
# ──────────────────────────────────────────────────────
class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age  = age

    def save(self): ...
    def login(self): ...
    def logout(self): ...

user = User("Samuel", 15)
print(user)

# ──────────────────────────────────────────────────────
# 6. inspect()
# ──────────────────────────────────────────────────────
inspect_obj(User)

# ──────────────────────────────────────────────────────
# 7. Theme switch demo
# ──────────────────────────────────────────────────────
print(log_separator())
print("Switching to Dracula theme...")
theme("dracula")
print(success("Theme applied: Dracula"))
print(warning("This is how warnings look now"))
theme("default")

# ──────────────────────────────────────────────────────
# 8. Traceback (triggered last, process ends)
# ──────────────────────────────────────────────────────
print(log_separator())
print("Triggering example traceback...")

def connect(host_ip):
    db_timeout = 30
    result = int(host_ip)   # will raise ValueError

connect(None)
