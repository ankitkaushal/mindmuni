"""Polygon outlines for node shapes as flat [x0, y0, x1, y1, ...] lists, ready for Canvas.create_polygon.

Every function takes the shape's centre and its half-width / half-height (the outer bounding box).
"""

import math

Coordinates = list[float]

HEXAGON_SLANT_RATIO = 0.6  # horizontal inset of the slanted sides, relative to half-height
CLOUD_BUMP_COUNT = 10
CLOUD_INNER_RADIUS_RATIO = 0.86
SQRT_3 = math.sqrt(3)
STAR_HALF_WIDTH_RATIO = SQRT_3 / 2  # a star's half-width relative to its point radius


def bounding_box(center_x: float, center_y: float, half_width: float, half_height: float) -> Coordinates:
    return [center_x - half_width, center_y - half_height, center_x + half_width, center_y + half_height]


def diamond(center_x: float, center_y: float, half_width: float, half_height: float) -> Coordinates:
    return [
        center_x, center_y - half_height,
        center_x + half_width, center_y,
        center_x, center_y + half_height,
        center_x - half_width, center_y,
    ]


def hexagon(center_x: float, center_y: float, half_width: float, half_height: float) -> Coordinates:
    inset = half_height * HEXAGON_SLANT_RATIO
    left, right = center_x - half_width, center_x + half_width
    top, bottom = center_y - half_height, center_y + half_height
    return [
        left, center_y,
        left + inset, top,
        right - inset, top,
        right, center_y,
        right - inset, bottom,
        left + inset, bottom,
    ]


def rounded_rectangle(
    center_x: float, center_y: float, half_width: float, half_height: float, radius: float
) -> Coordinates:
    """Draw with smooth=True: the doubled points keep the straight edges straight."""
    left, top, right, bottom = bounding_box(center_x, center_y, half_width, half_height)
    radius = min(radius, half_width, half_height)
    return [
        left + radius, top, left + radius, top, right - radius, top, right - radius, top,
        right, top, right, top + radius, right, top + radius, right, bottom - radius, right, bottom - radius,
        right, bottom, right - radius, bottom, right - radius, bottom, left + radius, bottom, left + radius, bottom,
        left, bottom, left, bottom - radius, left, bottom - radius, left, top + radius, left, top + radius,
        left, top,
    ]


def star_triangles(
    center_x: float, center_y: float, half_width: float, half_height: float
) -> tuple[Coordinates, Coordinates]:
    """A yantra-style six-pointed star (shatkona): an upward and a downward equilateral triangle.

    The triangles are never stretched: the star is the largest one that fits the box, centred in it.
    """
    radius = star_radius(half_width, half_height)

    def triangle(start_degrees: float) -> Coordinates:
        coordinates: Coordinates = []
        for corner in range(3):
            angle = math.radians(start_degrees + corner * 120)
            coordinates.append(center_x + radius * math.cos(angle))
            coordinates.append(center_y + radius * math.sin(angle))
        return coordinates

    return triangle(-90), triangle(90)  # screen y grows downwards, so -90 degrees is the top point


def star_radius(half_width: float, half_height: float) -> float:
    """Distance from the centre to each point of the largest star that fits the box."""
    return min(half_width / STAR_HALF_WIDTH_RATIO, half_height)


def star_box_for_content(content_half_width: float, content_half_height: float) -> tuple[float, float]:
    """Half-width and half-height of the smallest star whose inner hexagon holds a content box of the given size.

    The inner hexagon has its corners at mid-height (left and right) and flat top and bottom edges at radius / 2.
    """
    radius = max(SQRT_3 * content_half_width + content_half_height, 2 * content_half_height)
    return radius * STAR_HALF_WIDTH_RATIO, radius


def star_mid_height_half_width(half_width: float, half_height: float) -> float:
    """How far the star reaches left and right at its centre height: the inner hexagon's side corners."""
    return star_radius(half_width, half_height) / SQRT_3


def cloud(center_x: float, center_y: float, half_width: float, half_height: float) -> Coordinates:
    """Draw with smooth=True: alternating outer/inner points around an ellipse give the bumps."""
    point_count = CLOUD_BUMP_COUNT * 2
    coordinates: Coordinates = []
    for index in range(point_count):
        angle = 2 * math.pi * index / point_count
        radius_ratio = 1.0 if index % 2 == 0 else CLOUD_INNER_RADIUS_RATIO
        coordinates.append(center_x + half_width * radius_ratio * math.cos(angle))
        coordinates.append(center_y + half_height * radius_ratio * math.sin(angle))
    return coordinates
