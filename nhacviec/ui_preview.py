"""Capture the real Tk desktop using synthetic data, never the user's database.

Run from the source checkout, for example:
    python scripts/capture_ui.py --output build/ui-screenshots

Windows captures read the exposed client pixels from the desktop with BitBlt.
Larger windows are moved through the work area and assembled at native pixel
size. The native monitor layout is captured first; fresh applications then
exercise Tk font/layout scaling equivalent to 120, 144 and 192 DPI. These latter
phases do not change the user's OS DPI setting. The same code is callable from
the frozen executable's --capture-ui command.
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
        if offset in (-1, 0):
            store.update_task(task.id, notes="Đã đối chiếu số liệu đợt 1.\nCần xác nhận nội dung còn thiếu trước khi bàn giao.")
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
    """Legacy PrintWindow path retained for native rendering diagnostics.

    A driver may return a clipped backing bitmap even when PrintWindow reports
    success. Complete verification captures therefore use exposed desktop
    pixels in ``capture_windows_complete`` instead of this offscreen surface.
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


def capture_windows_complete(window, *, description="window"):
    """Capture large test windows in native pixel tiles on a smaller monitor.

    Each tile comes from the visible desktop after the same window has painted
    that region. It does not rely on a driver's offscreen PrintWindow backing
    surface. No font/image scaling is performed. Only the synthetic verification
    command moves the window, restoring its position and topmost state finally.
    """
    import ctypes
    from ctypes import wintypes

    api = ctypes.WinDLL("user32", use_last_error=True)
    declarations = (
        ("GetAncestor", [wintypes.HWND, wintypes.UINT], wintypes.HWND),
        ("GetWindowRect", [wintypes.HWND, ctypes.POINTER(wintypes.RECT)], wintypes.BOOL),
        ("GetClientRect", [wintypes.HWND, ctypes.POINTER(wintypes.RECT)], wintypes.BOOL),
        ("ClientToScreen", [wintypes.HWND, ctypes.POINTER(wintypes.POINT)], wintypes.BOOL),
        ("GetWindowLongW", [wintypes.HWND, ctypes.c_int], wintypes.LONG),
        ("SetWindowPos", [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                          ctypes.c_int, ctypes.c_int, wintypes.UINT], wintypes.BOOL),
        ("SystemParametersInfoW", [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT], wintypes.BOOL),
        ("GetSystemMetrics", [ctypes.c_int], ctypes.c_int),
        ("RedrawWindow", [wintypes.HWND, ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT], wintypes.BOOL),
    )
    for name, arguments, result in declarations:
        function = getattr(api, name)
        function.argtypes, function.restype = arguments, result
    gdi = ctypes.WinDLL("gdi32", use_last_error=True)
    gdi.GdiFlush.argtypes, gdi.GdiFlush.restype = [], wintypes.BOOL
    dwm = ctypes.WinDLL("dwmapi", use_last_error=True)
    dwm.DwmFlush.argtypes, dwm.DwmFlush.restype = [], wintypes.LONG

    def checked(value, operation):
        if not value:
            raise OSError(ctypes.get_last_error(), f"Windows preview: {operation} failed")
        return value

    # winfo_id identifies the Tk client HWND; its outer ancestor also includes
    # the caption and resize border. Keep those coordinate systems explicit.
    client_hwnd = int(window.winfo_id())
    outer_hwnd = api.GetAncestor(client_hwnd, 2) or client_hwnd
    original, client = wintypes.RECT(), wintypes.RECT()
    origin = wintypes.POINT(0, 0)
    checked(api.GetWindowRect(outer_hwnd, ctypes.byref(original)), "GetWindowRect")
    checked(api.GetClientRect(client_hwnd, ctypes.byref(client)), "GetClientRect")
    checked(api.ClientToScreen(client_hwnd, ctypes.byref(origin)), "ClientToScreen")
    frame_x, frame_y = origin.x - original.left, origin.y - original.top
    was_topmost = bool(api.GetWindowLongW(outer_hwnd, -20) & 0x00000008)
    work = wintypes.RECT()
    if not api.SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0):
        work = wintypes.RECT(0, 0, api.GetSystemMetrics(0), api.GetSystemMetrics(1))
    width, height = window.winfo_width(), window.winfo_height()
    native_size = (client.right - client.left, client.bottom - client.top)
    if native_size != (width, height):
        raise AssertionError(f"Windows preview {description}: Tk client {(width, height)} "
                             f"does not match native client {native_size}")
    virtual = (api.GetSystemMetrics(76), api.GetSystemMetrics(77),
               api.GetSystemMetrics(76) + api.GetSystemMetrics(78),
               api.GetSystemMetrics(77) + api.GetSystemMetrics(79))
    tile_width = min(width, work.right - work.left - 8)
    tile_height = min(height, work.bottom - work.top - 8)
    if min(tile_width, tile_height) <= 0:
        raise AssertionError("Windows preview: invalid desktop work area")

    def offsets(length, step):
        return [0] if length <= step else list(range(0, length - step, step)) + [length - step]

    geometry = {
        "tk_client": (width, height), "native_client": native_size,
        "original_outer": (original.left, original.top, original.right, original.bottom),
        "work": (work.left, work.top, work.right, work.bottom),
        "virtual_screen": virtual, "frame_offset": (frame_x, frame_y),
        "tile_size": (tile_width, tile_height),
    }
    last_tile = {}
    image = Image.new("RGB", (width, height))
    count = 0
    try:
        for y in offsets(height, tile_height):
            for x in offsets(width, tile_width):
                desired_x, desired_y = work.left + 4 - x, work.top + 4 - y
                # HWND_TOPMOST prevents another runner window from obscuring
                # the client pixels being checked; SWP_NOSIZE preserves layout.
                checked(api.SetWindowPos(outer_hwnd, ctypes.c_void_p(-1), desired_x - frame_x,
                                         desired_y - frame_y, 0, 0, 0x0011), "SetWindowPos")
                last_tile = {"offset": (x, y), "desired_origin": (desired_x, desired_y)}
                for attempt in range(3):
                    checked(api.RedrawWindow(outer_hwnd, None, None, 0x0185), "RedrawWindow")
                    settle(window)
                    checked(gdi.GdiFlush(), "GdiFlush")
                    result = dwm.DwmFlush()
                    # A non-composited desktop can still paint and capture
                    # through GDI; its pixels must pass the same checks below.
                    if result < 0 and (result & 0xffffffff) != 0x80263001:
                        raise OSError(f"Windows preview: DwmFlush failed, HRESULT=0x{result & 0xffffffff:08x}")
                    actual = wintypes.POINT(0, 0)
                    checked(api.ClientToScreen(client_hwnd, ctypes.byref(actual)), "ClientToScreen tile")
                    if abs(actual.x - desired_x) > 2 or abs(actual.y - desired_y) > 2:
                        raise AssertionError(f"Native preview tile could not be exposed: desired "
                                             f"{(desired_x, desired_y)}, actual {(actual.x, actual.y)}")
                    desktop_box = (actual.x + x, actual.y + y,
                                   actual.x + x + tile_width, actual.y + y + tile_height)
                    last_tile.update({"actual_origin": (actual.x, actual.y),
                                      "desktop_bbox": desktop_box, "attempt": attempt + 1})
                    if not (virtual[0] <= desktop_box[0] < desktop_box[2] <= virtual[2]
                            and virtual[1] <= desktop_box[1] < desktop_box[3] <= virtual[3]
                            and work.left <= desktop_box[0] < desktop_box[2] <= work.right
                            and work.top <= desktop_box[1] < desktop_box[3] <= work.bottom):
                        raise AssertionError("Native preview tile lies outside the visible desktop work area")
                    tile = ImageGrab.grab(bbox=desktop_box, all_screens=True)
                    try:
                        last_tile["raw_pixels"] = tile.size
                        if tile.size != (tile_width, tile_height):
                            raise AssertionError(f"Native desktop grab returned {tile.size}, "
                                                 f"expected {(tile_width, tile_height)}")
                        try:
                            check_black_padding(tile, f"native tile {x},{y}")
                        except AssertionError:
                            if attempt == 2:
                                raise
                            # Read a subsequent compositor frame, without
                            # filling, resampling or accepting unpainted pixels.
                            continue
                        image.paste(tile, (x, y))
                        break
                    finally:
                        tile.close()
                count += 1
        return image, count
    except Exception as exc:
        image.close()
        raise RuntimeError(f"Windows preview {description}: {exc}; "
                           f"client/work geometry={geometry}; raw tile={last_tile}") from exc
    finally:
        restore_order = ctypes.c_void_p(-1 if was_topmost else -2)
        api.SetWindowPos(outer_hwnd, restore_order, original.left, original.top, 0, 0, 0x0011)
        settle(window)


