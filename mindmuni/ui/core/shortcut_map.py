import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Shortcut:
    """A key binding: Tk event sequences plus the label shown in menus."""

    sequences: tuple[str, ...]
    label: str


class ShortcutMap:
    """The single place where key bindings are defined."""

    NEW_MAP = Shortcut(("<Control-n>",), "Ctrl+N")
    OPEN_MAP = Shortcut(("<Control-o>",), "Ctrl+O")
    SAVE_MAP = Shortcut(("<Control-s>",), "Ctrl+S")
    SAVE_MAP_AS = Shortcut(("<Control-S>", "<Control-Shift-s>"), "Ctrl+Shift+S")
    QUIT = Shortcut(("<Control-q>",), "Ctrl+Q")
    NAVIGATE_BACK = Shortcut(("<Escape>",), "Esc")
    ZOOM_IN = Shortcut(("<Control-plus>", "<Control-equal>", "<Control-KP_Add>"), "Ctrl++")
    ZOOM_OUT = Shortcut(("<Control-minus>", "<Control-KP_Subtract>"), "Ctrl+-")
    RESET_ZOOM = Shortcut(("<Control-0>", "<Control-KP_0>"), "Ctrl+0")
    INSERT_NODE = Shortcut(("<Insert>", "<KP_Insert>"), "Insert")
    DELETE_NODE = Shortcut(("<Delete>", "<KP_Delete>"), "Delete")

    @staticmethod
    def bind_global(root: tk.Tk, shortcut: Shortcut, action: Callable[[], None]) -> None:
        for sequence in shortcut.sequences:
            root.bind_all(sequence, ShortcutMap._as_event_handler(action))

    @staticmethod
    def bind_local(widget: tk.Misc, shortcut: Shortcut, action: Callable[[], None]) -> None:
        for sequence in shortcut.sequences:
            widget.bind(sequence, ShortcutMap._as_event_handler(action))

    @staticmethod
    def _as_event_handler(action: Callable[[], None]) -> Callable[[tk.Event], str]:
        def handle(_event: tk.Event) -> str:
            action()
            return "break"

        return handle
