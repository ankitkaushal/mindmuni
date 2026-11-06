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
SELECTED_OUTLINE_WIDTH = 4
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
NODE_TAG_PREFIX = "node:"


def node_tag(node_id: str) -> str:
    """Canvas tag shared by every item that belongs to one node, used for hit-testing."""
    return f"{NODE_TAG_PREFIX}{node_id}"


def node_id_from_tags(tags: tuple[str, ...]) -> str | None:
    """The node id in a canvas item's tags, or None if the item isn't part of a node."""
    return next((tag.removeprefix(NODE_TAG_PREFIX) for tag in tags if tag.startswith(NODE_TAG_PREFIX)), None)


class NodeRenderer:
    """Measures and draws a single node: its shape, title and collapsed-children badge.

    measure() works in map units (zoom 1), so the layout and the saved positions never depend on the zoom.
    draw() scales positions, sizes and fonts by the zoom, so the canvas shows map point p at p * zoom.
    """

    def __init__(self, canvas: tk.Canvas, theme: Theme, zoom: float = 1.0) -> None:
        self._canvas = canvas
        self._palette = theme.palette
        self._zoom = zoom
        title_size = theme.fonts.node_title_size
        badge_size = max(title_size - 3, 7)
        self._font = tkfont.Font(root=canvas, family=theme.fonts.family, size=title_size)
        # Rounded down so the zoomed text never outgrows its zoomed box.
        self._drawn_font = tkfont.Font(root=canvas, family=theme.fonts.family, size=max(int(title_size * zoom), 1))
        self._badge_font = tkfont.Font(root=canvas, family=theme.fonts.family, size=max(int(badge_size * zoom), 1))

    def measure(self, node: Node) -> Size:
        text_size = self._measure_title(node.title)
        base_width = max(text_size.width, MIN_TEXT_WIDTH) + 2 * HORIZONTAL_PADDING
        base_height = max(text_size.height + 2 * VERTICAL_PADDING, MIN_NODE_HEIGHT)
        width_scale, height_scale = SHAPE_SCALE[node.style.shape]
        return Size(base_width * width_scale, base_height * height_scale)

    def draw(self, node: Node, grows_left: bool = False, selected: bool = False) -> None:
        """grows_left: the node's children are drawn to its left, so the collapsed badge goes on that side.
        selected: draw the outline in the theme's selection colour, thicker.
        """
        fill_color = self._palette.color_for(node.style.color)
        tags = (NODE_TAG, node_tag(node.node_id))
        self._draw_shape(node, fill_color, selected, tags)
        self._draw_title(node, fill_color, tags)
        if node.collapsed and node.children:
            self._draw_collapsed_badge(node, grows_left, tags)

    def _measure_title(self, title: str) -> Size:
        lines = title.splitlines() or [""]
        width = max(self._font.measure(line) for line in lines)
        height = self._font.metrics("linespace") * len(lines)
        return Size(width, height)

    def _draw_shape(self, node: Node, fill_color: str, selected: bool, tags: tuple[str, ...]) -> None:
        size = self.measure(node)
        zoom = self._zoom
        center_x, center_y = node.position.x * zoom, node.position.y * zoom
        half_width, half_height = size.width * zoom / 2, size.height * zoom / 2
        if selected:
            outline, width = self._palette.selection_outline, self._line_width(SELECTED_OUTLINE_WIDTH)
        else:
            outline, width = darken(fill_color, OUTLINE_DARKEN_FRACTION), self._line_width()
        style = {"fill": fill_color, "outline": outline, "width": width, "tags": tags}
        match node.style.shape:
            case NodeShape.RECTANGLE:
                self._canvas.create_rectangle(*shape_geometry.bounding_box(center_x, center_y, half_width, half_height), **style)
            case NodeShape.ELLIPSE:
                self._canvas.create_oval(*shape_geometry.bounding_box(center_x, center_y, half_width, half_height), **style)
            case NodeShape.ROUNDED_RECTANGLE:
                points = shape_geometry.rounded_rectangle(center_x, center_y, half_width, half_height, CORNER_RADIUS * zoom)
                self._canvas.create_polygon(points, smooth=True, **style)
            case NodeShape.DIAMOND:
                self._canvas.create_polygon(shape_geometry.diamond(center_x, center_y, half_width, half_height), **style)
            case NodeShape.HEXAGON:
                self._canvas.create_polygon(shape_geometry.hexagon(center_x, center_y, half_width, half_height), **style)
            case NodeShape.CLOUD:
                self._canvas.create_polygon(shape_geometry.cloud(center_x, center_y, half_width, half_height), smooth=True, **style)

    def _draw_title(self, node: Node, fill_color: str, tags: tuple[str, ...]) -> None:
        self._canvas.create_text(
            node.position.x * self._zoom,
            node.position.y * self._zoom,
            text=node.title,
            font=self._drawn_font,
            fill=contrast_text_color(fill_color),
            justify="center",
            tags=tags,
        )

    def _draw_collapsed_badge(self, node: Node, grows_left: bool, tags: tuple[str, ...]) -> None:
        zoom = self._zoom
        direction = -1 if grows_left else 1
        badge_x = (node.position.x + direction * self.measure(node).width / 2) * zoom
        badge_y = node.position.y * zoom
        radius = BADGE_RADIUS * zoom
        self._canvas.create_oval(
            *shape_geometry.bounding_box(badge_x, badge_y, radius, radius),
            fill=self._palette.background,
            outline=self._palette.connector_line,
            width=self._line_width(),
            tags=tags,
        )
        self._canvas.create_text(
            badge_x, badge_y, text=str(len(node.children)), font=self._badge_font, fill=self._palette.foreground, tags=tags
        )

    def _line_width(self, base_width: float = OUTLINE_WIDTH) -> float:
        return max(base_width * self._zoom, 1.0)
