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

    def test_task_text_and_actions_remain_visible_after_window_resize(self):
        task = self.store.create_task(
            "Hoàn thiện báo cáo định kỳ và rà soát toàn bộ hồ sơ liên quan đến kế hoạch triển khai của các phòng ban",
            datetime.now() + timedelta(days=3),
            "Quản lý vận hành và phối hợp công việc giữa các phòng ban trong đơn vị",
            "Chuẩn bị báo cáo ngắn và danh sách các việc cần trao đổi trong cuộc họp giao ban tuần tới.",
        )
        page = self.app.pages["active"]
        page.query_var.set("Hoàn thiện báo cáo định kỳ")
        page.refresh()
        for geometry in ("1366x768", "1120x720", "1366x768"):
            with self.subTest(geometry=geometry):
                self.root.geometry(geometry)
                self.root.update()
                card = page.cards_by_id[task.id]
                for label in card.wrapping_labels:
                    self.assertGreaterEqual(label.winfo_width(), label.winfo_reqwidth())
                    self.assertGreaterEqual(label.winfo_height(), label.winfo_reqheight())
                buttons = [grandchild for child in card.winfo_children()
                           for grandchild in child.winfo_children()
                           if grandchild.winfo_class() == "TButton"]
                self.assertEqual({button.cget("text") for button in buttons},
                                 {"Chi tiết", "Ghi chú", "Bắt đầu", "Hoàn thành"})
                for button in buttons:
                    self.assertGreaterEqual(button.winfo_rootx(), card.winfo_rootx())
                    self.assertLessEqual(button.winfo_rootx() + button.winfo_width(),
                                         card.winfo_rootx() + card.winfo_width())
                    self.assertGreaterEqual(button.winfo_width(), button.winfo_reqwidth())

    def test_compact_task_dialog_keeps_save_visible_while_form_scrolls(self):
        task = self.store.get_task(self.tasks[1].id)
        dialog = TaskDialog(self.app, task)
        try:
            dialog.geometry("640x560")
            self.root.update()

            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)

            buttons = [widget for widget in descendants(dialog)
                       if widget.winfo_class() == "TButton"
                       and widget.cget("text") in ("Tạm dừng", "Hủy việc", "Đóng", "Lưu công việc")]
            self.assertEqual(len(buttons), 4)
            for button in buttons:
                self.assertGreaterEqual(button.winfo_rootx(), dialog.winfo_rootx())
                self.assertLessEqual(button.winfo_rootx() + button.winfo_width(),
                                     dialog.winfo_rootx() + dialog.winfo_width())
                self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                                     dialog.winfo_rooty() + dialog.winfo_height())
                self.assertGreaterEqual(button.winfo_width(), button.winfo_reqwidth())
            save = next(button for button in buttons if button.cget("text") == "Lưu công việc")
            save_position = (save.winfo_rootx(), save.winfo_rooty())
            canvas = dialog.form.canvas
            self.assertGreater(dialog.form.content.winfo_height(), canvas.winfo_height())
            before = canvas.yview()
            canvas.yview_moveto(1)
            self.root.update()
            self.assertGreater(canvas.yview()[0], before[0])
            self.assertEqual((save.winfo_rootx(), save.winfo_rooty()), save_position)
            self.assertLessEqual(dialog.requirements_text.winfo_rooty() + dialog.requirements_text.winfo_height(),
                                 canvas.winfo_rooty() + canvas.winfo_height())
        finally:
            dialog.destroy()

    def test_real_calendar_navigation_from_main_window(self):
        self.app.show_page("calendar")
        calendar = self.app.pages["calendar"]
        for mode in ("week", "month", "year"):
            calendar.mode.set(mode)
            calendar.refresh()
            self.root.update()
        self.assertEqual(self.app.current_page, "calendar")
        self.assertGreater(calendar.task_cards.canvas.winfo_height(), 100)
        self.root.geometry("1120x720")
        self.root.update()
        self.assertGreater(calendar.task_cards.canvas.winfo_height(), 100)

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
