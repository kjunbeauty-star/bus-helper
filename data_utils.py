from __future__ import annotations

from datetime import datetime


DEFAULT_INPUT_DATA = {
    "route": "미입력",
    "bus_no": "미입력",
    "relief_driver": "미입력",
    "relief_phone": "미입력",
    "front_bus": "미입력",
    "front_driver": "미입력",
    "front_phone": "미입력",
    "back_bus": "미입력",
    "back_driver": "미입력",
    "back_phone": "미입력",
}


def normalize_input_data(value):
    """Merge persisted vehicle data with the current storage schema."""
    result = DEFAULT_INPUT_DATA.copy()
    if isinstance(value, dict):
        for key in result:
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                result[key] = item.strip()
    return result


def normalize_schedules(value):
    """Drop malformed schedule rows and fill optional fields safely."""
    if not isinstance(value, dict):
        return {}
    result = {}
    for date_key, item in value.items():
        if not isinstance(date_key, str) or not isinstance(item, dict):
            continue
        try:
            datetime.strptime(date_key, "%Y-%m-%d")
        except ValueError:
            continue
        status = item.get("status", "")
        start_time = item.get("start_time", "")
        order_no = item.get("order_no", "")
        result[date_key] = {
            "status": status if isinstance(status, str) else "",
            "start_time": start_time if isinstance(start_time, str) else "",
            "order_no": str(order_no) if order_no is not None else "",
        }
    return result


def normalize_contacts(value):
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if not isinstance(item, dict):
            continue
        name, phone = item.get("name"), item.get("phone")
        if isinstance(name, str) and isinstance(phone, str):
            result.append({"name": name.strip(), "phone": format_phone(phone), "is_edit": False})
    return result


def format_phone(raw_value):
    """Format common Korean numbers without silently truncating input."""
    digits = "".join(ch for ch in str(raw_value or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("02"):
        if len(digits) == 9:
            return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
        if len(digits) == 10:
            return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        return digits
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:]}"
    if len(digits) <= 3:
        return digits
    if len(digits) <= 7:
        return f"{digits[:3]}-{digits[3:]}"
    return digits
