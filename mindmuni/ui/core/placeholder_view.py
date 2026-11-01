from collections.abc import Callable
from dataclasses import dataclass
from tkinter import ttk

from mindmuni.ui.core.view import View


@dataclass(frozen=True, slots=True)
class PlaceholderAction:
    label: str
    command: Callable[[], None]


class PlaceholderView(View):
    """Stand-in screen used until the real mapping and text-editor views exist."""

    def __init__(
        self, parent: ttk.Frame, view_id: str, title: str, description: str, actions: list[PlaceholderAction]
    ) -> None:
        super().__init__(parent, view_id)
        self._context_label: ttk.Label
        self._build(title, description, actions)

    def on_show(self, context: object | None) -> None:
        context_text = f"Context: {context}" if context is not None else ""
        self._context_label.configure(text=context_text)

    def _build(self, title: str, description: str, actions: list[PlaceholderAction]) -> None:
        content = ttk.Frame(self, padding=32)
        content.place(relx=0.5, rely=0.45, anchor="center")
        ttk.Label(content, text=title, style="Heading1.TLabel").pack(pady=(0, 8))
        ttk.Label(content, text=description, style="Heading2.TLabel", justify="center").pack(pady=(0, 16))
        self._context_label = ttk.Label(content)
        self._context_label.pack(pady=(0, 16))
        self._add_action_buttons(content, actions)

    @staticmethod
    def _add_action_buttons(content: ttk.Frame, actions: list[PlaceholderAction]) -> None:
        button_row = ttk.Frame(content)
        button_row.pack()
        for action in actions:
            ttk.Button(button_row, text=action.label, command=action.command).pack(side="left", padx=4)
