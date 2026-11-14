from dataclasses import dataclass
from enum import Enum


class NodeShape(Enum):
    RECTANGLE = "RECTANGLE"  # drawn with rounded corners
    ELLIPSE = "ELLIPSE"
    DIAMOND = "DIAMOND"
    HEXAGON = "HEXAGON"
    CLOUD = "CLOUD"
    STAR = "STAR"  # six-pointed star: two overlapping triangles


class NodeColor(Enum):
    """Color names only; the active Theme maps each name to a hex value."""

    RED = "RED"
    ORANGE = "ORANGE"
    AMBER = "AMBER"
    YELLOW = "YELLOW"
    LIME = "LIME"
    GREEN = "GREEN"
    TEAL = "TEAL"
    CYAN = "CYAN"
    BLUE = "BLUE"
    INDIGO = "INDIGO"
    PURPLE = "PURPLE"
    PINK = "PINK"


@dataclass(slots=True)
class NodeStyle:
    shape: NodeShape = NodeShape.RECTANGLE
    color: NodeColor = NodeColor.BLUE
