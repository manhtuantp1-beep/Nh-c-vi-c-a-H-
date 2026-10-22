"""Vietnamese desktop workflow for tasks, recurrence, notifications and backups."""
from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont
from tkinter.scrolledtext import ScrolledText
import traceback

from . import __version__
from .calendar_ui import CalendarView, close_schedule_editors
from .excel import export_workbook
from .models import Task
from .platform_support import PlatformSupport
from .reminders import ReminderEngine
from .widgets import DateEntry, parse_time, ui_font

GREEN = "#08775b"
BG = "#f4f7f5"
INK = "#24352d"
MUTED = "#64776b"
STATUS_LABELS = {"todo": "Cần làm", "in_progress": "Đang thực hiện", "completed": "Đã hoàn thành", "canceled": "Đã hủy"}
ALL_FILTER = "Tất cả việc chưa hoàn thành"
TODO_FILTER = "Chưa bắt đầu"


def configure_style(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")
    family = ui_font(root)[0]
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
        tkfont.nametofont(name, root=root).configure(family=family, size=10)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=INK, font=ui_font(root, 10))
    style.configure("Title.TLabel", font=ui_font(root, 23, "bold"))
    style.configure("Subtitle.TLabel", foreground=MUTED)
    style.configure("Accent.TButton", background=GREEN, foreground="white", padding=(14, 9))
    style.map("Accent.TButton", background=[("active", "#0d8c6b")])
    style.configure("TButton", padding=(10, 7), font=ui_font(root, 10))
    style.configure("Side.TFrame", background="white")
    style.configure("Side.TLabel", background="white", foreground=GREEN, font=ui_font(root, 15, "bold"))
    style.configure("Nav.TButton", anchor="w", padding=(12, 6))
    style.configure("Card.TFrame", background="white", relief="solid", borderwidth=1)
    style.configure("Card.TLabel", background="white", foreground=INK)
    style.configure("CardTitle.TLabel", background="white", foreground=INK, font=ui_font(root, 12, "bold"))
    style.configure("CardMeta.TLabel", background="white", foreground=MUTED, font=ui_font(root, 9))
    style.configure("CardStatus.TLabel", background="white", foreground=GREEN, font=ui_font(root, 9, "bold"))
    style.configure("Late.TLabel", background="white", foreground="#b04c24", font=ui_font(root, 9, "bold"))
    style.configure("TLabelframe", background=BG)
    style.configure("TLabelframe.Label", background=BG, foreground=GREEN)
    style.configure("Treeview", rowheight=28, font=ui_font(root, 10))
    style.configure("Treeview.Heading", font=ui_font(root, 10, "bold"))


