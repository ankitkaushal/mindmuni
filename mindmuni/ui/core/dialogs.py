from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

MAP_FILE_TYPES = [("Mind Muni map", "*.mson"), ("All files", "*")]
THEME_FILE_TYPES = [("Theme", "*.json"), ("All files", "*")]


class Dialogs:
    """Thin wrapper around Tk's standard dialogs so the rest of the UI never calls them directly."""

    def __init__(self, parent: tk.Tk, default_directory: Path) -> None:
        self._parent = parent
        self._default_directory = default_directory

    def ask_map_to_open(self) -> Path | None:
        chosen = filedialog.askopenfilename(
            parent=self._parent, title="Open map", initialdir=self._default_directory, filetypes=MAP_FILE_TYPES
        )
        return Path(chosen) if chosen else None

    def ask_map_save_path(self, suggested_name: str) -> Path | None:
        chosen = filedialog.asksaveasfilename(
            parent=self._parent,
            title="Save map as",
            initialdir=self._default_directory,
            initialfile=f"{suggested_name}.mson",
            defaultextension=".mson",
            filetypes=MAP_FILE_TYPES,
        )
        return Path(chosen) if chosen else None

    def ask_theme_to_open(self) -> Path | None:
        chosen = filedialog.askopenfilename(parent=self._parent, title="Load custom theme", filetypes=THEME_FILE_TYPES)
        return Path(chosen) if chosen else None

    def confirm_discard_changes(self) -> bool | None:
        """True = save first, False = discard, None = cancel."""
        return messagebox.askyesnocancel(
            "Unsaved changes", "Save changes to the current map before continuing?", parent=self._parent
        )

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self._parent)
