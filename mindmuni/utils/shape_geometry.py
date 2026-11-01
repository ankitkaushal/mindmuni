"""Polygon outlines for node shapes as flat [x0, y0, x1, y1, ...] lists, ready for Canvas.create_polygon.

Every function takes the shape's centre and its half-width / half-height (the outer bounding box).
"""

import math

Coordinates = list[float]

HEXAGON_SLANT_RATIO = 0.6  # horizontal inset of the slanted sides, relative to half-height
CLOUD_BUMP_COUNT = 10
CLOUD_INNER_RADIUS_RATIO = 0.86


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
