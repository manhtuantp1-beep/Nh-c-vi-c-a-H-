"""Read-only report generation: never creates occurrence rows or alters tasks."""
from datetime import date, datetime
from pathlib import Path
import os
import tempfile

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

from .storage import Storage

HEADERS = ["Loại dữ liệu", "Mã công việc", "Tên công việc", "Phân loại", "Trạng thái", "Deadline",
           "Ngày tạo", "Ngày hoàn thành", "Nội dung", "Yêu cầu", "Ngày", "Thứ", "Giờ", "Giờ kết thúc",
           "Kiểu lặp", "Nguồn buổi", "Nhắc trước (phút)", "Nhắc trước (ngày)", "Tháng deadline", "Năm deadline", "Ngày xuất", "Ghi chú công việc"]
TASK_LABELS = {"todo": "Cần làm", "in_progress": "Đang thực hiện", "completed": "Hoàn thành", "canceled": "Đã hủy"}
SESSION_LABELS = {"pending": "Chưa xác nhận", "completed": "Hoàn thành", "skipped": "Bỏ qua"}
RECURRENCE_LABELS = {"once": "Một lần", "weekly": "Hằng tuần", "monthly": "Hằng tháng", "yearly": "Hằng năm"}
WEEKDAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]


def _append(ws, values):
    ws.append(values)
    for cell in ws[ws.max_row]:
        if isinstance(cell.value, str):
            cell.data_type = "s"


def _style(ws, name):
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="16705A")
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 32
    # A header-only table is valid and avoids adding a fake data record.
    table = Table(displayName=name, ref=f"A1:{get_column_letter(ws.max_column)}{ws.max_row}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium4", showRowStripes=True)
    ws.add_table(table)
    for col in range(1, ws.max_column + 1):
        ws.column_dimensions[get_column_letter(col)].width = 22 if col != 3 else 38
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            from datetime import datetime, time
            if isinstance(cell.value, datetime):
                cell.number_format = "dd/mm/yyyy hh:mm"
            elif isinstance(cell.value, date):
                cell.number_format = "dd/mm/yyyy"
            elif isinstance(cell.value, time):
                cell.number_format = "hh:mm"
            cell.alignment = Alignment(vertical="top", wrap_text=True)


def export_workbook(storage: Storage, path: str | Path, start_date: date, end_date: date) -> Path:
    if end_date < start_date:
        raise ValueError("Ngày kết thúc phải từ ngày bắt đầu trở đi.")
    occurrences = storage.occurrences(start_date, end_date)
    workbook = Workbook()
    report = workbook.active
    report.title = "Báo cáo tổng hợp"
    report.append(HEADERS)
    exported_at = datetime.now().replace(microsecond=0)
    for task in storage.list_tasks():
        _append(report, ["Công việc", task.code, task.title, task.category, TASK_LABELS[task.status], task.deadline,
            task.created_at, task.completed_at, task.content, task.requirements, task.deadline.date(),
            WEEKDAYS[task.deadline.weekday()], task.deadline.time(), None, "", "Đã lưu", None, "",
            task.deadline.month, task.deadline.year, exported_at, task.notes])
    schedules = {s.id: s for s in storage.list_schedules()}
    recorded = {(r["schedule_id"], r["on_date"]) for r in storage.connection.execute("SELECT schedule_id,on_date FROM occurrence_overrides")}
    for occurrence in occurrences:
        schedule = schedules[occurrence.schedule_id]
        _append(report, ["Lịch", occurrence.key, occurrence.title, occurrence.category, SESSION_LABELS[occurrence.status],
            occurrence.start, None, None, occurrence.content, "", occurrence.start.date(), WEEKDAYS[occurrence.start.weekday()],
            occurrence.start.time(), occurrence.end.time(), RECURRENCE_LABELS[schedule.recurrence],
            "Đã lưu" if (schedule.id, occurrence.start.date().isoformat()) in recorded else "Dự kiến",
            schedule.reminder_minutes, ", ".join(map(str, schedule.reminder_days)), occurrence.start.month, occurrence.start.year, exported_at, ""])
    _style(report, "DuLieuCongViec")
    definitions = workbook.create_sheet("Lịch gốc")
    definitions.append(["Mã lịch", "Tên lịch", "Phân loại", "Kiểu lặp", "Áp dụng từ", "Kết thúc lặp", "Các thứ",
                        "Giờ bắt đầu", "Giờ kết thúc", "Nhắc trước (phút)", "Nhắc trước (ngày)", "Ngày thiếu",
                        "Trạng thái", "Nội dung"])
    for schedule in schedules.values():
        _append(definitions, [schedule.id, schedule.title, schedule.category, RECURRENCE_LABELS[schedule.recurrence],
            schedule.start_date, schedule.until, ", ".join(WEEKDAYS[d] for d in schedule.weekdays), schedule.start_time,
            schedule.end_time, schedule.reminder_minutes, ", ".join(map(str, schedule.reminder_days)),
            "Ngày cuối tháng" if schedule.invalid_day_policy == "last_day" else "Bỏ qua",
            "Đang áp dụng" if schedule.enabled else "Tạm dừng", schedule.content])
    _style(definitions, "DuLieuLichGoc")
    target = Path(path).expanduser().resolve()
    if target == storage.path:
        raise ValueError("Không thể ghi báo cáo đè lên cơ sở dữ liệu.")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".nhacviec-report-", suffix=".xlsx", dir=target.parent)
    os.close(fd)
    try:
        workbook.save(temp)
        Path(temp).replace(target)
    finally:
        workbook.close()
        Path(temp).unlink(missing_ok=True)
    return target
