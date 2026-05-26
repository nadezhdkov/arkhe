"""
nestifypy.yaml.metadata
--------------------
Manages persistent registry metadata and file hashes/mtimes in .nestifypy/
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

class MetadataManager:
    """
    Manages `.nestifypy/` storage for incremental scanning and registry persistence.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.nestifypy_dir = self.project_root / ".nestifypy"
        self.index_file = self.nestifypy_dir / "yaml_index.json"
        self.meta_file = self.nestifypy_dir / "yaml_metadata.json"

        # Memory state
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        if not self.nestifypy_dir.exists():
            self.nestifypy_dir.mkdir(parents=True, exist_ok=True)

    def load_index(self) -> Dict[str, str]:
        """Load the persisted path registry index."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_index(self, index: Dict[str, str]) -> None:
        """Save the path registry index to disk."""
        self._ensure_dir()
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

    def load_metadata(self) -> None:
        """Load the file hashes and mtimes into memory."""
        if self.meta_file.exists():
            try:
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except Exception:
                self._metadata = {}
        else:
            self._metadata = {}

    def save_metadata(self) -> None:
        """Save the in-memory metadata to disk."""
        self._ensure_dir()
        with open(self.meta_file, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, indent=2)

    def get_file_meta(self, absolute_path: str) -> Optional[Dict[str, Any]]:
        """Return the known metadata for a file."""
        return self._metadata.get(absolute_path)

    def update_file_meta(self, absolute_path: str, mtime: float, file_hash: str) -> None:
        """Update memory metadata for a file."""
        self._metadata[absolute_path] = {"mtime": mtime, "hash": file_hash}

    def remove_file_meta(self, absolute_path: str) -> None:
        """Remove a file from metadata."""
        self._metadata.pop(absolute_path, None)

    def is_modified(self, absolute_path: str, current_mtime: float) -> bool:
        """Check if a file was modified since the last scan (based on mtime)."""
        meta = self._metadata.get(absolute_path)
        if not meta:
            return True
        return meta.get("mtime") != current_mtime

    def clear(self) -> None:
        """Clear all metadata both in memory and on disk."""
        self._metadata.clear()
        if self.index_file.exists():
            self.index_file.unlink()
        if self.meta_file.exists():
            self.meta_file.unlink()
