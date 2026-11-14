# Mind Muni: Node Selection

This document explains how a node gets selected on the map: where the
selection is stored, how a click becomes a node id, how the selected node is
drawn, and how selection interacts with editing, zoom and themes.

See [rendering.md](rendering.md) for how the map itself is drawn, and
[mapping_ui.md](mapping_ui.md) for the controls.

---

## 1. Overview

At most one node is selected at a time. Four classes are involved:

| Class | File | Role |
|-------|------|------|
| `SelectionManager` | `mindmuni/core/selection_manager.py` | Stores the selected node's **id**. No Tkinter. |
| `MapCanvas` | `mindmuni/ui/mapping_main/map_canvas.py` | Turns a mouse click into a node id (or `None`), and passes the selected id to the renderer when drawing. |
| `NodeRenderer` | `mindmuni/ui/mapping_main/node_renderer.py` | Tags every item of a node with `node:<id>`, and draws the selected node's outline differently. |
| `MappingView` | `mindmuni/ui/mapping_main/mapping_view.py` | Connects the three: handles clicks, updates the selection, redraws, and enables or disables the toolbar buttons. |

```
mouse press on canvas
  MapCanvas._on_left_press
    _node_id_at(x, y)                     hit-test: topmost item tagged "node:<id>"
      ├─ node found  ─► on_node_click(node_id)
      └─ empty space ─► start a pan (if dragging is on);  on release within 3px ─► on_node_click(None)

MappingView._on_node_click(node_id)
  same as current selection? ─► do nothing
  SelectionManager.select(node_id)
  MapCanvas.draw_map(map, node_id)        redraw only, no new layout
    NodeRenderer.draw(node, selected=…)   selection_outline colour, thicker line
  _update_toolbar()                       Insert / Delete enabled or greyed out
```

---

## 2. Where the selection is stored

`SelectionManager` holds a single `selected_id: str | None`. It stores the
**id**, not the `Node` object, so:

- it stays valid when the layout moves nodes around (positions change, ids don't);
- `selected_node(mind_map)` looks the node up with `MindMap.find_node()` and
  returns `None` if nothing is selected **or** if the node is no longer in
  the map. A deleted node can therefore never be returned as "selected".

`MappingView` owns one `SelectionManager`. The canvas keeps its own copy of
the selected id (`MapCanvas._selected_id`) only so it can redraw the
selection when zooming; `MappingView` sets it each time it calls
`draw_map(map, selected_id)`.

---

## 3. From a click to a node id

### 3.1 Tagging
`NodeRenderer.draw()` gives every canvas item it creates for a node (the
shape, the title text and the collapsed badge) two tags:

- `"node"`: shared by all node items;
- `node_tag(node_id)` = `"node:<node_id>"`: unique to that node.

Connectors are tagged `"connector"` only, so they are never hit as nodes.

`node_id_from_tags(tags)` reads the id back: it returns the text after
`"node:"` from the first tag with that prefix, or `None`.

### 3.2 Hit-testing
`MapCanvas._node_id_at(window_x, window_y)`:

1. Converts the window pixel to canvas coordinates with `canvasx()` /
   `canvasy()`, which accounts for scrolling. Zoom needs no extra step,
   because items are already drawn at zoomed coordinates.
2. Asks Tk for every item at that point with `find_overlapping(x, y, x, y)`.
3. Walks the result **from the top** (the list is in stacking order, so it is
   reversed) and returns the first item's node id.

Tk tests each item against its own outline, so clicking the empty corner of
a diamond's bounding box misses the diamond, while clicking its title text
still hits the node.

### 3.3 Click versus pan
Left press, drag and release share one set of bindings, so `MapCanvas` has to
tell a click from a pan:

| Press lands on | What happens |
|----------------|--------------|
| A node | `on_node_click(node_id)` is called immediately. No pan starts, so dragging a node does nothing (yet). |
| Empty space | A pan starts (`scan_mark`), and `_press_point` remembers where. Dragging calls `scan_dragto`, but only while dragging is allowed (`MapCanvas.drag_enabled`, off by default and toggled by the view toolbar's **Drag** button); when it's locked, the pointer can move without panning. On release, if the pointer moved no more than `CLICK_TOLERANCE` (3px) in each direction, it counts as a click and `on_node_click(None)` is called, which clears the selection. A real drag pans and leaves the selection alone. |

Middle-button drag pans only while dragging is allowed, and never changes the selection.

`MapCanvas` doesn't decide what a click means; it only reports it through
the handler registered with `on_node_click(handler)`. `MappingView` registers
`_on_node_click`.

---

## 4. Applying a click

`MappingView._on_node_click(node_id)`:

1. Returns early if no map is shown, or if `node_id` equals the current
   selection. Clicking the selected node again, or clicking empty space when
   nothing is selected, costs nothing.
2. Calls `SelectionManager.select(node_id)` (`None` clears it).
3. Calls `MapCanvas.draw_map(map, node_id)`. Selection never changes a node's
   size, so the layout is **not** re-run: only the drawing is redone.
4. Calls `_update_toolbar()`.

---

## 5. Drawing the selected node

`MapCanvas._draw_nodes` passes `selected=(node.node_id == selected_id)` to
`NodeRenderer.draw()`. For the selected node, `_draw_shape` changes only the
outline:

| | Outline colour | Outline width |
|-|----------------|---------------|
| Normal node | Fill colour darkened by 30% | `2 × zoom` (at least 1px) |
| Selected node | `theme.palette.selection_outline` (`#1976d2` blue in the light theme, `#ffcc00` yellow in the dark theme) | `4 × zoom` (at least 1px) |

Fill, title and badge are unchanged. Because the colour comes from the
palette, switching themes recolours the selection too.

---

## 6. Selection and the toolbar

`MappingView._update_toolbar()` runs after every redraw and every selection
change:

| Selection | **+ Insert** | **✎ Edit** | **✕ Delete** | Style toolbar |
|-----------|:------------:|:----------:|:------------:|:-------------:|
| Nothing selected | disabled | disabled | disabled | greyed out |
| The root | enabled | enabled | disabled (`MapEditor.can_delete` is `False` for the root) | enabled |
| Any other node | enabled | enabled | enabled | enabled |

The style toolbar also rings the selected node's current colour and shape,
via `StyleToolbar.show_style()`.

Double-clicking a node selects it (if it isn't already) and opens its
title for editing.

The `Insert`, `F2` and `Delete` keys call the same methods as the buttons, and
those methods check the selection again, so a key press with nothing
selected (or with the root selected, for Delete) does nothing.

---

## 7. How other actions change the selection

| Action | Selection afterwards |
|--------|----------------------|
| `show_map(map)` (open, or `R` to reload in the preview) | The root |
| Click a node | That node |
| Click empty space (no drag) | Nothing |
| Drag on empty space / middle-drag | Unchanged |
| Insert (`insert_node`) | The new child |
| Delete (`delete_selected_node`) | The deleted node's parent |
| Change layout (`set_layout`) | Unchanged |
| Change theme (`apply_theme`) | Unchanged, redrawn in the new theme's colour |
| Zoom | Unchanged. `set_zoom` redraws with `MapCanvas._selected_id`. |

After Insert and Delete, the view also scrolls so the selected node (Insert)
or the parent (Delete) stays where it was on screen; see
`MappingView._redraw_keeping_in_place`.

---

## 8. Not yet implemented

- **Keyboard navigation.** Arrow keys to move to the parent, first child and
  siblings. These will go in `SelectionManager` as `select_parent`,
  `select_first_child`, `select_next_sibling` and `select_previous_sibling`
  (see [object_model.md](object_model.md)).
- **Selection events.** Selection changes are handled inside `MappingView`
  and are not published as `Events.SELECTION_CHANGED` on the `EventBus` yet.
  Other components, such as a status bar showing the selected node, will need
  that.
- **Scrolling to the selection.** A newly inserted node can appear off screen;
  the view doesn't scroll to bring it into view.
- **Hidden selected nodes.** Only visible nodes can be clicked, so today the
  selection is always visible. Once nodes can be collapsed from the UI,
  collapsing a branch that contains the selected node should move the
  selection to the collapsed node.
