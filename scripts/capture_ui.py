"""Capture the real Tk desktop using synthetic data, never the user's database.

Run from the source checkout, for example:
    python scripts/capture_ui.py --output build/ui-screenshots

Windows captures use Pillow's native window handle support. Default Windows/Tk
scaling is captured first; a fresh application then checks Tk's 120-DPI layout.
The latter changes Tk font/layout scaling only, not the Windows display mode.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import tkinter as tk
from tkinter import ttk

from PIL import ImageGrab, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nhacviec import __version__
from nhacviec.app import NhacViecApp
from nhacviec.models import Schedule
from nhacviec.storage import Storage


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


def capture(window, target: Path, records):
    window.lift()
    settle(window)
    if sys.platform == "win32":
        # This captures the actual native window, including its frame, without
        # converting between Windows logical coordinates and physical pixels.
        picture = ImageGrab.grab(window=int(window.wm_frame(), 0), include_layered_windows=True)
    else:
        picture = ImageGrab.grab(bbox=bounds(window))
    try:
        if picture.width < window.winfo_width() or picture.height < window.winfo_height():
            raise AssertionError(f"{target.name}: screenshot does not contain the complete window")
        if max(ImageStat.Stat(picture.convert("RGB")).var) < 1:
            raise AssertionError(f"{target.name}: blank screenshot")
        picture.save(target, format="PNG")
        if target.stat().st_size == 0:
            raise AssertionError(f"{target.name}: empty PNG")
        records.append({"file": target.name, "pixels": list(picture.size),
                        "tk_client_size": [window.winfo_width(), window.winfo_height()]})
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


def capture_phase(store, data_dir, output, report, today, task_id, *, scaling=None):
    root = tk.Tk()
    app = None
    errors = []
    suffix = "" if scaling is None else "-tk120dpi"
    try:
        if scaling is not None:
            root.tk.call("tk", "scaling", scaling)
        app = NhacViecApp(root, store, data_dir, integrations=False, enable_timers=False)
        root.report_callback_exception = lambda kind, value, _tb: errors.append(f"{kind.__name__}: {value}")
        report["scaling"].append({"phase": "native" if scaling is None else "tk120dpi",
                                  "tk_pixels_per_point": float(root.tk.call("tk", "scaling")),
                                  "screen": [root.winfo_screenwidth(), root.winfo_screenheight()]})
        for width, height in ((1120, 720), (1366, 768)):
            size = f"{width}x{height}"
            context = size + suffix
            root.geometry(f"{size}+16+16")
            app.show_page("active")
            settle(root)
            if (root.winfo_width(), root.winfo_height()) != (width, height):
                raise AssertionError(f"{context}: window manager did not allow requested client size")
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
                if view.tree.winfo_height() <= 100:
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
                name = "task-dialog.png" if width == 1366 and not suffix else f"task-dialog-{context}.png"
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
    report = {"passed": False, "version": __version__, "platform": sys.platform,
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
                capture_phase(store, data_dir, output, report, today, task_id, scaling=120 / 72)
        report["passed"] = True
        result = 0
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        (output / "layout-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "version": __version__,
                      "screenshots": len(report["screenshots"]), "checks": len(report["checks"]),
                      **({"error": report["error"]} if "error" in report else {})}, ensure_ascii=False))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
