import tkinter as tk
from collections.abc import Callable

from mindmuni.model.note_document import BlockType
from mindmuni.model.theme import Theme
from mindmuni.ui.core.toolbar_button import create_toolbar_button, style_toolbar_button
from mindmuni.ui.text_editor.rich_text_adapter import InlineFormat

BLOCK_BUTTONS = ((BlockType.HEADING_1, "H1"), (BlockType.HEADING_2, "H2"), (BlockType.PARAGRAPH, "Normal"))
INLINE_BUTTONS = ((InlineFormat.BOLD, "Bold"), (InlineFormat.HIGHLIGHTED, "Highlight"))
BAR_PADDING = (8, 4)  # around the row of buttons
BUTTON_GAP = 2
SEPARATOR_WIDTH = 1
SEPARATOR_GAP = 6


class FormattingToolbar(tk.Frame):
    """The text editor's toolbar, a fixed bar above the text: [H1 H2 Normal] | [Bold Highlight].

    H1, H2 and Normal set the block type of the current line (or of every selected line); the current line's
    type is shown highlighted. Bold and Highlight toggle a format on the selection; they're disabled with no
    selection and shown highlighted when the whole selection has the format.

    Plain tk widgets coloured from the Theme, like the map toolbars, so it looks right with or without ThemeStyler.
    """

    def __init__(
        self,
        parent: tk.Misc,
        on_block_type: Callable[[BlockType], None],
        on_inline_format: Callable[[InlineFormat], None],
    ) -> None:
        padx, pady = BAR_PADDING
        super().__init__(parent, borderwidth=0, padx=padx, pady=pady)
        self._theme: Theme | None = None
        self._current_block_type: BlockType | None = None
        self._active_formats: set[InlineFormat] = set()
        self._block_buttons: dict[BlockType, tk.Button] = {}
        self._inline_buttons: dict[InlineFormat, tk.Button] = {}
        for block_type, label in BLOCK_BUTTONS:
            button = create_toolbar_button(self, label, lambda chosen=block_type: on_block_type(chosen))
            button.pack(side="left", padx=(0, BUTTON_GAP))
            self._block_buttons[block_type] = button
        self._separator = tk.Frame(self, width=SEPARATOR_WIDTH, borderwidth=0)
        self._separator.pack(side="left", fill="y", padx=SEPARATOR_GAP)
        for inline_format, label in INLINE_BUTTONS:
            button = create_toolbar_button(self, label, lambda chosen=inline_format: on_inline_format(chosen))
            button.pack(side="left", padx=(0, BUTTON_GAP))
            self._inline_buttons[inline_format] = button
        self.show_inline_formats(set(), enabled=False)

    def show_block_type(self, block_type: BlockType | None) -> None:
        """Highlights the button for `block_type`, or none for None."""
        self._current_block_type = block_type
        self._style_buttons()

    def show_inline_formats(self, active: set[InlineFormat], enabled: bool) -> None:
        """Highlights the buttons for the `active` formats, and enables or greys out Bold and Highlight."""
        self._active_formats = set(active)
        for button in self._inline_buttons.values():
            button.configure(state="normal" if enabled else "disabled")
        self._style_buttons()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.configure(background=theme.palette.menu_background)
        self._separator.configure(background=theme.palette.connector_line)
        self._style_buttons()

    def _style_buttons(self) -> None:
        if self._theme is None:
            return
        for block_type, button in self._block_buttons.items():
            self._style_button(button, on=block_type is self._current_block_type)
        for inline_format, button in self._inline_buttons.items():
            self._style_button(button, on=inline_format in self._active_formats)

    def _style_button(self, button: tk.Button, on: bool) -> None:
        style_toolbar_button(button, self._theme)
        if on:
            palette = self._theme.palette
            button.configure(background=palette.highlight_background, foreground=palette.foreground)
