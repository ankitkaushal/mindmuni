import tkinter as tk
from collections.abc import Callable

from mindmuni.model.theme import Theme
from mindmuni.ui.core.toolbar_button import create_toolbar_button, style_toolbar_button
from mindmuni.ui.mapping_main.map_toolbar import TOOLBAR_MARGIN

ZOOM_LABEL_WIDTH = 5  # characters; fits "300%", so the toolbar doesn't resize as the zoom changes
DRAG_LABEL_WIDTH = 9  # characters; fits both drag labels, so the toolbar doesn't resize when toggled
DRAG_OFF_LABEL = "Drag: Off"
DRAG_ON_LABEL = "Drag: On"
TEXT_LABEL_WIDTH = 9  # characters; fits both text labels
TEXT_OFF_LABEL = "Text: Off"
TEXT_ON_LABEL = "Text: On"
SEPARATOR_WIDTH = 1
SEPARATOR_GAP = 4


class ViewToolbar(tk.Frame):
    """Floating view toolbar: − (zoom out), the zoom percentage (click it to reset to 100%), + (zoom in), a
    Drag toggle that allows or locks dragging the map around, and a Text toggle that opens or closes the
    selected node's note beside the map.

    Like MapToolbar, plain tk widgets coloured from the Theme. Call pin_to() to keep it in a widget's
    top-right corner, show_zoom() whenever the zoom changes, show_drag() whenever dragging is toggled and
    show_text() whenever the text area opens or closes.
    """

    def __init__(
        self,
        parent: tk.Misc,
        on_zoom_out: Callable[[], None],
        on_reset: Callable[[], None],
        on_zoom_in: Callable[[], None],
        on_toggle_drag: Callable[[], None],
        on_toggle_text: Callable[[], None],
    ) -> None:
        super().__init__(parent, highlightthickness=1, borderwidth=0, padx=4, pady=4)
        self._theme: Theme | None = None
        self._drag_enabled = False
        self._text_open = False
        self._zoom_out_button = create_toolbar_button(self, "−", on_zoom_out)
        self._reset_button = create_toolbar_button(self, "100%", on_reset)
        self._reset_button.configure(width=ZOOM_LABEL_WIDTH, padx=0)
        self._zoom_in_button = create_toolbar_button(self, "+", on_zoom_in)
        self._separator = tk.Frame(self, width=SEPARATOR_WIDTH, borderwidth=0)
        self._drag_button = create_toolbar_button(self, DRAG_OFF_LABEL, on_toggle_drag)
        self._drag_button.configure(width=DRAG_LABEL_WIDTH, padx=0)
        self._text_button = create_toolbar_button(self, TEXT_OFF_LABEL, on_toggle_text)
        self._text_button.configure(width=TEXT_LABEL_WIDTH, padx=0)
        for button in (self._zoom_out_button, self._reset_button, self._zoom_in_button):
            button.pack(side="left")
        self._separator.pack(side="left", fill="y", padx=SEPARATOR_GAP)
        self._drag_button.pack(side="left")
        self._text_button.pack(side="left")

    def pin_to(self, widget: tk.Misc) -> None:
        """Places the toolbar over the widget's top-right corner. `widget` must be this toolbar's parent or one of its children."""
        self.place(in_=widget, relx=1.0, rely=0.0, anchor="ne", x=-TOOLBAR_MARGIN, y=TOOLBAR_MARGIN)
        self.lift()

    def show_zoom(self, zoom: float, can_zoom_out: bool, can_zoom_in: bool) -> None:
        """Shows the zoom as a percentage, and greys out − or + at the zoom limits."""
        self._reset_button.configure(text=f"{round(zoom * 100)}%")
        self._zoom_out_button.configure(state="normal" if can_zoom_out else "disabled")
        self._zoom_in_button.configure(state="normal" if can_zoom_in else "disabled")

    def show_drag(self, enabled: bool) -> None:
        """Shows whether dragging the map is allowed. The button is highlighted while it is."""
        self._drag_enabled = enabled
        self._drag_button.configure(text=DRAG_ON_LABEL if enabled else DRAG_OFF_LABEL)
        self._style_toggles()

    def show_text(self, is_open: bool) -> None:
        """Shows whether the text area is open. The button is highlighted while it is."""
        self._text_open = is_open
        self._text_button.configure(text=TEXT_ON_LABEL if is_open else TEXT_OFF_LABEL)
        self._style_toggles()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        palette = theme.palette
        self.configure(background=palette.menu_background, highlightbackground=palette.connector_line)
        self._separator.configure(background=palette.connector_line)
        for button in (self._zoom_out_button, self._reset_button, self._zoom_in_button):
            style_toolbar_button(button, theme)
        self._style_toggles()

    def _style_toggles(self) -> None:
        """Styles Drag and Text, each highlighted while on."""
        if self._theme is None:
            return
        palette = self._theme.palette
        for button, on in ((self._drag_button, self._drag_enabled), (self._text_button, self._text_open)):
            style_toolbar_button(button, self._theme)
            if on:
                button.configure(background=palette.highlight_background, foreground=palette.foreground)