def capture(window, target: Path, records):
    window.lift()
    settle(window)
    if sys.platform == "win32":
        try:
            picture, tile_count = capture_windows_complete(window, description=target.name)
        except Exception as exc:
            raise RuntimeError(f"{target.name}: capture failed; Tk bounds={bounds(window)}; {exc}") from exc
        capture_method = ("Desktop BitBlt at native pixels" if tile_count == 1
                          else "Tiled desktop BitBlt at native pixels")
    else:
        picture = ImageGrab.grab(bbox=bounds(window))
        capture_method = "Pillow ImageGrab"
    try:
        expected_size = (window.winfo_width(), window.winfo_height())
        if picture.size != expected_size:
            raise AssertionError(f"{target.name}: screenshot size {picture.size} "
                                 f"does not match the complete Tk client {expected_size}")
        if max(ImageStat.Stat(picture.convert("RGB")).var) < 1:
            raise AssertionError(f"{target.name}: blank screenshot")
        check_black_padding(picture, target.name)
        picture.save(target, format="PNG")
        if target.stat().st_size == 0:
            raise AssertionError(f"{target.name}: empty PNG")
        record = {"file": target.name, "pixels": list(picture.size),
                  "tk_client_size": list(expected_size), "capture_method": capture_method}
        if sys.platform == "win32":
            record["native_tile_count"] = tile_count
        records.append(record)
    finally:
        picture.close()


