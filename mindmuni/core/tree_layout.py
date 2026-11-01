from collections.abc import Callable
from dataclasses import dataclass, field

from mindmuni.model.geometry import Point, Size
from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node

NodeMeasurer = Callable[[Node], Size]


@dataclass(frozen=True, slots=True)
class LayoutSpacing:
    horizontal_gap: float = 60.0  # between depth columns
    vertical_gap: float = 16.0  # between sibling subtrees
    origin: Point = field(default_factory=Point)  # top-left corner of the whole tree


def visible_children(node: Node) -> list[Node]:
    return [] if node.collapsed else node.children


class TreeLayout:
    """Left-to-right tree: root on the left, one column per depth, each parent centred on its children.

    Node sizes come from an injected measurer, so this class stays free of Tkinter.
    """

    def __init__(self, measure_node: NodeMeasurer, spacing: LayoutSpacing = LayoutSpacing()) -> None:
        self._measure_node = measure_node
        self._spacing = spacing

    def apply(self, mind_map: MindMap) -> None:
        sizes = self._measure_visible_nodes(mind_map.root)
        subtree_heights = self._compute_subtree_heights(mind_map.root, sizes)
        column_centers = self._compute_column_centers(mind_map.root, sizes)
        self._place_subtree(mind_map.root, 0, self._spacing.origin.y, subtree_heights, column_centers)

    def _measure_visible_nodes(self, root: Node) -> dict[str, Size]:
        sizes: dict[str, Size] = {}
        pending = [root]
        while pending:
            node = pending.pop()
            sizes[node.node_id] = self._measure_node(node)
            pending.extend(visible_children(node))
        return sizes

    def _compute_subtree_heights(self, node: Node, sizes: dict[str, Size]) -> dict[str, float]:
        heights: dict[str, float] = {}
        for child in visible_children(node):
            heights.update(self._compute_subtree_heights(child, sizes))
        children_height = self._stacked_height([heights[child.node_id] for child in visible_children(node)])
        heights[node.node_id] = max(sizes[node.node_id].height, children_height)
        return heights

    def _compute_column_centers(self, root: Node, sizes: dict[str, Size]) -> list[float]:
        column_widths = self._widest_node_per_depth(root, sizes)
        centers, left_edge = [], self._spacing.origin.x
        for width in column_widths:
            centers.append(left_edge + width / 2)
            left_edge += width + self._spacing.horizontal_gap
        return centers

    def _widest_node_per_depth(self, root: Node, sizes: dict[str, Size]) -> list[float]:
        widths: list[float] = []
        level = [root]
        while level:
            widths.append(max(sizes[node.node_id].width for node in level))
            level = [child for node in level for child in visible_children(node)]
        return widths

    def _place_subtree(
        self, node: Node, depth: int, top: float, heights: dict[str, float], column_centers: list[float]
    ) -> None:
        subtree_height = heights[node.node_id]
        node.position = Point(column_centers[depth], top + subtree_height / 2)
        children = visible_children(node)
        children_height = self._stacked_height([heights[child.node_id] for child in children])
        child_top = top + (subtree_height - children_height) / 2
        for child in children:
            self._place_subtree(child, depth + 1, child_top, heights, column_centers)
            child_top += heights[child.node_id] + self._spacing.vertical_gap

    def _stacked_height(self, heights: list[float]) -> float:
        if not heights:
            return 0.0
        return sum(heights) + self._spacing.vertical_gap * (len(heights) - 1)
