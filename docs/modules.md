# Mind Muni: Module Structure

The package layout follows the spec's split into **ui** (mapping main and text
editor), **utils**, **file**, **model** and **core**. Classes are described in
[object_model.md](object_model.md).

## 1. Package tree

```
MindMuni/
├── main.py                         # Entry point: builds the app and runs mainloop
├── map_preview.py                  # Standalone mapping-component preview (hard-coded map file)
├── text_editor_preview.py          # Standalone text-editor preview (hard-coded map file)
├── themes/                         # Built-in theme JSON files
│   ├── dark.json
│   └── light.json
├── maps/                           # Default location for saved map files
├── docs/
├── tests/
│   ├── model/
│   ├── core/
│   └── file/
└── mindmuni/
    ├── __init__.py
    ├── app.py                      # MindMuniApp: wires model, core, file and ui together
    │
    ├── model/                      # Pure data: no Tkinter, no I/O
    │   ├── __init__.py
    │   ├── mind_map.py             # MindMap
    │   ├── node.py                 # Node
    │   ├── node_style.py           # NodeStyle, NodeShape, NodeColor
    │   ├── note_document.py        # NoteDocument, TextBlock, TextSpan, BlockType
    │   ├── theme.py                # Theme, ThemePalette, FontSettings
    │   └── geometry.py             # Point
    │
    ├── core/                       # Application logic: no Tkinter
    │   ├── __init__.py
    │   ├── events.py               # Events enum, EventBus
    │   ├── map_factory.py          # MapFactory
    │   ├── map_editor.py           # MapEditor
    │   ├── selection_manager.py    # SelectionManager
    │   ├── tree_layout.py          # TreeLayout
    │   ├── theme_manager.py        # ThemeManager
    │   └── document_session.py     # DocumentSession (current map, path, dirty flag)
    │
    ├── file/                       # Persistence only
    │   ├── __init__.py
    │   ├── json_file_store.py      # JsonFileStore
    │   ├── map_serializer.py       # MapSerializer
    │   ├── theme_serializer.py     # ThemeSerializer
    │   ├── map_repository.py       # MapRepository
    │   └── theme_repository.py     # ThemeRepository
    │
    ├── ui/                         # Tkinter only
    │   ├── __init__.py
    │   │
    │   ├── core/                   # App shell shared by all views (see ui_core.md)
    │   │   ├── __init__.py
    │   │   ├── main_window.py      # MainWindow
    │   │   ├── menu_bar.py         # MenuBar (File, Theme)
    │   │   ├── view.py             # View base class
    │   │   ├── view_navigator.py   # ViewNavigator
    │   │   ├── shortcut_map.py     # ShortcutMap
    │   │   ├── theme_styler.py     # ThemeStyler
    │   │   ├── status_bar.py       # StatusBar
    │   │   ├── dialogs.py          # Open/save file dialogs, unsaved-changes prompt
    │   │   └── placeholder_view.py # Temporary stand-in view
    │   │
    │   ├── mapping_main/           # Mapping main component
    │   │   ├── __init__.py
    │   │   ├── mapping_view.py     # MappingView
    │   │   ├── map_canvas.py       # MapCanvas
    │   │   ├── node_renderer.py    # NodeRenderer
    │   │   ├── connector_renderer.py
    │   │   ├── map_toolbar.py      # MapToolbar
    │   │   ├── style_toolbar.py    # StyleToolbar (colour and shape picker)
    │   │   ├── view_toolbar.py     # ViewToolbar (zoom out, percentage/reset, zoom in, drag lock)
    │   │   ├── title_editor.py     # TitleEditor (in-place title editing)
    │   │   └── shape_drawing.py    # draw_shape, shared by NodeRenderer and StyleToolbar
    │   │
    │   └── text_editor/            # Node text component
    │       ├── __init__.py
    │       ├── text_editor_view.py # TextEditorView (tk.Text + scrollbar)
    │       └── rich_text_adapter.py # NoteDocument <-> tk.Text tags
    │
    └── utils/                      # Small helpers with no domain knowledge
        ├── __init__.py
        ├── id_generator.py         # new_id() -> uuid4 string
        ├── paths.py                # app_root_dir(), maps_dir(), themes_dir()
        ├── color_utils.py          # contrast_text_color(hex), darken(hex, pct)
        ├── shape_geometry.py       # Polygon points for diamond, hexagon, star and other shapes
        └── clock.py                # now(), so tests can control time
```

## 2. Dependency rules

```
ui  ──►  core  ──►  model
 │        │
 │        └──►  file  ──►  model
 └──────────────►  utils  ◄── (any layer)
```

- **model** imports only the standard library and `utils`.
- **core** imports `model`, `file` and `utils`. It never imports `tkinter`.
- **file** imports `model` and `utils`. It is the only package that reads or writes the disk.
- **ui** imports `core`, `model` and `utils`. It reaches files only through `core.DocumentSession` and `core.ThemeManager`.
- `app.py` is the only place where concrete objects are created and injected (composition root).

Under these rules you can unit-test `model`, `core` and `file` without
opening a Tk window.

## 3. Module responsibilities

| Module          | Owns                                   | Must not                       |
|-----------------|----------------------------------------|--------------------------------|
| `model`         | Data structures and invariants         | Do I/O or UI                   |
| `core`          | Use cases: edit, select, layout, theme, session | Touch widgets           |
| `file`          | JSON read/write and (de)serialization  | Hold application state         |
| `ui.core`       | Window, menu bar, view switching, shortcuts, styling, dialogs | Contain map- or editor-specific widgets |
| `ui.mapping_main` | Canvas drawing, toolbar, map shortcuts | Change the model directly (it goes through `MapEditor`) |
| `ui.text_editor`  | Text widget, formatting, Back          | Know about files               |
| `utils`         | Generic helpers                        | Import from other packages     |

## 4. Startup sequence (`main.py` → `app.py`)

```python
# main.py
from mindmuni.app import MindMuniApp

def main() -> None:
    MindMuniApp().run()

if __name__ == "__main__":
    main()
```

`MindMuniApp.__init__` does the following, one small method per step:
1. `_create_infrastructure()` builds `JsonFileStore`, `MapRepository` and `ThemeRepository`.
2. `_create_core()` builds `EventBus`, `ThemeManager`, `DocumentSession`, `MapEditor`, `SelectionManager` and `TreeLayout`.
3. `_create_ui()` builds `MainWindow`, `MenuBar`, `MappingView`, `TextEditorView` and `ViewNavigator`.
4. `_start_new_map()` calls `DocumentSession.new_map()`, which creates a map with a root node.
5. `run()` calls `root.mainloop()`.

## 5. Coding conventions (from the spec)

- Python 3.12. Use `@dataclass(slots=True)`, `enum.Enum`, type hints everywhere, and `X | None` unions.
- Tkinter / `ttk` only. No third-party GUI libraries.
- Clean code:
  - Keep functions small, with one level of abstraction per function.
  - Give one responsibility to each class and one main class to each file.
  - Use intention-revealing names (`add_child_to_selected_node`, not `addc`).
  - Write no logic in UI callbacks beyond delegating to core.
- OOP: inject dependencies through constructors and avoid global singletons.

## 6. Suggested build order

1. `model` and its tests
2. `file` serializers and repositories, with round-trip tests
3. `core`: `MapFactory`, `MapEditor`, `SelectionManager`, `TreeLayout`
4. `ui.mapping_main`: canvas, renderer, toolbar, shortcuts
5. `ui.text_editor`: rich text adapter, formatting toolbar, Back
6. `MenuBar`, `ThemeManager`, and the dark/light/custom themes
