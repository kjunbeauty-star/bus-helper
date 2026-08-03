from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


SCHEMA_VERSION = 1
MORNING_SHIFT = "morning"
AFTERNOON_SHIFT = "afternoon"
VALID_SHIFTS = {MORNING_SHIFT, AFTERNOON_SHIFT}


def _validate_time(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("alarm time must be a string in HH:MM format")
    parts = value.split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError("alarm time must use HH:MM format")
    hour, minute = (int(part) for part in parts)
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("alarm time is outside the valid range")
    return f"{hour:02d}:{minute:02d}"


@dataclass(frozen=True)
class AlarmSettings:
    enabled: bool = False
    morning_enabled: bool = True
    morning_time: str = "05:30"
    afternoon_enabled: bool = True
    afternoon_time: str = "12:30"
    sound_enabled: bool = True
    vibration_enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "morning_time", _validate_time(self.morning_time))
        object.__setattr__(self, "afternoon_time", _validate_time(self.afternoon_time))

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "morning_enabled": self.morning_enabled,
            "morning_time": self.morning_time,
            "afternoon_enabled": self.afternoon_enabled,
            "afternoon_time": self.afternoon_time,
            "sound_enabled": self.sound_enabled,
            "vibration_enabled": self.vibration_enabled,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any] | None) -> "AlarmSettings":
        if not isinstance(value, Mapping):
            return cls()
        defaults = cls()
        return cls(
            enabled=value.get("enabled") if isinstance(value.get("enabled"), bool) else defaults.enabled,
            morning_enabled=value.get("morning_enabled") if isinstance(value.get("morning_enabled"), bool) else defaults.morning_enabled,
            morning_time=value.get("morning_time") if isinstance(value.get("morning_time"), str) else defaults.morning_time,
            afternoon_enabled=value.get("afternoon_enabled") if isinstance(value.get("afternoon_enabled"), bool) else defaults.afternoon_enabled,
            afternoon_time=value.get("afternoon_time") if isinstance(value.get("afternoon_time"), str) else defaults.afternoon_time,
            sound_enabled=value.get("sound_enabled") if isinstance(value.get("sound_enabled"), bool) else defaults.sound_enabled,
            vibration_enabled=value.get("vibration_enabled") if isinstance(value.get("vibration_enabled"), bool) else defaults.vibration_enabled,
        )


@dataclass(frozen=True)
class AlarmEntry:
    alarm_id: str
    request_code: int
    date: str
    shift: str
    status: str
    trigger_at: int
    title: str
    message: str
    sound_enabled: bool = True
    vibration_enabled: bool = True

    def __post_init__(self) -> None:
        if not self.alarm_id:
            raise ValueError("alarm_id is required")
        if self.shift not in VALID_SHIFTS:
            raise ValueError(f"unsupported shift: {self.shift}")
        if not isinstance(self.request_code, int) or self.request_code <= 0:
            raise ValueError("request_code must be a positive integer")
        if not isinstance(self.trigger_at, int) or self.trigger_at <= 0:
            raise ValueError("trigger_at must be a positive epoch millisecond value")

    def to_dict(self) -> dict[str, Any]:
        return {
            "alarm_id": self.alarm_id,
            "request_code": self.request_code,
            "date": self.date,
            "shift": self.shift,
            "status": self.status,
            "trigger_at": self.trigger_at,
            "title": self.title,
            "message": self.message,
            "sound_enabled": self.sound_enabled,
            "vibration_enabled": self.vibration_enabled,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AlarmEntry":
        if not isinstance(value, Mapping):
            raise ValueError("alarm entry must be an object")
        return cls(
            alarm_id=str(value.get("alarm_id", "")),
            request_code=value.get("request_code"),
            date=str(value.get("date", "")),
            shift=str(value.get("shift", "")),
            status=str(value.get("status", "")),
            trigger_at=value.get("trigger_at"),
            title=str(value.get("title", "")),
            message=str(value.get("message", "")),
            sound_enabled=value.get("sound_enabled", True) is True,
            vibration_enabled=value.get("vibration_enabled", True) is True,
        )


@dataclass(frozen=True)
class ReconcilePlan:
    schedule: tuple[AlarmEntry, ...]
    update: tuple[AlarmEntry, ...]
    cancel: tuple[AlarmEntry, ...]
    unchanged: tuple[AlarmEntry, ...]

