"""Pure, bounded calendar expansion using the original date as the anchor.

Expanding a view never creates database rows.  In particular, a February
adjustment for a monthly 31st must not turn subsequent occurrences into 28ths.
All datetimes here are naive local wall-clock times, as used by the desktop app.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time, timedelta
from collections.abc import Iterator

from .models import Occurrence, Schedule


MAX_RANGE_DAYS = 3653
RECURRENCES = frozenset({"once", "weekly", "monthly", "yearly"})
INVALID_DAY_POLICIES = frozenset({"last_day", "skip"})


def _is_date(value: object) -> bool:
    # datetime is a date subclass, but silently accepting it breaks comparisons.
    return type(value) is date


def _integer_list(value: object, minimum: int, maximum: int, label: str) -> None:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} phải là một danh sách.")
    if any(type(item) is not int or not minimum <= item <= maximum for item in value):
        raise ValueError(f"{label} phải nằm trong khoảng {minimum}–{maximum}.")
    if len(set(value)) != len(value):
        raise ValueError(f"{label} không được trùng lặp.")


def validate_schedule(schedule: Schedule) -> None:
    """Raise ValueError for unsupported, ambiguous, or invalid schedule data."""
    if not isinstance(schedule.title, str) or not schedule.title.strip():
        raise ValueError("Tên lịch không được để trống.")
    if not isinstance(schedule.recurrence, str) or schedule.recurrence not in RECURRENCES:
        raise ValueError("Chu kỳ lặp không hợp lệ.")
    if not isinstance(schedule.invalid_day_policy, str) or schedule.invalid_day_policy not in INVALID_DAY_POLICIES:
        raise ValueError("Cách xử lý ngày không tồn tại không hợp lệ.")
    if not _is_date(schedule.start_date):
        raise ValueError("Ngày bắt đầu phải là một ngày hợp lệ.")
    if schedule.until is not None:
        if not _is_date(schedule.until):
            raise ValueError("Ngày kết thúc lặp phải là một ngày hợp lệ.")
        if schedule.until < schedule.start_date:
            raise ValueError("Ngày kết thúc lặp không được trước ngày bắt đầu.")
    for value in (schedule.start_time, schedule.end_time):
        if not isinstance(value, time) or value.tzinfo is not None:
            raise ValueError("Giờ lịch phải là giờ địa phương, không kèm múi giờ.")
    if schedule.end_time <= schedule.start_time:
        raise ValueError("Giờ kết thúc phải sau giờ bắt đầu trong cùng ngày.")
    _integer_list(schedule.weekdays, 0, 6, "Các thứ trong tuần")
    if schedule.recurrence == "weekly" and not schedule.weekdays:
        raise ValueError("Lịch hằng tuần cần chọn ít nhất một thứ.")
    if type(schedule.reminder_minutes) is not int or not 0 <= schedule.reminder_minutes <= 120:
        raise ValueError("Số phút nhắc trước phải từ 0 đến 120.")
    _integer_list(schedule.reminder_days, 1, 365, "Số ngày nhắc trước")
    if type(schedule.enabled) is not bool:
        raise ValueError("Trạng thái bật lịch không hợp lệ.")


def _adjusted_date(year: int, month: int, day: int, policy: str) -> date | None:
    last = monthrange(year, month)[1]
    if day > last:
        if policy == "skip":
            return None
        day = last
    return date(year, month, day)


def _candidate_dates(schedule: Schedule, lower: date, upper: date) -> Iterator[date]:
    if schedule.recurrence == "once":
        yield schedule.start_date
    elif schedule.recurrence == "weekly":
        weekdays = set(schedule.weekdays)
        for offset in range((upper - lower).days + 1):
            current = lower + timedelta(days=offset)
            if current.weekday() in weekdays:
                yield current
    elif schedule.recurrence == "monthly":
        # Month indices avoid both end-of-year rollover and date.max overflow.
        first = lower.year * 12 + lower.month - 1
        last = upper.year * 12 + upper.month - 1
        for month_index in range(first, last + 1):
            year, zero_month = divmod(month_index, 12)
            current = _adjusted_date(
                year, zero_month + 1, schedule.start_date.day, schedule.invalid_day_policy
            )
            if current is not None:
                yield current
    else:  # yearly
        for year in range(lower.year, upper.year + 1):
            current = _adjusted_date(
                year, schedule.start_date.month, schedule.start_date.day,
                schedule.invalid_day_policy,
            )
            if current is not None:
                yield current


def expand_schedule(schedule: Schedule, start_date: date, end_date: date) -> list[Occurrence]:
    """Return occurrences in an inclusive date range, without side effects.

    Saved schedules have positive IDs.  An unsaved schedule may be expanded for
    a form preview; its occurrences use the reserved ID 0.
    """
    validate_schedule(schedule)
    if not _is_date(start_date) or not _is_date(end_date):
        raise ValueError("Khoảng lịch cần ngày bắt đầu và ngày kết thúc hợp lệ.")
    if end_date < start_date:
        raise ValueError("Ngày kết thúc khoảng xem không được trước ngày bắt đầu.")
    if (end_date - start_date).days + 1 > MAX_RANGE_DAYS:
        raise ValueError(f"Mỗi lần xem hoặc xuất lịch tối đa {MAX_RANGE_DAYS} ngày.")
    if not schedule.enabled:
        return []
    lower = max(start_date, schedule.start_date)
    upper = min(end_date, schedule.until) if schedule.until is not None else end_date
    if lower > upper:
        return []

    result = []
    for current in _candidate_dates(schedule, lower, upper):
        if not lower <= current <= upper:
            continue
        result.append(Occurrence(
            schedule_id=schedule.id if schedule.id is not None else 0,
            title=schedule.title,
            start=datetime.combine(current, schedule.start_time),
            end=datetime.combine(current, schedule.end_time),
            category=schedule.category,
            content=schedule.content,
        ))
    return result
