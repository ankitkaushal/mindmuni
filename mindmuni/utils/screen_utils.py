import sys
import tkinter as tk

MONITOR_DEFAULTTONEAREST = 2


def monitor_right_edge(window: tk.Misc) -> int:
    """The x of the right edge of the monitor the window is on, in the same coordinates as winfo_rootx().

    Tk's winfo_screenwidth() is the main monitor's width only, so on Windows with more than one monitor it is
    asked which monitor holds the window. On a monitor to the right of the main one, that edge is past the main
    monitor's width. Elsewhere Tk's screen width is used.
    """
    if sys.platform == "win32":
        right = _windows_monitor_right_edge(window)
        if right is not None:
            return right
    return window.winfo_screenwidth()


def _windows_monitor_right_edge(window: tk.Misc) -> int | None:
    """The right edge of the work area (the monitor minus the taskbar) of the window's monitor, or None."""
    import ctypes
    from ctypes import wintypes

    class MonitorInfo(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", wintypes.RECT),
            ("rcWork", wintypes.RECT),
            ("dwFlags", wintypes.DWORD),
        ]

    try:
        user32 = ctypes.windll.user32
        user32.MonitorFromWindow.restype = wintypes.HMONITOR
        user32.MonitorFromWindow.argtypes = (wintypes.HWND, wintypes.DWORD)
        user32.GetMonitorInfoW.argtypes = (wintypes.HMONITOR, ctypes.POINTER(MonitorInfo))
        hwnd = int(window.winfo_toplevel().wm_frame(), 16)
        monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
        info = MonitorInfo(cbSize=ctypes.sizeof(MonitorInfo))
        if not monitor or not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return None
        return info.rcWork.right
    except (AttributeError, OSError, ValueError, tk.TclError):
        return None


def is_maximized(window: tk.Misc) -> bool:
    """Whether the window is maximized. Windows and macOS report it as the "zoomed" state, X11 as an attribute."""
    toplevel = window.winfo_toplevel()
    try:
        if toplevel.wm_state() == "zoomed":
            return True
        return bool(int(toplevel.wm_attributes("-zoomed")))
    except (tk.TclError, ValueError):
        return False
