"""Weekly/monthly/yearly calendar screens for the reconstructed desktop app."""
from __future__ import annotations

import calendar
import sqlite3
from collections import defaultdict
from datetime import date, datetime, time, timedelta
import tkinter as tk
from tkinter import messagebox, ttk

from .models import Schedule
from .recurrence import expand_schedule
from .widgets import DateEntry, ScrollableForm, format_date, parse_time, ui_font

RECURRENCE_LABELS = {"once": "Một lần", "weekly": "Hằng tuần", "monthly": "Hằng tháng", "yearly": "Hằng năm"}
STATUS_LABELS = {"pending": "Chưa xác nhận", "completed": "Hoàn thành", "skipped": "Bỏ qua"}
WEEKDAYS = ("Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật")


def parse_reminder_days(value: str) -> list[int]:
    """Read a comma/semicolon separated list without accepting fractional days."""
    if not value.strip():
        return []
    parts = value.replace(";", ",").split(",")
    try:
        values = [int(part.strip()) for part in parts if part.strip()]
    except ValueError as exc:
        raise ValueError("Mốc nhắc trước theo ngày phải là số nguyên, ví dụ 7, 1.") from exc
    if not values or any(not 1 <= item <= 365 for item in values):
        raise ValueError("Mỗi mốc nhắc trước phải từ 1 đến 365 ngày.")
    return sorted(set(values), reverse=True)


def _shift_month(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    year, month = divmod(index, 12)
    if not 1 <= year <= 9999:
        raise ValueError("Ngày đã vượt phạm vi được hỗ trợ.")
    month += 1
    return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))


def close_schedule_editors(widget) -> bool:
    """Close descendant editors, honoring every unsaved-changes decision.

    Parent windows should call this before destroying themselves. Tk does not
    run a child Toplevel's WM_DELETE_WINDOW handler when its parent is destroyed.
    """
    for child in list(widget.winfo_children()):
        if isinstance(child, ScheduleEditor):
            child._close()
            if child.winfo_exists():
                child.lift()
                return False
        elif not close_schedule_editors(child):
            return False
    return True


