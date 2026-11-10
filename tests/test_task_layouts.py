"""Real Tk checks for task identity and responsive layout, using synthetic data."""
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from nhacviec.models import Task
from nhacviec.task_layouts import TaskCards
from nhacviec.theme import configure_style


class TaskLayoutTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Display unavailable: {exc}")
        self.root.geometry("1000x700")
        self.root.maxsize(4000, 2300)
        self.root._layout_scale = 1.0
        self.root.tk.call("tk", "scaling", 96 / 72)
        configure_style(self.root)
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(str(args[1]))
        self.app = SimpleNamespace(edit_task=Mock(), edit_task_notes=Mock(), transition_task=Mock())
        self.cards = TaskCards(self.root, self.app, layout="grid")
        self.cards.pack(fill="both", expand=True)

    def tearDown(self):
        if hasattr(self, "root"):
            self.root.destroy()
            self.assertEqual(self.errors, [])

    def task(self, task_id, **fields):
        defaults = dict(id=task_id, code=f"09:30-10112026-{task_id}", title=f"Công việc {task_id}",
                        deadline=datetime.now() + timedelta(days=2),
                        content="Nội dung cần bàn giao.", notes="Đã kiểm tra phần đầu.\nCần xác nhận số liệu.")
        defaults.update(fields)
        return Task(**defaults)

    def settle(self):
        for _ in range(3):
            self.root.update_idletasks()
            self.root.update()

    def assert_card_fits(self, card):
        for label in card.wrapping_labels:
            self.assertGreaterEqual(label.winfo_width(), label.winfo_reqwidth(), label.cget("text"))
            self.assertGreaterEqual(label.winfo_height(), label.winfo_reqheight(), label.cget("text"))
        for button in card.action_buttons:
            self.assertGreaterEqual(button.winfo_width(), button.winfo_reqwidth(), button.cget("text"))
            self.assertGreaterEqual(button.winfo_rootx(), card.winfo_rootx())
            self.assertLessEqual(button.winfo_rootx() + button.winfo_width(),
                                 card.winfo_rootx() + card.winfo_width(), button.cget("text"))

    def test_grid_reflows_without_losing_order_or_note_contents(self):
        tasks = [self.task(i) for i in range(1, 6)]
        self.cards.set_tasks(tasks)
        self.settle()
        self.assertEqual(self.cards.columns, 2)
        self.assertEqual([task.id for task in self.cards.visible_tasks], list(range(1, 6)))
        first_card = self.cards.cards_by_id[1]
        self.assertEqual(first_card.grid_info()["column"], 0)
        self.assertEqual(self.cards.cards_by_id[2].grid_info()["column"], 1)
        self.root.geometry("650x700")
        self.settle()
        self.assertEqual(self.cards.columns, 1)
        self.assertIs(first_card, self.cards.cards_by_id[1])
        self.root.geometry("1600x700")
        self.settle()
        self.assertEqual(self.cards.columns, 3)
        self.assertEqual(tasks[0].notes, "Đã kiểm tra phần đầu.\nCần xác nhận số liệu.")

    def test_each_layout_keeps_actions_bound_to_the_same_task(self):
        tasks = [self.task(11), self.task(12, status="in_progress"), self.task(13, status="completed")]
        self.cards.set_tasks(tasks)
        for layout in ("grid", "list", "wide"):
            with self.subTest(layout=layout):
                self.cards.set_layout(layout)
                self.settle()
                self.assertEqual([task.id for task in self.cards.visible_tasks], [11, 12, 13])
                for task_id, caption in ((11, "Chi tiết"), (12, "Ghi chú"), (11, "Bắt đầu"),
                                         (12, "Hoàn thành"), (13, "Mở lại")):
                    card = self.cards.cards_by_id[task_id]
                    next(button for button in card.action_buttons if button.cget("text") == caption).invoke()
        self.assertEqual([call.args for call in self.app.edit_task.call_args_list], [(11,)] * 3)
        self.assertEqual([call.args for call in self.app.edit_task_notes.call_args_list], [(12,)] * 3)
        self.assertEqual([call.args for call in self.app.transition_task.call_args_list],
                         [(11, "in_progress"), (12, "completed"), (13, "todo", "Đã mở lại")] * 3)

    def test_compact_list_uses_less_height_and_can_show_notes(self):
        task = self.task(21, title="Đối chiếu báo cáo và xác nhận số liệu trước hạn bàn giao")
        self.cards.set_tasks([task])
        self.cards.set_layout("wide")
        self.settle()
        wide_height = self.cards.cards_by_id[21].winfo_height()
        self.cards.set_layout("list")
        self.settle()
        compact = self.cards.cards_by_id[21]
        self.assertLess(compact.winfo_height(), wide_height)
        self.assertTrue(compact.note_label.cget("text").startswith("Ghi chú: "))
        self.assertEqual(compact.title_label.cget("text"), task.title)

    def test_grid_list_wide_keep_large_text_and_actions_inside_cards(self):
        title = "Đánh giá kết quả thực hiện và phối hợp xử lý công việc giữa các phòng ban trước khi trình lãnh đạo phê duyệt"
        tasks = [self.task(i, title=title, category="Quản lý vận hành và phối hợp các bộ phận",
                           notes="Đã đối chiếu phần đầu; cần xác nhận lại các số liệu trước thời hạn bàn giao. " * 5)
                 for i in range(31, 35)]
        self.cards.set_tasks(tasks)
        for factor in (1.0, 1.25, 1.5, 2.0):
            self.root._layout_scale = factor
            self.root.tk.call("tk", "scaling", factor * 96 / 72)
            configure_style(self.root)
            for logical_width in (780, 1010):
                self.root.geometry(f"{round(logical_width * factor)}x{round(650 * factor)}")
                for layout in ("grid", "list", "wide"):
                    with self.subTest(factor=factor, width=logical_width, layout=layout):
                        self.cards.set_layout(layout)
                        self.settle()
                        for card in self.cards.cards_by_id.values():
                            self.assert_card_fits(card)
                            self.assertGreaterEqual(card.winfo_rootx(), self.cards.canvas.winfo_rootx())
                            self.assertLessEqual(card.winfo_rootx() + card.winfo_width(),
                                                 self.cards.canvas.winfo_rootx() + self.cards.canvas.winfo_width())
        self.assertEqual(tasks[0].title, title)
        self.assertNotIn("…", tasks[0].notes)

    def test_empty_state_and_pending_reflow_are_safe_when_destroyed(self):
        callback = Mock()
        self.cards.empty_action = ("Tạo công việc", callback)
        self.cards.set_tasks([])
        self.settle()
        button = next(widget for card in self.cards.card_container.winfo_children()
                      for widget in card.winfo_children() if isinstance(widget, ttk.Button))
        button.invoke()
        callback.assert_called_once_with()
        self.cards.set_tasks([self.task(51)])
        self.cards._queue_wraps()
        self.cards.destroy()
        self.root.update()

    def test_unknown_layout_is_rejected_without_changing_tasks(self):
        self.cards.set_tasks([self.task(61)])
        with self.assertRaises(ValueError):
            self.cards.set_layout("invalid")
        self.assertEqual(self.cards.layout_mode, "grid")
        self.assertEqual([task.id for task in self.cards.visible_tasks], [61])

    def test_unmapped_large_text_keeps_sane_wraps_until_canvas_has_width(self):
        self.root._layout_scale = 2.0
        self.root.tk.call("tk", "scaling", 192 / 72)
        configure_style(self.root)
        self.cards.set_tasks([
            self.task(index, title="Công việc cần đối chiếu trước khi bàn giao cho các phòng ban. " * 2,
                      notes="Đã xử lý phần đầu; cần xác nhận lại các thông tin còn thiếu. " * 3)
            for index in range(71, 77)
        ])
        self.assertEqual(self.cards.canvas.winfo_width(), 1)
        self.cards._update_wraps()
        for card in self.cards.cards_by_id.values():
            for label in card.wrapping_labels:
                self.assertGreater(int(label.cget("wraplength")), 100)
        self.root.geometry("2020x1300")
        self.settle()
        self.assertGreater(self.cards.canvas.winfo_width(), 1)
        self.assertLess(self.cards.card_container.winfo_height(), 10000)
        for card in self.cards.cards_by_id.values():
            self.assert_card_fits(card)

    def test_refresh_preserves_scroll_for_same_tasks_and_new_tasks_start_at_top(self):
        tasks = [self.task(index) for index in range(81, 93)]
        self.cards.set_layout("wide")
        self.cards.set_tasks(tasks)
        self.settle()
        self.cards.canvas.yview_moveto(1)
        self.settle()
        self.assertGreater(self.cards.canvas.yview()[0], 0)
        self.cards.set_tasks(tasks)
        self.settle()
        self.assertGreater(self.cards.canvas.yview()[0], 0)
        self.cards.set_tasks([self.task(101)])
        self.settle()
        self.assertEqual(self.cards.canvas.yview()[0], 0)


if __name__ == "__main__":
    unittest.main()
