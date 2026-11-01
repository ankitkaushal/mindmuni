from dataclasses import dataclass, field

from mindmuni.model.geometry import Point
from mindmuni.model.node_style import NodeStyle
from mindmuni.model.note_document import NoteDocument
from mindmuni.utils.id_generator import new_id


@dataclass(slots=True)
class Node:
    title: str
    node_id: str = field(default_factory=new_id)
    children: list["Node"] = field(default_factory=list)
    style: NodeStyle = field(default_factory=NodeStyle)
    note: NoteDocument = field(default_factory=NoteDocument)
    position: Point = field(default_factory=Point)
    collapsed: bool = False

    def add_child(self, child: "Node") -> None:
        self.children.append(child)

    def remove_child(self, node_id: str) -> None:
        self.children = [child for child in self.children if child.node_id != node_id]

    def has_child(self, node_id: str) -> bool:
        return any(child.node_id == node_id for child in self.children)

    def is_leaf(self) -> bool:
        return not self.children
