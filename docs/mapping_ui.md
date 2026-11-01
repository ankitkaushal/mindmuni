# Mind Muni: Mapping UI

The mapping component reads a map file, lays the nodes out as a left-to-right
tree and draws them on a scrollable canvas. It can run on its own through
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
MAP_FILE = maps_dir() / "sample.mindmuni.json"
```
To preview a different map, put it in `maps/` and change this line.

### Controls
| Input | Action |
|-------|--------|
| `T` | Switch between the light and dark themes |
| `R` | Reload the map file from disk (edit the JSON, then press R) |
| Left-drag | Pan the canvas |
| Mouse wheel | Scroll up and down |
| Shift + wheel | Scroll sideways |

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

`maps/sample.mindmuni.json` uses every shape, a multi-line title, a collapsed
node and a rich-text note, so it's a good file to copy from.

---

## 3. Files

### Preview script and sample data
| File | Contains |
|------|----------|
| `map_preview.py` | `MapPreview` creates a bare `tk.Tk` window, puts a `MappingView` in it, loads `MAP_FILE` through `MapRepository`, and binds `T` (theme) and `R` (reload). It's a test harness only; the real app will use `MainWindow` and `ViewNavigator` instead. |
| `maps/sample.mindmuni.json` | The sample map the preview loads. |

### `mindmuni/file/`: persistence
| File | Contains |
|------|----------|
| `json_file_store.py` | `JsonFileStore` reads and writes JSON files (UTF-8, indented). `write()` saves to a `.tmp` file first and then replaces the target, so a crash never leaves a half-written map. |
| `map_serializer.py` | `MapSerializer.to_dict(map)` and `from_dict(data)` convert between a `MindMap` (with its nodes, styles, positions and notes) and the JSON format. Missing optional fields get defaults. Bad content raises `MapFormatError`, and so does a `format_version` newer than `FORMAT_VERSION`. |
| `map_repository.py` | `MapRepository.load(path)` and `save(map, path)` combine the store and the serializer. `save` also updates the map's `updated_at`. |
| `__init__.py` | Re-exports `JsonFileStore`, `MapSerializer`, `MapFormatError` and `MapRepository`. |

### `mindmuni/core/`: layout
| File | Contains |
|------|----------|
| `tree_layout.py` | `TreeLayout(measure_node, spacing).apply(map)` sets `Node.position` (each node's centre) for every visible node. The root is on the left and there is one column per depth, as wide as the widest node in it. Each parent is centred vertically on its children, and collapsed branches are skipped. Node sizes come from the injected `measure_node` function, so this file has no Tkinter code. `LayoutSpacing` sets the column gap, the sibling gap and the origin. `visible_children(node)` returns no children for a collapsed node. |

### `mindmuni/ui/mapping_main/`: the mapping component (Tkinter)
| File | Contains |
|------|----------|
| `mapping_view.py` | `MappingView` is a `View` subclass and the component's public entry point. `show_map(map)` runs the layout, draws the map and centres the view on the root. `apply_theme(theme)` restyles and redraws, and re-runs the layout because font sizes can change. It wraps the canvas with scrollbars. |
| `map_canvas.py` | `MapCanvas` is a `tk.Canvas`. `apply_theme()` builds the renderers for the theme, `measure_node()` is passed to `TreeLayout`, `draw_map()` draws connectors first and nodes on top, and `center_on(point)` scrolls to a point. It also handles drag-to-pan and wheel scrolling (Linux uses `Button-4/5`, Windows and macOS use `MouseWheel`). |
| `node_renderer.py` | `NodeRenderer.measure(node)` sizes a node from its title text. `SHAPE_SCALE` makes the box bigger for shapes such as diamonds, ellipses and clouds so the text still fits inside. `draw(node)` draws the shape, the title (in dark or light text for contrast) and the collapsed-children badge. Every item it draws is tagged `"node"` and `node_tag(node_id)` (= `"node:<id>"`), ready for click selection later. |
| `connector_renderer.py` | `ConnectorRenderer.draw(parent, parent_size, child, child_size)` draws a smooth curve from the parent's right edge to the child's left edge, tagged `"connector"`. |
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
    JsonFileStore.read()  ──► dict
    MapSerializer.from_dict() ──► MindMap
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
