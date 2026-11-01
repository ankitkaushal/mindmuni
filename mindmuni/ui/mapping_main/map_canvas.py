import sys
import tkinter as tk
from collections.abc import Iterator

from mindmuni.core.tree_layout import visible_children
from mindmuni.model.geometry import Point, Size
from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node
from mindmuni.model.theme import Theme
from mindmuni.ui.mapping_main.connector_renderer import ConnectorRenderer
from mindmuni.ui.mapping_main.node_renderer import NodeRenderer

SCROLL_MARGIN = 120
WHEEL_SCROLL_UNITS = 3


def iter_visible_nodes(root: Node) -> Iterator[Node]:
    pending = [root]
    while pending:
        node = pending.pop()
        yield node
        pending.extend(reversed(visible_children(node)))


class MapCanvas(tk.Canvas):
    """Scrollable, pannable canvas that draws an already laid-out MindMap."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, highlightthickness=0, borderwidth=0)
        self._node_renderer: NodeRenderer | None = None
        self._connector_renderer: ConnectorRenderer | None = None
        self._bind_panning()
        self._bind_mouse_wheel()

    def apply_theme(self, theme: Theme) -> None:
        self.configure(background=theme.palette.canvas_background)
        self._node_renderer = NodeRenderer(self, theme)
        self._connector_renderer = ConnectorRenderer(self, theme)

    def measure_node(self, node: Node) -> Size:
        return self._require_node_renderer().measure(node)

    def draw_map(self, mind_map: MindMap) -> None:
        self.delete("all")
        self._draw_connectors(mind_map.root)
        self._draw_nodes(mind_map.root)
        self._update_scroll_region()

    def center_on(self, point: Point) -> None:
        left, top, right, bottom = (float(value) for value in self.cget("scrollregion").split())
        self.xview_moveto((point.x - left - self.winfo_width() / 2) / (right - left))
        self.yview_moveto((point.y - top - self.winfo_height() / 2) / (bottom - top))

    # --- drawing ------------------------------------------------------------

    def _draw_connectors(self, root: Node) -> None:
        connector_renderer = self._connector_renderer
        for parent in iter_visible_nodes(root):
            for child in visible_children(parent):
                connector_renderer.draw(parent, self.measure_node(parent), child, self.measure_node(child))

    def _draw_nodes(self, root: Node) -> None:
        node_renderer = self._require_node_renderer()
        for node in iter_visible_nodes(root):
            node_renderer.draw(node)

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
        self.bind("<ButtonPress-1>", lambda event: self.scan_mark(event.x, event.y))
        self.bind("<B1-Motion>", lambda event: self.scan_dragto(event.x, event.y, gain=1))

    def _bind_mouse_wheel(self) -> None:
        if sys.platform.startswith("linux"):
            self.bind("<Button-4>", lambda event: self._scroll(event, -1))
            self.bind("<Button-5>", lambda event: self._scroll(event, 1))
        else:
            self.bind("<MouseWheel>", lambda event: self._scroll(event, -1 if event.delta > 0 else 1))

    def _scroll(self, event: tk.Event, direction: int) -> None:
        shift_held = bool(event.state & 0x0001)
        scroll = self.xview_scroll if shift_held else self.yview_scroll
        scroll(direction * WHEEL_SCROLL_UNITS, "units")
