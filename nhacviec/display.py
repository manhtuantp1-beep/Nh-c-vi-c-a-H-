"""Initialize Windows' native pixel rendering before the first Tk window.

The frozen executable declares PerMonitorV2 in its manifest.  This module also
initializes source runs, which use the Python host executable's own manifest.
It never changes the display resolution, Windows text smoothing, or the user's
scaling preference.  Tk 8.6 does not provide automatic monitor-change reflow;
``sync_tk_scaling`` applies the current window's real DPI before building its UI.
"""
from __future__ import annotations

from dataclasses import dataclass
import ctypes
import sys


IS_WINDOWS = sys.platform == "win32"
PER_MONITOR_AWARE_V2 = -4
ERROR_ACCESS_DENIED = 5
E_ACCESSDENIED = 0x80070005


@dataclass(frozen=True)
class DisplayStatus:
    awareness: str
    source: str
    error: str = ""

    @property
    def dpi_aware(self) -> bool:
        return self.awareness in ("per-monitor-v2", "per-monitor", "system")

    @property
    def per_monitor_aware(self) -> bool:
        return self.awareness in ("per-monitor-v2", "per-monitor")


class _WindowsDpiApi:
    """Typed Win32 boundary, kept separate from initialization policy."""

    def __init__(self):
        from ctypes import wintypes

        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        try:
            self.shcore = ctypes.WinDLL("shcore", use_last_error=True)
        except OSError:
            self.shcore = None
        self._wintypes = wintypes

    def _function(self, library, name, arguments, result):
        function = getattr(library, name, None) if library is not None else None
        if function is not None:
            function.argtypes = arguments
            function.restype = result
        return function

    def query_awareness(self) -> str:
        w = self._wintypes
        context_function = self._function(self.user32, "GetThreadDpiAwarenessContext", [], w.HANDLE)
        if context_function is not None:
            actual = self._context_awareness(context_function())
            if actual != "unknown":
                return actual
        query = self._function(self.shcore, "GetProcessDpiAwareness", [w.HANDLE, ctypes.POINTER(ctypes.c_int)], ctypes.c_long)
        if query is not None:
            actual = ctypes.c_int(-1)
            if query(None, ctypes.byref(actual)) == 0 and actual.value in (0, 1, 2):
                return ("unaware", "system", "per-monitor")[actual.value]
        legacy = self._function(self.user32, "IsProcessDPIAware", [], w.BOOL)
        return "system" if legacy is not None and legacy() else "unknown"

    def _context_awareness(self, context) -> str:
        w = self._wintypes
        if not context:
            return "unknown"
        equal = self._function(self.user32, "AreDpiAwarenessContextsEqual", [w.HANDLE, w.HANDLE], w.BOOL)
        if equal is not None and equal(context, ctypes.c_void_p(PER_MONITOR_AWARE_V2)):
            return "per-monitor-v2"
        awareness = self._function(self.user32, "GetAwarenessFromDpiAwarenessContext", [w.HANDLE], ctypes.c_int)
        if awareness is not None:
            actual = awareness(context)
            if actual in (0, 1, 2):
                return ("unaware", "system", "per-monitor")[actual]
        return "unknown"

    def window_awareness(self, hwnd: int) -> str:
        w = self._wintypes
        getter = self._function(self.user32, "GetWindowDpiAwarenessContext", [w.HWND], w.HANDLE)
        return self._context_awareness(getter(hwnd)) if getter is not None else "unknown"

    def set_per_monitor_v2(self) -> tuple[bool, int] | None:
        w = self._wintypes
        setter = self._function(self.user32, "SetProcessDpiAwarenessContext", [w.HANDLE], w.BOOL)
        if setter is None:
            return None
        ctypes.set_last_error(0)
        success = bool(setter(ctypes.c_void_p(PER_MONITOR_AWARE_V2)))
        return success, 0 if success else ctypes.get_last_error()

    def set_per_monitor(self) -> tuple[bool, int] | None:
        setter = self._function(self.shcore, "SetProcessDpiAwareness", [ctypes.c_int], ctypes.c_long)
        if setter is None:
            return None
        result = int(setter(2))
        return result == 0, result & 0xFFFFFFFF

    def set_system(self) -> tuple[bool, int] | None:
        setter = self._function(self.user32, "SetProcessDPIAware", [], self._wintypes.BOOL)
        if setter is None:
            return None
        ctypes.set_last_error(0)
        success = bool(setter())
        return success, 0 if success else ctypes.get_last_error()

    def window_dpi(self, hwnd: int) -> int | None:
        getter = self._function(self.user32, "GetDpiForWindow", [self._wintypes.HWND], self._wintypes.UINT)
        if getter is not None:
            dpi = int(getter(hwnd))
            if dpi > 0:
                return dpi
        getter = self._function(self.user32, "GetDpiForSystem", [], self._wintypes.UINT)
        if getter is not None:
            dpi = int(getter())
            if dpi > 0:
                return dpi
        return None


