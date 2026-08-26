from __future__ import annotations
from datetime import datetime
from typing import Any, Callable, Mapping
ROUTE_SCHEMA_VERSION = 1
DAY_TYPES = ("weekday", "saturday", "sunday")
SHIFT_TYPES = ("morning", "afternoon")
STATUS_TO_SHIFT = {"오전": "morning", "오후": "afternoon"}

def _positive_count(value: Any) -> int:
    try: return max(0, int(value))
    except (TypeError, ValueError): return 0

def valid_time(value: Any) -> str:
    if not isinstance(value, str): return ""
    value = value.strip()
    if len(value) == 4 and value.isdigit():
        value = f"{value[:2]}:{value[2:]}"
    if ":" not in value: return ""
    try: hour, minute = (int(part) for part in value.split(":", 1))
    except ValueError: return ""
    return f"{hour:02d}:{minute:02d}" if 0 <= hour <= 23 and 0 <= minute <= 59 else ""

def empty_times() -> dict[str, dict[str, dict[str, str]]]:
    return {day: {shift: {} for shift in SHIFT_TYPES} for day in DAY_TYPES}

def normalize_route(route: Any) -> dict[str, Any] | None:
    if not isinstance(route, Mapping): return None
    route_id, route_number = str(route.get("id", "")).strip(), str(route.get("route_number", "")).strip()
    if not route_id or not route_number: return None
    raw_counts, raw_times = route.get("fleet_counts", {}), route.get("first_trip_times", {})
    counts = {day: _positive_count(raw_counts.get(day, 0)) if isinstance(raw_counts, Mapping) else 0 for day in DAY_TYPES}
    times = empty_times()
    for day in DAY_TYPES:
        source = raw_times.get(day, {}) if isinstance(raw_times, Mapping) else {}
        for shift in SHIFT_TYPES:
            shift_source = source.get(shift, {}) if isinstance(source, Mapping) else {}
            times[day][shift] = {str(order): normalized for order, value in (shift_source.items() if isinstance(shift_source, Mapping) else []) if str(order).isdigit() and int(order) > 0 and (normalized := valid_time(value))}
    return {"id": route_id, "route_number": route_number, "fleet_counts": counts, "first_trip_times": times}

def normalize_routes_state(value: Any) -> dict[str, Any]:
    routes, seen = [], set()
    if isinstance(value, Mapping):
        raw_routes = value.get("routes", [])
        for item in raw_routes if isinstance(raw_routes, list) else []:
            route = normalize_route(item)
            if route and route["id"] not in seen: routes.append(route); seen.add(route["id"])
    requested = str(value.get("default_route_id", "")) if isinstance(value, Mapping) else ""
    selected_company = str(value.get("selected_company", "")).strip() if isinstance(value, Mapping) else ""
    return {"schema_version": ROUTE_SCHEMA_VERSION, "default_route_id": requested if requested in seen else (routes[0]["id"] if routes else ""), "selected_company": selected_company, "routes": routes}

def find_route(routes_state: Mapping[str, Any], route_id: str) -> Mapping[str, Any] | None:
    return next((route for route in routes_state.get("routes", []) if isinstance(route, Mapping) and route.get("id") == route_id), None)

def find_route_by_number(routes_state: Mapping[str, Any], route_number: str) -> Mapping[str, Any] | None:
    number = str(route_number or "").strip()
    if not number:
        return None
    return next(
        (
            route for route in routes_state.get("routes", [])
            if isinstance(route, Mapping)
            and str(route.get("route_number", "")).strip() == number
        ),
        None,
    )

def default_route(routes_state: Mapping[str, Any]) -> Mapping[str, Any] | None:
    return find_route(routes_state, str(routes_state.get("default_route_id", "")))

def day_type_for_date(date_key: str, is_holiday: Callable[[str], bool]) -> str:
    if is_holiday(date_key): return "sunday"
    weekday = datetime.strptime(date_key, "%Y-%m-%d").weekday()
    return "saturday" if weekday == 5 else ("sunday" if weekday == 6 else "weekday")

def fleet_count(route: Mapping[str, Any] | None, day_type: str) -> int:
    counts = route.get("fleet_counts", {}) if route else {}
    return _positive_count(counts.get(day_type, 0)) if isinstance(counts, Mapping) and day_type in DAY_TYPES else 0

def first_trip_time(route: Mapping[str, Any] | None, day_type: str, status: str, order_no: Any) -> str:
    shift, order = STATUS_TO_SHIFT.get(status), str(order_no or "")
    if not route or not shift or day_type not in DAY_TYPES or not order.isdigit() or int(order) < 1 or int(order) > fleet_count(route, day_type): return ""
    try: return valid_time(route["first_trip_times"][day_type][shift].get(order, ""))
    except (KeyError, TypeError): return ""
