import tkinter as tk
from tkinter import ttk

from mindmuni.core.tree_layout import TreeLayout
from mindmuni.model.map_style import MapLayout
from mindmuni.model.mind_map import MindMap
from mindmuni.model.theme import Theme
from mindmuni.ui.core.view import View
from mindmuni.ui.mapping_main.map_canvas import MapCanvas

MAP_VIEW_ID = "map"


class MappingView(View):
    """Mapping main component: lays out a MindMap and shows it on a scrollable canvas."""

    def __init__(self, parent: tk.Misc, theme: Theme, view_id: str = MAP_VIEW_ID) -> None:
        super().__init__(parent, view_id)
        self._mind_map: MindMap | None = None
        self._canvas = self._create_scrollable_canvas()
        self._layout = TreeLayout(self._canvas.measure_node)
        self._canvas.apply_theme(theme)

    def show_map(self, mind_map: MindMap) -> None:
        self._mind_map = mind_map
        self._redraw()
        self.after_idle(lambda: self._canvas.center_on(mind_map.root.position))

    def set_layout(self, layout: MapLayout) -> None:
        """Changes the shown map's layout style (RIGHT or BALANCED) and redraws it around the root."""
        if self._mind_map is None or self._mind_map.style.layout is layout:
            return
        self._mind_map.style.layout = layout
        self._redraw()
        self.after_idle(lambda: self._canvas.center_on(self._mind_map.root.position))

    def apply_theme(self, theme: Theme) -> None:
        self._canvas.apply_theme(theme)
        self._redraw()  # fonts may change, so node sizes and layout change too

    def _redraw(self) -> None:
        if self._mind_map is None:
            return
        self._layout.apply(self._mind_map)
        self._canvas.draw_map(self._mind_map)

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
