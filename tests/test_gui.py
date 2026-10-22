"""Integration tests use real Tk widgets and a temporary SQLite database."""
from datetime import date, datetime, timedelta
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from nhacviec.app import NhacViecApp, ALL_FILTER, TODO_FILTER, TaskDialog
from nhacviec.storage import Storage


class DesktopTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Display not available: {exc}")
        self.directory = tempfile.TemporaryDirectory()
        self.store = Storage(Path(self.directory.name) / "data" / "tasks.db")
        self.app = NhacViecApp(self.root, self.store, Path(self.directory.name), integrations=False, enable_timers=False)
        self.callback_errors = []
        self.root.report_callback_exception = lambda *_args: self.callback_errors.append(str(_args[1]))
        self.tasks = []
        for title, status, reason in [("Việc mới", "todo", ""), ("Đang làm", "in_progress", ""), ("Đã tạm dừng", "todo", "Tạm dừng"), ("Đã mở lại", "todo", "Đã mở lại"), ("Đã xong", "completed", ""), ("Đã hủy", "canceled", "")]:
            task = self.store.create_task(title, datetime.now() + timedelta(days=2))
            self.store.set_task_status(task.id, status, reason)
            self.tasks.append(task)
        self.app.refresh_current()
        self.root.update()

    def tearDown(self):
        if hasattr(self, "app"):
            self.app.exit()
            self.store.close()
            self.directory.cleanup()
            self.assertEqual(self.callback_errors, [])

    def test_two_filters_preserve_pending_and_exclude_closed(self):
        page = self.app.pages["active"]
        self.assertEqual(len(page.visible_tasks), 4)
        page.filter_combo.current(1)
        page.filter_combo.event_generate("<<ComboboxSelected>>")
        self.root.update()
        self.assertEqual({t.title for t in page.visible_tasks}, {"Việc mới", "Đã tạm dừng", "Đã mở lại"})
        self.assertIn("tạm dừng", page.hint.cget("text"))

    def test_start_button_updates_filter_and_database(self):
        page = self.app.pages["active"]
        page.filter_var.set(TODO_FILTER)
        page.refresh()
        task_id = self.tasks[0].id
        card = page.cards_by_id[task_id]
        buttons = [grandchild for child in card.winfo_children() for grandchild in child.winfo_children() if grandchild.winfo_class() == "TButton"]
        next(b for b in buttons if b.cget("text") == "Bắt đầu").invoke()
        self.root.update()
        self.assertEqual(self.store.get_task(task_id).status, "in_progress")
        self.assertNotIn(task_id, {t.id for t in page.visible_tasks})
        self.assertEqual(page.filter_var.get(), TODO_FILTER)
        page.filter_var.set(ALL_FILTER)
        page.refresh()
        self.assertEqual(len(page.visible_tasks), 4)

    def test_search_sort_and_tab_filter_state(self):
        page = self.app.pages["active"]
        page.query_var.set("mới")
        page.apply_filters()
        self.assertEqual([t.title for t in page.visible_tasks], ["Việc mới"])
        self.app.show_page("completed")
        self.assertEqual(len(self.app.pages["completed"].visible_tasks), 1)
        self.app.show_page("active")
        self.assertEqual(page.query_var.get(), "mới")
        page.clear_filters()
        self.assertEqual(len(page.visible_tasks), 4)

    def test_task_form_saves_full_unicode_text(self):
        dialog = TaskDialog(self.app)
        self.root.update()
        dialog.title_var.set("Công việc mới có dấu")
        dialog.date_entry.set_date(date(2027, 2, 3))
        dialog.time_var.set("14:35")
        dialog.content_text.insert("1.0", "Nội dung đầy đủ\nDòng thứ hai")
        dialog.requirements_text.insert("1.0", "Bàn giao bản cuối")
        dialog.save()
        result = self.store.list_tasks(query="Công việc mới có dấu")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].deadline, datetime(2027, 2, 3, 14, 35))
        self.assertEqual(result[0].content, "Nội dung đầy đủ\nDòng thứ hai")

    def test_real_calendar_navigation_from_main_window(self):
        self.app.show_page("calendar")
        calendar = self.app.pages["calendar"]
        for mode in ("week", "month", "year"):
            calendar.mode.set(mode)
            calendar.refresh()
            self.root.update()
        self.assertEqual(self.app.current_page, "calendar")
        self.assertGreater(calendar.tree.winfo_height(), 100)

    def test_pending_timer_handles_do_not_accumulate(self):
        called = []
        for _ in range(12):
            self.app._schedule(0, lambda: called.append(True))
        self.root.update()
        self.assertEqual(len(called), 12)
        self.assertEqual(len(self.app._after_ids), 0)

    def test_global_exit_preserves_dirty_nested_schedule_when_discard_declined(self):
        from nhacviec.calendar_ui import ScheduleEditor, ScheduleManager
        from nhacviec.models import Schedule
        manager = ScheduleManager(self.root, self.store)
        editor = ScheduleEditor(manager, self.store, Schedule(title="Lịch đang sửa"))
        editor.title_var.set("Nội dung chưa lưu")
        with patch("nhacviec.calendar_ui.messagebox.askyesno", return_value=False):
            self.app.exit()
        self.assertFalse(self.app._closing)
        self.assertTrue(editor.winfo_exists())
        editor.destroy()
        manager.destroy()


if __name__ == "__main__":
    unittest.main()
