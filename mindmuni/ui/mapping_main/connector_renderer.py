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

    def __init__(self, canvas: tk.Canvas, theme: Theme) -> None:
        self._canvas = canvas
        self._line_color = theme.palette.connector_line

    def draw(self, parent: Node, parent_size: Size, child: Node, child_size: Size) -> None:
        direction = 1 if child.position.x >= parent.position.x else -1
        start_x, start_y = parent.position.x + direction * parent_size.width / 2, parent.position.y
        end_x, end_y = child.position.x - direction * child_size.width / 2, child.position.y
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
