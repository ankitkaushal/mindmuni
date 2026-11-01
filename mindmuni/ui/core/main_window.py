import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from mindmuni.ui.core.status_bar import StatusBar

APP_NAME = "Mind Muni"
DEFAULT_GEOMETRY = "1100x720"
MINIMUM_SIZE = (640, 420)


class MainWindow:
    """Owns the Tk root: menu bar slot, the view container and the status bar."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self._configure_root()
        self.view_container = self._create_view_container()
        self.status_bar = self._create_status_bar()

    def set_menu(self, menu: tk.Menu) -> None:
        self.root.configure(menu=menu)

    def set_document_title(self, document_title: str, has_unsaved_changes: bool = False) -> None:
        dirty_marker = "*" if has_unsaved_changes else ""
        self.root.title(f"{dirty_marker}{document_title} — {APP_NAME}")

    def on_close_requested(self, handler: Callable[[], None]) -> None:
        self.root.protocol("WM_DELETE_WINDOW", handler)

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        self.root.destroy()

    def _configure_root(self) -> None:
        self.root.title(APP_NAME)
        self.root.geometry(DEFAULT_GEOMETRY)
        self.root.minsize(*MINIMUM_SIZE)
        self.root.option_add("*tearOff", False)

    def _create_view_container(self) -> ttk.Frame:
        container = ttk.Frame(self.root)
        container.pack(side="top", fill="both", expand=True)
        return container

    def _create_status_bar(self) -> StatusBar:
        status_bar = StatusBar(self.root)
        status_bar.pack(side="bottom", fill="x", before=self.view_container)
        return status_bar
