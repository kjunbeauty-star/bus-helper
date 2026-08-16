from __future__ import annotations

from typing import Any, Mapping

import flet as ft


@ft.control("WorkAlarmService")
class WorkAlarmService(ft.Service):
    """Python facade for the local Flutter work-alarm service."""

    async def ping(self) -> dict[str, Any]:
        return await self._invoke_method("ping")

    async def get_permission_status(self) -> dict[str, Any]:
        return await self._invoke_method("get_permission_status")

    async def request_notification_permission(self) -> dict[str, Any]:
        return await self._invoke_method("request_notification_permission")

    async def open_exact_alarm_settings(self) -> dict[str, Any]:
        return await self._invoke_method("open_exact_alarm_settings")

    async def open_full_screen_settings(self) -> dict[str, Any]:
        return await self._invoke_method("open_full_screen_settings")

    async def reconcile(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        return await self._invoke_method("reconcile", {"snapshot": dict(snapshot)})

    async def cancel_all(self) -> dict[str, Any]:
        return await self._invoke_method("cancel_all")

    async def stop_ringing(self) -> dict[str, Any]:
        return await self._invoke_method("stop_ringing")

    async def get_native_snapshot(self) -> dict[str, Any]:
        return await self._invoke_method("get_native_snapshot")

    async def test_alarm(self) -> dict[str, Any]:
        return await self._invoke_method("test_alarm")
