import tkinter as tk
from tkinter import ttk

from mindmuni.core.map_editor import MapEditor
from mindmuni.core.selection_manager import SelectionManager
from mindmuni.core.tree_layout import TreeLayout
from mindmuni.model.map_style import MapLayout
from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node
from mindmuni.model.theme import Theme
from mindmuni.ui.core.view import View
from mindmuni.ui.mapping_main.map_canvas import MapCanvas
from mindmuni.ui.mapping_main.map_toolbar import MapToolbar

MAP_VIEW_ID = "map"


class MappingView(View):
    """Mapping main component: lays out a MindMap, shows it on a scrollable canvas, and edits it.

    The edit toolbar floats over the canvas's bottom-right corner and stays there when the window is resized.
    """

    def __init__(
        self, parent: tk.Misc, theme: Theme, view_id: str = MAP_VIEW_ID, editor: MapEditor | None = None
    ) -> None:
        super().__init__(parent, view_id)
        self._mind_map: MindMap | None = None
        self._editor = editor or MapEditor()
        self._selection = SelectionManager()
        self._canvas = self._create_scrollable_canvas()
        self._canvas.on_node_click(self._on_node_click)
        self._layout = TreeLayout(self._canvas.measure_node)
        self._toolbar = MapToolbar(self, on_insert=self.insert_node, on_delete=self.delete_selected_node)
        self._toolbar.pin_to(self._canvas)
        self.apply_theme(theme)

    def show_map(self, mind_map: MindMap) -> None:
        """Shows the map with its root selected, centred on the root."""
        self._mind_map = mind_map
        self._selection.select(mind_map.root.node_id)
        self._redraw()
        self.after_idle(lambda: self._canvas.center_on(mind_map.root.position))

    def set_layout(self, layout: MapLayout) -> None:
        """Changes the shown map's layout style (RIGHT or BALANCED) and redraws it around the root."""
        if self._mind_map is None or self._mind_map.style.layout is layout:
            return
        self._mind_map.style.layout = layout
        self._redraw()
        self.after_idle(lambda: self._canvas.center_on(self._mind_map.root.position))

    # --- editing ------------------------------------------------------------

    def insert_node(self) -> None:
        """Adds a child to the selected node and selects the new child."""
        selected = self._selected_node()
        if selected is None:
            return
        anchor = self._canvas.window_point_of(selected.position)
        child = self._editor.add_child(self._mind_map, selected.node_id)
        self._selection.select(child.node_id)
        self._redraw_keeping_in_place(selected, anchor)

    def delete_selected_node(self) -> None:
        """Deletes the selected node with its subtree and selects its parent. Does nothing for the root."""
        selected = self._selected_node()
        if selected is None or not self._editor.can_delete(self._mind_map, selected.node_id):
            return
        parent = self._mind_map.parent_of(selected.node_id)
        anchor = self._canvas.window_point_of(parent.position)
        self._editor.delete_node(self._mind_map, selected.node_id)
        self._selection.select(parent.node_id)
        self._redraw_keeping_in_place(parent, anchor)

    # --- zoom ---------------------------------------------------------------

    def zoom_in(self) -> None:
        self._canvas.zoom_in()

    def zoom_out(self) -> None:
        self._canvas.zoom_out()

    def reset_zoom(self) -> None:
        self._canvas.reset_zoom()

    @property
    def zoom(self) -> float:
        return self._canvas.zoom

    def apply_theme(self, theme: Theme) -> None:
        self._canvas.apply_theme(theme)
        self._toolbar.apply_theme(theme)
        self._redraw()  # fonts may change, so node sizes and layout change too

    # --- internals ----------------------------------------------------------

    def _on_node_click(self, node_id: str | None) -> None:
        if self._mind_map is None or node_id == self._selection.selected_id:
            return
        self._selection.select(node_id)
        self._canvas.draw_map(self._mind_map, node_id)  # selection doesn't change sizes, so no new layout
        self._update_toolbar()

    def _selected_node(self) -> Node | None:
        if self._mind_map is None:
            return None
        return self._selection.selected_node(self._mind_map)

    def _redraw(self) -> None:
        if self._mind_map is not None:
            self._layout.apply(self._mind_map)
            self._canvas.draw_map(self._mind_map, self._selection.selected_id)
        self._update_toolbar()

    def _redraw_keeping_in_place(self, node: Node, window_point: tuple[float, float]) -> None:
        """Redraws after an edit, then scrolls so `node` is back where it was on screen.

        The layout keeps the tree's top-left corner fixed, so without this an edit can make the whole map jump.
        """
        self._redraw()
        self._canvas.scroll_point_to(node.position, *window_point)

    def _update_toolbar(self) -> None:
        selected = self._selected_node()
        can_delete = selected is not None and self._editor.can_delete(self._mind_map, selected.node_id)
        self._toolbar.set_enabled(insert=selected is not None, delete=can_delete)

    def _create_scrollable_canvas(self) -> MapCanvas:
        canvas = MapCanvas(self)
        vertical = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        return canvas
