import unittest
from route_models import normalize_routes_state
class T(unittest.TestCase):
 def test_company(self):self.assertEqual(normalize_routes_state({"selected_company":"미추홀","routes":[]})["selected_company"],"미추홀")
 def test_old(self):self.assertEqual(normalize_routes_state({"routes":[]})["selected_company"],"")
