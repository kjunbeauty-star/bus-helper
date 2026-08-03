from __future__ import annotations

from datetime import date, datetime, time, timedelta, tzinfo
from typing import Callable, Iterable, Mapping, Any

from alarm_models import (
    AFTERNOON_SHIFT,
    MORNING_SHIFT,
    AlarmEntry,
    AlarmSettings,
    ReconcilePlan,
)


STATUS_TO_SHIFT = {"오전": MORNING_SHIFT, "오후": AFTERNOON_SHIFT}
SHIFT_CODE = {MORNING_SHIFT: 1, AFTERNOON_SHIFT: 2}


def build_alarm_id(work_date: date, shift: str) -> str:
    if shift not in SHIFT_CODE:
        raise ValueError(f"unsupported shift: {shift}")
    return f"{work_date.isoformat()}:{shift}"


def build_request_code(work_date: date, shift: str) -> int:
    if shift not in SHIFT_CODE:
        raise ValueError(f"unsupported shift: {shift}")
    return int(work_date.strftime("%Y%m%d")) * 10 + SHIFT_CODE[shift]


def _parse_alarm_time(value: str) -> time:
    try:
        hour, minute = (int(part) for part in value.split(":"))
        return time(hour=hour, minute=minute)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid alarm time: {value!r}") from exc


def _trigger_millis(work_date: date, alarm_time: str, timezone: tzinfo) -> int:
    local_dt = datetime.combine(work_date, _parse_alarm_time(alarm_time), tzinfo=timezone)
    return int(local_dt.timestamp() * 1000)


def build_desired_alarms(
    *,
    start_date: date,
    get_day_info: Callable[[str], Mapping[str, Any]],
    settings: AlarmSettings,
    timezone: tzinfo,
    now: datetime,
    days: int = 90,
) -> list[AlarmEntry]:
    """Build the complete desired native alarm snapshot for a rolling horizon."""
    if days < 0:
        raise ValueError("days must not be negative")
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if not settings.enabled:
        return []

    now_ms = int(now.timestamp() * 1000)
    alarms: list[AlarmEntry] = []
    for offset in range(days):
        work_date = start_date + timedelta(days=offset)
        day_info = get_day_info(work_date.isoformat())
        status = day_info.get("status", "") if isinstance(day_info, Mapping) else ""
        shift = STATUS_TO_SHIFT.get(status)
        if shift is None:
            continue
        if shift == MORNING_SHIFT:
            if not settings.morning_enabled:
                continue
            alarm_time = settings.morning_time
            title, message = "오전근무 알람", "오늘은 오전근무입니다."
        else:
            if not settings.afternoon_enabled:
                continue
            alarm_time = settings.afternoon_time
            title, message = "오후근무 알람", "오늘은 오후근무입니다."
        trigger_at = _trigger_millis(work_date, alarm_time, timezone)
        if trigger_at <= now_ms:
            continue
        alarms.append(AlarmEntry(
            alarm_id=build_alarm_id(work_date, shift),
            request_code=build_request_code(work_date, shift),
            date=work_date.isoformat(),
            shift=shift,
            status=status,
            trigger_at=trigger_at,
            title=title,
            message=message,
            sound_enabled=settings.sound_enabled,
            vibration_enabled=settings.vibration_enabled,
        ))
    return alarms


def build_reconcile_plan(
    desired: Iterable[AlarmEntry],
    existing: Iterable[AlarmEntry],
) -> ReconcilePlan:
    """Classify a full desired snapshot against the native stored snapshot."""
    desired_by_id = {entry.alarm_id: entry for entry in desired}
    existing_by_id = {entry.alarm_id: entry for entry in existing}
    schedule, update, cancel, unchanged = [], [], [], []

    for alarm_id, entry in desired_by_id.items():
        previous = existing_by_id.get(alarm_id)
        if previous is None:
            schedule.append(entry)
        elif previous == entry:
            unchanged.append(entry)
        else:
            update.append(entry)

    for alarm_id, entry in existing_by_id.items():
        if alarm_id not in desired_by_id:
            cancel.append(entry)

    sort_key = lambda entry: (entry.trigger_at, entry.alarm_id)
    return ReconcilePlan(
        schedule=tuple(sorted(schedule, key=sort_key)),
        update=tuple(sorted(update, key=sort_key)),
        cancel=tuple(sorted(cancel, key=sort_key)),
        unchanged=tuple(sorted(unchanged, key=sort_key)),
    )

