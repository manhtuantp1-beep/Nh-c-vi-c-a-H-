"""Task, reminder and export dialogs with a shared, readable desktop layout."""
from __future__ import annotations

import calendar
from datetime import date, datetime
import logging
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .excel import export_workbook
from .models import Task
from .widgets import DateEntry, ScrollableForm, parse_time, ui_font, layout_scale


STATUS_LABELS = {
    "todo": "Cần làm",
    "in_progress": "Đang thực hiện",
    "completed": "Đã hoàn thành",
    "canceled": "Đã hủy",
}
SURFACE = "#FFFFFF"
INK = "#15263E"
BORDER = "#CDD7E5"


def _prepare_dialog(window: tk.Toplevel, app, title: str, *, width: int, height: int,
                    min_width: int = 600, min_height: int = 440) -> None:
    """Fit the initial window inside the desktop, including its title bar."""
    window.title(title)
    window.transient(app.root)
    window.configure(background=SURFACE)
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    factor = layout_scale(app.root)
    window._layout_scale = factor
    width = min(round(width * factor), screen_width - 48)
    height = min(round(height * factor), screen_height - 96)
    x = max(16, min(app.root.winfo_rootx() + (app.root.winfo_width() - width) // 2,
                    screen_width - width - 16))
    y = max(16, min(app.root.winfo_rooty() + (app.root.winfo_height() - height) // 2,
                    screen_height - height - 64))
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.minsize(min(round(min_width * factor), width), min(round(min_height * factor), height))
    window.columnconfigure(0, weight=1)
    window.rowconfigure(1, weight=1)


def _header(window, title: str, description: str) -> ttk.Frame:
    frame = ttk.Frame(window, style="Surface.TFrame", padding=(28, 24, 28, 18))
    frame.grid(row=0, column=0, sticky="ew")
    ttk.Label(frame, text=title, style="Surface.TLabel",
              font=ui_font(window, 21, "bold")).pack(anchor="w")
    label = ttk.Label(frame, text=description, style="Hint.TLabel", wraplength=650)
    label.pack(anchor="w", fill="x", pady=(6, 0))
    frame.bind("<Configure>", lambda event: label.configure(wraplength=max(250, event.width - 56)))
    return frame


def _footer(window) -> ttk.Frame:
    footer = ttk.Frame(window, style="Surface.TFrame")
    footer.grid(row=2, column=0, sticky="ew")
    ttk.Separator(footer).pack(fill="x")
    buttons = ttk.Frame(footer, style="Surface.TFrame", padding=(28, 16))
    buttons.pack(fill="x")
    return buttons


def _label(parent, text: str, *, row: int, column: int = 0, columnspan: int = 1,
           top: int = 0) -> ttk.Label:
    label = ttk.Label(parent, text=text, style="Field.TLabel")
    label.grid(row=row, column=column, columnspan=columnspan, sticky="w", pady=(top, 7))
    return label


def _text_area(parent, *, height: int) -> ScrolledText:
    text = ScrolledText(
        parent, height=height, wrap="word", font=ui_font(parent, 12),
        foreground=INK, background=SURFACE, insertbackground=INK,
        selectbackground="#E9EFFF", selectforeground=INK,
        relief="flat", borderwidth=0, highlightthickness=1,
        highlightbackground=BORDER, highlightcolor="#315EFB",
        padx=12, pady=10, spacing1=2, spacing3=4, undo=True,
    )
    text.frame.configure(background=SURFACE)
    text.vbar.destroy()
    text.vbar = ttk.Scrollbar(text.frame, orient="vertical", command=text.yview)
    # ScrolledText delegates pack/grid to its outer frame; _w is the Text
    # widget itself, so the themed scrollbar can keep its original pack order.
    text.vbar.pack(side="right", fill="y", before=text._w)
    text.configure(yscrollcommand=text.vbar.set)
    return text


