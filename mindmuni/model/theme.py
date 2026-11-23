from dataclasses import dataclass, field

from mindmuni.model.node_style import NodeColor


@dataclass(slots=True)
class ThemePalette:
    background: str
    foreground: str
    canvas_background: str
    connector_line: str
    selection_outline: str
    highlight_background: str
    menu_background: str
    menu_foreground: str
    link_foreground: str  # links in notes
    node_colors: dict[NodeColor, str] = field(default_factory=dict)

    def color_for(self, node_color: NodeColor) -> str:
        return self.node_colors.get(node_color, self.background)


@dataclass(slots=True)
class FontSettings:
    family: str = "Helvetica"
    base_size: int = 11
    heading_1_size: int = 20
    heading_2_size: int = 16
    node_title_size: int = 11


@dataclass(slots=True)
class Theme:
    name: str
    palette: ThemePalette
    fonts: FontSettings = field(default_factory=FontSettings)
