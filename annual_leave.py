"""사용자가 지정한 입사일 기준 연차 규칙 (개근 여부 별도 판정 없음)."""
import calendar
from datetime import date, datetime


def parse_join_date(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError()
        return parsed
    except (ValueError, TypeError):
        raise ValueError("입사일은 올바른 YYYY-MM-DD 형식으로 입력해 주세요.") from None


def calculate_pay_grade(join_date, current_date):
    """간선 호봉. 6개월 당일은 1-1호봉이며, 월말/윤일은 말일로 보정한다."""
    today = (current_date.date() if isinstance(current_date, datetime)
             else date.fromisoformat(current_date) if isinstance(current_date, str)
             else current_date)
    try:
        joined = parse_join_date(join_date)
    except ValueError:
        return ""
    if joined > today:
        return ""

    def anniversary(months):
        year, month = divmod(joined.year * 12 + joined.month - 1 + months, 12)
        month += 1
        return date(year, month, min(joined.day, calendar.monthrange(year, month)[1]))

    if today <= anniversary(6):
        return "간선1-1"
    for months, grade in [(12, "간선1-2"), (24, "간선2"),
                          (60, "간선3"), (96, "간선4"),
                          (132, "간선5")]:
        if today < anniversary(months):
            return grade
    return "간선6"


def calculate_annual_leave(join_date, current_date):
    """미설정은 기존 15일. 월말/윤일 기념일은 해당 월 말일로 보정."""
    today = (current_date.date() if isinstance(current_date, datetime)
             else date.fromisoformat(current_date) if isinstance(current_date, str)
             else current_date)
    try:
        joined = parse_join_date(join_date)
    except ValueError:
        return 15
    if joined > today:
        return 0
    anniversary = date(today.year, joined.month,
                       min(joined.day, calendar.monthrange(today.year, joined.month)[1]))
    years = today.year - joined.year - (today < anniversary)
    if years >= 1:
        return min(25, 15 + (years - 1) // 2)
    months = (today.year - joined.year) * 12 + today.month - joined.month
    month_day = min(joined.day, calendar.monthrange(today.year, today.month)[1])
    return max(0, min(11, months - (today.day < month_day)))
