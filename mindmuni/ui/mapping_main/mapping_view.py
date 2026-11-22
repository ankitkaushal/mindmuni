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
from mindmuni.ui.text_editor.text_editor_view import TextEditorView

MAP_VIEW_ID = "map"
TEXT_TO_MAP_WIDTH = 1 / 3  # the text area opens a third as wide as the map
TEXT_BORDER_WIDTH = 1
RESIZE_TIMEOUT_MS = 1000  # the map's width is freed by then even if the window manager never resized the window
CANVAS_COLUMN, TEXT_BORDER_COLUMN, TEXT_COLUMN = 0, 2, 3  # column 1 is the map's vertical scrollbar


class MappingView(View):
    """Mapping main component: lays out a MindMap, shows it on a scrollable canvas, and edits it.

    The edit toolbar floats over the canvas's bottom-right corner, the style toolbar (colour and shape) over its
    bottom-left corner and the view toolbar (zoom and the drag lock) over its top-right corner; all stay there
    when the window is resized. They are hidden until the first map is shown. Dragging the map around is locked until the view toolbar's Drag button turns it on.

    A node's title is edited in place (double-click, F2 or the Edit button), by typing into its drawn text.
    The Edit button is disabled while a title is being edited.
    Every action that redraws first stops editing and saves what was typed, because a redraw replaces that text.

    The view toolbar's Text button opens the selected node's note in a TextEditorView to the right of the map,
    a third as wide as the map. The window grows to the right by that much, so everything already on screen,
    the map included, stays where it is; it shrinks back the same way when the text area closes. The text area
    keeps that width; if the window is resized while it is open, the map takes the change. Selecting another node shows its note; clicking empty space keeps the last
    one. The edited note is stored in its node by finish_editing(), which every action (and the app, before
    saving the file) calls first, and when the text area closes.
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
        self._canvas.on_before_zoom(self.finish_editing)
        self._canvas.on_zoom_changed(self._update_view_toolbar)
        self._layout = TreeLayout(self._canvas.measure_node)
        self._title_editor = TitleEditor(
            self._canvas, on_commit=self._rename_node, on_editing_changed=lambda _editing: self._update_toolbar()
        )
        self._toolbar = MapToolbar(
            self, on_insert=self.insert_node, on_edit=self.edit_selected_title, on_delete=self.delete_selected_node
        )
        self._style_toolbar = StyleToolbar(self, on_color=self.set_selected_color, on_shape=self.set_selected_shape)
        self._view_toolbar = ViewToolbar(
            self,
            on_zoom_out=self.zoom_out,
            on_reset=self.reset_zoom,
            on_zoom_in=self.zoom_in,
            on_toggle_drag=self.toggle_drag,
            on_toggle_text=self.toggle_text,
        )
        self._text_editor = TextEditorView(self, theme)
        self._text_editor.grid_propagate(False)  # its width is set when it opens, not by its contents
        self._text_border = tk.Frame(self, width=TEXT_BORDER_WIDTH, borderwidth=0)
        self._text_open = False
        self._note_node_id: str | None = None  # the node whose note the text area shows
        self._resize_target: int | None = None  # this view's width once the window has resized, while waiting
        self._unpin_job: str | None = None
        self.bind("<Configure>", self._on_resized, add="+")
        self._update_view_toolbar()
        self._theme = theme
        self.apply_theme(theme)

    def show_map(self, mind_map: MindMap) -> None:
        """Shows the map with its root selected, centred on the root."""
        self._title_editor.cancel()  # the node being edited belongs to the old map
        self._note_node_id = None  # and so does the note being edited
        self._mind_map = mind_map
        self._show_toolbars()
        self._selection.select(mind_map.root.node_id)
        self._show_selected_note()
        self._redraw()
        self.after_idle(lambda: self._canvas.center_on(mind_map.root.position))

    def set_layout(self, layout: MapLayout) -> None:
        """Changes the shown map's layout style (RIGHT or BALANCED) and redraws it around the root."""
        if self._mind_map is None or self._mind_map.style.layout is layout:
            return
        self.finish_editing()
        self._mind_map.style.layout = layout
        self._redraw()
        self.after_idle(lambda: self._canvas.center_on(self._mind_map.root.position))

    # --- editing ------------------------------------------------------------

    def finish_editing(self) -> None:
        """Closes the title editor if it is open and stores the note being edited, saving what was typed into the
        map. Call it before saving the map."""
        self._title_editor.finish()
        self._store_note()

    def on_hide(self) -> None:
        self.finish_editing()

    def insert_node(self) -> None:
        """Adds a child to the selected node, selects it and opens its title for editing, ready to type over."""
        self.finish_editing()
        selected = self._selected_node()
        if selected is None:
            return
        anchor = self._canvas.window_point_of(selected.position)
        child = self._editor.add_child(self._mind_map, selected.node_id)
        self._selection.select(child.node_id)
        self._show_selected_note()
        self._redraw_keeping_in_place(selected, anchor)
        self.edit_selected_title(select_all=True)

    def edit_selected_title(self, select_all: bool = False) -> None:
        """Opens the selected node's title for editing in place. Enter saves, Shift+Enter adds a line, Esc cancels."""
        self.finish_editing()
        selected = self._selected_node()
        if selected is None:
            return
        self._title_editor.start(selected, self._theme, select_all)

    def delete_selected_node(self) -> None:
        """Deletes the selected node with its subtree and selects its parent. Does nothing for the root."""
        self.finish_editing()
        selected = self._selected_node()
        if selected is None or not self._editor.can_delete(self._mind_map, selected.node_id):
            return
        parent = self._mind_map.parent_of(selected.node_id)
        anchor = self._canvas.window_point_of(parent.position)
        self._editor.delete_node(self._mind_map, selected.node_id)
        self._selection.select(parent.node_id)
        self._show_selected_note()
        self._redraw_keeping_in_place(parent, anchor)

    def set_selected_color(self, color: NodeColor) -> None:
        """Changes the selected node's colour. Sizes don't change, so the map is only redrawn."""
        self.finish_editing()
        selected = self._selected_node()
        if selected is None or not self._editor.set_color(self._mind_map, selected.node_id, color):
            return
        self._canvas.draw_map(self._mind_map, selected.node_id)
        self._update_toolbar()

    def set_selected_shape(self, shape: NodeShape) -> None:
        """Changes the selected node's shape. Its size can change, so the layout runs again with the node kept in place."""
        self.finish_editing()
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

    # --- text area ----------------------------------------------------------

    def toggle_text(self) -> None:
        """Opens or closes the text area beside the map."""
        self.set_text_open(not self._text_open)

    def set_text_open(self, is_open: bool) -> None:
        """Opens the selected node's note to the right of the map, ready for typing, or stores the note and closes
        it. The window widens or narrows on its right by the text area's width, so nothing else moves."""
        if is_open == self._text_open:
            return
        self.finish_editing()
        self.update_idletasks()  # current widths, for resizing the window
        self._pin_map_width()
        self._text_open = is_open
        if is_open:
            text_width = round(self._canvas.winfo_width() * TEXT_TO_MAP_WIDTH)
            self._text_editor.configure(width=text_width)
            self._text_border.grid(row=0, column=TEXT_BORDER_COLUMN, rowspan=2, sticky="ns")
            self._text_editor.grid(row=0, column=TEXT_COLUMN, rowspan=2, sticky="nsew")
            self._widen_window(text_width + TEXT_BORDER_WIDTH)
            self._note_node_id = None
            self._show_selected_note(focus=True)
        else:
            text_width = self._text_editor.winfo_width() + self._text_border.winfo_width()
            self._text_border.grid_remove()
            self._text_editor.grid_remove()
            self._widen_window(-text_width)
            self._note_node_id = None
        self._update_view_toolbar()

    @property
    def text_open(self) -> bool:
        return self._text_open

    def apply_theme(self, theme: Theme) -> None:
        self.finish_editing()
        self._theme = theme
        self._canvas.apply_theme(theme)
        self._toolbar.apply_theme(theme)
        self._style_toolbar.apply_theme(theme)
        self._view_toolbar.apply_theme(theme)
        self._text_editor.apply_theme(theme)
        self._text_border.configure(background=theme.palette.connector_line)
        self._redraw()  # fonts may change, so node sizes and layout change too

    # --- internals ----------------------------------------------------------

    def _on_node_click(self, node_id: str | None) -> None:
        if node_id is not None and node_id == self._title_editor.node_id:
            return  # a click on the title being edited keeps editing
        self.finish_editing()
        if self._mind_map is None or node_id == self._selection.selected_id:
            return
        self._selection.select(node_id)
        self._show_selected_note()
        self._canvas.draw_map(self._mind_map, node_id)  # selection doesn't change sizes, so no new layout
        self._update_toolbar()

    def _on_node_double_click(self, node_id: str) -> None:
        if self._mind_map is None:
            return
        if node_id != self._selection.selected_id:
            self._on_node_click(node_id)
        self.edit_selected_title()


    def _rename_node(self, node_id: str, title: str) -> None:
        """Saves an edited title. The node's size can change, so the layout runs again with the node kept in place."""
        node = self._mind_map.find_node(node_id) if self._mind_map is not None else None
        if node is None:
            return
        anchor = self._canvas.window_point_of(node.position)
        if self._editor.set_title(self._mind_map, node_id, title):
            self._redraw_keeping_in_place(node, anchor)

    def _widen_window(self, extra: int) -> None:
        """Makes the window `extra` pixels wider (narrower if negative) on its right, keeping its position and
        height, so everything already in it stays put. It doesn't grow past the screen's right edge; if it can't
        grow enough, the map gives up the rest once its width is unpinned."""
        window = self.winfo_toplevel()
        width = window.winfo_width() + extra
        if extra > 0:
            width = min(width, window.winfo_screenwidth() - window.winfo_rootx())
        width = max(width, 1)
        self._resize_target = self.winfo_width() + width - window.winfo_width()
        window.geometry(f"{width}x{window.winfo_height()}")

    def _pin_map_width(self) -> None:
        """Holds the map's column at its current width until the window has resized (see _on_resized()).

        The window manager resizes the window a moment after it's asked to. Meanwhile the text area is laid out
        past the window's right edge, out of sight, instead of taking the map's space (which flashed white), and
        on closing the map doesn't stretch into the space the text area leaves.
        """
        self.columnconfigure(CANVAS_COLUMN, weight=0, minsize=self._canvas.winfo_width())
        if self._unpin_job is not None:
            self.after_cancel(self._unpin_job)
        self._unpin_job = self.after(RESIZE_TIMEOUT_MS, self._unpin_map_width)

    def _unpin_map_width(self) -> None:
        """Lets the map's column take any change in the window's width again."""
        self.columnconfigure(CANVAS_COLUMN, weight=1, minsize=0)
        self._resize_target = None
        if self._unpin_job is not None:
            self.after_cancel(self._unpin_job)
            self._unpin_job = None

    def _on_resized(self, event: tk.Event) -> None:
        if self._resize_target is not None and event.width == self._resize_target:
            self._unpin_map_width()

    def _show_selected_note(self, focus: bool = False) -> None:
        """Shows the selected node's note in the text area, if it is open and the node isn't already shown.
        With nothing selected, the last note stays. Store the shown note first (finish_editing())."""
        selected = self._selected_node()
        if not self._text_open or selected is None or selected.node_id == self._note_node_id:
            return
        self._note_node_id = selected.node_id
        self._text_editor.show_note(selected.note, focus=focus)

    def _store_note(self) -> None:
        """Stores the text area's note in the node it belongs to, if the area is open and the node still exists."""
        if not self._text_open or self._note_node_id is None or self._mind_map is None:
            return
        if self._mind_map.find_node(self._note_node_id) is not None:
            self._editor.set_note(self._mind_map, self._note_node_id, self._text_editor.note())

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

    def _show_toolbars(self) -> None:
        """Pins the toolbars over the canvas. They stay hidden until the first map is shown."""
        for toolbar in (self._toolbar, self._style_toolbar, self._view_toolbar):
            toolbar.pin_to(self._canvas)

    def _update_view_toolbar(self) -> None:
        canvas = self._canvas
        self._view_toolbar.show_zoom(canvas.zoom, can_zoom_out=canvas.can_zoom_out, can_zoom_in=canvas.can_zoom_in)
        self._view_toolbar.show_drag(canvas.drag_enabled)
        self._view_toolbar.show_text(self._text_open)

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
        canvas.grid(row=0, column=CANVAS_COLUMN, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=CANVAS_COLUMN, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(CANVAS_COLUMN, weight=1)  # the map takes any change in the window's width
        return canvas
