import tkinter as tk
from collections.abc import Callable

from mindmuni.model.theme import Theme

TOOLBAR_MARGIN = 16  # gap between the toolbar and the canvas's bottom-right corner
BUTTON_PADDING = (12, 6)


def create_toolbar_button(parent: tk.Misc, text: str, command: Callable[[], None]) -> tk.Button:
    """A flat toolbar button, shared by the floating map toolbars. Colour it with style_toolbar_button()."""
    padx, pady = BUTTON_PADDING
    return tk.Button(
        parent, text=text, command=command, relief="flat", borderwidth=0, padx=padx, pady=pady, cursor="hand2"
    )


def style_toolbar_button(button: tk.Button, theme: Theme) -> None:
    palette, fonts = theme.palette, theme.fonts
    button.configure(
        background=palette.menu_background,
        foreground=palette.menu_foreground,
        activebackground=palette.highlight_background,
        activeforeground=palette.foreground,
        disabledforeground=palette.connector_line,
        highlightbackground=palette.menu_background,
        font=(fonts.family, fonts.base_size),
    )


class MapToolbar(tk.Frame):
    """Floating edit toolbar for the map: Insert (add a child to the selected node), Edit (its title) and Delete.

    Plain tk widgets, coloured from the Theme directly, so it looks right with or without ThemeStyler.
    Call pin_to() to keep it in the bottom-right corner of a widget, however that widget is resized.
    """

    def __init__(
        self,
        parent: tk.Misc,
        on_insert: Callable[[], None],
        on_edit: Callable[[], None],
        on_delete: Callable[[], None],
    ) -> None:
        super().__init__(parent, highlightthickness=1, borderwidth=0, padx=4, pady=4)
        self._insert_button = create_toolbar_button(self, "+ Insert", on_insert)
        self._edit_button = create_toolbar_button(self, "✎ Edit", on_edit)
        self._delete_button = create_toolbar_button(self, "✕ Delete", on_delete)
        self._insert_button.pack(side="left", padx=(0, 4))
        self._edit_button.pack(side="left", padx=(0, 4))
        self._delete_button.pack(side="left")

    def pin_to(self, widget: tk.Misc) -> None:
        """Places the toolbar over the widget's bottom-right corner. `widget` must be this toolbar's parent or one of its children."""
        self.place(in_=widget, relx=1.0, rely=1.0, anchor="se", x=-TOOLBAR_MARGIN, y=-TOOLBAR_MARGIN)
        self.lift()

    def set_enabled(self, insert: bool, edit: bool, delete: bool) -> None:
        self._insert_button.configure(state="normal" if insert else "disabled")
        self._edit_button.configure(state="normal" if edit else "disabled")
        self._delete_button.configure(state="normal" if delete else "disabled")

    def apply_theme(self, theme: Theme) -> None:
        self.configure(background=theme.palette.menu_background, highlightbackground=theme.palette.connector_line)
        for button in (self._insert_button, self._edit_button, self._delete_button):
            style_toolbar_button(button, theme)
