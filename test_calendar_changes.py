from pathlib import Path
import unittest


class CalendarChangeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("main.py").read_text(encoding="utf-8")

    def test_holiday_uses_normal_font_weight(self):
        self.assertIn(
            'ft.Text(holiday_name, size=7, weight="normal"',
            self.source,
        )

    def test_today_month_shortcut_is_available(self):
        self.assertIn('today_month_button = ft.TextButton(', self.source)
        self.assertIn('"오늘", visible=False', self.source)
        self.assertIn('def go_today_month(e):', self.source)

    def test_existing_pattern_prompts_for_effective_month(self):
        self.assertIn('"이번 달부터 적용"', self.source)
        self.assertIn('"다음 달부터 적용"', self.source)
        self.assertIn('이전 기간의 근무 이력은 그대로 유지됩니다.', self.source)


if __name__ == "__main__":
    unittest.main()