class TaskListPage(ttk.Frame):
    """Each status page retains its own search, ordering and date range."""

    def __init__(self, parent, app, view: str):
        super().__init__(parent, padding=24)
        self.app, self.view = app, view
        self.visible_tasks: list[Task] = []
        self.cards_by_id = {}
        self._columns = 0
        self._resize_job = None
        heading = {"active": "Cần làm", "in_progress": "Đang thực hiện", "due": "Sắp đến hạn", "completed": "Đã hoàn thành", "canceled": "Đã hủy"}[view]
        ttk.Label(self, text=heading, style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text="Theo dõi công việc theo trạng thái, deadline và nội dung.", style="Subtitle.TLabel").pack(anchor="w", pady=(5, 18))
        controls = ttk.Frame(self)
        controls.pack(fill="x")
        self.filter_var = tk.StringVar(value=ALL_FILTER)
        if view == "active":
            self.filter_combo = ttk.Combobox(controls, state="readonly", textvariable=self.filter_var, values=(ALL_FILTER, TODO_FILTER), width=33)
            self.filter_combo.pack(side="left", padx=(0, 12))
            self.filter_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        self.query_var = tk.StringVar()
        ttk.Label(controls, text="Tìm tên / mã:").pack(side="left")
        search = ttk.Entry(controls, textvariable=self.query_var, width=28)
        search.pack(side="left", padx=7, fill="x", expand=True)
        search.bind("<Return>", lambda _e: self.apply_filters())
        ttk.Button(controls, text="Tạo công việc", style="Accent.TButton", command=self.app.new_task).pack(side="right", padx=(12, 0))
        self.hint = ttk.Label(self, style="Subtitle.TLabel", wraplength=900)
        self.hint.pack(anchor="w", pady=(10, 15))
        dates = ttk.Frame(self)
        dates.pack(fill="x")
        ttk.Label(dates, text="Theo:").pack(side="left")
        self.sort_var = tk.StringVar(value="Deadline")
        ttk.Combobox(dates, state="readonly", textvariable=self.sort_var, values=("Deadline", "Ngày tạo"), width=11).pack(side="left", padx=6)
        self.descending = tk.BooleanVar(value=False)
        ttk.Checkbutton(dates, text="Giảm dần", variable=self.descending).pack(side="left", padx=(2, 14))
        ttk.Label(dates, text="Từ:").pack(side="left")
        self.date_from = DateEntry(dates, value=None, allow_empty=True)
        self.date_from.pack(side="left", padx=5)
        ttk.Label(dates, text="Đến:").pack(side="left")
        self.date_to = DateEntry(dates, value=None, allow_empty=True)
        self.date_to.pack(side="left", padx=5)
        ttk.Button(dates, text="Lọc", command=self.apply_filters).pack(side="left", padx=6)
        ttk.Button(dates, text="Xóa lọc", command=self.clear_filters).pack(side="left")
        self.count_label = ttk.Label(self)
        self.count_label.pack(anchor="w", pady=(19, 10))
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(body, background=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.card_container = ttk.Frame(self.canvas)
        self._canvas_window = self.canvas.create_window((0, 0), window=self.card_container, anchor="nw")
        self.card_container.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._resize)
        # Bind locally, rather than replacing wheel behavior in calendar/forms.
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<Button-4>", lambda _e: self.canvas.yview_scroll(-3, "units"))
        self.canvas.bind("<Button-5>", lambda _e: self.canvas.yview_scroll(3, "units"))
        self.refresh()

    def _wheel(self, event):
        self.canvas.yview_scroll(-int(event.delta / 120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1), "units")
        return "break"

    def _bind_card_wheel(self, widget):
        widget.bind("<MouseWheel>", self._wheel)
        widget.bind("<Button-4>", lambda _e: self.canvas.yview_scroll(-3, "units"))
        widget.bind("<Button-5>", lambda _e: self.canvas.yview_scroll(3, "units"))
        for child in widget.winfo_children():
            self._bind_card_wheel(child)

    def _resize(self, event):
        self.canvas.itemconfigure(self._canvas_window, width=event.width)
        columns = max(1, min(3, event.width // 365))
        if columns != self._columns:
            self._columns = columns
            if self._resize_job:
                self.after_cancel(self._resize_job)
            self._resize_job = self.after_idle(self._render_cards)

    def apply_filters(self):
        try:
            self.refresh()
        except ValueError as exc:
            messagebox.showerror("Bộ lọc chưa hợp lệ", str(exc), parent=self)

    def clear_filters(self):
        self.query_var.set("")
        self.sort_var.set("Deadline")
        self.descending.set(False)
        self.date_from.set_date(None)
        self.date_to.set_date(None)
        self.refresh()

    def refresh(self):
        start, end = self.date_from.get_date(), self.date_to.get_date()
        if start and end and start > end:
            raise ValueError("Ngày bắt đầu lọc phải trước hoặc bằng ngày kết thúc.")
        status = "active" if self.view in ("active", "due") else self.view
        if self.view == "active" and self.filter_var.get() == TODO_FILTER:
            status = "todo"
        tasks = self.app.store.list_tasks(status=status, query=self.query_var.get(), date_from=start, date_to=end,
                                          sort_by="deadline" if self.sort_var.get() == "Deadline" else "created_at", descending=self.descending.get())
        if self.view == "due":
            cutoff = date.today() + timedelta(days=self.app.store.get_settings()["days_before"])
            tasks = [t for t in tasks if t.deadline.date() <= cutoff]
        self.visible_tasks = tasks
        self.count_label.configure(text=f"{len(tasks)} công việc phù hợp")
        if self.view == "active":
            text = ("Gồm việc mới, chờ xử lý, đang thực hiện, tạm dừng và quá hạn. Việc hoàn thành/hủy ở mục riêng."
                    if self.filter_var.get() == ALL_FILTER else
                    "Nhóm Cần làm hiện tại: gồm cả việc tạm dừng hoặc mở lại; không gồm việc đang thực hiện.")
        elif self.view == "due":
            text = "Các việc chưa hoàn thành trong khoảng ngày nhắc đã chọn, bao gồm việc quá hạn."
        else:
            text = "Bấm Chi tiết để xem, chỉnh sửa hoặc thay đổi trạng thái công việc."
        self.hint.configure(text=text)
        self._render_cards()

    def _render_cards(self):
        self._resize_job = None
        for child in self.card_container.winfo_children():
            child.destroy()
        self.cards_by_id = {}
        for index in range(3):
            self.card_container.columnconfigure(index, weight=1 if index < max(self._columns, 1) else 0)
        if not self.visible_tasks:
            ttk.Label(self.card_container, text="Chưa có công việc phù hợp. Anh có thể tạo công việc mới hoặc xóa bộ lọc.", padding=24).grid(row=0, column=0, sticky="w")
            return
        for index, task in enumerate(self.visible_tasks):
            card = ttk.Frame(self.card_container, style="Card.TFrame", padding=17)
            card.grid(row=index // max(self._columns, 1), column=index % max(self._columns, 1), sticky="nsew", padx=(0, 12), pady=(0, 12))
            self.cards_by_id[task.id] = card
            ttk.Label(card, text=STATUS_LABELS[task.status].upper(), style="CardStatus.TLabel").pack(anchor="w")
            title = task.title if len(task.title) <= 82 else task.title[:79] + "…"
            ttk.Label(card, text=title, style="CardTitle.TLabel", wraplength=310).pack(anchor="w", fill="x", pady=(9, 5))
            ttk.Label(card, text=f"Mã: {task.code}", style="CardMeta.TLabel").pack(anchor="w")
            ttk.Label(card, text=task.category or "Chưa phân loại", style="CardMeta.TLabel").pack(anchor="w", pady=(4, 8))
            content = task.content.replace("\n", " ")
            if len(content) > 105:
                content = content[:102] + "…"
            ttk.Label(card, text=content or "Chưa có nội dung chi tiết.", style="CardMeta.TLabel", wraplength=310).pack(anchor="w", fill="x", pady=(0, 10))
            late = task.status in ("todo", "in_progress") and task.deadline < datetime.now()
            ttk.Label(card, text=task.deadline.strftime("Deadline: %d/%m/%Y · %H:%M") + (" · QUÁ HẠN" if late else ""),
                      style="Late.TLabel" if late else "CardMeta.TLabel").pack(anchor="w")
            if task.reason:
                ttk.Label(card, text=task.reason, style="CardMeta.TLabel", wraplength=310).pack(anchor="w", pady=(5, 0))
            actions = ttk.Frame(card, style="Card.TFrame")
            actions.pack(fill="x", pady=(14, 0))
            ttk.Button(actions, text="Chi tiết", command=lambda t=task: self.app.edit_task(t.id)).pack(side="left")
            if task.status == "todo":
                ttk.Button(actions, text="Bắt đầu", command=lambda t=task: self.app.transition_task(t.id, "in_progress")).pack(side="right", padx=(4, 0))
            if task.status in ("todo", "in_progress"):
                ttk.Button(actions, text="Hoàn thành", command=lambda t=task: self.app.transition_task(t.id, "completed")).pack(side="right", padx=(4, 0))
            else:
                ttk.Button(actions, text="Mở lại", command=lambda t=task: self.app.transition_task(t.id, "todo", "Đã mở lại")).pack(side="right")
            self._bind_card_wheel(card)


class TaskDialog(tk.Toplevel):
    def __init__(self, app, task: Task | None = None):
        super().__init__(app.root)
        self.app, self.task = app, task
        self.title("Chi tiết công việc" if task else "Tạo công việc / ghi nhớ mới")
        self.geometry("770x740")
        self.minsize(640, 620)
        self.transient(app.root)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.columnconfigure(0, weight=1)
        frame = ttk.Frame(self, padding=23)
        frame.grid(sticky="nsew")
        self.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        self.title_var = tk.StringVar(value=task.title if task else "")
        self.category_var = tk.StringVar(value=task.category if task else "")
        deadline = task.deadline if task else datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
        self.time_var = tk.StringVar(value=deadline.strftime("%H:%M"))
        ttk.Label(frame, text="Chi tiết công việc" if task else "Tạo công việc", font=ui_font(self, 18, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 17))
        ttk.Label(frame, text="Tên công việc *").grid(row=1, column=0, sticky="w", padx=(0, 15))
        title_entry = ttk.Entry(frame, textvariable=self.title_var)
        title_entry.grid(row=1, column=1, sticky="ew", pady=7)
        ttk.Label(frame, text="Deadline *").grid(row=2, column=0, sticky="w")
        when = ttk.Frame(frame)
        when.grid(row=2, column=1, sticky="w", pady=7)
        self.date_entry = DateEntry(when, value=deadline.date())
        self.date_entry.pack(side="left")
        ttk.Label(when, text="Giờ:").pack(side="left", padx=(12, 5))
        ttk.Entry(when, textvariable=self.time_var, width=8).pack(side="left")
        ttk.Label(when, text="hh:mm", style="Subtitle.TLabel").pack(side="left", padx=6)
        ttk.Label(frame, text="Phân loại").grid(row=3, column=0, sticky="w")
        categories = sorted({t.category for t in app.store.list_tasks() if t.category})
        ttk.Combobox(frame, textvariable=self.category_var, values=categories).grid(row=3, column=1, sticky="ew", pady=7)
        ttk.Label(frame, text="Nội dung").grid(row=4, column=0, sticky="nw", pady=8)
        self.content_text = ScrolledText(frame, height=7, wrap="word", relief="solid", borderwidth=1)
        self.content_text.grid(row=4, column=1, sticky="nsew", pady=7)
        ttk.Label(frame, text="Yêu cầu").grid(row=5, column=0, sticky="nw", pady=8)
        self.requirements_text = ScrolledText(frame, height=5, wrap="word", relief="solid", borderwidth=1)
        self.requirements_text.grid(row=5, column=1, sticky="nsew", pady=7)
        frame.rowconfigure(4, weight=1)
        frame.rowconfigure(5, weight=1)
        if task:
            self.content_text.insert("1.0", task.content)
            self.requirements_text.insert("1.0", task.requirements)
            ttk.Label(frame, text=f"{task.code} · {STATUS_LABELS[task.status]}", style="Subtitle.TLabel").grid(row=6, column=0, columnspan=2, sticky="w", pady=10)
        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        if task and task.status == "in_progress":
            ttk.Button(buttons, text="Tạm dừng", command=lambda: self.change_status("todo", "Tạm dừng")).pack(side="left", padx=(0, 7))
        if task and task.status in ("todo", "in_progress"):
            ttk.Button(buttons, text="Hủy việc", command=lambda: self.change_status("canceled")).pack(side="left")
        elif task:
            ttk.Button(buttons, text="Mở lại", command=lambda: self.change_status("todo", "Đã mở lại")).pack(side="left")
        ttk.Button(buttons, text="Lưu công việc", style="Accent.TButton", command=self.save).pack(side="right")
        ttk.Button(buttons, text="Đóng", command=self.cancel).pack(side="right", padx=9)
        self._initial = self.snapshot()
        self.bind("<Control-s>", lambda _e: self.save())
        self.bind("<Escape>", lambda _e: self.cancel())
        title_entry.focus_set()
        self.grab_set()

    def snapshot(self):
        return (self.title_var.get(), self.category_var.get(), self.time_var.get(),
                self.date_entry.get(), self.content_text.get("1.0", "end-1c"), self.requirements_text.get("1.0", "end-1c"))

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
                          requirements=self.requirements_text.get("1.0", "end-1c"))
            if self.task:
                self.app.store.update_task(self.task.id, **fields)
            else:
                self.app.store.create_task(**fields)
        except (ValueError, OSError) as exc:
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


class SettingsDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("Cài đặt nhắc việc")
        self.transient(app.root)
        frame = ttk.Frame(self, padding=26)
        frame.pack(fill="both", expand=True)
        settings = app.store.get_settings()
        ttk.Label(frame, text="Nhắc công việc hằng ngày", font=ui_font(self, 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 18))
        self.days = tk.StringVar(value=str(settings["days_before"]))
        self.at_time = tk.StringVar(value=settings["daily_time"])
        self.enabled = tk.BooleanVar(value=settings["notifications_enabled"])
        ttk.Label(frame, text="Số ngày trước deadline (1–30):").grid(row=1, column=0, sticky="w", padx=(0, 15), pady=9)
        ttk.Spinbox(frame, from_=1, to=30, textvariable=self.days, width=7).grid(row=1, column=1, sticky="w")
        ttk.Label(frame, text="Giờ nhắc hằng ngày (hh:mm):").grid(row=2, column=0, sticky="w", pady=9)
        ttk.Entry(frame, textvariable=self.at_time, width=9).grid(row=2, column=1, sticky="w")
        ttk.Checkbutton(frame, text="Bật nhắc việc và nhắc lịch", variable=self.enabled).grid(row=3, column=0, columnspan=2, sticky="w", pady=12)
        ttk.Label(frame, text="Lịch có mốc nhắc riêng theo phút và ngày.\nMáy cần đang bật, thức và ứng dụng đang chạy.\nGiờ nhắc dùng giờ địa phương trên máy.", style="Subtitle.TLabel").grid(row=4, column=0, columnspan=2, sticky="w", pady=12)
        ttk.Button(frame, text="Lưu cài đặt", style="Accent.TButton", command=self.save).grid(row=5, column=1, sticky="e", pady=(8, 0))
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
        self.title("Xuất báo cáo Excel")
        self.transient(app.root)
        frame = ttk.Frame(self, padding=26)
        frame.pack(fill="both", expand=True)
        today = date.today()
        ttk.Label(frame, text="Khoảng ngày của các buổi lịch", font=ui_font(self, 15, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))
        ttk.Label(frame, text="Từ ngày:").grid(row=1, column=0, sticky="w", pady=8)
        self.start = DateEntry(frame, value=today.replace(day=1))
        self.start.grid(row=1, column=1, padx=12)
        ttk.Label(frame, text="Đến ngày:").grid(row=2, column=0, sticky="w", pady=8)
        self.end = DateEntry(frame, value=today.replace(day=calendar.monthrange(today.year, today.month)[1]))
        self.end.grid(row=2, column=1, padx=12)
        ttk.Label(frame, text="Báo cáo luôn gồm toàn bộ công việc.\nLịch chỉ mở rộng trong khoảng ngày đã chọn.\nFile Excel là báo cáo, không thay thế bản sao lưu.", style="Subtitle.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=17)
        ttk.Button(frame, text="Chọn nơi lưu và xuất", style="Accent.TButton", command=self.export).grid(row=4, column=0, columnspan=2, sticky="e")
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


class NhacViecApp:
    def __init__(self, root: tk.Tk, store, data_dir: Path, *, integrations=True, enable_timers=True):
        self.root, self.store, self.data_dir = root, store, Path(data_dir)
        self.instance_lock = None
        self._closing = False
        self._after_ids = set()
        self.pages = {}
        self.current_page = "active"
        self.notification_window = None
        self.notification_text = None
        self.notifications = []
        root.title(f"Nhắc việc anh Hà {__version__} — bản dựng mới")
        root.geometry("1320x850")
        root.minsize(1120, 720)
        root.configure(background=BG)
        configure_style(root)
        root.report_callback_exception = self.report_exception
        root.protocol("WM_DELETE_WINDOW", self.minimize)
        shell = ttk.Frame(root)
        shell.pack(fill="both", expand=True)
        self.sidebar = ttk.Frame(shell, style="Side.TFrame", padding=(16, 22), width=228)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        ttk.Button(self.sidebar, text="Thoát hẳn", command=self.exit).pack(side="bottom", fill="x", pady=(15, 0))
        ttk.Label(self.sidebar, text="NHẮC VIỆC\nANH HÀ", style="Side.TLabel").pack(anchor="w", padx=7, pady=(0, 23))
        ttk.Button(self.sidebar, text="＋ Tạo công việc", style="Accent.TButton", command=self.new_task).pack(fill="x", pady=(0, 15))
        self.nav_buttons = {}
        for key, text in [("active", "Cần làm"), ("in_progress", "Đang thực hiện"), ("due", "Sắp đến hạn"), ("completed", "Đã hoàn thành"), ("canceled", "Đã hủy"), ("calendar", "Lịch tuần / tháng / năm")]:
            b = ttk.Button(self.sidebar, text=text, style="Nav.TButton", command=lambda k=key: self.show_page(k))
            b.pack(fill="x", pady=3)
            self.nav_buttons[key] = b
        ttk.Separator(self.sidebar).pack(fill="x", pady=14)
        for text, action in [("Xuất dữ liệu Excel", lambda: ExportDialog(self)), ("Cài đặt nhắc việc", lambda: SettingsDialog(self)), ("Sao lưu dữ liệu", self.backup), ("Khôi phục dữ liệu", self.restore), ("Thông báo đã nhận", self.show_notification_center), ("Thông tin bản dựng", self.about)]:
            ttk.Button(self.sidebar, text=text, style="Nav.TButton", command=action).pack(fill="x", pady=2)
        self.content = ttk.Frame(shell)
        self.content.pack(side="left", fill="both", expand=True)
        self.status_var = tk.StringVar(value="Dữ liệu được lưu trên máy · Bản dựng mới có thư mục dữ liệu riêng")
        ttk.Label(root, textvariable=self.status_var, padding=(16, 7), style="Subtitle.TLabel").pack(fill="x")
        self.platform = PlatformSupport(root, self.show_window, self.exit, self.on_notification_action)
        if integrations:
            self.platform.start_tray()
        self.reminder_engine = ReminderEngine(store)
        self.show_page("active")
        if enable_timers:
            self._schedule(250, self._platform_tick)
            self._schedule(1000, self._reminder_tick)

    def _schedule(self, delay, callback):
        if not self._closing:
            def run():
                self._after_ids.discard(handle)
                if not self._closing:
                    callback()
            handle = self.root.after(delay, run)
            self._after_ids.add(handle)

    def show_page(self, key):
        if key not in self.pages:
            if key == "calendar":
                self.pages[key] = CalendarView(self.content, self.store, on_change=self.refresh_current)
            else:
                self.pages[key] = TaskListPage(self.content, self, key)
        for page in self.pages.values():
            page.pack_forget()
        self.current_page = key
        self.pages[key].pack(fill="both", expand=True)
        self.refresh_current()

    def refresh_current(self):
        page = self.pages.get(self.current_page)
        if page:
            page.refresh()
        active = len(self.store.list_tasks(status="active"))
        self.nav_buttons["active"].configure(text=f"Cần làm  ·  {active}")
        for key in ("in_progress", "completed", "canceled"):
            self.nav_buttons[key].configure(text=f"{STATUS_LABELS[key]}  ·  {len(self.store.list_tasks(status=key))}")

    def new_task(self):
        return TaskDialog(self)

    def edit_task(self, task_id):
        task = self.store.get_task(task_id)
        if task is None:
            messagebox.showerror("Không tìm thấy", "Công việc không còn tồn tại.", parent=self.root)
            return None
        return TaskDialog(self, task)

    def transition_task(self, task_id, status, reason=""):
        self.store.set_task_status(task_id, status, reason=reason)
        self.refresh_current()

    def backup(self):
        target = filedialog.asksaveasfilename(parent=self.root, title="Sao lưu dữ liệu bản dựng mới", defaultextension=".db", filetypes=[("SQLite", "*.db")], initialfile=f"NhacViec-backup-{datetime.now():%Y%m%d-%H%M%S}.db")
        if not target:
            return
        try:
            self.store.backup(target)
            messagebox.showinfo("Đã sao lưu", f"Đã tạo bản sao nhất quán tại:\n{target}", parent=self.root)
        except Exception as exc:
            logging.exception("Sao lưu thất bại")
            messagebox.showerror("Không sao lưu được", str(exc), parent=self.root)

    def restore(self):
        target = filedialog.askopenfilename(parent=self.root, title="Khôi phục bản sao lưu của bản dựng mới", filetypes=[("SQLite", "*.db"), ("Tất cả", "*.*")])
        if not target:
            return
        if not messagebox.askyesno("Thay thế dữ liệu bản dựng mới", "Khôi phục thay thế toàn bộ dữ liệu hiện tại, không gộp hai bộ dữ liệu. Một bản sao trước khôi phục sẽ được giữ lại.\n\nChỉ hỗ trợ cơ sở dữ liệu của bản dựng mới. Tiếp tục?", parent=self.root):
            return
        try:
            previous = self.store.restore(target)
            self.reminder_engine = ReminderEngine(self.store)
            self.refresh_current()
            messagebox.showinfo("Đã khôi phục", f"Đã khôi phục dữ liệu. Bản dự phòng trước đó:\n{previous}", parent=self.root)
        except Exception as exc:
            logging.exception("Khôi phục thất bại")
            messagebox.showerror("Không khôi phục được", str(exc), parent=self.root)

    def _platform_tick(self):
        if self._closing:
            return
        try:
            self.platform.process_pending()
        except Exception:
            logging.exception("Xử lý khay hệ thống thất bại")
        self._schedule(250, self._platform_tick)

    def _reminder_tick(self):
        if self._closing:
            return
        try:
            fallback = []
            for item in self.reminder_engine.poll():
                if self.platform.notify(item):
                    self.notifications.append(item)
                    self.reminder_engine.mark_delivered(item)
                else:
                    fallback.append(item)
            if fallback:
                self.notifications.extend(fallback)
                self.show_window()
                self.show_notification_center()
                # A visible in-app notification counts as a delivered fallback.
                for item in fallback:
                    self.reminder_engine.mark_delivered(item)
        except Exception:
            logging.exception("Kiểm tra nhắc việc thất bại")
            self.status_var.set("Nhắc việc gặp lỗi. Xem nhật ký hoặc mở lại ứng dụng.")
        self._schedule(15_000, self._reminder_tick)

    def show_notification_center(self):
        if self.notification_window is not None and self.notification_window.winfo_exists():
            window = self.notification_window
        else:
            window = tk.Toplevel(self.root)
            window.title("Thông báo nhắc việc")
            window.geometry("650x470")
            ttk.Label(window, text="Thông báo trong phiên làm việc", font=ui_font(window, 16, "bold"), padding=16).pack(anchor="w")
            self.notification_text = ScrolledText(window, wrap="word", relief="flat", padx=16, pady=12)
            self.notification_text.pack(fill="both", expand=True)
            ttk.Button(window, text="Đóng", command=window.destroy).pack(anchor="e", padx=16, pady=12)
            self.notification_window = window
        self.notification_text.configure(state="normal")
        self.notification_text.delete("1.0", "end")
        if not self.notifications:
            self.notification_text.insert("end", "Chưa có thông báo trong phiên làm việc này.")
        for item in reversed(self.notifications[-200:]):
            self.notification_text.insert("end", f"{item.title}\n{item.message}\n\n")
        self.notification_text.configure(state="disabled")
        window.deiconify()
        window.lift()

    def on_notification_action(self, item=None):
        self.show_window()
        if item is not None and getattr(item, "schedule_id", None):
            self.show_page("calendar")

    def show_window(self):
        self.root.deiconify()
        self.root.lift()

    def minimize(self):
        self.platform.minimize()
        if not self.platform.tray_available:
            self.status_var.set("Ứng dụng đang chạy; cửa sổ thu nhỏ trên thanh tác vụ. Dùng Thoát hẳn để dừng nhắc.")

    def about(self):
        messagebox.showinfo("Thông tin bản dựng", f"Nhắc việc anh Hà {__version__}\nMã nguồn dựng mới từ tài liệu 1.7.0 và các yêu cầu bổ sung.\n\nDữ liệu: {self.store.path}\n\nBản mới có thư mục riêng. Chưa xác nhận nhập dữ liệu tasks.db của bản cũ.\nCác chức năng Windows cần kiểm thử trên máy Windows trước phát hành.", parent=self.root)

    def report_exception(self, exc_type, value, tb):
        logging.error("Lỗi giao diện: %s", "".join(traceback.format_exception(exc_type, value, tb)))
        messagebox.showerror("Thao tác chưa hoàn tất", f"{value}\n\nNhật ký: {self.data_dir / 'logs' / 'lifecycle.log'}", parent=self.root)

    def exit(self):
        if self._closing:
            return
        if not close_schedule_editors(self.root):
            return
        # Prevent discarding an open task form without the form's own check.
        for child in self.root.winfo_children():
            if isinstance(child, TaskDialog):
                child.cancel()
                if child.winfo_exists():
                    return
        self._closing = True
        for handle in self._after_ids:
            try:
                self.root.after_cancel(handle)
            except tk.TclError:
                pass
        self.platform.stop()
        if self.instance_lock is not None:
            self.instance_lock.close()
        logging.info("Thoát hẳn ứng dụng")
        self.root.destroy()
