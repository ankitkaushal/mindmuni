from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime

from mindmuni.model.map_style import MapStyle
from mindmuni.model.node import Node
from mindmuni.utils.clock import now
from mindmuni.utils.id_generator import new_id


@dataclass(slots=True)
class MindMap:
    title: str
    root: Node
    style: MapStyle = field(default_factory=MapStyle)
    map_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    def iter_nodes(self) -> Iterator[Node]:
        """Depth-first, parents before children."""
        pending = [self.root]
        while pending:
            node = pending.pop()
            yield node
            pending.extend(reversed(node.children))

    def find_node(self, node_id: str) -> Node | None:
        return next((node for node in self.iter_nodes() if node.node_id == node_id), None)

    def parent_of(self, node_id: str) -> Node | None:
        return next((node for node in self.iter_nodes() if node.has_child(node_id)), None)

    def touch(self) -> None:
        self.updated_at = now()
