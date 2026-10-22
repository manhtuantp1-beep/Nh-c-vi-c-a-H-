"""Calendar rules, including missing dates, are tested independently of SQLite."""

import unittest
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone

from nhacviec.models import Schedule
from nhacviec.recurrence import MAX_RANGE_DAYS, expand_schedule, validate_schedule


class RecurrenceTests(unittest.TestCase):
    def schedule(self, **changes):
        values = dict(
            id=7, title="Lịch mẫu", category="Công việc",
            start_date=date(2026, 1, 31), start_time=time(9), end_time=time(10),
            recurrence="monthly", content="Nội dung buổi",
        )
        values.update(changes)
        return Schedule(**values)

    def dates(self, schedule, start=date(2026, 1, 1), end=date(2026, 4, 30)):
        return [o.start.date() for o in expand_schedule(schedule, start, end)]

    def test_monthly_clamps_without_anchor_drift(self):
        schedule = self.schedule()
        self.assertEqual(self.dates(schedule), [
            date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)
        ])
        self.assertEqual(schedule.start_date, date(2026, 1, 31))

    def test_monthly_skip_excludes_only_invalid_months(self):
        self.assertEqual(self.dates(self.schedule(invalid_day_policy="skip")), [
            date(2026, 1, 31), date(2026, 3, 31)
        ])

    def test_monthly_leap_february_and_year_rollover(self):
        schedule = self.schedule(start_date=date(2023, 12, 31))
        self.assertEqual(self.dates(schedule, date(2023, 12, 1), date(2024, 3, 31)), [
            date(2023, 12, 31), date(2024, 1, 31), date(2024, 2, 29), date(2024, 3, 31)
        ])

    def test_yearly_leap_day_restores_anchor_in_next_leap_year(self):
        schedule = self.schedule(start_date=date(2024, 2, 29), recurrence="yearly")
        self.assertEqual(self.dates(schedule, date(2024, 1, 1), date(2028, 12, 31)), [
            date(2024, 2, 29), date(2025, 2, 28), date(2026, 2, 28),
            date(2027, 2, 28), date(2028, 2, 29)
        ])

    def test_yearly_skip_leap_day(self):
        schedule = self.schedule(start_date=date(2024, 2, 29), recurrence="yearly", invalid_day_policy="skip")
        self.assertEqual(self.dates(schedule, date(2024, 1, 1), date(2028, 12, 31)), [
            date(2024, 2, 29), date(2028, 2, 29)
        ])

    def test_weekly_sunday_and_start_bound_are_supported(self):
        schedule = self.schedule(start_date=date(2026, 10, 21), recurrence="weekly", weekdays=[0, 6])
        self.assertEqual(self.dates(schedule, date(2026, 10, 19), date(2026, 10, 31)), [
            date(2026, 10, 25), date(2026, 10, 26)
        ])

    def test_once_on_sunday_and_inclusive_bounds(self):
        schedule = self.schedule(start_date=date(2026, 10, 25), recurrence="once")
        self.assertEqual(self.dates(schedule, date(2026, 10, 25), date(2026, 10, 25)), [date(2026, 10, 25)])
        self.assertEqual(self.dates(schedule, date(2026, 10, 26), date(2026, 11, 1)), [])

    def test_until_is_inclusive_and_disables_future_occurrences(self):
        schedule = self.schedule(until=date(2026, 3, 31))
        self.assertEqual(self.dates(schedule), [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31)])
        self.assertEqual(self.dates(replace(schedule, enabled=False)), [])

    def test_requested_range_clips_month_and_retains_details(self):
        schedule = self.schedule()
        result = expand_schedule(schedule, date(2026, 2, 1), date(2026, 2, 28))
        self.assertEqual(len(result), 1)
        occurrence = result[0]
        self.assertEqual(occurrence.start, datetime(2026, 2, 28, 9))
        self.assertEqual(occurrence.end, datetime(2026, 2, 28, 10))
        self.assertEqual(occurrence.schedule_id, 7)
        self.assertEqual(occurrence.title, schedule.title)
        self.assertEqual(occurrence.category, schedule.category)
        self.assertEqual(occurrence.content, schedule.content)
        self.assertEqual(occurrence.status, "pending")

    def test_unsaved_preview_uses_reserved_zero_id(self):
        self.assertEqual(expand_schedule(self.schedule(id=None), date(2026, 1, 1), date(2026, 1, 31))[0].schedule_id, 0)

    def test_empty_intersection_before_start_or_after_until(self):
        schedule = self.schedule(until=date(2026, 3, 31))
        self.assertEqual(self.dates(schedule, date(2025, 1, 1), date(2025, 12, 31)), [])
        self.assertEqual(self.dates(schedule, date(2026, 4, 1), date(2026, 12, 31)), [])

    def test_invalid_form_values_are_rejected(self):
        cases = [
            {"title": "  "}, {"recurrence": "daily"}, {"recurrence": []},
            {"invalid_day_policy": "invented"}, {"invalid_day_policy": []},
            {"start_date": datetime(2026, 1, 31)},
            {"until": date(2026, 1, 1)}, {"until": datetime(2027, 1, 1)},
            {"end_time": time(9)}, {"end_time": time(8)},
            {"start_time": time(9, tzinfo=timezone.utc)},
            {"weekdays": [7]}, {"weekdays": [0, 0]}, {"weekdays": [True]},
            {"recurrence": "weekly", "weekdays": []},
            {"reminder_minutes": -1}, {"reminder_minutes": 121}, {"reminder_minutes": True},
            {"reminder_days": [0]}, {"reminder_days": [366]},
            {"reminder_days": [1, 1]}, {"reminder_days": [True]}, {"enabled": 1},
        ]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_schedule(self.schedule(**changes))

    def test_range_guard_and_type_checks(self):
        schedule = self.schedule()
        start = date(2026, 1, 1)
        # Exactly the documented limit is allowed.
        expand_schedule(schedule, start, start + timedelta(days=MAX_RANGE_DAYS - 1))
        for lower, upper in [
            (start, start + timedelta(days=MAX_RANGE_DAYS)),
            (date(2026, 2, 1), start),
            (datetime(2026, 1, 1), start),
        ]:
            with self.subTest(lower=lower, upper=upper), self.assertRaises(ValueError):
                expand_schedule(schedule, lower, upper)

    def test_date_max_no_overflow_for_weekly(self):
        schedule = self.schedule(start_date=date.max, recurrence="weekly", weekdays=[date.max.weekday()])
        self.assertEqual(self.dates(schedule, date.max, date.max), [date.max])


if __name__ == "__main__":
    unittest.main()
