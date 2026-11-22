# Mind Muni: Mapping UI

The mapping component reads a map file, lays the nodes out as a tree (all
branches to the right of the root, or balanced on both sides) and draws them on a scrollable canvas. It can run on its own through
`map_preview.py`, without the main window or menu bar described in
[ui_core.md](ui_core.md).

See [modules.md](modules.md) for the full package layout and
[object_model.md](object_model.md) for the domain classes. For a step-by-step walkthrough of how
a map is measured, laid out and drawn, see [rendering.md](rendering.md). For how clicking a node selects it,
see [selection.md](selection.md).

---

## 1. Running the preview script

### Prerequisites
- Python 3.12 with tkinter. On Ubuntu/Debian install it with
  `sudo apt install python3-tk`. The python.org builds for Windows and macOS
  already include it.
- Run from the project root so that `mindmuni` can be imported.

### Run it
```
.venv/bin/python map_preview.py          # Linux / macOS
.venv\Scripts\python map_preview.py      # Windows
```
In PyCharm, right-click `map_preview.py` and choose **Run**.

The script always loads one file, set at the top of `map_preview.py`:
```python
MAP_FILE = maps_dir() / "sample.mson"
```
To preview a different map, put it in `maps/` and change this line.

### Controls
| Input | Action |
|-------|--------|
| `T` | Switch between the light and dark themes |
| `L` | Switch between the right and balanced layouts (in memory only; `R` restores the file's layout) |
| `R` | Reload the map file from disk (edit the JSON, then press R) |
| Left-click a node | Select it (yellow/blue outline, from the theme's `selection_outline`) |
| Left-click empty space | Clear the selection |
| `Insert` or the **+ Insert** button | Add a child ("New node") to the selected node, select it and open its title for editing with the text selected, so you can type over it |
| Double-click a node, `F2` or the **✎ Edit** button | Edit the node's title in place |
| While editing a title: `Enter` | Save the title. A blank title is ignored and the old one kept. |
| While editing a title: `Shift` + `Enter` | Start a new line in the title |
| While editing a title: `Esc` | Cancel, keeping the old title |
| While editing a title: `←` `→` `Home` `End`, `Ctrl` + `A` | Move the cursor, select the whole title |
| While editing a title: click elsewhere, zoom, use a toolbar or a `Ctrl` shortcut | Save the title first, then do the action. Clicking the node being edited keeps editing. |
| `Delete` or the **✕ Delete** button | Delete the selected node and its subtree, then select its parent. Disabled for the root. |
| Click a colour swatch (style toolbar) | Set the selected node's colour. The current colour is ringed and its name (e.g. "Red") is shown in the name box. |
| Click a shape icon (style toolbar) | Set the selected node's shape. The current shape is ringed and its name is shown in the name box. The node is kept in place while the layout adjusts to its new size. |
| Left-drag on empty space, or middle-drag | Pan the canvas, only while **Drag: On** is set in the view toolbar. Dragging is locked by default; the scrollbars and mouse wheel always work. |
| Mouse wheel | Scroll up and down |
| Shift + wheel | Scroll sideways |
| Ctrl + wheel | Zoom in or out around the mouse pointer |
| `Ctrl` + `+` / `Ctrl` + `-` | Zoom in / out around the middle of the window |
| `Ctrl` + `0` | Reset the zoom to 100% |
| View toolbar (top-right): **−** / **+** | Zoom out / in around the middle of the window. Greyed out at 25% and 300%. |
| View toolbar: the percentage | Shows the current zoom, however it was changed. Click it to reset to 100%. |
| View toolbar: **Drag: Off** / **Drag: On** | Lock or allow dragging the map around. Off (locked) when the view opens; highlighted while on. |

The edit toolbar floats over the bottom-right corner of the canvas, the
style toolbar over the bottom-left corner and the view toolbar over the
top-right corner; all stay there when the window is resized. The style toolbar has one swatch per `NodeColor` (12 major colours,
shown in the theme's actual shades) and one transparent outline icon per
`NodeShape`. Next to it, a separate name box shows the selected node's colour
and shape names, each on the same line as its row and left-aligned with each
other. An arrow on each row points from the pickers to their name. It is greyed out when
no node is selected. The root is selected when a map is shown.
Edits only change the map in memory: nothing is saved, and `R` throws them
away by reloading the file.

Zoom goes from 25% to 300%, 1.2× per step. It only changes how the map is
drawn: node positions, the layout and the saved file are not affected.

### When something goes wrong
| Symptom | Cause |
|---------|-------|
| `ModuleNotFoundError: No module named 'tkinter'` | tkinter isn't installed. See the prerequisites above. |
| `ModuleNotFoundError: No module named 'mindmuni'` | The script wasn't run from the project root. |
| `MapFormatError: Invalid map file: KeyError('title')` | A node or the map is missing a required field. The error names the field. |
| `ValueError: 'SQUARE' is not a valid NodeShape` (inside `MapFormatError`) | A shape or colour name is misspelled. See the allowed values below. |
| `json.decoder.JSONDecodeError` | The file isn't valid JSON, e.g. a trailing comma or a missing quote. |

---

## 2. Writing a map file

Map files are JSON. The full format is in
[object_model.md §4](object_model.md#4-persistence-mindmunifile). For a
hand-written file, only `root` and each node's `title` are required.
Everything else falls back to a default:

| Field | Default |
|-------|---------|
| `map_id`, `node_id` | A new random id |
| `title` (map) | The root node's title |
| `created_at`, `updated_at` | The current time |
| `style.shape` | `RECTANGLE` |
| `style.color` | `BLUE` |
| `position` | `(0, 0)`. The layout overwrites it anyway. |
| `collapsed` | `false` |
| `note` | An empty note |
| `children` | None |

Minimal example:
```json
{
  "root": {
    "title": "Trip",
    "children": [
      { "title": "Flights", "style": { "shape": "DIAMOND", "color": "ORANGE" } },
      { "title": "Hotels\n(3 options)", "collapsed": true,
        "children": [{ "title": "A" }, { "title": "B" }, { "title": "C" }] }
    ]
  }
}
```

- **Shapes:** `RECTANGLE` (rounded corners), `ELLIPSE`, `DIAMOND`, `HEXAGON`, `CLOUD`, `STAR` (yantra-style: an upward and a downward equilateral triangle).
- **Colours:** `RED`, `ORANGE`, `AMBER`, `YELLOW`, `LIME`, `GREEN`, `TEAL`, `CYAN`, `BLUE`, `INDIGO`, `PURPLE`, `PINK`
- **Multi-line titles:** use `\n` inside the title.
- **Collapsed nodes:** their children are hidden, and the node shows a badge with the number of hidden children.

`maps/sample.mson` uses every shape, a multi-line title, a collapsed
node and a rich-text note, so it's a good file to copy from.

---

## 3. Files

### Preview script and sample data
| File | Contains |
|------|----------|
| `map_preview.py` | `MapPreview` creates a bare `tk.Tk` window, puts a `MappingView` in it, loads `MAP_FILE` through `MapRepository`, and binds `T` (theme), `L` (layout), `R` (reload) and the zoom shortcuts. It's a test harness only; the real app will use `MainWindow` and `ViewNavigator` instead. |
| `maps/sample.mson` | The sample map the preview loads. |

### `mindmuni/file/`: persistence
| File | Contains |
|------|----------|
| `json_file_store.py` | `JsonFileStore` reads and writes JSON files (a dict or a list) (UTF-8, indented). `write()` saves to a `.tmp` file first and then replaces the target, so a crash never leaves a half-written map. |
| `map_serializer.py` | `MapSerializer.to_document(map)` and `from_document(document)` convert between a `MindMap` and the `.mson` format: a JSON list `[map, style, text]`. The map section holds the node tree and titles, the style section holds map-wide styling (`map.layout`: `RIGHT` or `BALANCED`) and each node's shape, color, position and collapsed state, and the text section holds each node's note. Style and text are keyed by `node_id`. Missing optional fields get defaults. Bad content raises `MapFormatError`, and so does a `format_version` newer than `FORMAT_VERSION`. |
| `map_repository.py` | `MapRepository.load(path)` and `save(map, path)` combine the store and the serializer. `save` also updates the map's `updated_at`. |
| `__init__.py` | Re-exports `JsonFileStore`, `MapSerializer`, `MapFormatError` and `MapRepository`. |

### `mindmuni/core/`: layout
| File | Contains |
|------|----------|
| `map_editor.py` | `MapEditor` is the only code that changes the node tree. `add_child(map, parent_id)` appends a `"New node"` child (expanding a collapsed parent) and returns it. `delete_node(map, node_id)` removes the node with its subtree and returns the parent; it raises `ValueError` for the root. `can_delete()` says whether a node may be deleted. `set_title(map, node_id, title)` strips the title, refuses a blank one (`ValueError`) and returns whether it changed. `set_color(map, node_id, color)` and `set_shape(map, node_id, shape)` change a node's style and return whether anything changed. |
| `selection_manager.py` | `SelectionManager` holds the selected node id (`select`, `clear`, `selected_id`, `selected_node(map)`). Keyboard navigation will go here. |
| `tree_layout.py` | `TreeLayout(measure_node, spacing).apply(map)` sets `Node.position` (each node's centre) for every visible node, following `map.style.layout`. With `RIGHT`, the root is on the left and every branch grows to the right. With `BALANCED`, the root's branches are split in order, with the first ones on the right and the rest on the left, so the two sides are about the same height; the left side is a mirror image. Each side has one column per depth, as wide as the widest node in it on that side. Each parent is centred vertically on its children, and collapsed branches are skipped. Node sizes come from the injected `measure_node` function, so this file has no Tkinter code. `LayoutSpacing` sets the column gap, the sibling gap and the origin. `visible_children(node)` returns no children for a collapsed node. |

### `mindmuni/ui/mapping_main/`: the mapping component (Tkinter)
| File | Contains |
|------|----------|
| `mapping_view.py` | `MappingView` is a `View` subclass and the component's public entry point. It owns a `MapEditor`, a `SelectionManager` and the `MapToolbar`; `insert_node()` and `delete_selected_node()` edit the map, `set_selected_color(color)` and `set_selected_shape(shape)` restyle the selected node (a colour change only redraws; a shape change re-runs the layout because the node's size changes), then redraw and scroll so the edited node's parent stays put on screen. `show_map(map)` runs the layout, draws the map and centres the view on the root. The three toolbars stay hidden until the first `show_map()`, so an empty view shows only the canvas. `set_layout(layout)` changes the map's `style.layout` and redraws. `zoom_in()`, `zoom_out()`, `reset_zoom()` and the `zoom` property pass through to the canvas, and the `ViewToolbar` calls them. `toggle_drag()`, `set_drag_enabled(enabled)` and the `drag_enabled` property lock or allow dragging the map and keep the toolbar's toggle in step. `apply_theme(theme)` restyles and redraws, and re-runs the layout because font sizes can change. It wraps the canvas with scrollbars. |
| `map_canvas.py` | `MapCanvas` is a `tk.Canvas`. `apply_theme()` builds the renderers for the theme, `measure_node()` is passed to `TreeLayout`, `draw_map()` draws connectors first and nodes on top, and `center_on(point)` scrolls to a point. It also handles drag-to-pan (only while `set_drag_enabled(True)`; `drag_enabled` is `False` by default, and a left press on empty space still counts as a click either way), wheel scrolling (Linux uses `Button-4/5`, Windows and macOS use `MouseWheel`), zoom, and clicks: `on_node_click(handler)` reports the id of a clicked node, or `None` for a click on empty space; `on_node_double_click(handler)` reports a double-clicked node. `on_before_zoom(handler)` runs before each zoom change (the view uses it to save an open title edit) and `on_zoom_changed(handler)` after it, however the zoom was changed (the view uses it to update the zoom toolbar). `can_zoom_in` / `can_zoom_out` say whether the zoom is below `MAX_ZOOM` / above `MIN_ZOOM`. A left press on a node selects it; a left press on empty space starts a pan, and counts as a click if released within 3px. Zoom is a view-only transform: node positions stay in map units and the canvas draws map point `p` at `p * zoom`, so zooming redraws without re-running the layout. `set_zoom(zoom, anchor_x, anchor_y)` clamps the zoom to `MIN_ZOOM`..`MAX_ZOOM` and keeps the map point under the anchor (the mouse pointer for Ctrl+wheel, otherwise the middle of the window) in place. |
| `title_editor.py` | `TitleEditor` edits a title in place by typing straight into the node's title text item on the canvas (found by its `"title"` tag), using Tk's canvas text editing (`focus`, `icursor`, `insert`, `dchars`, `select_*`). No widget is laid over the node, so the text keeps the node's colours and font and nothing can flash when editing ends; the cursor is drawn in the title's text colour. It handles typing, BackSpace, Delete, Left/Right, Home/End, Ctrl+A, Shift+Enter (new line), Enter (save) and Esc (cancel). Ctrl and Alt shortcuts save first and then run. While editing, the canvas's bind tags leave out the toplevel, so window shortcuts such as `Insert`, `Delete` or `T` don't fire; `bind_all` shortcuts still do. `start(node, theme, select_all)` begins, `finish()` saves through `on_commit(node_id, title)` (only when the title changed and isn't blank) and `cancel()` puts the old title back. The text item belongs to the current drawing, so `MappingView` calls `finish()` before anything redraws. |
| `view_toolbar.py` | `ViewToolbar` is the floating view toolbar: **−**, the zoom percentage (a button that resets to 100%), **+**, and the **Drag** toggle. `show_zoom(zoom, can_zoom_out, can_zoom_in)` updates the percentage and greys out a button at the zoom limits; `show_drag(enabled)` switches the toggle between "Drag: Off" and a highlighted "Drag: On". The percentage and the toggle have fixed widths so the toolbar doesn't resize. `pin_to(widget)` places it over the widget's top-right corner. |
| `map_toolbar.py` | `MapToolbar` is the floating edit toolbar (**+ Insert**, **✎ Edit**, **✕ Delete**). It uses plain `tk` widgets coloured from the theme, so it looks right with or without `ThemeStyler`. `pin_to(widget)` places it over the widget's bottom-right corner with `place(relx=1, rely=1, anchor="se")`, so it follows resizes. `create_toolbar_button()` and `style_toolbar_button()` make and theme the flat buttons shared with `ViewToolbar`. `set_enabled(insert, edit, delete)` greys out buttons that can't be used. |
| `style_toolbar.py` | `StyleToolbar` is the floating colour and shape picker: a row of swatches (one per `NodeColor`, so the palette stays limited to the colours defined in the model) and a row of shape icons (one per `NodeShape`, drawn with `draw_shape` as transparent outlines in the theme's menu text colour). The toolbar is two separate bordered boxes side by side, the picker box and the name box, with a small canvas between them that draws one arrow per row (at the row's centre height; greyed out when nothing is selected), inside a borderless container that takes the canvas colour, so only the boxes show. Both boxes use the same border, padding and row heights, so each name lines up with its picker row. `style_label()` turns an enum value into its shown name (e.g. "Red", "Hexagon"). Each swatch and icon is a small `tk.Canvas`. `show_style(color, shape)` rings the current colour and shape and shows their names, or greys everything out and clears the names when given `None`. `pin_to(widget)` places it over the widget's bottom-left corner. |
| `node_renderer.py` | `NodeRenderer.measure(node)` sizes a node from its title text, in map units (zoom 1). `draw()` scales positions, sizes, line widths and fonts by the renderer's zoom; the zoomed font size is rounded down so the text always fits its box. `SHAPE_SCALE` makes the box bigger for shapes such as diamonds, ellipses and clouds so the text still fits inside; a star is sized from its title instead so its triangles stay equilateral. `edge_half_width(node)` says where connectors and the collapsed badge attach. `draw(node, grows_left)` draws the shape (through `draw_shape`), the title (in dark or light text for contrast) and the collapsed-children badge, which sits on the side the node's children grow towards. Every item it draws is tagged `"node"` and `node_tag(node_id)` (= `"node:<id>"`); `node_id_from_tags()` reads the id back for click selection. A selected node gets a thicker outline in the theme's `selection_outline` colour. |
| `shape_drawing.py` | `draw_shape(canvas, shape, …)` draws one `NodeShape` filling a box, used by both `NodeRenderer` and `StyleToolbar`. `fill=""` gives a transparent outline. A star is drawn as two filled triangles followed by both triangles' outlines, so every edge of each triangle shows. |
| `connector_renderer.py` | `ConnectorRenderer.draw(parent, child)` draws a smooth curve, tagged `"connector"`, from the parent's right edge to the child's left edge, or the other way round when the child is to the parent's left. Edges come from `NodeRenderer.edge_half_width()`, so connectors meet a star at its side corners. |
| `__init__.py` | Re-exports `MappingView`, `MapCanvas` and `MAP_VIEW_ID`. |

### `mindmuni/utils/`: helpers with no domain knowledge
| File | Contains |
|------|----------|
| `shape_geometry.py` | Outline points for each shape: `bounding_box`, `diamond`, `hexagon`, `rounded_rectangle`, `cloud` and `star_triangles` (the star's upward and downward equilateral triangles), with `star_box_for_content` and `star_mid_height_half_width` for sizing it and finding its side corners. Rounded rectangles and clouds are drawn with `smooth=True`. |
| `color_utils.py` | `contrast_text_color(background)` picks dark or light text, `darken(hex, fraction)` makes the node outlines, and there are hex/RGB conversion helpers. |
| `paths.py` | `maps_dir()` is where the preview looks for `MAP_FILE`. |

### `mindmuni/model/`
| File | Change |
|------|--------|
| `geometry.py` | Added `Size(width, height)`, which `NodeRenderer.measure` returns and `TreeLayout` uses. |

---

## 4. How a map gets on screen

```
map_preview.py
  MapRepository.load(MAP_FILE)
    JsonFileStore.read()  ──► [map, style, text]
    MapSerializer.from_document() ──► MindMap
  MappingView.show_map(mind_map)
    TreeLayout.apply(mind_map)
      MapCanvas.measure_node ──► NodeRenderer.measure   (size of every visible node)
      sets node.position for every visible node
    MapCanvas.draw_map(mind_map)
      ConnectorRenderer.draw  (one per parent → child pair, drawn first)
      NodeRenderer.draw       (shape, title, badge, drawn on top)
      scroll region = everything drawn + margin
    MapCanvas.center_on(root.position)
```

On a theme switch (`T`), `MappingView.apply_theme()` builds new renderers with
the new colours and fonts, then runs the same layout and drawing steps again.

---

## 5. Not yet implemented
- Selecting a node with the arrow keys.
- Editing: add sibling. Undo.
- Saving edits back to the file.
- Opening a node's note in the text editor (Ctrl+E).
