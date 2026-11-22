# Mind Muni: How a Map Is Rendered

This document explains how a `MindMap` goes from a `.mson` file to shapes on
a Tkinter canvas. It covers the order of the steps, the coordinate systems,
and which class owns each step.

For running the preview and writing map files, see
[mapping_ui.md](mapping_ui.md). For the domain classes, see
[object_model.md](object_model.md).

---

## 1. Overview

Rendering has four stages. Each one has a single owner:

| # | Stage | Owner | Tkinter? |
|---|-------|-------|----------|
| 1 | Load the file into a `MindMap` | `MapRepository` → `JsonFileStore` + `MapSerializer` | No |
| 2 | Measure every visible node | `NodeRenderer.measure` (called through `MapCanvas.measure_node`) | Yes (fonts) |
| 3 | Lay the tree out (set `Node.position`) | `TreeLayout.apply` | No |
| 4 | Draw connectors, then nodes | `MapCanvas.draw_map` → `ConnectorRenderer`, `NodeRenderer` | Yes |

```
MapRepository.load(path)
  JsonFileStore.read()            ──► [map, style, text]   (raw JSON list)
  MapSerializer.from_document()   ──► MindMap

MappingView.show_map(mind_map)
  _redraw()
    TreeLayout.apply(mind_map)                   stages 2 + 3
      _measure_visible_nodes  ─► MapCanvas.measure_node ─► NodeRenderer.measure
      _compute_subtree_heights
      _split_branches          (RIGHT or BALANCED)
      _build_side × 2          (column widths and offsets per depth)
      _root_position
      _place_branches          (sets node.position, recursively)
    MapCanvas.draw_map(mind_map)                 stage 4
      delete("all")
      _draw_connectors   ─► ConnectorRenderer.draw   (drawn first, so they sit underneath)
      _draw_nodes        ─► NodeRenderer.draw        (shape, title, collapsed badge)
      _update_scroll_region
  after_idle: MapCanvas.center_on(root.position)
```

The layout (`mindmuni/core/tree_layout.py`) has no Tkinter code. It only
needs a function `Node -> Size`, which `MappingView` supplies as
`MapCanvas.measure_node`. This keeps the layout testable without a display.

---

## 2. Coordinate systems

There are two units:

- **Map units**: what `Node.position` and `NodeRenderer.measure()` use.
  They are canvas pixels at 100% zoom. `Node.position` is the node's
  **centre**, not its top-left corner.
- **Canvas units**: what is actually drawn. Map point `p` is drawn at
  `p * zoom`.

Zoom is applied **only at draw time**. Measuring and layout always happen at
zoom 1, so zooming never moves nodes relative to each other, never re-runs
the layout, and never changes what gets saved.

The canvas's own scrolling (`xview`/`yview`) sits on top of canvas units.
`MapCanvas._scroll_to(point, window_x, window_y)` converts between the three:
it puts map point `point` at the window pixel `(window_x, window_y)`.

---

## 3. Stage 2: measuring a node

`NodeRenderer.measure(node)` in `mindmuni/ui/mapping_main/node_renderer.py`:

1. Splits the title on newlines. The text width is the widest line measured
   with the theme's title font (`theme.fonts.family`,
   `theme.fonts.node_title_size`); the text height is
   `linespace × number of lines`.
2. Adds padding and applies minimums:
   - width = `max(text_width, MIN_TEXT_WIDTH) + 2 × HORIZONTAL_PADDING`
   - height = `max(text_height + 2 × VERTICAL_PADDING, MIN_NODE_HEIGHT)`
3. Multiplies by `SHAPE_SCALE[shape]`. Shapes that cut into their bounding
   box need a larger box for the text to stay inside:

   | Shape | Width × | Height × |
   |-------|---------|----------|
   | `RECTANGLE` | 1.0 | 1.0 |
   | `HEXAGON` | 1.15 | 1.0 |
   | `ELLIPSE` | 1.3 | 1.3 |
   | `CLOUD` | 1.4 | 1.4 |
   | `DIAMOND` | 1.7 | 1.7 |

   `STAR` doesn't use a scale. Its triangles must stay equilateral, so
   `_measure_star` finds the smallest star whose inner hexagon holds the title
   plus a 4px margin (`shape_geometry.star_box_for_content`). The box is then
   √3/2 × the point radius on each side horizontally and the point radius
   vertically. Long titles make big stars.

The result is the node's outer bounding box in map units. Because the size
depends on the font, **a theme change can change the layout**, which is why
`MappingView.apply_theme` re-runs the layout and not just the drawing.

