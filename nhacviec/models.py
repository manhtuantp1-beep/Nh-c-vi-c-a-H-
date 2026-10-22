"""Domain records use naive datetimes in the current machine's local timezone."""
from dataclasses import dataclass, field
from datetime import date, datetime, time


TASK_STATUSES = ("todo", "in_progress", "completed", "canceled")
OCCURRENCE_STATUSES = ("pending", "completed", "skipped")


@dataclass
class Task:
    id: int | None = None
    code: str = ""
    title: str = ""
    deadline: datetime = field(default_factory=datetime.now)
    category: str = ""
    content: str = ""
    requirements: str = ""
    status: str = "todo"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    reason: str = ""


@dataclass
class Schedule:
    id: int | None = None
    title: str = ""
    category: str = ""
    start_date: date = field(default_factory=date.today)
    start_time: time = time(9)
    end_time: time = time(10)
    recurrence: str = "once"
    weekdays: list[int] = field(default_factory=list)
    until: date | None = None
    reminder_minutes: int = 10
    reminder_days: list[int] = field(default_factory=list)
    invalid_day_policy: str = "last_day"
    content: str = ""
    enabled: bool = True


@dataclass
class Occurrence:
    schedule_id: int
    title: str
    start: datetime
    end: datetime
    status: str = "pending"
    category: str = ""
    content: str = ""
    snoozed_until: datetime | None = None

    @property
    def key(self) -> str:
        return f"{self.schedule_id}:{self.start.date().isoformat()}"


@dataclass(frozen=True)
class Notification:
    key: str
    title: str
    message: str
    kind: str
    task_id: int | None = None
    schedule_id: int | None = None
    occurrence_date: date | None = None
