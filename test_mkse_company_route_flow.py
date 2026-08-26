import unittest
from pathlib import Path

from route_schedule import DEPOT_ROUTES, ROUTE_SCHEDULES, lookup_schedule


class MkseCompanyRouteFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("main.py").read_text(encoding="utf-8")

    def test_depot_route_mapping(self):
        self.assertEqual(DEPOT_ROUTES["미추홀"], ("76", "77", "75", "12"))
        self.assertEqual(DEPOT_ROUTES["제물포"], ("30", "78", "급행97"))

    def test_first_middle_last_orders_for_every_service_and_shift(self):
        for route_number, services in ROUTE_SCHEDULES.items():
            for service_type, service in services.items():
                last = service["fleet_count"]
                for order in sorted({1, (last + 1) // 2, last}):
                    for status in ("오전", "오후"):
                        item = lookup_schedule(route_number, service_type, status, order)
                        self.assertIsNotNone(
                            item,
                            f"{route_number} {service_type} {status} {order}번",
                        )
                        self.assertRegex(item["time"], r"^\d{2}:\d{2}$")

    def test_route_add_opens_depot_picker(self):
        self.assertIn("on_click=open_company_route_add", self.source)
        self.assertIn("회사를 선택하세요.", self.source)

    def test_company_registration_uses_embedded_fleet_counts(self):
        self.assertIn("company_fleet_count(number, SERVICE_WEEKDAY)", self.source)
        self.assertIn("company_fleet_count(number, SERVICE_SATURDAY)", self.source)
        self.assertIn("company_fleet_count(number, SERVICE_SUNDAY_HOLIDAY)", self.source)

    def test_duplicate_company_route_is_rejected(self):
        self.assertIn("노선은 이미 등록돼 있습니다.", self.source)

    def test_manual_route_editor_is_preserved(self):
        self.assertIn("def open_route_form(route_id=None):", self.source)
        self.assertIn("visible=not is_company_route_number", self.source)

    def test_saved_date_uses_company_lookup(self):
        self.assertIn("company_item = lookup_schedule(", self.source)
        self.assertIn('\"departure\": \"\" if date_route_state[\"override\"]', self.source)

    def test_calendar_never_composes_route_and_order(self):
        self.assertNotIn('f"{route_number}/{order_no}"', self.source)
        self.assertIn("status_order = str(order_no)", self.source)


if __name__ == "__main__":
    unittest.main()
