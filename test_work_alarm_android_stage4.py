import unittest
from pathlib import Path


ROOT = Path(__file__).parent
PLUGIN = ROOT / "extensions" / "work_alarm" / "src" / "flutter" / "work_alarm"
ANDROID = PLUGIN / "android"
KOTLIN = ANDROID / "src" / "main" / "kotlin" / "com" / "buscalendar" / "work_alarm"


class WorkAlarmAndroidStage4Tests(unittest.TestCase):
    def read_kotlin(self, name):
        return (KOTLIN / name).read_text(encoding="utf-8")

    def test_manifest_declares_android_14_media_playback_service(self):
        manifest = (ANDROID / "src" / "main" / "AndroidManifest.xml").read_text(
            encoding="utf-8"
        )
        self.assertIn("android.permission.FOREGROUND_SERVICE", manifest)
        self.assertIn(
            "android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK", manifest
        )
        self.assertIn('android:foregroundServiceType="mediaPlayback"', manifest)
        self.assertIn("com.buscalendar.work_alarm.AlarmRingingService", manifest)
        self.assertNotIn("android:process=", manifest)

    def test_manifest_registers_alarm_and_stop_receivers(self):
        manifest = (ANDROID / "src" / "main" / "AndroidManifest.xml").read_text(
            encoding="utf-8"
        )
        self.assertIn("com.buscalendar.work_alarm.AlarmReceiver", manifest)
        self.assertIn("com.buscalendar.work_alarm.StopAlarmReceiver", manifest)
        self.assertIn("android.permission.POST_NOTIFICATIONS", manifest)
        self.assertIn("android.permission.VIBRATE", manifest)

    def test_ringing_service_is_not_sticky_and_never_redelivers(self):
        source = self.read_kotlin("AlarmRingingService.kt")
        self.assertIn("return START_NOT_STICKY", source)
        self.assertNotIn("START_STICKY", source.replace("START_NOT_STICKY", ""))
        self.assertNotIn("START_REDELIVER_INTENT", source)

    def test_ringing_repeats_sound_and_vibration_until_stopped(self):
        source = self.read_kotlin("AlarmRingingService.kt")
        self.assertIn("isLooping = true", source)
        self.assertIn("VibrationEffect.createWaveform(pattern, 0)", source)
        self.assertIn("vibrator?.cancel()", source)
        self.assertIn("mediaPlayer?.runCatching", source)
        self.assertIn('"알람 끄기"', source)

    def test_alarm_receiver_records_start_failure_without_deleting_alarm(self):
        source = self.read_kotlin("AlarmReceiver.kt")
        self.assertIn("startForegroundService", source)
        self.assertIn("AlarmStore(context).recordFailure", source)
        self.assertIn("System.currentTimeMillis()", source)
        self.assertNotIn("writeSnapshot", source)
        self.assertNotIn("remove", source.lower())

    def test_stop_receiver_stops_service(self):
        source = self.read_kotlin("StopAlarmReceiver.kt")
        self.assertIn("context.stopService", source)
        self.assertIn("AlarmRingingService::class.java", source)

    def test_boot_receiver_still_does_not_start_ringing_service(self):
        source = self.read_kotlin("BootReceiver.kt")
        self.assertNotIn("AlarmRingingService", source)
        self.assertNotIn("startForegroundService", source)
        self.assertNotIn("startService", source)

    def test_native_stop_method_is_connected(self):
        kotlin = self.read_kotlin("WorkAlarmPlugin.kt")
        dart = (PLUGIN / "lib" / "src" / "work_alarm_service.dart").read_text(
            encoding="utf-8"
        )
        self.assertIn('"stopRinging"', kotlin)
        self.assertIn('"stopRinging"', dart)

    def test_alarm_lifecycle_has_diagnostic_logs(self):
        receiver = self.read_kotlin("AlarmReceiver.kt")
        service = self.read_kotlin("AlarmRingingService.kt")
        stop_receiver = self.read_kotlin("StopAlarmReceiver.kt")

        self.assertIn('private const val TAG = "AlarmReceiver"', receiver)
        self.assertIn('"alarm received alarm_id=$alarmId', receiver)
        self.assertIn('"service start requested alarm_id=$alarmId"', receiver)

        self.assertIn('private const val TAG = "AlarmService"', service)
        self.assertIn('"start requested alarm_id=$alarmId', service)
        self.assertIn('"ringtone started alarm_id=$alarmId"', service)
        self.assertIn('"vibration started alarm_id=$alarmId"', service)
        self.assertIn('"started alarm_id=$alarmId"', service)
        self.assertIn('"stopped"', service)

        self.assertIn('private const val TAG = "StopAlarmReceiver"', stop_receiver)
        self.assertIn('"stop requested alarm_id=$alarmId"', stop_receiver)

    def test_failures_are_logged_and_saved_to_diagnostics(self):
        receiver = self.read_kotlin("AlarmReceiver.kt")
        service = self.read_kotlin("AlarmRingingService.kt")
        store = self.read_kotlin("AlarmStore.kt")

        self.assertIn("Log.e(TAG, reason, error)", receiver)
        self.assertIn("Log.e(TAG, reason, error)", service)
        self.assertIn('"failure recorded at=$at reason=$reason"', store)


if __name__ == "__main__":
    unittest.main()