def initialize_display() -> DisplayStatus:
    """Request native rendering before creating Tk, respecting a locked host.

    A manifest sets process awareness before Python starts.  Access-denied
    therefore means the process already has a policy; query and report that
    policy instead of treating it as success or attempting a late downgrade.
    """
    if not IS_WINDOWS:
        return DisplayStatus("not-applicable", "non-windows")
    try:
        api = _WindowsDpiApi()
        current = api.query_awareness()
        if current == "per-monitor-v2":
            return DisplayStatus(current, "existing-policy")
        errors = []
        for mode, method in (("per-monitor-v2", api.set_per_monitor_v2),
                             ("per-monitor", api.set_per_monitor),
                             ("system", api.set_system)):
            attempt = method()
            if attempt is None:
                continue
            success, error = attempt
            if success:
                # A successful setter guarantees the requested policy. Query
                # where available so reports can expose a host/thread override.
                actual = api.query_awareness()
                return DisplayStatus(mode if actual == "unknown" else actual, f"initialized-{mode}")
            errors.append(f"{mode}: 0x{error:08x}")
            if error in (ERROR_ACCESS_DENIED, E_ACCESSDENIED):
                return DisplayStatus(api.query_awareness(), "existing-policy", "; ".join(errors))
        return DisplayStatus(api.query_awareness(), "unavailable", "; ".join(errors) or "DPI APIs unavailable")
    except (AttributeError, OSError) as exc:
        return DisplayStatus("unknown", "unavailable", str(exc))


def sync_tk_scaling(root) -> int | None:
    """Use the window's current monitor DPI before fonts/widgets are created.

    Points retain their intended physical size: 96 DPI means 96/72 Tk pixels
    per point, 144 DPI means 144/72.  This is not a fixed 100% scaling override.
    """
    if not IS_WINDOWS:
        return None
    try:
        dpi = _WindowsDpiApi().window_dpi(root.winfo_id())
        if dpi is not None and dpi > 0:
            root.tk.call("tk", "scaling", dpi / 72)
            return dpi
    except (AttributeError, OSError):
        pass
    return None


def get_display_state(root=None) -> dict:
    """Return measured rendering policy/DPI for packaged checks and previews.

    This is a query, not an initializer.  ``tk_scaling`` and ``window_dpi`` are
    separate so a simulated font-size phase cannot masquerade as real OS DPI.
    """
    result = {"platform": sys.platform, "awareness": "not-applicable",
              "awareness_level": None, "per_monitor_v2": False,
              "window_awareness": "not-applicable", "window_dpi": None, "tk_scaling": None}
    if root is not None:
        result["tk_scaling"] = float(root.tk.call("tk", "scaling"))
    if not IS_WINDOWS:
        return result
    try:
        api = _WindowsDpiApi()
        actual = api.query_awareness()
        result.update(awareness=actual,
                      awareness_level={"unaware": 0, "system": 1, "per-monitor": 2, "per-monitor-v2": 2}.get(actual),
                      per_monitor_v2=actual == "per-monitor-v2")
        if root is not None:
            hwnd = root.winfo_id()
            result["window_dpi"] = api.window_dpi(hwnd)
            result["window_awareness"] = api.window_awareness(hwnd)
    except (AttributeError, OSError) as exc:
        result.update(awareness="unknown", error=str(exc))
    return result
