# Mind Muni: Refactoring

Planned clean-ups that don't change behaviour.

---

## 1. Text editor: make layout construction consistent and clear

**Where:** `mindmuni/ui/text_editor/text_editor_view.py`, `TextEditorView.__init__` and
`_create_scrollable_text()`.

**Problem:** `_create_scrollable_text()` creates the `tk.Text` and its scrollbar, but it also
grids the toolbar and the border, which `__init__` created. So:
- The method's name doesn't say it lays out the whole view.
- `__init__` has to create the toolbar and border before calling it, but nothing shows that.
- To see where each piece goes, you have to read a helper whose name is about something else.

**Change:**
- In `__init__`, create every widget first: toolbar, border, text, scrollbar.
- `_create_scrollable_text()` only creates the text and scrollbar and links them; it doesn't
  call `grid`.
- A new `_layout()` method, called from `__init__` once everything exists, holds every
  `grid`, `rowconfigure` and `columnconfigure` call. It's the one place that shows the
  layout (row 0 toolbar, row 1 border, row 2 text and scrollbar, row 2 / column 0 stretch).
