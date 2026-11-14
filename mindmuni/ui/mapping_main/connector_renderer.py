import tkinter as tk

from mindmuni.model.node import Node
from mindmuni.model.theme import Theme
from mindmuni.ui.mapping_main.node_renderer import NodeRenderer

CONNECTOR_WIDTH = 2
CONNECTOR_TAG = "connector"


class ConnectorRenderer:
    """Draws the S-curve between a parent and a child, on whichever side of the parent the child is.

    Right of the parent: from the parent's right edge to the child's left edge.
    Left of the parent (balanced maps): from the parent's left edge to the child's right edge.
    The edges are where each node's outline crosses its centre height (NodeRenderer.edge_half_width).
    """

    def __init__(self, canvas: tk.Canvas, theme: Theme, node_renderer: NodeRenderer, zoom: float = 1.0) -> None:
        self._canvas = canvas
        self._node_renderer = node_renderer
        self._line_color = theme.palette.connector_line
        self._zoom = zoom  # positions and sizes are in map units; the canvas shows them multiplied by this

    def draw(self, parent: Node, child: Node) -> None:
        direction = 1 if child.position.x >= parent.position.x else -1
        start_x = parent.position.x + direction * self._node_renderer.edge_half_width(parent)
        end_x = child.position.x - direction * self._node_renderer.edge_half_width(child)
        start_y, end_y = parent.position.y, child.position.y
        bend_x = (start_x + end_x) / 2
        zoom = self._zoom
        self._canvas.create_line(
            start_x * zoom, start_y * zoom,
            bend_x * zoom, start_y * zoom,
            bend_x * zoom, end_y * zoom,
            end_x * zoom, end_y * zoom,
            smooth=True,
            width=max(CONNECTOR_WIDTH * zoom, 1.0),
            fill=self._line_color,
            tags=(CONNECTOR_TAG,),
        )
