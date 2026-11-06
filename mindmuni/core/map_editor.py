from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node

NEW_NODE_TITLE = "New node"


class MapEditor:
    """The only place that changes a map's node tree. The UI calls it instead of editing nodes directly."""

    def add_child(self, mind_map: MindMap, parent_id: str) -> Node:
        """Appends a new child to the parent and returns it. A collapsed parent is expanded so the child shows."""
        parent = self._require_node(mind_map, parent_id)
        child = Node(title=NEW_NODE_TITLE)
        parent.collapsed = False
        parent.add_child(child)
        mind_map.touch()
        return child

    def delete_node(self, mind_map: MindMap, node_id: str) -> Node:
        """Removes the node and its whole subtree, and returns its former parent. The root can't be deleted."""
        if node_id == mind_map.root.node_id:
            raise ValueError("The root node can't be deleted")
        parent = mind_map.parent_of(node_id)
        if parent is None:
            raise KeyError(f"No node with id {node_id!r}")
        parent.remove_child(node_id)
        mind_map.touch()
        return parent

    @staticmethod
    def can_delete(mind_map: MindMap, node_id: str) -> bool:
        return node_id != mind_map.root.node_id

    @staticmethod
    def _require_node(mind_map: MindMap, node_id: str) -> Node:
        node = mind_map.find_node(node_id)
        if node is None:
            raise KeyError(f"No node with id {node_id!r}")
        return node
