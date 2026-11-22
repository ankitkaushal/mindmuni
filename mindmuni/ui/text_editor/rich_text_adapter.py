import tkinter as tk

from mindmuni.model.note_document import BlockType, NoteDocument, TextBlock, TextSpan
from mindmuni.model.theme import Theme

BOLD_TAG = "bold"
HIGHLIGHT_TAG = "highlighted"
HEADING_TAGS = (BlockType.HEADING_1.value, BlockType.HEADING_2.value)  # a line without one is a paragraph


class RichTextAdapter:
    """Moves a NoteDocument into a tk.Text and back, using text tags for the formatting.

    Each block is one line. A line's block type is stored on its newline character, like Word's paragraph
    mark: a heading's newline carries "HEADING_1" or "HEADING_2", a paragraph's carries neither. The rest of
    the line carries the same tag only so it is drawn in the heading font; normalize_blocks() puts it back
    after edits, because Tk gives typed characters only the tags shared by the characters on both sides.
    Bold and highlighted characters carry "bold" and "highlighted".

    Keeping the type on the newline means typing never changes a line's type, an empty line can be a
    heading, and joining two lines (BackSpace at the start of a line) keeps the lower line's type.
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
        for tag in HEADING_TAGS:
            text.tag_remove(tag, "1.0", "end")  # the final newline survives delete() and may keep a tag
        for index, block in enumerate(note.blocks):
            if index > 0:
                text.insert("end-1c", "\n")
            for span in block.spans:
                span_tags = tuple(tag for tag, on in ((BOLD_TAG, span.bold), (HIGHLIGHT_TAG, span.highlighted)) if on)
                text.insert("end-1c", span.text, span_tags)
        for line, block in enumerate(note.blocks, start=1):
            self.set_block_type(line, line, block.block_type)
        text.mark_set("insert", "1.0")
        text.edit_reset()
        text.edit_modified(False)

    def dump(self) -> NoteDocument:
        """Reads the widget's content back as a NoteDocument. An empty widget gives a note with no blocks."""
        text = self._text
        if text.compare("end-1c", "==", "1.0"):
            return NoteDocument()
        return NoteDocument(blocks=[self._dump_line(line) for line in range(1, self.line_count() + 1)])

    def line_count(self) -> int:
        return int(self._text.index("end-1c").split(".")[0])

    def block_type_at(self, index: str) -> BlockType:
        """The block type of the line holding `index` (read from that line's newline)."""
        return self._block_type_of(set(self._text.tag_names(f"{index} lineend")))

    def set_block_type(self, first_line: int, last_line: int, block_type: BlockType) -> None:
        """Makes lines first_line..last_line (1-based, inclusive) all `block_type`."""
        text = self._text
        for line in range(first_line, last_line + 1):
            start, end = f"{line}.0", f"{line}.end+1c"  # the line and its newline
            for tag in HEADING_TAGS:
                text.tag_remove(tag, start, end)
            if block_type.value in HEADING_TAGS:
                text.tag_add(block_type.value, start, end)

    def normalize_blocks(self) -> None:
        """Re-tags every line's characters with the block type on its newline. Run after edits."""
        for line in range(1, self.line_count() + 1):
            self.set_block_type(line, line, self.block_type_at(f"{line}.0"))

    # --- internals ----------------------------------------------------------

    def _dump_line(self, line: int) -> TextBlock:
        text = self._text
        start, end = f"{line}.0", f"{line}.end"
        block = TextBlock(block_type=self.block_type_at(start))
        active = set(text.tag_names(start))  # dump() only reports tags that start inside the range
        for key, value, _index in text.dump(start, end, text=True, tag=True):
            if key == "tagon":
                active.add(value)
            elif key == "tagoff":
                active.discard(value)
            elif key == "text" and value:
                self._append_span(block, TextSpan(value, BOLD_TAG in active, HIGHLIGHT_TAG in active))
        return block

    @staticmethod
    def _block_type_of(tags: set[str]) -> BlockType:
        for tag in HEADING_TAGS:
            if tag in tags:
                return BlockType(tag)
        return BlockType.PARAGRAPH

    @staticmethod
    def _append_span(block: TextBlock, span: TextSpan) -> None:
        """Adds the span, merging it into the previous one when their formatting matches."""
        if block.spans and (block.spans[-1].bold, block.spans[-1].highlighted) == (span.bold, span.highlighted):
            block.spans[-1].text += span.text
        else:
            block.spans.append(span)
