"""Capture the real Tk desktop using synthetic data, never the user's database.

Run from the source checkout, for example:
    python scripts/capture_ui.py --output build/ui-screenshots

Windows captures use GDI PrintWindow into a dedicated bitmap. The native
monitor layout is captured first; fresh applications then exercise Tk font and
layout scaling equivalent to 120, 144 and 192 DPI. These latter phases simulate
application font/layout scaling; they do not change the user's OS DPI setting.
The same code is callable from the frozen executable's --capture-ui command.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date, datetime, time, timedelta
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageGrab, ImageStat

from . import __version__
from .app import NhacViecApp
from .models import Schedule
from .storage import Storage
from .display import get_display_state, initialize_display


def seed_demo(store: Storage, today: date) -> int:
    tasks = (
        ("Kiểm tra các hạng mục bàn giao", -1, "Vận hành", "todo",
         "Đối chiếu danh sách công việc và xác nhận các hạng mục còn thiếu."),
        ("Hoàn thiện báo cáo công việc trong tháng", 0, "Báo cáo", "in_progress",
         "Tổng hợp kết quả, ghi rõ những nội dung cần xử lý trong tuần tới."),
        ("Chuẩn bị tài liệu cho cuộc họp tuần", 1, "Công việc", "todo",
         "Cập nhật tiến độ từng hạng mục và chuẩn bị tài liệu trao đổi."),
        ("Liên hệ đối tác xác nhận kế hoạch triển khai", 2, "Đối tác", "todo",
         "Thống nhất thời gian làm việc và các đầu mối phối hợp."),
        ("Rà soát hợp đồng dịch vụ và hồ sơ thanh toán", 3, "Tài chính", "in_progress",
         "Kiểm tra các điều khoản, chứng từ và mốc thời gian thanh toán."),
        ("Cập nhật hồ sơ khách hàng và thông tin liên hệ", 4, "Khách hàng", "todo",
         "Bổ sung thông tin mới và rà soát các hồ sơ cần hoàn thiện."),
        ("Gửi biên bản cuộc họp đã thống nhất", -2, "Công việc", "completed",
         "Biên bản đã được tổng hợp và lưu để tra cứu."),
        ("Điều chỉnh lịch hẹn cũ", 5, "Cá nhân", "canceled",
         "Kế hoạch đã thay đổi; giữ lại thông tin để theo dõi."),
    )
    selected_id = None
    for title, offset, category, status, content in tasks:
        task = store.create_task(title, datetime.combine(today + timedelta(days=offset), time(17)),
                                 category=category, content=content,
                                 requirements="Thông tin đầy đủ, rõ ràng và được xác nhận trước hạn.")
        if status != "todo":
            store.set_task_status(task.id, status)
        if selected_id is None:
            selected_id = task.id
    first = date(today.year, 1, 1)
    daily = store.save_schedule(Schedule(
        title="Rà soát công việc đầu ngày", category="Công việc", start_date=first,
        start_time=time(8, 30), end_time=time(9), recurrence="weekly", weekdays=list(range(5)),
        content="Xác định các việc cần ưu tiên và sắp xếp thời gian trong ngày."))
    store.save_schedule(Schedule(
        title="Trao đổi tiến độ với nhóm", category="Cuộc họp", start_date=first,
        start_time=time(9, 30), end_time=time(10, 15), recurrence="weekly",
        weekdays=sorted({today.weekday(), (today.weekday() + 2) % 7}),
        content="Cập nhật tiến độ và thống nhất các nội dung cần phối hợp."))
    store.save_schedule(Schedule(
        title="Tổng kết kế hoạch tháng", category="Báo cáo",
        start_date=date(today.year, 1, min(today.day, 28)),
        start_time=time(14), end_time=time(15), recurrence="monthly"))
    store.save_schedule(Schedule(
        title="Làm việc với đối tác", category="Đối tác", start_date=today,
        start_time=time(11), end_time=time(12), recurrence="once"))
    store.save_schedule(Schedule(
        title="Rà soát mục tiêu hằng năm", category="Kế hoạch", start_date=today,
        start_time=time(16), end_time=time(17), recurrence="yearly"))
    if today.weekday() < 5:
        store.set_occurrence_status(daily.id, today, "completed")
    return selected_id


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def settle(window):
    # Run configure/after-idle handlers and complete actual widget painting.
    for _ in range(4):
        window.update_idletasks()
        window.update()


def bounds(widget):
    return (widget.winfo_rootx(), widget.winfo_rooty(),
            widget.winfo_rootx() + widget.winfo_width(),
            widget.winfo_rooty() + widget.winfo_height())


def require_visible(widget, within, description, *, natural_width=False):
    if not widget.winfo_ismapped():
        raise AssertionError(f"{description}: widget is not visible")
    left, top, right, bottom = bounds(widget)
    outer_left, outer_top, outer_right, outer_bottom = bounds(within)
    if (widget.winfo_width() <= 1 or widget.winfo_height() <= 1 or
            left < outer_left - 1 or top < outer_top - 1 or
            right > outer_right + 1 or bottom > outer_bottom + 1):
        raise AssertionError(f"{description}: widget bounds {(left, top, right, bottom)} "
                             f"exceed container {(outer_left, outer_top, outer_right, outer_bottom)}")
    if natural_width and widget.winfo_width() + 1 < widget.winfo_reqwidth():
        raise AssertionError(f"{description}: control is narrower than its label")


def capture_windows_window(window):
    """Ask the window to paint into memory, including content off the desktop.

    Screen BitBlt (including Pillow's HWND grab) clips at the runner's monitor.
    PrintWindow renders the native window into our independently sized bitmap.
    No display mode, system DPI, or user data is changed.
    """
    import ctypes
    from ctypes import wintypes

    class BitmapInfoHeader(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("width", wintypes.LONG),
                    ("height", wintypes.LONG), ("planes", wintypes.WORD),
                    ("bit_count", wintypes.WORD), ("compression", wintypes.DWORD),
                    ("image_size", wintypes.DWORD), ("x_pixels_per_meter", wintypes.LONG),
                    ("y_pixels_per_meter", wintypes.LONG), ("colors_used", wintypes.DWORD),
                    ("colors_important", wintypes.DWORD)]

    class BitmapInfo(ctypes.Structure):
        _fields_ = [("header", BitmapInfoHeader), ("colors", wintypes.DWORD * 1)]

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetClientRect.restype = wintypes.BOOL
    user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    user32.ClientToScreen.restype = wintypes.BOOL
    user32.GetWindowDC.argtypes = [wintypes.HWND]
    user32.GetWindowDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.ReleaseDC.restype = ctypes.c_int
    user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
    user32.PrintWindow.restype = wintypes.BOOL
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.PatBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int,
                           ctypes.c_int, ctypes.c_int, wintypes.DWORD]
    gdi32.PatBlt.restype = wintypes.BOOL
    gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT,
                              wintypes.UINT, ctypes.c_void_p, ctypes.POINTER(BitmapInfo), wintypes.UINT]
    gdi32.GetDIBits.restype = ctypes.c_int
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteObject.restype = wintypes.BOOL
    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    gdi32.DeleteDC.restype = wintypes.BOOL

    def checked(value, operation):
        if not value:
            raise OSError(ctypes.get_last_error(), f"Windows capture: {operation} failed")
        return value

    hwnd = int(window.wm_frame(), 0)
    rectangle, client = wintypes.RECT(), wintypes.RECT()
    origin = wintypes.POINT(0, 0)
    checked(user32.GetWindowRect(hwnd, ctypes.byref(rectangle)), "GetWindowRect")
    checked(user32.GetClientRect(hwnd, ctypes.byref(client)), "GetClientRect")
    checked(user32.ClientToScreen(hwnd, ctypes.byref(origin)), "ClientToScreen")
    width, height = rectangle.right - rectangle.left, rectangle.bottom - rectangle.top
    if width <= 0 or height <= 0:
        raise AssertionError(f"Windows capture: invalid native window dimensions {(width, height)}")
    source_dc = memory_dc = bitmap = previous_bitmap = None
    selected = False
    try:
        source_dc = checked(user32.GetWindowDC(hwnd), "GetWindowDC")
        memory_dc = checked(gdi32.CreateCompatibleDC(source_dc), "CreateCompatibleDC")
        bitmap = checked(gdi32.CreateCompatibleBitmap(source_dc, width, height), "CreateCompatibleBitmap")
        previous_bitmap = checked(gdi32.SelectObject(memory_dc, bitmap), "SelectObject")
        if previous_bitmap == ctypes.c_void_p(-1).value:
            raise OSError("Windows capture: SelectObject returned HGDI_ERROR")
        selected = True
        # Deterministic black makes an unpainted strip detectable after capture.
        checked(gdi32.PatBlt(memory_dc, 0, 0, width, height, 0x00000042), "PatBlt BLACKNESS")
        checked(user32.PrintWindow(hwnd, memory_dc, 2), "PrintWindow PW_RENDERFULLCONTENT")
        # GetDIBits requires that the bitmap is not selected into a DC.
        checked(gdi32.SelectObject(memory_dc, previous_bitmap), "restore original bitmap")
        selected = False
        info = BitmapInfo()
        info.header.size = ctypes.sizeof(BitmapInfoHeader)
        info.header.width, info.header.height = width, -height  # top-down BGRX
        info.header.planes, info.header.bit_count = 1, 32
        info.header.compression = 0  # BI_RGB, no palette or compression
        info.header.image_size = width * height * 4
        buffer = ctypes.create_string_buffer(info.header.image_size)
        copied = gdi32.GetDIBits(source_dc, bitmap, 0, height, buffer, ctypes.byref(info), 0)
        if copied != height:
            raise OSError(ctypes.get_last_error(), f"Windows capture: GetDIBits copied {copied}/{height} rows")
        whole = Image.frombytes("RGB", (width, height), buffer.raw, "raw", "BGRX", width * 4, 1)
        # Exclude the native caption/invisible resize border. Keep exactly the
        # client area being checked, with no desktop-coordinate/DPI guessing.
        left, top = origin.x - rectangle.left, origin.y - rectangle.top
        right, bottom = left + client.right - client.left, top + client.bottom - client.top
        try:
            if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                raise AssertionError("Windows capture: native client rectangle lies outside window bitmap")
            return whole.crop((left, top, right, bottom))
        finally:
            whole.close()
    finally:
        if selected:
            gdi32.SelectObject(memory_dc, previous_bitmap)
        if bitmap:
            gdi32.DeleteObject(bitmap)
        if memory_dc:
            gdi32.DeleteDC(memory_dc)
        if source_dc:
            user32.ReleaseDC(hwnd, source_dc)


def check_black_padding(picture, description):
    """Reject the black off-desktop strips produced by clipped screen grabs."""
    with picture.convert("RGB") as rgb:
        painted = rgb.getbbox()
    if painted is None:
        raise AssertionError(f"{description}: screenshot is entirely black")
    left, top, right, bottom = painted
    padding = (left, top, picture.width - right, picture.height - bottom)
    if max(padding) > 8:
        raise AssertionError(f"{description}: screenshot contains unrendered solid-black edge padding "
                             f"(left,top,right,bottom)={padding}")


def capture(window, target: Path, records):
    window.lift()
    settle(window)
    if sys.platform == "win32":
        picture = capture_windows_window(window)
    else:
        picture = ImageGrab.grab(bbox=bounds(window))
    try:
        if picture.width < window.winfo_width() or picture.height < window.winfo_height():
            raise AssertionError(f"{target.name}: screenshot does not contain the complete window")
        if max(ImageStat.Stat(picture.convert("RGB")).var) < 1:
            raise AssertionError(f"{target.name}: blank screenshot")
        check_black_padding(picture, target.name)
        picture.save(target, format="PNG")
        if target.stat().st_size == 0:
            raise AssertionError(f"{target.name}: empty PNG")
        records.append({"file": target.name, "pixels": list(picture.size),
                        "tk_client_size": [window.winfo_width(), window.winfo_height()],
                        "capture_method": "Win32 PrintWindow" if sys.platform == "win32" else "Pillow ImageGrab"})
    finally:
        picture.close()


def check_task_controls(page, root, checks, context, *, advanced=False):
    require_visible(page.search_entry, page.filters, f"{context}: search field")
    require_visible(page.filter_combo, page.filters, f"{context}: task filter")
    require_visible(page.advanced_button, page.filters, f"{context}: advanced-filter toggle", natural_width=True)
    require_visible(page.filters, root, f"{context}: filter panel")
    buttons = [w for w in descendants(page.filters) if isinstance(w, ttk.Button) and w.winfo_ismapped()]
    for button in buttons:
        require_visible(button, page.filters, f"{context}: filter button {button.cget('text')}", natural_width=True)
    if advanced:
        for field in (page.date_from, page.date_to):
            require_visible(field, page.filters, f"{context}: date filter")
    if page.canvas.winfo_height() < 100:
        raise AssertionError(f"{context}: task list has less than 100px of usable height")
    checks.append(f"{context}: search/filter controls fit; task list remains visible")


def capture_phase(store, data_dir, output, report, today, task_id, *, target_dpi=None):
    root = tk.Tk()
    app = None
    errors = []
    suffix = "" if target_dpi is None else f"-tk{target_dpi}dpi"
    try:
        font_scale = None if target_dpi is None else target_dpi / 96
        app = NhacViecApp(root, store, data_dir, integrations=False, enable_timers=False,
                          font_scale_override=font_scale)
        settle(root)
        display_state = get_display_state(root)
        if target_dpi is None:
            report["display_state"] = display_state
        if bool(getattr(sys, "frozen", False)) and sys.platform == "win32" and (
                display_state.get("awareness") != "per-monitor-v2" or
                display_state.get("window_awareness") != "per-monitor-v2"):
            raise AssertionError(f"Frozen window is not PerMonitorV2 aware: {display_state}")
        actual_tk_scaling = float(root.tk.call("tk", "scaling"))
        viewport_factor = float(getattr(root, "_layout_scale", font_scale or actual_tk_scaling / (96 / 72)))
        root.report_callback_exception = lambda kind, value, _tb: errors.append(f"{kind.__name__}: {value}")
        screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
        # Windows Tk derives its default maximum client size from the runner's
        # desktop. Native HWND capture can include an offscreen client area;
        # permit the requested test viewports without changing the display.
        root.maxsize(max(2880, screen_width + 128), max(1728, screen_height + 128))
        report["scaling"].append({"phase": "native" if target_dpi is None else f"tk{target_dpi}dpi",
                                  "mode": "native-monitor" if target_dpi is None else "tk-font-layout-simulation",
                                  "target_font_dpi": target_dpi,
                                  "tk_pixels_per_point": actual_tk_scaling,
                                  "effective_font_dpi": actual_tk_scaling * 72,
                                  "viewport_scale": viewport_factor,
                                  "screen": [screen_width, screen_height],
                                  "max_client_size": list(root.maxsize()),
                                  "display_state": display_state})
        for logical_width, logical_height in ((1120, 720), (1366, 768)):
            width, height = round(logical_width * viewport_factor), round(logical_height * viewport_factor)
            size = f"{logical_width}x{logical_height}"
            context = size + suffix
            root.geometry(f"{width}x{height}+16+16")
            app.show_page("active")
            settle(root)
            if (root.winfo_width(), root.winfo_height()) != (width, height):
                raise AssertionError(
                    f"{context}: window manager did not allow requested client size; "
                    f"requested={(width, height)}, actual={(root.winfo_width(), root.winfo_height())}, "
                    f"screen={(screen_width, screen_height)}, maxsize={root.maxsize()}")
            for key, button in app.nav_buttons.items():
                require_visible(button, app.sidebar, f"{context}: sidebar {key}", natural_width=True)
            page = app.pages["active"]
            if page._advanced_open:
                page.toggle_advanced()
                settle(root)
            check_task_controls(page, root, report["checks"], context)
            capture(root, output / f"tasks-{context}.png", report["screenshots"])
            page.toggle_advanced()
            settle(root)
            check_task_controls(page, root, report["checks"], context + " advanced", advanced=True)
            capture(root, output / f"tasks-filters-{context}.png", report["screenshots"])
            page.toggle_advanced()
            app.show_page("calendar")
            view = app.pages["calendar"]
            view.anchor = view.selected_date = today
            for mode in ("week", "month", "year"):
                view.mode.set(mode)
                view.refresh()
                settle(root)
                if view.tree.winfo_height() <= round(100 * viewport_factor):
                    raise AssertionError(f"{context} {mode}: calendar day tree height must exceed 100px")
                require_visible(view.tree, root, f"{context} {mode}: day list")
                for button in view.action_buttons:
                    require_visible(button, root, f"{context} {mode}: day action", natural_width=True)
                report["checks"].append(f"{context} {mode}: day list and actions fit")
                capture(root, output / f"calendar-{mode}-{context}.png", report["screenshots"])
            app.show_page("active")
            dialog = app.edit_task(task_id)
            try:
                settle(dialog)
                save = next(w for w in descendants(dialog)
                            if isinstance(w, ttk.Button) and w.cget("text") == "Lưu công việc")
                require_visible(save, dialog, f"{context}: task dialog save footer", natural_width=True)
                report["checks"].append(f"{context}: task dialog save footer visible")
                name = "task-dialog.png" if logical_width == 1366 and not suffix else f"task-dialog-{context}.png"
                capture(dialog, output / name, report["screenshots"])
            finally:
                dialog.destroy()
            if errors:
                raise AssertionError("Tk callback errors: " + "; ".join(errors))
    finally:
        if app is not None:
            # Close any surviving child dialogs directly: capture never edits
            # or saves them, and must not leave a blocking confirmation box.
            for child in root.winfo_children():
                if isinstance(child, tk.Toplevel):
                    child.destroy()
            app.exit()
        else:
            root.destroy()
    if errors:
        raise AssertionError("Tk callback errors: " + "; ".join(errors))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Directory for PNGs and layout-check.json")
    args = parser.parse_args(argv)
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    # This call precedes every Tk creation in this verification command. The
    # frozen manifest may already have selected a policy; record the API's
    # queried result rather than assuming the manifest or setter succeeded.
    display_status = initialize_display()
    report = {"passed": False, "version": __version__, "platform": sys.platform,
              "frozen": bool(getattr(sys, "frozen", False)),
              "executable": Path(sys.executable).name,
              "display_awareness": asdict(display_status),
              "data": "synthetic, temporary SQLite database", "scaling": [],
              "checks": [], "screenshots": []}
    result = 1
    try:
        with TemporaryDirectory(prefix="nhacviec-ui-capture-") as directory:
            data_dir = Path(directory)
            with Storage(data_dir / "data" / "tasks.db") as store:
                today = date.today()
                task_id = seed_demo(store, today)
                capture_phase(store, data_dir, output, report, today, task_id)
                for target_dpi in (120, 144, 192):
                    capture_phase(store, data_dir, output, report, today, task_id, target_dpi=target_dpi)
        report["passed"] = True
        result = 0
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        (output / "layout-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if sys.stdout is not None:
        print(json.dumps({"passed": report["passed"], "version": __version__,
                          "frozen": report["frozen"], "display_awareness": report["display_awareness"],
                          "screenshots": len(report["screenshots"]), "checks": len(report["checks"]),
                          **({"error": report["error"]} if "error" in report else {})}, ensure_ascii=False))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
