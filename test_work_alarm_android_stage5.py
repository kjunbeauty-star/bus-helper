import unittest
from pathlib import Path


ROOT = Path(__file__).parent
PLUGIN = ROOT / "extensions" / "work_alarm" / "src" / "flutter" / "work_alarm"
KOTLIN = PLUGIN / "android" / "src" / "main" / "kotlin" / "com" / "buscalendar" / "work_alarm"


class WorkAlarmAndroidStage5Tests(unittest.TestCase):
    def read(self, name):
        return (KOTLIN / name).read_text(encoding="utf-8")

    def test_notification_permission_uses_runtime_request_and_result(self):
        source = self.read("WorkAlarmPlugin.kt")
        self.assertIn("Manifest.permission.POST_NOTIFICATIONS", source)
        self.assertIn("ActivityCompat.requestPermissions", source)
        self.assertIn("onRequestPermissionsResult", source)
        self.assertIn('"requestNotificationPermission"', source)

    def test_exact_alarm_settings_rechecks_after_activity_result(self):
        source = self.read("WorkAlarmPlugin.kt")
        self.assertIn("Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM", source)
        self.assertIn("startActivityForResult", source)
        self.assertIn("onActivityResult", source)
        self.assertIn('"openExactAlarmSettings"', source)

    def test_permission_and_reconcile_logs_are_stable(self):
        source = self.read("WorkAlarmPlugin.kt")
        self.assertIn('private const val PERMISSION_TAG = "Permission"', source)
        self.assertIn('"Notification granted"', source)
        self.assertIn('"Exact alarm granted"', source)
        self.assertIn('private const val RECONCILE_TAG = "Reconcile"', source)
        self.assertIn('"started"', source)
        self.assertIn('"scheduled=$scheduled updated=$updated cancelled=$cancelled"', source)

    def test_test_alarm_dispatches_receiver_without_reservation(self):
        source = self.read("WorkAlarmPlugin.kt")
        self.assertIn('"testAlarm"', source)
        self.assertIn("setClass(context, AlarmReceiver::class.java)", source)
        self.assertIn("context.sendBroadcast(intent)", source)
        self.assertIn('private const val TEST_ALARM_TAG = "TestAlarm"', source)
        self.assertNotIn("scheduler.schedule", source[source.index("private fun testAlarm"):])

    def test_diagnostics_include_sync_and_current_alarm(self):
        store = self.read("AlarmStore.kt")
        service = self.read("AlarmRingingService.kt")
        self.assertIn('put("last_sync_at"', store)
        self.assertIn('put("current_alarm_id"', store)
        self.assertIn("setCurrentAlarm(alarmId)", service)
        self.assertIn("setCurrentAlarm(null)", service)

    def test_failed_exact_alarms_are_not_marked_as_reserved(self):
        source = self.read("WorkAlarmPlugin.kt")
        self.assertIn("val persisted = mutableListOf<StoredAlarm>()", source)
        self.assertIn("persisted.add(alarm)", source)
        self.assertIn('"reserved_count" to persisted.size', source)

    def test_native_stop_always_clears_current_alarm_diagnostic(self):
        plugin = self.read("WorkAlarmPlugin.kt")
        stop_receiver = self.read("StopAlarmReceiver.kt")
        self.assertIn("AlarmStore(context).setCurrentAlarm(null)", plugin)
        self.assertIn("AlarmStore(context).setCurrentAlarm(null)", stop_receiver)

    def test_full_screen_alarm_activity_and_permission_are_declared(self):
        manifest = (PLUGIN / "android" / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
        plugin = self.read("WorkAlarmPlugin.kt")
        service = self.read("AlarmRingingService.kt")
        activity = self.read("AlarmActivity.kt")
        self.assertIn("android.permission.USE_FULL_SCREEN_INTENT", manifest)
        self.assertIn("AlarmActivity", manifest)
        self.assertIn('android:showWhenLocked="true"', manifest)
        self.assertIn("canUseFullScreenIntent", plugin)
        self.assertIn("ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT", plugin)
        self.assertIn("setFullScreenIntent", service)
        self.assertIn('text = "알람 끄기"', activity)
        self.assertIn("stopService(Intent(this, AlarmRingingService::class.java))", activity)


if __name__ == "__main__":
    unittest.main()
