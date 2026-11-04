from collections.abc import Callable
from dataclasses import dataclass, field

from mindmuni.model.geometry import Point, Size
from mindmuni.model.map_style import MapLayout
from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node

NodeMeasurer = Callable[[Node], Size]

RIGHT = 1
LEFT = -1


@dataclass(frozen=True, slots=True)
class LayoutSpacing:
    horizontal_gap: float = 60.0  # between depth columns
    vertical_gap: float = 16.0  # between sibling subtrees
    origin: Point = field(default_factory=Point)  # top-left corner of the whole tree


@dataclass(frozen=True, slots=True)
class _Side:
    """The root's branches that grow in one direction, and the depth columns they occupy.

    Column 0 is the root's own column; column_offsets are measured from the root's centre.
    """

    direction: int
    branches: list[Node]
    column_widths: list[float]
    column_offsets: list[float]
    height: float

    @property
    def reach(self) -> float:
        """Distance from the root's centre to the outer edge of this side (half the root's width when empty)."""
        return self.column_offsets[-1] + self.column_widths[-1] / 2


def visible_children(node: Node) -> list[Node]:
    return [] if node.collapsed else node.children


class TreeLayout:
    """Places every visible node, one column per depth, each parent centred on its children.

    The map's layout style picks the shape:
      RIGHT    - all of the root's branches grow to the right.
      BALANCED - the root's branches are split in order: the first ones grow to the right, the rest
                 to the left, so both sides end up about the same height. The left side is a mirror image.

    Node sizes come from an injected measurer, so this class stays free of Tkinter.
    """

    def __init__(self, measure_node: NodeMeasurer, spacing: LayoutSpacing = LayoutSpacing()) -> None:
        self._measure_node = measure_node
        self._spacing = spacing

    def apply(self, mind_map: MindMap) -> None:
        root = mind_map.root
        sizes = self._measure_visible_nodes(root)
        heights = self._compute_subtree_heights(root, sizes)
        right_branches, left_branches = self._split_branches(root, heights, mind_map.style.layout)
        sides = [
            self._build_side(RIGHT, right_branches, root, sizes, heights),
            self._build_side(LEFT, left_branches, root, sizes, heights),
        ]
        root.position = self._root_position(root, sizes, sides)
        for side in sides:
            self._place_branches(side, root.position, heights)

    # --- measuring ----------------------------------------------------------

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

    # --- splitting the root's branches between the sides --------------------

    def _split_branches(
        self, root: Node, heights: dict[str, float], layout: MapLayout
    ) -> tuple[list[Node], list[Node]]:
        branches = visible_children(root)
        if layout is MapLayout.RIGHT or len(branches) < 2:
            return branches, []
        half_height = self._stacked_height([heights[branch.node_id] for branch in branches]) / 2
        split_index, right_height = 0, 0.0
        while split_index < len(branches) - 1 and right_height < half_height:
            right_height += heights[branches[split_index].node_id] + self._spacing.vertical_gap
            split_index += 1
        return branches[:split_index], branches[split_index:]

    # --- columns ------------------------------------------------------------

    def _build_side(
        self, direction: int, branches: list[Node], root: Node, sizes: dict[str, Size], heights: dict[str, float]
    ) -> _Side:
        column_widths = self._widest_node_per_depth(root, branches, sizes)
        return _Side(
            direction=direction,
            branches=branches,
            column_widths=column_widths,
            column_offsets=self._column_offsets(column_widths),
            height=self._stacked_height([heights[branch.node_id] for branch in branches]),
        )

    @staticmethod
    def _widest_node_per_depth(root: Node, branches: list[Node], sizes: dict[str, Size]) -> list[float]:
        widths = [sizes[root.node_id].width]
        level = branches
        while level:
            widths.append(max(sizes[node.node_id].width for node in level))
            level = [child for node in level for child in visible_children(node)]
        return widths

    def _column_offsets(self, column_widths: list[float]) -> list[float]:
        """Distance from the root's centre to the centre of each depth column."""
        offsets = [0.0]
        for previous_width, width in zip(column_widths, column_widths[1:]):
            offsets.append(offsets[-1] + previous_width / 2 + self._spacing.horizontal_gap + width / 2)
        return offsets

    # --- placing ------------------------------------------------------------

    def _root_position(self, root: Node, sizes: dict[str, Size], sides: list[_Side]) -> Point:
        """Root centre, chosen so the whole tree's top-left corner sits at the spacing origin."""
        left_side = next(side for side in sides if side.direction == LEFT)
        total_height = max([sizes[root.node_id].height] + [side.height for side in sides])
        return Point(self._spacing.origin.x + left_side.reach, self._spacing.origin.y + total_height / 2)

    def _place_branches(self, side: _Side, root_center: Point, heights: dict[str, float]) -> None:
        top = root_center.y - side.height / 2
        for branch in side.branches:
            self._place_subtree(branch, 1, top, side, root_center.x, heights)
            top += heights[branch.node_id] + self._spacing.vertical_gap

    def _place_subtree(
        self, node: Node, depth: int, top: float, side: _Side, root_x: float, heights: dict[str, float]
    ) -> None:
        subtree_height = heights[node.node_id]
        node.position = Point(root_x + side.direction * side.column_offsets[depth], top + subtree_height / 2)
        children = visible_children(node)
        children_height = self._stacked_height([heights[child.node_id] for child in children])
        child_top = top + (subtree_height - children_height) / 2
        for child in children:
            self._place_subtree(child, depth + 1, child_top, side, root_x, heights)
            child_top += heights[child.node_id] + self._spacing.vertical_gap

    def _stacked_height(self, heights: list[float]) -> float:
        if not heights:
            return 0.0
        return sum(heights) + self._spacing.vertical_gap * (len(heights) - 1)
