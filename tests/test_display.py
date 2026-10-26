"""DPI initialization contracts; no display or native Windows calls required."""
from pathlib import Path
import unittest
from unittest.mock import Mock, call, patch
from xml.etree import ElementTree

from nhacviec import display


class DisplayInitializationTests(unittest.TestCase):
    def api(self, awareness=("unaware", "per-monitor-v2")):
        api = Mock()
        api.query_awareness.side_effect = awareness
        api.set_per_monitor_v2.return_value = (True, 0)
        api.set_per_monitor.return_value = (True, 0)
        api.set_system.return_value = (True, 0)
        api.window_awareness.return_value = "per-monitor-v2"
        return api

    def test_non_windows_leaves_platform_and_scaling_untouched(self):
        root = Mock()
        with patch.object(display, "IS_WINDOWS", False), patch.object(display, "_WindowsDpiApi") as native:
            self.assertEqual(display.initialize_display().awareness, "not-applicable")
            self.assertIsNone(display.sync_tk_scaling(root))
        native.assert_not_called()
        root.tk.call.assert_not_called()

    def test_manifest_v2_policy_is_preserved_without_resetting_process(self):
        api = self.api(("per-monitor-v2",))
        with patch.object(display, "IS_WINDOWS", True), patch.object(display, "_WindowsDpiApi", return_value=api):
            status = display.initialize_display()
        self.assertEqual(status.awareness, "per-monitor-v2")
        self.assertEqual(status.source, "existing-policy")
        api.set_per_monitor_v2.assert_not_called()
        api.set_per_monitor.assert_not_called()
        api.set_system.assert_not_called()

    def test_source_run_requests_v2_before_trying_any_legacy_api(self):
        api = self.api()
        with patch.object(display, "IS_WINDOWS", True), patch.object(display, "_WindowsDpiApi", return_value=api):
            status = display.initialize_display()
        self.assertTrue(status.dpi_aware)
        self.assertEqual(status.awareness, "per-monitor-v2")
        self.assertEqual(api.mock_calls, [call.query_awareness(), call.set_per_monitor_v2(), call.query_awareness()])

    def test_missing_v2_api_falls_back_to_per_monitor(self):
        api = self.api(("unaware", "per-monitor"))
        api.set_per_monitor_v2.return_value = None
        with patch.object(display, "IS_WINDOWS", True), patch.object(display, "_WindowsDpiApi", return_value=api):
            status = display.initialize_display()
        self.assertEqual(status.awareness, "per-monitor")
        api.set_per_monitor.assert_called_once()
        api.set_system.assert_not_called()

    def test_locked_python_host_reports_actual_system_policy_not_v2_success(self):
        api = self.api(("system", "system"))
        api.set_per_monitor_v2.return_value = (False, display.ERROR_ACCESS_DENIED)
        with patch.object(display, "IS_WINDOWS", True), patch.object(display, "_WindowsDpiApi", return_value=api):
            status = display.initialize_display()
        self.assertEqual(status.awareness, "system")
        self.assertEqual(status.source, "existing-policy")
        self.assertIn("0x00000005", status.error)
        api.set_per_monitor.assert_not_called()
        api.set_system.assert_not_called()

    def test_locked_shcore_fallback_does_not_attempt_a_late_system_downgrade(self):
        api = self.api(("unaware", "per-monitor"))
        api.set_per_monitor_v2.return_value = None
        api.set_per_monitor.return_value = (False, display.E_ACCESSDENIED)
        with patch.object(display, "IS_WINDOWS", True), patch.object(display, "_WindowsDpiApi", return_value=api):
            status = display.initialize_display()
        self.assertEqual(status.awareness, "per-monitor")
        api.set_system.assert_not_called()

    def test_unavailable_apis_do_not_claim_native_rendering(self):
        api = self.api(("unaware", "unaware"))
        api.set_per_monitor_v2.return_value = None
        api.set_per_monitor.return_value = None
        api.set_system.return_value = None
        with patch.object(display, "IS_WINDOWS", True), patch.object(display, "_WindowsDpiApi", return_value=api):
            status = display.initialize_display()
        self.assertFalse(status.dpi_aware)
        self.assertEqual(status.awareness, "unaware")
        self.assertEqual(status.source, "unavailable")

    def test_native_loading_failure_remains_reportable_without_crashing_startup(self):
        with patch.object(display, "IS_WINDOWS", True), patch.object(display, "_WindowsDpiApi", side_effect=OSError("blocked")):
            status = display.initialize_display()
        self.assertFalse(status.dpi_aware)
        self.assertEqual(status.awareness, "unknown")
        self.assertIn("blocked", status.error)

    def test_current_window_dpi_sets_points_to_pixels_using_the_real_user_scale(self):
        api = self.api()
        api.window_dpi.return_value = 144
        root = Mock()
        root.winfo_id.return_value = 1234
        with patch.object(display, "IS_WINDOWS", True), patch.object(display, "_WindowsDpiApi", return_value=api):
            self.assertEqual(display.sync_tk_scaling(root), 144)
        api.window_dpi.assert_called_once_with(1234)
        root.tk.call.assert_called_once_with("tk", "scaling", 2.0)

    def test_missing_window_dpi_keeps_tks_platform_default(self):
        api = self.api()
        api.window_dpi.return_value = None
        root = Mock()
        with patch.object(display, "IS_WINDOWS", True), patch.object(display, "_WindowsDpiApi", return_value=api):
            self.assertIsNone(display.sync_tk_scaling(root))
        root.tk.call.assert_not_called()

    def test_report_distinguishes_actual_monitor_dpi_from_simulated_tk_scale(self):
        api = self.api(("per-monitor-v2",))
        api.window_dpi.return_value = 96
        root = Mock()
        root.winfo_id.return_value = 1234
        root.tk.call.return_value = 2.0
        with patch.object(display, "IS_WINDOWS", True), patch.object(display, "_WindowsDpiApi", return_value=api):
            state = display.get_display_state(root)
        self.assertEqual(state["awareness"], "per-monitor-v2")
        self.assertEqual(state["awareness_level"], 2)
        self.assertTrue(state["per_monitor_v2"])
        self.assertEqual(state["window_awareness"], "per-monitor-v2")
        self.assertEqual(state["window_dpi"], 96)
        self.assertEqual(state["tk_scaling"], 2.0)
        api.set_per_monitor_v2.assert_not_called()


class PackagedManifestTests(unittest.TestCase):
    def test_packaged_executable_declares_native_per_monitor_rendering(self):
        project = Path(__file__).resolve().parents[1]
        manifest = ElementTree.parse(project / "packaging" / "NhacViecAnhHa.manifest").getroot()
        def text(namespace, element):
            return manifest.find(f".//{{{namespace}}}{element}").text
        self.assertEqual(text("http://schemas.microsoft.com/SMI/2005/WindowsSettings", "dpiAware"), "true/pm")
        self.assertEqual(text("http://schemas.microsoft.com/SMI/2016/WindowsSettings", "dpiAwareness"), "PerMonitorV2,PerMonitor")
        self.assertEqual(text("http://schemas.microsoft.com/SMI/2017/WindowsSettings", "gdiScaling"), "false")


if __name__ == "__main__":
    unittest.main()
