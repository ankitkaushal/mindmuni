"""Standalone preview of the text editor component, without the main window or menu bar.

Loads the hard-coded map file below and shows one node's note in the editor (the root's, at first).
Keys: F5 reloads the file from disk, F6 moves to the next node (keeping the edited note in memory),
F7 toggles light/dark theme, F8 prints the edited note to the terminal (edits are not saved to the file).
"""

import tkinter as tk

from mindmuni.core.builtin_themes import dark_theme, light_theme
from mindmuni.file.json_file_store import JsonFileStore
from mindmuni.file.map_repository import MapRepository
from mindmuni.file.map_serializer import MapSerializer
from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node
from mindmuni.model.note_document import NoteDocument
from mindmuni.ui.text_editor.text_editor_view import TextEditorView
from mindmuni.utils.paths import maps_dir

MAP_FILE = maps_dir() / "sample.mson"
WINDOW_GEOMETRY = "800x600"


class TextEditorPreview:
    def __init__(self) -> None:
        self._repository = MapRepository(JsonFileStore(), MapSerializer())
        self._themes = [light_theme(), dark_theme()]
        self._theme_index = 0
        self._root = tk.Tk()
        self._root.geometry(WINDOW_GEOMETRY)
        self._view = TextEditorView(self._root, self._themes[self._theme_index])
        self._view.pack(fill="both", expand=True)
        self._nodes: list[Node] = []
        self._node_index = 0
        self._bind_keys()

    def run(self) -> None:
        self._reload_map()
        self._root.mainloop()

    def _bind_keys(self) -> None:
        self._root.bind("<F5>", lambda _event: self._reload_map())
        self._root.bind("<F6>", lambda _event: self._next_node())
        self._root.bind("<F7>", lambda _event: self._toggle_theme())
        self._root.bind("<F8>", lambda _event: self._print_note())

    def _reload_map(self) -> None:
        mind_map: MindMap = self._repository.load(MAP_FILE)
        self._nodes = list(mind_map.iter_nodes())
        self._node_index = 0
        self._show_current_node()

    def _next_node(self) -> None:
        self._current_node().note = self._view.note()  # keep the edits while moving around
        self._node_index = (self._node_index + 1) % len(self._nodes)
        self._show_current_node()

    def _show_current_node(self) -> None:
        node = self._current_node()
        self._view.show_note(node.note)
        position = f"{self._node_index + 1}/{len(self._nodes)}"
        self._root.title(f"{node.title} — text editor preview ({MAP_FILE.name}, node {position})")

    def _current_node(self) -> Node:
        return self._nodes[self._node_index]

    def _toggle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(self._themes)
        self._view.apply_theme(self._themes[self._theme_index])

    def _print_note(self) -> None:
        note: NoteDocument = self._view.note()
        print(f"--- {self._current_node().title}: {len(note.blocks)} block(s)")
        for block in note.blocks:
            spans = " | ".join(
                f"{span.text!r}{' bold' * span.bold}{' highlighted' * span.highlighted}" for span in block.spans
            )
            print(f"{block.block_type.value:<10} {spans}")


if __name__ == "__main__":
    TextEditorPreview().run()