def task_state(tasks):
    """Identify the same saved records after a purely visual layout change."""
    return [(task.id, task.status, task.notes) for task in tasks]


def check_task_layout(page, root, checks, context, expected_tasks, *, viewport_factor):
    # The area removed at the user's request must not return as a hidden,
    # space-consuming frame when the presentation mode changes.
    for removed in ("filters", "filter_combo", "advanced_button", "count_label", "list_note", "hint"):
        if hasattr(page, removed):
            raise AssertionError(f"{context}: removed task control still exists: {removed}")
    require_visible(page.layout_selector, root, f"{context}: layout selector")
    for button in page.layout_buttons.values():
        require_visible(button, page.layout_selector, f"{context}: layout choice {button.cget('text')}", natural_width=True)
    if page.canvas.winfo_height() <= round(100 * viewport_factor):
        raise AssertionError(f"{context}: task list has less than 100 logical pixels of usable height")
    require_visible(page.canvas, root, f"{context}: task list")
    if task_state(page.visible_tasks) != expected_tasks or task_state(page.cards.visible_tasks) != expected_tasks:
        raise AssertionError(f"{context}: switching layouts changed task identities, states or notes")
    if set(page.cards_by_id) != {task[0] for task in expected_tasks}:
        raise AssertionError(f"{context}: rendered cards do not match the task list")
    for card in page.cards_by_id.values():
        for control in descendants(card):
            if isinstance(control, (ttk.Button, ttk.Menubutton)):
                require_visible(control, card, f"{context}: task action {control.cget('text')}", natural_width=True)
        for label in getattr(card, "wrapping_labels", []):
            require_visible(label, card, f"{context}: task text", natural_width=True)
            if label.winfo_height() + 1 < label.winfo_reqheight():
                raise AssertionError(f"{context}: wrapped task text is clipped vertically")
    if page.layout_mode in ("list", "wide") and page.cards.columns != 1:
        raise AssertionError(f"{context}: row layout did not use one column")
    checks.append(f"{context}: layout choices and task actions fit; saved tasks and notes match")


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
        if app.pages["active"].layout_mode != "grid":
            raise AssertionError("A fresh task page did not default to grid layout")
        expected_tasks = task_state(store.list_tasks(status="active"))
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
            for layout in ("grid", "list", "wide"):
                page.set_layout(layout)
                settle(root)
                check_task_layout(page, root, report["checks"], f"{context} {layout}", expected_tasks,
                                  viewport_factor=viewport_factor)
                prefix = "tasks" if layout == "grid" else f"tasks-{layout}"
                capture(root, output / f"{prefix}-{context}.png", report["screenshots"])
            if task_state(store.list_tasks(status="active")) != expected_tasks:
                raise AssertionError(f"{context}: visual layout selection changed stored tasks")
            app.show_page("calendar")
            view = app.pages["calendar"]
            view.anchor = view.selected_date = today
            for mode in ("week", "month", "year"):
                view.mode.set(mode)
                view.refresh()
                settle(root)
                day_tasks = store.list_tasks(date_from=today, date_to=today)
                if [task.id for task in view.task_cards.visible_tasks] != [task.id for task in day_tasks]:
                    raise AssertionError(f"{context} {mode}: calendar tasks do not match deadline date")
                if view.task_cards.canvas.winfo_height() <= round(100 * viewport_factor):
                    raise AssertionError(f"{context} {mode}: calendar task list height must exceed 100px")
                require_visible(view.task_cards.canvas, root, f"{context} {mode}: deadline task list")
                for card in view.task_cards.cards_by_id.values():
                    for control in descendants(card):
                        if isinstance(control, ttk.Button):
                            require_visible(control, card, f"{context} {mode}: task action {control.cget('text')}", natural_width=True)
                report["checks"].append(f"{context} {mode}: deadline totals match task cards and actions fit")
                capture(root, output / f"calendar-{mode}-{context}.png", report["screenshots"])
                if mode == "month" and logical_width == 1366 and not suffix:
                    capture(root, output / "calendar-tasks-1366x768.png", report["screenshots"])
                if mode == "month":
                    view.day_notebook.select(view.schedules_tab)
                    settle(root)
                    require_visible(view.tree, root, f"{context}: schedule list")
                    for button in view.action_buttons:
                        require_visible(button, root, f"{context}: schedule action", natural_width=True)
                    report["checks"].append(f"{context}: existing schedule list and actions fit")
                    capture(root, output / f"calendar-schedules-{context}.png", report["screenshots"])
                    view.day_notebook.select(view.tasks_tab)
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
            notes = app.edit_task_notes(task_id)
            try:
                settle(notes)
                require_visible(notes.notes_text, notes, f"{context}: notes editor")
                save_notes = next(w for w in descendants(notes)
                                  if isinstance(w, ttk.Button) and w.cget("text") == "Lưu ghi chú")
                require_visible(save_notes, notes, f"{context}: notes save footer", natural_width=True)
                report["checks"].append(f"{context}: notes editor and save footer visible")
                name = "notes-dialog.png" if logical_width == 1366 and not suffix else f"notes-dialog-{context}.png"
                capture(notes, output / name, report["screenshots"])
            finally:
                notes.destroy()
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
              "default_task_layout": "grid", "task_layouts": ["grid", "list", "wide"],
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
