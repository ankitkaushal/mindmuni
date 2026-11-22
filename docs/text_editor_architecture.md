# Mind Muni: Text Editor Architecture

How the text editor is put together and why. For how to run it, its controls
and a per-file summary, see [text_editor.md](text_editor.md). For the note
model (`NoteDocument`, `TextBlock`, `TextSpan`, `BlockType`) see
[object_model.md](object_model.md).

---

## 1. Overview

The editor is three classes in `mindmuni/ui/text_editor/`, layered so that
only one of them knows how formatting is stored inside Tk:

```
caller (MappingView, or the preview script)
   │  show_note(note) · note() · apply_theme(theme)
   ▼
TextEditorView ─────────────── owns ───────────────┐
   │  ▲                                             │
   │  │ on_block_type(t)        show_block_type(t)  │
   │  │ on_inline_format(f)     show_inline_formats │
   │  └──────────── FormattingToolbar ◄─────────────┤
   │                                                │
   │  load · dump · set_block_type                  │
   │  block_type_at · normalize_blocks              │
   │  has_format · toggle_format                    │
   ▼                                                ▼
RichTextAdapter ──── reads/writes text + tags ──► tk.Text (+ ttk.Scrollbar)
                                                   tags: bold, highlighted,
                                                         HEADING_1, HEADING_2, sel
```

| Layer | Class | Knows about | Doesn't know about |
|-------|-------|-------------|--------------------|
| Component | `TextEditorView` | Layout, key bindings, cursor/selection, when to refresh the toolbar | How blocks and spans map to tags |
| Controls | `FormattingToolbar` | Its buttons and which one is highlighted | The text widget, the note |
| Translation | `RichTextAdapter` | The tag scheme; converting to and from `NoteDocument` | Keys, toolbar, layout |

The model (`mindmuni/model/note_document.py`) is plain dataclasses with no
Tkinter, as for the rest of `model/`.

---

## 2. Data flow

The editor works on a **copy**: it never holds or changes a `Node`.

```
Node.note ──show_note()──► RichTextAdapter.load() ──► tk.Text content + tags
                                                          │  user edits
                                                          ▼
new NoteDocument ◄──note()── RichTextAdapter.dump() ◄── tk.Text content + tags
```

- `show_note(note, focus=True)` loads the note, puts the cursor at `1.0`,
  clears the undo history and modified flag, refreshes the toolbar and, unless
  `focus` is false, focuses the text. `MappingView` passes `focus=False` when
  the selection changes, so clicking a node doesn't pull the keyboard away from
  the map.
- `note()` builds a fresh `NoteDocument` from what is on screen. Writing it back
  to the node is the caller's job: `MappingView` does it through
  `MapEditor.set_note()` (see §9), and `text_editor_preview.py` on F6.

The `tk.Text` itself is the editing state while a note is open; there is no
parallel model kept in sync on every keystroke.

---

## 3. The tag scheme (`RichTextAdapter`)

Every piece of formatting is a Tk text tag.

| Model | In the `tk.Text` |
|-------|------------------|
| `NoteDocument.blocks` | One line per block, joined with `\n` |
| `TextBlock.block_type` | Tag `"HEADING_1"` / `"HEADING_2"` on the line's **newline**; a paragraph's newline has neither |
| `TextSpan.bold` | Tag `"bold"` on its characters |
| `TextSpan.highlighted` | Tag `"highlighted"` on its characters |

The inline tags' names are the values of `InlineFormat` (`BOLD`, `HIGHLIGHTED`),
an enum in `rich_text_adapter.py` that the view and toolbar use to name a
format. Newlines never carry inline tags: `toggle_format()` skips them and
`normalize_blocks()` strips them (`Enter` inside a bold run would otherwise
give the new newline bold). Without this, typing at the end of a fully bold line
would stay bold, because both neighbours, the last character and the newline,
would be bold.

### Block type lives on the newline
Like Word's paragraph mark, the newline character carries the line's type.
This choice gives the editing behaviour for free:

- **Typing never changes a line's type** — new characters don't touch the
  newline.
- **An empty line can be a heading** — it still has a newline to carry the tag.
- **Joining lines** (`BackSpace` at line start) deletes the upper line's
  newline, so the joined line keeps the lower line's type.
- **Splitting a line** (`Enter` mid-line) leaves both halves with a newline
  inheriting the original's tags, so both keep the type.

The line's other characters also carry the heading tag, but only so they're
drawn in the heading font. That copy is derived and gets rebuilt by
`normalize_blocks()` (see §4).

### Tag priority
Tags are created in the order `bold`, `highlighted`, `HEADING_2`,
`HEADING_1`. Tk gives later tags priority where options clash, so a heading's
font wins over `bold` (bold inside a heading looks like the rest of it but is
still kept). `sel` is raised to the top so selections stay visible over
highlighted text.

### has_format() and toggle_format()
Both work on a range split into one segment per line, newlines left out
(`_line_segments()`).
- `has_format(f, start, end)` is true when every segment is fully covered by
  the tag. `_is_covered()` jumps from run to run of the tag with
  `tag_prevrange(tag, index+1c)` instead of checking each character. A range with
  no characters, such as a selection of only an empty line, is false.
