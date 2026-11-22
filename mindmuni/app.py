"""Composition root: the only place where concrete objects are created and wired together."""

from pathlib import Path

from mindmuni.core.builtin_themes import builtin_themes
from mindmuni.core.events import EventBus, Events
from mindmuni.core.theme_manager import ThemeManager
from mindmuni.file.json_file_store import JsonFileStore
from mindmuni.file.map_repository import MapRepository
from mindmuni.file.map_serializer import MapSerializer
from mindmuni.model.mind_map import MindMap
from mindmuni.model.theme import Theme
from mindmuni.ui.core.dialogs import Dialogs
from mindmuni.ui.core.main_window import MainWindow
from mindmuni.ui.core.menu_bar import FileCommands, MenuBar, ThemeCommands
from mindmuni.ui.core.placeholder_view import PlaceholderAction, PlaceholderView
from mindmuni.ui.core.shortcut_map import ShortcutMap
from mindmuni.ui.core.theme_styler import ThemeStyler
from mindmuni.ui.core.view import View
from mindmuni.ui.core.view_navigator import ViewNavigator
from mindmuni.ui.mapping_main.mapping_view import MAP_VIEW_ID, MappingView
from mindmuni.utils.paths import maps_dir

TEXT_EDITOR_VIEW_ID = "text_editor"
UNTITLED_MAP_TITLE = "Untitled map"


class MindMuniApp:
    def __init__(self) -> None:
        self._create_core()
        self._create_ui()
        self._subscribe_to_events()
        self._bind_global_shortcuts()
        self._start()

    def run(self) -> None:
        self._window.run()

    # --- construction -------------------------------------------------------

    def _create_core(self) -> None:
        self._event_bus = EventBus()
        self._theme_manager = ThemeManager(self._event_bus, builtin_themes())
        self._map_repository = MapRepository(JsonFileStore(), MapSerializer())
        self._mind_map: MindMap | None = None  # the map on screen
        self._map_path: Path | None = None  # where it was opened from or last saved to

    def _create_ui(self) -> None:
        self._window = MainWindow()
        self._styler = ThemeStyler(self._window.root)
        self._dialogs = Dialogs(self._window.root, maps_dir())
        self._menu_bar = self._create_menu_bar()
        self._window.set_menu(self._menu_bar)
        self._window.on_close_requested(self._quit)
        self._navigator = ViewNavigator(self._event_bus)
        self._register_views()

    def _create_menu_bar(self) -> MenuBar:
        file_commands = FileCommands(
            new_map=self._new_map,
            open_map=self._open_map,
            save_map=self._save_map,
            save_map_as=self._save_map_as,
            quit_app=self._quit,
        )
        theme_commands = ThemeCommands(
            select_theme=self._theme_manager.apply,
            load_custom_theme=self._load_custom_theme,
        )
        return MenuBar(self._window.root, file_commands, theme_commands, self._theme_manager.available_names())

    def _register_views(self) -> None:
        self._mapping_view = MappingView(self._window.view_container, self._theme_manager.current_theme)
        for view in (self._mapping_view, self._create_text_editor_placeholder()):
            self._navigator.register(view)

    def _create_text_editor_placeholder(self) -> View:
        back = PlaceholderAction("← Back to map", self._navigator.back)
        return PlaceholderView(
            self._window.view_container,
            TEXT_EDITOR_VIEW_ID,
            title="Text editor",
            description="The node's note editor will live here.\nPress Esc or Back to return.",
            actions=[back],
        )

    def _subscribe_to_events(self) -> None:
        self._event_bus.subscribe(Events.THEME_CHANGED, self._on_theme_changed)
        self._event_bus.subscribe(Events.VIEW_CHANGED, self._on_view_changed)

    def _bind_global_shortcuts(self) -> None:
        root = self._window.root
        ShortcutMap.bind_global(root, ShortcutMap.NEW_MAP, self._new_map)
        ShortcutMap.bind_global(root, ShortcutMap.OPEN_MAP, self._open_map)
        ShortcutMap.bind_global(root, ShortcutMap.SAVE_MAP, self._save_map)
        ShortcutMap.bind_global(root, ShortcutMap.SAVE_MAP_AS, self._save_map_as)
        ShortcutMap.bind_global(root, ShortcutMap.QUIT, self._quit)
        ShortcutMap.bind_global(root, ShortcutMap.NAVIGATE_BACK, self._navigator.back)

    def _start(self) -> None:
        self._theme_manager.apply(self._theme_manager.current_theme.name)
        self._window.set_document_title(UNTITLED_MAP_TITLE)
        self._navigator.reset_to(MAP_VIEW_ID)

    # --- event handlers -----------------------------------------------------

    def _on_theme_changed(self, theme: Theme) -> None:
        self._styler.apply(theme)
        self._menu_bar.apply_theme(theme)
        self._mapping_view.apply_theme(theme)
        self._window.status_bar.show_message(f"Theme: {theme.name}")

    def _on_view_changed(self, view: View) -> None:
        self._window.status_bar.show_message(f"View: {view.view_id}")

    # --- menu commands (New and Custom theme are still placeholders) --------

    def _new_map(self) -> None:
        self._window.set_document_title(UNTITLED_MAP_TITLE)
        self._navigator.reset_to(MAP_VIEW_ID)
        self._window.status_bar.show_message("New map")

    def _open_map(self) -> None:
        path = self._dialogs.ask_map_to_open()
        if path is None:
            return
        try:
            mind_map = self._map_repository.load(path)
        except (OSError, ValueError) as error:  # ValueError covers bad JSON and MapFormatError
            self._dialogs.show_error("Open map", f"Could not open {path.name}:\n{error}")
            return
        self._mind_map, self._map_path = mind_map, path
        self._navigator.reset_to(MAP_VIEW_ID)
        self._mapping_view.show_map(mind_map)
        self._window.set_document_title(mind_map.title)
        self._window.status_bar.show_message(f"Opened {path.name}")

    def _save_map(self) -> None:
        """Saves to the map's file, or asks for one (like Save As) if it has none yet."""
        if self._map_path is None:
            self._save_map_as()
        else:
            self._write_map(self._map_path)

    def _save_map_as(self) -> None:
        if self._mind_map is None:
            self._window.status_bar.show_message("No map to save")
            return
        suggested_name = self._map_path.stem if self._map_path is not None else self._mind_map.title
        path = self._dialogs.ask_map_save_path(suggested_name)
        if path is not None:
            self._write_map(path)

    def _write_map(self, path: Path) -> None:
        """Saves the map to `path`, which becomes its file from now on. Shows an error if writing fails."""
        self._mapping_view.finish_editing()  # a title being typed belongs in the saved file
        try:
            self._map_repository.save(self._mind_map, path)
        except OSError as error:
            self._dialogs.show_error("Save map", f"Could not save {path.name}:\n{error}")
            return
        self._map_path = path
        self._window.status_bar.show_message(f"Saved {path.name}")

    def _load_custom_theme(self) -> None:
        path = self._dialogs.ask_theme_to_open()
        if path is not None:
            self._report_not_implemented("Load theme", path)

    def _quit(self) -> None:
        self._window.close()

    def _report_not_implemented(self, action: str, path: Path) -> None:
        self._window.status_bar.show_message(f"{action}: {path.name} (file layer not implemented yet)")