---

## 4. Stage 3: layout

`TreeLayout.apply(mind_map)` sets `position` on every **visible** node. A
node's children are visible unless it is `collapsed`
(`visible_children(node)` returns `[]` for a collapsed node). Hidden nodes
keep whatever position they had.

### 4.1 Subtree heights
`_compute_subtree_heights` works bottom-up. A node's subtree height is the
larger of its own height and the height of its children stacked with
`vertical_gap` (16) between them.

### 4.2 Splitting the root's branches
- `RIGHT` (or fewer than two branches): every branch goes on the right.
- `BALANCED`: branches are taken **in order** onto the right side until the
  right side reaches half the total stacked height; the rest go on the left.
  At least one branch always ends up on the left.

### 4.3 Columns
Each side (`_Side`) has one column per depth. Column 0 is the root. A
column's width is the widest visible node at that depth **on that side**.
Column centres are spaced so that neighbouring columns are
`horizontal_gap` (60) apart edge to edge:

```
offset[d] = offset[d-1] + width[d-1]/2 + horizontal_gap + width[d]/2
```

Every node at the same depth on the same side shares the same x, so columns
line up even when titles have different widths.

### 4.4 Placing
- The root is placed so the whole tree's top-left corner is at
  `LayoutSpacing.origin`: x = origin.x + how far the left side reaches,
  y = origin.y + half the tallest of (root, right side, left side).
- `_place_branches` stacks each side's branches top to bottom, centred on
  the root's y.
- `_place_subtree` recurses: a node's x is
  `root.x + direction × column_offsets[depth]` (direction is `+1` right,
  `-1` left, so the left side is a mirror image), and its y is the middle
  of its subtree's band. Its children are stacked inside that band, so
  **every parent is centred vertically on its children**.

---

## 5. Stage 4: drawing

`MapCanvas.draw_map` clears the canvas and redraws everything. There is no
incremental update: every theme change, layout change or zoom step redraws
the whole map.

### 5.1 Traversal
`iter_visible_nodes(root)` walks the visible tree depth-first, pre-order, in
child order. It skips the children of collapsed nodes.

### 5.2 Connectors (drawn first)
`ConnectorRenderer.draw(parent, child)` draws one
smoothed `create_line` per visible parent → child pair, so connectors are
under the nodes:

- If the child is right of the parent: from the parent's right edge
  (`x + NodeRenderer.edge_half_width(parent)`) to the child's left edge.
  The edge is where the outline crosses the node's centre height. For every
  shape that's `width/2`, except the star, whose side corners sit inside its
  outer points. The collapsed badge sits on the same edge.
- If it is to the left: from the parent's left edge to the child's right edge.
- The four control points are start → (mid-x, start-y) → (mid-x, end-y) →
  end. With `smooth=True`, Tk turns them into an S-curve.
- Colour: `theme.palette.connector_line`. Width: `2 × zoom`, at least 1px.
- Tag: `"connector"`.

### 5.3 Nodes (drawn on top)
`NodeRenderer.draw(node, grows_left)` draws three things, all tagged
`"node"` and `"node:<node_id>"` so a whole node can be found or hit-tested
by tag later:

1. **Shape.** Fill is `palette.color_for(node.style.color)`; outline is that
   colour darkened by 30% (`color_utils.darken`). The outline points come from
   `mindmuni/utils/shape_geometry.py`, all scaled by zoom, and
   `mindmuni/ui/mapping_main/shape_drawing.py` (`draw_shape`) makes the Tk calls:

   | Shape | Tk call | Geometry |
   |-------|---------|----------|
   | `ELLIPSE` | `create_oval` | `bounding_box` |
   | `RECTANGLE` | `create_polygon(smooth=True)` | `rounded_rectangle`: each corner point is doubled so the straight edges stay straight after smoothing; radius `10 × zoom` |
   | `DIAMOND` | `create_polygon` | `diamond`: the four edge midpoints |
   | `HEXAGON` | `create_polygon` | `hexagon`: flat top and bottom, slanted sides inset by `0.6 × half_height` |
   | `CLOUD` | `create_polygon(smooth=True)` | `cloud`: 20 points around an ellipse, alternating between full and 86% radius, which smoothing turns into 10 bumps |
   | `STAR` | `create_polygon` × 4 | `star_triangles`: a yantra-style six-pointed star (shatkona), an upward and a downward equilateral triangle. They are never stretched: the star is the largest that fits the box. Both are filled first, then both are outlined, so all six edges show. |

   A selected node's outline uses `palette.selection_outline` instead, at
   `4 × zoom` wide.

