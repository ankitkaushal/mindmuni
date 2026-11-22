import tkinter as tk
from collections.abc import Callable

from mindmuni.model.note_document import BlockType
from mindmuni.model.theme import Theme
from mindmuni.ui.core.toolbar_button import create_toolbar_button, style_toolbar_button

BLOCK_BUTTONS = ((BlockType.HEADING_1, "H1"), (BlockType.HEADING_2, "H2"), (BlockType.PARAGRAPH, "Normal"))
BAR_PADDING = (8, 4)  # around the row of buttons
BUTTON_GAP = 2


class FormattingToolbar(tk.Frame):
    """The text editor's toolbar, a fixed bar above the text: H1, H2 and Normal set the block type of the
    current line (or of every selected line). The current line's type is shown highlighted.

    Plain tk widgets coloured from the Theme, like the map toolbars, so it looks right with or without ThemeStyler.
    """

    def __init__(self, parent: tk.Misc, on_block_type: Callable[[BlockType], None]) -> None:
        padx, pady = BAR_PADDING
        super().__init__(parent, borderwidth=0, padx=padx, pady=pady)
        self._theme: Theme | None = None
        self._current: BlockType | None = None
        self._block_buttons: dict[BlockType, tk.Button] = {}
        for block_type, label in BLOCK_BUTTONS:
            button = create_toolbar_button(self, label, lambda chosen=block_type: on_block_type(chosen))
            button.pack(side="left", padx=(0, BUTTON_GAP))
            self._block_buttons[block_type] = button

    def show_block_type(self, block_type: BlockType | None) -> None:
        """Highlights the button for `block_type`, or none for None."""
        self._current = block_type
        self._style_buttons()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.configure(background=theme.palette.menu_background)
        self._style_buttons()

    def _style_buttons(self) -> None:
        if self._theme is None:
            return
        palette = self._theme.palette
        for block_type, button in self._block_buttons.items():
            style_toolbar_button(button, self._theme)
            if block_type is self._current:
                button.configure(background=palette.highlight_background, foreground=palette.foreground)
