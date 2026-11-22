# Mind Muni: UI Core

This is the application shell that every screen runs inside: the window, menu
bar, view switching, shortcuts, theming and dialogs. It contains no
mind-map-specific UI. The mapping view and text editor will plug into it as
`View` subclasses.

See [modules.md](modules.md) for the full package layout and
[object_model.md](object_model.md) for the domain classes.

## Running it

```
sudo apt install python3-tk      # Ubuntu/Debian only; Windows/macOS python.org builds include tkinter
.venv/bin/python main.py
```

---

## 1. Files

### Entry point

| File | Contains |
|------|----------|
| `main.py` | `main()` creates `MindMuniApp` and calls `run()`. Nothing else. |
| `mindmuni/app.py` | `MindMuniApp`, the **composition root**. It is the only place that creates concrete objects and connects them. It builds the core services and the UI, registers views, subscribes to events, binds global shortcuts and shows the first view. It also holds the File-menu handlers and the open map with its file path. Open loads the chosen `.mson` file through `MapRepository` and shows it in the `MappingView`. Save writes to that path, or acts like Save As when there is none. Save As asks for a path (suggesting the current file's name, or the map's title) and makes it the map's path from then on. Both first call `MappingView.finish_editing()` so a title being typed is saved too. Read and write errors are shown with `Dialogs.show_error()`. New shows a fresh map, titled "Untitled map", with only a "Central idea" root opened for typing; it has no file until it is saved. The window title shows the map's file name, "Untitled map" while it has no file, or only the app name when no map is open. |

### `mindmuni/ui/core/`: Tkinter widgets

| File | Contains |
|------|----------|
| `main_window.py` | `MainWindow` owns the `tk.Tk` root. It provides `view_container` (the frame views are shown in) and `status_bar`. Methods: `set_menu()`, `set_document_title(title, has_unsaved_changes)` (adds a `*` when dirty), `clear_document_title()` (app name only, when no map is open), `on_close_requested(handler)`, `run()` and `close()`. Constants: `APP_NAME`, `DEFAULT_GEOMETRY`, `MINIMUM_SIZE`. |
| `menu_bar.py` | `MenuBar` is a `tk.Menu` with the **File** menu (New, Open…, Save, Save As…, Quit) and the **Theme** menu (one radio item per theme, plus Custom…). Its actions are injected through two frozen dataclasses, `FileCommands` and `ThemeCommands`, so the menu never knows what the actions do. `apply_theme(theme)` recolours the menus and `mark_active_theme(name)` ticks the current theme. |
| `view.py` | `View` is the base class for every screen (a `ttk.Frame` with a `view_id`). Override `on_show(context)` to load data when the view appears and `on_hide()` to save edits before it disappears. |
| `view_navigator.py` | `ViewNavigator` swaps views inside the container. Methods: `register(view)`, `show(view_id, context=None)` (adds the current view to the history), `back()`, `can_go_back()`, `reset_to(view_id)` (clears the history) and `current_view`. It publishes `Events.VIEW_CHANGED` after each switch. |
| `shortcut_map.py` | `Shortcut` holds Tk event sequences plus the label shown in menus. `ShortcutMap` defines every key binding in one place (`NEW_MAP`, `OPEN_MAP`, `SAVE_MAP`, `SAVE_MAP_AS`, `QUIT`, `NAVIGATE_BACK`, the mapping view's `ZOOM_IN`, `ZOOM_OUT`, `RESET_ZOOM`, `INSERT_NODE`, `EDIT_TITLE`, `DELETE_NODE`, and the text editor's `HEADING_1`, `HEADING_2`, `NORMAL_TEXT`, `BOLD`, `HIGHLIGHT`) and provides `bind_global()` (whole app) and `bind_local()` (one widget). |
| `theme_styler.py` | `ThemeStyler` translates a model `Theme` into `ttk.Style` settings on top of the `clam` ttk theme. It styles the root background, general widgets, buttons, the status bar, and the `Heading1.TLabel` / `Heading2.TLabel` label styles. |
| `status_bar.py` | `StatusBar` is a one-line message area: `show_message(text)` and `clear()`. |
| `dialogs.py` | `Dialogs` wraps Tk's standard dialogs so other code never calls `filedialog` or `messagebox` directly: `ask_map_to_open()`, `ask_map_save_path(name)`, `ask_theme_to_open()`, `confirm_discard_changes()` (Yes/No/Cancel → `True`/`False`/`None`) and `show_error()`. |
| `toolbar_button.py` | `create_toolbar_button(parent, text, command)` makes a flat `tk.Button` and `style_toolbar_button(button, theme)` colours it from the theme. Shared by the mapping view's toolbars and, next, the text editor's. |
| `placeholder_view.py` | `PlaceholderView` and `PlaceholderAction` are a temporary screen with a title, description and buttons, for views that don't exist yet. None is registered at the moment. |
| `__init__.py` | Re-exports the public UI shell classes (`from mindmuni.ui.core import MainWindow, ...`). |

