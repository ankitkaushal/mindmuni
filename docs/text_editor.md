# Mind Muni: Text Editor

The text editor edits one node's note (a `NoteDocument`): headings, paragraphs,
bold and highlighted text. It can run on its own through
`text_editor_preview.py`, without the main window or menu bar described in
[ui_core.md](ui_core.md). It isn't wired into the app yet.

See [object_model.md](object_model.md) for `NoteDocument`, `TextBlock`,
`TextSpan` and `BlockType`.

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
| `Ctrl` + `Z` / `Ctrl` + `Shift` + `Z` | Undo / redo (`tk.Text`'s own undo) |
| `F5` | Reload the map file from disk and show the root's note again |
| `F6` | Keep the edited note in memory and move to the next node (depth-first, wrapping round) |
| `F7` | Switch between the light and dark themes |
| `F8` | Print the edited note to the terminal, one line per block with its spans |

Edits are never written to the file.

### How formatting behaves while typing
- Headings, bold and highlighted text from the note are shown and kept.
- Typed text is bold or highlighted only when the text on both sides of it is
  (that's Tk's rule for untagged inserts). At the edge of a bold run it is plain.
- Each line is one block. After every edit a line takes the block type of its
  first character or, if that is plain, of any heading text in it. So typing
  at the start or end of a heading keeps it a heading, `Enter` at the end of a
  heading starts a paragraph, and an empty line is a paragraph.
- Headings are drawn bold, so bold text inside a heading looks the same as the
  rest of the heading (it is still kept as bold in the note).

---

## 2. Files

| File | Contains |
|------|----------|
| `text_editor_preview.py` | `TextEditorPreview`: a bare `tk.Tk` window with a `TextEditorView`, loading `MAP_FILE` through `MapRepository`, with the F5–F8 keys above. A test harness only. |
| `mindmuni/ui/text_editor/text_editor_view.py` | `TextEditorView` is a `View` subclass: a `tk.Text` with a vertical scrollbar. `show_note(note)` loads a note with the cursor at the start and an empty undo history; `note()` returns the text as a new `NoteDocument` (the view never changes a node); `apply_theme(theme)` colours the text area and its tags. `TEXT_EDITOR_VIEW_ID` is `"text_editor"`. |
| `mindmuni/ui/text_editor/rich_text_adapter.py` | `RichTextAdapter` converts between a `NoteDocument` and the `tk.Text`'s content and tags. Heading characters carry the tag `"HEADING_1"` or `"HEADING_2"` (paragraphs carry none); inline formatting uses `"bold"` and `"highlighted"`. `load(note)`, `dump()` and `normalize_blocks()` (gives every line one block type, run by the view after each edit). Heading tags are created after `bold` so their font wins; `sel` is raised so selections show over highlights. |
| `mindmuni/ui/text_editor/__init__.py` | Re-exports `TextEditorView`, `RichTextAdapter` and `TEXT_EDITOR_VIEW_ID`. |

Theme use: the text area takes `canvas_background` and `foreground`, the
selection `selection_outline`, highlighted text `highlight_background`, and
fonts come from `theme.fonts` (`base_size`, `heading_1_size`, `heading_2_size`).

---

## 3. Not yet implemented
- A formatting toolbar and shortcuts to make text a heading, a paragraph, bold
  or highlighted.
- A Back button.
- Wiring into the app: registering `TextEditorView` in place of the
  `"text_editor"` placeholder, opening it from a node, and writing the edited
  note back to the node.
