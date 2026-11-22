#!/usr/bin/env python3
"""Build a MindMuni .mson file from a compact JSON outline, or validate an existing .mson file.

Standalone: needs only the Python standard library.

    python3 build_mson.py outline.json out.mson
    python3 build_mson.py --check map.mson
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

FORMAT_VERSION = 1
SHAPES = {"RECTANGLE", "ELLIPSE", "DIAMOND", "HEXAGON", "CLOUD", "STAR"}
COLORS = ["RED", "ORANGE", "AMBER", "YELLOW", "LIME", "GREEN", "TEAL", "CYAN", "BLUE", "INDIGO", "PURPLE", "PINK"]
BRANCH_COLORS = ["RED", "ORANGE", "AMBER", "GREEN", "TEAL", "CYAN", "BLUE", "PURPLE", "PINK", "LIME", "YELLOW"]
LAYOUTS = {"RIGHT", "BALANCED"}
MIN_ZOOM, MAX_ZOOM = 0.25, 3.0
BLOCK_TYPES = {"HEADING_1", "HEADING_2", "PARAGRAPH"}
TIME_FORMAT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
INLINE = re.compile(r"(\*\*==.+?==\*\*|==\*\*.+?\*\*==|\*\*.+?\*\*|==.+?==)")


# --- outline -> .mson -------------------------------------------------------

def parse_spans(line: str) -> list[dict]:
    spans = []
    for part in INLINE.split(line):
        if not part:
            continue
        bold = highlighted = False
        if (part.startswith("**==") and part.endswith("==**")) or (part.startswith("==**") and part.endswith("**==")):
            part, bold, highlighted = part[4:-4], True, True
        elif part.startswith("**") and part.endswith("**"):
            part, bold = part[2:-2], True
        elif part.startswith("==") and part.endswith("=="):
            part, highlighted = part[2:-2], True
        spans.append({"text": part, "bold": bold, "highlighted": highlighted})
    return spans


def parse_note(text: str) -> dict:
    blocks = []
    for line in text.strip("\n").split("\n"):
        line = line.rstrip()
        if line.startswith("## "):
            blocks.append({"block_type": "HEADING_2", "spans": parse_spans(line[3:].strip())})
        elif line.startswith("# "):
            blocks.append({"block_type": "HEADING_1", "spans": parse_spans(line[2:].strip())})
        else:
            blocks.append({"block_type": "PARAGRAPH", "spans": parse_spans(line.strip())})
    return {"blocks": blocks}


def build(outline: dict) -> list:
    styles, notes = {}, {}

    def walk(node: dict, node_id: str, inherited_color: str, default_shape: str, depth: int) -> dict:
        color = node.get("color", inherited_color)
        styles[node_id] = {
            "shape": node.get("shape", default_shape),
            "color": color,
            "position": {"x": 0.0, "y": 0.0},
            "collapsed": bool(node.get("collapsed", False)),
        }
        if node.get("note"):
            notes[node_id] = parse_note(node["note"])
        children = []
        for index, child in enumerate(node.get("children", []), start=1):
            child_id = str(child.get("id") or f"{node_id}-{index}")
            child_color = BRANCH_COLORS[(index - 1) % len(BRANCH_COLORS)] if depth == 0 else color
            child_shape = "HEXAGON" if depth == 0 else "RECTANGLE"
            children.append(walk(child, child_id, child_color, child_shape, depth + 1))
        return {"node_id": node_id, "title": node["title"], "children": children}

    root = outline["root"]
    tree = walk(root, str(root.get("id") or "root"), root.get("color", "INDIGO"), root.get("shape", "ELLIPSE"), 0)
    stamp = datetime.now().replace(microsecond=0).isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", outline.get("title", root["title"]).lower()).strip("-") or "map"
    return [
        {
            "format_version": FORMAT_VERSION,
            "map_id": outline.get("map_id", slug),
            "title": outline.get("title", root["title"]),
            "created_at": stamp,
            "updated_at": stamp,
            "root": tree,
        },
        {"map": {"layout": outline.get("layout", "RIGHT"), "zoom": float(outline.get("zoom", 1.0))}, "nodes": styles},
        {"notes": notes},
    ]


# --- validation -------------------------------------------------------------

def validate(document) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, list) or len(document) != 3 or not all(isinstance(s, dict) for s in document):
        return ["top level must be a JSON list of 3 objects: [map, style, text]"]
    data, style, text = document

    if data.get("format_version") != FORMAT_VERSION:
        errors.append(f"format_version must be {FORMAT_VERSION}")
    if not data.get("map_id"):
        errors.append("map_id must be a non-empty string")
    for key in ("created_at", "updated_at"):
        if not TIME_FORMAT.match(str(data.get(key, ""))):
            errors.append(f"{key} must look like YYYY-MM-DDTHH:MM:SS")

    ids: list[str] = []

    def walk(node, path: str) -> None:
        if not isinstance(node, dict):
            errors.append(f"{path}: node must be an object")
            return
        for key in ("node_id", "title", "children"):
            if key not in node:
                errors.append(f"{path}: missing '{key}'")
        if not isinstance(node.get("title", ""), str):
            errors.append(f"{path}: title must be a string")
        ids.append(node.get("node_id"))
        for index, child in enumerate(node.get("children") or []):
            walk(child, f"{path}.children[{index}]")

    if "root" not in data:
        errors.append("map section has no 'root'")
    else:
        walk(data["root"], "root")
    duplicates = sorted({i for i in ids if ids.count(i) > 1 and i is not None})
    if duplicates:
        errors.append(f"duplicate node_ids: {duplicates}")
    id_set = set(ids)

    if style.get("map", {}).get("layout", "RIGHT") not in LAYOUTS:
        errors.append(f"map.layout must be one of {sorted(LAYOUTS)}")
    zoom = style.get("map", {}).get("zoom", 1.0)
    if isinstance(zoom, bool) or not isinstance(zoom, (int, float)) or not MIN_ZOOM <= zoom <= MAX_ZOOM:
        errors.append(f"map.zoom must be a number from {MIN_ZOOM} to {MAX_ZOOM} (1.0 is 100%)")
    node_styles = style.get("nodes", {})
    for node_id in id_set - set(node_styles):
        errors.append(f"style: no entry for node '{node_id}'")
    for node_id, node_style in node_styles.items():
        if node_id not in id_set:
            errors.append(f"style: entry for unknown node '{node_id}'")
        if node_style.get("shape", "RECTANGLE") not in SHAPES:
            errors.append(f"style[{node_id}]: bad shape {node_style.get('shape')!r}")
        if node_style.get("color", "BLUE") not in COLORS:
            errors.append(f"style[{node_id}]: bad color {node_style.get('color')!r}")

    for node_id, note in text.get("notes", {}).items():
        if node_id not in id_set:
            errors.append(f"notes: entry for unknown node '{node_id}'")
        for index, block in enumerate(note.get("blocks", [])):
            where = f"notes[{node_id}].blocks[{index}]"
            if block.get("block_type", "PARAGRAPH") not in BLOCK_TYPES:
                errors.append(f"{where}: bad block_type {block.get('block_type')!r}")
            for span in block.get("spans", []):
                if "text" not in span:
                    errors.append(f"{where}: span missing 'text'")
                elif "\n" in span["text"]:
                    errors.append(f"{where}: span text contains a newline; use a separate block")
    return errors


# --- CLI --------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "--check":
        document = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    elif len(argv) == 2:
        document = build(json.loads(Path(argv[0]).read_text(encoding="utf-8")))
    else:
        print(__doc__)
        return 2
    errors = validate(document)
    if errors:
        print("\n".join(f"error: {e}" for e in errors))
        return 1
    if argv[0] != "--check":
        out = Path(argv[1])
        out.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    print(f"ok: {len(document[1]['nodes'])} nodes, {len(document[2]['notes'])} notes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
