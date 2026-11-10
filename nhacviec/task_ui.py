"""Task pages with a clear overview and three compact layout choices."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import ttk

from .task_layouts import TaskCards
from .theme import BG

# Retained for callers that imported the former filter captions. The page now
# shows all unfinished tasks and does not expose the removed filter panel.
ALL_FILTER = "Tất cả việc chưa hoàn thành"
TODO_FILTER = "Chưa bắt đầu"
LAYOUT_LABELS = {"grid": "Lưới", "list": "Danh sách", "wide": "Rộng"}


class TaskListPage(ttk.Frame):
    """Status pages share one layout choice for the current app session."""

    def __init__(self, parent, app, view: str):
        super().__init__(parent, padding=(26, 23))
        self.app, self.view = app, view
        self.visible_tasks = []
        self.query_var = tk.StringVar(self)
        self._search_window = None
        heading = {
            "active": "Việc cần làm", "in_progress": "Đang thực hiện",
            "due": "Sắp đến hạn", "completed": "Đã hoàn thành", "canceled": "Đã hủy",
        }[view]
        descriptions = {
            "active": "Sắp xếp ưu tiên, theo dõi tiến độ và hoàn thành đúng hạn.",
            "in_progress": "Tập trung vào những việc anh đang xử lý.",
            "due": "Những công việc cần được ưu tiên trong thời gian tới.",
            "completed": "Xem lại các công việc đã hoàn thành.",
            "canceled": "Các công việc đã hủy vẫn được lưu để tra cứu.",
        }
        self._description = descriptions[view]
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 18))
        titles = ttk.Frame(header)
        titles.pack(side="left", fill="x", expand=True)
        ttk.Label(titles, text=heading, style="Title.TLabel").pack(anchor="w")
        self.subtitle = ttk.Label(titles, text=self._description, style="Subtitle.TLabel", wraplength=650)
        self.subtitle.pack(anchor="w", fill="x", pady=(4, 0))
        titles.bind("<Configure>", lambda event: self.subtitle.configure(wraplength=max(200, event.width)))
        ttk.Button(header, text="+  Tạo công việc", style="Accent.TButton", command=app.new_task).pack(side="right", padx=(12, 0))

        self.metrics = ttk.Frame(self)
        self.metrics.pack(fill="x", pady=(0, 12))
        self.metric_labels = {}
        for col, (key, label, style) in enumerate((
                ("todo", "Chưa bắt đầu", "Metric.TLabel"),
                ("in_progress", "Đang thực hiện", "Blue.Metric.TLabel"),
                ("late", "Đã quá hạn", "Red.Metric.TLabel"))):
            self.metrics.columnconfigure(col, weight=1, uniform="metrics")
            metric = ttk.Frame(self.metrics, style="Card.TFrame", padding=(15, 10))
            metric.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 6, 0 if col == 2 else 6))
            value = ttk.Label(metric, text="0", style=style)
            value.pack(side="left")
            ttk.Label(metric, text=label, style="MetricMeta.TLabel").pack(side="left", padx=(12, 0))
            self.metric_labels[key] = value

        # A single slim selector replaces the complete filter/search/count area.
        self.layout_toolbar = ttk.Frame(self)
        self.layout_toolbar.pack(fill="x", pady=(0, 12))
        self.layout_selector = ttk.Frame(self.layout_toolbar, style="Surface.TFrame", padding=3)
        self.layout_selector.pack(side="right")
        initial_layout = getattr(app, "_task_layout_mode", "grid")
        if initial_layout not in LAYOUT_LABELS:
            initial_layout = "grid"
        self.layout_var = tk.StringVar(self, value=initial_layout)
        self.layout_buttons = {}
        for mode, label in LAYOUT_LABELS.items():
            button = ttk.Radiobutton(
                self.layout_selector, text=label, variable=self.layout_var, value=mode,
                style="Segment.TRadiobutton", command=lambda value=mode: self.set_layout(value),
            )
            button.pack(side="left")
            self.layout_buttons[mode] = button
        self.cards = TaskCards(self, app, layout=initial_layout,
                               empty_message="Tạo công việc mới hoặc nhấn Ctrl+F để đổi tìm kiếm.",
                               empty_action=("Tạo công việc", app.new_task))
        self.cards.pack(fill="both", expand=True)
        self.canvas = self.cards.canvas
        self.card_container = self.cards.card_container
        self.refresh()

    @property
    def cards_by_id(self):
        return self.cards.cards_by_id

    @property
    def layout_mode(self):
        return self.layout_var.get()

    def set_layout(self, mode):
        if mode not in LAYOUT_LABELS:
            raise ValueError("Kiểu hiển thị công việc không hợp lệ.")
        self.layout_var.set(mode)
        self.app._task_layout_mode = mode
        self.cards.set_layout(mode)

    def open_search(self):
        """Keep Ctrl+F available without recreating the removed on-page panel."""
        window = self._search_window
        if window is not None and window.winfo_exists():
            window.lift()
            self.search_entry.focus_set()
            self.search_entry.selection_range(0, "end")
            return window
        window = self._search_window = tk.Toplevel(self)
        window.title("Tìm công việc")
        window.transient(self.app.root)
        window.configure(background=BG)
        window.resizable(True, False)
        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Tìm theo tên hoặc mã công việc", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))
        query = tk.StringVar(window, value=self.query_var.get())
        self.search_entry = ttk.Entry(frame, textvariable=query, width=36)
        self.search_entry.grid(row=1, column=0, sticky="ew")
        actions = ttk.Frame(frame)
        actions.grid(row=2, column=0, sticky="ew", pady=(16, 0))

        def apply_query():
            self.query_var.set(query.get())
            self.refresh()
            window.destroy()

        def clear_query():
            self.clear_filters()
            window.destroy()

        ttk.Button(actions, text="Xóa tìm kiếm", command=clear_query).pack(side="left")
        ttk.Button(actions, text="Tìm", style="Accent.TButton", command=apply_query).pack(side="right")
        ttk.Button(actions, text="Đóng", command=window.destroy).pack(side="right", padx=(0, 8))
        window.bind("<Return>", lambda _event: apply_query())
        window.bind("<Escape>", lambda _event: window.destroy())
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, "end")
        window.grab_set()
        return window

    def apply_filters(self):
        # Compatibility for integrations that previously applied a search query.
        self.refresh()

    def clear_filters(self):
        self.query_var.set("")
        self.refresh()

    def refresh(self):
        status = "active" if self.view in ("active", "due") else self.view
        tasks = self.app.store.list_tasks(status=status, query=self.query_var.get(), sort_by="deadline")
        if self.view == "due":
            cutoff = date.today() + timedelta(days=self.app.store.get_settings()["days_before"])
            tasks = [task for task in tasks if task.deadline.date() <= cutoff]
        self.visible_tasks = tasks
        active = self.app.store.list_tasks(status="active")
        self.metric_labels["todo"].configure(text=str(sum(task.status == "todo" for task in active)))
        self.metric_labels["in_progress"].configure(text=str(sum(task.status == "in_progress" for task in active)))
        self.metric_labels["late"].configure(text=str(sum(task.deadline < datetime.now() for task in active)))
        query = self.query_var.get().strip()
        self.subtitle.configure(text=f"Đang tìm: {query}  ·  Ctrl+F để sửa hoặc xóa tìm kiếm." if query else self._description)
        shared_layout = getattr(self.app, "_task_layout_mode", self.layout_mode)
        if shared_layout in LAYOUT_LABELS and shared_layout != self.layout_mode:
            self.layout_var.set(shared_layout)
            self.cards.set_layout(shared_layout)
        self.cards.set_tasks(tasks)
