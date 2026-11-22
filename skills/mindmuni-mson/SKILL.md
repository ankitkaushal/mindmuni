---
name: mindmuni-mson
description: Create or edit MindMuni mind-map files (.mson). Use whenever the user asks for a MindMuni map, a .mson file, or a mind map to open in MindMuni, such as "make a mind map of X as mson". Covers the full file format (node tree, shapes, colours, layout, rich-text notes), so no access to the MindMuni codebase is needed.
---

# MindMuni .mson files

MindMuni is a desktop mind-mapping app. A `.mson` file is **UTF-8 JSON** holding one map: a tree of nodes, how each node looks, and an optional rich-text note for each node.

You can produce a file in two ways:

1. **Helper script (preferred when you can run Python):** write a short outline in JSON, then run `scripts/build_mson.py` to expand and check it. See [Using the helper script](#using-the-helper-script).
2. **Write the JSON directly:** follow the format below exactly.

---

## File format

The top level is a **JSON list of three objects, in this order**:

```
[ map section, style section, text section ]
```

| Index | Section | Holds |
|---|---|---|
| 0 | map | metadata and the node tree (ids, titles, children) |
| 1 | style | the map's layout, plus shape, colour, position and collapsed state for each node |
| 2 | text | each node's rich-text note |

Sections 1 and 2 are optional: if one is missing, the app uses default styling and no notes. Always write all three anyway.

### 0. Map section

```json
{
  "format_version": 1,
  "map_id": "cissp-domains",
  "title": "CISSP Domains",
  "created_at": "2026-11-22T10:00:00",
  "updated_at": "2026-11-22T10:00:00",
  "root": {
    "node_id": "root",
    "title": "CISSP",
    "children": [
      { "node_id": "d1", "title": "Risk\nManagement", "children": [] }
    ]
  }
}
```

- `format_version`: always `1`. A higher number is rejected.
- `map_id`: any non-empty string. A short slug or a 32-character hex UUID both work.
- `title`: the map's name.
- `created_at` / `updated_at`: ISO 8601 local time **with no timezone and no microseconds**, `YYYY-MM-DDTHH:MM:SS`.
- `root`: exactly one root node. Every node has:
  - `node_id`: a string that is **unique across the whole map**. Styles and notes are looked up by this id, so a duplicate makes two nodes share styling and notes. Use readable slugs such as `"d1"` or `"d1-risk"`.
  - `title`: the text shown on the node. Use `\n` to break a long title over lines; keep each line under about 25 characters.
  - `children`: a list of nodes, in display order. Write `[]` for a leaf node; never leave the key out.

### 1. Style section

```json
{
  "map": { "layout": "BALANCED", "zoom": 1.0 },
  "nodes": {
    "root": {
      "shape": "ELLIPSE",
      "color": "INDIGO",
      "position": { "x": 0.0, "y": 0.0 },
      "collapsed": false
    },
    "d1": {
      "shape": "HEXAGON",
      "color": "RED",
      "position": { "x": 0.0, "y": 0.0 },
      "collapsed": false
    }
  }
}
```

- `map.layout`: `"RIGHT"` (every branch grows to the right of the root, which is the default) or `"BALANCED"` (the root's branches are split between its left and right). Use `BALANCED` when the root has 4 or more branches.
- `map.zoom`: how far the map is zoomed in when it opens, as a number: `1.0` is 100%, `0.75` is 75%. The app keeps it between `0.25` and `3.0`. Use `1.0` unless the map is very large (around 60 nodes or more), where `0.75` lets more of it fit on screen. Optional; defaults to `1.0`.
- `nodes`: one entry per node, keyed by `node_id`. Write an entry for **every** node.
  - `shape`: one of `RECTANGLE` (default, rounded corners), `ELLIPSE`, `DIAMOND`, `HEXAGON`, `CLOUD`, `STAR`.
  - `color`: one of `RED`, `ORANGE`, `AMBER`, `YELLOW`, `LIME`, `GREEN`, `TEAL`, `CYAN`, `BLUE` (default), `INDIGO`, `PURPLE`, `PINK`. These are colour *names*; the app's theme picks the actual hex values.
  - `position`: `{ "x": 0.0, "y": 0.0 }` for every node. **The app recomputes all positions with its own tree layout whenever it draws the map**, so you never need to work out coordinates.
  - `collapsed`: `true` hides the node's children until the user expands it. Usually `false`.

Values are **case-sensitive and must be upper case**. Any value not in these lists makes the whole file fail to load.

### 2. Text section (notes)

```json
{
  "notes": {
    "root": {
      "blocks": [
        {
          "block_type": "HEADING_1",
          "spans": [ { "text": "CISSP", "bold": false, "highlighted": false } ]
        },
        {
          "block_type": "PARAGRAPH",
          "spans": [
            { "text": "Covers ", "bold": false, "highlighted": false },
            { "text": "eight domains", "bold": true, "highlighted": true },
            { "text": " of security.", "bold": false, "highlighted": false }
          ]
        }
      ]
    }
  }
}
```

- `notes` maps `node_id` to a note. **Only include nodes that have a note**; leave the rest out. Write `"notes": {}` when no node has one.
- A note is a list of `blocks`, and each block is **one line or paragraph**:
  - `block_type`: `HEADING_1`, `HEADING_2` or `PARAGRAPH`.
  - `spans`: runs of text drawn one after another on the same line. Each span has `text`, `bold` (bool) and `highlighted` (bool, drawn like a highlighter pen). Split a line into several spans to format part of it.
- Use one block per line and **never put `\n` inside span text**. For a blank line, use a `PARAGRAPH` with `"spans": []`.
- There are no lists, links, italics or images. Write a list item as a paragraph that starts with `1. ` or `- `.

---

## Writing good maps

- **Structure:** one central idea at the root, 3 to 9 main branches, and 2 to 7 children per branch. Two or three levels is usually right. Put detail in notes rather than in deeper nodes.
- **Titles are short labels** (1 to 5 words). Explanations go in the node's note.
- **Visual hierarchy** (a convention, not a rule):
  - root: `ELLIPSE`, in a colour of its own (for example `INDIGO`)
  - main branches: `HEXAGON`, each in a different colour
  - children: `RECTANGLE`, in the same colour as their branch
  - use `DIAMOND` for decisions, `STAR` for key points and `CLOUD` for ideas or open questions
- **Notes:** start with a `HEADING_1`, put a `HEADING_2` above each section, use bold for key terms, and highlight sparingly for the single most important fact.

## Checklist before you deliver

- [ ] The top level is a list of exactly 3 objects: map, style, text.
- [ ] `format_version` is `1`, and the timestamps look like `YYYY-MM-DDTHH:MM:SS`.
- [ ] Every `node_id` is unique, and every node has `node_id`, `title` and `children`.
- [ ] Every node has a style entry with a valid upper-case `shape` and `color`.
- [ ] Every key in `notes` is an existing `node_id`, and every `block_type` is valid.
- [ ] No span text contains `\n`.
- [ ] The file is valid JSON (no trailing commas or comments) and uses the `.mson` extension.

---

## Using the helper script

`scripts/build_mson.py` needs only the Python 3.10+ standard library. It turns a compact outline into a complete `.mson` file and checks every rule above.

**Outline format** (JSON). Only `title` is required on each node:

```json
{
  "title": "CISSP Domains",
  "layout": "BALANCED",
  "zoom": 1.0,
  "root": {
    "id": "root",
    "title": "CISSP",
    "shape": "ELLIPSE",
    "color": "INDIGO",
    "note": "# CISSP\nCovers **eight domains** of ==information security==.",
    "children": [
      {
        "id": "d1",
        "title": "Risk\nManagement",
        "shape": "HEXAGON",
        "color": "RED",
        "note": "# Domain 1\n## Summary\nGovernance, risk and compliance.",
        "children": [
          { "title": "CIA triad", "note": "Confidentiality, integrity, availability." }
        ]
      }
    ]
  }
}
```

- `layout` / `zoom` (top level): optional; they default to `RIGHT` and `1.0`.
- `id`: optional. If it is missing, the script makes one from the parent's id and the node's position (for example `d1-1`).
- `shape` / `color`: optional. A child without them takes its **parent's colour** and the `RECTANGLE` shape. The root defaults to `ELLIPSE` and `INDIGO`. When the root's children have no colour, the script gives each one a different colour automatically.
- `collapsed`: optional bool.
- `note`: optional mini-markup, with one block per line:
  - `# text` becomes `HEADING_1`, `## text` becomes `HEADING_2`, and any other line becomes `PARAGRAPH` (an empty line becomes an empty paragraph).
  - `**bold**`, `==highlighted==`, and `**==both==**` for text that is bold and highlighted.

Run it:

```bash
python3 scripts/build_mson.py outline.json my-map.mson    # build
python3 scripts/build_mson.py --check my-map.mson         # check an existing .mson file
```

It prints the node count on success, or every problem it found and exits with status 1.
