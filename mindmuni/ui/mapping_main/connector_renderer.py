import tkinter as tk

from mindmuni.model.geometry import Size
from mindmuni.model.node import Node
from mindmuni.model.theme import Theme

CONNECTOR_WIDTH = 2
CONNECTOR_TAG = "connector"


class ConnectorRenderer:
    """Draws the S-curve from a parent's right edge to a child's left edge."""

    def __init__(self, canvas: tk.Canvas, theme: Theme) -> None:
        self._canvas = canvas
        self._line_color = theme.palette.connector_line

    def draw(self, parent: Node, parent_size: Size, child: Node, child_size: Size) -> None:
        start_x, start_y = parent.position.x + parent_size.width / 2, parent.position.y
        end_x, end_y = child.position.x - child_size.width / 2, child.position.y
        bend_x = (start_x + end_x) / 2
        self._canvas.create_line(
            start_x, start_y,
            bend_x, start_y,
            bend_x, end_y,
            end_x, end_y,
            smooth=True,
            width=CONNECTOR_WIDTH,
            fill=self._line_color,
            tags=(CONNECTOR_TAG,),
        )
