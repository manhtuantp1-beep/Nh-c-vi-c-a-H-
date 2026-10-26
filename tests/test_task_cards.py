"""Shared cards keep calendar/task-page actions bound to the displayed task."""
from datetime import datetime, timedelta
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from nhacviec.models import Task
from nhacviec.task_ui import TaskCards
from nhacviec.theme import configure_style


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class TaskCardsTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Display not available: {exc}")
        self.root.geometry("850x600")
        configure_style(self.root)
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(str(args[1]))
        self.app = SimpleNamespace(edit_task=Mock(), edit_task_notes=Mock(), transition_task=Mock())
        self.cards = TaskCards(self.root, self.app)
        self.cards.pack(fill="both", expand=True)

    def tearDown(self):
        if hasattr(self, "root"):
            self.root.destroy()
            self.assertEqual(self.errors, [])

    def task(self, task_id, **fields):
        defaults = dict(id=task_id, code=f"NV-{task_id}", title=f"Công việc {task_id}",
                        deadline=datetime.now() + timedelta(days=2))
        defaults.update(fields)
        return Task(**defaults)

    def button(self, task_id, text):
        return next(widget for widget in descendants(self.cards.cards_by_id[task_id])
                    if widget.winfo_class() == "TButton" and widget.cget("text") == text)

    def test_actions_keep_task_identity_and_closed_tasks_can_reopen(self):
        self.cards.set_tasks([self.task(11), self.task(12, status="in_progress"),
                              self.task(13, status="completed"), self.task(14, status="canceled")])
        self.root.update()
        self.button(11, "Chi tiết").invoke()
        self.button(12, "Ghi chú").invoke()
        self.button(11, "Bắt đầu").invoke()
        self.button(12, "Hoàn thành").invoke()
        self.button(13, "Mở lại").invoke()
        self.button(14, "Mở lại").invoke()
        self.app.edit_task.assert_called_once_with(11)
        self.app.edit_task_notes.assert_called_once_with(12)
        self.assertEqual([call.args for call in self.app.transition_task.call_args_list],
                         [(11, "in_progress"), (12, "completed"),
                          (13, "todo", "Đã mở lại"), (14, "todo", "Đã mở lại")])

    def test_note_preview_does_not_replace_content_or_mutate_full_notes(self):
        task = self.task(21, content="Nội dung bàn giao")
        task.notes = "Đã trao đổi với phòng kế toán.\n" + "Cần kiểm tra chứng từ. " * 12
        original_notes = task.notes
        self.cards.set_tasks([task])
        self.root.update()
        labels = [str(widget.cget("text")) for widget in descendants(self.cards.cards_by_id[21])
                  if widget.winfo_class() == "TLabel"]
        self.assertIn("Nội dung bàn giao", labels)
        note_preview = next(text for text in labels if text.startswith("Ghi chú: "))
        self.assertIn("Đã trao đổi với phòng kế toán.", note_preview)
        self.assertTrue(note_preview.endswith("…"))
        self.assertNotIn("\n", note_preview)
        self.assertEqual(task.notes, original_notes)

    def test_refresh_removes_old_cards_and_empty_action_remains_available(self):
        empty_action = Mock()
        self.cards.empty_action = ("Tạo việc vào ngày này", empty_action)
        self.cards.set_tasks([self.task(31)])
        self.root.update()
        self.cards.set_tasks([])
        self.root.update()
        self.assertEqual(self.cards.cards_by_id, {})
        self.assertEqual(self.cards.visible_tasks, [])
        action = next(widget for widget in descendants(self.cards)
                      if widget.winfo_class() == "TButton")
        action.invoke()
        empty_action.assert_called_once_with()
        self.cards.set_tasks([self.task(32)])
        self.root.update()
        self.assertEqual(set(self.cards.cards_by_id), {32})

    def test_long_notes_and_all_actions_fit_after_resize_and_destroy(self):
        task = self.task(41, title="Kiểm tra kế hoạch triển khai dự án của các phòng ban",
                         category="Quản lý và phối hợp công việc giữa các bộ phận")
        task.notes = "Cần đối chiếu các số liệu trước khi gửi báo cáo cho lãnh đạo. " * 5
        self.cards.set_tasks([task])
        for width in (850, 700, 850):
            with self.subTest(width=width):
                self.root.geometry(f"{width}x600")
                self.root.update()
                card = self.cards.cards_by_id[41]
                for label in card.wrapping_labels:
                    self.assertGreaterEqual(label.winfo_width(), label.winfo_reqwidth())
                    self.assertGreaterEqual(label.winfo_height(), label.winfo_reqheight())
                for text in ("Chi tiết", "Ghi chú", "Bắt đầu", "Hoàn thành"):
                    button = self.button(41, text)
                    self.assertGreaterEqual(button.winfo_rootx(), card.winfo_rootx())
                    self.assertLessEqual(button.winfo_rootx() + button.winfo_width(),
                                         card.winfo_rootx() + card.winfo_width())
        self.cards._queue_wraps()
        self.cards.destroy()
        self.root.update()


if __name__ == "__main__":
    unittest.main()
