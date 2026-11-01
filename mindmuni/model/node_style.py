from dataclasses import dataclass
from enum import Enum


class NodeShape(Enum):
    RECTANGLE = "RECTANGLE"
    ROUNDED_RECTANGLE = "ROUNDED_RECTANGLE"
    ELLIPSE = "ELLIPSE"
    DIAMOND = "DIAMOND"
    HEXAGON = "HEXAGON"
    CLOUD = "CLOUD"


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
    shape: NodeShape = NodeShape.ROUNDED_RECTANGLE
    color: NodeColor = NodeColor.BLUE
