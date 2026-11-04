from pathlib import Path

from mindmuni.file.json_file_store import JsonFileStore
from mindmuni.file.map_serializer import MapSerializer
from mindmuni.model.mind_map import MindMap


class MapRepository:
    """Loads and saves MindMaps as .mson files."""

    def __init__(self, store: JsonFileStore, serializer: MapSerializer) -> None:
        self._store = store
        self._serializer = serializer

    def load(self, path: Path) -> MindMap:
        return self._serializer.from_document(self._store.read(path))

    def save(self, mind_map: MindMap, path: Path) -> None:
        mind_map.touch()
        self._store.write(path, self._serializer.to_document(mind_map))
