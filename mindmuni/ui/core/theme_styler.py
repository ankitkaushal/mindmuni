import tkinter as tk
from tkinter import ttk

from mindmuni.model.theme import Theme

BASE_TTK_THEME = "clam"  # the only built-in ttk theme that honours custom colours everywhere


class ThemeStyler:
    """Translates a model Theme into ttk styles for all standard widgets."""

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._style = ttk.Style(root)
        self._style.theme_use(BASE_TTK_THEME)

    def apply(self, theme: Theme) -> None:
        self._style_root_window(theme)
        self._style_general_widgets(theme)
        self._style_buttons(theme)
        self._style_status_bar(theme)
        self._style_headings(theme)

    def _style_root_window(self, theme: Theme) -> None:
        self._root.configure(background=theme.palette.background)

    def _style_general_widgets(self, theme: Theme) -> None:
        palette, fonts = theme.palette, theme.fonts
        self._style.configure(
            ".",
            background=palette.background,
            foreground=palette.foreground,
            fieldbackground=palette.canvas_background,
            bordercolor=palette.connector_line,
            font=(fonts.family, fonts.base_size),
        )

    def _style_buttons(self, theme: Theme) -> None:
        palette = theme.palette
        self._style.configure("TButton", background=palette.menu_background, padding=(10, 4))
        self._style.map(
            "TButton",
            background=[("active", palette.highlight_background)],
            foreground=[("disabled", palette.connector_line)],
        )

    def _style_status_bar(self, theme: Theme) -> None:
        palette = theme.palette
        self._style.configure("StatusBar.TFrame", background=palette.menu_background)
        self._style.configure(
            "StatusBar.TLabel", background=palette.menu_background, foreground=palette.menu_foreground
        )

    def _style_headings(self, theme: Theme) -> None:
        fonts = theme.fonts
        self._style.configure("Heading1.TLabel", font=(fonts.family, fonts.heading_1_size, "bold"))
        self._style.configure("Heading2.TLabel", font=(fonts.family, fonts.heading_2_size))
