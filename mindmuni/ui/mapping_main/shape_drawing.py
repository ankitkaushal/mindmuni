"""Draws a NodeShape on a Tk canvas. Shared by the map's NodeRenderer and the StyleToolbar's shape icons."""

import tkinter as tk

from mindmuni.model.node_style import NodeShape
from mindmuni.utils import shape_geometry


def draw_shape(
    canvas: tk.Canvas,
    shape: NodeShape,
    center_x: float,
    center_y: float,
    half_width: float,
    half_height: float,
    *,
    corner_radius: float,
    fill: str,
    outline: str,
    width: float,
    tags: tuple[str, ...] = (),
) -> None:
    """Draws the shape filling the given box. `fill=""` draws a transparent outline only."""
    box = (center_x, center_y, half_width, half_height)
    style = {"fill": fill, "outline": outline, "width": width, "tags": tags}
    match shape:
        case NodeShape.RECTANGLE:
            canvas.create_polygon(shape_geometry.rounded_rectangle(*box, corner_radius), smooth=True, **style)
        case NodeShape.ELLIPSE:
            canvas.create_oval(*shape_geometry.bounding_box(*box), **style)
        case NodeShape.DIAMOND:
            canvas.create_polygon(shape_geometry.diamond(*box), **style)
        case NodeShape.HEXAGON:
            canvas.create_polygon(shape_geometry.hexagon(*box), **style)
        case NodeShape.CLOUD:
            canvas.create_polygon(shape_geometry.cloud(*box), smooth=True, **style)
        case NodeShape.STAR:
            triangles = shape_geometry.star_triangles(*box)
            # Fill both triangles first, then outline both on top, so every edge of each triangle shows.
            if fill:
                for triangle in triangles:
                    canvas.create_polygon(triangle, fill=fill, outline="", tags=tags)
            for triangle in triangles:
                canvas.create_polygon(triangle, fill="", outline=outline, width=width, tags=tags)
