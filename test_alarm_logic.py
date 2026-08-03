import unittest
from datetime import date, datetime, timedelta, timezone

from alarm_logic import build_desired_alarms, build_reconcile_plan
from alarm_models import AlarmEntry, AlarmSettings


KST = timezone(timedelta(hours=9))


class AlarmLogicTests(unittest.TestCase):
    def test_only_morning_and_afternoon_create_alarms(self):
        statuses = {"2026-08-03": "오전", "2026-08-04": "오후", "2026-08-05": "휴무"}
        alarms = build_desired_alarms(
            start_date=date(2026, 8, 3), days=3,
            get_day_info=lambda key: {"status": statuses[key]},
            settings=AlarmSettings(enabled=True, morning_time="05:30", afternoon_time="12:40"),
            timezone=KST, now=datetime(2026, 8, 3, 1, 0, tzinfo=KST),
        )
        self.assertEqual([alarm.shift for alarm in alarms], ["morning", "afternoon"])
        self.assertEqual([alarm.request_code for alarm in alarms], [202608031, 202608042])

    def test_disabled_alarm_returns_empty_snapshot(self):
        alarms = build_desired_alarms(
            start_date=date(2026, 8, 3), days=90,
            get_day_info=lambda key: {"status": "오전"},
            settings=AlarmSettings(enabled=False), timezone=KST,
            now=datetime(2026, 8, 3, 1, 0, tzinfo=KST),
        )
        self.assertEqual(alarms, [])

    def test_individual_shift_can_be_disabled(self):
        alarms = build_desired_alarms(
            start_date=date(2026, 8, 3), days=2,
            get_day_info=lambda key: {"status": "오전" if key.endswith("03") else "오후"},
            settings=AlarmSettings(enabled=True, morning_enabled=False, afternoon_enabled=True),
            timezone=KST, now=datetime(2026, 8, 3, 1, 0, tzinfo=KST),
        )
        self.assertEqual([alarm.shift for alarm in alarms], ["afternoon"])

    def test_past_trigger_is_not_scheduled(self):
        alarms = build_desired_alarms(
            start_date=date(2026, 8, 3), days=1,
            get_day_info=lambda key: {"status": "오전"},
            settings=AlarmSettings(enabled=True, morning_time="05:30"), timezone=KST,
            now=datetime(2026, 8, 3, 6, 0, tzinfo=KST),
        )
        self.assertEqual(alarms, [])

    def test_horizon_is_exactly_ninety_dates(self):
        alarms = build_desired_alarms(
            start_date=date(2026, 8, 3), days=90,
            get_day_info=lambda key: {"status": "오전"},
            settings=AlarmSettings(enabled=True), timezone=KST,
            now=datetime(2026, 8, 2, 23, 0, tzinfo=KST),
        )
        self.assertEqual(len(alarms), 90)
        self.assertEqual(alarms[0].date, "2026-08-03")
        self.assertEqual(alarms[-1].date, "2026-10-31")

    def test_ids_and_request_codes_are_unique(self):
        alarms = build_desired_alarms(
            start_date=date(2026, 8, 3), days=90,
            get_day_info=lambda key: {"status": "오전" if int(key[-2:]) % 2 else "오후"},
            settings=AlarmSettings(enabled=True), timezone=KST,
            now=datetime(2026, 8, 2, 23, 0, tzinfo=KST),
        )
        self.assertEqual(len({alarm.alarm_id for alarm in alarms}), len(alarms))
        self.assertEqual(len({alarm.request_code for alarm in alarms}), len(alarms))

    def test_reconcile_classifies_all_changes(self):
        base = AlarmEntry("2026-08-03:morning", 202608031, "2026-08-03", "morning", "오전", 1000, "오전근무 알람", "오늘은 오전근무입니다.")
        changed = AlarmEntry("2026-08-04:afternoon", 202608042, "2026-08-04", "afternoon", "오후", 3000, "오후근무 알람", "오늘은 오후근무입니다.")
        old_changed = AlarmEntry("2026-08-04:afternoon", 202608042, "2026-08-04", "afternoon", "오후", 2000, "오후근무 알람", "오늘은 오후근무입니다.")
        removed = AlarmEntry("2026-08-05:morning", 202608051, "2026-08-05", "morning", "오전", 4000, "오전근무 알람", "오늘은 오전근무입니다.")
        added = AlarmEntry("2026-08-06:morning", 202608061, "2026-08-06", "morning", "오전", 5000, "오전근무 알람", "오늘은 오전근무입니다.")
        plan = build_reconcile_plan([base, changed, added], [base, old_changed, removed])
        self.assertEqual([item.alarm_id for item in plan.unchanged], [base.alarm_id])
        self.assertEqual([item.alarm_id for item in plan.update], [changed.alarm_id])
        self.assertEqual([item.alarm_id for item in plan.schedule], [added.alarm_id])
        self.assertEqual([item.alarm_id for item in plan.cancel], [removed.alarm_id])

    def test_models_round_trip(self):
        settings = AlarmSettings(enabled=True, morning_time="5:07")
        self.assertEqual(settings.morning_time, "05:07")
        self.assertEqual(AlarmSettings.from_dict(settings.to_dict()), settings)
        entry = AlarmEntry("2026-08-03:morning", 202608031, "2026-08-03", "morning", "오전", 1000, "제목", "내용")
        self.assertEqual(AlarmEntry.from_dict(entry.to_dict()), entry)

    def test_invalid_time_is_rejected(self):
        with self.assertRaises(ValueError):
            AlarmSettings(enabled=True, morning_time="25:00")


if __name__ == "__main__":
    unittest.main()
