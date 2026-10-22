"""Small, dependency-free Tk widgets shared by the desktop screens."""
from __future__ import annotations

import calendar
from datetime import date, datetime, time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


def ui_font(root_or_widget, size: int = 11, weight: str = "normal") -> tuple[str, int, str]:
    """Choose an installed Unicode UI font, including on non-Windows hosts."""
    families = {family.casefold(): family for family in tkfont.families(root_or_widget)}
    for preferred in ("Segoe UI", "Noto Sans", "DejaVu Sans", "Arial"):
        if preferred.casefold() in families:
            return families[preferred.casefold()], size, weight
    default = tkfont.nametofont("TkDefaultFont", root=root_or_widget).actual("family")
    return default, size, weight


def parse_date(value: str, *, allow_empty: bool = False) -> date | None:
    value = value.strip()
    if not value:
        if allow_empty:
            return None
        raise ValueError("Vui lòng nhập ngày theo dạng dd/mm/yyyy.")
    try:
        parsed = datetime.strptime(value, "%d/%m/%Y").date()
    except (TypeError, ValueError) as exc:
        raise ValueError("Ngày không hợp lệ. Dùng dạng dd/mm/yyyy, ví dụ 21/10/2026.") from exc
    return parsed


def parse_time(value: str) -> time:
    try:
        parsed = datetime.strptime(value.strip(), "%H:%M").time()
    except (TypeError, ValueError) as exc:
        raise ValueError("Giờ không hợp lệ. Dùng dạng hh:mm, ví dụ 09:00.") from exc
    return parsed


def format_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value is not None else ""


