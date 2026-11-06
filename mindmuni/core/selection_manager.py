from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node


class SelectionManager:
    """Tracks the selected node by id. Keyboard navigation (parent, child, siblings) will be added here."""

    def __init__(self) -> None:
        self._selected_id: str | None = None

    @property
    def selected_id(self) -> str | None:
        return self._selected_id

    def select(self, node_id: str | None) -> None:
        self._selected_id = node_id

    def clear(self) -> None:
        self._selected_id = None

    def selected_node(self, mind_map: MindMap) -> Node | None:
        """The selected node, or None if nothing is selected or the node is no longer in the map."""
        if self._selected_id is None:
            return None
        return mind_map.find_node(self._selected_id)
