import tkinter as tk
from tkinter import ttk

from mindmuni.core.map_editor import MapEditor
from mindmuni.core.selection_manager import SelectionManager
from mindmuni.core.tree_layout import TreeLayout
from mindmuni.model.map_style import MapLayout
from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node
from mindmuni.model.node_style import NodeColor, NodeShape
from mindmuni.model.theme import Theme
from mindmuni.ui.core.view import View
from mindmuni.ui.mapping_main.map_canvas import MapCanvas
from mindmuni.ui.mapping_main.map_toolbar import MapToolbar
from mindmuni.ui.mapping_main.style_toolbar import StyleToolbar
from mindmuni.ui.mapping_main.title_editor import TitleEditor
from mindmuni.ui.mapping_main.view_toolbar import ViewToolbar

MAP_VIEW_ID = "map"


class MappingView(View):
    """Mapping main component: lays out a MindMap, shows it on a scrollable canvas, and edits it.

    The edit toolbar floats over the canvas's bottom-right corner, the style toolbar (colour and shape) over its
    bottom-left corner and the view toolbar (zoom and the drag lock) over its top-right corner; all stay there
    when the window is resized. Dragging the map around is locked until the view toolbar's Drag button turns it on.

    A node's title is edited in place (double-click, F2 or the Edit button), by typing into its drawn text.
    The Edit button is disabled while a title is being edited.
    Every action that redraws first stops editing and saves what was typed, because a redraw replaces that text.
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
        self._canvas.on_node_double_click(self._on_node_double_click)
        self._canvas.on_before_zoom(self._finish_editing)
        self._canvas.on_zoom_changed(self._update_view_toolbar)
        self._layout = TreeLayout(self._canvas.measure_node)
        self._title_editor = TitleEditor(
            self._canvas, on_commit=self._rename_node, on_editing_changed=lambda _editing: self._update_toolbar()
        )
        self._toolbar = MapToolbar(
            self, on_insert=self.insert_node, on_edit=self.edit_selected_title, on_delete=self.delete_selected_node
        )
        self._toolbar.pin_to(self._canvas)
        self._style_toolbar = StyleToolbar(self, on_color=self.set_selected_color, on_shape=self.set_selected_shape)
        self._style_toolbar.pin_to(self._canvas)
        self._view_toolbar = ViewToolbar(
            self,
            on_zoom_out=self.zoom_out,
            on_reset=self.reset_zoom,
            on_zoom_in=self.zoom_in,
            on_toggle_drag=self.toggle_drag,
        )
        self._view_toolbar.pin_to(self._canvas)
        self._update_view_toolbar()
        self._theme = theme
        self.apply_theme(theme)

    def show_map(self, mind_map: MindMap) -> None:
        """Shows the map with its root selected, centred on the root."""
        self._title_editor.cancel()  # the node being edited belongs to the old map
        self._mind_map = mind_map
        self._selection.select(mind_map.root.node_id)
        self._redraw()
        self.after_idle(lambda: self._canvas.center_on(mind_map.root.position))

    def set_layout(self, layout: MapLayout) -> None:
        """Changes the shown map's layout style (RIGHT or BALANCED) and redraws it around the root."""
        if self._mind_map is None or self._mind_map.style.layout is layout:
            return
        self._finish_editing()
        self._mind_map.style.layout = layout
        self._redraw()
        self.after_idle(lambda: self._canvas.center_on(self._mind_map.root.position))

    # --- editing ------------------------------------------------------------

    def insert_node(self) -> None:
        """Adds a child to the selected node, selects it and opens its title for editing, ready to type over."""
        self._finish_editing()
        selected = self._selected_node()
        if selected is None:
            return
        anchor = self._canvas.window_point_of(selected.position)
        child = self._editor.add_child(self._mind_map, selected.node_id)
        self._selection.select(child.node_id)
        self._redraw_keeping_in_place(selected, anchor)
        self.edit_selected_title(select_all=True)

    def edit_selected_title(self, select_all: bool = False) -> None:
        """Opens the selected node's title for editing in place. Enter saves, Shift+Enter adds a line, Esc cancels."""
        self._finish_editing()
        selected = self._selected_node()
        if selected is None:
            return
        self._title_editor.start(selected, self._theme, select_all)

    def delete_selected_node(self) -> None:
        """Deletes the selected node with its subtree and selects its parent. Does nothing for the root."""
        self._finish_editing()
        selected = self._selected_node()
        if selected is None or not self._editor.can_delete(self._mind_map, selected.node_id):
            return
        parent = self._mind_map.parent_of(selected.node_id)
        anchor = self._canvas.window_point_of(parent.position)
        self._editor.delete_node(self._mind_map, selected.node_id)
        self._selection.select(parent.node_id)
        self._redraw_keeping_in_place(parent, anchor)

    def set_selected_color(self, color: NodeColor) -> None:
        """Changes the selected node's colour. Sizes don't change, so the map is only redrawn."""
        self._finish_editing()
        selected = self._selected_node()
        if selected is None or not self._editor.set_color(self._mind_map, selected.node_id, color):
            return
        self._canvas.draw_map(self._mind_map, selected.node_id)
        self._update_toolbar()

    def set_selected_shape(self, shape: NodeShape) -> None:
        """Changes the selected node's shape. Its size can change, so the layout runs again with the node kept in place."""
        self._finish_editing()
        selected = self._selected_node()
        if selected is None:
            return
        anchor = self._canvas.window_point_of(selected.position)
        if self._editor.set_shape(self._mind_map, selected.node_id, shape):
            self._redraw_keeping_in_place(selected, anchor)

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

    # --- dragging -----------------------------------------------------------

    def toggle_drag(self) -> None:
        """Allows or locks dragging the map around with the mouse."""
        self.set_drag_enabled(not self._canvas.drag_enabled)

    def set_drag_enabled(self, enabled: bool) -> None:
        self._canvas.set_drag_enabled(enabled)
        self._update_view_toolbar()

    @property
    def drag_enabled(self) -> bool:
        return self._canvas.drag_enabled

    def apply_theme(self, theme: Theme) -> None:
        self._finish_editing()
        self._theme = theme
        self._canvas.apply_theme(theme)
        self._toolbar.apply_theme(theme)
        self._style_toolbar.apply_theme(theme)
        self._view_toolbar.apply_theme(theme)
        self._redraw()  # fonts may change, so node sizes and layout change too

    # --- internals ----------------------------------------------------------

    def _on_node_click(self, node_id: str | None) -> None:
        if node_id is not None and node_id == self._title_editor.node_id:
            return  # a click on the title being edited keeps editing
        self._finish_editing()
        if self._mind_map is None or node_id == self._selection.selected_id:
            return
        self._selection.select(node_id)
        self._canvas.draw_map(self._mind_map, node_id)  # selection doesn't change sizes, so no new layout
        self._update_toolbar()

    def _on_node_double_click(self, node_id: str) -> None:
        if self._mind_map is None:
            return
        if node_id != self._selection.selected_id:
            self._on_node_click(node_id)
        self.edit_selected_title()

    def _finish_editing(self) -> None:
        """Closes the title editor if it is open, saving what was typed."""
        self._title_editor.finish()

    def _rename_node(self, node_id: str, title: str) -> None:
        """Saves an edited title. The node's size can change, so the layout runs again with the node kept in place."""
        node = self._mind_map.find_node(node_id) if self._mind_map is not None else None
        if node is None:
            return
        anchor = self._canvas.window_point_of(node.position)
        if self._editor.set_title(self._mind_map, node_id, title):
            self._redraw_keeping_in_place(node, anchor)

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

    def _update_view_toolbar(self) -> None:
        canvas = self._canvas
        self._view_toolbar.show_zoom(canvas.zoom, can_zoom_out=canvas.can_zoom_out, can_zoom_in=canvas.can_zoom_in)
        self._view_toolbar.show_drag(canvas.drag_enabled)

    def _update_toolbar(self) -> None:
        selected = self._selected_node()
        can_delete = selected is not None and self._editor.can_delete(self._mind_map, selected.node_id)
        can_edit = selected is not None and not self._title_editor.is_editing
        self._toolbar.set_enabled(insert=selected is not None, edit=can_edit, delete=can_delete)
        if selected is None:
            self._style_toolbar.show_style(None, None)
        else:
            self._style_toolbar.show_style(selected.style.color, selected.style.shape)

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