class DateEntry(ttk.Frame):
    """A dd/mm/yyyy field with a small, fully local calendar picker.

    ``get_date()`` validates rather than silently replacing bad input. ``get``
    and ``set`` also expose raw text for form dirty-state tracking.
    """

    def __init__(self, parent, value: date | None = None, *, allow_empty: bool = False,
                 textvariable: tk.StringVar | None = None, width: int = 12, **kwargs):
        super().__init__(parent, **kwargs)
        self.allow_empty = allow_empty
        self.variable = textvariable if textvariable is not None else tk.StringVar(self)
        self.entry = ttk.Entry(self, textvariable=self.variable, width=width)
        self.entry.pack(side="left", fill="x", expand=True)
        self.button = ttk.Button(self, text="Lịch", style="Compact.TButton", command=self._open_calendar, width=4)
        self.button.pack(side="left", padx=(5, 0))
        self._popup: tk.Toplevel | None = None
        self._enabled = True
        if textvariable is None or value is not None:
            self.set_date(value if value is not None or allow_empty else date.today())

    def get_date(self) -> date | None:
        return parse_date(self.variable.get(), allow_empty=self.allow_empty)

    def set_date(self, value: date | None) -> None:
        self.variable.set(format_date(value))

    def get(self) -> str:
        return self.variable.get()

    def set(self, value: str) -> None:
        self.variable.set(value)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.entry.configure(state="normal" if enabled else "disabled")
        self.button.configure(state="normal" if enabled else "disabled")

    def _open_calendar(self) -> None:
        if not self._enabled:
            return
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.lift()
            return
        try:
            chosen = self.get_date() or date.today()
        except ValueError:
            chosen = date.today()
        popup = self._popup = tk.Toplevel(self)
        previous_grab = self.grab_current()
        popup.title("Chọn ngày")
        popup.transient(self.winfo_toplevel())
        popup.resizable(False, False)
        self.update_idletasks()
        screen_height = popup.winfo_screenheight()
        x = max(0, min(self.winfo_rootx(), popup.winfo_screenwidth() - 330))
        y = max(0, min(self.winfo_rooty() + self.winfo_height() + 5, screen_height - 330))
        popup.geometry(f"+{x}+{y}")
        outer = ttk.Frame(popup, padding=14, style="Surface.TFrame")
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer, style="Surface.TFrame")
        header.pack(fill="x", pady=(0, 8))
        title = tk.StringVar(popup)
        body = ttk.Frame(outer, style="Surface.TFrame")
        body.pack()
        current = [chosen.year, chosen.month]

        def close():
            if popup.winfo_exists():
                popup.destroy()
            self._popup = None
            if self.winfo_exists():
                self.entry.focus_set()
            if previous_grab is not None and previous_grab.winfo_exists():
                previous_grab.grab_set()

        def choose(value: date | None):
            self.set_date(value)
            self.event_generate("<<DateChanged>>")
            close()

        def move(delta: int):
            year, month = current
            month += delta
            if month < 1:
                year, month = year - 1, 12
            elif month > 12:
                year, month = year + 1, 1
            if not 1 <= year <= 9999:
                return
            current[:] = year, month
            draw()

        def draw():
            for child in body.winfo_children():
                child.destroy()
            year, month = current
            title.set(f"Tháng {month:02d} / {year}")
            for col, label in enumerate(("T2", "T3", "T4", "T5", "T6", "T7", "CN")):
                ttk.Label(body, text=label, anchor="center", width=4, style="Hint.TLabel").grid(row=0, column=col, pady=5)
            for row, week in enumerate(calendar.Calendar(firstweekday=0).monthdayscalendar(year, month), 1):
                for col, day in enumerate(week):
                    if not day:
                        ttk.Label(body, text="", width=4, style="Surface.TLabel").grid(row=row, column=col)
                        continue
                    value = date(year, month, day)
                    day_style = "Selected.Day.TButton" if value == chosen else "Today.Day.TButton" if value == date.today() else "Day.TButton"
                    button = ttk.Button(body, text=str(day), width=4, style=day_style,
                                        command=lambda d=value: choose(d))
                    button.grid(row=row, column=col, padx=1, pady=1)

        ttk.Button(header, text="‹", width=3, command=lambda: move(-1)).pack(side="left")
        ttk.Label(header, textvariable=title, anchor="center", width=20, style="Surface.TLabel").pack(side="left", expand=True)
        ttk.Button(header, text="›", width=3, command=lambda: move(1)).pack(side="right")
        footer = ttk.Frame(outer, style="Surface.TFrame")
        footer.pack(fill="x", pady=(10, 0))
        ttk.Button(footer, text="Hôm nay", command=lambda: choose(date.today())).pack(side="left")
        if self.allow_empty:
            ttk.Button(footer, text="Xóa mốc", command=lambda: choose(None)).pack(side="left", padx=6)
        ttk.Button(footer, text="Đóng", command=close).pack(side="right")
        popup.bind("<Escape>", lambda _event: close())
        popup.protocol("WM_DELETE_WINDOW", close)
        draw()
        popup.update_idletasks()
        popup_width, popup_height = popup.winfo_reqwidth(), popup.winfo_reqheight()
        x = max(8, min(self.winfo_rootx(), popup.winfo_screenwidth() - popup_width - 12))
        y = max(8, min(self.winfo_rooty() + self.winfo_height() + 5,
                       popup.winfo_screenheight() - popup_height - 48))
        popup.geometry(f"+{x}+{y}")
        popup.grab_set()
        popup.focus_set()


class ScrollableForm(ttk.Frame):
    """A form with a vertical scrollbar; does not capture global mouse bindings."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        frame_style = kwargs.get("style", "TFrame")
        background = ttk.Style(self).lookup(frame_style, "background") or "#F4F6FA"
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, background=background)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.content = ttk.Frame(self.canvas, padding=14, style=frame_style)
        self._window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._resize)
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._window, width=e.width))
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<Button-4>", lambda _e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda _e: self.canvas.yview_scroll(1, "units"))

    def _resize(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._bind_children(self.content)

    def _bind_children(self, widget):
        # Keep scrolling local to this form and preserve a text area's own
        # scroll behavior. Labels and fields must not become dead wheel zones.
        if widget.winfo_class() in ("Text", "Toplevel", "Treeview", "Listbox"):
            return
        if not getattr(widget, "_form_wheel_bound", False):
            widget.bind("<MouseWheel>", self._wheel, add="+")
            widget.bind("<Button-4>", lambda _e: self._scroll(-3), add="+")
            widget.bind("<Button-5>", lambda _e: self._scroll(3), add="+")
            widget._form_wheel_bound = True
        for child in widget.winfo_children():
            self._bind_children(child)

    def _scroll(self, units):
        if self.canvas.bbox("all") and self.content.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(units, "units")
            return "break"

    def _wheel(self, event):
        delta = -int(event.delta / 120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1)
        if event.delta:
            return self._scroll(delta)

