"""Optional Windows tray/toast support and an OS-held single-instance lock.

All tray callbacks are placed in a thread-safe queue.  The Tk main thread must
call ``PlatformSupport.process_pending()`` periodically; worker threads never
call Tk methods.  A failed/missing tray falls back to normal taskbar minimising.

``notify`` returning True means Windows toast submission succeeded, not that
Windows displayed it (Do not disturb and system policy remain authoritative).
The toast itself has no activation URI; the tray's "Thông báo gần nhất" action
dispatches ``on_notification_action(notification)`` on the Tk thread instead.

No optional GUI/native package is imported on Linux.  The single-instance file
is kept under the caller-provided *new* application data directory.  A stale
file is harmless: the operating system owns and releases the actual lock.
"""

from __future__ import annotations

import importlib
import errno
import logging
import os
from pathlib import Path
import queue
import sys
import threading
from typing import Any, Callable


LOGGER = logging.getLogger(__name__)
IS_WINDOWS = sys.platform == "win32"


class InstanceLock:
    """Keep one instance per application data directory without deleting files.

    ``acquire`` is idempotent on the owning object.  A second object/process
    returns False while the first owns the lock.  ``close`` releases it; process
    termination also releases it automatically.  The directory must refer to
    the new application, never the original 1.7 data directory.
    """

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.path = self.directory / "app.lock"
        self._file: Any | None = None

    def acquire(self) -> bool:
        if self._file is not None:
            return True
        self.directory.mkdir(parents=True, exist_ok=True)
        stream = self.path.open("a+b")
        try:
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            if IS_WINDOWS:
                msvcrt = importlib.import_module("msvcrt")
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl = importlib.import_module("fcntl")
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            stream.close()
            if exc.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                return False
            raise
        except BaseException:
            stream.close()
            raise
        self._file = stream
        return True

    def close(self) -> None:
        stream, self._file = self._file, None
        if stream is None:
            return
        try:
            stream.seek(0)
            if IS_WINDOWS:
                msvcrt = importlib.import_module("msvcrt")
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl = importlib.import_module("fcntl")
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            stream.close()

    def __enter__(self) -> "InstanceLock":
        if not self.acquire():
            raise RuntimeError("Ứng dụng đang chạy với thư mục dữ liệu này.")
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()


