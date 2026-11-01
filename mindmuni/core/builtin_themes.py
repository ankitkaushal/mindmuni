"""Fallback dark/light themes until themes are loaded from JSON files."""

from mindmuni.model.node_style import NodeColor
from mindmuni.model.theme import Theme, ThemePalette

DARK_NODE_COLORS = {
    NodeColor.RED: "#e57373",
    NodeColor.ORANGE: "#ffb74d",
    NodeColor.AMBER: "#ffd54f",
    NodeColor.YELLOW: "#fff176",
    NodeColor.LIME: "#dce775",
    NodeColor.GREEN: "#81c784",
    NodeColor.TEAL: "#4db6ac",
    NodeColor.CYAN: "#4dd0e1",
    NodeColor.BLUE: "#64b5f6",
    NodeColor.INDIGO: "#7986cb",
    NodeColor.PURPLE: "#ba68c8",
    NodeColor.PINK: "#f06292",
}

LIGHT_NODE_COLORS = {
    NodeColor.RED: "#ef9a9a",
    NodeColor.ORANGE: "#ffcc80",
    NodeColor.AMBER: "#ffe082",
    NodeColor.YELLOW: "#fff59d",
    NodeColor.LIME: "#e6ee9c",
    NodeColor.GREEN: "#a5d6a7",
    NodeColor.TEAL: "#80cbc4",
    NodeColor.CYAN: "#80deea",
    NodeColor.BLUE: "#90caf9",
    NodeColor.INDIGO: "#9fa8da",
    NodeColor.PURPLE: "#ce93d8",
    NodeColor.PINK: "#f48fb1",
}


def dark_theme() -> Theme:
    palette = ThemePalette(
        background="#1e1e1e",
        foreground="#e0e0e0",
        canvas_background="#252526",
        connector_line="#808080",
        selection_outline="#ffcc00",
        highlight_background="#665c00",
        menu_background="#2d2d2d",
        menu_foreground="#e0e0e0",
        node_colors=dict(DARK_NODE_COLORS),
    )
    return Theme(name="dark", palette=palette)


def light_theme() -> Theme:
    palette = ThemePalette(
        background="#f5f5f5",
        foreground="#212121",
        canvas_background="#ffffff",
        connector_line="#9e9e9e",
        selection_outline="#1976d2",
        highlight_background="#fff176",
        menu_background="#eeeeee",
        menu_foreground="#212121",
        node_colors=dict(LIGHT_NODE_COLORS),
    )
    return Theme(name="light", palette=palette)


def builtin_themes() -> list[Theme]:
    return [light_theme(), dark_theme()]
