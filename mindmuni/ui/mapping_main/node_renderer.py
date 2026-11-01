import tkinter as tk
from tkinter import font as tkfont

from mindmuni.model.geometry import Size
from mindmuni.model.node import Node
from mindmuni.model.node_style import NodeShape
from mindmuni.model.theme import Theme
from mindmuni.utils import shape_geometry
from mindmuni.utils.color_utils import contrast_text_color, darken

MIN_NODE_HEIGHT = 36
MIN_TEXT_WIDTH = 40
HORIZONTAL_PADDING = 14
VERTICAL_PADDING = 8
CORNER_RADIUS = 10
OUTLINE_WIDTH = 2
OUTLINE_DARKEN_FRACTION = 0.3
BADGE_RADIUS = 9

# Shapes that cut into their bounding box need a bigger box so the title still fits inside.
SHAPE_SCALE: dict[NodeShape, tuple[float, float]] = {
    NodeShape.RECTANGLE: (1.0, 1.0),
    NodeShape.ROUNDED_RECTANGLE: (1.0, 1.0),
    NodeShape.ELLIPSE: (1.3, 1.3),
    NodeShape.DIAMOND: (1.7, 1.7),
    NodeShape.HEXAGON: (1.15, 1.0),
    NodeShape.CLOUD: (1.4, 1.4),
}

NODE_TAG = "node"


def node_tag(node_id: str) -> str:
    """Canvas tag shared by every item that belongs to one node (for hit-testing later)."""
    return f"node:{node_id}"


class NodeRenderer:
    """Measures and draws a single node: its shape, title and collapsed-children badge."""

    def __init__(self, canvas: tk.Canvas, theme: Theme) -> None:
        self._canvas = canvas
        self._palette = theme.palette
        self._font = tkfont.Font(root=canvas, family=theme.fonts.family, size=theme.fonts.node_title_size)
        self._badge_font = tkfont.Font(root=canvas, family=theme.fonts.family, size=max(theme.fonts.node_title_size - 3, 7))

    def measure(self, node: Node) -> Size:
        text_size = self._measure_title(node.title)
        base_width = max(text_size.width, MIN_TEXT_WIDTH) + 2 * HORIZONTAL_PADDING
        base_height = max(text_size.height + 2 * VERTICAL_PADDING, MIN_NODE_HEIGHT)
        width_scale, height_scale = SHAPE_SCALE[node.style.shape]
        return Size(base_width * width_scale, base_height * height_scale)

    def draw(self, node: Node) -> None:
        fill_color = self._palette.color_for(node.style.color)
        tags = (NODE_TAG, node_tag(node.node_id))
        self._draw_shape(node, fill_color, tags)
        self._draw_title(node, fill_color, tags)
        if node.collapsed and node.children:
            self._draw_collapsed_badge(node, tags)

    def _measure_title(self, title: str) -> Size:
        lines = title.splitlines() or [""]
        width = max(self._font.measure(line) for line in lines)
        height = self._font.metrics("linespace") * len(lines)
        return Size(width, height)

    def _draw_shape(self, node: Node, fill_color: str, tags: tuple[str, ...]) -> None:
        size = self.measure(node)
        center_x, center_y = node.position.x, node.position.y
        half_width, half_height = size.width / 2, size.height / 2
        style = {"fill": fill_color, "outline": darken(fill_color, OUTLINE_DARKEN_FRACTION), "width": OUTLINE_WIDTH, "tags": tags}
        match node.style.shape:
            case NodeShape.RECTANGLE:
                self._canvas.create_rectangle(*shape_geometry.bounding_box(center_x, center_y, half_width, half_height), **style)
            case NodeShape.ELLIPSE:
                self._canvas.create_oval(*shape_geometry.bounding_box(center_x, center_y, half_width, half_height), **style)
            case NodeShape.ROUNDED_RECTANGLE:
                points = shape_geometry.rounded_rectangle(center_x, center_y, half_width, half_height, CORNER_RADIUS)
                self._canvas.create_polygon(points, smooth=True, **style)
            case NodeShape.DIAMOND:
                self._canvas.create_polygon(shape_geometry.diamond(center_x, center_y, half_width, half_height), **style)
            case NodeShape.HEXAGON:
                self._canvas.create_polygon(shape_geometry.hexagon(center_x, center_y, half_width, half_height), **style)
            case NodeShape.CLOUD:
                self._canvas.create_polygon(shape_geometry.cloud(center_x, center_y, half_width, half_height), smooth=True, **style)

    def _draw_title(self, node: Node, fill_color: str, tags: tuple[str, ...]) -> None:
        self._canvas.create_text(
            node.position.x,
            node.position.y,
            text=node.title,
            font=self._font,
            fill=contrast_text_color(fill_color),
            justify="center",
            tags=tags,
        )

    def _draw_collapsed_badge(self, node: Node, tags: tuple[str, ...]) -> None:
        badge_x = node.position.x + self.measure(node).width / 2
        badge_y = node.position.y
        self._canvas.create_oval(
            *shape_geometry.bounding_box(badge_x, badge_y, BADGE_RADIUS, BADGE_RADIUS),
            fill=self._palette.background,
            outline=self._palette.connector_line,
            width=OUTLINE_WIDTH,
            tags=tags,
        )
        self._canvas.create_text(
            badge_x, badge_y, text=str(len(node.children)), font=self._badge_font, fill=self._palette.foreground, tags=tags
        )
