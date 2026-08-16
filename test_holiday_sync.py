import unittest
from datetime import datetime
from holiday_sync import build_holiday_payload, normalize_holiday_name, parse_official_holiday_xml, should_check_holidays

class HolidaySyncTests(unittest.TestCase):
    def test_parse_official_xml(self):
        xml = """<response><header><resultCode>00</resultCode></header><body><items><item><dateName>광복절</dateName><isHoliday>Y</isHoliday><locdate>20260815</locdate></item><item><dateName>대체공휴일</dateName><isHoliday>Y</isHoliday><locdate>20260817</locdate></item></items></body></response>""".encode("utf-8")
        self.assertEqual(parse_official_holiday_xml(xml), {"2026-08-15": "광복절", "2026-08-17": "대체휴"})
    def test_monthly_check(self):
        now = datetime(2026, 8, 17)
        self.assertFalse(should_check_holidays("2026-08", now))
        self.assertTrue(should_check_holidays("2026-07", now))
    def test_payload_has_stable_version(self):
        first = build_holiday_payload({"2026-08-17": "대체공휴일"})
        second = build_holiday_payload({"2026-08-17": "대체공휴일"})
        self.assertEqual(first["version"], second["version"])
        self.assertEqual(first["holidays"]["2026-08-17"], "대체휴")
    def test_name_normalization(self):
        self.assertEqual(normalize_holiday_name("대체공휴일"), "대체휴")
        self.assertEqual(normalize_holiday_name("설날"), "설날")

if __name__ == "__main__":
    unittest.main()
