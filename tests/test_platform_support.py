"""Portable contract tests. Native Windows tray/toast behavior needs Windows QA."""

from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from nhacviec.platform_support import InstanceLock, PlatformSupport
from nhacviec import platform_support


class InstanceLockTests(unittest.TestCase):
    def test_excludes_second_owner_and_releases_without_deleting_file(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = InstanceLock(directory), InstanceLock(directory)
            try:
                self.assertTrue(first.acquire())
                self.assertTrue(first.acquire())
                self.assertFalse(second.acquire())
                self.assertTrue(first.path.is_file())
                first.close()
                self.assertTrue(first.path.is_file())
                self.assertTrue(second.acquire())
            finally:
                first.close()
                second.close()

    def test_context_releases_after_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "example"):
                with InstanceLock(directory):
                    raise ValueError("example")
            with InstanceLock(directory) as lock:
                self.assertTrue(lock.path.exists())

    def test_locks_are_scoped_to_new_application_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "NhacViecAnhHa" / "data" / "tasks.db"
            legacy.parent.mkdir(parents=True)
            legacy.write_bytes(b"legacy data")
            with InstanceLock(Path(directory) / "NhacViecAnhHaMoi"):
                self.assertEqual(legacy.read_bytes(), b"legacy data")


class PlatformSupportTests(unittest.TestCase):
    def make_support(self):
        self.root = Mock()
        self.show, self.exit, self.action = Mock(), Mock(), Mock()
        return PlatformSupport(self.root, self.show, self.exit, self.action)

    @patch.object(platform_support, "IS_WINDOWS", False)
    @patch.object(platform_support.importlib, "import_module")
    def test_linux_never_imports_native_modules_and_uses_taskbar(self, importer):
        importer.reset_mock()  # Exclude unittest.patch's own import resolution.
        support = self.make_support()
        self.assertFalse(support.start_tray())
        self.assertFalse(support.notify(SimpleNamespace(title="Test", message="Body")))
        support.minimize()
        self.root.iconify.assert_called_once()
        self.root.withdraw.assert_not_called()
        importer.assert_not_called()

    @patch("nhacviec.platform_support.IS_WINDOWS", False)
    def test_callbacks_wait_for_main_thread_queue_pump(self):
        support = self.make_support()
        notification = SimpleNamespace(title="Sample")
        worker = threading.Thread(target=lambda: (
            support._enqueue("show"),
            support._enqueue("notification", notification),
            support._enqueue("exit"),
        ))
        worker.start()
        worker.join()
        self.show.assert_not_called()
        self.action.assert_not_called()
        self.exit.assert_not_called()
        self.assertEqual(self.root.mock_calls, [])
        self.assertEqual(support.process_pending(), 3)
        self.show.assert_called_once()
        self.action.assert_called_once_with(notification)
        self.exit.assert_called_once()

    @patch("nhacviec.platform_support.IS_WINDOWS", True)
    def test_missing_dependencies_are_reported_and_not_hidden(self):
        with patch("nhacviec.platform_support.importlib.import_module", side_effect=ImportError("not installed")):
            support = self.make_support()
            self.assertFalse(support.notifications_available)
            self.assertFalse(support.start_tray())
            self.assertIn("not installed", support.last_error)
            self.assertFalse(support.notify(SimpleNamespace(title="Test", message="Body")))
        support.minimize()
        self.root.iconify.assert_called_once()

    @patch("nhacviec.platform_support.IS_WINDOWS", True)
    def test_toast_submission_preserves_vietnamese_content(self):
        toast_class = Mock()
        with patch("nhacviec.platform_support.importlib.import_module", return_value=SimpleNamespace(Notification=toast_class)):
            support = self.make_support()
        notification = SimpleNamespace(title="Lịch họp tháng", message="Bắt đầu lúc 09:00")
        self.assertTrue(support.notify(notification))
        toast_class.assert_called_once_with(
            app_id="Nhắc việc anh Hà", title="Lịch họp tháng", msg="Bắt đầu lúc 09:00", duration="long"
        )
        toast_class.return_value.show.assert_called_once()
        self.assertTrue(support.notifications_available)

    @patch("nhacviec.platform_support.IS_WINDOWS", True)
    def test_failed_toast_returns_false_for_visible_fallback(self):
        toast_class = Mock()
        toast_class.return_value.show.side_effect = OSError("policy")
        with patch("nhacviec.platform_support.importlib.import_module", return_value=SimpleNamespace(Notification=toast_class)):
            support = self.make_support()
        self.assertFalse(support.notify(SimpleNamespace(title="Test", message="Body")))
        self.assertFalse(support.notifications_available)
        self.assertIn("policy", support.last_error)

    @patch("nhacviec.platform_support.IS_WINDOWS", False)
    def test_only_ready_tray_can_hide_window(self):
        support = self.make_support()
        support._tray_available = True
        support.minimize()
        self.root.withdraw.assert_called_once()
        self.root.iconify.assert_not_called()
        self.root.withdraw.side_effect = RuntimeError("closed root")
        support.minimize()
        self.root.iconify.assert_called_once()

    @patch("nhacviec.platform_support.IS_WINDOWS", False)
    def test_shutdown_is_idempotent_and_discards_pending_callbacks(self):
        support = self.make_support()
        support._tray = Mock()
        support._enqueue("exit")
        support.stop()
        support.stop()
        support._tray.stop.assert_called_once()
        self.assertEqual(support.process_pending(), 0)
        self.exit.assert_not_called()
        support._enqueue("show")
        self.assertEqual(support.process_pending(), 0)
        self.assertFalse(support.notify(SimpleNamespace(title="Test", message="Body")))

    @patch("nhacviec.platform_support.IS_WINDOWS", True)
    def test_native_tray_ready_callbacks_queued_and_stop_closes_worker(self):
        class FakeIcon:
            def __init__(self, name, image, title, menu):
                self.menu = menu
                self.finished = threading.Event()
                self.visible = False

            def run(self, setup):
                setup(self)
                self.finished.wait(timeout=5)

            def stop(self):
                self.finished.set()

        fake_tray = SimpleNamespace(
            Menu=lambda *items: items,
            MenuItem=lambda label, action, **kwargs: SimpleNamespace(label=label, action=action, **kwargs),
            Icon=FakeIcon,
        )
        fake_modules = {
            "winotify": SimpleNamespace(Notification=Mock()),
            "pystray": fake_tray,
            "PIL.Image": SimpleNamespace(new=Mock(return_value=object())),
            "PIL.ImageDraw": SimpleNamespace(Draw=Mock(return_value=Mock())),
        }
        with patch("nhacviec.platform_support.importlib.import_module", side_effect=lambda name: fake_modules[name]):
            support = self.make_support()
            try:
                self.assertTrue(support.start_tray())
                self.assertTrue(support.tray_available)
                self.assertTrue(support.start_tray())  # No second native worker.
                support._tray.menu[0].action(None, None)
                self.show.assert_not_called()
                support.process_pending()
                self.show.assert_called_once()
                support.minimize()
                self.root.withdraw.assert_called_once()
            finally:
                support.stop()
            self.assertFalse(support.tray_available)
            self.assertFalse(support._tray_thread.is_alive())


if __name__ == "__main__":
    unittest.main()
