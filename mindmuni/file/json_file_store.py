import json
import os
from pathlib import Path


class JsonFileStore:
    """Low-level JSON read/write. The only class that touches the disk."""

    def read(self, path: Path) -> dict:
        with path.open(encoding="utf-8") as json_file:
            return json.load(json_file)

    def write(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_name(path.name + ".tmp")
        with temporary_path.open("w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=2, ensure_ascii=False)
        os.replace(temporary_path, path)  # atomic: a crash never leaves a half-written map
