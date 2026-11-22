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
caller (preview script, later the app)
   │  show_note(note) · note() · apply_theme(theme)
   ▼
TextEditorView ─────────────── owns ───────────────┐
   │  ▲                                             │
   │  │ on_block_type(t)        show_block_type(t)  │
   │  └──────────── FormattingToolbar ◄─────────────┤
   │                                                │
   │  load · dump · set_block_type                  │
   │  block_type_at · normalize_blocks              │
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

- `show_note(note)` loads the note, puts the cursor at `1.0`, clears the undo
  history and modified flag, focuses the text and refreshes the toolbar.
- `note()` builds a fresh `NoteDocument` from what is on screen. Writing it back
  to the node is the caller's job (today only `text_editor_preview.py` does,
  on F6).

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
                            ├─ adapter.normalize_blocks()   # re-tag each line from its newline
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

### Which lines a command applies to
`_selected_lines()` returns the cursor's line, or the first and last line the
selection touches. A selection ending at column 0 of a later line leaves that
line out, which matches what the user sees as selected.

`_update_toolbar()` collects the block types of those lines and highlights the
button only when they're all the same; mixed selections highlight nothing.

---

## 5. The toolbar (`FormattingToolbar`)

A plain `tk.Frame` with **H1**, **H2** and **Normal**, made with the shared
`create_toolbar_button()` / `style_toolbar_button()` from
`mindmuni/ui/core/toolbar_button.py` (the same helpers as the map toolbars).

It's deliberately passive:
- **Out:** a click calls the `on_block_type(block_type)` callback given at
  construction (the view passes `set_block_type`).
- **In:** `show_block_type(block_type | None)` sets which button is drawn with
  `highlight_background`.

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
| Toolbar | `menu_background`, toolbar button styling, `highlight_background` for the current type |
| Border | `connector_line` |

---

## 8. Undo

Undo/redo is `tk.Text`'s own (`undo=True`). It records insertions and
deletions but not tag changes, so block-type changes made with the toolbar or
shortcuts aren't undoable. `load()` calls `edit_reset()` so one note's history
can't be undone into another.

---

## 9. Integration status and extension points

The editor isn't wired into the app yet: `mindmuni/app.py` registers a
placeholder view under `"text_editor"`. It's exercised through
`text_editor_preview.py`, which stands in for the future caller (load a node,
show its note, read it back with `note()` when moving on).

Planned work and where it fits:

| Feature | Where |
|---------|-------|
| Bold / Highlight buttons and `Ctrl+B` / `Ctrl+H` | New buttons and a toggle callback in `FormattingToolbar`; a tag add/remove over the selection in `RichTextAdapter`; shortcuts in `ShortcutMap` bound in `_bind_keys()` |
| Back button | Toolbar callback that asks the navigator to return to the map |
| App wiring | Register `TextEditorView` instead of the placeholder; in `on_show(context)` call `show_note()` with the node's note, and in `on_hide()` write `note()` back to the node |
| New block types | Add to `BlockType`, add the tag to `HEADING_TAGS` (or a renamed equivalent) with its font, add a toolbar button |
