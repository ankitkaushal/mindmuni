from datetime import datetime

from mindmuni.model.geometry import Point
from mindmuni.model.map_style import MapLayout, MapStyle
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
    """Converts a MindMap to and from the .mson document.

    A .mson document is a JSON list of three sections:
      [0] map   - map metadata and the node tree (node ids, titles, children)
      [1] style - how the map looks: "map" holds map-wide styling (layout, zoom),
                  "nodes" holds per-node styling keyed by node_id
                  (shape, color, position, collapsed)
      [2] text  - each node's rich-text note, keyed by node_id
    """

    # --- MindMap -> document ------------------------------------------------

    def to_document(self, mind_map: MindMap) -> list[dict]:
        return [self._map_section(mind_map), self._style_section(mind_map), self._text_section(mind_map)]

    def _map_section(self, mind_map: MindMap) -> dict:
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
            "children": [self._node_to_dict(child) for child in node.children],
        }

    @staticmethod
    def _style_section(mind_map: MindMap) -> dict:
        return {
            "map": {"layout": mind_map.style.layout.value, "zoom": mind_map.style.zoom},
            "nodes": {
                node.node_id: {
                    "shape": node.style.shape.value,
                    "color": node.style.color.value,
                    "position": {"x": node.position.x, "y": node.position.y},
                    "collapsed": node.collapsed,
                }
                for node in mind_map.iter_nodes()
            }
        }

    def _text_section(self, mind_map: MindMap) -> dict:
        """Only nodes that have a note get an entry."""
        return {
            "notes": {
                node.node_id: {"blocks": [self._block_to_dict(block) for block in node.note.blocks]}
                for node in mind_map.iter_nodes()
                if node.note.blocks
            }
        }

    @staticmethod
    def _block_to_dict(block: TextBlock) -> dict:
        spans = [{"text": span.text, "bold": span.bold, "highlighted": span.highlighted} for span in block.spans]
        return {"block_type": block.block_type.value, "spans": spans}

    # --- document -> MindMap ------------------------------------------------

    def from_document(self, document: list) -> MindMap:
        try:
            data, style, text = self._split_sections(document)
            self._check_version(data)
            mind_map = self._map_from_dict(data, style.get("nodes", {}), text.get("notes", {}))
            mind_map.style = self._map_style_from_dict(style.get("map", {}))
            return mind_map
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            if isinstance(error, MapFormatError):
                raise
            raise MapFormatError(f"Invalid map file: {error!r}") from error

    @staticmethod
    def _split_sections(document: list) -> tuple[dict, dict, dict]:
        """The style and text sections are optional; missing ones mean defaults and no notes."""
        if not isinstance(document, list) or not document:
            raise MapFormatError("A .mson file must be a JSON list: [map, style, text]")
        data, style, text = (document + [{}, {}])[:3]
        if not all(isinstance(section, dict) for section in (data, style, text)):
            raise MapFormatError("The map, style and text sections must be JSON objects")
        return data, style, text

    @staticmethod
    def _check_version(data: dict) -> None:
        version = data.get("format_version", FORMAT_VERSION)
        if version > FORMAT_VERSION:
            raise MapFormatError(f"Map format version {version} is newer than supported ({FORMAT_VERSION})")

    def _map_from_dict(self, data: dict, node_styles: dict, node_notes: dict) -> MindMap:
        root = self._node_from_dict(data["root"], node_styles, node_notes)
        return MindMap(
            title=data.get("title", root.title),
            root=root,
            map_id=data.get("map_id") or new_id(),
            created_at=self._parse_time(data.get("created_at")),
            updated_at=self._parse_time(data.get("updated_at")),
        )

    def _node_from_dict(self, data: dict, node_styles: dict, node_notes: dict) -> Node:
        node_id = data.get("node_id") or new_id()
        style = node_styles.get(node_id, {})
        return Node(
            title=data["title"],
            node_id=node_id,
            children=[self._node_from_dict(child, node_styles, node_notes) for child in data.get("children", [])],
            style=self._style_from_dict(style),
            note=self._note_from_dict(node_notes.get(node_id, {})),
            position=self._point_from_dict(style.get("position", {})),
            collapsed=bool(style.get("collapsed", False)),
        )

    @staticmethod
    def _map_style_from_dict(data: dict) -> MapStyle:
        default = MapStyle()
        return MapStyle(
            layout=MapLayout(data.get("layout", default.layout.value)),
            zoom=float(data.get("zoom", default.zoom)),
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
