from dataclasses import dataclass, field
from enum import Enum


class BlockType(Enum):
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    PARAGRAPH = "PARAGRAPH"


@dataclass(slots=True)
class TextSpan:
    """A run of text sharing the same inline formatting."""

    text: str
    bold: bool = False
    highlighted: bool = False


@dataclass(slots=True)
class TextBlock:
    """One paragraph; its spans are rendered next to each other on the line."""

    block_type: BlockType = BlockType.PARAGRAPH
    spans: list[TextSpan] = field(default_factory=list)

    def plain_text(self) -> str:
        return "".join(span.text for span in self.spans)

    def is_empty(self) -> bool:
        return self.plain_text() == ""


@dataclass(slots=True)
class NoteDocument:
    blocks: list[TextBlock] = field(default_factory=list)

    def plain_text(self) -> str:
        return "\n".join(block.plain_text() for block in self.blocks)

    def is_empty(self) -> bool:
        return all(block.is_empty() for block in self.blocks)