- `toggle_format(f, start, end)` removes the tag from every segment if
  `has_format()` is true, otherwise adds it to every segment. So a partly bold
  selection becomes all bold first, as in most editors.

### load()
1. Delete everything and strip heading tags from the surviving final newline.
2. Insert each block's spans with their inline tags, `\n` between blocks.
3. `set_block_type(line, line, type)` for each block.
4. Reset cursor, undo stack and modified flag.

### dump()
For each line, read its type with `block_type_at()` (tags on `line lineend`),
then walk `tk.Text.dump()` from `line.0` to `line.end`, tracking `tagon` /
`tagoff` to know which inline tags are active for each text chunk. The tags
already active at the start of the line are seeded from `tag_names()`, since
`dump()` only reports tags that begin inside the range. Adjacent chunks with
the same formatting are merged into one `TextSpan`, so the result doesn't
depend on how Tk split the text. An empty widget gives a note with no blocks.

---

## 4. Keeping the tags consistent (`TextEditorView`)

Tk gives an inserted character only the tags shared by the characters on both
sides of it. That's fine for `bold`/`highlighted` (typing inside a bold run
stays bold, at its edge it's plain), but it would leave typed characters in a
heading without the heading font. The view fixes this after every change:

```
edit ──► <<Modified>> ──► _on_modified()
                            ├─ adapter.normalize_blocks()   # re-tag each line from its newline,
                            │                               # strip inline tags from newlines
                            └─ text.edit_modified(False)    # re-arm the event
```

`<<Modified>>` fires only when the modified flag changes, so clearing it is
what makes it fire again on the next edit. The handler ignores the event that
the clear itself triggers.

### Event handling

| Binding | Handler | Purpose |
|---------|---------|---------|
| `<<Modified>>` | `_on_modified` | Normalize heading tags after any edit |
| `<Return>`, `<KP_Enter>` | `_on_return` | At the end of a heading (no selection), insert `\n` and make the new line a paragraph; returns `"break"`. Otherwise falls through to Tk's default |
| `<KeyRelease>`, `<ButtonRelease-1>` | `_update_toolbar` | Tk has no "cursor moved" event, so the toolbar is refreshed after keys and clicks |
| `Ctrl+1` / `Ctrl+2` / `Ctrl+0` | `set_block_type(...)` | Bound locally on the text widget via `ShortcutMap.bind_local`, using `ShortcutMap.HEADING_1`, `HEADING_2`, `NORMAL_TEXT` |
| `Ctrl+B` / `Ctrl+H` | `toggle_format(...)` | `ShortcutMap.BOLD`, `HIGHLIGHT`. The handler returns `"break"`, so `tk.Text`'s own class bindings (cursor left, BackSpace) don't run |

### Which lines a command applies to
`_selected_lines()` returns the cursor's line, or the first and last line the
selection touches. A selection ending at column 0 of a later line leaves that
line out, which matches what the user sees as selected.

`_update_toolbar()` collects the block types of those lines and highlights the
button only when they're all the same; mixed selections highlight nothing. It
also tells the toolbar which inline formats the whole selection has
(`has_format()` on `sel.first`..`sel.last`), and enables Bold and Highlight only
when there is a selection. `toggle_format()` in the view does nothing without a
selection.

---

## 5. The toolbar (`FormattingToolbar`)

A plain `tk.Frame` with **H1**, **H2** and **Normal**, a one-pixel separator,
then **Bold** and **Highlight**, all made with the shared
`create_toolbar_button()` / `style_toolbar_button()` from
`mindmuni/ui/core/toolbar_button.py` (the same helpers as the map toolbars).

It's deliberately passive:
- **Out:** a click calls the `on_block_type(block_type)` or
  `on_inline_format(inline_format)` callback given at construction (the view
  passes `set_block_type` and `toggle_format`).
- **In:** `show_block_type(block_type | None)` and
  `show_inline_formats(active, enabled)` set which buttons are drawn with
  `highlight_background`, and whether Bold and Highlight are enabled.

The buttons are laid out with `pack(side="left")` inside the bar.

It has no reference to the text widget, so it could be reused or replaced
without touching the editing logic. After a click the view puts focus back on
the text so typing continues.

---

## 6. Layout

`TextEditorView` is a `View` (a `ttk.Frame` with a `view_id`, default
`TEXT_EDITOR_VIEW_ID = "text_editor"`) laid out with `grid`:

| Row | Column 0 | Column 1 |
|-----|----------|----------|
| 0 | `FormattingToolbar` (spans both) | |
| 1 | 1px border frame (spans both) | |
| 2 | `tk.Text` (`wrap="word"`, `undo=True`, padding 24×16) — stretches | `ttk.Scrollbar` |

---

## 7. Theming

`apply_theme(theme)` fans out to every part, so a theme switch restyles live:

