"""
tools/sync.py
-------------
Synchronize all derived files from project.yml.
Run: python tools/sync.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌  pyyaml required: pip install pyyaml")
    sys.exit(1)

CONFIG_FILE = "project.yml"


def main() -> None:
    cfg_path = Path(CONFIG_FILE)
    if not cfg_path.exists():
        print(f"❌  {CONFIG_FILE} not found. Run: nestify init")
        sys.exit(1)

    with open(cfg_path, "r") as f:
        config = yaml.safe_load(f)

    python_version: str = str(config["python"]["version"])
    project_name: str = config["project"]["name"]
    project_version: str = config["project"]["version"]

    print(f"\n🔄  Syncing from {CONFIG_FILE}…\n")

    # ── .python-version ──────────────────────
    pv = Path(".python-version")
    pv.write_text(python_version)
    print(f"  ✓  .python-version → {python_version}")

    # ── pyproject.toml ────────────────────────
    pp = Path("pyproject.toml")
    if pp.exists():
        content = pp.read_text(encoding="utf-8")
        content = re.sub(
            r'requires-python\s*=\s*"[^"]+"',
            f'requires-python = ">={python_version}"',
            content,
        )
        content = re.sub(
            r'^version\s*=\s*"[^"]+"',
            f'version = "{project_version}"',
            content,
            flags=re.MULTILINE,
        )
        pp.write_text(content, encoding="utf-8")
        print(f"  ✓  pyproject.toml → version={project_version}, python>={python_version}")

    # ── Dockerfile ────────────────────────────
    docker_cfg = config.get("docker", {})
    image_name: str = docker_cfg.get("image", f"{project_name}:latest")

    dockerfile = Path("Dockerfile")
    if not dockerfile.exists():
        dockerfile.write_text(
            f"FROM python:{python_version}-slim\n"
            f"WORKDIR /app\n"
            f"COPY . .\n"
            f"RUN pip install -e .\n"
            f'CMD ["python", "-m", "{project_name}"]\n'
        )
        print(f"  ✓  Dockerfile generated (python:{python_version}-slim)")
    else:
        content = dockerfile.read_text(encoding="utf-8")
        content = re.sub(
            r"FROM python:[^\s]+",
            f"FROM python:{python_version}-slim",
            content,
        )
        dockerfile.write_text(content, encoding="utf-8")
        print(f"  ✓  Dockerfile → python:{python_version}-slim")

    print(f"\n✅  Sync complete.\n")


if __name__ == "__main__":
    main()
