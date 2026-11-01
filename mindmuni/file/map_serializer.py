from datetime import datetime

from mindmuni.model.geometry import Point
from mindmuni.model.mind_map import MindMap
from mindmuni.model.node import Node
from mindmuni.model.node_style import NodeColor, NodeShape, NodeStyle
from mindmuni.model.note_document import BlockType, NoteDocument, TextBlock, TextSpan
from mindmuni.utils.clock import now
from mindmuni.utils.id_generator import new_id

FORMAT_VERSION = 1


class MapFormatError(ValueError):
    """Raised when a map file's content cannot be turned into a MindMap."""


class MapSerializer:
    """Converts a MindMap to and from plain dicts (the JSON file format)."""

    # --- MindMap -> dict ----------------------------------------------------

    def to_dict(self, mind_map: MindMap) -> dict:
        return {
            "format_version": FORMAT_VERSION,
            "map_id": mind_map.map_id,
            "title": mind_map.title,
            "created_at": mind_map.created_at.isoformat(),
            "updated_at": mind_map.updated_at.isoformat(),
            "root": self._node_to_dict(mind_map.root),
        }

    def _node_to_dict(self, node: Node) -> dict:
        return {
            "node_id": node.node_id,
            "title": node.title,
            "style": {"shape": node.style.shape.value, "color": node.style.color.value},
            "position": {"x": node.position.x, "y": node.position.y},
            "collapsed": node.collapsed,
            "note": {"blocks": [self._block_to_dict(block) for block in node.note.blocks]},
            "children": [self._node_to_dict(child) for child in node.children],
        }

    @staticmethod
    def _block_to_dict(block: TextBlock) -> dict:
        spans = [{"text": span.text, "bold": span.bold, "highlighted": span.highlighted} for span in block.spans]
        return {"block_type": block.block_type.value, "spans": spans}

    # --- dict -> MindMap ----------------------------------------------------

    def from_dict(self, data: dict) -> MindMap:
        try:
            self._check_version(data)
            return self._map_from_dict(data)
        except (KeyError, TypeError, ValueError) as error:
            raise MapFormatError(f"Invalid map file: {error!r}") from error

    @staticmethod
    def _check_version(data: dict) -> None:
        version = data.get("format_version", FORMAT_VERSION)
        if version > FORMAT_VERSION:
            raise MapFormatError(f"Map format version {version} is newer than supported ({FORMAT_VERSION})")

    def _map_from_dict(self, data: dict) -> MindMap:
        root = self._node_from_dict(data["root"])
        return MindMap(
            title=data.get("title", root.title),
            root=root,
            map_id=data.get("map_id") or new_id(),
            created_at=self._parse_time(data.get("created_at")),
            updated_at=self._parse_time(data.get("updated_at")),
        )

    def _node_from_dict(self, data: dict) -> Node:
        return Node(
            title=data["title"],
            node_id=data.get("node_id") or new_id(),
            children=[self._node_from_dict(child) for child in data.get("children", [])],
            style=self._style_from_dict(data.get("style", {})),
            note=self._note_from_dict(data.get("note", {})),
            position=self._point_from_dict(data.get("position", {})),
            collapsed=bool(data.get("collapsed", False)),
        )

    @staticmethod
    def _style_from_dict(data: dict) -> NodeStyle:
        default = NodeStyle()
        return NodeStyle(
            shape=NodeShape(data.get("shape", default.shape.value)),
            color=NodeColor(data.get("color", default.color.value)),
        )

    def _note_from_dict(self, data: dict) -> NoteDocument:
        return NoteDocument(blocks=[self._block_from_dict(block) for block in data.get("blocks", [])])

    @staticmethod
    def _block_from_dict(data: dict) -> TextBlock:
        spans = [
            TextSpan(text=span["text"], bold=span.get("bold", False), highlighted=span.get("highlighted", False))
            for span in data.get("spans", [])
        ]
        return TextBlock(block_type=BlockType(data.get("block_type", BlockType.PARAGRAPH.value)), spans=spans)

    @staticmethod
    def _point_from_dict(data: dict) -> Point:
        return Point(x=float(data.get("x", 0.0)), y=float(data.get("y", 0.0)))

    @staticmethod
    def _parse_time(value: str | None) -> datetime:
        return datetime.fromisoformat(value) if value else now()
