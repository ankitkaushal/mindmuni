import tkinter as tk
from collections.abc import Callable

from mindmuni.model.node import Node
from mindmuni.model.theme import Theme
from mindmuni.ui.mapping_main.node_renderer import TITLE_TAG, node_tag
from mindmuni.utils.color_utils import contrast_text_color

INSERT_CURSOR_WIDTH = 2
CONTROL_MASK = 0x0004
SHIFT_MASK = 0x0001
ALT_MASK = 0x0008

TitleCommitHandler = Callable[[str, str], None]  # (node_id, new_title)
EditingChangedHandler = Callable[[bool], None]  # (is_editing)


class TitleEditor:
    """Edits a node's title in place by typing straight into its title text item on the canvas.

    No widget is laid over the node, so nothing can flash when editing ends: the text keeps the node's own
    colours and font, and only a cursor (and a selection, for new nodes) shows that it is being edited.
    Enter saves, Shift+Enter starts a new line, Escape cancels. Ctrl/Alt shortcuts save first and then run.

    It never changes the node itself: a save calls on_commit(node_id, title), and only when the title actually
    changed and isn't blank. on_editing_changed(is_editing) is called whenever editing starts or stops. The text item belongs to the current drawing, so the owner must call finish()
    before anything redraws the canvas.
    """

    def __init__(
        self,
        canvas: tk.Canvas,
        on_commit: TitleCommitHandler,
        on_editing_changed: EditingChangedHandler | None = None,
    ) -> None:
        self._canvas = canvas
        self._on_commit = on_commit
        self._on_editing_changed = on_editing_changed
        self._item: int | None = None
        self._last_item: int | None = None
        self._node_id: str | None = None
        self._original_title = ""
        self._saved_bindtags: tuple[str, ...] = ()

    @property
    def is_editing(self) -> bool:
        return self._item is not None

    @property
    def node_id(self) -> str | None:
        """The node being edited, or None."""
        return self._node_id if self._item is not None else None

    def start(self, node: Node, theme: Theme, select_all: bool = False) -> None:
        """Starts editing the node's drawn title. select_all: select the whole title, so typing replaces it."""
        self.cancel()
        item = self._find_title_item(node.node_id)
        if item is None:
            return
        self._item, self._node_id, self._original_title = item, node.node_id, node.title
        text_color = contrast_text_color(theme.palette.color_for(node.style.color))
        canvas = self._canvas
        canvas.configure(
            insertbackground=text_color, insertwidth=INSERT_CURSOR_WIDTH,
            selectbackground=theme.palette.highlight_background, selectforeground=theme.palette.foreground,
        )
        # Leave out the toplevel's tag while editing, so window shortcuts (Insert, Delete, single letters) don't
        # fire while typing. Global shortcuts bound with bind_all still do.
        self._saved_bindtags = canvas.bindtags()
        canvas.bindtags((str(canvas), "Canvas", "all"))
        canvas.bind("<KeyPress>", self._on_key)
        canvas.focus_set()
        canvas.focus(item)
        canvas.icursor(item, "end")
        if select_all:
            self._select_all()
        self._notify_editing_changed()

    def finish(self) -> None:
        """Stops editing and saves the title, if it changed and isn't blank."""
        if self._item is None:
            return
        title = self._canvas.itemcget(self._item, "text").strip()
        node_id, original = self._node_id, self._original_title
        self._stop()
        if title and title != original:
            self._on_commit(node_id, title)
        else:
            self._restore_text(original)

    def cancel(self) -> None:
        """Stops editing and puts the old title back."""
        if self._item is None:
            return
        self._stop()
        self._restore_text(self._original_title)

    # --- internals ----------------------------------------------------------

    def _stop(self) -> None:
        canvas = self._canvas
        canvas.select_clear()
        canvas.focus("")
        canvas.unbind("<KeyPress>")
        canvas.bindtags(self._saved_bindtags)
        self._last_item, self._item = self._item, None
        self._notify_editing_changed()

    def _notify_editing_changed(self) -> None:
        if self._on_editing_changed is not None:
            self._on_editing_changed(self.is_editing)

    def _restore_text(self, title: str) -> None:
        """Puts a title back on the item (after a cancel, or a blank or unchanged edit)."""
        if self._canvas.type(self._last_item):  # still on the canvas
            self._canvas.itemconfigure(self._last_item, text=title)

    def _find_title_item(self, node_id: str) -> int | None:
        for item in self._canvas.find_withtag(node_tag(node_id)):
            if TITLE_TAG in self._canvas.gettags(item):
                return item
        return None

    def _on_key(self, event: tk.Event) -> str | None:
        if event.state & (CONTROL_MASK | ALT_MASK):
            if event.state & CONTROL_MASK and event.keysym.lower() == "a":
                self._select_all()
                return "break"
            self.finish()  # save, then let the shortcut run
            return None
        match event.keysym:
            case "Return" | "KP_Enter":
                if event.state & SHIFT_MASK:
                    self._type("\n")
                else:
                    self.finish()
            case "Escape":
                self.cancel()
            case "BackSpace":
                self._delete(backwards=True)
            case "Delete" | "KP_Delete":
                self._delete(backwards=False)
            case "Left" | "Right":
                self._move_cursor(-1 if event.keysym == "Left" else 1)
            case "Home":
                self._set_cursor(0)
            case "End":
                self._set_cursor("end")
            case _:
                if len(event.char) == 1 and event.char.isprintable():
                    self._type(event.char)
        return "break"  # every other key is swallowed while editing

    def _selection(self) -> tuple[int, int] | None:
        """(first, end) of the selected characters, end exclusive, or None."""
        canvas, item = self._canvas, self._item
        if str(canvas.select_item()) != str(item):
            return None
        return canvas.index(item, "sel.first"), canvas.index(item, "sel.last") + 1

    def _delete_selection(self) -> bool:
        selection = self._selection()
        if selection is None:
            return False
        first, end = selection
        self._canvas.dchars(self._item, first, end - 1)
        self._canvas.select_clear()
        self._canvas.icursor(self._item, first)
        return True

    def _type(self, characters: str) -> None:
        self._delete_selection()
        self._canvas.insert(self._item, "insert", characters)

    def _delete(self, backwards: bool) -> None:
        if self._delete_selection():
            return
        cursor = self._canvas.index(self._item, "insert")
        index = cursor - 1 if backwards else cursor
        if 0 <= index < self._canvas.index(self._item, "end"):
            self._canvas.dchars(self._item, index)

    def _move_cursor(self, step: int) -> None:
        selection = self._selection()
        if selection is not None:  # like a text box: an arrow key collapses the selection to that side
            self._set_cursor(selection[0] if step < 0 else selection[1])
            return
        self._set_cursor(max(self._canvas.index(self._item, "insert") + step, 0))

    def _set_cursor(self, index: int | str) -> None:
        self._canvas.select_clear()
        self._canvas.icursor(self._item, index)

    def _select_all(self) -> None:
        self._canvas.select_from(self._item, 0)
        self._canvas.select_to(self._item, "end")
