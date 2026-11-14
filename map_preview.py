"""Standalone preview of the mapping component, without the main window or menu bar.

Loads the hard-coded map file below and draws it.
Keys: T toggles light/dark theme, L toggles right/balanced layout, R reloads the file from disk,
Ctrl+plus / Ctrl+minus zoom in and out, Ctrl+0 resets the zoom,
Insert adds a child to the selected node, Delete deletes the selected node (edits are not saved).
Mouse: click a node to select it, use the bottom-left toolbar to change its colour and shape, drag empty space (or middle-drag) to pan, wheel to scroll
(Shift+wheel scrolls sideways, Ctrl+wheel zooms around the pointer).
"""

import tkinter as tk

from mindmuni.core.builtin_themes import dark_theme, light_theme
from mindmuni.file.json_file_store import JsonFileStore
from mindmuni.file.map_repository import MapRepository
from mindmuni.file.map_serializer import MapSerializer
from mindmuni.model.map_style import MapLayout
from mindmuni.model.mind_map import MindMap
from mindmuni.ui.core.shortcut_map import ShortcutMap
from mindmuni.ui.mapping_main.mapping_view import MappingView
from mindmuni.utils.paths import maps_dir

MAP_FILE = maps_dir() / "sample.mson"
WINDOW_GEOMETRY = "1100x700"


class MapPreview:
    def __init__(self) -> None:
        self._repository = MapRepository(JsonFileStore(), MapSerializer())
        self._themes = [light_theme(), dark_theme()]
        self._theme_index = 0
        self._root = self._create_window()
        self._view = MappingView(self._root, self._themes[self._theme_index])
        self._view.pack(fill="both", expand=True)
        self._mind_map: MindMap | None = None
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
        self._root.bind("<KeyPress-l>", lambda _event: self._toggle_layout())
        self._root.bind("<KeyPress-r>", lambda _event: self._reload_map())
        ShortcutMap.bind_local(self._root, ShortcutMap.ZOOM_IN, self._view.zoom_in)
        ShortcutMap.bind_local(self._root, ShortcutMap.ZOOM_OUT, self._view.zoom_out)
        ShortcutMap.bind_local(self._root, ShortcutMap.RESET_ZOOM, self._view.reset_zoom)
        ShortcutMap.bind_local(self._root, ShortcutMap.INSERT_NODE, self._view.insert_node)
        ShortcutMap.bind_local(self._root, ShortcutMap.DELETE_NODE, self._view.delete_selected_node)

    def _reload_map(self) -> None:
        mind_map = self._repository.load(MAP_FILE)
        self._show(mind_map)

    def _show(self, mind_map: MindMap) -> None:
        self._mind_map = mind_map
        self._update_title()
        self._view.show_map(mind_map)

    def _update_title(self) -> None:
        layout = self._mind_map.style.layout.name.lower()
        self._root.title(f"{self._mind_map.title} — map preview ({MAP_FILE.name}, {layout} layout)")

    def _toggle_layout(self) -> None:
        """Changes the layout in memory only; press R to go back to the file's layout."""
        if self._mind_map is None:
            return
        is_right = self._mind_map.style.layout is MapLayout.RIGHT
        self._view.set_layout(MapLayout.BALANCED if is_right else MapLayout.RIGHT)
        self._update_title()

    def _toggle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(self._themes)
        self._view.apply_theme(self._themes[self._theme_index])


if __name__ == "__main__":
    MapPreview().run()