class PlatformSupport:
    """Bridge native platform facilities to callbacks on the Tk main thread.

    Call ``start_tray`` after creating the Tk root.  Call ``process_pending``
    from the application's regular ``root.after`` tick.  Explicit shutdown
    should call ``stop`` before destroying root.  Inspect ``last_error`` for
    diagnostic logging and show an in-app reminder when ``notify`` is False.
    """

    def __init__(
        self,
        root: Any,
        on_show: Callable[[], None],
        on_exit: Callable[[], None],
        on_notification_action: Callable[[Any], None] | None = None,
    ) -> None:
        self.root = root
        self.on_show = on_show
        self.on_exit = on_exit
        self.on_notification_action = on_notification_action
        self._queue: queue.SimpleQueue[tuple[str, Any]] = queue.SimpleQueue()
        self._tray: Any | None = None
        self._tray_thread: threading.Thread | None = None
        self._tray_available = False
        self._notification_class: Any | None = None
        self._notifications_loaded = False
        self._notifications_available = False
        self._latest_notification: Any | None = None
        self._closed = False
        self._errors: list[str] = []
        self._error_lock = threading.Lock()
        if IS_WINDOWS:
            self._load_notifications()

    @property
    def tray_available(self) -> bool:
        return self._tray_available and not self._closed

    @property
    def notifications_available(self) -> bool:
        """Whether toast dependencies/submission are available, not OS policy."""
        return self._notifications_available and not self._closed

    @property
    def errors(self) -> list[str]:
        with self._error_lock:
            return list(self._errors)

    @property
    def last_error(self) -> str | None:
        with self._error_lock:
            return self._errors[-1] if self._errors else None

    def _record_error(self, message: str, error: BaseException | None = None) -> None:
        detail = f"{message}: {error}" if error is not None else message
        with self._error_lock:
            self._errors.append(detail)
            del self._errors[:-20]
        LOGGER.warning("%s", detail)

    def _load_notifications(self) -> None:
        if self._notifications_loaded or not IS_WINDOWS:
            return
        self._notifications_loaded = True
        try:
            self._notification_class = importlib.import_module("winotify").Notification
            self._notifications_available = True
        except Exception as exc:
            self._record_error("Không có thông báo Windows; dùng danh sách nhắc trong ứng dụng", exc)

    def _enqueue(self, action: str, payload: Any = None) -> None:
        if not self._closed:
            self._queue.put((action, payload))

    def process_pending(self) -> int:
        """Dispatch at most 100 tray actions.  Call only on the Tk main thread."""
        processed = 0
        while processed < 100:
            try:
                action, payload = self._queue.get_nowait()
            except queue.Empty:
                break
            if self._closed:
                continue
            try:
                if action == "show":
                    self.on_show()
                elif action == "exit":
                    self.on_exit()
                elif action == "notification":
                    if self.on_notification_action is not None and payload is not None:
                        self.on_notification_action(payload)
                    else:
                        self.on_show()
                processed += 1
            except Exception as exc:
                self._record_error("Không xử lý được thao tác khay hệ thống", exc)
        return processed

    def start_tray(self) -> bool:
        """Start optional pystray on Windows; wait up to 2s for native readiness."""
        if self._closed or not IS_WINDOWS:
            return False
        if self.tray_available:
            return True
        if self._tray_thread is not None and self._tray_thread.is_alive():
            return False
        try:
            pystray = importlib.import_module("pystray")
            image_module = importlib.import_module("PIL.Image")
            draw_module = importlib.import_module("PIL.ImageDraw")
            image = image_module.new("RGB", (64, 64), "#08775b")
            draw = draw_module.Draw(image)
            draw.rounded_rectangle((12, 13, 52, 53), radius=6, outline="white", width=3)
            draw.line((23, 9, 23, 20), fill="white", width=3)
            draw.line((41, 9, 41, 20), fill="white", width=3)
            draw.line((22, 35, 29, 42, 43, 28), fill="white", width=4)
            menu = pystray.Menu(
                pystray.MenuItem("Mở ứng dụng", lambda *_: self._enqueue("show"), default=True),
                pystray.MenuItem(
                    "Thông báo gần nhất",
                    lambda *_: self._enqueue("notification", self._latest_notification),
                    visible=lambda _item: self._latest_notification is not None,
                ),
                pystray.MenuItem("Thoát hẳn", lambda *_: self._enqueue("exit")),
            )
            icon = pystray.Icon("NhacViecAnhHaMoi", image, "Nhắc việc anh Hà", menu)
        except Exception as exc:
            self._record_error("Không khởi tạo được khay hệ thống", exc)
            return False

        ready = threading.Event()
        cancelled = threading.Event()
        self._tray = icon

        def setup(native_icon: Any) -> None:
            if cancelled.is_set() or self._closed:
                native_icon.stop()
                ready.set()
                return
            try:
                native_icon.visible = True
                self._tray_available = True
            except Exception as exc:
                self._record_error("Không hiển thị được biểu tượng khay hệ thống", exc)
                native_icon.stop()
            finally:
                ready.set()

        def run() -> None:
            had_tray = False
            try:
                icon.run(setup=setup)
                had_tray = self._tray_available
            except Exception as exc:
                had_tray = self._tray_available
                self._record_error("Khay hệ thống dừng do lỗi", exc)
            finally:
                self._tray_available = False
                ready.set()
                # A withdrawn window must not disappear when its tray crashes.
                if had_tray and not self._closed:
                    self._enqueue("show")

        self._tray_thread = threading.Thread(target=run, name="nhacviec-tray", daemon=True)
        self._tray_thread.start()
        if not ready.wait(timeout=2.0):
            cancelled.set()
            self._record_error("Khay hệ thống chưa sẵn sàng; dùng nút thu nhỏ trên thanh tác vụ")
            try:
                icon.stop()
            except Exception as exc:
                self._record_error("Không dừng được khay hệ thống chưa sẵn sàng", exc)
            return False
        return self.tray_available

    def notify(self, notification: Any) -> bool:
        """Submit a Windows toast, or return False for the caller's fallback UI."""
        self._latest_notification = notification
        if self._closed or not IS_WINDOWS:
            return False
        self._load_notifications()
        if self._notification_class is None:
            return False
        try:
            toast = self._notification_class(
                app_id="Nhắc việc anh Hà",
                title=str(getattr(notification, "title", "Nhắc việc")),
                msg=str(getattr(notification, "message", "")),
                duration="long",
            )
            toast.show()
            self._notifications_available = True
            return True
        except Exception as exc:
            self._notifications_available = False
            self._record_error("Không gửi được thông báo Windows; dùng nhắc trong ứng dụng", exc)
            return False

    def minimize(self) -> None:
        """Withdraw only when a ready tray can bring the application back."""
        if self.tray_available:
            try:
                self.root.withdraw()
                return
            except Exception as exc:
                self._record_error("Không ẩn được cửa sổ vào khay hệ thống", exc)
        try:
            self.root.iconify()
        except Exception as exc:
            self._record_error("Không thu nhỏ được cửa sổ", exc)

    def stop(self) -> None:
        """Stop native resources without ever destroying the Tk root itself."""
        if self._closed:
            return
        self._closed = True
        self._tray_available = False
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception as exc:
                self._record_error("Không dừng được khay hệ thống", exc)
        if self._tray_thread is not None and self._tray_thread is not threading.current_thread():
            self._tray_thread.join(timeout=0.5)
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

