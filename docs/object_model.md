# Mind Muni: Object Model

This is the domain model for Mind Muni, the Tkinter-based mind-mapping tool.
It comes from `mindmuni-2026-10-18-19-01.txt`.

## Spec interpretation

The spec text came from handwriting recognition, so I read some words as follows:

| Spec text            | Read as                                   |
|----------------------|-------------------------------------------|
| Tent / Tent editor   | Text / Text editor                        |
| Thome                | Theme                                     |
| Tinker               | Tkinter                                   |
| hi 42 heading Types  | H1, H2 heading types (plus normal text)   |
| Saxe                 | Save                                      |
| Python 3:12          | Python 3.12                               |

---

## 1. Class diagram (overview)

```
MindMap 1 ──── 1 Node (root)
Node    1 ──── * Node (children)
Node    1 ──── 1 NodeStyle
Node    1 ──── 1 NoteDocument
NoteDocument 1 ── * TextBlock
TextBlock    1 ── * TextSpan
NodeStyle  ──► NodeShape (enum), NodeColor (enum)
Theme      1 ── 1 ThemePalette, 1 FontSettings
```

---

## 2. Model classes (`mindmuni/model`)

These are plain data classes (`@dataclass`). They have no Tkinter and no file I/O.

### `MindMap`
The aggregate root. It holds one whole map.

| Attribute    | Type            | Notes                                    |
|--------------|-----------------|------------------------------------------|
| `map_id`     | `str`           | UUID                                     |
| `title`      | `str`           | Shown in the window title                |
| `root`       | `Node`          | A new map always starts with a root node |
| `style`      | `MapStyle`      | Map-wide styling                         |
| `created_at` | `datetime`      |                                          |
| `updated_at` | `datetime`      |                                          |

Methods:
- `find_node(node_id) -> Node | None`
- `iter_nodes() -> Iterator[Node]` walks the tree depth-first.
- `parent_of(node_id) -> Node | None`

### `MapStyle`
Styling that applies to the whole map rather than to one node.

