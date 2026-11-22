import tkinter as tk
from tkinter import ttk

from mindmuni.model.note_document import NoteDocument
from mindmuni.model.theme import Theme
from mindmuni.ui.core.view import View
from mindmuni.ui.text_editor.rich_text_adapter import RichTextAdapter

TEXT_EDITOR_VIEW_ID = "text_editor"
TEXT_PADDING = (24, 16)  # space between the text and the widget's edges


class TextEditorView(View):
    """Text component: edits one node's note in a scrollable tk.Text.

    show_note() loads a NoteDocument and note() reads the edited text back as a new one; the view never
    changes a node itself. Headings, bold and highlighted text from the note are shown and kept while
    editing. Typed text is bold or highlighted only when the text on both sides is; a line takes the block
    type of its first character, or of any heading text in it (an empty or new line is a paragraph).
    """

    def __init__(self, parent: tk.Misc, theme: Theme, view_id: str = TEXT_EDITOR_VIEW_ID) -> None:
        super().__init__(parent, view_id)
        self._text = self._create_scrollable_text()
        self._adapter = RichTextAdapter(self._text)
        self._text.bind("<<Modified>>", self._on_modified)
        self.apply_theme(theme)

    def show_note(self, note: NoteDocument) -> None:
        """Shows the note with the cursor at the start, ready for typing. Undo history starts empty."""
        self._adapter.load(note)
        self._text.see("1.0")
        self._text.focus_set()

    def note(self) -> NoteDocument:
        """The text as it is now, as a new NoteDocument."""
        return self._adapter.dump()

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

    # --- internals ----------------------------------------------------------

    def _on_modified(self, _event: tk.Event) -> None:
        if not self._text.edit_modified():
            return  # the event also fires when the flag is cleared below
        self._adapter.normalize_blocks()
        self._text.edit_modified(False)

    def _create_scrollable_text(self) -> tk.Text:
        padx, pady = TEXT_PADDING
        text = tk.Text(
            self, wrap="word", undo=True, relief="flat", borderwidth=0, highlightthickness=0, padx=padx, pady=pady
        )
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        return text
