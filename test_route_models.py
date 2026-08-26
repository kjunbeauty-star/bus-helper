import unittest
from route_models import day_type_for_date, find_route, find_route_by_number, first_trip_time, normalize_routes_state, valid_time

def sample_state():
    return normalize_routes_state({"default_route_id": "route-123", "routes": [{"id": "route-123", "route_number": "123", "fleet_counts": {"weekday": 2, "saturday": 1, "sunday": 1}, "first_trip_times": {"weekday": {"morning": {"1": "06:20", "3": "07:00"}, "afternoon": {"1": "13:10"}}, "saturday": {"morning": {"1": "06:40"}, "afternoon": {}}, "sunday": {"morning": {"1": "07:00"}, "afternoon": {}}}}]})

class RouteModelTests(unittest.TestCase):
    def test_time_without_colon_is_normalized(self):
        self.assertEqual(valid_time("0620"), "06:20")
        self.assertEqual(valid_time(" 1345 "), "13:45")
        self.assertEqual(valid_time("2460"), "")

    def test_normalize_preserves_hidden_times_when_count_is_reduced(self):
        route = sample_state()["routes"][0]
        self.assertEqual(route["first_trip_times"]["weekday"]["morning"]["3"], "07:00")
        self.assertEqual(first_trip_time(route, "weekday", "오전", "3"), "")

    def test_first_trip_uses_status_and_order(self):
        route = sample_state()["routes"][0]
        self.assertEqual(first_trip_time(route, "weekday", "오전", "1"), "06:20")
        self.assertEqual(first_trip_time(route, "weekday", "오후", "1"), "13:10")

    def test_holiday_uses_sunday_table(self):
        self.assertEqual(day_type_for_date("2026-08-17", lambda key: key == "2026-08-17"), "sunday")
        self.assertEqual(day_type_for_date("2026-08-22", lambda key: False), "saturday")

class RouteReconnectTests(unittest.TestCase):
    def test_find_route_by_number_reconnects_old_id(self):
        state = normalize_routes_state({"routes": [{
            "id": "current-76", "route_number": "76",
            "fleet_counts": {}, "first_trip_times": {},
        }]})
        self.assertIsNone(find_route(state, "old-76"))
        self.assertEqual(find_route_by_number(state, "76")["id"], "current-76")

    def test_find_route_by_number_returns_none_for_deleted_route(self):
        state = normalize_routes_state({"routes": [{
            "id": "current-76", "route_number": "76",
            "fleet_counts": {}, "first_trip_times": {},
        }]})
        self.assertIsNone(find_route_by_number(state, "99"))
