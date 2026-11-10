"""Shared task views with readable grid, compact list and wide-card layouts."""
from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import ttk

from .dialogs import STATUS_LABELS
from .models import Task
from .theme import BG
from .widgets import scale_px


LAYOUTS = ("grid", "list", "wide")
LAYOUT_LABELS = {"grid": "Lưới", "list": "Danh sách", "wide": "Rộng"}


def _preview(value: str, limit: int) -> str:
    text = " ".join(value.split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


class TaskCards(ttk.Frame):
    """Render the supplied records without changing their order or contents.

    Calendar hosts retain wide cards by default. Task pages can select ``grid``
    initially and change layout without changing the query or task identity.
    ``empty_action`` is an optional (caption, callback) pair.
    """

    def __init__(self, parent, app, *, layout="wide", empty_title="Chưa có công việc ở đây",
                 empty_message="Tạo công việc mới để bắt đầu.", empty_action=None):
        super().__init__(parent)
        if layout not in LAYOUTS:
            raise ValueError("Kiểu xem công việc không hợp lệ.")
        self.app = app
        self.layout_mode = layout
        self.empty_title, self.empty_message = empty_title, empty_message
        self.empty_action = empty_action
        self.visible_tasks: list[Task] = []
        self.cards_by_id = {}
        self.columns = 1
        self._resize_job = None
        self._restore_job = None
        self._pending_scroll = None
        self._destroying = False
        self._placed_columns = None
        self.canvas = tk.Canvas(self, background=BG, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y", padx=(scale_px(self, 7), 0))
        self.canvas.pack(side="left", fill="both", expand=True)
        self.card_container = ttk.Frame(self.canvas)
        self._canvas_window = self.canvas.create_window((0, 0), window=self.card_container, anchor="nw")
        self.card_container.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._resize)
        self._bind_card_wheel(self.canvas)

    def set_tasks(self, tasks):
        tasks = list(tasks)
        same_records = ([task.id for task in tasks] == [task.id for task in self.visible_tasks])
        if same_records:
            # Rebuilding cards briefly collapses the canvas's scroll region.
            # Preserve the location until new widgets have finished measuring.
            if self._pending_scroll is None:
                self._pending_scroll = self.canvas.yview()[0]
        else:
            self._pending_scroll = 0.0
        self.visible_tasks = tasks
        self._render_cards()

    def set_layout(self, mode):
        if mode not in LAYOUTS:
            raise ValueError("Kiểu xem công việc không hợp lệ.")
        if mode != self.layout_mode:
            self.layout_mode = mode
            self._pending_scroll = 0.0
            self._render_cards()
            self.canvas.yview_moveto(0)

    def _wheel(self, event):
        if not event.delta:
            return None
        units = -int(event.delta / 120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1)
        self.canvas.yview_scroll(units, "units")
        return "break"

    def _bind_card_wheel(self, widget):
        widget.bind("<MouseWheel>", self._wheel)
        widget.bind("<Button-4>", lambda _e: self.canvas.yview_scroll(-3, "units"))
        widget.bind("<Button-5>", lambda _e: self.canvas.yview_scroll(3, "units"))
        for child in widget.winfo_children():
            self._bind_card_wheel(child)

    def _update_scrollregion(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize(self, event):
        self.canvas.itemconfigure(self._canvas_window, width=event.width)
        self._queue_wraps()

    def _queue_wraps(self, _event=None):
        if not self._destroying and self._resize_job is None:
            self._resize_job = self.after_idle(self._update_wraps)

    def destroy(self):
        self._destroying = True
        for name in ("_resize_job", "_restore_job"):
            handle = getattr(self, name)
            if handle is None:
                continue
            try:
                self.after_cancel(handle)
            except tk.TclError:
                pass
            setattr(self, name, None)
        super().destroy()

    def _column_count(self):
        if self.layout_mode != "grid":
            return 1
        width = max(1, self.canvas.winfo_width())
        gap = scale_px(self, 12)
        minimum = scale_px(self, 360)
        # A wider minimum also respects unusually large system font metrics.
        for card in self.cards_by_id.values():
            if card.action_buttons:
                minimum = max(minimum, max(button.winfo_reqwidth() for button in card.action_buttons) * 2
                              + scale_px(self, 40))
        return max(1, min(3, (width + gap) // (minimum + gap)))

    def _place_cards(self):
        self.columns = self._column_count()
        if self._placed_columns == self.columns:
            return
        self._placed_columns = self.columns
        for column in range(3):
            self.card_container.columnconfigure(column, weight=1 if column < self.columns else 0,
                                                uniform="taskcards" if column < self.columns else "")
        gap = scale_px(self, 12)
        if not self.cards_by_id:
            for child in self.card_container.winfo_children():
                child.grid_configure(columnspan=self.columns)
            return
        for index, card in enumerate(self.cards_by_id.values()):
            row, column = divmod(index, self.columns)
            right_gap = gap if column < self.columns - 1 else 0
            card.grid(row=row, column=column, sticky="nsew", padx=(0, right_gap), pady=(0, gap))

    def _update_wraps(self):
        self._resize_job = None
        # An unmapped canvas is one pixel wide. Wrapping long text to that
        # temporary width can request a bitmap tens of thousands of pixels
        # tall. Its real Configure event will queue the fit once it is mapped.
        if self.canvas.winfo_width() <= 1:
            return
        self._place_cards()
        for card in self.cards_by_id.values():
            self._fit_card(card)
        if not self.cards_by_id:
            width = max(60, self.canvas.winfo_width() - scale_px(self, 64))
            for child in self.card_container.winfo_children():
                for label in getattr(child, "wrapping_labels", []):
                    if int(label.cget("wraplength")) != width:
                        label.configure(wraplength=width)
        self._update_scrollregion()
        if self._pending_scroll is not None and self._restore_job is None:
            self._restore_job = self.after_idle(self._restore_scroll)

    def _restore_scroll(self):
        self._restore_job = None
        if self._pending_scroll is not None:
            self._update_scrollregion()
            self.canvas.yview_moveto(self._pending_scroll)
            self._pending_scroll = None

    @staticmethod
    def _wrap(label, width):
        # ttk labels add their own text insets to wraplength. Leave that room
        # inside the grid cell, including under larger Tk font/layout scales.
        width = max(24, int(width) - scale_px(label, 12))
        if int(label.cget("wraplength")) != width:
            label.configure(wraplength=width)

    def _fit_card(self, card, _event=None):
        if not card.winfo_exists() or self.canvas.winfo_width() <= 1:
            return
        gap = scale_px(self, 12)
        estimated = max(1, (self.canvas.winfo_width() - gap * (self.columns - 1)) // self.columns)
        width = card.winfo_width() if card.winfo_width() > 1 else estimated
        body = max(24, width - 2 * card._padding_x - 2)
        if self.layout_mode == "grid":
            for label in card.wrapping_labels:
                self._wrap(label, body)
            self._wrap(card.code_label, body - card.status_label.winfo_reqwidth() - gap)
            self._layout_actions(card, body, maximum_columns=2)
        elif self.layout_mode == "list":
            self._fit_list(card, body)
        else:
            right_width = max(card.status_label.winfo_reqwidth(), card.deadline_label.winfo_reqwidth())
            left_width = max(24, body - right_width - gap)
            # Preserve the familiar title/status and category/deadline pairing.
            for label in card.wrapping_labels:
                self._wrap(label, body if getattr(label, "_full_card_width", False) else left_width)
            self._layout_actions(card, body, maximum_columns=4)

    def _layout_actions(self, card, available, *, maximum_columns):
        buttons = card.action_buttons
        widest = max(button.winfo_reqwidth() for button in buttons)
        gap = scale_px(self, 5)
        columns = min(maximum_columns, len(buttons))
        if columns > 2 and columns * widest + (columns - 1) * gap > available:
            columns = 2
        if columns * widest + (columns - 1) * gap > available:
            columns = 1
        if getattr(card, "_action_columns", None) == columns:
            return
        card._action_columns = columns
        for column in range(4):
            card.actions.columnconfigure(column, weight=1 if column < columns else 0,
                                         uniform="taskactions" if column < columns else "")
        for index, button in enumerate(buttons):
            row, column = divmod(index, columns)
            button.grid(row=row, column=column, sticky="ew",
                        padx=(0, gap if column < columns - 1 else 0), pady=(0, scale_px(self, 4)))

    def _fit_list(self, card, body):
        gap = scale_px(self, 14)
        two_actions = max(button.winfo_reqwidth() for button in card.action_buttons) * 2 + scale_px(self, 5)
        right_width = max(two_actions, card.status_label.winfo_reqwidth())
        stacked = body - right_width - gap < scale_px(self, 220)
        if card._list_stacked != stacked:
            card._list_stacked = stacked
            for label in (card.title_label, card.deadline_label, card.metadata_label, card.note_label):
                if label is not None:
                    label.grid_remove()
            card.status_label.grid_remove()
            card.actions.grid_remove()
            if stacked:
                card.title_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, scale_px(self, 6)))
                card.status_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, scale_px(self, 5)))
                card.deadline_label.grid(row=2, column=0, columnspan=2, sticky="ew")
                card.metadata_label.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(scale_px(self, 3), 0))
                if card.note_label is not None:
                    card.note_label.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(scale_px(self, 4), 0))
                card.actions.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(scale_px(self, 8), 0))
                card.columnconfigure(1, weight=0)
            else:
                card.title_label.grid(row=0, column=0, sticky="ew", padx=(0, gap), pady=(0, scale_px(self, 4)))
                card.status_label.grid(row=0, column=1, sticky="e")
                card.deadline_label.grid(row=1, column=0, sticky="ew", padx=(0, gap))
                card.metadata_label.grid(row=2, column=0, sticky="ew", padx=(0, gap), pady=(scale_px(self, 3), 0))
                if card.note_label is not None:
                    card.note_label.grid(row=3, column=0, sticky="ew", padx=(0, gap), pady=(scale_px(self, 4), 0))
                card.actions.grid(row=1, column=1, rowspan=3, sticky="ne", pady=(scale_px(self, 4), 0))
                card.columnconfigure(1, weight=0)
        for label in card.wrapping_labels:
            self._wrap(label, body if stacked else body - right_width - gap)
        self._layout_actions(card, body if stacked else right_width, maximum_columns=4 if stacked else 2)

    def _status(self, card, task):
        pill = {"todo": "Todo", "in_progress": "Progress", "completed": "Done", "canceled": "Canceled"}[task.status]
        card.status_label = ttk.Label(card, text=STATUS_LABELS[task.status], style=f"{pill}.Pill.TLabel")

    def _deadline(self, card, task):
        late = task.status in ("todo", "in_progress") and task.deadline < datetime.now()
        text = ("Quá hạn · " if late else "Hạn: ") + task.deadline.strftime("%d/%m/%Y · %H:%M")
        card.deadline_label = ttk.Label(card, text=text, style="Late.TLabel" if late else "CardMeta.TLabel",
                                        wraplength=400)

    def _actions(self, card, task):
        card.actions = ttk.Frame(card, style="Surface.TFrame")
        commands = [("Chi tiết", lambda: self.app.edit_task(task.id)),
                    ("Ghi chú", lambda: self.app.edit_task_notes(task.id))]
        if task.status == "todo":
            commands.append(("Bắt đầu", lambda: self.app.transition_task(task.id, "in_progress")))
        if task.status in ("todo", "in_progress"):
            commands.append(("Hoàn thành", lambda: self.app.transition_task(task.id, "completed")))
        else:
            commands.append(("Mở lại", lambda: self.app.transition_task(task.id, "todo", "Đã mở lại")))
        card.action_buttons = [ttk.Button(card.actions, text=caption, style="Compact.TButton", command=callback)
                               for caption, callback in commands]
        self._layout_actions(card, scale_px(self, 700), maximum_columns=4)

    def _new_card(self, task, *, padding=(16, 12)):
        card = ttk.Frame(self.card_container, style="Card.TFrame",
                         padding=tuple(scale_px(self, value) for value in padding))
        card._padding_x = scale_px(self, padding[0])
        card.columnconfigure(0, weight=1)
        card.wrapping_labels = []
        card.title_label = ttk.Label(card, text=task.title, style="CardTitle.TLabel", wraplength=500)
        card.title_label.configure(cursor="hand2")
        card.title_label.bind("<Button-1>", lambda _e: self.app.edit_task(task.id))
        card.metadata_label = ttk.Label(card, text=f"{task.category or 'Chưa phân loại'}   ·   {task.code}",
                                        style="CardMeta.TLabel", wraplength=500)
        card.note_label = None
        self._status(card, task)
        self._deadline(card, task)
        self._actions(card, task)
        card.bind("<Configure>", self._queue_wraps)
        return card

    def _make_grid(self, task):
        card = self._new_card(task, padding=(16, 14))
        card.columnconfigure(1, weight=1)
        card.status_label.grid(row=0, column=0, sticky="w")
        card.code_label = ttk.Label(card, text=task.code, style="CardMeta.TLabel", wraplength=180, justify="right")
        card.code_label.grid(row=0, column=1, sticky="e", padx=(scale_px(self, 8), 0))
        card.title_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(scale_px(self, 12), scale_px(self, 8)))
        card.deadline_label.grid(row=2, column=0, columnspan=2, sticky="ew")
        card.metadata_label.configure(text=task.category or "Chưa phân loại")
        card.metadata_label.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(scale_px(self, 5), scale_px(self, 8)))
        content = _preview(task.reason or task.content or "Chưa có nội dung chi tiết.", 100)
        content_label = ttk.Label(card, text=content, style="CardBody.TLabel", wraplength=500)
        content_label.grid(row=4, column=0, columnspan=2, sticky="ew")
        note = _preview(getattr(task, "notes", ""), 160)
        if note:
            card.note_label = ttk.Label(card, text=f"Ghi chú: {note}", style="CardBody.TLabel", wraplength=500)
            card.note_label.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(scale_px(self, 8), 0))
        card.rowconfigure(6, weight=1)
        ttk.Separator(card).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(scale_px(self, 12), scale_px(self, 8)))
        card.actions.grid(row=8, column=0, columnspan=2, sticky="sew")
        card.wrapping_labels = [card.title_label, card.deadline_label, card.metadata_label, content_label]
        if card.note_label is not None:
            card.wrapping_labels.append(card.note_label)
        self._layout_actions(card, scale_px(self, 320), maximum_columns=2)
        return card

    def _make_list(self, task):
        card = self._new_card(task, padding=(14, 10))
        card.title_label.configure(text=_preview(task.title, 120))
        note = _preview(getattr(task, "notes", ""), 85)
        if note:
            card.note_label = ttk.Label(card, text=f"Ghi chú: {note}", style="CardMeta.TLabel", wraplength=500)
        card.wrapping_labels = [card.title_label, card.deadline_label, card.metadata_label]
        if card.note_label is not None:
            card.wrapping_labels.append(card.note_label)
        card._list_stacked = None
        self._fit_list(card, scale_px(self, 700))
        return card

    def _make_wide(self, task):
        card = self._new_card(task)
        card.title_label.grid(row=0, column=0, sticky="ew", padx=(0, scale_px(self, 15)))
        card.status_label.grid(row=0, column=1, sticky="e")
        card.metadata_label.grid(row=1, column=0, sticky="ew", pady=(scale_px(self, 5), scale_px(self, 8)),
                                 padx=(0, scale_px(self, 15)))
        # The deadline is not part of the shrinking left text column.
        card.deadline_label.configure(wraplength=0)
        card.deadline_label.grid(row=1, column=1, sticky="e", pady=(scale_px(self, 5), scale_px(self, 8)))
        content_label = ttk.Label(card, text=_preview(task.reason or task.content or "Chưa có nội dung chi tiết.", 80),
                                  style="CardBody.TLabel", wraplength=700)
        content_label._full_card_width = True
        content_label.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(scale_px(self, 2), 0))
        card.wrapping_labels = [card.title_label, card.metadata_label, content_label]
        note = _preview(getattr(task, "notes", ""), 160)
        if note:
            card.note_label = ttk.Label(card, text=f"Ghi chú: {note}", style="CardBody.TLabel", wraplength=700)
            card.note_label._full_card_width = True
            card.note_label.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(scale_px(self, 8), 0))
            card.wrapping_labels.append(card.note_label)
        card.actions.grid(row=4, column=0, columnspan=2, sticky="e", pady=(scale_px(self, 12), 0))
        return card

    def _render_cards(self):
        for child in self.card_container.winfo_children():
            child.destroy()
        self.cards_by_id.clear()
        self._placed_columns = None
        if not self.visible_tasks:
            empty = ttk.Frame(self.card_container, style="Card.TFrame", padding=(scale_px(self, 28), scale_px(self, 35)))
            empty.grid(row=0, column=0, sticky="ew")
            title = ttk.Label(empty, text=self.empty_title, style="CardTitle.TLabel", wraplength=500, justify="center")
            title.pack(anchor="center", fill="x")
            message = ttk.Label(empty, text=self.empty_message, style="CardMeta.TLabel", wraplength=500, justify="center")
            message.pack(fill="x", pady=(scale_px(self, 8), scale_px(self, 16)))
            empty.wrapping_labels = [title, message]
            if self.empty_action:
                caption, callback = self.empty_action
                ttk.Button(empty, text=caption, command=callback).pack()
            self._bind_card_wheel(empty)
        else:
            factory = {"grid": self._make_grid, "list": self._make_list, "wide": self._make_wide}[self.layout_mode]
            for task in self.visible_tasks:
                card = factory(task)
                self.cards_by_id[task.id] = card
                self._bind_card_wheel(card)
        self._place_cards()
        self._queue_wraps()