class CalendarView(ttk.Frame):
    """CalendarView(parent, store, on_change=None); ``refresh()`` rereads storage."""

    def __init__(self, parent, store, on_change=None):
        super().__init__(parent, padding=12)
        self.store = store
        self.on_change = on_change
        self.mode = tk.StringVar(self, "week")
        self.anchor = date.today()
        self.selected_date = self.anchor
        self._occurrences = []
        self._by_day = defaultdict(list)
        self._selected_occurrences = {}
        self._range = (self.anchor, self.anchor)
        self._build()
        self.refresh()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1, minsize=220)
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(toolbar, text="Lịch", font=ui_font(self, 19, "bold")).pack(side="left")
        ttk.Button(toolbar, text="Thêm lịch", command=self.add_schedule).pack(side="right", padx=(6, 0))
        ttk.Button(toolbar, text="Quản lý lịch", command=self.manage_schedules).pack(side="right")
        modebar = ttk.Frame(self)
        modebar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        for value, label in (("week", "Tuần"), ("month", "Tháng"), ("year", "Năm")):
            ttk.Radiobutton(modebar, text=label, variable=self.mode, value=value,
                            command=self._mode_changed).pack(side="left", padx=(0, 12))
        ttk.Button(modebar, text="‹", width=3, command=lambda: self._navigate(-1)).pack(side="left", padx=(12, 3))
        ttk.Button(modebar, text="Hôm nay", command=self._today).pack(side="left")
        ttk.Button(modebar, text="›", width=3, command=lambda: self._navigate(1)).pack(side="left", padx=3)
        self.period_label = ttk.Label(modebar, text="", font=ui_font(self, 11, "bold"))
        self.period_label.pack(side="left", padx=15)
        self.summary = ttk.Label(self, text="", wraplength=950)
        self.summary.grid(row=2, column=0, sticky="w", pady=(0, 8))
        self.calendar_frame = ttk.Frame(self)
        self.calendar_frame.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        daybox = ttk.LabelFrame(self, text="Các buổi trong ngày", padding=8)
        daybox.grid(row=4, column=0, sticky="nsew")
        daybox.columnconfigure(0, weight=1)
        daybox.rowconfigure(1, weight=1)
        self.day_label = ttk.Label(daybox, text="", font=ui_font(self, 11, "bold"))
        self.day_label.grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.tree = ttk.Treeview(daybox, columns=("start", "end", "title", "status", "category"),
                                 show="headings", selectmode="browse", height=7)
        for key, label, width in (("start", "Bắt đầu", 65), ("end", "Kết thúc", 65),
                                  ("title", "Tên lịch", 300), ("status", "Kết quả", 150),
                                  ("category", "Phân loại", 120)):
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, minwidth=50, stretch=key in ("title", "category"))
        self.tree.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(daybox, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.tag_configure("completed", foreground="#187349")
        self.tree.tag_configure("skipped", foreground="#777777")
        self.tree.tag_configure("overdue", foreground="#b34935")
        self.tree.tag_configure("snoozed", foreground="#8152aa")
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._selection_changed())
        actions = ttk.Frame(daybox)
        actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.action_buttons = []
        for label, callback in (("Hoàn thành buổi", lambda: self._set_status("completed")),
                                ("Bỏ qua buổi", lambda: self._set_status("skipped")),
                                ("Mở lại buổi", lambda: self._set_status("pending")),
                                ("Nhắc lại sau 10 phút", self._snooze),
                                ("Sửa lịch gốc", self.edit_selected)):
            button = ttk.Button(actions, text=label, command=callback)
            button.pack(side="left", padx=(0, 5))
            self.action_buttons.append(button)
        ttk.Label(self, text="Kết quả được lưu riêng từng buổi. Số giờ là thời lượng đã lên lịch, không phải thời gian làm thực tế.",
                  wraplength=1000, foreground="#65736a").grid(row=5, column=0, sticky="w", pady=(8, 0))

    def _period_range(self):
        if self.mode.get() == "week":
            first = self.anchor - timedelta(days=self.anchor.weekday())
            return first, first + timedelta(days=6)
        if self.mode.get() == "month":
            return self.anchor.replace(day=1), self.anchor.replace(day=calendar.monthrange(self.anchor.year, self.anchor.month)[1])
        return date(self.anchor.year, 1, 1), date(self.anchor.year, 12, 31)

    def refresh(self):
        self._range = self._period_range()
        try:
            self._occurrences = self.store.occurrences(*self._range)
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror("Không đọc được lịch", str(exc), parent=self.winfo_toplevel())
            self._occurrences = []
        self._by_day = defaultdict(list)
        for occurrence in self._occurrences:
            self._by_day[occurrence.start.date()].append(occurrence)
        first, last = self._range
        if self.mode.get() == "week":
            self.period_label.configure(text=f"{format_date(first)} — {format_date(last)}")
        elif self.mode.get() == "month":
            self.period_label.configure(text=f"Tháng {self.anchor.month:02d} / {self.anchor.year}")
        else:
            self.period_label.configure(text=f"Năm {self.anchor.year}")
        completed = sum(o.status == "completed" for o in self._occurrences)
        skipped = sum(o.status == "skipped" for o in self._occurrences)
        hours = sum((o.end - o.start).total_seconds() / 3600 for o in self._occurrences)
        self.summary.configure(text=f"{len(self._occurrences)} buổi · {hours:g} giờ dự kiến · {completed} hoàn thành · {skipped} bỏ qua · {len(self._occurrences) - completed - skipped} chưa xác nhận")
        self._draw_calendar()
        self._draw_day()

    def _mode_changed(self):
        self.anchor = self.selected_date
        self.refresh()

    def _today(self):
        self.anchor = self.selected_date = date.today()
        self.refresh()

    def _navigate(self, step):
        try:
            if self.mode.get() == "week":
                target = self.anchor + timedelta(days=7 * step)
            elif self.mode.get() == "month":
                target = _shift_month(self.anchor, step)
            else:
                target = _shift_month(self.anchor, step * 12)
            self.anchor = self.selected_date = target
            self.refresh()
        except (ValueError, OverflowError) as exc:
            messagebox.showerror("Không thể chuyển lịch", str(exc), parent=self.winfo_toplevel())

    def show_day(self, on_date: date):
        self.selected_date = on_date
        if not self._range[0] <= on_date <= self._range[1]:
            self.anchor = on_date
            self.refresh()
        else:
            self._draw_calendar()
            self._draw_day()

    def _draw_calendar(self):
        for child in self.calendar_frame.winfo_children():
            child.destroy()
        for column in range(7):
            self.calendar_frame.columnconfigure(column, weight=0)
        if self.mode.get() == "week":
            self._draw_week()
        elif self.mode.get() == "month":
            self._draw_month()
        else:
            self._draw_year()

    def _draw_week(self):
        first, _ = self._range
        for col in range(7):
            self.calendar_frame.columnconfigure(col, weight=1, uniform="week")
            day = first + timedelta(days=col)
            frame = ttk.Frame(self.calendar_frame, relief="groove", borderwidth=1, padding=5)
            frame.grid(row=0, column=col, sticky="nsew", padx=2)
            button = ttk.Button(frame, text=f"{WEEKDAYS[col]}\n{day:%d/%m}",
                                command=lambda value=day: self.show_day(value))
            button.pack(fill="x", pady=(0, 5))
            if day == self.selected_date:
                button.state(["pressed"])
            occurrences = self._by_day.get(day, [])
            if not occurrences:
                ttk.Label(frame, text="Chưa có lịch", foreground="#87918a", wraplength=110).pack(anchor="w", pady=5)
            for occurrence in occurrences[:3]:
                symbol = "✓" if occurrence.status == "completed" else "–" if occurrence.status == "skipped" else "•"
                title = occurrence.title if len(occurrence.title) <= 30 else occurrence.title[:29] + "…"
                label = ttk.Label(frame, text=f"{symbol} {occurrence.start:%H:%M}\n{title}", wraplength=120,
                                  cursor="hand2", foreground="#187349" if occurrence.status == "completed" else "#33473c")
                label.pack(anchor="w", fill="x", pady=3)
                label.bind("<Button-1>", lambda _event, value=day: self.show_day(value))
            if len(occurrences) > 3:
                ttk.Label(frame, text=f"+ {len(occurrences) - 3} buổi khác", foreground="#65736a").pack(anchor="w")

    def _draw_month(self):
        year, month = self.anchor.year, self.anchor.month
        for col, label in enumerate(WEEKDAYS):
            self.calendar_frame.columnconfigure(col, weight=1, uniform="month")
            ttk.Label(self.calendar_frame, text=label, anchor="center").grid(row=0, column=col, sticky="ew", pady=(0, 3))
        for row, week in enumerate(calendar.Calendar(firstweekday=0).monthdayscalendar(year, month), 1):
            for col, day in enumerate(week):
                if not day:
                    ttk.Label(self.calendar_frame, text="").grid(row=row, column=col)
                    continue
                value = date(year, month, day)
                count = len(self._by_day.get(value, []))
                label = f"{day:02d}" + (f" · {count} buổi" if count else "")
                if value == date.today():
                    label = "Hôm nay · " + label
                button = ttk.Button(self.calendar_frame, text=label,
                                    command=lambda d=value: self.show_day(d))
                button.grid(row=row, column=col, sticky="nsew", padx=2, pady=2, ipady=5)
                if value == self.selected_date:
                    button.state(["pressed"])

    def _draw_year(self):
        # Keep the daily results usable on a 720px Windows desktop. Full mini
        # calendars consume most of the window; each tile opens the month grid.
        ttk.Style(self).configure("YearMonth.TButton", font=ui_font(self, 10), padding=(10, 8))
        for col in range(4):
            self.calendar_frame.columnconfigure(col, weight=1, uniform="year")
        for month in range(1, 13):
            days = sorted(day.day for day, items in self._by_day.items() if day.month == month and items)
            count = sum(len(items) for day, items in self._by_day.items() if day.month == month)
            dates = ", ".join(f"{day:02d}" for day in days[:4])
            if len(days) > 4:
                dates += "…"
            detail = "Ngày: " + dates if dates else "Xem lịch tháng"
            text = f"Tháng {month:02d}\n{count} buổi\n{detail}"
            button = ttk.Button(self.calendar_frame, text=text, style="YearMonth.TButton",
                                command=lambda m=month: self._open_month(m))
            button.grid(row=(month - 1) // 4, column=(month - 1) % 4, sticky="nsew", padx=3, pady=3)

    def _open_month(self, month):
        self.anchor = self.selected_date = date(self.anchor.year, month, 1)
        self.mode.set("month")
        self.refresh()

    def _draw_day(self):
        self.tree.delete(*self.tree.get_children())
        self._selected_occurrences = {}
        now = datetime.now()
        values = sorted(self._by_day.get(self.selected_date, []), key=lambda item: (item.start, item.title))
        self.day_label.configure(text=f"{WEEKDAYS[self.selected_date.weekday()]}, {format_date(self.selected_date)} · {len(values)} buổi")
        for index, occurrence in enumerate(values):
            key = str(index)
            self._selected_occurrences[key] = occurrence
            status = STATUS_LABELS.get(occurrence.status, occurrence.status)
            tag = occurrence.status
            if occurrence.status == "pending":
                if occurrence.snoozed_until and occurrence.snoozed_until > now:
                    status = f"Hoãn đến {occurrence.snoozed_until:%H:%M}"
                    tag = "snoozed"
                elif occurrence.end <= now:
                    status, tag = "Hết giờ / chưa xác nhận", "overdue"
                elif occurrence.start <= now < occurrence.end:
                    status = "Đang trong giờ"
            self.tree.insert("", "end", iid=key, values=(occurrence.start.strftime("%H:%M"),
                             occurrence.end.strftime("%H:%M"), occurrence.title, status, occurrence.category), tags=(tag,))
        self._selection_changed()

    def _selection_changed(self):
        state = "normal" if self.tree.selection() else "disabled"
        for button in self.action_buttons:
            button.configure(state=state)

    def _selected(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self._selected_occurrences.get(selection[0])

    def _changed(self):
        self.refresh()
        if self.on_change:
            self.on_change()

    def _set_status(self, status):
        occurrence = self._selected()
        if occurrence is None:
            return
        try:
            self.store.set_occurrence_status(occurrence.schedule_id, occurrence.start.date(), status)
            self._changed()
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror("Không lưu được kết quả", str(exc), parent=self.winfo_toplevel())

    def _snooze(self):
        occurrence = self._selected()
        if occurrence is None:
            return
        now = datetime.now()
        until = now + timedelta(minutes=10)
        if occurrence.status != "pending":
            messagebox.showinfo("Không thể hoãn", "Chỉ hoãn nhắc cho buổi chưa xác nhận.", parent=self.winfo_toplevel())
            return
        if until >= occurrence.end:
            messagebox.showinfo("Không thể hoãn", "Buổi đã kết thúc hoặc không còn đủ 10 phút trước giờ kết thúc.", parent=self.winfo_toplevel())
            return
        try:
            self.store.snooze_occurrence(occurrence.schedule_id, occurrence.start.date(), until)
            self._changed()
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror("Không hoãn được nhắc", str(exc), parent=self.winfo_toplevel())

    def add_schedule(self):
        initial = Schedule(start_date=self.selected_date)
        ScheduleEditor(self.winfo_toplevel(), self.store, initial, on_saved=self._changed)

    def edit_selected(self):
        occurrence = self._selected()
        if occurrence is None:
            return
        schedule = self.store.get_schedule(occurrence.schedule_id)
        if schedule:
            ScheduleEditor(self.winfo_toplevel(), self.store, schedule, on_saved=self._changed)

    def manage_schedules(self):
        ScheduleManager(self.winfo_toplevel(), self.store, on_changed=self._changed)


class ScheduleEditor(tk.Toplevel):
    def __init__(self, parent, store, schedule: Schedule, on_saved=None):
        super().__init__(parent)
        self.store, self.schedule, self.on_saved = store, schedule, on_saved
        self.title("Sửa lịch gốc" if schedule.id is not None else "Thêm lịch")
        self.transient(parent)
        self.geometry(f"650x{min(820, max(500, self.winfo_screenheight() - 100))}")
        self.minsize(520, 440)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        note = "Chỉnh sửa áp dụng cho các buổi sắp tới; các buổi đã bắt đầu hoặc xác nhận vẫn được giữ." if schedule.id is not None else "Chọn cách lặp. Lịch tháng/năm lấy ngày bắt đầu làm mốc lặp."
        ttk.Label(self, text=note, wraplength=600, padding=12, foreground="#5a6c60").grid(row=0, column=0, sticky="ew")
        scroll = ScrollableForm(self)
        scroll.grid(row=1, column=0, sticky="nsew")
        form = scroll.content
        form.columnconfigure(1, weight=1)
        self.title_var = tk.StringVar(self, schedule.title)
        self.category_var = tk.StringVar(self, schedule.category)
        self.recurrence_var = tk.StringVar(self, RECURRENCE_LABELS[schedule.recurrence])
        self.start_var = tk.StringVar(self, schedule.start_time.strftime("%H:%M"))
        self.end_var = tk.StringVar(self, schedule.end_time.strftime("%H:%M"))
        self.minutes_var = tk.StringVar(self, str(schedule.reminder_minutes))
        self.days_var = tk.StringVar(self, ", ".join(map(str, schedule.reminder_days)))
        self.policy_var = tk.StringVar(self, "Ngày cuối tháng" if schedule.invalid_day_policy == "last_day" else "Bỏ qua lần thiếu ngày")
        self.enabled_var = tk.BooleanVar(self, schedule.enabled)
        self.weekday_vars = [tk.BooleanVar(self, i in schedule.weekdays) for i in range(7)]
        self.weekday_buttons = []
        row = 0

        def field(label, widget):
            nonlocal row
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="nw", padx=(0, 12), pady=6)
            widget.grid(row=row, column=1, sticky="ew", pady=5)
            row += 1

        self.title_entry = ttk.Entry(form, textvariable=self.title_var)
        field("Tên lịch *", self.title_entry)
        field("Phân loại", ttk.Entry(form, textvariable=self.category_var))
        recurrence_combo = ttk.Combobox(form, textvariable=self.recurrence_var, state="readonly", values=list(RECURRENCE_LABELS.values()))
        field("Cách lặp", recurrence_combo)
        recurrence_combo.bind("<<ComboboxSelected>>", lambda _e: self._recurrence_changed())
        self.start_date = DateEntry(form, schedule.start_date)
        field("Ngày bắt đầu *", self.start_date)
        time_frame = ttk.Frame(form)
        ttk.Entry(time_frame, textvariable=self.start_var, width=8).pack(side="left")
        ttk.Label(time_frame, text="  đến  ").pack(side="left")
        ttk.Entry(time_frame, textvariable=self.end_var, width=8).pack(side="left")
        ttk.Label(time_frame, text="  (hh:mm, cùng ngày)").pack(side="left")
        field("Giờ *", time_frame)
        weekdays = ttk.Frame(form)
        for i, label in enumerate(("T2", "T3", "T4", "T5", "T6", "T7", "CN")):
            button = ttk.Checkbutton(weekdays, text=label, variable=self.weekday_vars[i])
            button.grid(row=0, column=i, padx=(0, 6))
            self.weekday_buttons.append(button)
        field("Các thứ lặp", weekdays)
        self.until_date = DateEntry(form, schedule.until, allow_empty=True)
        field("Kết thúc lặp", self.until_date)
        self.policy_combo = ttk.Combobox(form, textvariable=self.policy_var, state="readonly",
                                         values=("Ngày cuối tháng", "Bỏ qua lần thiếu ngày"))
        field("Tháng thiếu ngày", self.policy_combo)
        self.rule_note = ttk.Label(form, text="", wraplength=410, foreground="#65736a")
        field("", self.rule_note)
        minutes = ttk.Spinbox(form, from_=0, to=120, textvariable=self.minutes_var, width=8)
        field("Nhắc trước (phút)", minutes)
        field("Nhắc trước (ngày)", ttk.Entry(form, textvariable=self.days_var))
        field("", ttk.Label(form, text="Ví dụ 7, 1 = trước 7 ngày và 1 ngày. Để trống nếu không dùng.\nMốc phút 0: chỉ nhắc lúc bắt đầu. Các mốc ngày dùng giờ bắt đầu.", wraplength=410, foreground="#65736a"))
        self.content = tk.Text(form, height=5, wrap="word", font=ui_font(self), relief="solid", borderwidth=1)
        self.content.insert("1.0", schedule.content)
        field("Nội dung / mục tiêu", self.content)
        field("", ttk.Checkbutton(form, text="Đang áp dụng lịch này", variable=self.enabled_var))
        footer = ttk.Frame(self, padding=12)
        footer.grid(row=2, column=0, sticky="ew")
        ttk.Button(footer, text="Hủy", command=self._close).pack(side="right", padx=(6, 0))
        ttk.Button(footer, text="Lưu lịch", command=self._save).pack(side="right")
        self.bind("<Control-Return>", lambda _e: self._save())
        self.bind("<Escape>", lambda _e: self._close())
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._recurrence_changed()
        self._initial_snapshot = self._snapshot()
        self.grab_set()
        self.title_entry.focus_set()

    def _snapshot(self):
        return (self.title_var.get(), self.category_var.get(), self.recurrence_var.get(),
                self.start_date.get(), self.start_var.get(), self.end_var.get(),
                tuple(v.get() for v in self.weekday_vars), self.until_date.get(), self.policy_var.get(),
                self.minutes_var.get(), self.days_var.get(), self.content.get("1.0", "end-1c"), self.enabled_var.get())

    def _close(self):
        if self._snapshot() != self._initial_snapshot:
            if not messagebox.askyesno("Chưa lưu thay đổi", "Bỏ các thay đổi chưa lưu và đóng biểu mẫu?", parent=self):
                return False
        self.destroy()
        return True

    def _recurrence_changed(self):
        recurrence = next(key for key, value in RECURRENCE_LABELS.items() if value == self.recurrence_var.get())
        for button in self.weekday_buttons:
            button.configure(state="normal" if recurrence == "weekly" else "disabled")
        self.until_date.set_enabled(recurrence != "once")
        self.policy_combo.configure(state="readonly" if recurrence in ("monthly", "yearly") else "disabled")
        notes = {
            "once": "Lịch chỉ diễn ra đúng ngày bắt đầu; các ô thứ lặp và kết thúc lặp không được dùng.",
            "weekly": "Chọn ít nhất một thứ. Để trống ngày kết thúc để lặp mỗi tuần.",
            "monthly": "Lặp vào ngày của ngày bắt đầu. Ví dụ ngày 31: dùng quy tắc tháng thiếu ngày đã chọn, vẫn giữ mốc 31 cho tháng tiếp theo.",
            "yearly": "Lặp vào cùng ngày/tháng của ngày bắt đầu. Ngày 29/2 trong năm không nhuận dùng quy tắc tháng thiếu ngày đã chọn.",
        }
        self.rule_note.configure(text=notes[recurrence])

    def _read_schedule(self):
        title = self.title_var.get().strip()
        if not title:
            raise ValueError("Vui lòng nhập tên lịch.")
        recurrence = next(key for key, value in RECURRENCE_LABELS.items() if value == self.recurrence_var.get())
        start_date = self.start_date.get_date()
        start_time, end_time = parse_time(self.start_var.get()), parse_time(self.end_var.get())
        if end_time <= start_time:
            raise ValueError("Giờ kết thúc phải sau giờ bắt đầu trong cùng ngày.")
        weekdays = [i for i, value in enumerate(self.weekday_vars) if value.get()] if recurrence == "weekly" else []
        if recurrence == "weekly" and not weekdays:
            raise ValueError("Lịch hằng tuần cần chọn ít nhất một thứ.")
        until = self.until_date.get_date() if recurrence != "once" else None
        if until and until < start_date:
            raise ValueError("Ngày kết thúc lặp không được trước ngày bắt đầu.")
        try:
            minutes = int(self.minutes_var.get())
        except ValueError as exc:
            raise ValueError("Số phút nhắc trước phải là số nguyên từ 0 đến 120.") from exc
        if not 0 <= minutes <= 120:
            raise ValueError("Số phút nhắc trước phải từ 0 đến 120.")
        return Schedule(id=self.schedule.id, title=title, category=self.category_var.get().strip(),
                        start_date=start_date, start_time=start_time, end_time=end_time,
                        recurrence=recurrence, weekdays=weekdays, until=until,
                        reminder_minutes=minutes, reminder_days=parse_reminder_days(self.days_var.get()),
                        invalid_day_policy="last_day" if self.policy_var.get() == "Ngày cuối tháng" else "skip",
                        content=self.content.get("1.0", "end-1c").strip(), enabled=self.enabled_var.get())

    def _confirm_overlap(self, schedule):
        if not schedule.enabled:
            return True
        start = max(schedule.start_date, date.today())
        end = min(start + timedelta(days=min(366, (date.max - start).days)), schedule.until or date.max)
        if end < start:
            return True
        proposed = expand_schedule(schedule, start, end)
        existing = self.store.occurrences(start, end)
        existing_by_day = defaultdict(list)
        for occurrence in existing:
            existing_by_day[occurrence.start.date()].append(occurrence)
        collisions = []
        for item in proposed:
            for other in existing_by_day.get(item.start.date(), []):
                if other.schedule_id == schedule.id or other.status == "skipped":
                    continue
                if item.start < other.end and other.start < item.end:
                    collisions.append((item, other))
                    break
            if len(collisions) == 3:
                break
        if not collisions:
            return True
        lines = [f"• {item.start:%d/%m/%Y %H:%M}: trùng với {other.title}" for item, other in collisions]
        return messagebox.askyesno("Lịch trùng giờ", "Phát hiện lịch trùng giờ trong tối đa 366 ngày tới:\n\n" + "\n".join(lines) + "\n\nAnh vẫn muốn lưu lịch này?", parent=self)

    def _save(self):
        try:
            schedule = self._read_schedule()
            if not self._confirm_overlap(schedule):
                return
            self.store.save_schedule(schedule)
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror("Chưa lưu được lịch", str(exc), parent=self)
            return
        callback = self.on_saved
        self.destroy()
        if callback:
            callback()


class ScheduleManager(tk.Toplevel):
    def __init__(self, parent, store, on_changed=None):
        super().__init__(parent)
        self.store, self.on_changed = store, on_changed
        self.title("Quản lý lịch gốc")
        self.transient(parent)
        self.geometry("850x460")
        self.minsize(640, 350)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text="Sửa lịch gốc áp dụng cho các buổi sắp tới. Tạm dừng không tạo buổi mới trong thời gian dừng; lịch sử vẫn được giữ.",
                  wraplength=800, padding=12).grid(row=0, column=0, sticky="ew")
        frame = ttk.Frame(self, padding=(12, 0))
        frame.grid(row=1, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(frame, columns=("title", "recurrence", "start", "status"), show="headings", selectmode="browse")
        for key, text, width in (("title", "Tên lịch", 330), ("recurrence", "Cách lặp", 110),
                                  ("start", "Ngày bắt đầu", 110), ("status", "Áp dụng", 120)):
            self.tree.heading(key, text=text)
            self.tree.column(key, width=width, minwidth=70, stretch=key == "title")
        self.tree.grid(row=0, column=0, sticky="nsew")
        bar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        bar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=bar.set)
        self.tree.bind("<Double-1>", lambda _e: self._edit())
        buttons = ttk.Frame(self, padding=12)
        buttons.grid(row=2, column=0, sticky="ew")
        ttk.Button(buttons, text="Thêm lịch", command=self._add).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Sửa lịch", command=self._edit).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Tạm dừng / Bật lại", command=self._toggle).pack(side="left")
        ttk.Button(buttons, text="Đóng", command=self._close).pack(side="right")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Escape>", lambda _event: self._close())
        self.refresh()

    def _close(self):
        if not close_schedule_editors(self):
            return False
        self.destroy()
        return True

    def refresh(self):
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for schedule in self.store.list_schedules(include_disabled=True):
            self.tree.insert("", "end", iid=str(schedule.id), values=(schedule.title,
                             RECURRENCE_LABELS.get(schedule.recurrence, schedule.recurrence),
                             format_date(schedule.start_date), "Đang áp dụng" if schedule.enabled else "Tạm dừng"))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0])

    def _changed(self):
        self.refresh()
        if self.on_changed:
            self.on_changed()

    def _selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Chọn lịch", "Vui lòng chọn một lịch trong danh sách.", parent=self)
            return None
        return self.store.get_schedule(int(selected[0]))

    def _add(self):
        ScheduleEditor(self, self.store, Schedule(), on_saved=self._changed)

    def _edit(self):
        schedule = self._selected()
        if schedule:
            ScheduleEditor(self, self.store, schedule, on_saved=self._changed)

    def _toggle(self):
        schedule = self._selected()
        if schedule is None:
            return
        try:
            self.store.set_schedule_enabled(schedule.id, not schedule.enabled)
            self._changed()
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror("Không cập nhật được lịch", str(exc), parent=self)