| Part | Theme values |
|------|--------------|
| Text area | `canvas_background`, `foreground` (text and cursor), `selection_outline` (selection), `connector_line` (inactive selection), font `family` / `base_size` |
| Tags (adapter) | `bold` → base size bold; `highlighted` → `highlight_background`; `HEADING_1` / `HEADING_2` → `heading_1_size` / `heading_2_size` bold |
| Toolbar | `menu_background`, toolbar button styling (`connector_line` for disabled text), `highlight_background` for the current type and active formats, `connector_line` for the separator |
| Border | `connector_line` |

---

## 8. Undo

Undo/redo is `tk.Text`'s own (`undo=True`). It records insertions and
deletions but not tag changes, so block-type and bold/highlight changes made
with the toolbar or shortcuts aren't undoable. `load()` calls `edit_reset()` so one note's history
can't be undone into another.

---

## 9. In the app: the split screen

The editor opens in a split screen inside `MappingView`, not as a separate
screen swapped in by `ViewNavigator`, so it has no Back button. The view
toolbar's **Text** button (beside **Drag**) calls `MappingView.toggle_text()`.

```
MappingView (grid)
  column 0 (weight 1)                    column 1     column 2      column 3 (weight 0, fixed width)
  ┌──────────────────────────────────┐  ┌───┐        ┌─┐           ┌─────────────────────────┐
  │ MapCanvas + pinned toolbars      │  │ ▲ │        │ │ 1px       │ TextEditorView           │
  │                                  │  │ █ │        │ │ border    │                          │
  ├──────────────────────────────────┤  └───┘        └─┘           │                          │
  │ horizontal scrollbar             │                              │                          │
  └──────────────────────────────────┘                              └─────────────────────────┘
```

- **Nothing already on screen moves.** Opening the area must not shrink or move
  the map or anything else. `set_text_open(True)` measures the canvas and sets
  the editor's width to a third of it (`TEXT_TO_MAP_WIDTH`). The editor has
  `grid_propagate(False)`, so that width is used whatever its contents ask for.
  Then `_widen_window()` makes the toplevel window wider on its right by that
  width plus the 1px border, keeping its position. The map keeps its exact width
  and the text area fills the new space. The title-bar text, centred by the
  window manager, moves with the window's middle, and that's accepted. The
  window doesn't grow past the screen's right edge; if it can't grow enough,
  the map gives up the rest.
- **Resizing while open:** the text area keeps its width and the map's column
  (weight 1) takes any change.
- **Closing:** hides the border and editor with `grid_remove()` and narrows the
  window on its right by their width, so everything is back where it was.
- **Pinning the map's width while the window resizes:** the window manager
  resizes the window a moment after `geometry()` asks it to. If the map's
  column could stretch in the meantime, opening would lay the text area out
  inside the old window, over the right of the map (a white flash), and closing
  would briefly stretch the map into the space the text left (which also made
  Tk snap the map to its scroll region's edge). So `_pin_map_width()` sets the
  map's column to weight 0 with `minsize` at its current width first. Until
  the window has resized, the text area is laid out past the window's right
  edge, out of sight, and the map's size never changes. `_on_resized()`
  unpins the column (weight 1, no `minsize`) when the view reaches the width
  `_widen_window()` expects. It also unpins after `RESIZE_TIMEOUT_MS` (1 s),
  in case the window manager doesn't resize the window as asked.
- **Which note:** `MappingView` remembers the node whose note is shown
  (`_note_node_id`). `_show_selected_note()` runs after every selection change
  (`show_map`, a node click, `insert_node`, `delete_selected_node`) and loads
  the selected node's note. Clicking empty space selects nothing and keeps the
  last note, so typing never goes nowhere. `show_map()` forgets the node first,
  so an old map's note is never written into a new map.
- **Storing the note:** `finish_editing()`, which every map action already calls
  first, now also stores the shown note into its node with
  `MapEditor.set_note()` (it touches the map only when the note changed). The app
  calls `finish_editing()` before writing the file, so **Save** includes the text
  being typed. Closing the text area stores it too.
- **Keys:** the app binds only `Ctrl` shortcuts and `Esc` globally, which don't
  clash with typing. `map_preview.py` binds plain keys (`T`, `L`, `R`, `Insert`,
  `Delete`, `F2`) on its window, so it ignores them when they come from the text
  area.

`text_editor_preview.py` still runs the editor on its own.

---

## 10. Extension points

Planned work and where it fits:

| Feature | Where |
|---------|-------|
| `Ctrl+B` / `Ctrl+H` with no selection (format the next typed text) | A pending-format set in the view, applied to inserted text in `_on_modified()` and cleared when the cursor moves |
| A draggable divider | Put the map and the text area in a `ttk.PanedWindow` instead of two grid columns |
| New inline formats | Add to `InlineFormat` and `TextSpan`, configure the tag in `apply_theme()`, read it in `_dump_line()` / write it in `load()`, add to `INLINE_BUTTONS` |
| New block types | Add to `BlockType`, add the tag to `HEADING_TAGS` (or a renamed equivalent) with its font, add a toolbar button |
