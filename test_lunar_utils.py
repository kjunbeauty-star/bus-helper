import unittest

from lunar_utils import get_lunar_marker


class LunarUtilsTests(unittest.TestCase):
    def test_marks_first_lunar_day(self):
        self.assertEqual(get_lunar_marker(2026, 8, 13), "7.1")

    def test_marks_eleventh_lunar_day(self):
        self.assertEqual(get_lunar_marker(2026, 8, 23), "7.11")

    def test_marks_twenty_first_lunar_day(self):
        self.assertEqual(get_lunar_marker(2026, 9, 2), "7.21")

    def test_ordinary_lunar_day_is_hidden(self):
        self.assertEqual(get_lunar_marker(2026, 8, 27), "")

    def test_out_of_supported_range_is_hidden(self):
        self.assertEqual(get_lunar_marker(2051, 1, 1), "")


if __name__ == "__main__":
    unittest.main()
