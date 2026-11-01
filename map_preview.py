"""Standalone preview of the mapping component, without the main window or menu bar.

Loads the hard-coded map file below and draws it.
Keys: T toggles light/dark theme, R reloads the file from disk.
Mouse: drag to pan, wheel to scroll (Shift+wheel scrolls sideways).
"""

import tkinter as tk

from mindmuni.core.builtin_themes import dark_theme, light_theme
from mindmuni.file.json_file_store import JsonFileStore
from mindmuni.file.map_repository import MapRepository
from mindmuni.file.map_serializer import MapSerializer
from mindmuni.model.mind_map import MindMap
from mindmuni.ui.mapping_main.mapping_view import MappingView
from mindmuni.utils.paths import maps_dir

MAP_FILE = maps_dir() / "sample.mindmuni.json"
WINDOW_GEOMETRY = "1100x700"


class MapPreview:
    def __init__(self) -> None:
        self._repository = MapRepository(JsonFileStore(), MapSerializer())
        self._themes = [light_theme(), dark_theme()]
        self._theme_index = 0
        self._root = self._create_window()
        self._view = MappingView(self._root, self._themes[self._theme_index])
        self._view.pack(fill="both", expand=True)
        self._bind_keys()

    def run(self) -> None:
        self._reload_map()
        self._root.mainloop()

    def _create_window(self) -> tk.Tk:
        root = tk.Tk()
        root.geometry(WINDOW_GEOMETRY)
        return root

    def _bind_keys(self) -> None:
        self._root.bind("<KeyPress-t>", lambda _event: self._toggle_theme())
        self._root.bind("<KeyPress-r>", lambda _event: self._reload_map())

    def _reload_map(self) -> None:
        mind_map = self._repository.load(MAP_FILE)
        self._show(mind_map)

    def _show(self, mind_map: MindMap) -> None:
        self._root.title(f"{mind_map.title} — map preview ({MAP_FILE.name})")
        self._view.show_map(mind_map)

    def _toggle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(self._themes)
        self._view.apply_theme(self._themes[self._theme_index])


if __name__ == "__main__":
    MapPreview().run()
