import tkinter as tk
from collections.abc import Callable

from mindmuni.model.node_style import NodeColor, NodeShape
from mindmuni.model.theme import Theme
from mindmuni.ui.mapping_main.shape_drawing import draw_shape
from mindmuni.utils.color_utils import darken

TOOLBAR_MARGIN = 16  # gap between the toolbar and the canvas's bottom-left corner
SWATCH_SIZE = 20
SWATCH_GAP = 3
SHAPE_ICON_WIDTH = 34
SHAPE_ICON_HEIGHT = 24
SHAPE_ICON_PADDING = 4
CORNER_RADIUS = 4
RING_WIDTH = 2
OUTLINE_DARKEN_FRACTION = 0.3
DISABLED_STIPPLE = "gray50"
ROW_GAP = 6
BOX_PADDING = 6  # gap between each box's border and its contents
BOX_BORDER = 1
ARROW_GAP_WIDTH = 28  # gap between the picker box and the name box, holding one arrow per row
ARROW_MARGIN = 4  # space between each arrow end and the boxes
ARROW_WIDTH = 1.5
ARROW_HEAD = (7, 8, 3)  # Tk arrowshape: length to tip, length to back corners, half-width
NAME_WIDTH = 9  # characters; fits the longest name ("Rectangle"), so the toolbar doesn't resize

# Every NodeColor gets a swatch, so the palette stays limited to the major colours defined in the model.
COLORS: tuple[NodeColor, ...] = tuple(NodeColor)
SHAPES: tuple[NodeShape, ...] = tuple(NodeShape)


