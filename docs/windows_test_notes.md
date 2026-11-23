# Windows test notes

Context for testing recent fixes on Windows. They were made and tested on Linux only, so the Windows-specific code paths have never run. Delete this file once everything below is confirmed.

## 1. Title editing ends on every key press (committed: a2a40aa)

**Symptom:** while editing a node title (double-click, F2 or Edit), any key press ended editing and nothing was typed.

**Cause:** `TitleEditor._on_key` (`mindmuni/ui/mapping_main/title_editor.py`) saves and stops editing when Ctrl or Alt is held, so window shortcuts can run. It treated bit `0x0008` of `event.state` as Alt. On Windows Tk sets that bit for **Num Lock**; Alt is `0x20000`. With Num Lock on, every key looked like an Alt shortcut.

**Fix:** `ALT_MASK` is now per platform: `0x20000` on Windows, `0x0010` (Option) on macOS, `0x0008` elsewhere.

**Test:** with Num Lock on, edit a title and type letters, digits, Backspace and the arrow keys. Editing should continue until Enter, Escape or a click elsewhere. Ctrl+S while editing should save the title and then save the map.

**Known gap, not fixed:** AltGr on European layouts reports as Ctrl+Alt, so typing `@` or `€` with AltGr still ends editing. A possible fix is to type `event.char` whenever it is a printable character, even with Ctrl+Alt held.

## 2. Text area resizing on a second monitor (committed: a234a78)

**Symptom:** on the second monitor (to the right of the main one, same size), pressing the view toolbar's Text button shrank the window instead of widening it. Closing Text then made it narrower still.

**How Text resizing works:** `MappingView.set_text_open` (`mindmuni/ui/mapping_main/mapping_view.py`) opens the note editor to the right of the map and widens the window by the text area's width (`_widen_window`), so the map doesn't move. Closing narrows it again. While the window is resizing, the map's column is held at a fixed width (`_pin_map_width`) until a `<Configure>` event reports the expected width, or until 1 s passes.

**Cause:** `_widen_window` capped the new width at `winfo_screenwidth() - winfo_rootx()`. On Windows `winfo_screenwidth()` is the **main** monitor's width, while `winfo_rootx()` is measured across all monitors. On a monitor to the right, `rootx` ≥ the main monitor's width, so the cap went to zero or below and the window dropped to its 640 px minimum size.

**Fix:**
- New `mindmuni/utils/screen_utils.py` with `monitor_right_edge(window)`. On Windows it uses `ctypes` (`MonitorFromWindow` on the `wm_frame()` handle, then `GetMonitorInfoW`) and returns the right edge of the work area of the window's monitor (the monitor minus the taskbar). Elsewhere, or if the call fails, it returns `winfo_screenwidth()`.
- `_widen_window` now returns how much it changed the width and never shrinks the window when asked to grow it. If the width doesn't change, it unpins the map at once instead of waiting 1 s.
- `MappingView._window_grown_by` records how much opening Text added. Closing shrinks by exactly that, so open then close gets back to the starting width.

**Test:** on the right-hand monitor, with the window not maximized and not touching the monitor's right edge:
1. Press Text. The window should widen to the right, and the map should stay the same size and position.
2. Press Text again. The window should go back to its exact starting width.
3. Move the window so its right edge nearly touches the monitor's edge, then press Text. The window should grow only up to the monitor's edge, with the map giving up the rest. Closing should get back to the starting width.
4. Repeat 1–3 on the main monitor to check nothing regressed.

If `monitor_right_edge` returns a wrong value, put a temporary print of it next to `winfo_rootx()` and `winfo_width()` in `_widen_window`. If the displays use different scaling percentages, Tk's coordinates and the Win32 ones may not agree, because the app doesn't declare DPI awareness. A mismatch there is the first thing to suspect.

## 3. Restore after maximize doesn't return to the starting size (committed: a234a78)

**Symptom:** after maximizing and then restoring, the window didn't come back to its size from before maximizing.

**Likely cause:** `_widen_window` called `window.geometry(...)` while the window was maximized (whenever Text was toggled). On Windows, setting a maximized window's size changes the size it is restored to.

**Fix:**
- `screen_utils.is_maximized(window)`: `wm_state() == "zoomed"` on Windows and macOS, or the `-zoomed` attribute on X11.
- `_widen_window` never resizes a maximized window. The text area takes space from the map instead.
- `_on_resized` tracks `_was_maximized` and calls `_on_restored` when the window goes from maximized back to normal. `_on_restored` then:
  - **Text closed while maximized** after being opened at normal size (which widened the window): gives back that width. It was saved in `_shrink_on_restore`.
  - **Text opened while maximized** (`_text_opened_maximized`): the text area was sized as a third of the *maximized* map. Without a fix, restoring left it at that width and squeezed the map to almost nothing (seen: map 136 px, text 848 px in a 1000 px window). It is now refit. If the restored size already has room (Text was open before maximizing, then closed and reopened while maximized), the text area takes that room. Otherwise it becomes a third of the map and the window widens by that much, as when opening Text normally. `_pin_map_width` takes an optional width for this.

**Linux results** (window/map/text widths in px, `-` = Text closed; the start width is 1000 and the maximized width 2560). The map is back at 985 after every restore:

| Steps | Widths after each step |
|---|---|
| open, max, restore, close | 1000/985/- → 1329/985/328 → 2560/2216/328 → 1329/985/328 → 1000/985/- |
| max, open, restore, close | 1000/985/- → 2560/2545/- → 2560/1696/848 → 1329/985/328 → 1000/985/- |
| max, open, close, restore | 1000/985/- → 2560/2545/- → 2560/1696/848 → 2560/2545/- → 1000/985/- |
| open, max, close, restore | 1000/985/- → 1329/985/328 → 2560/2216/328 → 2560/2545/- → 1000/985/- |
| open, max, close, open, restore, close | … → 2560/1696/848 → 1329/985/328 → 1000/985/- |
| max, open, restore, max, restore, close | … → 1329/985/328 → 2560/2216/328 → 1329/985/328 → 1000/985/- |

**Test on Windows:** run the same sequences with the maximize button. After each restore, the map should be its starting width and the text area about a third of it. Also try maximize then restore without touching Text. If that fails, the cause is something else, because nothing else in the app sets the window size. The only other call is `MainWindow._configure_root`, which sets the starting geometry (`mindmuni/ui/core/main_window.py`).

## Open items from the same session (not started)

- **macOS title editing:** Option + key (used to type `é`, `ñ`, `€`) ends editing instead of typing the character. Command isn't checked, so Cmd+S while editing probably types "s". Suggested fix: type any printable `event.char`, and on macOS treat Command (`0x0008`) as the shortcut modifier.
- **macOS shortcuts:** `mindmuni/ui/core/shortcut_map.py` binds only `<Control-…>`, so Mac users must use Control, not Command. The menu labels also say "Ctrl+".