class TaskDialog(tk.Toplevel):
    def __init__(self, app, task: Task | None = None):
        super().__init__(app.root)
        self.app, self.task = app, task
        heading = "Chi tiết công việc" if task else "Tạo công việc"
        _prepare_dialog(self, app, heading, width=760, height=740,
                        min_width=640, min_height=520)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        description = (f"{task.code}  ·  {STATUS_LABELS[task.status]}" if task else
                       "Ghi rõ việc cần làm và hạn hoàn thành để dễ theo dõi.")
        _header(self, heading, description)

        self.form = ScrollableForm(self, style="Surface.TFrame")
        self.form.grid(row=1, column=0, sticky="nsew", padx=14)
        frame = self.form.content
        frame.configure(style="Surface.TFrame", padding=(14, 4, 14, 24))
        self.form.canvas.configure(background=SURFACE)
        frame.columnconfigure(0, weight=1)

        self.title_var = tk.StringVar(self, value=task.title if task else "")
        self.category_var = tk.StringVar(self, value=task.category if task else "")
        deadline = task.deadline if task else datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
        self.time_var = tk.StringVar(self, value=deadline.strftime("%H:%M"))

        _label(frame, "Tên công việc *", row=0)
        title_entry = ttk.Entry(frame, textvariable=self.title_var)
        title_entry.grid(row=1, column=0, sticky="ew")

        timing = ttk.Frame(frame, style="Surface.TFrame")
        timing.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        timing.columnconfigure(0, weight=1)
        timing.columnconfigure(1, weight=1)
        date_box = ttk.Frame(timing, style="Surface.TFrame")
        date_box.grid(row=0, column=0, sticky="ew", padx=(0, 18))
        _label(date_box, "Ngày đến hạn *", row=0)
        self.date_entry = DateEntry(date_box, value=deadline.date(), style="Surface.TFrame")
        self.date_entry.grid(row=1, column=0, sticky="w")
        time_box = ttk.Frame(timing, style="Surface.TFrame")
        time_box.grid(row=0, column=1, sticky="ew")
        _label(time_box, "Giờ đến hạn *", row=0)
        time_field = ttk.Frame(time_box, style="Surface.TFrame")
        time_field.grid(row=1, column=0, sticky="w")
        ttk.Entry(time_field, textvariable=self.time_var, width=8).pack(side="left")
        ttk.Label(time_field, text="hh:mm", style="Hint.TLabel").pack(side="left", padx=10)

        _label(frame, "Phân loại", row=3, top=18)
        categories = sorted({t.category for t in app.store.list_tasks() if t.category})
        ttk.Combobox(frame, textvariable=self.category_var, values=categories).grid(row=4, column=0, sticky="ew")

        _label(frame, "Nội dung công việc", row=5, top=18)
        self.content_text = _text_area(frame, height=5)
        self.content_text.grid(row=6, column=0, sticky="ew")
        _label(frame, "Yêu cầu hoàn thành", row=7, top=18)
        self.requirements_text = _text_area(frame, height=3)
        self.requirements_text.grid(row=8, column=0, sticky="ew")
        _label(frame, "Ghi chú", row=9, top=18)
        self.notes_text = _text_area(frame, height=4)
        self.notes_text.grid(row=10, column=0, sticky="ew")
        ttk.Label(frame, text="Lưu tiến độ đang làm, nội dung cần trao đổi hoặc điều cần chú ý.",
                  style="Hint.TLabel", wraplength=600).grid(row=11, column=0, sticky="w", pady=(7, 0))
        ttk.Label(frame, text="* Thông tin bắt buộc. Nhấn Ctrl+S để lưu nhanh.",
                  style="Hint.TLabel").grid(row=12, column=0, sticky="w", pady=(14, 0))
        if task:
            self.content_text.insert("1.0", task.content)
            self.requirements_text.insert("1.0", task.requirements)
            self.notes_text.insert("1.0", task.notes)

        buttons = _footer(self)
        if task and task.status == "in_progress":
            ttk.Button(buttons, text="Tạm dừng", style="Quiet.TButton",
                       command=lambda: self.change_status("todo", "Tạm dừng")).pack(side="left", padx=(0, 8))
        if task and task.status in ("todo", "in_progress"):
            ttk.Button(buttons, text="Hủy việc", style="Danger.TButton",
                       command=lambda: self.change_status("canceled")).pack(side="left")
        elif task:
            ttk.Button(buttons, text="Mở lại", style="Secondary.TButton",
                       command=lambda: self.change_status("todo", "Đã mở lại")).pack(side="left")
        ttk.Button(buttons, text="Lưu công việc", style="Accent.TButton", command=self.save).pack(side="right")
        ttk.Button(buttons, text="Đóng", style="Secondary.TButton", command=self.cancel).pack(side="right", padx=(0, 10))
        self._initial = self.snapshot()
        self.bind("<Control-s>", lambda _e: self.save())
        self.bind("<Escape>", lambda _e: self.cancel())
        title_entry.focus_set()
        self.grab_set()

    def snapshot(self):
        return (self.title_var.get(), self.category_var.get(), self.time_var.get(),
                self.date_entry.get(), self.content_text.get("1.0", "end-1c"),
                self.requirements_text.get("1.0", "end-1c"), self.notes_text.get("1.0", "end-1c"))

    def cancel(self):
        if self.snapshot() != self._initial and not messagebox.askyesno("Chưa lưu thay đổi", "Đóng biểu mẫu và bỏ những thay đổi chưa lưu?", parent=self):
            return
        self.destroy()

    def save(self):
        try:
            when = self.date_entry.get_date()
            if when is None:
                raise ValueError("Anh cần chọn ngày deadline.")
            fields = dict(title=self.title_var.get(), deadline=datetime.combine(when, parse_time(self.time_var.get())),
                          category=self.category_var.get(), content=self.content_text.get("1.0", "end-1c"),
                          requirements=self.requirements_text.get("1.0", "end-1c"),
                          notes=self.notes_text.get("1.0", "end-1c"))
            if self.task:
                self.app.store.update_task(self.task.id, **fields)
            else:
                self.app.store.create_task(**fields)
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror("Chưa lưu được công việc", str(exc), parent=self)
            return
        self.destroy()
        self.app.refresh_current()

    def change_status(self, status, reason=""):
        if self.snapshot() != self._initial:
            messagebox.showinfo("Cần lưu nội dung", "Anh lưu thay đổi trước khi chuyển trạng thái công việc.", parent=self)
            return
        if status == "canceled" and not messagebox.askyesno("Hủy công việc", "Chuyển công việc vào Đã hủy? Dữ liệu vẫn được giữ lại.", parent=self):
            return
        self.app.transition_task(self.task.id, status, reason)
        self.destroy()


