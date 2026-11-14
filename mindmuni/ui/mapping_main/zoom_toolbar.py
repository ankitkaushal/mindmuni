import tkinter as tk
from collections.abc import Callable

from mindmuni.model.theme import Theme
from mindmuni.ui.mapping_main.map_toolbar import TOOLBAR_MARGIN, create_toolbar_button, style_toolbar_button

ZOOM_LABEL_WIDTH = 5  # characters; fits "300%", so the toolbar doesn't resize as the zoom changes


class ZoomToolbar(tk.Frame):
    """Floating zoom toolbar: − (zoom out), the zoom percentage (click it to reset to 100%) and + (zoom in).

    Like MapToolbar, plain tk widgets coloured from the Theme. Call pin_to() to keep it in a widget's
    top-right corner, and show_zoom() whenever the zoom changes.
    """

    def __init__(
        self,
        parent: tk.Misc,
        on_zoom_out: Callable[[], None],
        on_reset: Callable[[], None],
        on_zoom_in: Callable[[], None],
    ) -> None:
        super().__init__(parent, highlightthickness=1, borderwidth=0, padx=4, pady=4)
        self._zoom_out_button = create_toolbar_button(self, "−", on_zoom_out)
        self._reset_button = create_toolbar_button(self, "100%", on_reset)
        self._reset_button.configure(width=ZOOM_LABEL_WIDTH, padx=0)
        self._zoom_in_button = create_toolbar_button(self, "+", on_zoom_in)
        for button in (self._zoom_out_button, self._reset_button, self._zoom_in_button):
            button.pack(side="left")

    def pin_to(self, widget: tk.Misc) -> None:
        """Places the toolbar over the widget's top-right corner. `widget` must be this toolbar's parent or one of its children."""
        self.place(in_=widget, relx=1.0, rely=0.0, anchor="ne", x=-TOOLBAR_MARGIN, y=TOOLBAR_MARGIN)
        self.lift()

    def show_zoom(self, zoom: float, can_zoom_out: bool, can_zoom_in: bool) -> None:
        """Shows the zoom as a percentage, and greys out − or + at the zoom limits."""
        self._reset_button.configure(text=f"{round(zoom * 100)}%")
        self._zoom_out_button.configure(state="normal" if can_zoom_out else "disabled")
        self._zoom_in_button.configure(state="normal" if can_zoom_in else "disabled")

    def apply_theme(self, theme: Theme) -> None:
        self.configure(background=theme.palette.menu_background, highlightbackground=theme.palette.connector_line)
        for button in (self._zoom_out_button, self._reset_button, self._zoom_in_button):
            style_toolbar_button(button, theme)
