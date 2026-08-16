from __future__ import annotations

from datetime import datetime


ALL_MONTHS = "0001-01"


def _valid_segment(value):
    if not isinstance(value, dict):
        return None
    name = value.get("name")
    anchor_date = value.get("anchor_date")
    anchor_index = value.get("anchor_index", 0)
    effective_month = value.get("effective_month")
    if not isinstance(name, str) or not name:
        return None
    try:
        datetime.strptime(anchor_date, "%Y-%m-%d")
        if effective_month != ALL_MONTHS:
            datetime.strptime(effective_month, "%Y-%m")
        anchor_index = int(anchor_index)
    except (TypeError, ValueError):
        return None
    return {
        "name": name,
        "anchor_date": anchor_date,
        "anchor_index": anchor_index,
        "effective_month": effective_month,
    }


def normalize_pattern_state(value):
    state = dict(value) if isinstance(value, dict) else {}
    history = []
    if isinstance(state.get("history"), list):
        for item in state["history"]:
            segment = _valid_segment(item)
            if segment:
                history.append(segment)
    if not history and state.get("name") and state.get("anchor_date"):
        legacy = _valid_segment({
            "name": state.get("name"),
            "anchor_date": state.get("anchor_date"),
            "anchor_index": state.get("anchor_index", 0),
            "effective_month": ALL_MONTHS,
        })
        if legacy:
            history.append(legacy)
    history.sort(key=lambda item: item["effective_month"])
    state.setdefault("name", None)
    state.setdefault("anchor_date", None)
    state.setdefault("anchor_index", 0)
    state["history"] = history
    return state


def add_pattern_segment(state, name, anchor_date, anchor_index, effective_month):
    normalized = normalize_pattern_state(state)
    segment = _valid_segment({
        "name": name,
        "anchor_date": anchor_date,
        "anchor_index": anchor_index,
        "effective_month": effective_month,
    })
    if not segment:
        raise ValueError("Invalid work-pattern segment")
    history = [
        item for item in normalized["history"]
        if item["effective_month"] != effective_month
    ]
    history.append(segment)
    history.sort(key=lambda item: item["effective_month"])
    state.update(normalized)
    state.update({"name": name, "anchor_date": anchor_date, "anchor_index": int(anchor_index)})
    state["history"] = history
    return state


def get_pattern_segment(state, date_key):
    try:
        target_month = datetime.strptime(date_key, "%Y-%m-%d").strftime("%Y-%m")
    except (TypeError, ValueError):
        return None
    normalized = normalize_pattern_state(state)
    eligible = [
        item for item in normalized["history"]
        if item["effective_month"] <= target_month
    ]
    return eligible[-1] if eligible else None


def get_repeating_pattern_status(state, patterns, date_key):
    segment = get_pattern_segment(state, date_key)
    if not segment:
        return None
    pattern = patterns.get(segment["name"])
    if not pattern:
        return None
    try:
        anchor = datetime.strptime(segment["anchor_date"], "%Y-%m-%d")
        target = datetime.strptime(date_key, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None
    delta_days = (target - anchor).days
    idx = (segment["anchor_index"] + delta_days) % len(pattern)
    return pattern[idx]
