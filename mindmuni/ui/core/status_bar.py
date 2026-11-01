import tkinter as tk
from tkinter import ttk


class StatusBar(ttk.Frame):
    """One-line message area at the bottom of the main window."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, style="StatusBar.TFrame", padding=(8, 2))
        self._message = ttk.Label(self, style="StatusBar.TLabel", anchor="w")
        self._message.pack(fill="x")

    def show_message(self, text: str) -> None:
        self._message.configure(text=text)

    def clear(self) -> None:
        self.show_message("")
