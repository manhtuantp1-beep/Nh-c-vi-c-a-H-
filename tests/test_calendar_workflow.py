"""Exercise the requested deadline-to-calendar and quick-notes user journey."""
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from nhacviec.app import NhacViecApp
from nhacviec.dialogs import NotesDialog
from nhacviec.storage import Storage


class CalendarWorkflowTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Display unavailable: {exc}")
        self.directory = TemporaryDirectory()
        self.store = Storage(Path(self.directory.name) / "tasks.db")
        self.app = NhacViecApp(self.root, self.store, Path(self.directory.name),
                              integrations=False, enable_timers=False)

    def tearDown(self):
        if hasattr(self, "app"):
            for child in self.root.winfo_children():
                if isinstance(child, tk.Toplevel):
                    child.destroy()
            self.app.exit()
            self.store.close()
            self.directory.cleanup()

    def test_selected_day_creation_notes_and_deadline_move_use_same_record(self):
        self.app.show_page("calendar")
        view = self.app.pages["calendar"]
        view.mode.set("month")
        view.show_day(date(2030, 1, 8))
        dialog = self.app.new_task()
        self.assertEqual(dialog.date_entry.get_date(), date(2030, 1, 8))
        dialog.title_var.set("Bàn giao hồ sơ")
        dialog.notes_text.insert("1.0", "Chờ xác nhận từ đối tác.")
        dialog.save()
        self.root.update()
        task = self.store.list_tasks()[0]
        self.assertEqual([t.id for t in view.task_cards.visible_tasks], [task.id])
        self.assertEqual(view.day_notebook.tab(view.tasks_tab, "text"), "Công việc (1)")
        card = view.task_cards.cards_by_id[task.id]
        buttons = [grandchild for child in card.winfo_children()
                   for grandchild in child.winfo_children() if isinstance(grandchild, ttk.Button)]
        next(button for button in buttons if button.cget("text") == "Ghi chú").invoke()
        notes = next(child for child in self.root.winfo_children() if isinstance(child, NotesDialog))
        notes.notes_text.insert("end", "\nĐã nhận bản nháp.")
        notes.save()
        self.root.update()
        self.assertEqual(view.selected_date, date(2030, 1, 8))
        self.assertIn("Đã nhận bản nháp.", view.task_cards.visible_tasks[0].notes)
        details = self.app.edit_task(task.id)
        details.date_entry.set_date(date(2030, 1, 9))
        details.save()
        self.root.update()
        self.assertEqual(view.task_cards.visible_tasks, [])
        view.show_day(date(2030, 1, 9))
        self.root.update()
        self.assertEqual([t.id for t in view.task_cards.visible_tasks], [task.id])
        self.assertEqual(len(self.store.list_tasks()), 1)
        self.assertIn("Đã nhận bản nháp.", view.task_cards.visible_tasks[0].notes)

    def test_global_exit_respects_dirty_quick_notes(self):
        task = self.store.create_task("Cần chú ý", datetime(2030, 1, 8), notes="Đã lưu")
        dialog = self.app.edit_task_notes(task.id)
        dialog.notes_text.insert("end", "\nChưa lưu")
        with patch("nhacviec.dialogs.messagebox.askyesno", return_value=False):
            self.app.exit()
        self.assertFalse(self.app._closing)
        self.assertTrue(dialog.winfo_exists())
        self.assertEqual(self.store.get_task(task.id).notes, "Đã lưu")


if __name__ == "__main__":
    unittest.main()
