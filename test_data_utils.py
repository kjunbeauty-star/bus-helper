import unittest

from data_utils import DEFAULT_INPUT_DATA, format_phone, normalize_contacts, normalize_input_data, normalize_schedules


class DataUtilsTests(unittest.TestCase):
    def test_partial_input_data_is_merged_with_defaults(self):
        result = normalize_input_data({"route": "101"})
        self.assertEqual(result["route"], "101")
        self.assertEqual(result["back_phone"], DEFAULT_INPUT_DATA["back_phone"])
        self.assertEqual(result["relief_driver"], "미입력")
        self.assertEqual(result["relief_phone"], "미입력")

    def test_relief_driver_data_is_preserved(self):
        result = normalize_input_data({"relief_driver": "홍길동", "relief_phone": "010-1234-5678"})
        self.assertEqual(result["relief_driver"], "홍길동")
        self.assertEqual(result["relief_phone"], "010-1234-5678")

    def test_malformed_schedule_rows_are_dropped(self):
        result = normalize_schedules({
            "2026-08-03": None,
            "not-a-date": {"status": "오전"},
            "2026-08-04": {"status": "오후"},
        })
        self.assertEqual(result, {"2026-08-04": {
            "status": "오후", "start_time": "", "order_no": "",
            "alarm_mode": "", "alarm_offset_minutes": 0, "alarm_time": "",
        }})

    def test_date_alarm_fields_are_preserved(self):
        result = normalize_schedules({
            "2026-08-04": {
                "status": "오후", "start_time": "16:25", "order_no": "6",
                "alarm_mode": "relative", "alarm_offset_minutes": 90,
            }
        })
        self.assertEqual(result["2026-08-04"]["alarm_mode"], "relative")
        self.assertEqual(result["2026-08-04"]["alarm_offset_minutes"], 90)

    def test_phone_format_supports_seoul_and_mobile_numbers(self):
        self.assertEqual(format_phone("0212345678"), "02-1234-5678")
        self.assertEqual(format_phone("01012345678"), "010-1234-5678")

    def test_phone_format_supports_eight_digit_service_numbers(self):
        self.assertEqual(format_phone("18338500"), "1833-8500")
        self.assertEqual(format_phone("15442399"), "1544-2399")

    def test_phone_format_does_not_truncate_unexpected_length(self):
        self.assertEqual(format_phone("123456789012"), "123456789012")

    def test_malformed_contacts_are_dropped(self):
        self.assertEqual(
            normalize_contacts([None, "bad", {"name": " 기사 ", "phone": "010-1234-5678", "is_edit": True}]),
            [{"name": "기사", "phone": "010-1234-5678", "is_edit": False}],
        )

    def test_existing_eight_digit_contact_is_normalized_on_load(self):
        self.assertEqual(
            normalize_contacts([{"name": "단말기 A/S", "phone": "18338500"}]),
            [{"name": "단말기 A/S", "phone": "1833-8500", "is_edit": False}],
        )


if __name__ == "__main__":
    unittest.main()
