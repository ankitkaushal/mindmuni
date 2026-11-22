import tkinter as tk

from mindmuni.model.note_document import BlockType, NoteDocument, TextBlock, TextSpan
from mindmuni.model.theme import Theme

BOLD_TAG = "bold"
HIGHLIGHT_TAG = "highlighted"
HEADING_TAGS = (BlockType.HEADING_1.value, BlockType.HEADING_2.value)  # a line without one is a paragraph


class RichTextAdapter:
    """Moves a NoteDocument into a tk.Text and back, using text tags for the formatting.

    Each block is one line. A heading's characters carry its block tag ("HEADING_1" or "HEADING_2"); paragraphs
    carry none. Bold and highlighted characters carry "bold" and "highlighted". Tk gives typed characters only
    the tags shared by the characters on both sides, so text typed at the edge of a heading loses its tag;
    after every edit normalize_blocks() gives each line one block type again.
    """

    def __init__(self, text: tk.Text) -> None:
        self._text = text
        # Tags created later win where their options clash, so headings' fonts beat bold's.
        for tag in (BOLD_TAG, HIGHLIGHT_TAG, BlockType.HEADING_2.value, BlockType.HEADING_1.value):
            text.tag_configure(tag)
        text.tag_raise("sel")  # selected text stays visible over highlighted text

    def apply_theme(self, theme: Theme) -> None:
        fonts, palette = theme.fonts, theme.palette
        text = self._text
        text.tag_configure(BOLD_TAG, font=(fonts.family, fonts.base_size, "bold"))
        text.tag_configure(HIGHLIGHT_TAG, background=palette.highlight_background)
        text.tag_configure(BlockType.HEADING_1.value, font=(fonts.family, fonts.heading_1_size, "bold"))
        text.tag_configure(BlockType.HEADING_2.value, font=(fonts.family, fonts.heading_2_size, "bold"))

    def load(self, note: NoteDocument) -> None:
        """Replaces the widget's content with the note. Clears undo history and the modified flag."""
        text = self._text
        text.delete("1.0", "end")
        for index, block in enumerate(note.blocks):
            if index > 0:
                text.insert("end", "\n")
            block_tags = (block.block_type.value,) if block.block_type.value in HEADING_TAGS else ()
            for span in block.spans:
                span_tags = tuple(tag for tag, on in ((BOLD_TAG, span.bold), (HIGHLIGHT_TAG, span.highlighted)) if on)
                text.insert("end", span.text, block_tags + span_tags)
        text.mark_set("insert", "1.0")
        text.edit_reset()
        text.edit_modified(False)

    def dump(self) -> NoteDocument:
        """Reads the widget's content back as a NoteDocument. An empty widget gives a note with no blocks."""
        text = self._text
        if text.compare("end-1c", "==", "1.0"):
            return NoteDocument()
        blocks: list[TextBlock] = []
        current = TextBlock()
        block_type: BlockType | None = None
        active: set[str] = set()
        for key, value, _index in text.dump("1.0", "end-1c", text=True, tag=True):
            if key == "tagon":
                active.add(value)
            elif key == "tagoff":
                active.discard(value)
            elif key == "text":
                for line_number, part in enumerate(value.split("\n")):
                    if line_number > 0:  # a newline ends the block
                        current.block_type = block_type or BlockType.PARAGRAPH
                        blocks.append(current)
                        current, block_type = TextBlock(), None
                    if part:
                        block_type = block_type or self._block_type_of(active)
                        self._append_span(current, TextSpan(part, BOLD_TAG in active, HIGHLIGHT_TAG in active))
        current.block_type = block_type or BlockType.PARAGRAPH
        blocks.append(current)
        return NoteDocument(blocks=blocks)

    def normalize_blocks(self) -> None:
        """Gives every line exactly one block type: the type of its first character, or else of its first
        heading character. Run after edits, because typed or joined text can leave a line with mixed tags."""
        text = self._text
        last_line = int(text.index("end-1c").split(".")[0])
        for line in range(1, last_line + 1):
            start, end = f"{line}.0", f"{line}.end"
            block_tag = self._line_block_tag(start, end)
            for tag in HEADING_TAGS:
                if tag != block_tag:
                    text.tag_remove(tag, start, end)
            if block_tag is not None:
                text.tag_add(block_tag, start, end)

    # --- internals ----------------------------------------------------------

    def _line_block_tag(self, start: str, end: str) -> str | None:
        text = self._text
        if text.compare(start, "==", end):
            return None  # an empty line is a paragraph
        first_char_tags = set(text.tag_names(start))
        for tag in HEADING_TAGS:
            if tag in first_char_tags:
                return tag
        earliest: tuple[str, str] | None = None
        for tag in HEADING_TAGS:
            found = text.tag_nextrange(tag, start, end)
            if found and (earliest is None or text.compare(found[0], "<", earliest[1])):
                earliest = (tag, found[0])
        return earliest[0] if earliest else None

    @staticmethod
    def _block_type_of(tags: set[str]) -> BlockType | None:
        for tag in HEADING_TAGS:
            if tag in tags:
                return BlockType(tag)
        return None

    @staticmethod
    def _append_span(block: TextBlock, span: TextSpan) -> None:
        """Adds the span, merging it into the previous one when their formatting matches."""
        if block.spans and (block.spans[-1].bold, block.spans[-1].highlighted) == (span.bold, span.highlighted):
            block.spans[-1].text += span.text
        else:
            block.spans.append(span)
