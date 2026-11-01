import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from mindmuni.model.theme import Theme
from mindmuni.ui.core.shortcut_map import ShortcutMap

Command = Callable[[], None]


@dataclass(frozen=True, slots=True)
class FileCommands:
    new_map: Command
    open_map: Command
    save_map: Command
    save_map_as: Command
    quit_app: Command


@dataclass(frozen=True, slots=True)
class ThemeCommands:
    select_theme: Callable[[str], None]
    load_custom_theme: Command


class MenuBar(tk.Menu):
    """Main menu shared by every view: File and Theme."""

    def __init__(
        self,
        root: tk.Tk,
        file_commands: FileCommands,
        theme_commands: ThemeCommands,
        theme_names: list[str],
    ) -> None:
        super().__init__(root)
        self._theme_commands = theme_commands
        self._selected_theme = tk.StringVar(master=root)
        self._submenus: list[tk.Menu] = []
        self._add_file_menu(file_commands)
        self._add_theme_menu(theme_names)

    def mark_active_theme(self, theme_name: str) -> None:
        self._selected_theme.set(theme_name)

    def apply_theme(self, theme: Theme) -> None:
        palette = theme.palette
        colors = {
            "background": palette.menu_background,
            "foreground": palette.menu_foreground,
            "activebackground": palette.selection_outline,
            "activeforeground": palette.menu_background,
        }
        for menu in (self, *self._submenus):
            menu.configure(**colors)
        self.mark_active_theme(theme.name)

    def _add_file_menu(self, commands: FileCommands) -> None:
        file_menu = self._new_submenu("File")
        file_menu.add_command(label="New", command=commands.new_map, accelerator=ShortcutMap.NEW_MAP.label)
        file_menu.add_command(label="Open…", command=commands.open_map, accelerator=ShortcutMap.OPEN_MAP.label)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=commands.save_map, accelerator=ShortcutMap.SAVE_MAP.label)
        file_menu.add_command(label="Save As…", command=commands.save_map_as, accelerator=ShortcutMap.SAVE_MAP_AS.label)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=commands.quit_app, accelerator=ShortcutMap.QUIT.label)

    def _add_theme_menu(self, theme_names: list[str]) -> None:
        theme_menu = self._new_submenu("Theme")
        for theme_name in theme_names:
            self._add_theme_choice(theme_menu, theme_name)
        theme_menu.add_separator()
        theme_menu.add_command(label="Custom…", command=self._theme_commands.load_custom_theme)

    def _add_theme_choice(self, theme_menu: tk.Menu, theme_name: str) -> None:
        theme_menu.add_radiobutton(
            label=theme_name.capitalize(),
            value=theme_name,
            variable=self._selected_theme,
            command=lambda: self._theme_commands.select_theme(theme_name),
        )

    def _new_submenu(self, label: str) -> tk.Menu:
        submenu = tk.Menu(self)
        self.add_cascade(label=label, menu=submenu)
        self._submenus.append(submenu)
        return submenu
