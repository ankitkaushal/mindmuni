import tkinter as tk

from mindmuni.model.geometry import Size
from mindmuni.model.node import Node
from mindmuni.model.theme import Theme

CONNECTOR_WIDTH = 2
CONNECTOR_TAG = "connector"


class ConnectorRenderer:
    """Draws the S-curve between a parent and a child, on whichever side of the parent the child is.

    Right of the parent: from the parent's right edge to the child's left edge.
    Left of the parent (balanced maps): from the parent's left edge to the child's right edge.
    """

    def __init__(self, canvas: tk.Canvas, theme: Theme, zoom: float = 1.0) -> None:
        self._canvas = canvas
        self._line_color = theme.palette.connector_line
        self._zoom = zoom  # positions and sizes are in map units; the canvas shows them multiplied by this

    def draw(self, parent: Node, parent_size: Size, child: Node, child_size: Size) -> None:
        direction = 1 if child.position.x >= parent.position.x else -1
        start_x, start_y = parent.position.x + direction * parent_size.width / 2, parent.position.y
        end_x, end_y = child.position.x - direction * child_size.width / 2, child.position.y
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
