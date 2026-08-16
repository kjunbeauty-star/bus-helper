import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).parent
PLUGIN = ROOT / "extensions" / "work_alarm" / "src" / "flutter" / "work_alarm"
ANDROID = PLUGIN / "android"
KOTLIN = ANDROID / "src" / "main" / "kotlin" / "com" / "buscalendar" / "work_alarm"


class WorkAlarmAndroidStage3Tests(unittest.TestCase):
    def read_kotlin(self, name):
        return (KOTLIN / name).read_text(encoding="utf-8")

    def test_flutter_plugin_registration_is_persistent_source(self):
        pubspec = (PLUGIN / "pubspec.yaml").read_text(encoding="utf-8")
        self.assertIn("package: com.buscalendar.work_alarm", pubspec)
        self.assertIn("pluginClass: WorkAlarmPlugin", pubspec)

    def test_manifest_keeps_boot_and_exact_alarm_contract(self):
        manifest_path = ANDROID / "src" / "main" / "AndroidManifest.xml"
        root = ET.parse(manifest_path).getroot()
        xml = manifest_path.read_text(encoding="utf-8")
        self.assertEqual(root.tag, "manifest")
        self.assertIn("android.permission.RECEIVE_BOOT_COMPLETED", xml)
        self.assertIn("android.permission.SCHEDULE_EXACT_ALARM", xml)
        self.assertIn("com.buscalendar.work_alarm.BootReceiver", xml)

    def test_boot_receiver_only_restores_future_reservations(self):
        source = self.read_kotlin("BootReceiver.kt")
        self.assertIn("alarm.triggerAt > now", source)
        self.assertIn("scheduler.schedule(alarm)", source)
        self.assertNotIn("AlarmRingingService", source)
        self.assertNotIn("startForegroundService", source)
        self.assertNotIn("startService", source)

    def test_alarm_store_persists_required_native_fields(self):
        source = self.read_kotlin("AlarmStore.kt")
        for field in ("alarm_id", "request_code", "trigger_at"):
            self.assertIn(f'"{field}"', source)
        self.assertIn('"snapshot_json"', source)
        self.assertIn('"last_failure_reason"', source)
        self.assertIn('"last_failure_at"', source)

    def test_scheduler_uses_exact_idle_alarm_and_stable_request_code(self):
        source = self.read_kotlin("AlarmScheduler.kt")
        self.assertIn("setExactAndAllowWhileIdle", source)
        self.assertIn("alarm.requestCode", source)
        self.assertIn("PendingIntent.FLAG_IMMUTABLE", source)
        self.assertIn("canScheduleExactAlarms", source)

    def test_native_plugin_exposes_stage3_contract(self):
        source = self.read_kotlin("WorkAlarmPlugin.kt")
        for method in (
            "getPermissionStatus",
            "getNativeSnapshot",
            "reconcile",
            "cancelAll",
        ):
            self.assertIn(f'"{method}"', source)


if __name__ == "__main__":
    unittest.main()
