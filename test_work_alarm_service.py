import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock


class _FakeService:
    pass


def _control(name):
    def decorator(cls):
        cls._control_name = name
        return cls
    return decorator


class WorkAlarmServiceTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        fake_flet = types.ModuleType("flet")
        fake_flet.Service = _FakeService
        fake_flet.control = _control
        cls._old_flet = sys.modules.get("flet")
        sys.modules["flet"] = fake_flet
        extension_src = Path(__file__).parent / "extensions" / "work_alarm" / "src"
        sys.path.insert(0, str(extension_src))
        cls._extension_src = str(extension_src)
        cls.service_module = importlib.import_module("work_alarm.service")

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(cls._extension_src)
        for name in ["work_alarm.service", "work_alarm"]:
            sys.modules.pop(name, None)
        if cls._old_flet is None:
            sys.modules.pop("flet", None)
        else:
            sys.modules["flet"] = cls._old_flet

    def make_service(self):
        service = self.service_module.WorkAlarmService()
        service._invoke_method = AsyncMock(return_value={"ok": True})
        return service

    async def test_ping_uses_expected_method_name(self):
        service = self.make_service()
        self.assertEqual(await service.ping(), {"ok": True})
        service._invoke_method.assert_awaited_once_with("ping")

    async def test_reconcile_wraps_snapshot(self):
        service = self.make_service()
        snapshot = {"schema_version": 1, "alarms": [{"alarm_id": "a"}]}
        await service.reconcile(snapshot)
        service._invoke_method.assert_awaited_once_with(
            "reconcile", {"snapshot": snapshot}
        )

    async def test_all_native_api_method_names_are_stable(self):
        service = self.make_service()
        await service.get_permission_status()
        await service.request_notification_permission()
        await service.open_exact_alarm_settings()
        await service.open_full_screen_settings()
        await service.cancel_all()
        await service.stop_ringing()
        await service.get_native_snapshot()
        await service.test_alarm()
        self.assertEqual(
            [call.args[0] for call in service._invoke_method.await_args_list],
            [
                "get_permission_status",
                "request_notification_permission",
                "open_exact_alarm_settings",
                "open_full_screen_settings",
                "cancel_all",
                "stop_ringing",
                "get_native_snapshot",
                "test_alarm",
            ],
        )


if __name__ == "__main__":
    unittest.main()
