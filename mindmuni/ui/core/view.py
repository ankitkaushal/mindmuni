from tkinter import ttk


class View(ttk.Frame):
    """Base class for every screen that the ViewNavigator can show."""

    def __init__(self, parent: ttk.Frame, view_id: str) -> None:
        super().__init__(parent)
        self.view_id = view_id

    def on_show(self, context: object | None) -> None:
        """Called after the view becomes visible; `context` is what the caller passed to show()."""

    def on_hide(self) -> None:
        """Called before the view is hidden, e.g. to flush unsaved edits into the model."""
