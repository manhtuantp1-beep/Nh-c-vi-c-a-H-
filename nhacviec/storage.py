"""SQLite persistence, consistent backups and guarded restoration.

The rebuilt app deliberately uses another directory than the legacy program.
Unknown schemas are rejected without modifying the database.
"""
from __future__ import annotations

from dataclasses import replace
from contextlib import closing
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import sqlite3
import tempfile
from typing import Any

from .models import Task, Schedule, Occurrence, TASK_STATUSES, OCCURRENCE_STATUSES

APP_ID = "nhacviec-anhha-rebuilt"
SCHEMA_VERSION = 1
DEFAULT_SETTINGS = {"daily_time": "09:00", "days_before": 7, "notifications_enabled": True}


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


class UnsupportedDatabase(ValueError):
    """A database does not belong to this app or needs a different schema version."""


def default_database_path() -> Path:
    return Path.home() / "NhacViecAnhHaMoi" / "data" / "tasks.db"


def _datetime(value: datetime | str) -> datetime:
    result = datetime.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(result, datetime) or result.tzinfo is not None:
        raise ValueError("Ngày giờ phải dùng giờ địa phương, không kèm múi giờ.")
    return result.replace(microsecond=0)


def _date(value: date | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    result = date.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(result, date):
        raise ValueError("Ngày không hợp lệ.")
    return result


class Storage:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or default_database_path()).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing = self.path.exists() and self.path.stat().st_size > 0
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        try:
            self.connection.execute("PRAGMA foreign_keys=ON")
            self.connection.execute("PRAGMA trusted_schema=OFF")
            if existing:
                self._validate_database(self.connection)
            else:
                self._initialize()
            self.connection.execute("PRAGMA journal_mode=WAL")
        except Exception:
            self.connection.close()
            raise

    @staticmethod
    def _validate_database(conn: sqlite3.Connection) -> None:
        try:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            marker = conn.execute("SELECT value FROM app_metadata WHERE key='app_id'").fetchone()
            if version != SCHEMA_VERSION or not marker or marker[0] != APP_ID:
                raise UnsupportedDatabase("Cơ sở dữ liệu không thuộc bản dựng mới hoặc sai phiên bản.")
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            required = {"tasks", "schedules", "occurrence_overrides", "settings", "notification_log", "schedule_pauses"}
            if not required.issubset(tables):
                raise UnsupportedDatabase("Cơ sở dữ liệu thiếu bảng bắt buộc.")
            columns = {
                "tasks": {"id", "code", "title", "deadline", "category", "content", "requirements", "status", "created_at", "updated_at", "completed_at", "reason"},
                "schedules": {"id", "title", "category", "start_date", "start_time", "end_time", "recurrence", "weekdays", "until_date", "reminder_minutes", "reminder_days", "invalid_day_policy", "content", "enabled", "effective_from"},
                "occurrence_overrides": {"schedule_id", "on_date", "status", "snoozed_until", "title", "category", "content", "start_at", "end_at"},
                "settings": {"key", "value"}, "notification_log": {"key", "delivered_at"},
                "schedule_pauses": {"id", "schedule_id", "paused_at", "resumed_at"},
            }
            for table, expected in columns.items():
                actual = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
                if not expected.issubset(actual):
                    raise UnsupportedDatabase("Cơ sở dữ liệu có cấu trúc không được hỗ trợ.")
            if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise UnsupportedDatabase("Cơ sở dữ liệu bị lỗi; không thực hiện khôi phục.")
            if conn.execute("PRAGMA foreign_key_check").fetchone():
                raise UnsupportedDatabase("Cơ sở dữ liệu có liên kết không hợp lệ.")
            # Parse all definitions so invalid stored rules cannot be restored silently.
            for row in conn.execute("SELECT * FROM tasks"):
                task = Storage._task(row)
                if (not task.title.strip() or task.status not in TASK_STATUSES
                        or not all(isinstance(value, datetime) for value in (task.deadline, task.created_at, task.updated_at))):
                    raise UnsupportedDatabase("Dữ liệu công việc không hợp lệ.")
            from .recurrence import validate_schedule
            for row in conn.execute("SELECT * FROM schedules"):
                validate_schedule(Storage._schedule(row))
                _datetime(row["effective_from"])
            values = dict(DEFAULT_SETTINGS)
            values.update({r["key"]: json.loads(r["value"]) for r in conn.execute("SELECT * FROM settings")})
            Storage._validate_settings(values)
            for row in conn.execute("SELECT * FROM occurrence_overrides"):
                occurrence = Storage._recorded_occurrence(row)
                if occurrence.status not in OCCURRENCE_STATUSES or occurrence.end <= occurrence.start:
                    raise UnsupportedDatabase("Kết quả buổi lịch không hợp lệ.")
                if occurrence.start.date().isoformat() != row["on_date"]:
                    raise UnsupportedDatabase("Ngày diễn ra không khớp dữ liệu lưu.")
                if occurrence.snoozed_until and occurrence.snoozed_until > occurrence.end:
                    raise UnsupportedDatabase("Giờ hoãn nhắc vượt giờ kết thúc.")
            for row in conn.execute("SELECT * FROM schedule_pauses"):
                paused = _datetime(row["paused_at"])
                resumed = _datetime(row["resumed_at"]) if row["resumed_at"] else None
                if resumed and resumed < paused:
                    raise UnsupportedDatabase("Khoảng tạm dừng lịch không hợp lệ.")
        except UnsupportedDatabase:
            raise
        except (sqlite3.Error, ValueError, TypeError, KeyError, IndexError) as exc:
            raise UnsupportedDatabase("Không nhận diện được cơ sở dữ liệu của bản dựng mới.") from exc

    def _initialize(self) -> None:
        with self.connection:
            self.connection.executescript("""
                CREATE TABLE app_metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE tasks(
                    id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
                    deadline TEXT NOT NULL, category TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '', requirements TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL CHECK(status IN ('todo','in_progress','completed','canceled')),
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    completed_at TEXT, reason TEXT NOT NULL DEFAULT '');
                CREATE INDEX tasks_deadline ON tasks(deadline);
                CREATE TABLE schedules(
                    id INTEGER PRIMARY KEY,title TEXT NOT NULL,category TEXT NOT NULL DEFAULT '',
                    start_date TEXT NOT NULL,start_time TEXT NOT NULL,end_time TEXT NOT NULL,
                    recurrence TEXT NOT NULL CHECK(recurrence IN ('once','weekly','monthly','yearly')),
                    weekdays TEXT NOT NULL,until_date TEXT,reminder_minutes INTEGER NOT NULL,
                    reminder_days TEXT NOT NULL,invalid_day_policy TEXT NOT NULL,
                    content TEXT NOT NULL DEFAULT '',enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
                    effective_from TEXT NOT NULL);
                CREATE TABLE occurrence_overrides(
                    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
                    on_date TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('pending','completed','skipped')),
                    snoozed_until TEXT,title TEXT NOT NULL,category TEXT NOT NULL,content TEXT NOT NULL,
                    start_at TEXT NOT NULL,end_at TEXT NOT NULL,PRIMARY KEY(schedule_id,on_date));
                CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE notification_log(key TEXT PRIMARY KEY,delivered_at TEXT NOT NULL);
                CREATE TABLE schedule_pauses(id INTEGER PRIMARY KEY,
                    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
                    paused_at TEXT NOT NULL,resumed_at TEXT);
            """)
            self.connection.execute("INSERT INTO app_metadata VALUES('app_id',?)", (APP_ID,))
            self.connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            self.connection.executemany("INSERT INTO settings VALUES(?,?)", [(k, json.dumps(v)) for k, v in DEFAULT_SETTINGS.items()])

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Storage:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    @staticmethod
    def _task(row: sqlite3.Row) -> Task:
        data = dict(row)
        for name in ("deadline", "created_at", "updated_at", "completed_at"):
            data[name] = _datetime(data[name]) if data[name] else None
        return Task(**data)

    def create_task(self, title: str, deadline: datetime, category: str = "", content: str = "", requirements: str = "") -> Task:
        title = title.strip()
        if not title:
            raise ValueError("Tên công việc không được để trống.")
        deadline = _datetime(deadline)
        now = datetime.now().replace(microsecond=0)
        stem = now.strftime("%H:%M-%d%m%Y")
        code, suffix = stem, 1
        while self.connection.execute("SELECT 1 FROM tasks WHERE code=?", (code,)).fetchone():
            suffix += 1
            code = f"{stem}-{suffix:02d}"
        with self.connection:
            cur = self.connection.execute("""INSERT INTO tasks
                (code,title,deadline,category,content,requirements,status,created_at,updated_at,reason)
                VALUES(?,?,?,?,?,?,'todo',?,?,'')""",
                (code, title, deadline.isoformat(), category.strip(), content, requirements, now.isoformat(), now.isoformat()))
        return self.get_task(cur.lastrowid)

    def get_task(self, task_id: int) -> Task | None:
        row = self.connection.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return self._task(row) if row else None

    def update_task(self, task_id: int, **fields: Any) -> Task:
        task = self.get_task(task_id)
        if task is None:
            raise ValueError("Không tìm thấy công việc.")
        allowed = {"title", "deadline", "category", "content", "requirements", "status", "reason"}
        if fields.keys() - allowed:
            raise ValueError("Trường công việc không được hỗ trợ.")
        task = replace(task, **fields)
        task.title = task.title.strip()
        task.deadline = _datetime(task.deadline)
        if not task.title or task.status not in TASK_STATUSES:
            raise ValueError("Tên hoặc trạng thái công việc không hợp lệ.")
        task.updated_at = datetime.now().replace(microsecond=0)
        task.completed_at = (task.completed_at or task.updated_at) if task.status == "completed" else None
        with self.connection:
            self.connection.execute("""UPDATE tasks SET title=?,deadline=?,category=?,content=?,requirements=?,
                status=?,updated_at=?,completed_at=?,reason=? WHERE id=?""",
                (task.title, task.deadline.isoformat(), task.category.strip(), task.content, task.requirements,
                 task.status, task.updated_at.isoformat(), task.completed_at.isoformat() if task.completed_at else None,
                 task.reason, task_id))
        return self.get_task(task_id)

    def set_task_status(self, task_id: int, status: str, reason: str = "") -> Task:
        return self.update_task(task_id, status=status, reason=reason)

    def list_tasks(self, status: str | None = None, query: str = "", date_from: date | None = None,
                   date_to: date | None = None, sort_by: str = "deadline", descending: bool = False) -> list[Task]:
        if sort_by not in {"deadline", "created_at", "title", "status"}:
            raise ValueError("Trường sắp xếp không hợp lệ.")
        if status not in (None, "active", *TASK_STATUSES):
            raise ValueError("Trạng thái không hợp lệ.")
        tasks = [self._task(r) for r in self.connection.execute("SELECT * FROM tasks")]
        if status == "active":
            tasks = [t for t in tasks if t.status in ("todo", "in_progress")]
        elif status:
            tasks = [t for t in tasks if t.status == status]
        text = query.strip().casefold()
        if text:
            tasks = [t for t in tasks if text in (t.title + " " + t.code).casefold()]
        date_field = "created_at" if sort_by == "created_at" else "deadline"
        if date_from:
            tasks = [t for t in tasks if getattr(t, date_field).date() >= _date(date_from)]
        if date_to:
            tasks = [t for t in tasks if getattr(t, date_field).date() <= _date(date_to)]
        return sorted(tasks, key=lambda t: (getattr(t, sort_by), t.id), reverse=descending)

    @staticmethod
    def _schedule(row: sqlite3.Row) -> Schedule:
        from datetime import time
        data = dict(row)
        data.pop("effective_from")
        data["start_date"] = date.fromisoformat(data["start_date"])
        data["start_time"] = time.fromisoformat(data["start_time"])
        data["end_time"] = time.fromisoformat(data["end_time"])
        until = data.pop("until_date")
        data["until"] = date.fromisoformat(until) if until else None
        data["weekdays"] = json.loads(data["weekdays"])
        data["reminder_days"] = json.loads(data["reminder_days"])
        data["enabled"] = bool(data["enabled"])
        return Schedule(**data)

    def save_schedule(self, schedule: Schedule) -> Schedule:
        from .recurrence import validate_schedule
        validate_schedule(schedule)
        args = (schedule.title.strip(), schedule.category.strip(), schedule.start_date.isoformat(),
                schedule.start_time.isoformat(), schedule.end_time.isoformat(), schedule.recurrence,
                json.dumps(schedule.weekdays), schedule.until.isoformat() if schedule.until else None,
                schedule.reminder_minutes, json.dumps(schedule.reminder_days), schedule.invalid_day_policy,
                schedule.content, int(schedule.enabled))
        with self.connection:
            if schedule.id is None:
                cur = self.connection.execute("""INSERT INTO schedules
                    (title,category,start_date,start_time,end_time,recurrence,weekdays,until_date,
                     reminder_minutes,reminder_days,invalid_day_policy,content,enabled,effective_from)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", args + (datetime.combine(schedule.start_date, datetime.min.time()).isoformat(),))
                schedule_id = cur.lastrowid
                if not schedule.enabled:
                    # An initially paused definition has never been active, even
                    # when its requested anchor precedes the creation date.
                    began = min(_now(), datetime.combine(schedule.start_date, datetime.min.time()))
                    self.connection.execute("INSERT INTO schedule_pauses(schedule_id,paused_at) VALUES(?,?)", (schedule_id, began.isoformat()))
            else:
                old_schedule = self.get_schedule(schedule.id)
                if not old_schedule:
                    raise ValueError("Không tìm thấy lịch.")
                self._preserve_started(old_schedule)
                changed_at = _now().isoformat()
                if old_schedule.enabled and not schedule.enabled:
                    self.connection.execute("INSERT INTO schedule_pauses(schedule_id,paused_at) VALUES(?,?)", (schedule.id, changed_at))
                elif not old_schedule.enabled and schedule.enabled:
                    self.connection.execute("UPDATE schedule_pauses SET resumed_at=? WHERE schedule_id=? AND resumed_at IS NULL", (changed_at, schedule.id))
                self.connection.execute("""UPDATE schedules SET title=?,category=?,start_date=?,start_time=?,
                    end_time=?,recurrence=?,weekdays=?,until_date=?,reminder_minutes=?,reminder_days=?,
                    invalid_day_policy=?,content=?,enabled=?,effective_from=? WHERE id=?""", args + (changed_at, schedule.id))
                schedule_id = schedule.id
        return self.get_schedule(schedule_id)

    def create_schedule(self, **fields: Any) -> Schedule:
        return self.save_schedule(Schedule(**fields))

    def update_schedule(self, schedule_id: int, **fields: Any) -> Schedule:
        current = self.get_schedule(schedule_id)
        if current is None:
            raise ValueError("Không tìm thấy lịch.")
        if "id" in fields:
            raise ValueError("Không thể đổi mã lịch.")
        return self.save_schedule(replace(current, **fields))

    def get_schedule(self, schedule_id: int) -> Schedule | None:
        row = self.connection.execute("SELECT * FROM schedules WHERE id=?", (schedule_id,)).fetchone()
        return self._schedule(row) if row else None

    def list_schedules(self, include_disabled: bool = True) -> list[Schedule]:
        query = "SELECT * FROM schedules" + ("" if include_disabled else " WHERE enabled=1") + " ORDER BY id"
        return [self._schedule(r) for r in self.connection.execute(query)]

    def set_schedule_enabled(self, schedule_id: int, enabled: bool) -> Schedule:
        return self.update_schedule(schedule_id, enabled=enabled)

    def occurrences(self, start_date: date, end_date: date) -> list[Occurrence]:
        from .recurrence import expand_schedule, MAX_RANGE_DAYS
        start_date, end_date = _date(start_date), _date(end_date)
        if end_date < start_date or (end_date - start_date).days + 1 > MAX_RANGE_DAYS:
            raise ValueError("Khoảng ngày phải hợp lệ và không vượt quá 10 năm.")
        result: dict[str, Occurrence] = {}
        for schedule in self.list_schedules():
            pauses = self._pause_intervals(schedule.id)
            effective_from = self._effective_from(schedule.id)
            for occurrence in expand_schedule(schedule, start_date, end_date):
                if occurrence.start >= effective_from and not any(start <= occurrence.start and (end is None or occurrence.start < end) for start, end in pauses):
                    result[occurrence.key] = occurrence
        # Snapshots retain confirmed and already-started sessions when a rule is
        # edited or paused; viewing/exporting a calendar does not create rows.
        rows = self.connection.execute("""SELECT * FROM occurrence_overrides
            WHERE on_date>=? AND on_date<=?""", (start_date.isoformat(), end_date.isoformat()))
        for row in rows:
            occurrence = self._recorded_occurrence(row)
            result[occurrence.key] = occurrence
        return sorted(result.values(), key=lambda o: (o.start, o.schedule_id))

    @staticmethod
    def _recorded_occurrence(row: sqlite3.Row) -> Occurrence:
        return Occurrence(schedule_id=row["schedule_id"], title=row["title"], category=row["category"],
                          content=row["content"], start=_datetime(row["start_at"]), end=_datetime(row["end_at"]),
                          status=row["status"], snoozed_until=_datetime(row["snoozed_until"]) if row["snoozed_until"] else None)

    def record_occurrence(self, occurrence: Occurrence) -> None:
        """Retain a session snapshot once it starts, without resetting results."""
        with self.connection:
            self.connection.execute("""INSERT OR IGNORE INTO occurrence_overrides
                (schedule_id,on_date,status,snoozed_until,title,category,content,start_at,end_at)
                VALUES(?,?,?,?,?,?,?,?,?)""", (occurrence.schedule_id, occurrence.start.date().isoformat(),
                occurrence.status, occurrence.snoozed_until.isoformat() if occurrence.snoozed_until else None,
                occurrence.title, occurrence.category, occurrence.content, occurrence.start.isoformat(), occurrence.end.isoformat()))

    def _preserve_started(self, schedule: Schedule) -> None:
        if not schedule.enabled:
            return
        from .recurrence import expand_schedule
        now = _now()
        first = max(schedule.start_date, now.date() - timedelta(days=3652))
        if first > now.date():
            return
        pauses = self._pause_intervals(schedule.id)
        effective_from = self._effective_from(schedule.id)
        for occurrence in expand_schedule(schedule, first, now.date()):
            if effective_from <= occurrence.start <= now and not any(start <= occurrence.start and (end is None or occurrence.start < end) for start, end in pauses):
                self.record_occurrence(occurrence)

    def _effective_from(self, schedule_id: int) -> datetime:
        row = self.connection.execute("SELECT effective_from FROM schedules WHERE id=?", (schedule_id,)).fetchone()
        return _datetime(row[0])

    def _pause_intervals(self, schedule_id: int) -> list[tuple[datetime, datetime | None]]:
        return [(_datetime(row["paused_at"]), _datetime(row["resumed_at"]) if row["resumed_at"] else None)
                for row in self.connection.execute("SELECT paused_at,resumed_at FROM schedule_pauses WHERE schedule_id=?", (schedule_id,))]

    def _get_occurrence(self, schedule_id: int, on_date: date) -> Occurrence:
        on_date = _date(on_date)
        schedule = self.get_schedule(schedule_id)
        if schedule is None:
            raise ValueError("Không tìm thấy lịch.")
        row = self.connection.execute("SELECT * FROM occurrence_overrides WHERE schedule_id=? AND on_date=?",
                                      (schedule_id, on_date.isoformat())).fetchone()
        if row:
            return self._recorded_occurrence(row)
        from .recurrence import expand_schedule
        generated = expand_schedule(replace(schedule, enabled=True), on_date, on_date)
        if not generated:
            raise ValueError("Lịch không có buổi diễn ra vào ngày đã chọn.")
        if generated[0].start < self._effective_from(schedule_id):
            raise ValueError("Buổi nằm trước thời điểm áp dụng phiên bản lịch hiện tại.")
        if any(start <= generated[0].start and (end is None or generated[0].start < end)
               for start, end in self._pause_intervals(schedule_id)):
            raise ValueError("Buổi nằm trong thời gian lịch đã tạm dừng.")
        return generated[0]

    def set_occurrence_status(self, schedule_id: int, on_date: date, status: str) -> None:
        if status not in OCCURRENCE_STATUSES:
            raise ValueError("Trạng thái buổi không hợp lệ.")
        occurrence = self._get_occurrence(schedule_id, on_date)
        self.record_occurrence(occurrence)
        with self.connection:
            self.connection.execute("""UPDATE occurrence_overrides SET status=?,snoozed_until=NULL
                WHERE schedule_id=? AND on_date=?""", (status, schedule_id, _date(on_date).isoformat()))

    def snooze_occurrence(self, schedule_id: int, on_date: date, until: datetime) -> None:
        occurrence = self._get_occurrence(schedule_id, on_date)
        until = _datetime(until)
        current = next((o for o in self.occurrences(on_date, on_date) if o.schedule_id == schedule_id), occurrence)
        if current.status != "pending":
            raise ValueError("Chỉ hoãn nhắc buổi chưa xác nhận.")
        if until > occurrence.end:
            raise ValueError("Không thể hoãn nhắc vượt giờ kết thúc.")
        if until <= datetime.now():
            raise ValueError("Giờ hoãn nhắc phải ở tương lai.")
        self.record_occurrence(occurrence)
        with self.connection:
            self.connection.execute("""UPDATE occurrence_overrides SET snoozed_until=?
                WHERE schedule_id=? AND on_date=?""", (until.isoformat(), schedule_id, _date(on_date).isoformat()))

    def get_settings(self) -> dict[str, Any]:
        values = dict(DEFAULT_SETTINGS)
        values.update({r["key"]: json.loads(r["value"]) for r in self.connection.execute("SELECT * FROM settings")})
        return values

    def save_settings(self, **values: Any) -> None:
        if values.keys() - DEFAULT_SETTINGS.keys():
            raise ValueError("Thiết lập không được hỗ trợ.")
        merged = self.get_settings() | values
        hours, minutes = self._validate_settings(merged)
        values["daily_time"] = f"{hours:02d}:{minutes:02d}"
        with self.connection:
            self.connection.executemany("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                                        [(k, json.dumps(v)) for k, v in values.items()])

    @staticmethod
    def _validate_settings(merged: dict[str, Any]) -> tuple[int, int]:
        try:
            hours, minutes = map(int, merged["daily_time"].split(":"))
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError
        except (TypeError, AttributeError, ValueError):
            raise ValueError("Giờ nhắc phải có dạng hh:mm.") from None
        if type(merged["days_before"]) is not int or not 1 <= merged["days_before"] <= 30:
            raise ValueError("Số ngày nhắc trước phải từ 1 đến 30.")
        if type(merged["notifications_enabled"]) is not bool:
            raise ValueError("Lựa chọn thông báo không hợp lệ.")
        return hours, minutes

    def notification_delivered(self, key: str) -> bool:
        return self.connection.execute("SELECT 1 FROM notification_log WHERE key=?", (key,)).fetchone() is not None

    def mark_notification(self, key: str, delivered_at: datetime) -> None:
        with self.connection:
            self.connection.execute("INSERT OR IGNORE INTO notification_log VALUES(?,?)", (key, _datetime(delivered_at).isoformat()))

    def backup(self, target: str | Path) -> Path:
        target = Path(target).expanduser().resolve()
        if target == self.path:
            raise ValueError("Bản sao lưu phải khác tệp dữ liệu đang dùng.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".nhacviec-backup-", suffix=".db", dir=target.parent, delete=False) as f:
            temporary = Path(f.name)
        try:
            with closing(sqlite3.connect(temporary)) as dest:
                self.connection.backup(dest)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return target

    def restore(self, source: str | Path) -> Path:
        source = Path(source).expanduser().resolve()
        if source == self.path or not source.is_file():
            raise ValueError("Chọn một tệp sao lưu khác với dữ liệu đang dùng.")
        conn = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA trusted_schema=OFF")
            self._validate_database(conn)
            saved = self.path.with_name("tasks.pre-restore-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".db")
            self.backup(saved)
            self.connection.commit()
            conn.backup(self.connection)
            self.connection.commit()
            return saved
        finally:
            conn.close()
