"""Reminder decisions independent of the OS notification adapter.

poll() does not mark anything delivered. The GUI calls mark_delivered() after a
native notification or visible in-app fallback succeeds, so adapter errors retry.
"""
from datetime import datetime, timedelta, time

from .models import Notification
from .storage import Storage


class ReminderEngine:
    def __init__(self, storage: Storage):
        self.storage = storage

    def poll(self, now: datetime | None = None) -> list[Notification]:
        now = (now or datetime.now()).replace(microsecond=0)
        if now.tzinfo is not None:
            raise ValueError("Bộ nhắc sử dụng giờ địa phương không kèm múi giờ.")
        settings = self.storage.get_settings()
        if not settings["notifications_enabled"]:
            return []
        result: list[Notification] = []

        def emit(notification: Notification) -> None:
            if not self.storage.notification_delivered(notification.key):
                result.append(notification)

        hour, minute = map(int, settings["daily_time"].split(":"))
        daily = datetime.combine(now.date(), time(hour, minute))
        for task in self.storage.list_tasks(status="active"):
            deadline = task.deadline.strftime("%d/%m/%Y %H:%M")
            if now >= daily and (task.deadline.date() - now.date()).days <= settings["days_before"]:
                emit(Notification(key=f"task:{task.id}:daily:{now.date().isoformat()}",
                    title="Nhắc công việc" if task.deadline >= now else "Công việc quá hạn",
                    message=f"{task.title}\nHạn: {deadline}", kind="task_daily", task_id=task.id))
            if task.deadline - timedelta(hours=1) <= now < task.deadline:
                emit(Notification(key=f"task:{task.id}:urgent:{task.deadline.isoformat()}",
                    title="Công việc sắp đến hạn", message=f"{task.title}\nHạn: {deadline}",
                    kind="task_urgent", task_id=task.id))

        schedules = {s.id: s for s in self.storage.list_schedules(include_disabled=False)}
        horizon = max((max(s.reminder_days, default=0) for s in schedules.values()), default=0)
        # Include tomorrow even with no day reminders: a reminder 120 minutes
        # before an early-morning session may fall on the preceding day.
        last = now.date() + timedelta(days=max(horizon, 1))
        for occurrence in self.storage.occurrences(now.date(), last):
            schedule = schedules.get(occurrence.schedule_id)
            if schedule is None or occurrence.status != "pending" or now >= occurrence.end:
                continue
            # A future time edit represents a new checkpoint for the same date.
            # Recorded historical sessions retain their original start timestamp.
            base = f"schedule:{occurrence.key}:{occurrence.start.isoformat()}"
            details = f"{occurrence.title}\n{occurrence.start:%d/%m/%Y %H:%M} – {occurrence.end:%H:%M}"
            if occurrence.start <= now:
                self.storage.record_occurrence(occurrence)
            # A snooze suppresses all normal reminders for that session, including
            # a repeated startup check, and produces one reminder when due.
            if occurrence.snoozed_until is not None:
                if now >= occurrence.snoozed_until:
                    emit(Notification(key=f"{base}:snooze:{occurrence.snoozed_until.isoformat()}",
                        title="Nhắc lại lịch", message=details, kind="schedule_snooze",
                        schedule_id=schedule.id, occurrence_date=occurrence.start.date()))
                continue
            if occurrence.start <= now < occurrence.end:
                emit(Notification(key=f"{base}:start", title="Lịch đang diễn ra", message=details,
                    kind="schedule_start", schedule_id=schedule.id, occurrence_date=occurrence.start.date()))
                continue
            # If waking after the minute reminder but before start, deliver it
            # once. Expired sessions are excluded above, with no notification flood.
            if schedule.reminder_minutes and occurrence.start - timedelta(minutes=schedule.reminder_minutes) <= now < occurrence.start:
                emit(Notification(key=f"{base}:minutes", title="Lịch sắp bắt đầu", message=details,
                    kind="schedule_before", schedule_id=schedule.id, occurrence_date=occurrence.start.date()))
                continue
            # Day reminders fire at the session's local start time on the
            # requested earlier date. Only today's checkpoint can be caught up.
            for days in sorted(schedule.reminder_days):
                target = occurrence.start - timedelta(days=days)
                if now.date() == target.date() and target <= now < occurrence.start:
                    emit(Notification(key=f"{base}:days:{days}", title=f"Lịch sau {days} ngày", message=details,
                        kind="schedule_days", schedule_id=schedule.id, occurrence_date=occurrence.start.date()))
                    break
        return result

    def mark_delivered(self, notification: Notification, now: datetime | None = None) -> None:
        self.storage.mark_notification(notification.key, now or datetime.now())
