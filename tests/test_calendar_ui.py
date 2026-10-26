"""Calendar parsing and real Tk-to-SQLite integration tests.

The Tk cases require a display (use Xvfb on Linux); parser cases always run.
"""
from datetime import date, datetime, time, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from nhacviec.calendar_ui import CalendarView, ScheduleEditor, ScheduleManager, close_schedule_editors, parse_reminder_days
from nhacviec.models import Schedule
from nhacviec.storage import Storage
from nhacviec.theme import configure_style
from nhacviec.widgets import DateEntry, parse_date, parse_time


class CalendarParsingTests(unittest.TestCase):
    def test_parse_valid_dates_and_times(self):
        self.assertEqual(parse_date("29/02/2024"), date(2024, 2, 29))
        self.assertIsNone(parse_date("", allow_empty=True))
        self.assertEqual(parse_time("23:59"), time(23, 59))

    def test_invalid_dates_and_times(self):
        for value in ("29/02/2025", "31/04/2026", "", "2026-10-21"):
            with self.assertRaises(ValueError):
                parse_date(value)
        for value in ("24:00", "09:61", "", "morning"):
            with self.assertRaises(ValueError):
                parse_time(value)

    def test_reminder_days_validation(self):
        self.assertEqual(parse_reminder_days("1, 7; 30, 7"), [30, 7, 1])
        self.assertEqual(parse_reminder_days(" "), [])
        for value in ("0", "366", "-1", "1.5", ",", "tomorrow"):
            with self.assertRaises(ValueError):
                parse_reminder_days(value)


class CalendarTkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.geometry("1250x950")
        except tk.TclError as exc:
            raise unittest.SkipTest(f"Tk display unavailable: {exc}")

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.store = Storage(Path(self.temp.name) / "tasks.db")
        self.view = CalendarView(self.root, self.store)
        self.view.pack(fill="both", expand=True)
        self.root.update()

    def tearDown(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.store.close()
        self.temp.cleanup()
        self.root.update()

    def make_schedule(self, **fields):
        defaults = dict(title="Báo cáo tháng", start_date=date(2026, 1, 31),
                        start_time=time(9), end_time=time(10), recurrence="monthly")
        defaults.update(fields)
        return self.store.save_schedule(Schedule(**defaults))

    def test_week_month_year_views_and_day_selection(self):
        self.make_schedule()
        self.view.anchor = self.view.selected_date = date(2026, 2, 28)
        for mode in ("week", "month", "year"):
            self.view.mode.set(mode)
            self.view.refresh()
            self.root.update()
            self.assertEqual(len(self.view.tree.get_children()), 1)
            self.assertTrue(self.view.calendar_frame.winfo_children())
        self.view._open_month(3)
        self.assertEqual(self.view.mode.get(), "month")
        self.view.show_day(date(2026, 3, 31))
        self.assertEqual(len(self.view.tree.get_children()), 1)

    def test_deadline_date_groups_every_task_status_without_copying(self):
        day = date(2026, 10, 27)
        tasks = []
        for index, status in enumerate(("todo", "in_progress", "completed", "canceled")):
            task = self.store.create_task(f"Việc {status}", datetime.combine(day, time(index, 30)))
            if status != "todo":
                task = self.store.set_task_status(task.id, status)
            tasks.append(task)
        self.store.create_task("Ngày khác", datetime(2026, 10, 28, 0, 0))
        self.store.create_task("Năm khác", datetime(2025, 10, 27, 23, 59))
        self.view.anchor = self.view.selected_date = day
        for mode in ("week", "month", "year"):
            self.view.mode.set(mode)
            self.view.refresh()
            self.root.update()
            shown = self.view.task_cards.visible_tasks
            self.assertEqual([task.id for task in shown], [task.id for task in tasks])
            self.assertEqual({task.status for task in shown}, {"todo", "in_progress", "completed", "canceled"})
            self.assertEqual(self.view.day_notebook.tab(self.view.tasks_tab, "text"), "Công việc (4)")
            self.assertEqual(self.view.day_count_label.cget("text"), "4 công việc · 0 lịch hẹn")
        self.assertEqual(len(self.store.list_tasks()), 6)

    def test_task_counts_and_recurring_appointments_remain_distinct(self):
        day = date(2026, 10, 27)
        for hour in (0, 23):
            self.store.create_task(f"Deadline {hour}", datetime.combine(day, time(hour, 59)))
        self.make_schedule(start_date=day, recurrence="once")
        self.view.anchor = self.view.selected_date = day
        self.view.mode.set("month")
        self.view.refresh()
        self.root.update()
        self.assertEqual(len(self.view._tasks_by_day[day]), 2)
        self.assertEqual(len(self.view._by_day[day]), 1)
        self.assertEqual(len(self.view.tree.get_children()), 1)
        self.assertEqual(self.view.day_count_label.cget("text"), "2 công việc · 1 lịch hẹn")
        self.assertEqual(self.view.summary.cget("text"), "2 công việc theo ngày deadline · 1 lịch hẹn · 1 giờ lịch hẹn")
        month_buttons = [widget for widget in self.view.calendar_frame.winfo_children()
                         if isinstance(widget, ttk.Button)]
        self.assertIn("27 · 2 việc\n1 lịch hẹn", [widget.cget("text") for widget in month_buttons])
        self.view.mode.set("year")
        self.view.refresh()
        self.assertIn("Tháng 10 · 2 việc\n1 lịch hẹn", [widget.cget("text") for widget in self.view.calendar_frame.winfo_children()])

    def test_clicking_deadline_day_opens_shared_task_cards(self):
        day = date(2026, 10, 27)
        task = self.store.create_task("Cần xem từ lịch", datetime.combine(day, time(17)))
        self.view.anchor = self.view.selected_date = date(2026, 10, 1)
        self.view.mode.set("month")
        self.view.refresh()
        self.view.day_notebook.select(self.view.schedules_tab)
        button = next(widget for widget in self.view.calendar_frame.winfo_children()
                      if isinstance(widget, ttk.Button) and widget.cget("text") == "27 · 1 việc")
        button.invoke()
        self.root.update()
        self.assertEqual(self.view.selected_date, day)
        self.assertEqual(self.view.day_notebook.select(), str(self.view.tasks_tab))
        self.assertEqual([value.id for value in self.view.task_cards.visible_tasks], [task.id])
        self.assertIn(task.id, self.view.task_cards.cards_by_id)

    def test_editing_deadline_moves_task_and_counts_after_refresh(self):
        first, second = date(2026, 10, 27), date(2026, 10, 28)
        task = self.store.create_task("Chuyển deadline", datetime.combine(first, time(17)))
        self.view.anchor = self.view.selected_date = first
        self.view.mode.set("month")
        self.view.refresh()
        self.store.update_task(task.id, deadline=datetime.combine(second, time(9)))
        self.view.refresh()
        self.assertEqual(self.view.task_cards.visible_tasks, [])
        self.assertEqual(len(self.view._tasks_by_day.get(first, [])), 0)
        self.assertEqual([value.id for value in self.view._tasks_by_day[second]], [task.id])
        self.view.show_day(second)
        self.assertEqual([value.id for value in self.view.task_cards.visible_tasks], [task.id])
        self.assertEqual(len(self.store.list_tasks()), 1)

    def test_calendar_task_actions_update_the_existing_task(self):
        day = date(2026, 10, 27)
        task = self.store.create_task("Thao tác từ lịch", datetime.combine(day, time(17)))
        self.view.anchor = self.view.selected_date = day
        self.view.refresh()

        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)

        card = self.view.task_cards.cards_by_id[task.id]
        next(button for button in descendants(card)
             if isinstance(button, ttk.Button) and button.cget("text") == "Bắt đầu").invoke()
        self.assertEqual(self.store.get_task(task.id).status, "in_progress")
        card = self.view.task_cards.cards_by_id[task.id]
        next(button for button in descendants(card)
             if isinstance(button, ttk.Button) and button.cget("text") == "Hoàn thành").invoke()
        self.assertEqual(self.store.get_task(task.id).status, "completed")
        self.assertEqual(self.view.day_notebook.tab(self.view.tasks_tab, "text"), "Công việc (1)")
        self.assertEqual(len(self.store.list_tasks()), 1)

    def test_populated_six_week_month_keeps_day_cards_inside_page(self):
        # This is the actual content area left by the 1120 × 720 app shell.
        self.root.tk.call("tk", "scaling", 96 / 72)
        configure_style(self.root)
        self.view.destroy()
        self.view = CalendarView(self.root, self.store)
        self.view.pack(fill="both", expand=True)
        self.root.geometry("880x690")
        for day in range(1, 32):
            self.store.create_task("Việc trong tháng", datetime(2026, 8, day, 17))
            self.make_schedule(start_date=date(2026, 8, day), recurrence="once")
        self.view.anchor = self.view.selected_date = date(2026, 8, 1)
        self.view.mode.set("month")
        self.view.refresh()
        self.root.update()
        canvas = self.view.task_cards.canvas
        self.assertGreater(canvas.winfo_height(), 100)
        self.assertLessEqual(canvas.winfo_rooty() + canvas.winfo_height(),
                             self.view.winfo_rooty() + self.view.winfo_height())
        for button in self.view.calendar_frame.winfo_children():
            if isinstance(button, ttk.Button):
                self.assertGreaterEqual(button.winfo_width(), button.winfo_reqwidth())
        self.root.geometry("1250x950")

    def test_new_task_from_empty_day_uses_selected_deadline(self):
        day = date(2026, 11, 27)
        self.view.show_day(day)
        self.view.add_task()
        editor = next(child for child in self.root.winfo_children()
                      if isinstance(child, tk.Toplevel))
        self.assertEqual(editor.date_entry.get_date(), day)
        self.assertEqual(editor.snapshot(), editor._initial)
        editor.destroy()

    def test_large_font_short_calendar_scrolls_without_hiding_day_tasks(self):
        # Exercise larger text in the same physical window. This is a font
        # metrics stress case, not a claim about changing the OS monitor DPI.
        self.root.tk.call("tk", "scaling", 120 / 72)
        configure_style(self.root)
        self.view.destroy()
        self.view = CalendarView(self.root, self.store)
        self.view.pack(fill="both", expand=True)
        self.root.geometry("880x650")
        try:
            for day in range(1, 32):
                self.store.create_task("Việc trong tháng", datetime(2026, 8, day, 17))
                self.make_schedule(start_date=date(2026, 8, day), recurrence="once")
            self.view.anchor = self.view.selected_date = date(2026, 8, 1)
            self.view.mode.set("month")
            self.view.refresh()
            self.root.update()
            cards_canvas = self.view.task_cards.canvas
            self.assertGreater(cards_canvas.winfo_height(), 100)
            self.assertLessEqual(cards_canvas.winfo_rooty() + cards_canvas.winfo_height(),
                                 self.view.winfo_rooty() + self.view.winfo_height())
            self.assertTrue(self.view._calendar_scroll)
            self.assertTrue(self.view.calendar_viewport.scrollbar.winfo_ismapped())
            calendar_canvas = self.view.calendar_viewport.canvas
            calendar_canvas.yview_moveto(1)
            self.root.update()
            self.assertGreater(calendar_canvas.yview()[0], 0)
            self.view.show_day(date(2026, 8, 1))
            self.root.update()
            selected = self.view._selected_day_button
            self.assertGreaterEqual(selected.winfo_rooty(), calendar_canvas.winfo_rooty())
            self.assertLessEqual(selected.winfo_rooty() + selected.winfo_height(),
                                 calendar_canvas.winfo_rooty() + calendar_canvas.winfo_height())
            self.view.show_day(date(2026, 8, 31))
            self.root.update()
            selected = self.view._selected_day_button
            self.assertGreaterEqual(selected.winfo_rooty(), calendar_canvas.winfo_rooty())
            self.assertLessEqual(selected.winfo_rooty() + selected.winfo_height(),
                                 calendar_canvas.winfo_rooty() + calendar_canvas.winfo_height())
            self.assertEqual(len(self.view.task_cards.visible_tasks), 1)
            for button in self.view.calendar_frame.winfo_children():
                if isinstance(button, ttk.Button):
                    self.assertGreaterEqual(button.winfo_width(), button.winfo_reqwidth())
        finally:
            self.root.tk.call("tk", "scaling", 96 / 72)
            configure_style(self.root)
            self.root.geometry("1250x950")

    def test_switching_days_starts_at_top_of_task_list(self):
        first, second = date(2026, 10, 27), date(2026, 10, 28)
        for day in (first, second):
            for index in range(12):
                self.store.create_task(f"Việc {index}", datetime.combine(day, time(17)))
        self.view.anchor = self.view.selected_date = first
        self.view.mode.set("month")
        self.view.refresh()
        self.root.update()
        canvas = self.view.task_cards.canvas
        canvas.yview_moveto(1)
        self.root.update()
        self.assertGreater(canvas.yview()[0], 0)
        self.view.refresh()
        self.root.update()
        self.assertGreater(canvas.yview()[0], 0)
        self.view.show_day(second)
        self.root.update()
        self.assertEqual(canvas.yview()[0], 0)

    def test_occurrence_completion_reopen_and_pause_preserve_history(self):
        schedule = self.make_schedule()
        self.view.anchor = self.view.selected_date = date(2026, 2, 28)
        self.view.mode.set("month")
        self.view.refresh()
        self.view.tree.selection_set(self.view.tree.get_children()[0])
        self.view._set_status("completed")
        self.assertEqual(self.store.occurrences(date(2026, 2, 28), date(2026, 2, 28))[0].status, "completed")
        self.view.tree.selection_set(self.view.tree.get_children()[0])
        self.view._set_status("pending")
        self.assertEqual(self.store.occurrences(date(2026, 2, 28), date(2026, 2, 28))[0].status, "pending")
        self.view.tree.selection_set(self.view.tree.get_children()[0])
        self.view._set_status("skipped")
        self.store.set_schedule_enabled(schedule.id, False)
        self.view.refresh()
        self.assertEqual(self.store.occurrences(date(2026, 2, 28), date(2026, 2, 28))[0].status, "skipped")

    def test_editor_saves_yearly_rule_and_rejects_invalid_time(self):
        editor = ScheduleEditor(self.root, self.store, Schedule())
        editor.title_var.set("Gia hạn hợp đồng")
        editor.recurrence_var.set("Hằng năm")
        editor.start_date.set_date(date(2028, 2, 29))
        editor.start_var.set("10:00")
        editor.end_var.set("11:00")
        editor.days_var.set("30,7,1")
        with patch.object(editor, "_confirm_overlap", return_value=True):
            editor._save()
        saved = self.store.list_schedules()[0]
        self.assertEqual(saved.recurrence, "yearly")
        self.assertEqual(saved.reminder_days, [30, 7, 1])
        self.assertEqual(saved.start_date, date(2028, 2, 29))
        editor = ScheduleEditor(self.root, self.store, saved)
        editor.end_var.set("09:59")
        with patch("nhacviec.calendar_ui.messagebox.showerror") as error:
            editor._save()
            error.assert_called_once()
        self.assertEqual(self.store.get_schedule(saved.id).end_time, time(11))

    def test_editor_warns_before_overlapping_schedule(self):
        day = date.today() + timedelta(days=1)
        self.make_schedule(title="Họp", start_date=day, recurrence="once")
        editor = ScheduleEditor(self.root, self.store,
                                Schedule(title="Việc khác", start_date=day,
                                         start_time=time(9, 30), end_time=time(10, 30)))
        with patch("nhacviec.calendar_ui.messagebox.askyesno", return_value=False) as prompt:
            editor._save()
            prompt.assert_called_once()
        self.assertEqual(len(self.store.list_schedules()), 1)

    def test_manager_toggle_and_date_picker(self):
        schedule = self.make_schedule()
        manager = ScheduleManager(self.root, self.store)
        manager.tree.selection_set(str(schedule.id))
        manager._toggle()
        self.assertFalse(self.store.get_schedule(schedule.id).enabled)
        manager._toggle()
        self.assertTrue(self.store.get_schedule(schedule.id).enabled)
        picker = DateEntry(self.root, value=date(2024, 2, 29), allow_empty=True)
        self.assertEqual(picker.get_date(), date(2024, 2, 29))
        picker.set_date(None)
        self.assertIsNone(picker.get_date())
        picker._open_calendar()
        self.root.update()
        self.assertTrue(picker._popup.winfo_exists())

    def test_manager_close_protects_dirty_child_editor_on_cancel(self):
        manager = ScheduleManager(self.root, self.store)
        editor = ScheduleEditor(manager, self.store, Schedule())
        editor.title_var.set("Nội dung chưa lưu")
        with patch("nhacviec.calendar_ui.messagebox.askyesno", return_value=False) as prompt:
            self.assertFalse(manager._close())
            prompt.assert_called_once()
        self.assertTrue(manager.winfo_exists())
        self.assertTrue(editor.winfo_exists())
        self.assertEqual(editor.title_var.get(), "Nội dung chưa lưu")
        self.assertEqual(self.store.list_schedules(), [])
        with patch("nhacviec.calendar_ui.messagebox.askyesno", return_value=True):
            self.assertTrue(manager._close())
        self.assertFalse(manager.winfo_exists())
        self.assertFalse(editor.winfo_exists())

    def test_recursive_editor_guard_handles_nested_manager(self):
        outer = ScheduleManager(self.root, self.store)
        inner = ScheduleManager(outer, self.store)
        editor = ScheduleEditor(inner, self.store, Schedule())
        editor.content.insert("1.0", "Không được mất khi đóng cửa sổ cha")
        with patch("nhacviec.calendar_ui.messagebox.askyesno", return_value=False):
            self.assertFalse(close_schedule_editors(self.root))
            self.assertFalse(outer._close())
        self.assertTrue(outer.winfo_exists())
        self.assertTrue(inner.winfo_exists())
        self.assertTrue(editor.winfo_exists())
        with patch("nhacviec.calendar_ui.messagebox.askyesno", return_value=True):
            self.assertTrue(outer._close())
        self.assertFalse(editor.winfo_exists())


if __name__ == "__main__":
    unittest.main()