2. **Title.** `create_text` at the node's centre, centre-justified. Text
   colour is dark (`#1a1a1a`) or white depending on the fill's luminance
   (`color_utils.contrast_text_color`, threshold 0.55). The font size is
   `int(title_size × zoom)`, rounded **down** so zoomed text never outgrows
   its zoomed box.

3. **Collapsed badge** (only if `collapsed` and the node has children). A
   circle of radius `9 × zoom` with the number of hidden children, sitting
   on the node's edge on the side its children grow towards. `MapCanvas`
   passes `grows_left=True` for nodes left of the root.

### 5.4 Scroll region
After drawing, `_update_scroll_region` sets the scroll region to the
bounding box of everything drawn plus `SCROLL_MARGIN` (120) on every side.

---

## 6. What triggers a redraw

| Trigger | Measure | Layout | Draw | Scroll afterwards |
|---------|:-------:|:------:|:----:|-------------------|
| `MappingView.show_map(map)` (zoom set first from `MapStyle.zoom` by `MapCanvas.restore_zoom`) | ✓ | ✓ | ✓ | Centre on the root |
| `MappingView.set_layout(layout)` | ✓ | ✓ | ✓ | Centre on the root |
| `MappingView.apply_theme(theme)` | ✓ | ✓ | ✓ | Unchanged |
| `MapCanvas.set_zoom(...)` (wheel, `Ctrl` `+`/`-`/`0`) | — | — | ✓ | Keep the anchor point fixed |
| Insert / Delete (`MappingView.insert_node`, `delete_selected_node`) | ✓ | ✓ | ✓ | Keep the edited node's parent where it was on screen |
| Click to select | — | — | ✓ | Unchanged |
| Pan / scroll | — | — | — | Tk scrolls the existing items |

On a theme change, `MapCanvas.apply_theme` sets the canvas background and
builds new `NodeRenderer` and `ConnectorRenderer` objects (they hold the
palette and fonts). On a zoom change, `set_zoom` also rebuilds the renderers
(they hold the zoom and the zoomed fonts), redraws, then scrolls so the map
point that was under the anchor (the mouse pointer, or the window centre) is
still under it. Zoom is clamped to 25%–300%. After every zoom change
`MappingView` copies the zoom into `MapStyle.zoom`, so it is saved with the map.

`show_map` and `set_layout` centre on the root with `after_idle`, because the
window may not have its final size until Tk has processed pending events.

---

## 7. Files involved

| File | Role in rendering |
|------|-------------------|
| `mindmuni/ui/mapping_main/mapping_view.py` | `MappingView`: entry point. Owns the `TreeLayout` and the `MapCanvas` with its scrollbars; runs layout + draw. |
| `mindmuni/ui/mapping_main/map_canvas.py` | `MapCanvas`: zoom, scroll region, panning, wheel handling, draw order. |
| `mindmuni/ui/mapping_main/node_renderer.py` | `NodeRenderer`: measures and draws one node. |
| `mindmuni/ui/mapping_main/map_toolbar.py` | `MapToolbar`: the edit toolbar. It is a separate widget placed over the canvas, not drawn on it, so it doesn't scroll or zoom with the map. |
| `mindmuni/ui/mapping_main/connector_renderer.py` | `ConnectorRenderer`: draws one parent → child curve. |
| `mindmuni/core/tree_layout.py` | `TreeLayout`, `LayoutSpacing`, `visible_children`: positions, no Tkinter. |
| `mindmuni/ui/mapping_main/shape_drawing.py` | `draw_shape`: the Tk calls for each shape, shared with the style toolbar. |
| `mindmuni/utils/shape_geometry.py` | Polygon points for each shape. |
| `mindmuni/utils/color_utils.py` | Text contrast and outline darkening. |
| `mindmuni/model/theme.py` | `ThemePalette` (colours, `color_for`) and `FontSettings`. |

---

## 8. Known limits

- **Full redraw every time.** Fine for small and medium maps; large maps may
  feel slow when zooming, since each step deletes and recreates every item.
- **Repeated measuring.** Drawing calls `measure()` again for each connector
  end and each node (layout already computed these sizes). Caching the sizes
  from the layout pass would avoid the extra font measurements.
- **Text at odd zoom levels.** Text is measured at zoom 1 and drawn with a
  rounded-down font size, so at some zoom levels the text looks slightly
  small for its box.
