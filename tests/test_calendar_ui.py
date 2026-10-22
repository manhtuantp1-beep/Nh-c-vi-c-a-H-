"""Calendar parsing and real Tk-to-SQLite integration tests.

The Tk cases require a display (use Xvfb on Linux); parser cases always run.
"""
from datetime import date, datetime, time, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
import unittest
from unittest.mock import patch

from nhacviec.calendar_ui import CalendarView, ScheduleEditor, ScheduleManager, close_schedule_editors, parse_reminder_days
from nhacviec.models import Schedule
from nhacviec.storage import Storage
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
