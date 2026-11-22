import tkinter as tk
from tkinter import ttk

from mindmuni.model.note_document import BlockType, NoteDocument
from mindmuni.model.theme import Theme
from mindmuni.ui.core.shortcut_map import ShortcutMap
from mindmuni.ui.core.view import View
from mindmuni.ui.text_editor.formatting_toolbar import FormattingToolbar
from mindmuni.ui.text_editor.rich_text_adapter import InlineFormat, RichTextAdapter

TEXT_EDITOR_VIEW_ID = "text_editor"
TEXT_PADDING = (24, 16)  # space between the text and the widget's edges


class TextEditorView(View):
    """Text component: edits one node's note in a scrollable tk.Text, with the formatting toolbar above it.

    show_note() loads a NoteDocument and note() reads the edited text back as a new one; the view never
    changes a node itself. Each line is a heading or a paragraph: H1, H2 and Normal on the toolbar (or
    Ctrl+1, Ctrl+2, Ctrl+0) set it for the cursor's line or every selected line, and typing never changes
    it. Enter at the end of a heading starts a paragraph. Bold and Highlight (Ctrl+B, Ctrl+H) toggle a format
    on the selection. Typed text is bold or highlighted only when the text on both sides of it is.
    """

    def __init__(self, parent: tk.Misc, theme: Theme, view_id: str = TEXT_EDITOR_VIEW_ID) -> None:
        super().__init__(parent, view_id)
        self._toolbar = FormattingToolbar(
            self, on_block_type=self.set_block_type, on_inline_format=self.toggle_format
        )
        self._toolbar_border = tk.Frame(self, height=1, borderwidth=0)
        self._text = self._create_scrollable_text()
        self._adapter = RichTextAdapter(self._text)
        self._bind_keys()
        self.apply_theme(theme)

    def show_note(self, note: NoteDocument, focus: bool = True) -> None:
        """Shows the note with the cursor at the start. Undo history starts empty. With `focus`, the text takes
        the keyboard focus, ready for typing; without it, focus stays where it is (e.g. on the map)."""
        self._adapter.load(note)
        self._text.see("1.0")
        if focus:
            self._text.focus_set()
        self._update_toolbar()

    def note(self) -> NoteDocument:
        """The text as it is now, as a new NoteDocument."""
        return self._adapter.dump()

    def set_block_type(self, block_type: BlockType) -> None:
        """Makes the cursor's line, or every line the selection touches, a heading or a paragraph."""
        first_line, last_line = self._selected_lines()
        self._adapter.set_block_type(first_line, last_line, block_type)
        self._text.focus_set()  # back to typing after a toolbar click
        self._update_toolbar()

    def toggle_format(self, inline_format: InlineFormat) -> None:
        """Removes the format from the selection if all of it has it, otherwise adds it to all of it. Does
        nothing without a selection."""
        if self._text.tag_ranges("sel"):
            self._adapter.toggle_format(inline_format, "sel.first", "sel.last")
        self._text.focus_set()  # back to typing after a toolbar click
        self._update_toolbar()

    def apply_theme(self, theme: Theme) -> None:
        palette, fonts = theme.palette, theme.fonts
        self._text.configure(
            background=palette.canvas_background,
            foreground=palette.foreground,
            insertbackground=palette.foreground,
            selectbackground=palette.selection_outline,
            selectforeground=palette.canvas_background,
            inactiveselectbackground=palette.connector_line,
            font=(fonts.family, fonts.base_size),
        )
        self._adapter.apply_theme(theme)
        self._toolbar.apply_theme(theme)
        self._toolbar_border.configure(background=palette.connector_line)

    # --- internals ----------------------------------------------------------

    def _bind_keys(self) -> None:
        text = self._text
        text.bind("<<Modified>>", self._on_modified)
        for sequence in ("<Return>", "<KP_Enter>"):
            text.bind(sequence, self._on_return)
        # Tk has no "cursor moved" event, so the toolbar is refreshed after keys and clicks.
        text.bind("<KeyRelease>", lambda _event: self._update_toolbar(), add="+")
        text.bind("<ButtonRelease-1>", lambda _event: self._update_toolbar(), add="+")
        ShortcutMap.bind_local(text, ShortcutMap.HEADING_1, lambda: self.set_block_type(BlockType.HEADING_1))
        ShortcutMap.bind_local(text, ShortcutMap.HEADING_2, lambda: self.set_block_type(BlockType.HEADING_2))
        ShortcutMap.bind_local(text, ShortcutMap.NORMAL_TEXT, lambda: self.set_block_type(BlockType.PARAGRAPH))
        # These replace tk.Text's own Ctrl+B (cursor left) and Ctrl+H (BackSpace).
        ShortcutMap.bind_local(text, ShortcutMap.BOLD, lambda: self.toggle_format(InlineFormat.BOLD))
        ShortcutMap.bind_local(text, ShortcutMap.HIGHLIGHT, lambda: self.toggle_format(InlineFormat.HIGHLIGHTED))

    def _on_modified(self, _event: tk.Event) -> None:
        if not self._text.edit_modified():
            return  # the event also fires when the flag is cleared below
        self._adapter.normalize_blocks()
        self._text.edit_modified(False)

    def _on_return(self, _event: tk.Event) -> str | None:
        """Enter at the end of a heading starts a paragraph, as in most editors. Anywhere else Tk's own
        Enter runs, and the new line gets the type of the line it was split from."""
        text = self._text
        at_line_end = text.compare("insert", "==", "insert lineend")
        if text.tag_ranges("sel") or not at_line_end or self._adapter.block_type_at("insert") is BlockType.PARAGRAPH:
            return None
        text.insert("insert", "\n")
        line = int(text.index("insert").split(".")[0])
        self._adapter.set_block_type(line, line, BlockType.PARAGRAPH)
        text.see("insert")
        self._update_toolbar()
        return "break"

    def _selected_lines(self) -> tuple[int, int]:
        """First and last line of the selection, or the cursor's line twice. A selection that ends at the
        very start of a line doesn't include that line."""
        text = self._text
        if not text.tag_ranges("sel"):
            line = int(text.index("insert").split(".")[0])
            return line, line
        first = int(text.index("sel.first").split(".")[0])
        last_line, last_column = map(int, text.index("sel.last").split("."))
        if last_column == 0 and last_line > first:
            last_line -= 1
        return first, last_line

    def _update_toolbar(self) -> None:
        first_line, last_line = self._selected_lines()
        types = {self._adapter.block_type_at(f"{line}.0") for line in range(first_line, last_line + 1)}
        self._toolbar.show_block_type(types.pop() if len(types) == 1 else None)
        has_selection = bool(self._text.tag_ranges("sel"))
        active = {
            inline_format
            for inline_format in InlineFormat
            if has_selection and self._adapter.has_format(inline_format, "sel.first", "sel.last")
        }
        self._toolbar.show_inline_formats(active, enabled=has_selection)

    def _create_scrollable_text(self) -> tk.Text:
        padx, pady = TEXT_PADDING
        text = tk.Text(
            self, wrap="word", undo=True, relief="flat", borderwidth=0, highlightthickness=0, padx=padx, pady=pady
        )
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        self._toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self._toolbar_border.grid(row=1, column=0, columnspan=2, sticky="ew")
        text.grid(row=2, column=0, sticky="nsew")
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        return text
