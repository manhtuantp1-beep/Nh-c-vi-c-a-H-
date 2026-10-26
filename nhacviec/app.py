"""Vietnamese desktop workflow for tasks, recurrence, notifications and backups."""
from __future__ import annotations

from datetime import datetime
import logging
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont
from tkinter.scrolledtext import ScrolledText
import traceback

from . import __version__
from .calendar_ui import CalendarView, close_schedule_editors
from .platform_support import PlatformSupport
from .reminders import ReminderEngine
from .widgets import ui_font, scale_px
from .display import sync_tk_scaling

from .dialogs import TaskDialog, NotesDialog, SettingsDialog, ExportDialog, STATUS_LABELS
from .task_ui import TaskListPage, ALL_FILTER, TODO_FILTER
from .theme import BG, INK, MUTED, PRIMARY, BORDER, NAVY, NAV_TEXT, NAV_MUTED, configure_style, line_icon


class NhacViecApp:
    def __init__(self, root: tk.Tk, store, data_dir: Path, *, integrations=True, enable_timers=True,
                 font_scale_override: float | None = None):
        self.root, self.store, self.data_dir = root, store, Path(data_dir)
        self.instance_lock = None
        self._closing = False
        self._after_ids = set()
        self.pages = {}
        self.current_page = "active"
        self.notification_window = None
        self.notification_text = None
        self.notifications = []
        if font_scale_override is None:
            native_dpi = sync_tk_scaling(root)
            factor = (native_dpi / 96 if native_dpi else float(root.tk.call("tk", "scaling")) / (96 / 72)) if sys.platform == "win32" else 1.0
        else:
            factor = float(font_scale_override)
            if not 0.5 <= factor <= 4:
                raise ValueError("Unsupported interface scale")
            root.tk.call("tk", "scaling", factor * (96 / 72))
        root._layout_scale = factor
        px = lambda value: scale_px(root, value)
        root.title(f"Nhắc việc anh Hà · {__version__}")
        available_width = root.winfo_screenwidth() - px(40)
        available_height = root.winfo_screenheight() - px(64)
        min_width = min(px(1120), available_width)
        min_height = min(px(680), available_height)
        width = max(min_width, min(px(1320), available_width))
        height = max(min_height, min(px(820), available_height))
        root.geometry(f"{width}x{height}")
        root.minsize(min_width, min_height)
        root.configure(background=BG)
        configure_style(root)
        root.report_callback_exception = self.report_exception
        root.protocol("WM_DELETE_WINDOW", self.minimize)
        footer = ttk.Frame(root, style="Surface.TFrame", padding=(18, 6))
        footer.pack(side="bottom", fill="x")
        self.status_var = tk.StringVar(value="Sẵn sàng  ·  Dữ liệu được lưu trên máy tính của anh")
        ttk.Label(footer, textvariable=self.status_var, style="Footer.TLabel").pack(side="left")
        ttk.Label(footer, text=f"Phiên bản {__version__}", style="Footer.TLabel").pack(side="right")
        shell = ttk.Frame(root)
        shell.pack(fill="both", expand=True)
        nav_font = tkfont.Font(root=root, font=ui_font(root, 11, "bold"))
        sidebar_width = max(px(230), nav_font.measure("Đang thực hiện   999") + px(64))
        self.sidebar = ttk.Frame(shell, style="Side.TFrame", padding=(px(12), px(18)), width=sidebar_width)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        bottom = ttk.Frame(self.sidebar, style="Side.TFrame")
        bottom.pack(side="bottom", fill="x")
        ttk.Separator(bottom, style="Side.TSeparator").pack(fill="x", pady=(10, 10))
        ttk.Button(bottom, text="Thông tin ứng dụng", style="Nav.TButton", command=self.about).pack(fill="x")
        ttk.Button(bottom, text="Thoát hẳn ứng dụng", style="Nav.TButton", command=self.exit).pack(fill="x", pady=(2, 0))
        brand = ttk.Frame(self.sidebar, style="Side.TFrame")
        brand.pack(fill="x", padx=9, pady=(0, 20))
        logo = tk.Canvas(brand, width=px(34), height=px(34), background=NAVY, highlightthickness=0)
        logo.pack(side="left", padx=(0, 9))
        logo.create_oval(px(1), px(1), px(33), px(33), fill="#F1CA65", outline="#F1CA65")
        logo.create_line(px(10), px(17), px(15), px(22), px(25), px(11), fill=NAVY, width=px(3), capstyle="round", joinstyle="round")
        brand_text = ttk.Frame(brand, style="Side.TFrame")
        brand_text.pack(side="left")
        ttk.Label(brand_text, text="Nhắc việc", style="Side.TLabel").pack(anchor="w")
        ttk.Label(brand_text, text="Không gian cá nhân", style="SideMeta.TLabel").pack(anchor="w", pady=(3, 0))
        ttk.Label(self.sidebar, text="CÔNG VIỆC", style="SideSection.TLabel").pack(anchor="w", padx=12, pady=(0, 9))
        self.nav_buttons = {}
        self._nav_icons = {}
        for key, text in [("active", "Việc cần làm"), ("in_progress", "Đang thực hiện"), ("due", "Sắp đến hạn"),
                          ("completed", "Đã hoàn thành"), ("canceled", "Đã hủy"), ("calendar", "Lịch của anh")]:
            self._nav_icons[key] = (line_icon(root, key, NAV_MUTED, size=px(18)), line_icon(root, key, "#F1CA65", size=px(18)))
            b = ttk.Button(self.sidebar, text=text, image=self._nav_icons[key][0], compound="left",
                           style="Nav.TButton", command=lambda k=key: self.show_page(k))
            b.pack(fill="x", pady=2)
            self.nav_buttons[key] = b
        ttk.Label(self.sidebar, text="TIỆN ÍCH", style="SideSection.TLabel").pack(anchor="w", padx=12, pady=(18, 7))
        self.data_menu = tk.Menu(self.sidebar, tearoff=False, borderwidth=0, activeborderwidth=0)
        for text, action in (("Xuất báo cáo Excel…", lambda: ExportDialog(self)), ("Sao lưu dữ liệu…", self.backup),
                             ("Khôi phục dữ liệu…", self.restore)):
            self.data_menu.add_command(label=text, command=action)
        ttk.Menubutton(self.sidebar, text="Dữ liệu và báo cáo", style="Utility.TMenubutton", menu=self.data_menu).pack(fill="x", pady=2)
        for text, action in (("Cài đặt nhắc việc", lambda: SettingsDialog(self)), ("Thông báo đã nhận", self.show_notification_center)):
            ttk.Button(self.sidebar, text=text, style="Nav.TButton", command=action).pack(fill="x", pady=2)
        ttk.Frame(shell, style="Border.TFrame", width=1).pack(side="left", fill="y")
        self.content = ttk.Frame(shell)
        self.content.pack(side="left", fill="both", expand=True)
        root.bind("<Control-n>", lambda _e: self.new_task())
        root.bind("<Control-f>", self.focus_search)
        self.platform = PlatformSupport(root, self.show_window, self.exit, self.on_notification_action)
        if integrations:
            self.platform.start_tray()
        self.reminder_engine = ReminderEngine(store)
        self.show_page("active")
        if enable_timers:
            self._schedule(250, self._platform_tick)
            self._schedule(1000, self._reminder_tick)

    def _schedule(self, delay, callback):
        if not self._closing:
            def run():
                self._after_ids.discard(handle)
                if not self._closing:
                    callback()
            handle = self.root.after(delay, run)
            self._after_ids.add(handle)

    def show_page(self, key):
        if key not in self.pages:
            if key == "calendar":
                self.pages[key] = CalendarView(self.content, self.store, on_change=self.refresh_current, app=self)
            else:
                self.pages[key] = TaskListPage(self.content, self, key)
        for page in self.pages.values():
            page.pack_forget()
        self.current_page = key
        for nav_key, button in self.nav_buttons.items():
            selected = nav_key == key
            button.configure(style="Selected.Nav.TButton" if selected else "Nav.TButton",
                             image=self._nav_icons[nav_key][int(selected)])
        self.pages[key].pack(fill="both", expand=True)
        self.refresh_current()

    def refresh_current(self):
        page = self.pages.get(self.current_page)
        if page:
            page.refresh()
        active = len(self.store.list_tasks(status="active"))
        self.nav_buttons["active"].configure(text=f"Việc cần làm   {active}")
        for key in ("in_progress", "completed", "canceled"):
            self.nav_buttons[key].configure(text=f"{STATUS_LABELS[key]}   {len(self.store.list_tasks(status=key))}")

    def focus_search(self, _event=None):
        page = self.pages.get(self.current_page)
        if isinstance(page, TaskListPage):
            page.search_entry.focus_set()
            page.search_entry.selection_range(0, "end")
            return "break"

    def new_task(self):
        dialog = TaskDialog(self)
        if self.current_page == "calendar":
            dialog.date_entry.set_date(self.pages["calendar"].selected_date)
            dialog._initial = dialog.snapshot()
        return dialog

    def edit_task(self, task_id):
        task = self.store.get_task(task_id)
        if task is None:
            messagebox.showerror("Không tìm thấy", "Công việc không còn tồn tại.", parent=self.root)
            return None
        return TaskDialog(self, task)

    def edit_task_notes(self, task_id):
        task = self.store.get_task(task_id)
        if task is None:
            messagebox.showerror("Không tìm thấy", "Công việc không còn tồn tại.", parent=self.root)
            return None
        return NotesDialog(self, task)

    def transition_task(self, task_id, status, reason=""):
        self.store.set_task_status(task_id, status, reason=reason)
        self.refresh_current()

    def backup(self):
        target = filedialog.asksaveasfilename(parent=self.root, title="Sao lưu dữ liệu bản dựng mới", defaultextension=".db", filetypes=[("SQLite", "*.db")], initialfile=f"NhacViec-backup-{datetime.now():%Y%m%d-%H%M%S}.db")
        if not target:
            return
        try:
            self.store.backup(target)
            messagebox.showinfo("Đã sao lưu", f"Đã tạo bản sao nhất quán tại:\n{target}", parent=self.root)
        except Exception as exc:
            logging.exception("Sao lưu thất bại")
            messagebox.showerror("Không sao lưu được", str(exc), parent=self.root)

    def restore(self):
        target = filedialog.askopenfilename(parent=self.root, title="Khôi phục bản sao lưu của bản dựng mới", filetypes=[("SQLite", "*.db"), ("Tất cả", "*.*")])
        if not target:
            return
        if not messagebox.askyesno("Thay thế dữ liệu bản dựng mới", "Khôi phục thay thế toàn bộ dữ liệu hiện tại, không gộp hai bộ dữ liệu. Một bản sao trước khôi phục sẽ được giữ lại.\n\nChỉ hỗ trợ cơ sở dữ liệu của bản dựng mới. Tiếp tục?", parent=self.root):
            return
        try:
            previous = self.store.restore(target)
            self.reminder_engine = ReminderEngine(self.store)
            self.refresh_current()
            messagebox.showinfo("Đã khôi phục", f"Đã khôi phục dữ liệu. Bản dự phòng trước đó:\n{previous}", parent=self.root)
        except Exception as exc:
            logging.exception("Khôi phục thất bại")
            messagebox.showerror("Không khôi phục được", str(exc), parent=self.root)

    def _platform_tick(self):
        if self._closing:
            return
        try:
            self.platform.process_pending()
        except Exception:
            logging.exception("Xử lý khay hệ thống thất bại")
        self._schedule(250, self._platform_tick)

    def _reminder_tick(self):
        if self._closing:
            return
        try:
            fallback = []
            for item in self.reminder_engine.poll():
                if self.platform.notify(item):
                    self.notifications.append(item)
                    self.reminder_engine.mark_delivered(item)
                else:
                    fallback.append(item)
            if fallback:
                self.notifications.extend(fallback)
                self.show_window()
                self.show_notification_center()
                # A visible in-app notification counts as a delivered fallback.
                for item in fallback:
                    self.reminder_engine.mark_delivered(item)
        except Exception:
            logging.exception("Kiểm tra nhắc việc thất bại")
            self.status_var.set("Nhắc việc gặp lỗi. Xem nhật ký hoặc mở lại ứng dụng.")
        self._schedule(15_000, self._reminder_tick)

    def show_notification_center(self):
        if self.notification_window is not None and self.notification_window.winfo_exists():
            window = self.notification_window
        else:
            window = tk.Toplevel(self.root)
            window.title("Thông báo nhắc việc")
            window.geometry("650x470")
            ttk.Label(window, text="Thông báo trong phiên làm việc", font=ui_font(window, 16, "bold"), padding=16).pack(anchor="w")
            self.notification_text = ScrolledText(window, wrap="word", relief="flat", padx=20, pady=16,
                                                  font=ui_font(window, 11), background="white", foreground=INK,
                                                  spacing1=4, spacing3=8)
            self.notification_text.pack(fill="both", expand=True)
            ttk.Button(window, text="Đóng", command=window.destroy).pack(anchor="e", padx=16, pady=12)
            self.notification_window = window
        self.notification_text.configure(state="normal")
        self.notification_text.delete("1.0", "end")
        if not self.notifications:
            self.notification_text.insert("end", "Chưa có thông báo trong phiên làm việc này.")
        for item in reversed(self.notifications[-200:]):
            self.notification_text.insert("end", f"{item.title}\n{item.message}\n\n")
        self.notification_text.configure(state="disabled")
        window.deiconify()
        window.lift()

    def on_notification_action(self, item=None):
        self.show_window()
        if item is not None and getattr(item, "schedule_id", None):
            self.show_page("calendar")

    def show_window(self):
        self.root.deiconify()
        self.root.lift()

    def minimize(self):
        self.platform.minimize()
        if not self.platform.tray_available:
            self.status_var.set("Ứng dụng đang chạy; cửa sổ thu nhỏ trên thanh tác vụ. Dùng Thoát hẳn để dừng nhắc.")

    def about(self):
        messagebox.showinfo("Nhắc việc anh Hà", f"Nhắc việc anh Hà {__version__}\nQuản lý công việc và lịch cá nhân.\n\nDữ liệu: {self.store.path}\n\nDữ liệu bản 2.0.0 tiếp tục dùng được trong bản này. Chưa hỗ trợ tự động nhập dữ liệu bản 1.7.0.", parent=self.root)

    def report_exception(self, exc_type, value, tb):
        logging.error("Lỗi giao diện: %s", "".join(traceback.format_exception(exc_type, value, tb)))
        messagebox.showerror("Thao tác chưa hoàn tất", f"{value}\n\nNhật ký: {self.data_dir / 'logs' / 'lifecycle.log'}", parent=self.root)

    def exit(self):
        if self._closing:
            return
        if not close_schedule_editors(self.root):
            return
        # Prevent discarding an open task form without the form's own check.
        for child in self.root.winfo_children():
            if isinstance(child, (TaskDialog, NotesDialog)):
                child.cancel()
                if child.winfo_exists():
                    return
        self._closing = True
        for handle in self._after_ids:
            try:
                self.root.after_cancel(handle)
            except tk.TclError:
                pass
        self.platform.stop()
        if self.instance_lock is not None:
            self.instance_lock.close()
        logging.info("Thoát hẳn ứng dụng")
        self.root.destroy()