class StyleToolbar(tk.Frame):
    """Floating toolbar that sets the selected node's colour and shape.

    One swatch per NodeColor and one icon per NodeShape, drawn on small canvases so they show the
    theme's actual colours, and shape icons drawn as transparent outlines. The selected node's current colour
    and shape are ringed, and their names are shown in a separate box to the right of the pickers' box, each name
    on the same line as its row, left-aligned. An arrow on each row points from the pickers to their name. Like MapToolbar,
    it uses plain tk widgets coloured from the Theme. Call pin_to() to keep it in a widget's bottom-left corner.
    """

    def __init__(
        self,
        parent: tk.Misc,
        on_color: Callable[[NodeColor], None],
        on_shape: Callable[[NodeShape], None],
    ) -> None:
        # The container itself has no border and takes the canvas colour, so only the two boxes show.
        super().__init__(parent, highlightthickness=0, borderwidth=0)
        self._on_color = on_color
        self._on_shape = on_shape
        self._theme: Theme | None = None
        self._enabled = False
        self._current_color: NodeColor | None = None
        self._current_shape: NodeShape | None = None

        # Two boxes side by side. Both use the same border, padding and row heights, so each name lines up
        # with its picker row.
        self._picker_box = self._create_box()
        # height=1: the canvas only stretches to the boxes' height (fill="y"), never sets it.
        self._arrows = tk.Canvas(self, width=ARROW_GAP_WIDTH, height=1, highlightthickness=0, borderwidth=0)
        self._name_box = self._create_box()
        self._picker_box.pack(side="left", fill="y")
        self._arrows.pack(side="left", fill="y")
        self._name_box.pack(side="left", fill="y")
        self._swatch_row = tk.Frame(self._picker_box, borderwidth=0)
        self._shape_row = tk.Frame(self._picker_box, borderwidth=0)
        self._swatch_row.grid(row=0, column=0, sticky="w")
        self._shape_row.grid(row=1, column=0, sticky="w", pady=(ROW_GAP, 0))
        self._swatches = {color: self._create_cell(self._swatch_row, SWATCH_SIZE, SWATCH_SIZE) for color in COLORS}
        self._shape_icons = {
            shape: self._create_cell(self._shape_row, SHAPE_ICON_WIDTH, SHAPE_ICON_HEIGHT) for shape in SHAPES
        }
        self._name_box.rowconfigure(0, minsize=SWATCH_SIZE)
        self._name_box.rowconfigure(1, minsize=SHAPE_ICON_HEIGHT + ROW_GAP)
        self._color_name = self._create_name_label(row=0)
        self._shape_name = self._create_name_label(row=1)
        for color, swatch in self._swatches.items():
            swatch.bind("<Button-1>", lambda _event, c=color: self._pick_color(c))
        for shape, icon in self._shape_icons.items():
            icon.bind("<Button-1>", lambda _event, s=shape: self._pick_shape(s))

    def pin_to(self, widget: tk.Misc) -> None:
        """Places the toolbar over the widget's bottom-left corner. `widget` must be this toolbar's parent or one of its children."""
        self.place(in_=widget, relx=0.0, rely=1.0, anchor="sw", x=TOOLBAR_MARGIN, y=-TOOLBAR_MARGIN)
        self.lift()

    def show_style(self, color: NodeColor | None, shape: NodeShape | None) -> None:
        """Shows the selected node's style, or None for both when no node is selected (which disables the toolbar)."""
        self._current_color, self._current_shape = color, shape
        self._enabled = color is not None and shape is not None
        self._redraw()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        palette = theme.palette
        self.configure(background=palette.canvas_background)
        self._arrows.configure(background=palette.canvas_background)
        for box in (self._picker_box, self._name_box):
            box.configure(background=palette.menu_background, highlightbackground=palette.connector_line)
        for frame in (self._swatch_row, self._shape_row):
            frame.configure(background=palette.menu_background)
        for cell in (*self._swatches.values(), *self._shape_icons.values()):
            cell.configure(background=palette.menu_background)
        for label in (self._color_name, self._shape_name):
            label.configure(
                background=palette.menu_background,
                foreground=palette.menu_foreground,
                font=(theme.fonts.family, theme.fonts.base_size),
            )
        self._redraw()

    # --- internals ----------------------------------------------------------

    def _pick_color(self, color: NodeColor) -> None:
        if self._enabled:
            self._on_color(color)

    def _pick_shape(self, shape: NodeShape) -> None:
        if self._enabled:
            self._on_shape(shape)

    def _create_cell(self, parent: tk.Frame, width: int, height: int) -> tk.Canvas:
        cell = tk.Canvas(parent, width=width, height=height, highlightthickness=0, borderwidth=0)
        cell.pack(side="left", padx=(0, SWATCH_GAP))
        return cell

    def _create_box(self) -> tk.Frame:
        return tk.Frame(self, highlightthickness=BOX_BORDER, borderwidth=0, padx=BOX_PADDING, pady=BOX_PADDING)

    def _draw_arrows(self) -> None:
        """One arrow per row, at the height of the row's centre (both boxes share the same row layout)."""
        top = BOX_BORDER + BOX_PADDING
        row_centers = (top + SWATCH_SIZE / 2, top + SWATCH_SIZE + ROW_GAP + SHAPE_ICON_HEIGHT / 2)
        color = self._theme.palette.menu_foreground if self._enabled else self._theme.palette.connector_line
        self._arrows.delete("all")
        for y in row_centers:
            self._arrows.create_line(
                ARROW_MARGIN, y, ARROW_GAP_WIDTH - ARROW_MARGIN, y,
                fill=color, width=ARROW_WIDTH, arrow="last", arrowshape=ARROW_HEAD,
            )

    def _create_name_label(self, row: int) -> tk.Label:
        """A name label in the name box, in the grid row matching its picker row."""
        label = tk.Label(self._name_box, width=NAME_WIDTH, anchor="w", borderwidth=0, padx=0, pady=0)
        label.grid(row=row, column=0, sticky="w", pady=(ROW_GAP if row > 0 else 0, 0))
        return label

    def _redraw(self) -> None:
        if self._theme is None:
            return
        cursor = "hand2" if self._enabled else "arrow"
        self._draw_arrows()
        self._color_name.configure(text=style_label(self._current_color) if self._enabled else "")
        self._shape_name.configure(text=style_label(self._current_shape) if self._enabled else "")
        for color, swatch in self._swatches.items():
            swatch.configure(cursor=cursor)
            self._draw_swatch(swatch, color)
        for shape, icon in self._shape_icons.items():
            icon.configure(cursor=cursor)
            self._draw_shape_icon(icon, shape)

    def _draw_swatch(self, swatch: tk.Canvas, color: NodeColor) -> None:
        palette = self._theme.palette
        fill = palette.color_for(color)
        is_current = self._enabled and color is self._current_color
        swatch.delete("all")
        inset = RING_WIDTH + 1
        swatch.create_rectangle(
            inset, inset, SWATCH_SIZE - inset, SWATCH_SIZE - inset,
            fill=fill, outline=darken(fill, OUTLINE_DARKEN_FRACTION), width=1,
            stipple="" if self._enabled else DISABLED_STIPPLE,
        )
        if is_current:
            swatch.create_rectangle(1, 1, SWATCH_SIZE - 1, SWATCH_SIZE - 1, outline=palette.selection_outline, width=RING_WIDTH)

    def _draw_shape_icon(self, icon: tk.Canvas, shape: NodeShape) -> None:
        palette = self._theme.palette
        is_current = self._enabled and shape is self._current_shape
        icon.delete("all")
        if is_current:
            icon.create_rectangle(
                1, 1, SHAPE_ICON_WIDTH - 1, SHAPE_ICON_HEIGHT - 1,
                outline=palette.selection_outline, width=RING_WIDTH,
            )
        center_x, center_y = SHAPE_ICON_WIDTH / 2, SHAPE_ICON_HEIGHT / 2
        half_width = SHAPE_ICON_WIDTH / 2 - SHAPE_ICON_PADDING
        half_height = SHAPE_ICON_HEIGHT / 2 - SHAPE_ICON_PADDING
        # Outline only (no fill), so the icons stay transparent over the toolbar background.
        outline = palette.menu_foreground if self._enabled else palette.connector_line
        draw_shape(
            icon, shape, center_x, center_y, half_width, half_height,
            corner_radius=CORNER_RADIUS, fill="", outline=outline, width=1.5,
        )

def style_label(value: NodeColor | NodeShape | None) -> str:
    """The name shown for a colour or shape, e.g. "Red" or "Hexagon"."""
    return value.name.replace("_", " ").capitalize() if value is not None else ""
