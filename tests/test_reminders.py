from datetime import date, datetime, time, timedelta
from pathlib import Path
import tempfile
import unittest

from nhacviec.reminders import ReminderEngine
from nhacviec.storage import Storage


class ReminderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Storage(Path(self.temp.name) / "db.sqlite")
        self.engine = ReminderEngine(self.store)
        self.now = datetime(2030, 1, 1, 9)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def schedule(self, **fields):
        defaults = dict(title="Họp", start_date=self.now.date(), start_time=time(10), end_time=time(11), reminder_minutes=10)
        return self.store.create_schedule(**(defaults | fields))

    def test_daily_window_active_overdue_and_closed(self):
        self.store.create_task("Sắp hạn", self.now + timedelta(days=7))
        self.store.create_task("Quá hạn", self.now - timedelta(days=20))
        self.store.create_task("Còn xa", self.now + timedelta(days=8))
        closed = self.store.create_task("Đã xong", self.now)
        self.store.set_task_status(closed.id, "completed")
        self.assertEqual(self.engine.poll(self.now - timedelta(minutes=1)), [])
        result = self.engine.poll(self.now)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(n.kind == "task_daily" for n in result))

    def test_delivery_only_deduplicates_after_success_and_survives_restart(self):
        self.store.create_task("Nhắc", self.now + timedelta(days=1))
        result = self.engine.poll(self.now)
        self.assertEqual(len(self.engine.poll(self.now)), 1)
        self.engine.mark_delivered(result[0], self.now)
        self.assertEqual(ReminderEngine(self.store).poll(self.now), [])
        self.assertEqual(len(self.engine.poll(self.now + timedelta(days=1))), 1)

    def test_urgent_last_hour_and_changed_deadline(self):
        task = self.store.create_task("Gấp", self.now + timedelta(minutes=30))
        result = self.engine.poll(self.now)
        urgent = next(n for n in result if n.kind == "task_urgent")
        self.engine.mark_delivered(urgent, self.now)
        self.assertFalse(any(n.kind == "task_urgent" for n in self.engine.poll(self.now)))
        self.store.update_task(task.id, deadline=self.now + timedelta(minutes=45))
        self.assertTrue(any(n.kind == "task_urgent" for n in self.engine.poll(self.now)))

    def test_minute_start_and_no_ended_backlog(self):
        self.schedule()
        before = self.engine.poll(self.now.replace(hour=9, minute=50))
        self.assertEqual([n.kind for n in before], ["schedule_before"])
        self.engine.mark_delivered(before[0], self.now)
        self.assertEqual(self.engine.poll(self.now.replace(hour=9, minute=55)), [])
        during = self.engine.poll(self.now.replace(hour=10, minute=15))
        self.assertEqual([n.kind for n in during], ["schedule_start"])
        self.assertEqual(self.engine.poll(self.now.replace(hour=11)), [])

    def test_early_morning_reminder_can_fire_on_previous_date(self):
        self.schedule(start_date=date(2030, 1, 2), start_time=time(0, 30), end_time=time(1), reminder_minutes=120)
        result = self.engine.poll(datetime(2030, 1, 1, 22, 30))
        self.assertEqual([n.kind for n in result], ["schedule_before"])

    def test_edited_future_start_has_new_notification_checkpoint(self):
        s = self.schedule()
        first = self.engine.poll(self.now.replace(hour=9, minute=50))
        self.engine.mark_delivered(first[0], self.now)
        self.store.update_schedule(s.id, start_time=time(10, 30), end_time=time(11, 30))
        next_reminder = self.engine.poll(self.now.replace(hour=10, minute=20))
        self.assertEqual([n.kind for n in next_reminder], ["schedule_before"])
        self.assertNotEqual(first[0].key, next_reminder[0].key)

    def test_day_reminders_monthly_and_yearly(self):
        self.schedule(start_date=date(2030, 1, 8), start_time=time(9), end_time=time(10), recurrence="monthly", reminder_days=[7, 1])
        self.schedule(title="Kỷ niệm", start_date=date(2024, 1, 8), start_time=time(9), end_time=time(10), recurrence="yearly", reminder_days=[7])
        result = self.engine.poll(self.now)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(n.kind == "schedule_days" for n in result))
        self.assertEqual(self.engine.poll(self.now.replace(hour=8)), [])
        self.assertEqual(self.engine.poll(self.now + timedelta(days=1)), [])

    def test_snooze_suppresses_normal_and_sends_once(self):
        s = self.schedule()
        due = self.now.replace(hour=10, minute=10)
        self.store.snooze_occurrence(s.id, self.now.date(), due)
        self.assertEqual(self.engine.poll(self.now.replace(hour=10, minute=5)), [])
        result = self.engine.poll(due)
        self.assertEqual([n.kind for n in result], ["schedule_snooze"])
        self.engine.mark_delivered(result[0], due)
        self.assertEqual(self.engine.poll(due + timedelta(minutes=1)), [])

    def test_completed_skipped_and_disabled_never_notify(self):
        completed = self.schedule()
        skipped = self.schedule(title="Bỏ qua")
        disabled = self.schedule(title="Tạm dừng", enabled=False)
        self.store.set_occurrence_status(completed.id, self.now.date(), "completed")
        self.store.set_occurrence_status(skipped.id, self.now.date(), "skipped")
        self.assertEqual(self.engine.poll(self.now.replace(hour=10)), [])

    def test_notifications_disabled_and_invalid_timezone(self):
        self.store.create_task("Việc", self.now)
        self.store.save_settings(notifications_enabled=False)
        self.assertEqual(self.engine.poll(self.now), [])
        from datetime import timezone
        with self.assertRaises(ValueError):
            self.engine.poll(self.now.replace(tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