class NotesDialog(tk.Toplevel):
    """Edit progress notes without changing any other task field."""

    def __init__(self, app, task: Task):
        super().__init__(app.root)
        self.app, self.task = app, task
        _prepare_dialog(self, app, "Ghi chú công việc", width=720, height=570,
                        min_width=560, min_height=420)
        _header(self, "Ghi chú công việc", f"{task.title}\n{task.code}  ·  {STATUS_LABELS[task.status]}")
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        frame = ttk.Frame(self, style="Surface.TFrame", padding=(28, 0, 28, 12))
        frame.grid(row=1, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        hint = ttk.Label(frame, text="Ghi lại tiến độ đang làm và những nội dung cần chú ý.",
                         style="Hint.TLabel", wraplength=620)
        hint.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        frame.bind("<Configure>", lambda event: hint.configure(wraplength=max(240, event.width - 56)))
        self.notes_text = _text_area(frame, height=10)
        self.notes_text.grid(row=1, column=0, sticky="nsew")
        self.notes_text.insert("1.0", task.notes)
        self._initial = self.snapshot()
        buttons = _footer(self)
        ttk.Button(buttons, text="Lưu ghi chú", style="Accent.TButton", command=self.save).pack(side="right")
        ttk.Button(buttons, text="Đóng", style="Secondary.TButton", command=self.cancel).pack(side="right", padx=(0, 10))
        self.bind("<Control-s>", lambda _e: self.save())
        self.bind("<Escape>", lambda _e: self.cancel())
        self.notes_text.focus_set()
        self.grab_set()

    def snapshot(self):
        return self.notes_text.get("1.0", "end-1c")

    def cancel(self):
        if self.snapshot() != self._initial and not messagebox.askyesno(
                "Chưa lưu ghi chú", "Đóng và bỏ những ghi chú chưa lưu?", parent=self):
            return
        self.destroy()

    def save(self):
        try:
            self.app.store.update_task(self.task.id, notes=self.snapshot())
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror("Chưa lưu được ghi chú", str(exc), parent=self)
            return
        self.destroy()
        self.app.refresh_current()


class SettingsDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        _prepare_dialog(self, app, "Cài đặt nhắc việc", width=620, height=550,
                        min_width=560, min_height=500)
        _header(self, "Cài đặt nhắc việc", "Chọn thời điểm nhận nhắc để không bỏ lỡ công việc.")
        frame = ttk.Frame(self, style="Surface.TFrame", padding=(28, 4, 28, 24))
        frame.grid(row=1, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        settings = app.store.get_settings()
        self.days = tk.StringVar(self, value=str(settings["days_before"]))
        self.at_time = tk.StringVar(self, value=settings["daily_time"])
        self.enabled = tk.BooleanVar(self, value=settings["notifications_enabled"])

        ttk.Checkbutton(frame, text="Bật nhắc việc và nhắc lịch", variable=self.enabled,
                        style="Surface.TCheckbutton").grid(row=0, column=0, sticky="w", pady=(0, 20))
        fields = ttk.Frame(frame, style="Surface.TFrame")
        fields.grid(row=1, column=0, sticky="ew")
        fields.columnconfigure(0, weight=1)
        fields.columnconfigure(1, weight=1)
        before = ttk.Frame(fields, style="Surface.TFrame")
        before.grid(row=0, column=0, sticky="w", padx=(0, 24))
        _label(before, "Nhắc trước hạn", row=0)
        before_value = ttk.Frame(before, style="Surface.TFrame")
        before_value.grid(row=1, column=0, sticky="w")
        ttk.Spinbox(before_value, from_=1, to=30, textvariable=self.days, width=6).pack(side="left")
        ttk.Label(before_value, text="ngày", style="Hint.TLabel").pack(side="left", padx=10)
        daily = ttk.Frame(fields, style="Surface.TFrame")
        daily.grid(row=0, column=1, sticky="w")
        _label(daily, "Giờ nhắc mỗi ngày", row=0)
        daily_value = ttk.Frame(daily, style="Surface.TFrame")
        daily_value.grid(row=1, column=0, sticky="w")
        ttk.Entry(daily_value, textvariable=self.at_time, width=8).pack(side="left")
        ttk.Label(daily_value, text="hh:mm", style="Hint.TLabel").pack(side="left", padx=10)

        note = ttk.Frame(frame, padding=16)
        note.grid(row=2, column=0, sticky="ew", pady=(26, 0))
        ttk.Label(note, text="Để nhận nhắc đúng giờ", style="Section.TLabel").pack(anchor="w")
        ttk.Label(note, text="Máy cần đang bật, thức và ứng dụng đang chạy. Giờ nhắc theo giờ trên máy.\n\nMỗi lịch có thể đặt thêm mốc nhắc riêng theo phút và ngày.",
                  style="Subtitle.TLabel", wraplength=470, justify="left").pack(anchor="w", fill="x", pady=(8, 0))
        buttons = _footer(self)
        ttk.Button(buttons, text="Lưu cài đặt", style="Accent.TButton", command=self.save).pack(side="right")
        ttk.Button(buttons, text="Đóng", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=(0, 10))
        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Control-s>", lambda _e: self.save())
        self.grab_set()

    def save(self):
        try:
            days = int(self.days.get())
            daily_time = parse_time(self.at_time.get()).strftime("%H:%M")
            self.app.store.save_settings(days_before=days, daily_time=daily_time, notifications_enabled=self.enabled.get())
        except ValueError as exc:
            messagebox.showerror("Cài đặt chưa hợp lệ", str(exc), parent=self)
            return
        self.destroy()
        self.app.refresh_current()


class ExportDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        _prepare_dialog(self, app, "Xuất báo cáo Excel", width=650, height=510,
                        min_width=600, min_height=470)
        _header(self, "Xuất báo cáo Excel", "Tổng hợp công việc và lịch trong một tệp dễ theo dõi.")
        frame = ttk.Frame(self, style="Surface.TFrame", padding=(28, 4, 28, 24))
        frame.grid(row=1, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        today = date.today()
        _label(frame, "Khoảng ngày của các buổi lịch", row=0)
        dates = ttk.Frame(frame, style="Surface.TFrame")
        dates.grid(row=1, column=0, sticky="ew", pady=(7, 0))
        dates.columnconfigure(0, weight=1)
        dates.columnconfigure(1, weight=1)
        first = ttk.Frame(dates, style="Surface.TFrame")
        first.grid(row=0, column=0, sticky="w", padx=(0, 18))
        _label(first, "Từ ngày", row=0)
        self.start = DateEntry(first, value=today.replace(day=1), style="Surface.TFrame")
        self.start.grid(row=1, column=0, sticky="w")
        last = ttk.Frame(dates, style="Surface.TFrame")
        last.grid(row=0, column=1, sticky="w")
        _label(last, "Đến ngày", row=0)
        self.end = DateEntry(last, value=today.replace(day=calendar.monthrange(today.year, today.month)[1]), style="Surface.TFrame")
        self.end.grid(row=1, column=0, sticky="w")

        note = ttk.Frame(frame, padding=16)
        note.grid(row=2, column=0, sticky="ew", pady=(26, 0))
        ttk.Label(note, text="Nội dung báo cáo", style="Section.TLabel").pack(anchor="w")
        ttk.Label(note, text="Toàn bộ công việc và các buổi lịch trong khoảng ngày đã chọn.\n\nTệp Excel dùng để xem và chia sẻ báo cáo; không thay thế bản sao lưu dữ liệu.",
                  style="Subtitle.TLabel", wraplength=510, justify="left").pack(anchor="w", fill="x", pady=(8, 0))
        buttons = _footer(self)
        ttk.Button(buttons, text="Xuất báo cáo", style="Accent.TButton", command=self.export).pack(side="right")
        ttk.Button(buttons, text="Đóng", style="Secondary.TButton", command=self.destroy).pack(side="right", padx=(0, 10))
        self.bind("<Escape>", lambda _e: self.destroy())
        self.grab_set()

    def export(self):
        try:
            start, end = self.start.get_date(), self.end.get_date()
            if start is None or end is None or start > end:
                raise ValueError("Chọn khoảng ngày hợp lệ.")
            target = filedialog.asksaveasfilename(parent=self, title="Lưu báo cáo", defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile=f"NhacViec-{date.today():%Y%m%d}.xlsx")
            if not target:
                return
            export_workbook(self.app.store, target, start, end)
        except Exception as exc:
            logging.exception("Xuất Excel thất bại")
            messagebox.showerror("Không xuất được báo cáo", str(exc), parent=self)
            return
        messagebox.showinfo("Đã xuất báo cáo", f"Đã lưu: {target}", parent=self)
        self.destroy()
