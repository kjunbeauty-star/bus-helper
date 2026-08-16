import unittest

from pattern_utils import (
    ALL_MONTHS,
    add_pattern_segment,
    get_repeating_pattern_status,
    normalize_pattern_state,
)


PATTERNS = {
    "old": ["오전", "휴무"],
    "new": ["오후", "오후", "휴무"],
}


class PatternHistoryTests(unittest.TestCase):
    def test_first_setup_applies_to_all_months(self):
        state = normalize_pattern_state({})
        add_pattern_segment(state, "old", "2026-08-16", 0, ALL_MONTHS)
        self.assertIsNotNone(get_repeating_pattern_status(state, PATTERNS, "2026-07-01"))

    def test_change_this_month_preserves_previous_month_pattern(self):
        state = normalize_pattern_state({})
        add_pattern_segment(state, "old", "2026-06-01", 0, ALL_MONTHS)
        old_value = get_repeating_pattern_status(state, PATTERNS, "2026-07-15")
        add_pattern_segment(state, "new", "2026-08-16", 0, "2026-08")
        self.assertEqual(
            get_repeating_pattern_status(state, PATTERNS, "2026-07-15"),
            old_value,
        )
        self.assertIn(
            get_repeating_pattern_status(state, PATTERNS, "2026-08-01"),
            PATTERNS["new"],
        )

    def test_change_next_month_keeps_current_month_pattern(self):
        state = normalize_pattern_state({})
        add_pattern_segment(state, "old", "2026-06-01", 0, ALL_MONTHS)
        august_value = get_repeating_pattern_status(state, PATTERNS, "2026-08-20")
        add_pattern_segment(state, "new", "2026-08-16", 0, "2026-09")
        self.assertEqual(
            get_repeating_pattern_status(state, PATTERNS, "2026-08-20"),
            august_value,
        )
        self.assertIn(
            get_repeating_pattern_status(state, PATTERNS, "2026-09-01"),
            PATTERNS["new"],
        )

    def test_reselecting_same_effective_month_replaces_that_segment(self):
        state = normalize_pattern_state({})
        add_pattern_segment(state, "old", "2026-06-01", 0, ALL_MONTHS)
        add_pattern_segment(state, "new", "2026-08-16", 0, "2026-08")
        add_pattern_segment(state, "old", "2026-08-17", 1, "2026-08")
        self.assertEqual(len(state["history"]), 2)
        self.assertEqual(state["history"][-1]["name"], "old")

    def test_legacy_state_keeps_previous_all_date_behavior(self):
        state = normalize_pattern_state({
            "name": "old", "anchor_date": "2026-08-16", "anchor_index": 0,
        })
        self.assertEqual(state["history"][0]["effective_month"], ALL_MONTHS)


if __name__ == "__main__":
    unittest.main()
