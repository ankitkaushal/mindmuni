import sys
import tkinter as tk
from collections.abc import Callable, Iterator

from mindmuni.core.tree_layout import visible_children
from mindmuni.model.geometry import Point, Size
from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node
from mindmuni.model.theme import Theme
from mindmuni.ui.mapping_main.connector_renderer import ConnectorRenderer
from mindmuni.ui.mapping_main.node_renderer import NodeRenderer, node_id_from_tags

SCROLL_MARGIN = 120
WHEEL_SCROLL_UNITS = 3

MIN_ZOOM = 0.25
MAX_ZOOM = 3.0
ZOOM_STEP = 1.2  # each zoom in multiplies the zoom by this, each zoom out divides by it
CONTROL_MASK = 0x0004
SHIFT_MASK = 0x0001
CLICK_TOLERANCE = 3  # a press and release closer than this (in pixels) is a click, not a pan

NodeClickHandler = Callable[[str | None], None]


def iter_visible_nodes(root: Node) -> Iterator[Node]:
    pending = [root]
    while pending:
        node = pending.pop()
        yield node
        pending.extend(reversed(visible_children(node)))


class MapCanvas(tk.Canvas):
    """Scrollable, pannable, zoomable canvas that draws an already laid-out MindMap.

    Node positions stay in map units; the canvas shows map point p at canvas point p * zoom.
    Zooming only redraws, it never re-runs the layout or changes Node.position.

    Left-click on a node reports its id to the click handler. Left-drag on empty space (or middle-drag
    anywhere) pans; a left-click on empty space without dragging reports None.
    """

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, highlightthickness=0, borderwidth=0)
        self._theme: Theme | None = None
        self._zoom = 1.0
        self._mind_map: MindMap | None = None
        self._selected_id: str | None = None
        self._on_node_click: NodeClickHandler = lambda _node_id: None
        self._press_point: tuple[int, int] | None = None  # where an empty-space left press started, for panning
        self._node_renderer: NodeRenderer | None = None
        self._connector_renderer: ConnectorRenderer | None = None
        self._bind_panning()
        self._bind_mouse_wheel()

    @property
    def zoom(self) -> float:
        return self._zoom

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.configure(background=theme.palette.canvas_background)
        self._build_renderers()

    def measure_node(self, node: Node) -> Size:
        """Size in map units (zoom 1), for the layout."""
        return self._require_node_renderer().measure(node)

    def on_node_click(self, handler: NodeClickHandler) -> None:
        """handler(node_id) on a click on a node; handler(None) on a click on empty space."""
        self._on_node_click = handler

    def draw_map(self, mind_map: MindMap, selected_id: str | None = None) -> None:
        self._mind_map = mind_map
        self._selected_id = selected_id
        self.delete("all")
        self._draw_connectors(mind_map.root)
        self._draw_nodes(mind_map.root)
        self._update_scroll_region()

    def center_on(self, point: Point) -> None:
        """Scrolls so the map point (in map units) is in the middle of the window."""
        self._scroll_to(point, self.winfo_width() / 2, self.winfo_height() / 2)

    def window_point_of(self, point: Point) -> tuple[float, float]:
        """Where the map point (in map units) currently appears in the window, in window pixels."""
        return point.x * self._zoom - self.canvasx(0), point.y * self._zoom - self.canvasy(0)

    def scroll_point_to(self, point: Point, window_x: float, window_y: float) -> None:
        """Scrolls so the map point (in map units) appears at the window point, e.g. to undo a layout shift."""
        self._scroll_to(point, window_x, window_y)

    def zoom_in(self) -> None:
        self.set_zoom(self._zoom * ZOOM_STEP)

    def zoom_out(self) -> None:
        self.set_zoom(self._zoom / ZOOM_STEP)

    def reset_zoom(self) -> None:
        self.set_zoom(1.0)

    def set_zoom(self, zoom: float, anchor_x: float | None = None, anchor_y: float | None = None) -> None:
        """Zooms, keeping the map point under the window point (anchor_x, anchor_y) where it is.

        The anchor defaults to the middle of the window. The zoom is clamped to MIN_ZOOM..MAX_ZOOM.
        """
        zoom = min(max(zoom, MIN_ZOOM), MAX_ZOOM)
        if zoom == self._zoom:
            return
        if anchor_x is None or anchor_y is None:
            anchor_x, anchor_y = self.winfo_width() / 2, self.winfo_height() / 2
        anchor = Point(self.canvasx(anchor_x) / self._zoom, self.canvasy(anchor_y) / self._zoom)
        self._zoom = zoom
        self._build_renderers()
        if self._mind_map is not None:
            self.draw_map(self._mind_map, self._selected_id)
            self._scroll_to(anchor, anchor_x, anchor_y)

    def _build_renderers(self) -> None:
        if self._theme is None:
            return
        self._node_renderer = NodeRenderer(self, self._theme, self._zoom)
        self._connector_renderer = ConnectorRenderer(self, self._theme, self._zoom)

    def _scroll_to(self, point: Point, window_x: float, window_y: float) -> None:
        """Scrolls so the map point (in map units) appears at the window point."""
        left, top, right, bottom = (float(value) for value in self.cget("scrollregion").split())
        self.xview_moveto((point.x * self._zoom - left - window_x) / (right - left))
        self.yview_moveto((point.y * self._zoom - top - window_y) / (bottom - top))

    # --- drawing ------------------------------------------------------------

    def _draw_connectors(self, root: Node) -> None:
        connector_renderer = self._connector_renderer
        for parent in iter_visible_nodes(root):
            for child in visible_children(parent):
                connector_renderer.draw(parent, self.measure_node(parent), child, self.measure_node(child))

    def _draw_nodes(self, root: Node) -> None:
        node_renderer = self._require_node_renderer()
        for node in iter_visible_nodes(root):
            node_renderer.draw(
                node, grows_left=node.position.x < root.position.x, selected=node.node_id == self._selected_id
            )

    def _update_scroll_region(self) -> None:
        left, top, right, bottom = self.bbox("all") or (0, 0, 0, 0)
        self.configure(
            scrollregion=(left - SCROLL_MARGIN, top - SCROLL_MARGIN, right + SCROLL_MARGIN, bottom + SCROLL_MARGIN)
        )

    def _require_node_renderer(self) -> NodeRenderer:
        if self._node_renderer is None:
            raise RuntimeError("MapCanvas.apply_theme() must be called before drawing")
        return self._node_renderer

    # --- navigation ---------------------------------------------------------

    def _bind_panning(self) -> None:
        self.bind("<ButtonPress-1>", self._on_left_press)
        self.bind("<B1-Motion>", self._on_left_drag)
        self.bind("<ButtonRelease-1>", self._on_left_release)
        self.bind("<ButtonPress-2>", lambda event: self.scan_mark(event.x, event.y))
        self.bind("<B2-Motion>", lambda event: self.scan_dragto(event.x, event.y, gain=1))

    def _on_left_press(self, event: tk.Event) -> None:
        node_id = self._node_id_at(event.x, event.y)
        if node_id is not None:
            self._press_point = None
            self._on_node_click(node_id)
            return
        self._press_point = (event.x, event.y)
        self.scan_mark(event.x, event.y)

    def _on_left_drag(self, event: tk.Event) -> None:
        if self._press_point is not None:
            self.scan_dragto(event.x, event.y, gain=1)

    def _on_left_release(self, event: tk.Event) -> None:
        if self._press_point is None:
            return
        start_x, start_y = self._press_point
        self._press_point = None
        if abs(event.x - start_x) <= CLICK_TOLERANCE and abs(event.y - start_y) <= CLICK_TOLERANCE:
            self._on_node_click(None)

    def _node_id_at(self, window_x: int, window_y: int) -> str | None:
        """The node drawn at the window point, if any (the topmost item there that belongs to a node)."""
        x, y = self.canvasx(window_x), self.canvasy(window_y)
        for item in reversed(self.find_overlapping(x, y, x, y)):
            node_id = node_id_from_tags(self.gettags(item))
            if node_id is not None:
                return node_id
        return None

    def _bind_mouse_wheel(self) -> None:
        if sys.platform.startswith("linux"):
            self.bind("<Button-4>", lambda event: self._scroll(event, -1))
            self.bind("<Button-5>", lambda event: self._scroll(event, 1))
        else:
            self.bind("<MouseWheel>", lambda event: self._scroll(event, -1 if event.delta > 0 else 1))

    def _scroll(self, event: tk.Event, direction: int) -> None:
        """direction is -1 for wheel up, 1 for wheel down. Ctrl+wheel zooms around the mouse pointer."""
        if event.state & CONTROL_MASK:
            factor = ZOOM_STEP if direction < 0 else 1 / ZOOM_STEP
            self.set_zoom(self._zoom * factor, event.x, event.y)
            return
        shift_held = bool(event.state & SHIFT_MASK)
        scroll = self.xview_scroll if shift_held else self.yview_scroll
        scroll(direction * WHEEL_SCROLL_UNITS, "units")
