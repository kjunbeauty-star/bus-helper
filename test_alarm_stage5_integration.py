import unittest
from pathlib import Path


MAIN = (Path(__file__).parent / "main.py").read_text(encoding="utf-8")


class AlarmStage5IntegrationTests(unittest.TestCase):
    def test_android_service_is_platform_guarded(self):
        self.assertIn("alarm_service = WorkAlarmService() if is_native_android", MAIN)
        self.assertIn('"reason": "android_only"', MAIN)

    def test_reconcile_runs_for_required_changes(self):
        for reason in (
            "app_start", "enabled", "morning_enabled", "afternoon_enabled",
            "morning_time", "afternoon_time", "notification_permission",
            "exact_alarm_permission", "schedule_saved", "schedule_deleted",
            "work_pattern_applied", "work_pattern_cleared", "schedule_reset",
        ):
            self.assertIn(reason, MAIN)

    def test_settings_show_required_diagnostics_and_test_action(self):
        for label in (
            "알람 사용", "오전근무", "오후근무", "알림 권한",
            "정확한 알람 권한", "지금 울려보기", "현재 알람 끄기", "마지막 동기화",
            "예약된 알람", "현재 울리는 알람",
        ):
            self.assertIn(label, MAIN)

    def test_snapshot_is_rolling_ninety_days(self):
        self.assertIn("build_desired_alarms(", MAIN)
        self.assertIn("days=90", MAIN)
        self.assertIn('"alarms": [alarm.to_dict() for alarm in alarms]', MAIN)

    def test_stop_button_stops_test_and_scheduled_ringing(self):
        self.assertIn("async def stop_alarm_now", MAIN)
        self.assertIn("await alarm_service.stop_ringing()", MAIN)
        self.assertIn('alarm_runtime_state["current_alarm_id"] = None', MAIN)
        self.assertIn('if key == "enabled" and not value:', MAIN)

    def test_date_popup_supports_relative_and_direct_alarm(self):
        for value in ("relative_30", "relative_60", "relative_90", "relative_120", "direct"):
            self.assertIn(value, MAIN)
        self.assertIn("첫탕 시간을 먼저 선택하거나 직접 시간을 입력하세요.", MAIN)
        self.assertIn('"alarm_offset_minutes": alarm_offset', MAIN)


    def test_calendar_marks_explicit_date_alarms(self):
        self.assertIn(
            'day_info.get("alarm_mode", "") in ("relative", "direct")',
            MAIN,
        )
        self.assertIn("ft.Icon(ft.Icons.ALARM", MAIN)

    def test_direct_alarm_accepts_four_digits_and_inserts_colon(self):
        self.assertIn("def parse_direct_alarm_time(value):", MAIN)
        self.assertIn('f"{digits[:2]}:{digits[2:]}" if len(digits) == 4', MAIN)
        self.assertIn("keyboard_type=ft.KeyboardType.NUMBER", MAIN)
        self.assertIn("alarm_time = parse_direct_alarm_time(candidate)", MAIN)


    def test_expired_date_alarm_is_cleared_on_resume_and_redraw(self):
        self.assertIn("def clear_expired_date_alarms", MAIN)
        self.assertIn('info["alarm_mode"] = ""', MAIN)
        self.assertIn('info["alarm_time"] = ""', MAIN)
        self.assertIn('reconcile_alarms("app_resumed")', MAIN)
        self.assertIn("page.on_app_lifecycle_state_change", MAIN)


if __name__ == "__main__":
    unittest.main()
