# Mind Muni: Mapping UI

The mapping component reads a map file, lays the nodes out as a tree (all
branches to the right of the root, or balanced on both sides) and draws them on a scrollable canvas. It can run on its own through
`map_preview.py`, without the main window or menu bar described in
[ui_core.md](ui_core.md).

See [modules.md](modules.md) for the full package layout and
[object_model.md](object_model.md) for the domain classes.

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
| Left-drag | Pan the canvas |
| Mouse wheel | Scroll up and down |
| Shift + wheel | Scroll sideways |
| Ctrl + wheel | Zoom in or out around the mouse pointer |
| `Ctrl` + `+` / `Ctrl` + `-` | Zoom in / out around the middle of the window |
| `Ctrl` + `0` | Reset the zoom to 100% |

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
| `style.shape` | `ROUNDED_RECTANGLE` |
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

- **Shapes:** `RECTANGLE`, `ROUNDED_RECTANGLE`, `ELLIPSE`, `DIAMOND`, `HEXAGON`, `CLOUD`
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
| `tree_layout.py` | `TreeLayout(measure_node, spacing).apply(map)` sets `Node.position` (each node's centre) for every visible node, following `map.style.layout`. With `RIGHT`, the root is on the left and every branch grows to the right. With `BALANCED`, the root's branches are split in order, with the first ones on the right and the rest on the left, so the two sides are about the same height; the left side is a mirror image. Each side has one column per depth, as wide as the widest node in it on that side. Each parent is centred vertically on its children, and collapsed branches are skipped. Node sizes come from the injected `measure_node` function, so this file has no Tkinter code. `LayoutSpacing` sets the column gap, the sibling gap and the origin. `visible_children(node)` returns no children for a collapsed node. |

### `mindmuni/ui/mapping_main/`: the mapping component (Tkinter)
| File | Contains |
|------|----------|
| `mapping_view.py` | `MappingView` is a `View` subclass and the component's public entry point. `show_map(map)` runs the layout, draws the map and centres the view on the root. `set_layout(layout)` changes the map's `style.layout` and redraws. `zoom_in()`, `zoom_out()`, `reset_zoom()` and the `zoom` property pass through to the canvas. `apply_theme(theme)` restyles and redraws, and re-runs the layout because font sizes can change. It wraps the canvas with scrollbars. |
| `map_canvas.py` | `MapCanvas` is a `tk.Canvas`. `apply_theme()` builds the renderers for the theme, `measure_node()` is passed to `TreeLayout`, `draw_map()` draws connectors first and nodes on top, and `center_on(point)` scrolls to a point. It also handles drag-to-pan, wheel scrolling (Linux uses `Button-4/5`, Windows and macOS use `MouseWheel`) and zoom. Zoom is a view-only transform: node positions stay in map units and the canvas draws map point `p` at `p * zoom`, so zooming redraws without re-running the layout. `set_zoom(zoom, anchor_x, anchor_y)` clamps the zoom to `MIN_ZOOM`..`MAX_ZOOM` and keeps the map point under the anchor (the mouse pointer for Ctrl+wheel, otherwise the middle of the window) in place. |
| `node_renderer.py` | `NodeRenderer.measure(node)` sizes a node from its title text, in map units (zoom 1). `draw()` scales positions, sizes, line widths and fonts by the renderer's zoom; the zoomed font size is rounded down so the text always fits its box. `SHAPE_SCALE` makes the box bigger for shapes such as diamonds, ellipses and clouds so the text still fits inside. `draw(node, grows_left)` draws the shape, the title (in dark or light text for contrast) and the collapsed-children badge, which sits on the side the node's children grow towards. Every item it draws is tagged `"node"` and `node_tag(node_id)` (= `"node:<id>"`), ready for click selection later. |
| `connector_renderer.py` | `ConnectorRenderer.draw(parent, parent_size, child, child_size)` draws a smooth curve, tagged `"connector"`, from the parent's right edge to the child's left edge, or the other way round when the child is to the parent's left. |
| `__init__.py` | Re-exports `MappingView`, `MapCanvas` and `MAP_VIEW_ID`. |

### `mindmuni/utils/`: helpers with no domain knowledge
| File | Contains |
|------|----------|
| `shape_geometry.py` | Outline points for each shape: `bounding_box`, `diamond`, `hexagon`, `rounded_rectangle` and `cloud`. Rounded rectangles and clouds are drawn with `smooth=True`. |
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
- Selecting a node by click or with the arrow keys. Left-drag currently pans, so panning will move to the middle button or to dragging on empty space.
- Editing: add child (Tab), add sibling (Enter), delete, rename (F2), and choosing shape and colour (`MapEditor`, `MapToolbar`, `StylePicker`).
- Opening a node's note in the text editor (Ctrl+E).
- Registering `MappingView` in `app.py` in place of the `"map"` placeholder.
