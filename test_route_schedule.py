import unittest

from route_schedule import (
    ROUTE_SCHEDULES,
    SERVICE_SATURDAY,
    SERVICE_SUNDAY_HOLIDAY,
    SERVICE_WEEKDAY,
    company_fleet_count,
    lookup_schedule,
    service_for_date,
)


class CompanyRouteScheduleTests(unittest.TestCase):
    def test_all_seven_routes_are_embedded(self):
        self.assertEqual(
            set(ROUTE_SCHEDULES),
            {"76", "77", "75", "12", "78", "급행97", "30"},
        )

    def test_reduced_service_is_deferred(self):
        for services in ROUTE_SCHEDULES.values():
            self.assertNotIn("weekday_reduced", services)

    def test_fleet_counts_match_workbook(self):
        self.assertEqual(company_fleet_count("76", SERVICE_WEEKDAY), 7)
        self.assertEqual(company_fleet_count("75", SERVICE_SATURDAY), 8)
        self.assertEqual(company_fleet_count("12", SERVICE_SUNDAY_HOLIDAY), 22)
        self.assertEqual(company_fleet_count("30번", SERVICE_WEEKDAY), 33)
        self.assertEqual(company_fleet_count("급행97", SERVICE_WEEKDAY), 10)

    def test_day_type_uses_matching_service(self):
        self.assertEqual(service_for_date("76", "weekday"), SERVICE_WEEKDAY)
        self.assertEqual(service_for_date("76", "saturday"), SERVICE_SATURDAY)
        self.assertEqual(service_for_date("76", "sunday"), SERVICE_SUNDAY_HOLIDAY)

    def test_every_embedded_time_is_valid(self):
        departure_count = 0
        for route_number, services in ROUTE_SCHEDULES.items():
            for service_type, service in services.items():
                self.assertEqual(service["fleet_count"], len(service["orders"]))
                for order, shifts in service["orders"].items():
                    for status, shift in (("오전", "morning"), ("오후", "afternoon")):
                        raw = shifts[shift]
                        self.assertIsNotNone(raw)
                        hour, minute = map(int, raw["time"].split(":"))
                        self.assertIn(hour, range(24))
                        self.assertIn(minute, range(60))
                        self.assertEqual(
                            lookup_schedule(route_number, service_type, status, order),
                            raw,
                        )
                        departure_count += bool(raw.get("departure"))
        self.assertGreater(departure_count, 0)


if __name__ == "__main__":
    unittest.main()
