import tkinter as tk
from collections.abc import Callable

from mindmuni.model.theme import Theme

BUTTON_PADDING = (12, 6)


def create_toolbar_button(parent: tk.Misc, text: str, command: Callable[[], None]) -> tk.Button:
    """A flat toolbar button, shared by every view's toolbars. Colour it with style_toolbar_button()."""
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