| Attribute | Type        | Notes                                                        |
|-----------|-------------|--------------------------------------------------------------|
| `layout`  | `MapLayout` | `RIGHT` (all branches to the right of the root, the default) or `BALANCED` (the root's branches split between left and right) |

### `Node`
One idea in the map.

| Attribute   | Type           | Notes                                    |
|-------------|----------------|------------------------------------------|
| `node_id`   | `str`          | UUID                                     |
| `title`     | `str`          | Label drawn inside the shape             |
| `children`  | `list[Node]`   | Ordered                                  |
| `style`     | `NodeStyle`    | Shape and color                          |
| `note`      | `NoteDocument` | Rich-text note opened in the text editor |
| `position`  | `Point`        | Canvas coordinates, set by the layout    |
| `collapsed` | `bool`         | Optional: hides the children             |

Methods:
- `add_child(child: Node) -> None`
- `remove_child(node_id: str) -> None`
- `is_leaf() -> bool`

### `NodeStyle`
| Attribute | Type        |
|-----------|-------------|
| `shape`   | `NodeShape` |
| `color`   | `NodeColor` |

### `NodeShape` (Enum)
`RECTANGLE`, `ROUNDED_RECTANGLE`, `ELLIPSE`, `DIAMOND`, `HEXAGON`, `CLOUD`

### `NodeColor` (Enum, 12 colors)
`RED`, `ORANGE`, `AMBER`, `YELLOW`, `LIME`, `GREEN`, `TEAL`, `CYAN`, `BLUE`,
`INDIGO`, `PURPLE`, `PINK`

The enum holds only *names*. The theme supplies the actual hex values, so
each color can look right in both dark and light themes.

### `NoteDocument`
The text component's content for one node.

| Attribute | Type              |
|-----------|-------------------|
| `blocks`  | `list[TextBlock]` |

Methods: `is_empty() -> bool`, `plain_text() -> str`

### `TextBlock`
One line or paragraph.

| Attribute    | Type             |
|--------------|------------------|
| `block_type` | `BlockType`      |
| `spans`      | `list[TextSpan]` |

### `BlockType` (Enum)
`HEADING_1`, `HEADING_2`, `PARAGRAPH`

### `TextSpan`
A run of text that has the same inline formatting.

| Attribute     | Type   |
|---------------|--------|
| `text`        | `str`  |
| `bold`        | `bool` |
| `highlighted` | `bool` |

### `Theme`
| Attribute  | Type           | Notes                         |
|------------|----------------|-------------------------------|
| `name`     | `str`          | `"dark"`, `"light"` or custom |
| `palette`  | `ThemePalette` |                               |
| `fonts`    | `FontSettings` |                               |

### `ThemePalette`
`background`, `foreground`, `canvas_background`, `connector_line`,
`selection_outline`, `highlight_background`, `menu_background`,
`menu_foreground`, `node_colors: dict[NodeColor, str]`

### `FontSettings`
`family`, `base_size`, `heading_1_size`, `heading_2_size`, `node_title_size`

### `Point`
`x: float`, `y: float` (a frozen dataclass)

---

## 3. Core services (`mindmuni/core`)

These classes hold the application logic. They work on model objects and
know nothing about Tkinter widgets.

| Class               | Responsibility                                                                 |
|---------------------|--------------------------------------------------------------------------------|
| `MapFactory`        | `create_new_map(title)` returns a `MindMap` with a default root node            |
| `MapEditor`         | Edits the map: `add_child`, `add_sibling`, `rename_node`, `delete_node`, `set_shape`, `set_color` |
| `SelectionManager`  | Tracks the selected node. Provides `select_parent/first_child/next_sibling/previous_sibling` for keyboard navigation |
| `TreeLayout`        | Computes `Node.position` for every node, right-only or balanced per `MapStyle.layout` |
| `ThemeManager`      | Holds the current `Theme`, switches dark/light/custom, notifies subscribers     |
| `DocumentSession`   | Holds the open `MindMap`, its file path and dirty flag. Also handles new/open/save/save-as through the repositories |
| `EventBus`          | Simple publish/subscribe (`subscribe(event, handler)`, `publish(event, payload)`) that keeps the UI decoupled from core |
| `Events` (Enum)     | `MAP_CHANGED`, `SELECTION_CHANGED`, `THEME_CHANGED`, `NODE_NOTE_REQUESTED`      |

---

## 4. Persistence (`mindmuni/file`)

| Class               | Responsibility                                                  |
|---------------------|-----------------------------------------------------------------|
| `MapSerializer`     | `to_document(MindMap)` / `from_document(list)`, splitting map, style and text |
| `ThemeSerializer`   | `to_dict(Theme)` / `from_dict(dict)`                            |
| `JsonFileStore`     | Low-level `read(path) -> dict | list`, `write(path, data)`           |
| `MapRepository`     | `save(map, path)`, `load(path) -> MindMap`, defaults to the app root directory |
| `ThemeRepository`   | `load(name) -> Theme`, `load_custom(path)`, `list_available()`  |

### Map file format (`*.mson`)
A `.mson` file is JSON whose top level is a list of three sections, so the
map's structure, its look and its text are kept apart:

1. **map** – metadata and the node tree: node ids, titles, children.
2. **style** – UI-only properties, in two parts:
   - `map`: styling for the whole map. `layout` is `RIGHT` (all branches grow
     to the right of the root) or `BALANCED` (the root's branches are split
     between its left and right sides). Default `RIGHT`.
   - `nodes`: styling for each node, keyed by `node_id`: shape, color, canvas
     position and collapsed state.
3. **text** – each node's rich-text note, keyed by `node_id`. Only nodes
   that have a note get an entry.

The style and text sections may be missing. A missing `map` entry means the
default map style, a node with no style entry gets the default style, and a node with no text entry has an empty note. Entries
whose `node_id` is not in the map are ignored.

```json
[
  {
    "format_version": 1,
    "map_id": "6f1c…",
    "title": "Project ideas",
    "created_at": "2026-10-18T19:01:00",
    "updated_at": "2026-10-18T19:30:00",
    "root": {
      "node_id": "a1…",
      "title": "Project ideas",
      "children": []
    }
  },
  {
    "map": { "layout": "BALANCED" },
    "nodes": {
      "a1…": {
        "shape": "ELLIPSE",
        "color": "BLUE",
        "position": { "x": 400, "y": 300 },
        "collapsed": false
      }
    }
  },
  {
    "notes": {
      "a1…": {
        "blocks": [
          { "block_type": "HEADING_1", "spans": [{ "text": "Goals", "bold": false, "highlighted": false }] },
          { "block_type": "PARAGRAPH", "spans": [
            { "text": "Ship ", "bold": false, "highlighted": false },
            { "text": "v1", "bold": true, "highlighted": true }
          ]}
        ]
      }
    }
  }
]
```

### Theme file format (`themes/<name>.json`)
```json
{
  "name": "dark",
  "palette": {
    "background": "#1e1e1e",
    "foreground": "#e0e0e0",
    "canvas_background": "#252526",
    "connector_line": "#808080",
    "selection_outline": "#ffcc00",
    "highlight_background": "#665c00",
    "menu_background": "#2d2d2d",
    "menu_foreground": "#e0e0e0",
    "node_colors": {
      "RED": "#e57373", "ORANGE": "#ffb74d", "AMBER": "#ffd54f", "YELLOW": "#fff176",
      "LIME": "#dce775", "GREEN": "#81c784", "TEAL": "#4db6ac", "CYAN": "#4dd0e1",
      "BLUE": "#64b5f6", "INDIGO": "#7986cb", "PURPLE": "#ba68c8", "PINK": "#f06292"
    }
  },
  "fonts": {
    "family": "Helvetica", "base_size": 11,
    "heading_1_size": 20, "heading_2_size": 16, "node_title_size": 11
  }
}
```

---

## 5. UI classes (`mindmuni/ui`)

| Class                 | Responsibility                                                         |
|-----------------------|------------------------------------------------------------------------|
| `MainWindow`          | Owns the `tk.Tk` root, the menu bar and a view container. Swaps between the map view and the text editor view |
| `MenuBar`             | File (New, Save, Save As, Open) and Theme (Dark, Light, Custom…)       |
| `ViewNavigator`       | `show_map_view()` / `show_text_editor(node)`. Back returns to the map view |
| `MappingView`         | Main mapping component: canvas, toolbar, shortcut bindings             |
| `MapCanvas`           | `tk.Canvas` subclass that draws nodes and connectors from the layout   |
| `NodeRenderer`        | Draws one node shape and its label (one method per `NodeShape`)        |
| `ConnectorRenderer`   | Draws parent-to-child lines                                            |
| `MapToolbar`          | Buttons: Add Child, Add Sibling, Delete, Open Note, Shape ▾, Color ▾   |
| `StylePicker`         | Popup with the shape list and a 12-color swatch grid                   |
| `TextEditorView`      | Text component: toolbar plus `tk.Text`, and a Back button              |
| `FormattingToolbar`   | H1, H2, Normal, **Bold**, Highlight buttons                            |
| `RichTextAdapter`     | Converts `NoteDocument` to and from `tk.Text` tags                      |
| `ShortcutMap`         | One place that defines all key bindings                                |

### Default shortcuts
| Action                 | Key            | View   |
|------------------------|----------------|--------|
| Add child              | `Tab`          | Map    |
| Add sibling            | `Enter`        | Map    |
| Delete node            | `Delete`       | Map    |
| Rename node            | `F2`           | Map    |
| Navigate selection     | Arrow keys     | Map    |
| Open node text area    | `Ctrl+E`       | Map    |
| Back to map            | `Esc`          | Editor |
| Heading 1 / Heading 2  | `Ctrl+1` / `Ctrl+2` | Editor |
| Normal text            | `Ctrl+0`       | Editor |
| Bold                   | `Ctrl+B`       | Editor |
| Highlight              | `Ctrl+H`       | Editor |
| New / Open / Save / Save As | `Ctrl+N` / `Ctrl+O` / `Ctrl+S` / `Ctrl+Shift+S` | Global |

---

## 6. Key interactions

**Add child node**
```
Tab key / button → MappingView → MapEditor.add_child(selected_id)
  → EventBus.publish(MAP_CHANGED) → TreeLayout.apply(map) → MapCanvas.redraw()
  → SelectionManager.select(new_node)
```

**Open node text**
```
Ctrl+E / button → ViewNavigator.show_text_editor(node)
  → RichTextAdapter.load(node.note) into tk.Text
Back / Esc → RichTextAdapter.dump() → node.note = … → MAP_CHANGED
  → ViewNavigator.show_map_view()
```

**Switch theme**
```
Menu Theme → Dark → ThemeManager.apply(ThemeRepository.load("dark"))
  → EventBus.publish(THEME_CHANGED) → every view re-styles itself
```