### `mindmuni/core/`: logic, no Tkinter

| File | Contains |
|------|----------|
| `events.py` | `Events` enum (`MAP_CHANGED`, `SELECTION_CHANGED`, `THEME_CHANGED`, `NODE_NOTE_REQUESTED`, `VIEW_CHANGED`) and `EventBus` (`subscribe`, `unsubscribe`, `publish`). Components talk through the bus instead of holding references to each other. |
| `theme_manager.py` | `ThemeManager` holds the available themes and the active one. `apply(name)` switches the theme and publishes `THEME_CHANGED`. Other methods: `available_names()`, `add_theme()` and `current_theme`. |
| `builtin_themes.py` | `light_theme()`, `dark_theme()` and `builtin_themes()` define fallback themes in Python, including the 12 node colours for each. They will be replaced by `themes/*.json` once the file layer exists. |
| `__init__.py` | Re-exports `EventBus`, `Events` and `ThemeManager`. |

### `mindmuni/utils/`

| File | Contains |
|------|----------|
| `paths.py` | `app_root_dir()`, `maps_dir()` and `themes_dir()`: default locations for map and theme files. |

---

## 2. How the pieces connect

```
main.py
  └── MindMuniApp (app.py)
        ├── EventBus ◄──────────────── publish / subscribe ────────────────┐
        ├── ThemeManager ── THEME_CHANGED ──► ThemeStyler, MenuBar,        │
        │                                      StatusBar                   │
        └── MainWindow (tk.Tk)                                             │
              ├── MenuBar ── FileCommands / ThemeCommands ──► app handlers │
              ├── view_container ◄── ViewNavigator ── VIEW_CHANGED ────────┘
              │                        └── "map"          (MappingView, with the
              │                                            TextEditorView beside it)
              └── StatusBar
```

### Startup (`MindMuniApp.__init__`)
1. `_create_core()` creates the `EventBus` and the `ThemeManager` with the built-in themes.
2. `_create_ui()` creates `MainWindow`, `ThemeStyler`, `Dialogs`, `MenuBar` and `ViewNavigator`, then registers the views.
3. `_subscribe_to_events()` subscribes to `THEME_CHANGED` and `VIEW_CHANGED`.
4. `_bind_global_shortcuts()` binds the global keys through `ShortcutMap`.
5. `_start()` applies the default theme, sets the title and shows the `"map"` view.

### Switching theme
```
Theme → Dark (MenuBar) → ThemeCommands.select_theme("dark")
  → ThemeManager.apply("dark") → EventBus.publish(THEME_CHANGED, theme)
  → ThemeStyler.apply · MenuBar.apply_theme · StatusBar message
```

### Navigating between views
```
navigator.show("text_editor", node)  → current view.on_hide() → added to history
                                     → text_editor.on_show(node) → VIEW_CHANGED
navigator.back() / Esc               → previous view restored with its original context
```

---

## 3. Global shortcuts

| Action | Key |
|--------|-----|
| New map | `Ctrl+N` |
| Open map | `Ctrl+O` |
| Save | `Ctrl+S` |
| Save As | `Ctrl+Shift+S` |
| Quit | `Ctrl+Q` |
| Back to the previous view | `Esc` |

---

## 4. Adding a real view

1. Subclass `View`, passing `view_id` to `super().__init__(parent, view_id)`.
2. Override `on_show(context)` and `on_hide()` as needed.
3. In `app.py`, create the view with `self._window.view_container` as the parent and call `self._navigator.register(view)`, replacing the matching placeholder.
4. Put any view-specific key bindings in `ShortcutMap` and attach them with `bind_local()`.

---

## 5. Placeholders still in place

| Item | Current behaviour | Replaced by |
|------|-------------------|-------------|
| Unsaved changes | Not tracked: no `*` in the title, no prompt before Open | A dirty flag plus `Dialogs.confirm_discard_changes()` |
| Theme → Custom… | Reports the chosen file only | `ThemeRepository.load_custom()` |
| Quit | Closes without asking about unsaved changes | A dirty check plus `Dialogs.confirm_discard_changes()` |
| Built-in themes | Defined in Python | `themes/dark.json` and `themes/light.json` |
