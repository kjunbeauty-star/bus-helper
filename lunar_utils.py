from functools import lru_cache

from korean_lunar_calendar import KoreanLunarCalendar


@lru_cache(maxsize=4096)
def get_lunar_marker(year: int, month: int, day: int) -> str:
    """Return a compact marker only for the 1st, 11th and 21st lunar day."""
    lunar = KoreanLunarCalendar()
    if not lunar.setSolarDate(year, month, day):
        return ""
    if lunar.lunarDay not in (1, 11, 21):
        return ""
    return f"{lunar.lunarMonth}.{lunar.lunarDay}"
