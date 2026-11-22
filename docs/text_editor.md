# Mind Muni: Text Editor

The text editor edits one node's note (a `NoteDocument`): headings, paragraphs,
bold and highlighted text. A fixed toolbar above the text sets each line's
block type. It can run on its own through
`text_editor_preview.py`, without the main window or menu bar described in
[ui_core.md](ui_core.md). It isn't wired into the app yet.

See [object_model.md](object_model.md) for `NoteDocument`, `TextBlock`,
`TextSpan` and `BlockType`, and
[text_editor_architecture.md](text_editor_architecture.md) for how the
editor's classes fit together.

---

## 1. Running the preview script

Prerequisites are the same as for the mapping preview (Python 3.12 with
tkinter, run from the project root).

```
.venv/bin/python text_editor_preview.py          # Linux / macOS
.venv\Scripts\python text_editor_preview.py      # Windows
```
In PyCharm, right-click `text_editor_preview.py` and choose **Run**.

The script loads `maps/sample.mson` (set by `MAP_FILE` at the top of the
script) and shows the root's note, which has a heading and a bold, highlighted
span. The window title shows the node's title and its position in the map.

### Controls
| Input | Action |
|-------|--------|
| Typing, `Enter`, `BackSpace`, arrows, mouse selection | Normal text editing (`tk.Text`) |
| `Ctrl` + `Z` / `Ctrl` + `Shift` + `Z` | Undo / redo (`tk.Text`'s own undo; it covers text, not block-type changes) |
| **H1** / **H2** / **Normal**, or `Ctrl` + `1` / `Ctrl` + `2` / `Ctrl` + `0` | Make the cursor's line, or every line the selection touches, a heading 1, heading 2 or paragraph. A selection ending at the very start of a line leaves that line out. The button for the current line's type is highlighted; none is when the selected lines differ. |
| `F5` | Reload the map file from disk and show the root's note again |
| `F6` | Keep the edited note in memory and move to the next node (depth-first, wrapping round) |
| `F7` | Switch between the light and dark themes |
| `F8` | Print the edited note to the terminal, one line per block with its spans |

Edits are never written to the file.

### How formatting behaves while typing
- Headings, bold and highlighted text from the note are shown and kept.
- Typed text is bold or highlighted only when the text on both sides of it is
  (that's Tk's rule for untagged inserts). At the edge of a bold run it is plain.
- Each line is one block, and its type is stored on its newline character (like
  Word's paragraph mark). Typing never changes a line's type, and an empty line
  can be a heading.
- `Enter` at the end of a heading starts a paragraph. `Enter` in the middle of
  a line splits it into two lines of the same type; at the start of a line it
  adds an empty paragraph above.
- `BackSpace` at the start of a line joins it to the line above, and the joined
  line keeps the lower line's type (as in Word).
- Headings are drawn bold, so bold text inside a heading looks the same as the
  rest of the heading (it is still kept as bold in the note).

---

## 2. Files

| File | Contains |
|------|----------|
| `text_editor_preview.py` | `TextEditorPreview`: a bare `tk.Tk` window with a `TextEditorView`, loading `MAP_FILE` through `MapRepository`, with the F5–F8 keys above. A test harness only. |
| `mindmuni/ui/text_editor/text_editor_view.py` | `TextEditorView` is a `View` subclass: the `FormattingToolbar` across the top, a one-pixel border, then a `tk.Text` with a vertical scrollbar. `show_note(note)` loads a note with the cursor at the start and an empty undo history; `note()` returns the text as a new `NoteDocument` (the view never changes a node); `set_block_type(block_type)` changes the cursor's or selected lines; `apply_theme(theme)` colours the text area, its tags and the toolbar. It binds `Ctrl+1/2/0` on the text widget, overrides `Enter` at the end of a heading, and refreshes the toolbar after key and mouse releases (Tk has no cursor-moved event). `TEXT_EDITOR_VIEW_ID` is `"text_editor"`. |
| `mindmuni/ui/text_editor/formatting_toolbar.py` | `FormattingToolbar` is a plain `tk.Frame` bar with **H1**, **H2** and **Normal**, made with the shared `create_toolbar_button()` / `style_toolbar_button()`. `on_block_type(block_type)` is called on a click; `show_block_type(block_type or None)` highlights the current one with `highlight_background`, like the map's **Drag: On**. |
| `mindmuni/ui/text_editor/rich_text_adapter.py` | `RichTextAdapter` converts between a `NoteDocument` and the `tk.Text`'s content and tags. A line's block type is the tag `"HEADING_1"` or `"HEADING_2"` on its newline (paragraphs carry none); the line's characters get the same tag for the heading font, and `normalize_blocks()` (run by the view after each edit) re-applies it. Inline formatting uses `"bold"` and `"highlighted"`. Also `load(note)`, `dump()`, `block_type_at(index)`, `set_block_type(first_line, last_line, block_type)` and `line_count()`. Heading tags are created after `bold` so their font wins; `sel` is raised so selections show over highlights. |
| `mindmuni/ui/text_editor/__init__.py` | Re-exports `TextEditorView`, `FormattingToolbar`, `RichTextAdapter` and `TEXT_EDITOR_VIEW_ID`. |

Theme use: the text area takes `canvas_background` and `foreground`, the
selection `selection_outline`, highlighted text `highlight_background`, and
the toolbar uses the menu colours with `highlight_background` for the
current block type, and fonts come from `theme.fonts` (`base_size`, `heading_1_size`, `heading_2_size`).

---

## 3. Not yet implemented
- Bold and Highlight buttons and shortcuts (`Ctrl+B`, `Ctrl+H`).
- A Back button.
- Wiring into the app: registering `TextEditorView` in place of the
  `"text_editor"` placeholder, opening it from a node, and writing the edited
  note back to the node.
