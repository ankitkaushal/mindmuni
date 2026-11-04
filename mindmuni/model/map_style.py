from dataclasses import dataclass
from enum import Enum


class MapLayout(Enum):
    RIGHT = "RIGHT"  # every branch grows to the right of the root
    BALANCED = "BALANCED"  # the root's branches are split between its left and right sides


@dataclass(slots=True)
class MapStyle:
    """Styling that applies to the whole map rather than to a single node."""

    layout: MapLayout = MapLayout.RIGHT
