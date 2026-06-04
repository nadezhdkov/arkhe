import sys
from pathlib import Path
from arkhe.yaml import Yaml

Path("test_db.yml").write_text("database:\n  host: localhost\n  port: 5432")

Yaml.scan(".")

print("Registry:", Yaml.registry())
print("Yaml.get('database'):", Yaml.get("database"))
print("Yaml.get('database.host'):", Yaml.get("database.host"))

