import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
import sqlite3
from contextlib import closing
import tempfile
import unittest
from unittest.mock import patch

from nhacviec.models import Schedule
from nhacviec.storage import Storage, UnsupportedDatabase


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "tasks.db"
        self.store = Storage(self.path)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def task(self, title="Việc mới", deadline=None):
        return self.store.create_task(title, deadline or datetime(2030, 1, 10, 16), category="Báo cáo", content="Nội dung", requirements="Đúng hạn")

    def schedule(self, **fields):
        defaults = dict(title="Lịch mẫu", start_date=date(2030, 1, 1), start_time=time(9), end_time=time(10), recurrence="weekly", weekdays=[1])
        return self.store.create_schedule(**(defaults | fields))

    def test_task_lifecycle_two_filters_and_reopen(self):
        a, b, c = self.task("Mới"), self.task("Đang làm"), self.task("Đã xong")
        self.store.set_task_status(b.id, "in_progress")
        done = self.store.set_task_status(c.id, "completed")
        self.assertIsNotNone(done.completed_at)
        self.assertEqual([t.id for t in self.store.list_tasks(status="todo")], [a.id])
        self.assertEqual({t.id for t in self.store.list_tasks(status="active")}, {a.id, b.id})
        reopened = self.store.set_task_status(c.id, "todo", reason="Đã mở lại")
        self.assertIsNone(reopened.completed_at)
        self.assertEqual(reopened.reason, "Đã mở lại")
        self.assertEqual(len(self.store.list_tasks(status="active")), 3)

    def test_unique_codes_and_immutable_identifier(self):
        a, b = self.task(), self.task()
        self.assertNotEqual(a.code, b.code)
        self.assertEqual(self.store.update_task(a.id, title="Đổi tên").code, a.code)
        with self.assertRaises(ValueError):
            self.store.update_task(a.id, code="overwrite")

    def test_search_vietnamese_casefold_dates_and_sort(self):
        a = self.task("BÁO CÁO", datetime(2030, 1, 5, 12))
        self.task("Công việc khác", datetime(2030, 1, 6, 12))
        self.assertEqual([t.id for t in self.store.list_tasks(query="báo cáo")], [a.id])
        self.assertEqual([t.id for t in self.store.list_tasks(date_from=date(2030, 1, 5), date_to=date(2030, 1, 5))], [a.id])
        self.assertEqual(self.store.list_tasks(descending=True)[0].title, "Công việc khác")

    def test_invalid_tasks_and_settings_leave_state_unchanged(self):
        with self.assertRaises(ValueError):
            self.task("   ")
        with self.assertRaises(ValueError):
            self.store.save_settings(days_before=True)
        with self.assertRaises(ValueError):
            self.store.save_settings(daily_time="25:00")
        with self.assertRaises(ValueError):
            self.store.save_settings(notifications_enabled=1)
        self.assertEqual(self.store.get_settings()["days_before"], 7)
        a = self.task()
        with self.assertRaises(ValueError):
            self.store.set_task_status(a.id, "unknown")
        self.assertEqual(self.store.get_task(a.id).status, "todo")

    def test_settings_persist_after_reopen(self):
        self.store.save_settings(daily_time="8:05", days_before=14, notifications_enabled=False)
        self.store.close()
        self.store = Storage(self.path)
        self.assertEqual(self.store.get_settings(), {"daily_time": "08:05", "days_before": 14, "notifications_enabled": False})

    def test_session_status_changes_only_one_repetition(self):
        s = self.schedule()
        self.store.set_occurrence_status(s.id, date(2030, 1, 1), "completed")
        sessions = self.store.occurrences(date(2030, 1, 1), date(2030, 1, 8))
        self.assertEqual([o.status for o in sessions], ["completed", "pending"])
        self.store.set_occurrence_status(s.id, date(2030, 1, 1), "pending")
        self.assertEqual(self.store.occurrences(date(2030, 1, 1), date(2030, 1, 1))[0].status, "pending")

    def test_snapshot_preserved_after_rule_edit_and_pause(self):
        s = self.schedule()
        self.store.set_occurrence_status(s.id, date(2030, 1, 1), "completed")
        self.store.update_schedule(s.id, weekdays=[2], title="Tên mới", start_time=time(11), end_time=time(12))
        occurrences = self.store.occurrences(date(2030, 1, 1), date(2030, 1, 2))
        self.assertEqual(len(occurrences), 2)
        self.assertEqual((occurrences[0].title, occurrences[0].start.hour, occurrences[0].status), ("Lịch mẫu", 9, "completed"))
        self.store.set_schedule_enabled(s.id, False)
        remaining = self.store.occurrences(date(2030, 1, 1), date(2030, 1, 9))
        self.assertEqual([(o.start.date(), o.status) for o in remaining], [(date(2030, 1, 1), "completed")])

    def test_started_sessions_preserved_when_disabling(self):
        yesterday = date.today() - timedelta(days=1)
        s = self.schedule(start_date=yesterday, recurrence="once", weekdays=[])
        self.store.set_schedule_enabled(s.id, False)
        result = self.store.occurrences(yesterday, yesterday)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, "pending")

    def test_snooze_boundaries_and_completed_guard(self):
        s = self.schedule()
        day = date(2030, 1, 1)
        until = datetime(2030, 1, 1, 9, 10)
        self.store.snooze_occurrence(s.id, day, until)
        self.assertEqual(self.store.occurrences(day, day)[0].snoozed_until, until)
        with self.assertRaises(ValueError):
            self.store.snooze_occurrence(s.id, day, datetime(2030, 1, 1, 10, 1))
        self.store.set_occurrence_status(s.id, day, "completed")
        with self.assertRaises(ValueError):
            self.store.snooze_occurrence(s.id, day, until)
        with self.assertRaises(ValueError):
            self.store.set_occurrence_status(s.id, date(2030, 1, 2), "completed")

    def test_past_snooze_is_rejected(self):
        s = self.schedule(start_date=date.today(), recurrence="once", weekdays=[])
        with self.assertRaises(ValueError):
            self.store.snooze_occurrence(s.id, date.today(), datetime.now() - timedelta(minutes=1))

    def test_viewing_occurrences_does_not_write_rows(self):
        self.schedule()
        self.store.occurrences(date(2030, 1, 1), date(2030, 2, 1))
        count = self.store.connection.execute("SELECT count(*) FROM occurrence_overrides").fetchone()[0]
        self.assertEqual(count, 0)

    def test_backup_restore_and_pre_restore_copy(self):
        original = self.task("Trước sao lưu")
        self.store.save_settings(days_before=21)
        s = self.schedule()
        self.store.set_occurrence_status(s.id, date(2030, 1, 1), "completed")
        backup = self.store.backup(Path(self.temp.name) / "backup.db")
        self.store.update_task(original.id, title="Sau sao lưu")
        preserved = self.store.restore(backup)
        self.assertTrue(preserved.exists())
        self.assertEqual(self.store.get_task(original.id).title, "Trước sao lưu")
        self.assertEqual(self.store.get_settings()["days_before"], 21)
        self.assertEqual(self.store.occurrences(date(2030, 1, 1), date(2030, 1, 1))[0].status, "completed")
        with Storage(preserved) as previous:
            self.assertEqual(previous.get_task(original.id).title, "Sau sao lưu")

    def test_backup_releases_destination_before_atomic_replace(self):
        """Windows refuses to replace a database while its handle is still open."""
        self.task("Kiểm tra sao lưu Windows")
        target = Path(self.temp.name) / "windows-backup.db"
        real_connect, real_replace = sqlite3.connect, Path.replace
        destinations = []

        def connect(*args, **kwargs):
            connection = real_connect(*args, **kwargs)
            destinations.append(connection)
            return connection

        def windows_replace(source, destination):
            for connection in destinations:
                try:
                    connection.execute("SELECT 1")
                except sqlite3.ProgrammingError:
                    continue
                raise PermissionError("Windows cannot replace an open database")
            return real_replace(source, destination)

        try:
            with patch("nhacviec.storage.sqlite3.connect", side_effect=connect), patch.object(Path, "replace", windows_replace):
                self.store.backup(target)
        finally:
            for connection in destinations:
                connection.close()
        with Storage(target) as backup:
            self.assertEqual(backup.list_tasks()[0].title, "Kiểm tra sao lưu Windows")

    def test_unknown_legacy_database_rejected_without_changes(self):
        other = Path(self.temp.name) / "legacy.db"
        with closing(sqlite3.connect(other)) as conn, conn:
            conn.execute("CREATE TABLE old_tasks(title TEXT)")
        before = other.read_bytes()
        with self.assertRaises(UnsupportedDatabase):
            Storage(other)
        self.assertEqual(other.read_bytes(), before)
        self.task("Giữ lại")
        with self.assertRaises(UnsupportedDatabase):
            self.store.restore(other)
        self.assertEqual(len(self.store.list_tasks()), 1)

    def test_corrupt_settings_in_backup_are_rejected(self):
        saved = self.store.backup(Path(self.temp.name) / "invalid.db")
        with closing(sqlite3.connect(saved)) as conn, conn:
            conn.execute("UPDATE settings SET value=? WHERE key='days_before'", (json.dumps(True),))
        with self.assertRaises(UnsupportedDatabase):
            self.store.restore(saved)

    def test_blank_required_timestamps_in_backup_are_rejected(self):
        self.task()
        saved = self.store.backup(Path(self.temp.name) / "blank-time.db")
        with closing(sqlite3.connect(saved)) as conn, conn:
            conn.execute("UPDATE tasks SET deadline=''")
        with self.assertRaises(UnsupportedDatabase):
            self.store.restore(saved)
        self.assertEqual(len(self.store.list_tasks()), 1)

    def test_pause_resume_does_not_backfill_sessions_during_pause(self):
        with patch("nhacviec.storage._now", return_value=datetime(2030, 1, 1, 8)):
            s = self.schedule()
        with patch("nhacviec.storage._now", return_value=datetime(2030, 1, 2, 8)):
            self.store.set_schedule_enabled(s.id, False)
        with patch("nhacviec.storage._now", return_value=datetime(2030, 1, 15, 8)):
            self.store.set_schedule_enabled(s.id, True)
        sessions = self.store.occurrences(date(2030, 1, 1), date(2030, 1, 15))
        self.assertEqual([o.start.date() for o in sessions], [date(2030, 1, 1), date(2030, 1, 15)])
        # A subsequent edit must not snapshot the previously paused session.
        with patch("nhacviec.storage._now", return_value=datetime(2030, 1, 16, 8)):
            self.store.update_schedule(s.id, title="Lịch đổi tên")
        sessions = self.store.occurrences(date(2030, 1, 1), date(2030, 1, 15))
        self.assertEqual([o.start.date() for o in sessions], [date(2030, 1, 1), date(2030, 1, 15)])

    def test_new_rule_never_invents_extra_historical_sessions(self):
        with patch("nhacviec.storage._now", return_value=datetime(2030, 1, 1, 8)):
            s = self.schedule()
        with patch("nhacviec.storage._now", return_value=datetime(2030, 1, 16, 8)):
            self.store.update_schedule(s.id, weekdays=[2])
        sessions = self.store.occurrences(date(2030, 1, 1), date(2030, 1, 23))
        self.assertEqual([o.start.date() for o in sessions],
                         [date(2030, 1, 1), date(2030, 1, 8), date(2030, 1, 15), date(2030, 1, 16), date(2030, 1, 23)])
        with patch("nhacviec.storage._now", return_value=datetime(2030, 1, 24, 8)):
            self.store.update_schedule(s.id, title="Đổi tên lần nữa")
        previous = self.store.occurrences(date(2030, 1, 1), date(2030, 1, 23))
        self.assertEqual([o.start.date() for o in previous], [o.start.date() for o in sessions])

    def test_invalid_ranges_are_rejected_even_without_schedules(self):
        with self.assertRaises(ValueError):
            self.store.occurrences(date(2030, 2, 1), date(2030, 1, 1))
        with self.assertRaises(ValueError):
            self.store.occurrences(date(2000, 1, 1), date(2030, 1, 1))


if __name__ == "__main__":
    unittest.main()
