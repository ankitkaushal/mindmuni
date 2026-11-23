from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node
from mindmuni.model.node_style import NodeColor, NodeShape
from mindmuni.model.note_document import NoteDocument

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

    def set_title(self, mind_map: MindMap, node_id: str, title: str) -> bool:
        """Sets the node's title, without leading or trailing whitespace. A blank title is refused (ValueError).

        Returns whether anything changed (a new title can change the node's size).
        """
        node = self._require_node(mind_map, node_id)
        title = title.strip()
        if not title:
            raise ValueError("A node's title can't be blank")
        if node.title == title:
            return False
        node.title = title
        mind_map.touch()
        return True

    def set_color(self, mind_map: MindMap, node_id: str, color: NodeColor) -> bool:
        """Sets the node's colour. Returns whether anything changed."""
        node = self._require_node(mind_map, node_id)
        if node.style.color is color:
            return False
        node.style.color = color
        mind_map.touch()
        return True

    def set_shape(self, mind_map: MindMap, node_id: str, shape: NodeShape) -> bool:
        """Sets the node's shape. Returns whether anything changed (a new shape can change the node's size)."""
        node = self._require_node(mind_map, node_id)
        if node.style.shape is shape:
            return False
        node.style.shape = shape
        mind_map.touch()
        return True

    def set_note(self, mind_map: MindMap, node_id: str, note: NoteDocument) -> bool:
        """Sets the node's note. Returns whether anything changed."""
        node = self._require_node(mind_map, node_id)
        if node.note == note:
            return False
        node.note = note
        mind_map.touch()
        return True

    def move_node(self, mind_map: MindMap, node_id: str, new_parent_id: str) -> bool:
        """Moves the node, with its subtree, to the end of the new parent's children. A collapsed new parent is
        expanded so the node shows. Refused (ValueError) when can_move() says no. Returns whether anything changed:
        dropping a node on its own parent while it's already the last child changes nothing."""
        if not self.can_move(mind_map, node_id, new_parent_id):
            raise ValueError(f"Node {node_id!r} can't be moved under {new_parent_id!r}")
        node = self._require_node(mind_map, node_id)
        old_parent = mind_map.parent_of(node_id)
        new_parent = self._require_node(mind_map, new_parent_id)
        if old_parent is new_parent and new_parent.children[-1] is node:
            return False
        old_parent.remove_child(node_id)
        new_parent.collapsed = False
        new_parent.add_child(node)
        mind_map.touch()
        return True

    @staticmethod
    def can_move(mind_map: MindMap, node_id: str, new_parent_id: str) -> bool:
        """Whether the node can be moved under the new parent: not the root, and not onto itself or anything in
        its own subtree."""
        node = mind_map.find_node(node_id)
        if node is None or node is mind_map.root or mind_map.find_node(new_parent_id) is None:
            return False
        pending = [node]
        while pending:
            current = pending.pop()
            if current.node_id == new_parent_id:
                return False
            pending.extend(current.children)
        return True

    @staticmethod
    def can_delete(mind_map: MindMap, node_id: str) -> bool:
        return node_id != mind_map.root.node_id

    @staticmethod
    def _require_node(mind_map: MindMap, node_id: str) -> Node:
        node = mind_map.find_node(node_id)
        if node is None:
            raise KeyError(f"No node with id {node_id!r}")
        return node
