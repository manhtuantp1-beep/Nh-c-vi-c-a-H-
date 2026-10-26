"""Readable task overview with compact rows and progressively disclosed filters."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import messagebox, ttk

from .dialogs import STATUS_LABELS
from .models import Task
from .theme import BG
from .widgets import DateEntry

ALL_FILTER = "Tất cả việc chưa hoàn thành"
TODO_FILTER = "Chưa bắt đầu"


class TaskCards(ttk.Frame):
    """The same scrollable task cards and actions in task pages and calendars.

    ``empty_action`` is an optional (caption, callback) pair. The host owns task
    filtering and refreshes after mutations; this widget only renders that list.
    """

    def __init__(self, parent, app, *, empty_title="Chưa có công việc ở đây",
                 empty_message="Tạo công việc mới để bắt đầu.", empty_action=None):
        super().__init__(parent)
        self.app = app
        self.empty_title = empty_title
        self.empty_message = empty_message
        self.empty_action = empty_action
        self.visible_tasks: list[Task] = []
        self.cards_by_id = {}
        self._resize_job = None
        self.canvas = tk.Canvas(self, background=BG, highlightthickness=0, borderwidth=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", padx=(7, 0))
        self.canvas.pack(side="left", fill="both", expand=True)
        self.card_container = ttk.Frame(self.canvas)
        self.card_container.columnconfigure(0, weight=1)
        self._canvas_window = self.canvas.create_window((0, 0), window=self.card_container, anchor="nw")
        self.card_container.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._resize)
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<Button-4>", lambda _e: self.canvas.yview_scroll(-3, "units"))
        self.canvas.bind("<Button-5>", lambda _e: self.canvas.yview_scroll(3, "units"))

    def set_tasks(self, tasks):
        self.visible_tasks = list(tasks)
        self._render_cards()

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
        self._queue_wraps()

    def _queue_wraps(self, _event=None):
        if self._resize_job is None:
            self._resize_job = self.after_idle(self._update_wraps)

    def destroy(self):
        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except tk.TclError:
                pass
            self._resize_job = None
        super().destroy()

    def _update_wraps(self):
        self._resize_job = None
        for card in self.cards_by_id.values():
            self._fit_card(card)

    def _fit_card(self, card, _event=None):
        if not card.winfo_exists():
            return
        # A Configure event precedes grid's child layout. Derive the available
        # column from the new card width and the controls' natural widths so
        # resizing cannot keep a stale wrap length from the previous window.
        right_column = [child for child in card.grid_slaves(column=1)
                        if int(child.grid_info()["column"]) == 1 and int(child.grid_info().get("columnspan", 1)) == 1]
        right_width = max((child.winfo_reqwidth() for child in right_column), default=260)
        width = max(160, card.winfo_width() - 34 - right_width - 18)
        for label in getattr(card, "wrapping_labels", []):
            target_width = max(160, card.winfo_width() - 36) if getattr(label, "_full_card_width", False) else width
            if int(label.cget("wraplength")) != target_width:
                label.configure(wraplength=target_width)

    def _render_cards(self):
        for child in self.card_container.winfo_children():
            child.destroy()
        self.cards_by_id.clear()
        if not self.visible_tasks:
            empty = ttk.Frame(self.card_container, style="Card.TFrame", padding=(28, 35))
            empty.grid(row=0, column=0, sticky="ew")
            ttk.Label(empty, text=self.empty_title, style="CardTitle.TLabel").pack(anchor="center")
            ttk.Label(empty, text=self.empty_message, style="CardMeta.TLabel").pack(pady=(8, 16))
            if self.empty_action:
                caption, callback = self.empty_action
                ttk.Button(empty, text=caption, command=callback).pack()
            self._bind_card_wheel(empty)
            return
        for index, task in enumerate(self.visible_tasks):
            card = ttk.Frame(self.card_container, style="Card.TFrame", padding=(16, 12))
            card.grid(row=index, column=0, sticky="ew", pady=(0, 9))
            card.columnconfigure(0, weight=1)
            self.cards_by_id[task.id] = card
            title = task.title if len(task.title) <= 105 else task.title[:102] + "…"
            title_label = ttk.Label(card, text=title, style="CardTitle.TLabel", wraplength=520)
            title_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
            pill = {"todo": "Todo", "in_progress": "Progress", "completed": "Done", "canceled": "Canceled"}[task.status]
            ttk.Label(card, text=STATUS_LABELS[task.status], style=f"{pill}.Pill.TLabel").grid(row=0, column=1, sticky="e")
            category = task.category or "Chưa phân loại"
            metadata = ttk.Label(card, text=f"{category}   ·   {task.code}", style="CardMeta.TLabel", wraplength=520)
            metadata.grid(row=1, column=0, sticky="w", pady=(5, 8), padx=(0, 15))
            late = task.status in ("todo", "in_progress") and task.deadline < datetime.now()
            when = task.deadline.strftime("%d/%m/%Y · %H:%M")
            ttk.Label(card, text=("Quá hạn · " if late else "Hạn: ") + when,
                      style="Late.TLabel" if late else "CardMeta.TLabel").grid(row=1, column=1, sticky="e", pady=(5, 8))
            content = task.reason or task.content.replace("\n", " ") or "Chưa có nội dung chi tiết."
            if len(content) > 80:
                content = content[:77] + "…"
            content_label = ttk.Label(card, text=content, style="CardBody.TLabel", wraplength=700)
            content_label._full_card_width = True
            content_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))
            wrapping_labels = [title_label, metadata, content_label]
            note = " ".join(getattr(task, "notes", "").split())
            if note:
                preview = note if len(note) <= 160 else note[:157] + "…"
                note_label = ttk.Label(card, text=f"Ghi chú: {preview}",
                                       style="CardBody.TLabel", wraplength=700)
                note_label._full_card_width = True
                note_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
                wrapping_labels.append(note_label)
            actions = ttk.Frame(card, style="Surface.TFrame")
            actions.grid(row=4, column=0, columnspan=2, sticky="e", pady=(12, 0))
            ttk.Button(actions, text="Chi tiết", style="Compact.TButton", command=lambda t=task: self.app.edit_task(t.id)).pack(side="left", padx=(0, 5))
            ttk.Button(actions, text="Ghi chú", style="Compact.TButton", command=lambda t=task: self.app.edit_task_notes(t.id)).pack(side="left", padx=(0, 5))
            if task.status == "todo":
                ttk.Button(actions, text="Bắt đầu", style="Compact.TButton", command=lambda t=task: self.app.transition_task(t.id, "in_progress")).pack(side="left", padx=(0, 5))
            if task.status in ("todo", "in_progress"):
                ttk.Button(actions, text="Hoàn thành", style="Compact.TButton", command=lambda t=task: self.app.transition_task(t.id, "completed")).pack(side="left")
            else:
                ttk.Button(actions, text="Mở lại", style="Compact.TButton", command=lambda t=task: self.app.transition_task(t.id, "todo", "Đã mở lại")).pack(side="left")
            card.wrapping_labels = wrapping_labels
            card.bind("<Configure>", lambda event, c=card: self._fit_card(c, event))
            title_label.configure(cursor="hand2")
            title_label.bind("<Button-1>", lambda _e, t=task: self.app.edit_task(t.id))
            self._bind_card_wheel(card)
        self._queue_wraps()


class TaskListPage(ttk.Frame):
    """Each status page retains its search, ordering and date range."""

    def __init__(self, parent, app, view: str):
        super().__init__(parent, padding=(26, 23))
        self.app, self.view = app, view
        self.visible_tasks: list[Task] = []
        self._advanced_open = False
        heading = {"active": "Việc cần làm", "in_progress": "Đang thực hiện", "due": "Sắp đến hạn",
                   "completed": "Đã hoàn thành", "canceled": "Đã hủy"}[view]
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 18))
        titles = ttk.Frame(header)
        titles.pack(side="left", fill="x", expand=True)
        ttk.Label(titles, text=heading, style="Title.TLabel").pack(anchor="w")
        subtitles = {"active": "Sắp xếp ưu tiên, theo dõi tiến độ và hoàn thành đúng hạn.",
                     "in_progress": "Tập trung vào những việc anh đang xử lý.",
                     "due": "Những công việc cần được ưu tiên trong thời gian tới.",
                     "completed": "Xem lại các công việc đã hoàn thành.", "canceled": "Các công việc đã hủy vẫn được lưu để tra cứu."}
        ttk.Label(titles, text=subtitles[view], style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Button(header, text="+  Tạo công việc", style="Accent.TButton", command=app.new_task).pack(side="right", padx=(12, 0))

        metrics = self.metrics = ttk.Frame(self)
        metrics.pack(fill="x", pady=(0, 17))
        self.metric_labels = {}
        for col, (key, label, style) in enumerate((("todo", "Chưa bắt đầu", "Metric.TLabel"),
                                                 ("in_progress", "Đang thực hiện", "Blue.Metric.TLabel"),
                                                 ("late", "Đã quá hạn", "Red.Metric.TLabel"))):
            metrics.columnconfigure(col, weight=1, uniform="metrics")
            metric = ttk.Frame(metrics, style="Card.TFrame", padding=(15, 10))
            metric.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 6, 0 if col == 2 else 6))
            value = ttk.Label(metric, text="0", style=style)
            value.pack(side="left")
            ttk.Label(metric, text=label, style="MetricMeta.TLabel").pack(side="left", padx=(12, 0))
            self.metric_labels[key] = value

        self.filters = ttk.Frame(self, style="Card.TFrame", padding=(15, 12))
        self.filters.pack(fill="x")
        self.filters.columnconfigure(1, weight=1)
        self._filters_stacked = None
        self.filter_var = tk.StringVar(value=ALL_FILTER)
        self.filter_group = None
        if view == "active":
            self.filter_group = ttk.Frame(self.filters, style="Surface.TFrame")
            self.filter_group.grid(row=0, column=0, sticky="ew", padx=(0, 14))
            ttk.Label(self.filter_group, text="Hiển thị", style="Field.TLabel").pack(anchor="w", pady=(0, 6))
            self.filter_combo = ttk.Combobox(self.filter_group, state="readonly", textvariable=self.filter_var,
                                             values=(ALL_FILTER, TODO_FILTER), width=27)
            self.filter_combo.pack(fill="x")
            self.filter_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        self.search_group = ttk.Frame(self.filters, style="Surface.TFrame")
        self.search_group.grid(row=0, column=1, sticky="ew")
        ttk.Label(self.search_group, text="Tìm công việc", style="Field.TLabel").pack(anchor="w", pady=(0, 6))
        search_row = ttk.Frame(self.search_group, style="Surface.TFrame")
        search_row.pack(fill="x")
        self.query_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_row, textvariable=self.query_var, width=14)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda _e: self.apply_filters())
        ttk.Button(search_row, text="Tìm", width=5, command=self.apply_filters).pack(side="left", padx=(8, 0))
        self.advanced_button = ttk.Button(search_row, text="Bộ lọc +", width=10, style="Quiet.TButton", command=self.toggle_advanced)
        self.advanced_button.pack(side="left", padx=(4, 0))
        self.advanced = ttk.Frame(self.filters, style="Surface.TFrame")
        self.advanced.columnconfigure(0, weight=1)
        ordering = ttk.Frame(self.advanced, style="Surface.TFrame")
        ordering.grid(row=0, column=0, sticky="ew", pady=(13, 10))
        self.sort_var = tk.StringVar(value="Deadline")
        self.descending = tk.BooleanVar(value=False)
        ttk.Label(ordering, text="Sắp xếp theo", style="Field.TLabel").pack(side="left")
        ttk.Combobox(ordering, state="readonly", textvariable=self.sort_var,
                     values=("Deadline", "Ngày tạo"), width=13).pack(side="left", padx=(10, 12))
        ttk.Checkbutton(ordering, text="Giảm dần", variable=self.descending, style="Surface.TCheckbutton").pack(side="left")
        self.filter_actions = ttk.Frame(self.advanced, style="Surface.TFrame")
        self.filter_actions.grid(row=0, column=1, sticky="e", pady=(13, 10), padx=(12, 0))
        ttk.Button(self.filter_actions, text="Áp dụng", width=7, style="Compact.TButton", command=self.apply_filters).pack(side="right", padx=(6, 0))
        ttk.Button(self.filter_actions, text="Xóa lọc", width=7, style="Compact.TButton", command=self.clear_filters).pack(side="right")
        dates = ttk.Frame(self.advanced, style="Surface.TFrame")
        dates.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Label(dates, text="Từ ngày", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.date_from = DateEntry(dates, value=None, allow_empty=True, width=10)
        self.date_from.grid(row=0, column=1, sticky="w")
        ttk.Label(dates, text="Đến ngày", style="Field.TLabel").grid(row=0, column=2, padx=(16, 8))
        self.date_to = DateEntry(dates, value=None, allow_empty=True, width=10)
        self.date_to.grid(row=0, column=3, sticky="w")
        self.filters.bind("<Configure>", self._layout_filters)

        listing = ttk.Frame(self)
        listing.pack(fill="x", pady=(16, 6))
        self.count_label = ttk.Label(listing, style="Section.TLabel")
        self.count_label.pack(side="left")
        self.list_note = ttk.Label(listing, text="Theo hạn hoàn thành", style="Subtitle.TLabel")
        self.list_note.pack(side="right")
        self.hint = ttk.Label(self, style="Subtitle.TLabel", wraplength=800)
        self.hint.pack(anchor="w", pady=(0, 10))
        self.cards = TaskCards(
            self, app,
            empty_message="Thử xóa bộ lọc hoặc tạo công việc mới để bắt đầu.",
            empty_action=("Xóa bộ lọc", self.clear_filters),
        )
        self.cards.pack(fill="both", expand=True)
        self.canvas = self.cards.canvas
        self.card_container = self.cards.card_container
        self.canvas.bind("<Configure>", lambda event: self.hint.configure(wraplength=max(400, event.width)), add="+")
        self.refresh()

    def toggle_advanced(self):
        self._advanced_open = not self._advanced_open
        if self._advanced_open:
            self.advanced.grid(row=2, column=0, columnspan=2, sticky="ew")
        else:
            self.advanced.grid_remove()
        self._filter_caption()
        self._layout_filters()

    def _layout_filters(self, _event=None):
        """Keep larger text usable instead of shrinking controls to fit one row."""
        available = max(1, self.filters.winfo_width() - 32)
        stacked = bool(self.filter_group is not None and
                       self.filter_group.winfo_reqwidth() + self.search_group.winfo_reqwidth() + 14 > available)
        if stacked != self._filters_stacked:
            self._filters_stacked = stacked
            if self.filter_group is None:
                self.search_group.grid_configure(row=0, column=0, columnspan=2, pady=0)
                self.filters.columnconfigure(0, weight=1)
                self.filters.columnconfigure(1, weight=0)
            elif stacked:
                self.filter_group.grid_configure(row=0, column=0, columnspan=2, padx=0)
                self.search_group.grid_configure(row=1, column=0, columnspan=2, pady=(10, 0))
                self.filters.columnconfigure(0, weight=1)
                self.filters.columnconfigure(1, weight=0)
            else:
                self.filter_group.grid_configure(row=0, column=0, columnspan=1, padx=(0, 14))
                self.search_group.grid_configure(row=0, column=1, columnspan=1, pady=0)
                self.filters.columnconfigure(0, weight=0)
                self.filters.columnconfigure(1, weight=1)
        # Expanded filters take priority over summary tiles in a narrow window.
        # Hiding only the tiles keeps the actual task list usable below them.
        if stacked and self._advanced_open:
            if self.metrics.winfo_manager():
                self.metrics.pack_forget()
        elif not self.metrics.winfo_manager():
            self.metrics.pack(fill="x", pady=(0, 17), before=self.filters)

    def _filter_caption(self):
        count = sum((bool(self.date_from.get()), bool(self.date_to.get()),
                     self.descending.get(), self.sort_var.get() != "Deadline"))
        caption = "Thu gọn −" if self._advanced_open else f"Bộ lọc ({count})" if count else "Bộ lọc +"
        self.advanced_button.configure(text=caption)

    @property
    def cards_by_id(self):
        return self.cards.cards_by_id

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
        self._filter_caption()
        active = self.app.store.list_tasks(status="active")
        self.metric_labels["todo"].configure(text=str(sum(t.status == "todo" for t in active)))
        self.metric_labels["in_progress"].configure(text=str(sum(t.status == "in_progress" for t in active)))
        self.metric_labels["late"].configure(text=str(sum(t.deadline < datetime.now() for t in active)))
        self.count_label.configure(text=f"{len(tasks)} công việc")
        self.list_note.configure(text="Theo hạn hoàn thành" if self.sort_var.get() == "Deadline" else "Theo ngày tạo")
        if self.view == "active":
            text = ("Việc mới và đang làm, gồm cả việc tạm dừng hoặc mở lại."
                    if self.filter_var.get() == ALL_FILTER else "Việc chưa bắt đầu, gồm cả việc tạm dừng hoặc mở lại.")
        elif self.view == "due":
            text = "Gồm các việc quá hạn và các việc trong khoảng ngày nhắc đã chọn."
        else:
            text = "Chọn Chi tiết để xem nội dung và cập nhật công việc."
        self.hint.configure(text=text)
        self.cards.set_tasks(self.visible_tasks)
