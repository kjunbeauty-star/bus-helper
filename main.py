# ==========================================
# [앱 이름: 버스캘린더]
# 현재 배포 버전: 빌드 0005 (주석 및 이모지 완벽 복구본)
# ==========================================

import os
import calendar
import asyncio
from datetime import datetime, timedelta, timezone
import flet as ft
import json

from route_models import (
    DAY_TYPES, day_type_for_date, default_route, empty_times, find_route,
    find_route_by_number, first_trip_time, fleet_count, normalize_routes_state,
    valid_time,
)
from route_schedule import (
    DEPOT_ROUTES, SERVICE_SATURDAY, SERVICE_SUNDAY_HOLIDAY, SERVICE_WEEKDAY,
    company_fleet_count, default_service_for_day_type, lookup_schedule,
    service_for_date,
)

from alarm_logic import build_desired_alarms, is_expired_date_alarm
from alarm_models import AlarmSettings, SCHEMA_VERSION

try:
    from work_alarm import WorkAlarmService
except ImportError:
    WorkAlarmService = None

from data_utils import format_phone, normalize_contacts, normalize_input_data, normalize_schedules
from lunar_utils import get_lunar_marker
from holiday_sync import download_holidays, should_check_holidays
from pattern_utils import (
    ALL_MONTHS,
    add_pattern_segment,
    get_pattern_segment,
    get_repeating_pattern_status,
    normalize_pattern_state,
)

try:
    import holidays as holidays_lib
except ImportError:
    holidays_lib = None

# 한국 표준시(KST) 및 데이터베이스/저장소 키 설정
KST = timezone(timedelta(hours=9))
STORAGE_SCHEDULES_KEY = "bus_helper_schedules"
STORAGE_MANGEUN_KEY = "bus_helper_mangeun_targets"
STORAGE_INPUT_DATA_KEY = "bus_helper_input_data"
STORAGE_PHONEBOOK_KEY = "bus_helper_phonebook"
STORAGE_EMERGENCY_KEY = "bus_helper_emergency"
STORAGE_PATTERN_KEY = "bus_helper_work_pattern"
STORAGE_MEMO_KEY = "bus_helper_date_memos"
STORAGE_ALARM_SETTINGS_KEY = "bus_helper_alarm_settings"
STORAGE_HOLIDAYS_KEY = "bus_helper_online_holidays"
STORAGE_HOLIDAY_CHECK_MONTH_KEY = "bus_helper_holiday_check_month"
STORAGE_ROUTES_KEY = "bus_helper_routes"
HOLIDAY_UPDATE_URL = os.environ.get(
    "HOLIDAY_UPDATE_URL", "https://bus-helper.onrender.com/api/holidays"
)

# 🔁 반복 근무 패턴 정의 (버스종사자 근무 유형별 순환 사이클)
WORK_PATTERNS = {
    "4일오전 4일오후": ["오전", "오전", "오전", "오전", "휴무", "오후", "오후", "오후", "오후", "휴무"],
    "5일오전 5일오후": ["오전", "오전", "오전", "오전", "오전", "휴무", "오후", "오후", "오후", "오후", "오후", "휴무"],
    "격일제": ["근무", "휴무"],
    "복격일": ["근무", "근무", "휴무"],
}

# 🇰🇷 대한민국 법정공휴일 데이터 (인터넷 연결 없이도 앱 안에 내장되어 표시됨, 2025~2027년)
# 음력 기반 명절(설날/추석/부처님오신날)과 대체공휴일은 매년 날짜가 달라 몇 년 치를 직접 넣어두었음.
# 참고: 노동절(5/1)은 관공서 공휴일은 아니지만 버스회사 등 민간사업장에는 실질적으로 적용되어 포함함.
HOLIDAYS = {
    "2025-01-01": "신정", "2025-01-27": "임시공휴일", "2025-01-28": "설연휴", "2025-01-29": "설날", "2025-01-30": "설연휴",
    "2025-03-01": "삼일절", "2025-03-03": "대체휴", "2025-05-01": "노동절", "2025-05-05": "어린이날/부처님",
    "2025-06-03": "대선", "2025-06-06": "현충일", "2025-08-15": "광복절", "2025-10-03": "개천절",
    "2025-10-05": "추석연휴", "2025-10-06": "추석", "2025-10-07": "추석연휴", "2025-10-08": "대체휴",
    "2025-10-09": "한글날", "2025-12-25": "성탄절",
    "2026-01-01": "신정", "2026-02-16": "설연휴", "2026-02-17": "설날", "2026-02-18": "설연휴",
    "2026-03-01": "삼일절", "2026-03-02": "대체휴", "2026-05-01": "노동절", "2026-05-05": "어린이날",
    "2026-05-24": "부처님", "2026-05-25": "대체휴", "2026-06-03": "지방선거", "2026-06-06": "현충일",
    "2026-07-17": "제헌절", "2026-08-15": "광복절", "2026-08-17": "대체휴", "2026-09-24": "추석연휴",
    "2026-09-25": "추석", "2026-09-26": "추석연휴", "2026-10-03": "개천절", "2026-10-05": "대체휴",
    "2026-10-09": "한글날", "2026-12-25": "성탄절",
    "2027-01-01": "신정", "2027-02-06": "설연휴", "2027-02-07": "설날", "2027-02-08": "설연휴", "2027-02-09": "대체휴",
    "2027-03-01": "삼일절", "2027-05-01": "노동절", "2027-05-05": "어린이날", "2027-05-13": "부처님",
    "2027-06-06": "현충일", "2027-07-17": "제헌절", "2027-08-15": "광복절", "2027-08-16": "대체휴",
    "2027-09-14": "추석연휴", "2027-09-15": "추석", "2027-09-16": "추석연휴", "2027-10-03": "개천절",
    "2027-10-04": "대체휴", "2027-10-09": "한글날", "2027-10-11": "대체휴", "2027-12-25": "성탄절", "2027-12-27": "대체휴",
}

_HOLIDAY_YEAR_CACHE = {}
ONLINE_HOLIDAYS = {}


def get_holiday_name(date_key):
    """Return a Korean holiday name, including years outside the bundled table."""
    if date_key in ONLINE_HOLIDAYS:
        return ONLINE_HOLIDAYS[date_key]
    if date_key in HOLIDAYS:
        return HOLIDAYS[date_key]
    try:
        year = int(date_key[:4])
        datetime.strptime(date_key, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None
    if holidays_lib is not None:
        try:
            year_holidays = _HOLIDAY_YEAR_CACHE.get(year)
            if year_holidays is None:
                # APK 빌드에서 번역 리소스가 제외될 수 있으므로 language를 강제하지 않는다.
                year_holidays = holidays_lib.country_holidays("KR", years=[year], observed=True)
                _HOLIDAY_YEAR_CACHE[year] = year_holidays
            name = year_holidays.get(date_key)
            if name:
                return str(name)
        except Exception as exc:
            # 선택적 라이브러리나 패키지 리소스에 문제가 있어도 달력 전체가 중단되면 안 된다.
            print(f"[WARN] holiday lookup failed for {year}: {exc}", flush=True)
    # The app remains useful if the optional holiday package is unavailable.
    return {
        f"{year}-01-01": "신정",
        f"{year}-03-01": "삼일절",
        f"{year}-05-05": "어린이날",
        f"{year}-06-06": "현충일",
        f"{year}-08-15": "광복절",
        f"{year}-10-03": "개천절",
        f"{year}-10-09": "한글날",
        f"{year}-12-25": "성탄절",
    }.get(date_key)

# 🎨 근무상태별 색상 및 근무/휴무 분류 (근무변경 메뉴에서 고를 수 있는 항목들 포함)
STATUS_COLORS = {
    "오전": "#1A73E8", "오후": "#7E22CE", "전일": "#137333", "근무": "#137333",
    "휴무": "#D93025", "월차": "#B45309", "연차": "#B45309", "휴가": "#B45309", "병가": "#B45309",
    "교육": "#0D9488", "조퇴": "#0D9488", "대체근무": "#0D9488",
}
OFF_STATUSES = {"휴무", "월차", "연차", "휴가", "병가"}
WORK_STATUSES = {"오전", "오후", "전일", "근무", "교육", "조퇴", "대체근무"}

def status_color(s):
    return STATUS_COLORS.get(s, "#374151")

async def main(page: ft.Page):
    global ONLINE_HOLIDAYS
    page.title = "버스캘린더"
    page.theme_mode = "light"

    # 외부 앱(전화 다이얼러 등)을 여는 Flet 서비스
    # Service는 화면 레이어(overlay)가 아니라 page.services에 등록해야 한다.
    url_launcher = ft.UrlLauncher()
    page.services.append(url_launcher)

    # 안드로이드 네이티브 앱에서만 상태바(시간/배터리/신호) 침범 방지용 상단 여백 추가
    # 웹(Render) 배포는 브라우저가 자체적으로 상태바를 처리하므로 영향 없어야 함
    is_native_android = (page.platform == ft.PagePlatform.ANDROID) and not page.web
    alarm_service = WorkAlarmService() if is_native_android and WorkAlarmService else None
    if alarm_service:
        page.services.append(alarm_service)
    top_inset = 30 if is_native_android else 4  # 30은 시작값 — 실기기 테스트하며 조정
    print(f"[DEBUG] platform={page.platform}, web={page.web}, is_native_android={is_native_android}, top_inset={top_inset}", flush=True)
    page.padding = ft.Padding.only(left=4, right=4, top=top_inset, bottom=0)

    # 긴급연락처 화면을 담을 메인 기둥 레이아웃
    setting_column = ft.Column(spacing=2, visible=False)

    # 메모리 상의 긴급연락처 리스트 변수
    EMERGENCY_LIST = []

    # 스마트폰 내부 저장소(Shared Preferences)에서 기존 데이터 불러오기
    # 🛡️ 예전 버전들을 거치며 저장된 값이 혹시 깨진 형태(dict가 아닌 문자열 등)로 남아있어도
    # 앱이 죽지 않고 조용히 기본값으로 초기화되도록 안전하게 불러오는 헬퍼
    def safe_json_load(raw, expected_type, default):
        try:
            val = json.loads(raw) if raw else default
        except Exception:
            return default
        return val if isinstance(val, expected_type) else default

    saved_schedules = await page.shared_preferences.get(STORAGE_SCHEDULES_KEY)
    saved_targets = await page.shared_preferences.get(STORAGE_MANGEUN_KEY)
    saved_input_data = await page.shared_preferences.get(STORAGE_INPUT_DATA_KEY)
    saved_phonebook = await page.shared_preferences.get(STORAGE_PHONEBOOK_KEY)
    saved_routes = await page.shared_preferences.get(STORAGE_ROUTES_KEY)

    saved_emergency = await page.shared_preferences.get(STORAGE_EMERGENCY_KEY)
    EMERGENCY_LIST = safe_json_load(saved_emergency, list, [])

    saved_pattern = await page.shared_preferences.get(STORAGE_PATTERN_KEY)
    # pattern_state: name(패턴명) / anchor_date(기준일 YYYY-MM-DD) / anchor_index(그날이 패턴의 몇 번째인지)
    pattern_state = normalize_pattern_state(
        safe_json_load(saved_pattern, dict, {"name": None, "anchor_date": None, "anchor_index": 0}))

    saved_memos = await page.shared_preferences.get(STORAGE_MEMO_KEY)
    DATE_MEMOS = safe_json_load(saved_memos, dict, {})
    saved_alarm_settings = await page.shared_preferences.get(STORAGE_ALARM_SETTINGS_KEY)
    saved_online_holidays = await page.shared_preferences.get(STORAGE_HOLIDAYS_KEY)
    saved_holiday_check_month = await page.shared_preferences.get(
        STORAGE_HOLIDAY_CHECK_MONTH_KEY
    )
    ONLINE_HOLIDAYS = safe_json_load(saved_online_holidays, dict, {})
    alarm_settings_state = AlarmSettings.from_dict(
        safe_json_load(saved_alarm_settings, dict, {})
    ).to_dict()
    alarm_runtime_state = {
        "notifications_granted": False,
        "exact_alarm_granted": False,
        "full_screen_granted": False,
        "last_sync_at": 0,
        "reserved_count": 0,
        "current_alarm_id": None,
        "message": "Android APK에서만 사용할 수 있습니다." if not is_native_android else "확인 중",
    }

    USER_SCHEDULES = normalize_schedules(safe_json_load(saved_schedules, dict, {}))
    routes_state = normalize_routes_state(safe_json_load(saved_routes, dict, {}))
    if routes_state.get("selected_company") not in DEPOT_ROUTES:
        companies = {c for r in routes_state["routes"] for c, nums in DEPOT_ROUTES.items() if str(r.get("route_number", "")).strip() in nums}
        routes_state["selected_company"] = next(iter(companies)) if len(companies) == 1 else ""
    MANGEUN_TARGETS = safe_json_load(saved_targets, dict, {})
    PHONEBOOK_LIST = normalize_contacts(safe_json_load(saved_phonebook, list, []))
    EMERGENCY_LIST = normalize_contacts(EMERGENCY_LIST)

    # 운행정보(내차/앞차/뒷차) 초기값 세팅
    _loaded_input_data = safe_json_load(saved_input_data, dict, None)
    input_data_state = normalize_input_data(_loaded_input_data)

    # 데이터 변경 시 스마트폰 저장소에 즉시 통합 저장하는 함수
    # (shared_preferences는 비동기 API라서 함수 자체는 async로 두고,
    #  호출하는 쪽에서는 page.run_task(save_all_to_client_storage)로 실행해서
    #  기존의 수많은 버튼 클릭 함수들을 전부 async로 바꾸지 않아도 되게 함)
    async def save_all_to_client_storage():
        await page.shared_preferences.set(STORAGE_SCHEDULES_KEY, json.dumps(USER_SCHEDULES, ensure_ascii=False))
        await page.shared_preferences.set(STORAGE_MANGEUN_KEY, json.dumps(MANGEUN_TARGETS, ensure_ascii=False))
        await page.shared_preferences.set(STORAGE_INPUT_DATA_KEY, json.dumps(input_data_state, ensure_ascii=False))
        await page.shared_preferences.set(STORAGE_PHONEBOOK_KEY, json.dumps(PHONEBOOK_LIST, ensure_ascii=False))
        await page.shared_preferences.set(STORAGE_EMERGENCY_KEY, json.dumps(EMERGENCY_LIST, ensure_ascii=False))
        await page.shared_preferences.set(STORAGE_PATTERN_KEY, json.dumps(pattern_state, ensure_ascii=False))
        await page.shared_preferences.set(STORAGE_MEMO_KEY, json.dumps(DATE_MEMOS, ensure_ascii=False))

    async def save_routes():
        await page.shared_preferences.set(STORAGE_ROUTES_KEY, json.dumps(routes_state, ensure_ascii=False))

    def sync_input_route_from_default():
        active_route = default_route(routes_state)
        if active_route is None:
            return False
        route_number = str(active_route.get("route_number", "") or "").strip() or "미입력"
        if input_data_state.get("route") == route_number:
            return False
        input_data_state["route"] = route_number
        return True

    if sync_input_route_from_default():
        await save_all_to_client_storage()

    async def save_alarm_settings():
        await page.shared_preferences.set(
            STORAGE_ALARM_SETTINGS_KEY,
            json.dumps(alarm_settings_state, ensure_ascii=False),
        )


    # 앱 켜질 때 오늘 날짜 및 시간 제어용 초기값 설정
    now_kst = datetime.now(KST)
    current = {"year": now_kst.year, "month": now_kst.month, "selected_date": f"{now_kst.year}-{now_kst.month:02d}-{now_kst.day:02d}"}
    selected_time_state = {"hour": None, "minute": None}

    current_tab = "달력"

    async def sync_online_holidays():
        nonlocal saved_holiday_check_month
        check_time = datetime.now(KST)
        if not should_check_holidays(saved_holiday_check_month, check_time):
            return
        try:
            downloaded = await asyncio.to_thread(download_holidays, HOLIDAY_UPDATE_URL, [check_time.year, check_time.year + 1])
            if downloaded:
                ONLINE_HOLIDAYS.update(downloaded)
                saved_holiday_check_month = check_time.strftime("%Y-%m")
                await page.shared_preferences.set(STORAGE_HOLIDAYS_KEY, json.dumps(ONLINE_HOLIDAYS, ensure_ascii=False))
                await page.shared_preferences.set(STORAGE_HOLIDAY_CHECK_MONTH_KEY, saved_holiday_check_month)
                print(f"[HolidaySync] updated={len(downloaded)} month={saved_holiday_check_month}", flush=True)
                rebuild_interface()
        except Exception as exc:
            print(f"[HolidaySync] skipped: {exc}", flush=True)

    # 📱 팝업 카드를 "교대자다3"처럼 화면 좌우 꽉 채운 시트 형태로 만드는 공용 헬퍼
    # inner_content: 카드 안에 들어갈 ft.Column 등 / top: 화면 상단에서부터의 여백(px)
    def make_full_width_sheet(inner_content, top=60, bottom=None):
        # bottom이 지정되면 top 대신 화면 하단 기준으로 배치 (엄지손가락이 닿기 편한 위치)
        position_kwargs = {"bottom": bottom} if bottom is not None else {"top": top}
        card = ft.Container(content=inner_content, bgcolor="white", padding=16, border_radius=16, left=0, right=0, **position_kwargs)
        return ft.Stack([card], expand=True)

    # 메인 상단 텍스트 레이블 선언
    month_title = ft.Text("", size=20, weight="bold", text_align="center")
    stats_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    morning_count_text = ft.Text("", size=11, weight="normal", color="#1E3A8A", offset=ft.Offset(0, -0.16))
    afternoon_count_text = ft.Text("", size=11, weight="normal", color="#1E3A8A")
    mangeun_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_value_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    annual_used_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    annual_remaining_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")

    calendar_grid = ft.Column(spacing=0)
    input_zone_container = ft.Column(spacing=2, visible=False)
    settings_zone_container = ft.Column(spacing=2, visible=False)

    phonebook_items_column = ft.Column(spacing=2)

    # [화면 구역] 📞 전화번호부 관리 페이지 레이아웃
    phonebook_zone_container = ft.Container(
        content=ft.Column([
            ft.Row([ft.Text("🚌 기사 연락처", size=16, weight="bold", color="#1E3A8A")]),
            ft.Divider(height=1),
            ft.Row([
                pb_name := ft.TextField(cursor_width=1, label="이름/직책", label_style=ft.TextStyle(size=11), width=100, height=38, text_size=13, content_padding=8),
                pb_phone := ft.TextField(cursor_width=1, label="전화번호(숫자만)", label_style=ft.TextStyle(size=11), expand=True, height=38, text_size=13, content_padding=8, keyboard_type=ft.KeyboardType.PHONE),
                ft.ElevatedButton(content=ft.Text("추가", size=12, weight="bold", color="white"), bgcolor="#2563EB", width=60, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e: add_phonebook_item())
            ], spacing=4),
            ft.Column(
                [
                    ft.Divider(height=1, color="#E2E8F0"),
                    phonebook_items_column,
                ],
                spacing=2,
            )
        ]),
        padding=ft.Padding.symmetric(horizontal=4, vertical=8), visible=False
    )

    # 📇 전화번호부는 이제 하단 '연락처' 탭 안에 통합되어 있음 (별도 큰 버튼 제거됨)

    # [하단 탭 메뉴 버튼] 기사님 디자인 피드백 반영 (텍스트 이모지 장착 및 한여름의 패딩 제거 버전)
    btn_status = ft.ElevatedButton(content=ft.Container(content=ft.Text("📊 근무현황", color="white", size=11, weight="bold"), alignment=ft.Alignment.CENTER), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: navigate_to("/status"))
    btn_setting = ft.ElevatedButton(content=ft.Container(content=ft.Text("📇 연락처", color="white", size=11, weight="bold"), alignment=ft.Alignment.CENTER), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: navigate_to("/emergency"))
    btn_config = ft.ElevatedButton(content=ft.Container(content=ft.Text("⚙️ 설정", color="white", size=11, weight="bold"), alignment=ft.Alignment.CENTER), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: navigate_to("/settings"))

    # ==========================================================
    # [UI 개선]
    # 달력 격자선을 연한 회색으로 변경
    # 기존보다 모바일 앱 느낌이 나도록 수정
    # ==========================================================
    CALENDAR_GRID_LINE_COLOR = "#D6D9DE"

    # 달력 최상단 요일 표시줄 (일~토)
    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row([ft.Container(content=ft.Text(d, size=13, weight="bold", color="#D93025" if d=="일" else ("#1A73E8" if d=="토" else "black")), expand=1, alignment=ft.Alignment(0, 0), padding=ft.Padding.symmetric(vertical=2), bgcolor="#E5E7EB", border=ft.Border.all(0.5, CALENDAR_GRID_LINE_COLOR)) for d in days_letters], alignment="spaceAround", spacing=0)
    calendar_table = ft.Column([weeks_header, calendar_grid], spacing=0)


    # 📞 전화번호부 목록을 화면에 다시 그려주는 함수 (일반연락처용)
    def rebuild_phonebook_view():
        phonebook_items_column.controls.clear()
        if not PHONEBOOK_LIST:
            phonebook_items_column.controls.append(ft.Container(content=ft.Text("등록된 연락처가 없습니다.\n자주 쓰는 번호를 상단에 등록해 보세요!", size=13, color="grey", text_align="center"), padding=20, alignment=ft.Alignment.CENTER))
        else:
            for index, item in enumerate(PHONEBOOK_LIST):
                name = item.get("name", "")
                phone = item.get("phone", "")
                row_content = ft.Row([
                    ft.Text(name, size=14, weight="bold", color="black", width=80, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(phone, size=13, weight="bold", color="#1E3A8A", no_wrap=True, expand=True),
                    ft.Row([
                        ft.IconButton(ft.Icons.PHONE, icon_color="green", icon_size=20, width=32, height=32, padding=0, on_click=lambda e, p=phone: make_call(p)),
                        ft.ElevatedButton(content=ft.Container(ft.Text("수정", size=10, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#2563EB", width=42, height=28, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e, idx=index: open_contact_edit_dialog("phonebook", idx)),
                    ], spacing=6, tight=True),
                ], alignment="spaceBetween", spacing=6)

                phonebook_items_column.controls.append(ft.Container(content=row_content, padding=ft.Padding.only(left=4, right=4, top=6, bottom=6), border=ft.border.Border(bottom=ft.border.BorderSide(0.5, "#E2E8F0"))))
        page.update()

    # 🚨 긴급연락처 목록을 화면에 다시 그려주는 함수 (사무실/정비실 최상단 고정 정렬 기능 포함)
    def rebuild_emergency_view(target_column):
        target_column.controls.clear()
        target_column.controls.append(emergency_form_container)

        def get_sort_key(item):
            name = item.get("name", "")
            if name == "사무실": return (0, "")
            elif name == "정비실": return (1, "")
            else: return (2, name)

        EMERGENCY_LIST.sort(key=get_sort_key)

        if len(EMERGENCY_LIST) == 0:
            target_column.controls.append(ft.Container(content=ft.Text("등록된 긴급 연락처가 없습니다.\n사무실, 정비실 번호를 등록해 보세요!", size=13, color="grey", text_align="center"), padding=20, alignment=ft.Alignment.CENTER))
        else:
            for index, item in enumerate(EMERGENCY_LIST):
                name = item.get("name", "")
                phone = item.get("phone", "")
                display_phone = phone if phone else "(번호 없음)"
                row_content = ft.Row([
                    ft.Text(name, size=14, weight="normal", color="black", width=80, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(display_phone, size=13, weight="bold", color="#1E3A8A", no_wrap=True, expand=True),
                    ft.Row([
                        ft.IconButton(ft.Icons.PHONE, icon_color="green", icon_size=20, width=32, height=32, padding=0, on_click=lambda e, ph=phone: make_call(ph)),
                        ft.ElevatedButton(content=ft.Container(ft.Text("수정", size=10, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#2563EB", width=42, height=28, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e, idx=index: open_contact_edit_dialog("emergency", idx)),
                    ], spacing=6, tight=True),
                ], alignment="spaceBetween", spacing=6)

                target_column.controls.append(ft.Container(content=row_content, padding=ft.Padding.only(left=4, right=4, top=6, bottom=6), border=ft.border.Border(bottom=ft.border.BorderSide(0.5, "#E2E8F0"))))
        page.update()

    # ⚙️ 설정 화면 - 반복 근무 패턴 선택 (예: 4일오전 4일오후 등 순환근무 자동 채우기)
    pattern_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    pending_pattern_name = {"value": None}
    popup_view_mode = {"mode": "list", "confirm_idx": None}

    def pattern_slot_color(slot_status):
        return {"오전": "#1A73E8", "오후": "#7E22CE", "휴무": "#D93025", "전일": "#137333", "근무": "#137333"}.get(slot_status, "black")

    def close_pattern_popup(e):
        pattern_popup_layer.visible = False
        pattern_select_box.content.value, pattern_select_box.content.color = "눌러서 선택하세요", "grey"
        page.update()

    def finish_pattern_apply(e):
        # ✅ 적용 완료 화면에서 확인을 누르면 설정화면에 머무르지 않고 바로 달력으로 이동해서
        # 방금 적용된 근무형태가 실제로 반영된 걸 바로 눈으로 확인할 수 있게 함
        pattern_popup_layer.visible = False
        pattern_select_box.content.value, pattern_select_box.content.color = "눌러서 선택하세요", "grey"
        navigate_to("/")
        page.update()

    def back_to_slot_list(e):
        popup_view_mode["mode"] = "list"
        popup_view_mode["confirm_idx"] = None
        build_pattern_popup()
        page.update()

    def select_pattern_slot(idx):
        popup_view_mode["mode"] = "confirm"
        popup_view_mode["confirm_idx"] = idx
        build_pattern_popup()
        page.update()

    def request_pattern_apply(idx):
        if pattern_state.get("history"):
            popup_view_mode["mode"] = "apply_scope"
            popup_view_mode["confirm_idx"] = idx
            build_pattern_popup()
            page.update()
            return
        apply_pattern(idx, ALL_MONTHS)

    def apply_pattern(idx, effective_month):
        today_str = datetime.now(KST).strftime("%Y-%m-%d")
        add_pattern_segment(
            pattern_state,
            pending_pattern_name["value"],
            today_str,
            idx,
            effective_month,
        )
        page.run_task(save_all_to_client_storage)
        page.run_task(reconcile_alarms, "work_pattern_applied")
        rebuild_settings_view(); rebuild_interface()
        popup_view_mode["mode"] = "done"
        popup_view_mode["applied_idx"] = idx
        popup_view_mode["applied_date"] = today_str
        popup_view_mode["applied_scope"] = (
            "전체 일정" if effective_month == ALL_MONTHS else f"{effective_month}월부터"
        )
        build_pattern_popup()
        page.update()

    def confirm_apply_pattern(e):
        request_pattern_apply(popup_view_mode["confirm_idx"])

    def apply_pattern_this_month(e):
        month_key = datetime.now(KST).strftime("%Y-%m")
        apply_pattern(popup_view_mode["confirm_idx"], month_key)

    def apply_pattern_next_month(e):
        today = datetime.now(KST)
        next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        apply_pattern(popup_view_mode["confirm_idx"], next_month.strftime("%Y-%m"))

    def clear_pattern(e):
        pattern_state["name"], pattern_state["anchor_date"], pattern_state["anchor_index"] = None, None, 0
        pattern_state["history"] = []
        page.run_task(save_all_to_client_storage)
        page.run_task(reconcile_alarms, "work_pattern_cleared")
        rebuild_settings_view(); rebuild_interface()

    def build_pattern_popup():
        pat = WORK_PATTERNS.get(pending_pattern_name["value"], [])
        if popup_view_mode["mode"] == "done":
            # ✅ 근무형태 선택 직후, 선택 전 화면으로 바로 돌아가면 뭐가 바뀌었는지 헷갈리므로
            # "적용 완료" 화면을 따로 보여줘서 지금 어떤 근무형태/오늘 상태로 적용됐는지 바로 확인 가능하게 함
            # → "교대자다3"처럼 전체 근무 주기를 박스로 보여주고, 오늘 선택한 칸만 초록색으로 강조 표시
            idx = popup_view_mode["applied_idx"]
            today_status = pat[idx] if idx < len(pat) else ""
            slot_chips = []
            for i, slot_status in enumerate(pat):
                is_today = (i == idx)
                slot_chips.append(ft.Container(
                    content=ft.Text(slot_status, size=15, weight="bold", color="#137333" if is_today else pattern_slot_color(slot_status)),
                    width=76, height=52, alignment=ft.Alignment.CENTER, border_radius=8,
                    bgcolor="#DCFCE7" if is_today else "#F1F5F9",
                    border=ft.Border.all(2, "#16A34A") if is_today else None,
                ))
            pattern_popup_layer.content = make_full_width_sheet(ft.Column([
                    ft.Text("✅ 근무형태 적용 완료", size=16, weight="bold", color="#137333"),
                    ft.Divider(height=1),
                    ft.Text(f"근무형태: {pending_pattern_name['value']}", size=14, weight="bold", color="black"),
                    ft.Text(f"기준일: {popup_view_mode['applied_date']}  (초록색 칸이 오늘 근무: {today_status})", size=12, color="grey"),
                    ft.Text(f"적용 범위: {popup_view_mode['applied_scope']}", size=12, color="#2563EB"),
                    ft.Row(slot_chips, wrap=True, spacing=6, run_spacing=6),
                    ft.Text("직접 입력한 날짜와 이전 근무 이력은 그대로 유지됩니다.", size=12, color="grey"),
                    ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#2563EB", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=finish_pattern_apply)], spacing=8),
                ], spacing=10, tight=True, horizontal_alignment="stretch"))
            return
        if popup_view_mode["mode"] == "apply_scope":
            pattern_popup_layer.content = make_full_width_sheet(ft.Column([
                    ft.Text("근무형태 변경", size=16, weight="bold", color="black"),
                    ft.Text("새 근무형태를 언제부터 적용할까요?\n이전 기간의 근무 이력은 그대로 유지됩니다.", size=13, color="black", text_align="center"),
                    ft.ElevatedButton(content=ft.Text("이번 달부터 적용", size=14, weight="bold"), height=42, bgcolor="#2563EB", color="white", on_click=apply_pattern_this_month),
                    ft.ElevatedButton(content=ft.Text("다음 달부터 적용", size=14, weight="bold"), height=42, bgcolor="#1E3A8A", color="white", on_click=apply_pattern_next_month),
                    ft.ElevatedButton(content=ft.Text("취소", size=14, weight="bold"), height=38, bgcolor="grey", color="white", on_click=back_to_slot_list),
                ], spacing=10, tight=True, horizontal_alignment="stretch"))
            return
        if pending_pattern_name["value"] == "격일제":
            # 🔁 격일제는 근무/휴무 2가지뿐이라 "몇 번째 근무"를 물어볼 필요가 없음
            # → 오늘이 근무인지 휴무인지만 고르면 그 기준으로 이후 날짜가 하루씩 번갈아 자동 채워짐
            pattern_popup_layer.content = make_full_width_sheet(ft.Column([
                    ft.Text("오늘 격일제 근무를 선택하세요", size=15, weight="bold", color="black"),
                    ft.Text("선택한 상태를 기준으로 이후 근무/휴무가 하루씩 번갈아 자동 설정됩니다.", size=12, color="grey"),
                    ft.Row([
                        ft.ElevatedButton(content=ft.Container(ft.Text("오늘 근무", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#137333", expand=1, height=44, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: request_pattern_apply(0)),
                        ft.ElevatedButton(content=ft.Container(ft.Text("오늘 휴무", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#D93025", expand=1, height=44, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: request_pattern_apply(1)),
                    ], spacing=8),
                    ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("닫기", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="grey", expand=1, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=close_pattern_popup)], spacing=8),
                ], spacing=14, tight=True, horizontal_alignment="stretch"))
            return
        if popup_view_mode["mode"] == "confirm" and popup_view_mode["confirm_idx"] is not None:
            idx = popup_view_mode["confirm_idx"]
            slot_status = pat[idx] if idx < len(pat) else ""
            pattern_popup_layer.content = make_full_width_sheet(ft.Column([
                    ft.Text(f"{pending_pattern_name['value']}", size=15, weight="bold", color="black"),
                    ft.Text(f"오늘을 {idx+1}번째 근무({slot_status})로\n적용하시겠습니까?", size=14, color="black", text_align="center"),
                    ft.Row([
                        ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#2563EB", expand=1, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=confirm_apply_pattern),
                        ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="grey", expand=1, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=back_to_slot_list),
                    ], spacing=8),
                ], spacing=14, tight=True, horizontal_alignment="stretch"))
        else:
            slot_rows = []
            for i, slot_status in enumerate(pat):
                slot_rows.append(
                    ft.Container(
                        content=ft.Text(f"{i+1}. {slot_status}", size=14, weight="bold", color=pattern_slot_color(slot_status)),
                        bgcolor="#F1F5F9", alignment=ft.Alignment.CENTER_LEFT,
                        padding=ft.Padding.symmetric(vertical=10, horizontal=14), border_radius=6,
                        on_click=lambda e, idx=i: select_pattern_slot(idx),
                    )
                )
            pattern_popup_layer.content = make_full_width_sheet(ft.Column([
                    ft.Text(f"오늘 근무선택 ({pending_pattern_name['value']})", size=15, weight="bold", color="black"),
                    ft.Text("오늘이 몇 번째 근무인지 선택하세요.", size=12, color="grey"),
                    ft.Column(slot_rows, spacing=6, scroll=ft.ScrollMode.AUTO, height=min(360, len(pat) * 48), horizontal_alignment="stretch"),
                    ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("닫기", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="grey", expand=1, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=close_pattern_popup)], spacing=8),
                ], spacing=10, tight=True, horizontal_alignment="stretch"))

    def open_pattern_popup(pattern_name):
        pending_pattern_name["value"] = pattern_name
        popup_view_mode["mode"], popup_view_mode["confirm_idx"] = "list", None
        build_pattern_popup()
        pattern_popup_layer.visible = True
        page.update()

    pattern_name_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)

    def close_pattern_name_popup(e=None):
        pattern_name_popup_layer.visible = False
        page.update()

    def pick_pattern_name(name):
        pattern_name_popup_layer.visible = False
        pattern_select_box.content.value, pattern_select_box.content.color = name, "black"
        open_pattern_popup(name)

    def pick_direct_input(e=None):
        pattern_name_popup_layer.visible = False
        clear_pattern(None)

    def open_pattern_name_popup(e=None):
        direct_row = ft.Container(content=ft.Text("직접입력 (패턴 사용 안함)", size=15, weight="bold", color="grey"), alignment=ft.Alignment.CENTER_LEFT, padding=ft.Padding.symmetric(vertical=10, horizontal=14), border_radius=6, bgcolor="#F1F5F9", on_click=pick_direct_input)
        rows = [ft.Container(content=ft.Text(name, size=15, weight="bold", color="black"), alignment=ft.Alignment.CENTER_LEFT, padding=ft.Padding.symmetric(vertical=10, horizontal=14), border_radius=6, bgcolor="#F1F5F9", on_click=lambda e, n=name: pick_pattern_name(n)) for name in WORK_PATTERNS.keys()]
        all_rows = [direct_row] + rows
        pattern_name_popup_layer.content = make_full_width_sheet(ft.Column([
                ft.Text("근무형태 선택", size=16, weight="bold", color="black"),
                ft.Column(all_rows, spacing=6, scroll=ft.ScrollMode.AUTO, height=min(340, len(all_rows) * 48), horizontal_alignment="stretch"),
                ft.Divider(height=1),
                ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="grey", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=close_pattern_name_popup)], spacing=8),
            ], spacing=10, tight=True, horizontal_alignment="stretch"))
        pattern_name_popup_layer.visible = True
        page.update()

    pattern_select_box = ft.Container(content=ft.Text("눌러서 선택하세요", size=13, color="grey"), height=44, border=ft.Border.all(1, "#94A3B8"), border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=10), alignment=ft.Alignment.CENTER_LEFT, on_click=open_pattern_name_popup)
    pattern_status_text = ft.Text("", size=12, color="grey")

    def format_sync_time(epoch_millis):
        if not epoch_millis:
            return "없음"
        return datetime.fromtimestamp(epoch_millis / 1000, KST).strftime("%Y-%m-%d %H:%M")

    def refresh_alarm_controls():
        supported = alarm_service is not None
        alarm_master_switch.value = alarm_settings_state["enabled"]
        alarm_morning_switch.value = alarm_settings_state["morning_enabled"]
        alarm_afternoon_switch.value = alarm_settings_state["afternoon_enabled"]
        alarm_morning_time.value = alarm_settings_state["morning_time"]
        alarm_afternoon_time.value = alarm_settings_state["afternoon_time"]
        for control in (
            alarm_master_switch, alarm_morning_switch, alarm_afternoon_switch,
            alarm_morning_time, alarm_afternoon_time, notification_permission_button,
            exact_alarm_permission_button, test_alarm_button, stop_alarm_button,
            full_screen_permission_button,
        ):
            control.disabled = not supported
        notification_permission_button.content.value = (
            "허용됨" if alarm_runtime_state["notifications_granted"] else "허용 필요"
        )
        exact_alarm_permission_button.content.value = (
            "허용됨" if alarm_runtime_state["exact_alarm_granted"] else "설정 필요"
        )
        full_screen_permission_button.content.value = (
            "허용됨" if alarm_runtime_state["full_screen_granted"] else "설정 필요"
        )
        alarm_last_sync_text.value = format_sync_time(alarm_runtime_state["last_sync_at"])
        alarm_reserved_count_text.value = f"{alarm_runtime_state['reserved_count']}개"
        alarm_current_text.value = alarm_runtime_state["current_alarm_id"] or "없음"
        alarm_message_text.value = alarm_runtime_state["message"]

    async def refresh_alarm_status(e=None):
        if alarm_service is None:
            refresh_alarm_controls()
            return
        try:
            permission = await alarm_service.get_permission_status()
            snapshot = await alarm_service.get_native_snapshot()
            diagnostics = snapshot.get("diagnostics", {}) if isinstance(snapshot, dict) else {}
            alarms = snapshot.get("alarms", []) if isinstance(snapshot, dict) else []
            alarm_runtime_state.update({
                "notifications_granted": permission.get("notifications_granted", False),
                "exact_alarm_granted": permission.get("exact_alarm_granted", False),
                "full_screen_granted": permission.get("full_screen_granted", False),
                "last_sync_at": diagnostics.get("last_sync_at", 0),
                "reserved_count": len(alarms) if isinstance(alarms, list) else 0,
                "current_alarm_id": diagnostics.get("current_alarm_id"),
                "message": "",
            })
        except Exception as exc:
            alarm_runtime_state["message"] = f"상태 확인 실패: {exc}"
            print(f"[Permission] status failed: {exc}", flush=True)
        refresh_alarm_controls()
        page.update()

    async def reconcile_alarms(reason="manual"):
        now = datetime.now(KST)
        expired_count = clear_expired_date_alarms(now)
        if expired_count:
            await save_all_to_client_storage()
            print(f"[Reconcile] expired_date_alarms_cleared={expired_count}", flush=True)
        if alarm_service is None:
            return {"native_scheduling": False, "reason": "android_only"}
        print(f"[Reconcile] started reason={reason}", flush=True)
        try:
            now = datetime.now(KST)
            alarms = build_desired_alarms(
                start_date=now.date(),
                get_day_info=get_effective_day_info,
                settings=AlarmSettings.from_dict(alarm_settings_state),
                timezone=KST,
                now=now,
                days=90,
            )
            snapshot = {
                "schema_version": SCHEMA_VERSION,
                "generated_at": int(now.timestamp() * 1000),
                "alarms": [alarm.to_dict() for alarm in alarms],
            }
            result = await alarm_service.reconcile(snapshot)
            alarm_runtime_state.update({
                "last_sync_at": result.get("last_sync_at", int(now.timestamp() * 1000)),
                "reserved_count": result.get("reserved_count", len(alarms)),
                "message": "" if not result.get("failed") else f"예약 실패 {result['failed']}개",
            })
            print(
                f"[Reconcile] scheduled={result.get('scheduled', 0)} "
                f"updated={result.get('updated', 0)} cancelled={result.get('cancelled', 0)}",
                flush=True,
            )
            await refresh_alarm_status()
            return result
        except Exception as exc:
            alarm_runtime_state["message"] = f"동기화 실패: {exc}"
            print(f"[Reconcile] failed reason={reason}: {exc}", flush=True)
            refresh_alarm_controls()
            page.update()
            return {"native_scheduling": False, "error": str(exc)}

    async def update_alarm_option(key, value):
        alarm_settings_state[key] = bool(value)
        alarm_settings_summary_text.value = "사용 중" if alarm_settings_state["enabled"] else "사용 안 함"
        await save_alarm_settings()
        await reconcile_alarms(key)
        if key == "enabled" and value and not alarm_runtime_state["notifications_granted"]:
            alarm_runtime_state["message"] = "알림·정확한 알람·전체 화면 권한을 확인해 주세요."
            await request_notification_permission()
        if key == "enabled" and not value:
            await stop_alarm_now()

    async def update_alarm_time(key, control):
        candidate = (control.value or "").strip()
        updated = dict(alarm_settings_state)
        updated[key] = candidate
        try:
            normalized = AlarmSettings.from_dict(updated).to_dict()[key]
        except ValueError:
            control.value = alarm_settings_state[key]
            alarm_runtime_state["message"] = "시간은 00:00~23:59 형식으로 입력하세요."
            refresh_alarm_controls()
            page.update()
            return
        alarm_settings_state[key] = normalized
        control.value = normalized
        await save_alarm_settings()
        await reconcile_alarms(key)

    async def request_notification_permission(e=None):
        if alarm_service is None:
            return
        result = await alarm_service.request_notification_permission()
        alarm_runtime_state["notifications_granted"] = result.get("notifications_granted", False)
        print(f"[Permission] Notification granted={alarm_runtime_state['notifications_granted']}", flush=True)
        await reconcile_alarms("notification_permission")

    async def request_exact_alarm_permission(e=None):
        if alarm_service is None:
            return
        result = await alarm_service.open_exact_alarm_settings()
        alarm_runtime_state["exact_alarm_granted"] = result.get("exact_alarm_granted", False)
        print(f"[Permission] Exact alarm granted={alarm_runtime_state['exact_alarm_granted']}", flush=True)
        await reconcile_alarms("exact_alarm_permission")

    async def request_full_screen_permission(e=None):
        if alarm_service is None:
            return
        result = await alarm_service.open_full_screen_settings()
        alarm_runtime_state["full_screen_granted"] = result.get("full_screen_granted", False)
        print(f"[Permission] Full screen granted={alarm_runtime_state['full_screen_granted']}", flush=True)
        await refresh_alarm_status()

    async def run_test_alarm(e=None):
        if alarm_service is None:
            return
        print("[TestAlarm] started", flush=True)
        try:
            result = await alarm_service.test_alarm()
            alarm_runtime_state["current_alarm_id"] = result.get("alarm_id")
            alarm_runtime_state["message"] = (
                f"테스트 알람 실행: {result.get('alarm_id', '')}" if result.get("started")
                else "테스트 알람을 시작하지 못했습니다."
            )
            print("[TestAlarm] completed", flush=True)
        except Exception as exc:
            alarm_runtime_state["message"] = f"테스트 알람 실패: {exc}"
            print(f"[TestAlarm] failed: {exc}", flush=True)
        refresh_alarm_controls()
        page.update()

    async def stop_alarm_now(e=None):
        if alarm_service is None:
            return
        print("[AlarmStop] requested", flush=True)
        try:
            await alarm_service.stop_ringing()
            alarm_runtime_state["current_alarm_id"] = None
            alarm_runtime_state["message"] = "알람을 껐습니다."
            print("[AlarmStop] completed", flush=True)
        except Exception as exc:
            alarm_runtime_state["message"] = f"알람 끄기 실패: {exc}"
            print(f"[AlarmStop] failed: {exc}", flush=True)
        refresh_alarm_controls()
        page.update()

    alarm_master_switch = ft.Switch(
        label="알람 사용", value=alarm_settings_state["enabled"],
        on_change=lambda e: page.run_task(update_alarm_option, "enabled", e.control.value),
    )
    alarm_morning_switch = ft.Switch(
        label="사용", value=alarm_settings_state["morning_enabled"],
        on_change=lambda e: page.run_task(update_alarm_option, "morning_enabled", e.control.value),
    )
    alarm_afternoon_switch = ft.Switch(
        label="사용", value=alarm_settings_state["afternoon_enabled"],
        on_change=lambda e: page.run_task(update_alarm_option, "afternoon_enabled", e.control.value),
    )
    alarm_morning_time = ft.TextField(
        label="시간", value=alarm_settings_state["morning_time"], width=110, height=42,
        text_size=13, keyboard_type=ft.KeyboardType.DATETIME,
        on_blur=lambda e: page.run_task(update_alarm_time, "morning_time", e.control),
        on_submit=lambda e: page.run_task(update_alarm_time, "morning_time", e.control),
    )
    alarm_afternoon_time = ft.TextField(
        label="시간", value=alarm_settings_state["afternoon_time"], width=110, height=42,
        text_size=13, keyboard_type=ft.KeyboardType.DATETIME,
        on_blur=lambda e: page.run_task(update_alarm_time, "afternoon_time", e.control),
        on_submit=lambda e: page.run_task(update_alarm_time, "afternoon_time", e.control),
    )
    notification_permission_button = ft.TextButton(
        content=ft.Text("허용 필요"), on_click=lambda e: page.run_task(request_notification_permission)
    )
    exact_alarm_permission_button = ft.TextButton(
        content=ft.Text("설정 필요"), on_click=lambda e: page.run_task(request_exact_alarm_permission)
    )
    full_screen_permission_button = ft.TextButton(
        content=ft.Text("설정 필요"), on_click=lambda e: page.run_task(request_full_screen_permission)
    )
    test_alarm_button = ft.ElevatedButton(
        "지금 울려보기", icon=ft.Icons.ALARM, bgcolor="#2563EB", color="white", expand=1,
        on_click=lambda e: page.run_task(run_test_alarm),
    )
    stop_alarm_button = ft.ElevatedButton(
        "현재 알람 끄기", icon=ft.Icons.STOP_CIRCLE, bgcolor="#D93025", color="white", expand=1,
        on_click=lambda e: page.run_task(stop_alarm_now),
    )
    alarm_last_sync_text = ft.Text("없음", size=12, weight="bold")
    alarm_reserved_count_text = ft.Text("0개", size=12, weight="bold")
    alarm_current_text = ft.Text("없음", size=12, weight="bold")
    alarm_message_text = ft.Text("", size=11, color="#D93025")
    alarm_settings_summary_text = ft.Text("사용 안 함", size=12, color="#64748B")

    def close_alarm_settings_popup(e=None):
        alarm_settings_popup_layer.visible = False
        page.update()

    def open_alarm_settings_popup(e=None):
        refresh_alarm_controls()
        alarm_settings_popup_layer.content = make_full_width_sheet(
            ft.Column([
                ft.Text("⏰ 알람 설정", size=16, weight="bold", color="#1E3A8A"),
                alarm_master_switch,
                ft.Divider(height=1),
                ft.Text("오전근무 기본 알람", size=13, weight="bold"),
                ft.Row([alarm_morning_switch, alarm_morning_time], alignment="spaceBetween"),
                ft.Text("오후근무 기본 알람", size=13, weight="bold"),
                ft.Row([alarm_afternoon_switch, alarm_afternoon_time], alignment="spaceBetween"),
                ft.Divider(height=1),
                ft.Row([ft.Text("알림 권한", size=12), notification_permission_button], alignment="spaceBetween"),
                ft.Row([ft.Text("정확한 알람 권한", size=12), exact_alarm_permission_button], alignment="spaceBetween"),
                ft.Row([ft.Text("전체 화면 알람 권한", size=12), full_screen_permission_button], alignment="spaceBetween"),
                ft.Row([test_alarm_button, stop_alarm_button], spacing=6),
                ft.Divider(height=1),
                ft.Row([ft.Text("마지막 동기화", size=11, color="grey"), alarm_last_sync_text], alignment="spaceBetween"),
                ft.Row([ft.Text("예약된 알람", size=11, color="grey"), alarm_reserved_count_text], alignment="spaceBetween"),
                ft.Row([ft.Text("현재 울리는 알람", size=11, color="grey"), alarm_current_text], alignment="spaceBetween"),
                alarm_message_text,
                ft.ElevatedButton("닫기", bgcolor="#64748B", color="white", on_click=close_alarm_settings_popup),
            ], spacing=6, tight=True, scroll=ft.ScrollMode.AUTO, height=530,
               horizontal_alignment="stretch"),
            top=45,
        )
        alarm_settings_popup_layer.visible = True
        if alarm_service is not None:
            page.run_task(refresh_alarm_status)
        page.update()

    route_editor_state = {
        "draft": None,
        "time_fields": {},
        "time_values": {},
        "view": None,
        "delete_confirm_id": None,
    }
    route_message_text = ft.Text("", size=11, color="#D93025")
    route_number_field = ft.TextField(label="노선번호", height=44, text_size=13)
    weekday_count_field = ft.TextField(label="평일 운행대수", height=44, text_size=13, keyboard_type=ft.KeyboardType.NUMBER)
    saturday_count_field = ft.TextField(label="토요일 운행대수", height=44, text_size=13, keyboard_type=ft.KeyboardType.NUMBER)
    sunday_count_field = ft.TextField(label="일요일(공휴일) 운행대수", height=44, text_size=13, keyboard_type=ft.KeyboardType.NUMBER)

    def close_route_popup(e=None):
        route_settings_popup_layer.visible = False
        page.update()

    def is_company_route_number(route_number):
        number = str(route_number or "").strip()
        return any(number in route_numbers for route_numbers in DEPOT_ROUTES.values())

    def company_route_label(route_number):
        number = str(route_number or "").strip()
        return number if number.startswith("급행") else f"{number}번"

    def register_company_route(depot, route_number):
        number = str(route_number or "").strip()
        if number not in DEPOT_ROUTES.get(depot, ()):
            return
        selected_company = routes_state.get("selected_company", "")
        if selected_company in DEPOT_ROUTES and selected_company != depot:
            return
        if any(str(route.get("route_number", "")).strip() == number for route in routes_state["routes"]):
            show_route_list()
            route_message_text.value = f"{company_route_label(number)} 노선은 이미 등록돼 있습니다."
            page.update()
            return
        route = {
            "id": f"company-route-{number}-{int(datetime.now(KST).timestamp() * 1000)}",
            "route_number": number,
            "fleet_counts": {
                "weekday": company_fleet_count(number, SERVICE_WEEKDAY),
                "saturday": company_fleet_count(number, SERVICE_SATURDAY),
                "sunday": company_fleet_count(number, SERVICE_SUNDAY_HOLIDAY),
            },
            "first_trip_times": empty_times(),
        }
        routes_state["routes"].append(route)
        if not routes_state["default_route_id"]:
            routes_state["default_route_id"] = route["id"]
        routes_state["selected_company"] = depot
        sync_input_route_from_default()
        page.run_task(save_routes)
        page.run_task(save_all_to_client_storage)
        rebuild_interface()
        show_route_list()
        route_message_text.value = f"{depot} {company_route_label(number)} 노선을 등록했습니다."
        route_message_text.color = "#137333"
        page.update()

    def open_company_route_picker(depot):
        route_editor_state["view"] = "company_routes"
        buttons = []
        registered = {
            str(route.get("route_number", "")).strip()
            for route in routes_state["routes"]
        }
        for number in DEPOT_ROUTES.get(depot, ()):
            already_registered = number in registered
            buttons.append(
                ft.ElevatedButton(
                    company_route_label(number) + (" · 등록됨" if already_registered else ""),
                    disabled=already_registered,
                    bgcolor="#CBD5E1" if already_registered else "#2563EB",
                    color="white",
                    height=42,
                    on_click=lambda e, d=depot, n=number: register_company_route(d, n),
                )
            )
        locked = routes_state.get("selected_company") in DEPOT_ROUTES
        picker_actions = [ft.ElevatedButton("취소", expand=1, bgcolor="grey", color="white", on_click=close_route_popup)]
        if not locked:
            picker_actions.insert(0, ft.ElevatedButton("뒤로가기", expand=1, bgcolor="#64748B", color="white", on_click=open_company_depot_picker))
        route_settings_popup_layer.content = make_full_width_sheet(
            ft.Column([
                ft.Text(f"{depot} 노선 선택", size=16, weight="bold", color="#1E3A8A"),
                ft.Text("등록할 노선을 선택하세요.", size=12, color="#64748B"),
                ft.Column(buttons, spacing=8, horizontal_alignment="stretch"),
                ft.Row(picker_actions, spacing=8),
            ], spacing=10, tight=True, horizontal_alignment="stretch"),
            top=90,
        )
        route_settings_popup_layer.visible = True
        page.update()

    def open_company_depot_picker(e=None):
        route_editor_state["view"] = "company_depot"
        depot_buttons = [
            ft.ElevatedButton(
                depot, bgcolor="#2563EB", color="white", height=46,
                on_click=lambda e, d=depot: open_company_route_picker(d),
            )
            for depot in DEPOT_ROUTES
        ]
        route_settings_popup_layer.content = make_full_width_sheet(
            ft.Column([
                ft.Text("노선 추가", size=16, weight="bold", color="#1E3A8A"),
                ft.Text("회사를 선택하세요.", size=12, color="#64748B"),
                *depot_buttons,
                ft.ElevatedButton("취소", bgcolor="#64748B", color="white", on_click=close_route_popup),
            ], spacing=10, tight=True, horizontal_alignment="stretch"),
            top=110,
        )
        route_settings_popup_layer.visible = True
        page.update()

    def open_company_route_add(e=None):
        company = routes_state.get("selected_company", "")
        open_company_route_picker(company) if company in DEPOT_ROUTES else open_company_depot_picker()

    def set_default_route(route_id):
        routes_state["default_route_id"] = route_id
        sync_input_route_from_default()
        page.run_task(save_routes)
        page.run_task(save_all_to_client_storage)
        rebuild_interface()
        show_route_list()

    def delete_route(route_id):
        used_count = sum(
            1 for info in USER_SCHEDULES.values()
            if isinstance(info, dict) and info.get("route_id") == route_id
        )
        route = find_route(routes_state, route_id)
        route_number = route["route_number"] if route else ""
        history_notice = (
            f"\n과거 사용 일정 {used_count}건의 노선·순번 기록은 그대로 보존됩니다."
            if used_count else ""
        )
        route_settings_popup_layer.content = make_full_width_sheet(
            ft.Column(
                [
                    ft.Text("노선 삭제", size=16, weight="bold", color="#D93025"),
                    ft.Text(
                        f"{route_number}번 노선을 삭제하시겠습니까?{history_notice}",
                        size=13,
                        color="black",
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "취소",
                                expand=1,
                                bgcolor="#64748B",
                                color="white",
                                on_click=show_route_list,
                            ),
                            ft.ElevatedButton(
                                "확인",
                                expand=1,
                                bgcolor="#D93025",
                                color="white",
                                on_click=lambda e, rid=route_id: confirm_delete_route(rid),
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=14,
                tight=True,
                horizontal_alignment="stretch",
            ),
            top=120,
        )
        route_settings_popup_layer.visible = True
        page.update()

    def confirm_delete_route(route_id):
        routes_state["routes"] = [
            route for route in routes_state["routes"] if route["id"] != route_id
        ]
        if routes_state["default_route_id"] == route_id:
            routes_state["default_route_id"] = (
                routes_state["routes"][0]["id"] if routes_state["routes"] else ""
            )
        if not routes_state["routes"]:
            routes_state["selected_company"] = ""

        # 삭제일 이전 일정은 노선 스냅샷을 보존하고, 오늘 이후 일정만
        # 남아 있는 기본 노선으로 안전하게 전환한다.
        today_key = datetime.now(KST).strftime("%Y-%m-%d")
        replacement = default_route(routes_state)
        for date_key, info in USER_SCHEDULES.items():
            if date_key < today_key or info.get("route_id") != route_id:
                continue
            if replacement is None:
                info["route_id"] = ""
                info["route_number"] = ""
                info["start_time_override"] = bool(info.get("start_time"))
                continue
            info["route_id"] = replacement["id"]
            info["route_number"] = replacement["route_number"]
            day_type = day_type_for_date(date_key, lambda key: bool(get_holiday_name(key)))
            order = str(info.get("order_no", "") or "")
            service_type = service_for_date(replacement["route_number"], day_type, "")
            maximum = company_fleet_count(replacement["route_number"], service_type) or fleet_count(replacement, day_type)
            if order and (not order.isdigit() or int(order) > maximum):
                info["order_no"] = ""
                info["start_time"] = ""
                info["departure"] = ""
                info["start_time_override"] = False
            elif info.get("start_time_override") is not True:
                company_item = lookup_schedule(
                    replacement["route_number"], service_type,
                    info.get("status", ""), order,
                )
                info["service_type"] = service_type
                info["start_time"] = company_item["time"] if company_item else first_trip_time(
                    replacement, day_type, info.get("status", ""), order
                )
                info["departure"] = company_item.get("departure", "") if company_item else ""

        sync_input_route_from_default()
        page.run_task(save_routes)
        page.run_task(save_all_to_client_storage)
        page.run_task(reconcile_alarms, "route_deleted")
        rebuild_interface()
        show_route_list()

    def show_route_list(e=None):
        route_editor_state["view"] = "list"
        rows = []
        for route in routes_state["routes"]:
            is_default = route["id"] == routes_state["default_route_id"]
            rows.append(ft.Container(content=ft.Column([
                ft.Row([
                    ft.Column([ft.Text(f"{route['route_number']}번", size=15, weight="bold"), ft.Text("기본 노선" if is_default else "등록 노선", size=11, color="#2563EB" if is_default else "grey")], spacing=1),
                    ft.Row([
                        ft.TextButton("기본지정", disabled=is_default, on_click=lambda e, rid=route["id"]: set_default_route(rid)),
                        ft.TextButton("수정", visible=not is_company_route_number(route["route_number"]), on_click=lambda e, rid=route["id"]: open_route_form(rid)),
                        ft.TextButton("삭제", on_click=lambda e, rid=route["id"]: delete_route(rid)),
                    ], spacing=0),
                ], alignment="spaceBetween"),
                ft.Text(f"평일 {route['fleet_counts']['weekday']}대 · 토요일 {route['fleet_counts']['saturday']}대 · 일요일/공휴일 {route['fleet_counts']['sunday']}대", size=11, color="#64748B"),
            ], spacing=3), padding=10, border=ft.Border.all(1, "#E2E8F0"), border_radius=8))
        if not rows:
            rows.append(ft.Text("등록된 노선이 없습니다. 노선을 먼저 등록해 주세요.", size=12, color="grey"))
        route_message_text.value = ""
        route_message_text.color = "#D93025"
        company = routes_state.get("selected_company", "")
        company_notice = ft.Text(f"현재 선택한 회사는 {company}입니다.", size=12, weight="bold", color="#1E3A8A") if company in DEPOT_ROUTES else ft.Container(height=0)
        route_settings_popup_layer.content = make_full_width_sheet(ft.Column([
            ft.Text("🚌 노선지정", size=16, weight="bold", color="#1E3A8A"),
            company_notice,
            ft.Column(rows, spacing=6, scroll=ft.ScrollMode.AUTO, height=350),
            route_message_text,
            ft.ElevatedButton("노선 추가", icon=ft.Icons.ADD, bgcolor="#2563EB", color="white", on_click=open_company_route_add),
            ft.ElevatedButton("닫기", bgcolor="#64748B", color="white", on_click=close_route_popup),
        ], spacing=8, tight=True, horizontal_alignment="stretch"), top=45)
        route_settings_popup_layer.visible = True
        page.update()

    def open_route_form(route_id=None):
        route_editor_state["view"] = "basic"
        pending_draft = route_editor_state.get("draft")
        reuse_pending = bool(
            route_id and pending_draft and pending_draft.get("id") == route_id
        )
        if not reuse_pending:
            route_editor_state["time_values"] = {}
        existing = pending_draft if reuse_pending else (find_route(routes_state, route_id) if route_id else None)
        draft = json.loads(json.dumps(existing, ensure_ascii=False)) if existing else {
            "id": f"route-{int(datetime.now(KST).timestamp() * 1000)}",
            "route_number": "", "fleet_counts": {"weekday": 0, "saturday": 0, "sunday": 0},
            "first_trip_times": empty_times(),
        }
        route_editor_state["draft"] = draft
        route_number_field.value = draft["route_number"]
        weekday_count_field.value = str(draft["fleet_counts"]["weekday"] or "")
        saturday_count_field.value = str(draft["fleet_counts"]["saturday"] or "")
        sunday_count_field.value = str(draft["fleet_counts"]["sunday"] or "")
        route_message_text.value = ""
        route_settings_popup_layer.content = make_full_width_sheet(ft.Column([
            ft.Text("노선 기본정보", size=16, weight="bold", color="#1E3A8A"),
            route_number_field, weekday_count_field, saturday_count_field, sunday_count_field,
            ft.Text("운행대수를 줄여도 숨겨진 상위 순번 시간은 안전하게 보존됩니다.", size=11, color="#64748B"),
            route_message_text,
            ft.Row([
                ft.ElevatedButton("취소", expand=1, bgcolor="#64748B", color="white", on_click=close_route_popup),
                ft.ElevatedButton("다음", expand=1, bgcolor="#2563EB", color="white", on_click=open_route_times),
            ], spacing=8),
            # 모바일 키보드가 열린 상태에서도 마지막 입력칸과 버튼을
            # 충분히 위로 올릴 수 있도록 하단 스크롤 여백을 둔다.
            ft.Container(height=120),
        ], spacing=8, tight=True, horizontal_alignment="stretch",
           scroll=ft.ScrollMode.AUTO, height=330), top=12)
        page.update()

    def format_route_time_input(e):
        control = e.control
        raw = (control.value or "").strip()
        if len(raw) == 4 and raw.isdigit():
            normalized = valid_time(raw)
            if normalized:
                control.value = normalized
                control.update()

    def back_from_route_times(e=None):
        # 아직 저장하지 않은 입력 문자열까지 그대로 보존한다.
        route_editor_state["time_values"] = {
            key: (control.value or "")
            for key, control in route_editor_state["time_fields"].items()
        }
        draft = route_editor_state.get("draft")
        open_route_form(draft["id"] if draft else None)

    def open_route_times(e=None):
        number = (route_number_field.value or "").strip()
        values = [weekday_count_field.value, saturday_count_field.value, sunday_count_field.value]
        if not number or any(not str(value or "").isdigit() or int(value) < 1 for value in values):
            route_message_text.value = "노선번호와 1대 이상의 운행대수를 숫자로 입력해 주세요."
            page.update()
            return
        draft = route_editor_state["draft"]
        draft["route_number"] = number
        draft["fleet_counts"] = dict(zip(DAY_TYPES, map(int, values)))
        route_editor_state["view"] = "times"
        fields, sections = {}, []
        labels = {"weekday": "평일", "saturday": "토요일", "sunday": "일요일·공휴일"}
        for day in DAY_TYPES:
            controls = []
            for order in range(1, draft["fleet_counts"][day] + 1):
                morning_key = (day, "morning", str(order))
                afternoon_key = (day, "afternoon", str(order))
                morning = ft.TextField(label="오전", value=route_editor_state["time_values"].get(morning_key, draft["first_trip_times"][day]["morning"].get(str(order), "")), hint_text="HH:MM", width=112, height=40, text_size=12, keyboard_type=ft.KeyboardType.DATETIME, on_change=format_route_time_input)
                afternoon = ft.TextField(label="오후", value=route_editor_state["time_values"].get(afternoon_key, draft["first_trip_times"][day]["afternoon"].get(str(order), "")), hint_text="HH:MM", width=112, height=40, text_size=12, keyboard_type=ft.KeyboardType.DATETIME, on_change=format_route_time_input)
                fields[(day, "morning", str(order))], fields[(day, "afternoon", str(order))] = morning, afternoon
                controls.append(ft.Row([ft.Text(f"{order}번", width=42, size=12, weight="bold"), morning, afternoon], spacing=6))
            sections.extend([ft.Text(labels[day], size=14, weight="bold", color="#1E3A8A"), ft.Column(controls, spacing=4)])
        route_editor_state["time_fields"] = fields
        route_message_text.value = ""
        route_settings_popup_layer.content = make_full_width_sheet(ft.Column([
            ft.Text(f"{number}번 순번별 첫탕", size=16, weight="bold", color="#1E3A8A"),
            ft.Text("시간은 0620 또는 06:20 형식으로 입력하세요.", size=11, color="#64748B"),
            # 목록과 하단 동작을 같은 스크롤에 넣어 키보드가 열린 상태에서도
            # 마지막 순번과 저장 버튼까지 위로 끌어올릴 수 있게 한다.
            ft.Column(sections, spacing=8),
            route_message_text,
            ft.Row([
                ft.ElevatedButton(
                    content=ft.Container(
                        ft.Text("뒤로가기", size=11, weight="bold", color="white", no_wrap=True),
                        alignment=ft.Alignment.CENTER,
                    ),
                    expand=1, bgcolor="#64748B", height=40,
                    style=ft.ButtonStyle(padding=0),
                    on_click=back_from_route_times,
                ),
                ft.ElevatedButton(
                    content=ft.Text("취소", size=12, weight="bold", color="white", no_wrap=True),
                    expand=1, bgcolor="grey", height=40,
                    style=ft.ButtonStyle(padding=0),
                    on_click=close_route_popup,
                ),
                ft.ElevatedButton(
                    content=ft.Text("저장", size=12, weight="bold", color="white", no_wrap=True),
                    expand=1, bgcolor="#2563EB", height=40,
                    style=ft.ButtonStyle(padding=0),
                    on_click=save_route_editor,
                ),
            ], spacing=5),
            ft.Container(height=160),
        ], spacing=7, tight=True, horizontal_alignment="stretch",
           scroll=ft.ScrollMode.AUTO, height=330), top=12)
        page.update()

    def save_route_editor(e=None):
        draft = route_editor_state["draft"]
        for (day, shift, order), control in route_editor_state["time_fields"].items():
            raw = (control.value or "").strip()
            normalized = valid_time(raw) if raw else ""
            if raw and not normalized:
                route_message_text.value = f"{day} {order}번 시간이 올바르지 않습니다. 예: 0620 또는 06:20"
                page.update()
                return
            if normalized:
                draft["first_trip_times"][day][shift][order] = normalized
            else:
                draft["first_trip_times"][day][shift].pop(order, None)
        existing_index = next((i for i, route in enumerate(routes_state["routes"]) if route["id"] == draft["id"]), None)
        if existing_index is None:
            routes_state["routes"].append(draft)
            if not routes_state["default_route_id"]:
                routes_state["default_route_id"] = draft["id"]
        else:
            routes_state["routes"][existing_index] = draft
        for date_key, info in USER_SCHEDULES.items():
            if info.get("route_id") != draft["id"] or info.get("start_time_override") is True:
                continue
            day_type = day_type_for_date(date_key, lambda key: bool(get_holiday_name(key)))
            info["route_number"] = draft["route_number"]
            info["start_time"] = first_trip_time(draft, day_type, info.get("status", ""), info.get("order_no", ""))
        sync_input_route_from_default()
        page.run_task(save_routes)
        page.run_task(save_all_to_client_storage)
        page.run_task(reconcile_alarms, "route_updated")
        rebuild_interface()
        show_route_list()

    def rebuild_settings_view():
        today_key = datetime.now(KST).strftime("%Y-%m-%d")
        current_month_key = today_key[:7]
        active_segment = get_pattern_segment(pattern_state, today_key)
        future_segments = [
            item for item in pattern_state.get("history", [])
            if item.get("effective_month", ALL_MONTHS) > current_month_key
        ]
        if active_segment:
            pattern_status_text.value = f"✅ 현재 적용중: {active_segment['name']}"
        else:
            pattern_status_text.value = "적용된 반복 근무 패턴이 없습니다."
        if future_segments:
            next_segment = sorted(future_segments, key=lambda item: item["effective_month"])[0]
            pattern_status_text.value += (
                f"\n📅 {next_segment['effective_month']}월부터: {next_segment['name']}"
            )
        pattern_select_box.content.value, pattern_select_box.content.color = "눌러서 선택하세요", "grey"
        settings_zone_container.controls.clear()
        alarm_settings_summary_text.value = "사용 중" if alarm_settings_state["enabled"] else "사용 안 함"
        settings_zone_container.controls.extend([
            ft.Container(
                content=ft.Column([
                    ft.Text("⚙️ 설정", size=16, weight="bold", color="#1E3A8A"),
                    ft.Divider(height=1),
                    ft.Text(
                        "※ 본 앱은 현직 76번 기사가 만든 미추홀교통과 제물포교통 기사님들을 위한 캘린더형 근무관리 앱입니다.",
                        size=11,
                        color="#64748B",
                    ),
                    ft.Text("근무형태 (반복 근무 패턴)", size=13, weight="bold", color="black"),
                    pattern_status_text,
                    ft.Text("패턴 선택:", size=12, color="grey"),
                    pattern_select_box,
                ], spacing=8, tight=True, horizontal_alignment="stretch"),
                padding=12, bgcolor="#F8FAFC", border_radius=8, border=ft.Border.all(1, "#E2E8F0"),
            ),
            ft.Container(
                content=ft.Row([
                    ft.Text("🚌 노선지정", size=14, weight="bold", color="#1E3A8A"),
                    ft.Text(f"{len(routes_state['routes'])}개 등록", size=12, color="#64748B"),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#64748B"),
                ], alignment="spaceBetween"),
                padding=14, bgcolor="#F8FAFC", border_radius=8,
                border=ft.Border.all(1, "#E2E8F0"), on_click=show_route_list,
            ),
            ft.Container(
                content=ft.Row([
                    ft.Text("⏰ 알람 설정", size=14, weight="bold", color="#1E3A8A"),
                    alarm_settings_summary_text,
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#64748B"),
                ], alignment="spaceBetween"),
                padding=14, bgcolor="#F8FAFC", border_radius=8,
                border=ft.Border.all(1, "#E2E8F0"), on_click=open_alarm_settings_popup,
            ),
        ])
        refresh_alarm_controls()
        page.update()

    # 연락처 수정은 목록 안에서 처리하지 않고 작은 모달에서 저장/삭제/취소한다.
    contact_edit_dialog = ft.AlertDialog(modal=True)

    def open_contact_edit_dialog(contact_type, index):
        target_list = PHONEBOOK_LIST if contact_type == "phonebook" else EMERGENCY_LIST
        if not (0 <= index < len(target_list)):
            return
        item = target_list[index]
        edit_name = ft.TextField(
            cursor_width=1, label="이름/직책" if contact_type == "phonebook" else "이름/서비스명",
            value=item.get("name", ""), width=250, height=44, text_size=14, content_padding=10,
        )
        edit_phone = ft.TextField(
            cursor_width=1, label="전화번호(숫자만)", value=item.get("phone", "").replace("-", ""),
            width=250, height=44, text_size=14, content_padding=10, keyboard_type=ft.KeyboardType.PHONE,
        )

        def close_dialog(e=None):
            page.pop_dialog()

        def save_contact(e=None):
            name_value = (edit_name.value or "").strip()
            phone_value = final_format_phone(edit_phone.value)
            if not name_value or not phone_value:
                return
            target_list[index] = {"name": name_value, "phone": phone_value, "is_edit": False}
            if contact_type == "phonebook":
                target_list.sort(key=lambda x: x.get("name", ""))
            page.run_task(save_all_to_client_storage)
            page.pop_dialog()
            rebuild_phonebook_view() if contact_type == "phonebook" else rebuild_emergency_view(setting_column)

        def delete_contact(e=None):
            if 0 <= index < len(target_list):
                target_list.pop(index)
                page.run_task(save_all_to_client_storage)
            page.pop_dialog()
            rebuild_phonebook_view() if contact_type == "phonebook" else rebuild_emergency_view(setting_column)

        contact_edit_dialog.title = ft.Text("연락처 수정", size=16, weight="bold")
        contact_edit_dialog.content = ft.Container(
            content=ft.Column([edit_name, edit_phone], spacing=10, tight=True), width=250,
        )
        contact_edit_dialog.actions = [ft.Row([
            ft.TextButton("저장", style=ft.ButtonStyle(color="#137333"), on_click=save_contact),
            ft.TextButton("삭제", style=ft.ButtonStyle(color="#D93025"), on_click=delete_contact),
            ft.TextButton("취소", style=ft.ButtonStyle(color="#64748B"), on_click=close_dialog),
        ], alignment="spaceEvenly", spacing=2)]
        page.show_dialog(contact_edit_dialog)

    # 연락처 관리 관련 내부 기능 함수들 (추가 및 이전 데이터 호환용 삭제 함수)
    def delete_emergency_item(index, target_column):
        if 0 <= index < len(EMERGENCY_LIST):
            EMERGENCY_LIST.pop(index)
            page.run_task(save_all_to_client_storage)
            rebuild_emergency_view(target_column)

    def add_emergency_item():
        if em_name.value and em_phone.value:
            input_name = em_name.value.strip()
            formatted_num = final_format_phone(em_phone.value)
            found_index = -1
            for i, item in enumerate(EMERGENCY_LIST):
                if item["name"] == input_name:
                    found_index = i
                    break
            if found_index != -1:
                EMERGENCY_LIST[found_index]["phone"] = formatted_num
            else:
                EMERGENCY_LIST.append({"name": input_name, "phone": formatted_num, "is_edit": False})
            page.run_task(save_all_to_client_storage)
            em_name.value = ""
            em_phone.value = ""
            rebuild_emergency_view(setting_column)

    def add_phonebook_item():
        if pb_name.value and pb_phone.value:
            formatted_num = final_format_phone(pb_phone.value)
            PHONEBOOK_LIST.append({"name": pb_name.value, "phone": formatted_num, "is_edit": False})
            PHONEBOOK_LIST.sort(key=lambda x: x.get("name", ""))
            page.run_task(save_all_to_client_storage)
            pb_name.value = ""
            pb_phone.value = ""
            rebuild_phonebook_view()

    def delete_phonebook_item(index):
        if 0 <= index < len(PHONEBOOK_LIST):
            PHONEBOOK_LIST.pop(index)
            page.run_task(save_all_to_client_storage)
            rebuild_phonebook_view()

    # 🔄 [메인 함수] 하단 메뉴 탭 전환 마스터 제어 함수 — 달력은 홈 화면(버튼 없음), 나머지는 topbar 뒤로가기로 복귀
    def change_tab(tab_name):
        nonlocal current_tab
        current_tab = tab_name

        btn_status.style = ft.ButtonStyle(color="white" if tab_name == "근무현황" else "#94A3B8", bgcolor="#2563EB" if tab_name == "근무현황" else "transparent", shape=ft.RoundedRectangleBorder(radius=6), padding=0)
        btn_setting.style = ft.ButtonStyle(color="white" if tab_name == "긴급연락처" else "#94A3B8", bgcolor="#2563EB" if tab_name == "긴급연락처" else "transparent", shape=ft.RoundedRectangleBorder(radius=6), padding=0)
        btn_config.style = ft.ButtonStyle(color="white" if tab_name == "설정" else "#94A3B8", bgcolor="#2563EB" if tab_name == "설정" else "transparent", shape=ft.RoundedRectangleBorder(radius=6), padding=0)

        btn_status.update()
        btn_setting.update()
        btn_config.update()

        topbar_back_row.visible = tab_name != "달력"
        # 🛠️ summary_area(근무/휴무/만근 요약)는 visible=False로만 숨기면 자리(공백)가 그대로 남는 문제가 있어서,
        # 근무현황 탭일 때만 컨트롤 목록에 실제로 넣고, 그 외엔 아예 목록에서 빼서 공간 자체가 안 생기게 함
        summary_area_holder.controls = [summary_area] if tab_name == "근무현황" else []
        # 📇 연락처 화면 안에서만 쓰는 서브탭 전환 버튼바. 다른 탭으로 나가면 항상 숨김.
        contacts_subtab_bar.visible = (tab_name == "긴급연락처")
        if tab_name != "긴급연락처":
            contacts_content_host.visible = False

        if tab_name == "달력":
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, settings_zone_container.visible, weeks_header.visible = True, False, True, True, False, False, False, False, True
        elif tab_name == "근무현황":
            topbar_title.value = "📊 근무현황"
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, settings_zone_container.visible, weeks_header.visible = False, True, False, False, True, False, False, False, False
            refresh_input_tab_view()
        elif tab_name == "긴급연락처":
            topbar_title.value = "📇 연락처"
            # ⚠️ 긴급연락처/기사연락처 둘 다 True로 동시에 보여주면, 위쪽(긴급연락처) 목록이 길어질수록
            # 아래쪽 기사연락처의 '추가' 버튼이 화면 밖으로 밀려버림 → 여기선 둘 다 일단 꺼두고
            # switch_contacts_subtab()이 마지막 선택값에 따라 둘 중 하나만 켜도록 위임한다.
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, settings_zone_container.visible, weeks_header.visible = False, False, False, False, False, False, False, False, False
            rebuild_emergency_view(setting_column)
            PHONEBOOK_LIST.sort(key=lambda x: x.get("name", ""))
            rebuild_phonebook_view()
            switch_contacts_subtab(contacts_subtab_state["value"])
        elif tab_name == "설정":
            topbar_title.value = "⚙️ 설정"
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, settings_zone_container.visible, weeks_header.visible = False, False, False, False, False, False, False, True, False
            rebuild_settings_view()
        page.update()

    # 📇 연락처 화면 서브탭: 긴급연락처 / 기사연락처 (한 화면에 이어붙이면 위쪽 목록이 길어질 때
    # 아래쪽 '추가' 버튼이 화면 밖으로 밀리는 문제가 있어, 한 번에 하나만 보이게 토글로 전환)
    contacts_subtab_state = {"value": "기사"}
    contacts_swipe_state = {"dx": 0.0}

    def switch_contacts_subtab(name):
        contacts_subtab_state["value"] = name
        # 하나의 스와이프 영역 안에서 콘텐츠만 교체해 웹 렌더 트리를 안정적으로 유지한다.
        setting_column.visible = True
        phonebook_zone_container.visible = True
        contacts_content_host.content = setting_column if name == "긴급" else phonebook_zone_container
        contacts_content_host.visible = True
        btn_contacts_emergency.style = ft.ButtonStyle(color="white" if name == "긴급" else "#64748B", bgcolor="#2563EB" if name == "긴급" else "#E2E8F0", shape=ft.RoundedRectangleBorder(radius=6), padding=0)
        btn_contacts_driver.style = ft.ButtonStyle(color="white" if name == "기사" else "#64748B", bgcolor="#2563EB" if name == "기사" else "#E2E8F0", shape=ft.RoundedRectangleBorder(radius=6), padding=0)
        page.update()

    def update_contacts_swipe(e):
        primary_delta = getattr(e, "primary_delta", None)
        if primary_delta is not None:
            contacts_swipe_state["dx"] += primary_delta
        else:
            local_delta = getattr(e, "local_delta", None)
            contacts_swipe_state["dx"] = getattr(local_delta, "x", 0.0) or 0.0

    def start_contacts_swipe(e):
        contacts_swipe_state["dx"] = 0.0

    def finish_contacts_swipe(e):
        dx = contacts_swipe_state["dx"]
        contacts_swipe_state["dx"] = 0.0
        if dx <= -35 and contacts_subtab_state["value"] == "기사":
            switch_contacts_subtab("긴급")
        elif dx >= 35 and contacts_subtab_state["value"] == "긴급":
            switch_contacts_subtab("기사")

    btn_contacts_emergency = ft.ElevatedButton(
        content=ft.Container(ft.Text("🚨 긴급연락처", size=13, weight="bold"), alignment=ft.Alignment.CENTER),
        expand=1, height=36, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0),
        on_click=lambda e: switch_contacts_subtab("긴급"),
    )
    btn_contacts_driver = ft.ElevatedButton(
        content=ft.Container(ft.Text("🚌 기사연락처", size=13, weight="bold"), alignment=ft.Alignment.CENTER),
        expand=1, height=36, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0),
        on_click=lambda e: switch_contacts_subtab("기사"),
    )
    contacts_subtab_bar = ft.Container(
        content=ft.Row([btn_contacts_driver, btn_contacts_emergency], spacing=6),
        padding=ft.Padding.only(left=4, right=4, top=4, bottom=6),
        visible=False,
    )

    # 🧭 URL 라우팅: 브라우저/안드로이드 "뒤로가기"가 각 화면 → 달력(홈)으로 자연스럽게 이어지도록 연결
    ROUTE_TO_TAB = {"/": "달력", "/home": "달력", "/status": "근무현황", "/emergency": "긴급연락처", "/settings": "설정"}
    suppress_next_pad = {"flag": False}
    home_back_armed = {"value": False}
    exit_confirm_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    pending_pop_view = {"view": None}

    async def close_exit_confirm(e=None):
        # "취소": 현재 뒤로가기(pop) 요청을 취소하고 앱을 그대로 유지한다.
        exit_confirm_popup_layer.visible = False
        view = pending_pop_view["view"]
        pending_pop_view["view"] = None
        page.update()
        if view is not None:
            await view.confirm_pop(False)

    async def confirm_exit_app(e=None):
        # "종료": 보류 중인 root View의 pop 요청을 허용하여 앱을 정상 종료한다.
        exit_confirm_popup_layer.visible = False
        view = pending_pop_view["view"]
        pending_pop_view["view"] = None
        page.update()
        if view is not None:
            await view.confirm_pop(True)
        else:
            await page.window.destroy()

    def show_exit_confirm():
        exit_confirm_popup_layer.content = make_full_width_sheet(ft.Column([
                ft.Text("앱을 종료하시겠습니까?", size=16, weight="bold", color="black"),
                ft.Row([
                    ft.ElevatedButton(content=ft.Container(ft.Text("종료", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#D93025", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=confirm_exit_app),
                    ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="grey", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=close_exit_confirm),
                ], spacing=8),
            ], spacing=14, tight=True, horizontal_alignment="stretch"), bottom=90)  # 엄지손가락이 닿기 편하도록 하단 근처에 배치
        exit_confirm_popup_layer.visible = True
        page.update()

    def on_route_change(e):
        change_tab(ROUTE_TO_TAB.get(page.route, "달력"))
        # (직전 호출이 "내가 방금 스스로 호출한 page.go()"였는지를 플래그로 구분해서
        #  "/"와 "/home"이 서로를 무한히 계속 호출하는 걸 막음 — 이게 없으면 무한루프/깜빡임 발생)
        if suppress_next_pad["flag"]:
            suppress_next_pad["flag"] = False
            return
        if page.route not in ("/", "/home"):
            # 달력을 벗어난 다른 화면으로 이동함 → 종료 확인 함정은 일단 해제
            home_back_armed["value"] = False
            return
        if home_back_armed["value"]:
            # 🚪 이미 달력 화면에 있는 상태에서 뒤로가기를 또 눌렀을 때만 종료 확인을 띄움
            show_exit_confirm()
        else:
            # 달력에 처음 도착함 → 조용히 뒤로가기 함정을 한 번 걸어둠 (앱이 바로 안 꺼지게)
            home_back_armed["value"] = True
            suppress_next_pad["flag"] = True
            page.go("/home" if page.route == "/" else "/")

    page.on_route_change = on_route_change

    # 🧭 탭 이동 헬퍼: 달력(홈)에서 이동할 때만 새 히스토리를 쌓고, 하위화면끼리 이동할 땐 히스토리를 안 쌓아서
    # "뒤로가기 한 번 = 무조건 달력으로" 동작이 되도록 함
    def navigate_to(route):
        # 달력(홈)에서 나갈 때만 히스토리를 쌓고, 하위화면끼리 이동할 땐 히스토리를 안 쌓아서
        # "뒤로가기 한 번 = 무조건 달력으로" 동작이 웹/앱 둘 다에서 보장되도록 함
        if page.route in ("/", "/home"):
            page.go(route)
        else:
            page.route = route
            change_tab(ROUTE_TO_TAB.get(route, "달력"))

    # 달력 날짜 클릭 시 튀어나오는 첫탕 근무등록 팝업창 세팅들
    popup_date_title = ft.Text("", size=16, weight="bold", color="black", text_align="center")
    date_route_state = {
        "route_id": "", "route_number": "", "override": False,
        "service_type": "", "departure": "",
    }
    date_route_text = ft.Text("노선 미지정", size=13, weight="bold", color="#1E3A8A")
    date_route_change_button = ft.TextButton(
        content=ft.Text("노선 변경", size=12, weight="bold", no_wrap=True),
        height=26,
        style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=5)),
        on_click=lambda e: open_date_route_picker(e),
    )
    date_route_compact_button = ft.TextButton(
        content=ft.Text("노선 변경", size=12, weight="bold", no_wrap=True),
        height=26,
        style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=5)),
        on_click=lambda e: open_date_route_picker(e),
        visible=False,
    )
    date_route_row = ft.Row(
        [date_route_text, date_route_change_button],
        alignment="spaceBetween",
        height=28,
    )
    date_first_trip_text = ft.Text(
        "첫탕 시간이 설정되지 않았습니다.", size=12, color="#D93025", expand=True
    )
    date_first_trip_row = ft.Row(
        [date_first_trip_text, date_route_compact_button],
        alignment="spaceBetween",
        vertical_alignment="center",
        spacing=4,
    )

    def selected_date_route():
        return find_route(routes_state, date_route_state["route_id"])

    def resolve_company_or_user_schedule(route, day_type, status, order_no):
        route_number = route.get("route_number", "") if route else date_route_state["route_number"]
        service_type = service_for_date(
            route_number, day_type, date_route_state.get("service_type", "")
        )
        company_item = lookup_schedule(route_number, service_type, status, order_no)
        if company_item:
            return company_item, service_type
        manual_time = first_trip_time(route, day_type, status, order_no)
        if manual_time:
            return {"time": manual_time, "departure": ""}, default_service_for_day_type(day_type)
        return None, service_type or default_service_for_day_type(day_type)

    def selected_route_fleet_count(route, day_type):
        route_number = route.get("route_number", "") if route else date_route_state["route_number"]
        service_type = service_for_date(
            route_number, day_type, date_route_state.get("service_type", "")
        )
        company_count = company_fleet_count(route_number, service_type)
        return company_count or fleet_count(route, day_type)

    def set_time_controls(value):
        if value and ":" in value:
            hour, minute = map(int, value.split(":"))
            selected_time_state["hour"], selected_time_state["minute"] = hour, minute
            hour_display_box.content.value, minute_display_box.content.value = f"{hour:02d}", f"{minute:02d}"
            hour_display_box.content.color = minute_display_box.content.color = "black"
        else:
            selected_time_state["hour"] = selected_time_state["minute"] = None
            hour_display_box.content.value, minute_display_box.content.value = "시간", "분"
            hour_display_box.content.color = minute_display_box.content.color = "grey"

    def refresh_date_first_trip(reset_override=True):
        route = selected_date_route()
        deleted_route = bool(date_route_state["route_id"] and route is None)
        # 단일 노선도 다중 노선과 동일하게 현재 노선 행과 변경 버튼을 표시한다.
        date_route_row.visible = True
        date_route_compact_button.visible = False
        if route:
            date_route_text.value = f"현재 노선: {route['route_number']}번"
        elif deleted_route and date_route_state["route_number"]:
            date_route_text.value = f"삭제된 노선: {date_route_state['route_number']}번"
        else:
            date_route_text.value = "현재 노선: 미지정"
        if reset_override:
            date_route_state["override"] = False
        status = pending_status_state["value"]
        order = order_value_state["value"]
        day_type = day_type_for_date(current["selected_date"], lambda key: bool(get_holiday_name(key)))
        schedule_item, service_type = resolve_company_or_user_schedule(
            route, day_type, status, order
        )
        date_route_state["service_type"] = service_type
        automatic = schedule_item["time"] if schedule_item else ""
        automatic_departure = schedule_item.get("departure", "") if schedule_item else ""
        if automatic and not date_route_state["override"]:
            set_time_controls(automatic)
            date_route_state["departure"] = automatic_departure
            departure_summary = f" / 출발: {automatic_departure}" if automatic_departure else ""
            date_first_trip_text.value = f"자동 첫탕: {automatic}{departure_summary}"
            date_first_trip_text.color = "#137333"
        elif date_route_state["override"] and selected_time_state["hour"] is not None:
            value = f"{selected_time_state['hour']:02d}:{selected_time_state['minute']:02d}"
            date_first_trip_text.value = f"이 날짜만 직접 수정: {value}"
            date_first_trip_text.color = "#B45309"
        elif status not in ("오전", "오후"):
            set_time_controls("")
            date_first_trip_text.value = "오전·오후 근무일 때 노선표가 자동 적용됩니다."
            date_first_trip_text.color = "#64748B"
        else:
            set_time_controls("")
            date_route_state["departure"] = ""
            date_first_trip_text.value = "첫탕 시간이 설정되지 않았습니다."
            date_first_trip_text.color = "#D93025"

    def select_date_route(route_id):
        date_route_state["route_id"] = route_id
        route = selected_date_route()
        date_route_state["route_number"] = route["route_number"] if route else ""
        day_type = day_type_for_date(current["selected_date"], lambda key: bool(get_holiday_name(key)))
        order = order_value_state["value"]
        if order and int(order) > selected_route_fleet_count(route, day_type):
            order_value_state["value"] = ""
            order_display_box.content.value, order_display_box.content.color = "순번", "grey"
        route_settings_popup_layer.visible = False
        refresh_date_first_trip()
        page.update()

    def open_date_route_picker(e=None):
        route_editor_state["view"] = "date_picker"
        if not routes_state["routes"]:
            route_editor_state["view"] = "notice"
            route_settings_popup_layer.content = make_full_width_sheet(
                ft.Column(
                    [
                        ft.Text("노선 안내", size=16, weight="bold", color="#1E3A8A"),
                        ft.Text(
                            "추가된 노선이 없습니다. 설정에서 노선을 추가해 주세요.",
                            size=13,
                            color="#D93025",
                        ),
                        ft.ElevatedButton(
                            "확인",
                            bgcolor="#2563EB",
                            color="white",
                            on_click=close_route_popup,
                        ),
                    ],
                    spacing=14,
                    tight=True,
                    horizontal_alignment="stretch",
                ),
                top=120,
            )
            route_settings_popup_layer.visible = True
            page.update()
            return
        if len(routes_state["routes"]) == 1:
            route_editor_state["view"] = "notice"
            route_settings_popup_layer.content = make_full_width_sheet(
                ft.Column(
                    [
                        ft.Text("노선 안내", size=16, weight="bold", color="#1E3A8A"),
                        ft.Text(
                            "현재 1개의 노선만 추가돼 있습니다. 노선을 추가하시겠습니까?",
                            size=13,
                            color="black",
                        ),
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "추가",
                                    expand=1,
                                    bgcolor="#2563EB",
                                    color="white",
                                    on_click=open_company_route_add,
                                ),
                                ft.ElevatedButton(
                                    "취소",
                                    expand=1,
                                    bgcolor="#64748B",
                                    color="white",
                                    on_click=close_route_popup,
                                ),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=14,
                    tight=True,
                    horizontal_alignment="stretch",
                ),
                top=100,
            )
            route_settings_popup_layer.visible = True
            page.update()
            return

        buttons = [ft.Container(content=ft.Row([
            ft.Text(f"{route['route_number']}번", size=15, weight="bold"),
            ft.Text("기본" if route["id"] == routes_state["default_route_id"] else "", size=11, color="#2563EB"),
        ], alignment="spaceBetween"), padding=12, bgcolor="#F1F5F9", border_radius=6, on_click=lambda e, rid=route["id"]: select_date_route(rid)) for route in routes_state["routes"]]
        route_settings_popup_layer.content = make_full_width_sheet(ft.Column([
            ft.Text("날짜 노선 선택", size=16, weight="bold", color="#1E3A8A"),
            ft.Column(buttons, spacing=6, scroll=ft.ScrollMode.AUTO, height=300),
            ft.TextButton("노선 설정으로 이동", on_click=lambda e: show_route_list()),
            ft.ElevatedButton("취소", bgcolor="#64748B", color="white", on_click=close_route_popup),
        ], spacing=8, tight=True, horizontal_alignment="stretch"))
        route_settings_popup_layer.visible = True
        page.update()
    memo_field = ft.TextField(
        cursor_width=1,
        hint_text="메모 (선택 입력)",
        hint_style=ft.TextStyle(size=12, color="#9CA3AF"),
        height=36,
        text_size=12,
        dense=True,
        content_padding=ft.Padding.symmetric(vertical=4, horizontal=10),
        expand=True,
    )
    order_value_state = {"value": ""}
    date_alarm_state = {"mode": "", "offset": 0, "time": ""}
    date_alarm_display_state = {"selected": False}
    date_alarm_option_labels = {
        "default": "터치하여 알람 설정",
        "off": "이 날짜는 알람 사용 안 함",
        "relative_30": "첫탕 30분 전",
        "relative_60": "첫탕 1시간 전",
        "relative_90": "첫탕 1시간 30분 전",
        "relative_120": "첫탕 2시간 전",
        "direct": "알람 시간 직접 입력",
    }
    alarm_validation_text = ft.Text("", size=11, color="#D93025")

    def parse_direct_alarm_time(value):
        candidate = (value or "").strip()
        digits = candidate.replace(":", "")
        if len(digits) != 4 or not digits.isdigit():
            raise ValueError("alarm time must contain four digits")
        hour, minute = int(digits[:2]), int(digits[2:])
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError("alarm time is out of range")
        return f"{hour:02d}:{minute:02d}"

    def update_direct_alarm_input(e):
        digits = "".join(ch for ch in (e.control.value or "") if ch.isdigit())[:4]
        e.control.value = f"{digits[:2]}:{digits[2:]}" if len(digits) == 4 else digits
        update_date_alarm_ui()

    def update_date_alarm_ui(e=None):
        if e is not None:
            date_alarm_display_state["selected"] = True
        value = date_alarm_dropdown.value or "default"
        date_alarm_dropdown.error_text = None
        date_alarm_direct_time.visible = value == "direct"
        display_text = "터치하여 알람 설정"
        placeholder = value == "default"

        # Dropdown은 닫혀 있을 때 text보다 선택된 option 문구를 우선 표시하므로
        # 매번 원래 선택 문구를 복구한 뒤 현재 항목만 실제 표시 문구로 바꾼다.
        for option in date_alarm_dropdown.options:
            option.text = date_alarm_option_labels.get(option.key, option.text)

        if value.startswith("relative_"):
            if selected_time_state["hour"] is None or selected_time_state["minute"] is None:
                date_alarm_dropdown.error_text = "첫탕 시간을 먼저 설정하세요."
                display_text = "터치하여 알람 설정"
                placeholder = True
            else:
                offset = int(value.split("_", 1)[1])
                first_trip = datetime(
                    2000, 1, 2, selected_time_state["hour"], selected_time_state["minute"]
                )
                alarm_time = first_trip - timedelta(minutes=offset)
                display_text = f"알람예정: {alarm_time.strftime('%H:%M')}"
        elif value == "direct":
            if date_alarm_direct_time.value:
                try:
                    normalized_time = parse_direct_alarm_time(date_alarm_direct_time.value)
                    display_text = f"알람예정: {normalized_time}"
                except ValueError:
                    date_alarm_dropdown.error_text = "시간 4자리를 입력하세요. 예: 0530"
                    display_text = "알람 시간 직접 입력"
            else:
                display_text = "알람 시간 직접 입력"
        elif value == "off":
            display_text = "알람 사용 안 함"

        for option in date_alarm_dropdown.options:
            if option.key == value:
                option.text = display_text
                break
        date_alarm_dropdown.text = display_text
        date_alarm_dropdown.color = "#9CA3AF" if placeholder else "#111827"
        page.update()

    date_alarm_dropdown = ft.Dropdown(
        value="default", text="터치하여 알람 설정", expand=True, height=36, text_size=12, dense=True,
        color="#9CA3AF",
        content_padding=ft.Padding.symmetric(vertical=4, horizontal=10),
        options=[
            ft.DropdownOption(key="default", text="터치하여 알람 설정"),
            ft.DropdownOption(key="off", text="이 날짜는 알람 사용 안 함"),
            ft.DropdownOption(key="relative_30", text="첫탕 30분 전"),
            ft.DropdownOption(key="relative_60", text="첫탕 1시간 전"),
            ft.DropdownOption(key="relative_90", text="첫탕 1시간 30분 전"),
            ft.DropdownOption(key="relative_120", text="첫탕 2시간 전"),
            ft.DropdownOption(key="direct", text="알람 시간 직접 입력"),
        ],
        on_select=update_date_alarm_ui,
    )
    date_alarm_direct_time = ft.TextField(
        hint_text="직접 알람 시간 예: 0530", expand=True, height=36,
        text_size=12, dense=True,
        hint_style=ft.TextStyle(size=12, color="#94A3B8"),
        content_padding=ft.Padding.symmetric(vertical=4, horizontal=10),
        keyboard_type=ft.KeyboardType.NUMBER, visible=False,
        on_change=update_direct_alarm_input,
    )

    def close_value_picker(e=None):
        value_picker_popup_layer.visible = False
        page.update()

    def apply_value_selection(field, value):
        if field == "hour":
            selected_time_state["hour"] = int(value) if value != "" else None
            hour_display_box.content.value = value if value != "" else "시간"
            hour_display_box.content.color = "black" if value != "" else "grey"
        elif field == "minute":
            selected_time_state["minute"] = int(value) if value != "" else None
            minute_display_box.content.value = value if value != "" else "분"
            minute_display_box.content.color = "black" if value != "" else "grey"
        elif field == "mangeun":
            key = f"{current['year']}_{current['month']}"
            MANGEUN_TARGETS[key] = int(value)
            mangeun_display_box.content.value = value
            page.run_task(save_all_to_client_storage)
            value_picker_popup_layer.visible = False
            mangeun_popup_layer.visible = False
            rebuild_interface()
            return
        else:
            order_value_state["value"] = value
            order_display_box.content.value = f"{value}번" if value != "" else "순번"
            order_display_box.content.color = "black" if value != "" else "grey"
            refresh_date_first_trip()
        value_picker_popup_layer.visible = False
        if field in ("hour", "minute"):
            date_route_state["override"] = True
            refresh_date_first_trip(reset_override=False)
            update_date_alarm_ui()
        page.update()

    def open_value_picker(field):
        if field == "hour":
            title, items = "시간 선택", [(f"{i:02d}", f"{i:02d}") for i in range(24)]
        elif field == "minute":
            title, items = "분 선택", [(f"{i:02d}", f"{i:02d}") for i in range(60)]
        elif field == "mangeun":
            title, items = "만근 기준 선택", [(str(i), str(i)) for i in range(15, 27)]
        else:
            route = selected_date_route()
            if route is None:
                open_date_route_picker()
                return
            day_type = day_type_for_date(current["selected_date"], lambda key: bool(get_holiday_name(key)))
            maximum = selected_route_fleet_count(route, day_type)
            if maximum < 1:
                show_route_list()
                route_message_text.value = "이 요일의 운행대수를 먼저 설정해 주세요."
                page.update()
                return
            title, items = "순번 선택", [(str(i), f"{i}번") for i in range(1, maximum + 1)]
        num_btns = [ft.Container(content=ft.Text(label, size=14, weight="bold", color="black"), width=52, height=40, alignment=ft.Alignment.CENTER, border_radius=6, bgcolor="#F1F5F9", on_click=lambda e, v=val: apply_value_selection(field, v)) for val, label in items]
        top_row = [] if field == "mangeun" else [ft.Row([ft.Container(content=ft.Text("선택 안함", size=13, color="grey"), padding=ft.Padding.symmetric(vertical=8, horizontal=14), border_radius=6, bgcolor="#F1F5F9", on_click=lambda e: apply_value_selection(field, ""))], alignment="center")]
        value_picker_popup_layer.content = make_full_width_sheet(ft.Column([
                ft.Text(title, size=16, weight="bold", color="black"),
                *top_row,
                ft.Column([ft.Row(num_btns, wrap=True, spacing=6, run_spacing=6)], scroll=ft.ScrollMode.AUTO, height=220),
                ft.Divider(height=1),
                ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="grey", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=close_value_picker)], spacing=8),
            ], spacing=10, tight=True))
        value_picker_popup_layer.visible = True
        page.update()

    hour_display_box = ft.Container(content=ft.Text("시간", size=16, color="grey"), width=72, height=32, border=ft.Border.all(1, "#94A3B8"), border_radius=6, alignment=ft.Alignment.CENTER, on_click=lambda e: open_value_picker("hour"))
    minute_display_box = ft.Container(content=ft.Text("분", size=16, color="grey"), width=72, height=32, border=ft.Border.all(1, "#94A3B8"), border_radius=6, alignment=ft.Alignment.CENTER, on_click=lambda e: open_value_picker("minute"))
    order_display_box = ft.Container(content=ft.Text("순번", size=14, color="grey"), width=76, height=32, border=ft.Border.all(1, "#94A3B8"), border_radius=6, alignment=ft.Alignment.CENTER, on_click=lambda e: open_value_picker("order"))

    mangeun_display_box = ft.Container(content=ft.Text("22", size=14, weight="bold", color="black"), width=62, height=36, border=ft.Border.all(1, "#94A3B8"), border_radius=6, alignment=ft.Alignment.CENTER, on_click=lambda e: open_value_picker("mangeun"))

    # dial_row는 더 이상 쓰지 않음 (시/분/순번이 popup_card에서 한 줄로 직접 배치됨)
    popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    value_picker_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    mangeun_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    status_picker_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    driver_list_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    alarm_settings_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    route_settings_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    # 매월 유동적으로 변하는 자동 만근 일수 계산 로직
    def get_mangeun_target():
        try:
            y, m = int(current['year']), int(current['month'])
            key = f"{y}_{m}"
            if key in MANGEUN_TARGETS: return int(MANGEUN_TARGETS[key])
            return 22 if calendar.monthrange(y, m)[1] == 31 else (20 if m == 2 else 21)
        except: return 22

    # 번호 터치 시 스마트폰 기본 전화 다이얼로 즉시 토스해 주는 함수
    # page.launch_url()은 최신 Flet에서 deprecated 되었고 Android APK에서
    # tel: 스킴이 무반응일 수 있어 UrlLauncher 외부 앱 모드로 실행한다.
    async def _launch_phone(phone_number):
        if not phone_number or phone_number == "미입력":
            return
        # 하이픈/공백 등은 제거하고 숫자와 선행 +만 유지
        raw = str(phone_number).strip()
        clean = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
        if not clean:
            return
        print(f"[DEBUG] _launch_phone calling url_launcher.launch_url(tel:{clean})", flush=True)
        await url_launcher.launch_url(f"tel:{clean}", mode=ft.LaunchMode.EXTERNAL_APPLICATION)
        print(f"[DEBUG] _launch_phone launch_url call completed", flush=True)

    def make_call(phone_number):
        page.run_task(_launch_phone, phone_number)

    driving_subtab_state = {"value": "앞차"}
    driving_swipe_state = {"dx": 0.0}

    def switch_driving_subtab(name):
        driving_subtab_state["value"] = name
        refresh_input_tab_view()

    def update_driving_swipe(e):
        primary_delta = getattr(e, "primary_delta", None)
        if primary_delta is not None:
            driving_swipe_state["dx"] += primary_delta
        else:
            local_delta = getattr(e, "local_delta", None)
            driving_swipe_state["dx"] = getattr(local_delta, "x", 0.0) or 0.0

    def start_driving_swipe(e):
        driving_swipe_state["dx"] = 0.0

    def finish_driving_swipe(e):
        dx = driving_swipe_state["dx"]
        driving_swipe_state["dx"] = 0.0
        if dx <= -35 and driving_subtab_state["value"] == "앞차":
            switch_driving_subtab("뒷차")
        elif dx >= 35 and driving_subtab_state["value"] == "뒷차":
            switch_driving_subtab("앞차")

    # 🚍 운행정보 탭 내부의 내차/앞차/뒷차 요약 카드뷰 빌드
    def build_driving_summary_zone():
        def phone_action_row(phone):
            if phone == "미입력":
                return ft.Text("미입력", size=13, color="#1E3A8A", weight="bold")
            return ft.Row([
                ft.GestureDetector(content=ft.Text(phone, size=13, color="#1E3A8A", weight="bold", no_wrap=True), on_tap=lambda e, p=phone: make_call(p)),
                ft.IconButton(ft.Icons.PHONE, icon_color="green", icon_size=18, width=28, height=28, padding=0, tooltip="전화 걸기", on_click=lambda e, p=phone: make_call(p)),
            ], spacing=4, alignment="start", vertical_alignment="center", tight=True)

        my_card = ft.Container(content=ft.Column([ft.Row([ft.Text("내차 정보", size=11, color="grey", weight="bold"), ft.ElevatedButton(content=ft.Container(ft.Text("입력", size=10, weight="bold", color="white"), alignment=ft.Alignment.CENTER), on_click=lambda e: open_info_input_popup("내차"), bgcolor="#2563EB", width=55, height=22, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0))], alignment="spaceBetween"), ft.Text(f"노선: {input_data_state['route']}", size=14, weight="bold", color="black"), ft.Text(f"내차: {input_data_state['bus_no']}", size=14, weight="bold", color="black"), ft.Text(f"교대자: {input_data_state['relief_driver']}", size=14, weight="bold", color="black"), phone_action_row(input_data_state['relief_phone'])], spacing=2, tight=True), bgcolor="#F8FAFC", border=ft.Border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1)
        front_card = ft.Container(content=ft.Column([ft.Row([ft.Text("앞차 정보", size=11, color="grey", weight="bold"), ft.ElevatedButton(content=ft.Container(ft.Text("입력", size=10, weight="bold", color="white"), alignment=ft.Alignment.CENTER), on_click=lambda e: open_info_input_popup("앞차"), bgcolor="#1E3A8A", width=55, height=22, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0))], alignment="spaceBetween"), ft.Text(input_data_state['front_bus'], size=14, weight="bold", color="black"), ft.Text(input_data_state['front_driver'], size=14, weight="bold", color="black"), phone_action_row(input_data_state['front_phone'])], spacing=2, tight=True), bgcolor="#F8FAFC", border=ft.Border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1)
        back_card = ft.Container(content=ft.Column([ft.Row([ft.Text("뒷차 정보", size=11, color="grey", weight="bold"), ft.ElevatedButton(content=ft.Container(ft.Text("입력", size=10, weight="bold", color="white"), alignment=ft.Alignment.CENTER), on_click=lambda e: open_info_input_popup("뒷차"), bgcolor="#1E3A8A", width=55, height=22, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0))], alignment="spaceBetween"), ft.Text(input_data_state['back_bus'], size=14, weight="bold", color="black"), ft.Text(input_data_state['back_driver'], size=14, weight="bold", color="black"), phone_action_row(input_data_state['back_phone'])], spacing=2, tight=True), bgcolor="#F8FAFC", border=ft.Border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1)
        selected_name = driving_subtab_state["value"]
        front_tab = ft.ElevatedButton(content=ft.Text("앞차 정보", size=12, weight="bold"), expand=1, height=34, style=ft.ButtonStyle(color="white" if selected_name == "앞차" else "#64748B", bgcolor="#2563EB" if selected_name == "앞차" else "#E2E8F0", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: switch_driving_subtab("앞차"))
        back_tab = ft.ElevatedButton(content=ft.Text("뒷차 정보", size=12, weight="bold"), expand=1, height=34, style=ft.ButtonStyle(color="white" if selected_name == "뒷차" else "#64748B", bgcolor="#2563EB" if selected_name == "뒷차" else "#E2E8F0", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: switch_driving_subtab("뒷차"))
        selected_card = front_card if selected_name == "앞차" else back_card
        return ft.Container(content=ft.Column([ft.Text("🚍 운행 정보 요약", size=14, weight="bold", color="#1E3A8A"), my_card, ft.Row([front_tab, back_tab], spacing=6), selected_card], spacing=8, horizontal_alignment="stretch"), padding=12, border=ft.Border.all(1, "#2563EB"), border_radius=10, margin=ft.Margin.only(top=12, bottom=10))

    # 하이픈(-) 자동 정렬 마법의 번호 교정 포맷 함수
    def final_format_phone(raw_value):
        return format_phone(raw_value)

    # 앞차/뒷차/내차 세부 입력용 팝업 조립 레이아웃 구역
    # 📇 앞차/뒷차 기사성함 입력 시, 기사연락처(전화번호부)에서 선택하면 전화번호가 자동으로 채워지는 드롭다운
    driver_list_dialog = ft.AlertDialog(modal=False)

    def build_driver_picker(name_field, phone_field):
        def pick_driver(val):
            if val and val != "직접입력":
                match = next((p for p in PHONEBOOK_LIST if p.get("name") == val), None)
                if match:
                    name_field.value = match.get("name", "")
                    phone_field.value = match.get("phone", "").replace("-", "")
            page.pop_dialog()
            page.update()

        def open_driver_list(e=None):
            names = ["직접입력"] + [p["name"] for p in PHONEBOOK_LIST if p.get("name")]
            rows = [ft.Container(content=ft.Text(n, size=14, weight="bold", color="black"), alignment=ft.Alignment.CENTER_LEFT, padding=ft.Padding.symmetric(vertical=10, horizontal=14), border_radius=6, bgcolor="#F1F5F9", on_click=lambda e, v=n: pick_driver(v)) for n in names]
            # ⚠️ 앞/뒷차 입력창(info_dialog)이 이미 떠 있는 상태에서 이 창을 별도 페이지-레벨 오버레이로 열면
            # 이미 열려있는 AlertDialog 뒤에 가려져서 탭해도 반응이 없어 보임 → 다이얼로그를 하나 더 쌓아서(page.show_dialog)
            # 그 위에 띄우고, 취소/선택 시 page.pop_dialog()로 닫으면 원래 입력창이 그대로 다시 보임
            driver_list_dialog.title = ft.Text("기사연락처에서 선택", size=15, weight="bold")
            driver_list_dialog.content = ft.Container(content=ft.Column(rows, spacing=6, scroll=ft.ScrollMode.AUTO, height=min(280, len(rows) * 48), horizontal_alignment="stretch"), width=260)
            driver_list_dialog.actions = [ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="grey", expand=1, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: page.pop_dialog())]
            page.show_dialog(driver_list_dialog)

        return ft.Container(content=ft.Text("기사연락처에서 선택 (탭)", size=13, color="grey"), width=252, height=44, border=ft.Border.all(1, "#94A3B8"), border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=10), alignment=ft.Alignment.CENTER_LEFT, on_click=open_driver_list)

    def open_info_input_popup(target_type):
        if target_type == "내차":
            has_registered_routes = bool(routes_state["routes"])
            sync_input_route_from_default()
            tf_route = ft.TextField(
                cursor_width=1,
                label="노선번호 (자동)" if has_registered_routes else "노선번호",
                value=input_data_state["route"].replace("미입력", ""),
                keyboard_type=ft.KeyboardType.TEXT,
                width=260,
                height=38,
                text_size=13,
                content_padding=8,
                disabled=has_registered_routes,
            )
            tf_bus_no = ft.TextField(cursor_width=1, label="내차번호", value=input_data_state["bus_no"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, width=260, height=38, text_size=13, content_padding=8)
            tf_relief_driver = ft.TextField(cursor_width=1, label="교대자 성함", value=input_data_state["relief_driver"].replace("미입력",""), width=260, height=38, text_size=13, content_padding=8)
            tf_relief_phone = ft.TextField(cursor_width=1, label="교대자 전화번호(숫자만)", value=input_data_state["relief_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, width=260, height=38, text_size=13, content_padding=8)
            def save_my(e):
                if has_registered_routes:
                    sync_input_route_from_default()
                else:
                    input_data_state["route"] = tf_route.value if tf_route.value else "미입력"
                input_data_state["bus_no"] = f"{tf_bus_no.value}호" if tf_bus_no.value else "미입력"
                input_data_state["relief_driver"] = tf_relief_driver.value.strip() if tf_relief_driver.value and tf_relief_driver.value.strip() else "미입력"
                input_data_state["relief_phone"] = final_format_phone(tf_relief_phone.value) if tf_relief_phone.value else "미입력"
                page.run_task(save_all_to_client_storage); page.pop_dialog(); page.update(); rebuild_interface()
            info_dialog.title = ft.Text("👤 내 차량 설정", size=14, weight="bold")
            info_dialog.content = ft.Container(content=ft.Column([tf_route, tf_bus_no, build_driver_picker(tf_relief_driver, tf_relief_phone), tf_relief_driver, tf_relief_phone], spacing=8, tight=True), width=260)
            info_dialog.actions = [ft.Row([
                ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white", no_wrap=True), alignment=ft.Alignment.CENTER), on_click=save_my, expand=1, height=38, bgcolor="#2563EB"),
                ft.ElevatedButton(content=ft.Container(ft.Text("뒤로가기", size=12, weight="bold", color="white", no_wrap=True), alignment=ft.Alignment.CENTER), on_click=lambda e: page.pop_dialog(), expand=1, height=38, bgcolor="grey"),
            ], spacing=8, width=260)]
        elif target_type == "앞차":
            tf_f_bus, tf_f_driver, tf_f_phone = ft.TextField(cursor_width=1, label="앞차번호", value=input_data_state["front_bus"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, width=260, height=38, text_size=13, content_padding=8), ft.TextField(cursor_width=1, label="기사성함", value=input_data_state["front_driver"].replace("미입력",""), width=260, height=38, text_size=13, content_padding=8), ft.TextField(cursor_width=1, label="전화번호(숫자만)", value=input_data_state["front_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, width=260, height=38, text_size=13, content_padding=8)
            def save_front(e):
                input_data_state["front_bus"], input_data_state["front_driver"], input_data_state["front_phone"] = f"{tf_f_bus.value}호" if tf_f_bus.value else "미입력", tf_f_driver.value if tf_f_driver.value else "미입력", final_format_phone(tf_f_phone.value) if tf_f_phone.value else "미입력"
                page.run_task(save_all_to_client_storage); page.pop_dialog(); page.update(); rebuild_interface()
            # ⌨️ title/content/actions을 AlertDialog 표준 슬롯대로 나눠서 넣음.
            # actions는 Flutter의 진짜 다이얼로그 액션바라서 content가 아무리 커도, 키보드가 떠도 항상 화면에 고정으로 보임.
            info_dialog.title = ft.Text("◀ 앞차 정보 입력", size=14, weight="bold")
            info_dialog.content = ft.Container(content=ft.Column([tf_f_bus, build_driver_picker(tf_f_driver, tf_f_phone), tf_f_driver, tf_f_phone], spacing=10, tight=True), width=260)
            info_dialog.actions = [ft.Row([
                ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white", no_wrap=True), alignment=ft.Alignment.CENTER), on_click=save_front, expand=1, height=38, bgcolor="#1E3A8A"),
                ft.ElevatedButton(content=ft.Container(ft.Text("뒤로가기", size=12, weight="bold", color="white", no_wrap=True), alignment=ft.Alignment.CENTER), on_click=lambda e: page.pop_dialog(), expand=1, height=38, bgcolor="grey"),
            ], spacing=8, width=260)]
        elif target_type == "뒷차":
            tf_b_bus, tf_b_driver, tf_b_phone = ft.TextField(cursor_width=1, label="뒷차번호", value=input_data_state["back_bus"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, width=260, height=38, text_size=13, content_padding=8), ft.TextField(cursor_width=1, label="기사성함", value=input_data_state["back_driver"].replace("미입력",""), width=260, height=38, text_size=13, content_padding=8), ft.TextField(cursor_width=1, label="전화번호 (숫자만)", value=input_data_state["back_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, width=260, height=38, text_size=13, content_padding=8)
            def save_back(e):
                input_data_state["back_bus"], input_data_state["back_driver"], input_data_state["back_phone"] = f"{tf_b_bus.value}호" if tf_b_bus.value else "미입력", tf_b_driver.value if tf_b_driver.value else "미입력", final_format_phone(tf_b_phone.value) if tf_b_phone.value else "미입력"
                page.run_task(save_all_to_client_storage); page.pop_dialog(); page.update(); rebuild_interface()
            info_dialog.title = ft.Text("▶ 뒷차 정보 입력", size=14, weight="bold")
            info_dialog.content = ft.Container(content=ft.Column([tf_b_bus, build_driver_picker(tf_b_driver, tf_b_phone), tf_b_driver, tf_b_phone], spacing=10, tight=True), width=260)
            info_dialog.actions = [ft.Row([
                ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white", no_wrap=True), alignment=ft.Alignment.CENTER), on_click=save_back, expand=1, height=38, bgcolor="#1E3A8A"),
                ft.ElevatedButton(content=ft.Container(ft.Text("뒤로가기", size=12, weight="bold", color="white", no_wrap=True), alignment=ft.Alignment.CENTER), on_click=lambda e: page.pop_dialog(), expand=1, height=38, bgcolor="grey"),
            ], spacing=8, width=260)]
        page.show_dialog(info_dialog)

    info_dialog = ft.AlertDialog(
        modal=False,
        content=ft.Container(),
        scrollable=True,
        alignment=ft.Alignment(0, -1),
        inset_padding=ft.Padding.only(left=24, right=24, top=12, bottom=12),
    )
    def refresh_input_tab_view(): input_zone_container.controls.clear(); input_zone_container.controls.append(build_driving_summary_zone()); page.update()

    # 📅 [캘린더 렌더러] 매달 달력 날짜 그리드 및 실시간 만근 카운트 일체 갱신 함수
    # 🔁 특정 날짜가 반복패턴상 몇 번째 슬롯인지 계산해서 상태를 돌려줌 (패턴 미설정 시 None)
    def get_pattern_status(date_key):
        return get_repeating_pattern_status(pattern_state, WORK_PATTERNS, date_key)

    # 📌 해당 날짜의 실제 표시용 근무정보: 수동입력 있으면 그걸 우선, 없으면 반복패턴으로 자동 채움
    def get_effective_day_info(date_key):
        manual = USER_SCHEDULES.get(date_key)
        if manual:
            result = dict(manual)
            result["memo"] = DATE_MEMOS.get(date_key, "")
            return result
        p_status = get_pattern_status(date_key)
        if p_status:
            return {"status": p_status, "start_time": "", "order_no": ""}
        return {"status": "", "start_time": "", "order_no": ""}

    def clear_expired_date_alarms(now=None):
        """Clear only expired per-date alarm overrides; preserve work data and memos."""
        current_time = now or datetime.now(KST)
        cleared = 0
        for date_key, info in USER_SCHEDULES.items():
            if not isinstance(info, dict):
                continue
            try:
                work_date = datetime.strptime(date_key, "%Y-%m-%d").date()
            except (TypeError, ValueError):
                continue
            if not is_expired_date_alarm(
                work_date=work_date, day_info=info, timezone=KST, now=current_time,
            ):
                continue
            info["alarm_mode"] = ""
            info["alarm_offset_minutes"] = 0
            info["alarm_time"] = ""
            cleared += 1
        return cleared


    def rebuild_interface():
        nonlocal USER_SCHEDULES, MANGEUN_TARGETS
        today = datetime.now(KST)
        if clear_expired_date_alarms(today):
            page.run_task(save_all_to_client_storage)
        today_y, today_m, today_d = today.year, today.month, today.day
        month_title.value = f"{current['year']}년 {current['month']}월"
        today_month_button.visible = not (
            current["year"] == today_y and current["month"] == today_m)
        month_prefix = f"{current['year']}-{current['month']:02d}"
        month_data = {k: v for k, v in USER_SCHEDULES.items() if k.startswith(month_prefix)}
        days_in_month = calendar.monthrange(current['year'], current['month'])[1]
        month_effective_statuses = [get_effective_day_info(f"{month_prefix}-{d:02d}").get("status", "") for d in range(1, days_in_month + 1)]
        work_days, off_days = sum(1 for s in month_effective_statuses if s in WORK_STATUSES), sum(1 for s in month_effective_statuses if s in OFF_STATUSES)
        morning_days = sum(1 for s in month_effective_statuses if s == "오전")
        afternoon_days = sum(1 for s in month_effective_statuses if s == "오후")
        m_target = get_mangeun_target(); mangeun_display_box.content.value = str(m_target)
        annual_used = sum(1 for date_key, info in USER_SCHEDULES.items() if date_key.startswith(f"{current['year']}-") and isinstance(info, dict) and info.get("status") == "연차")
        annual_remaining = max(0, 15 - annual_used)
        stats_text.value = f"근무: {work_days}"
        morning_count_text.value = f"오전: {morning_days}"
        afternoon_count_text.value = f"오후: {afternoon_days}"
        mangeun_text.value, mangeun_value_text.value = f"휴무: {off_days}", f"만근: {m_target}"
        annual_used_text.value = f"연차사용: {annual_used}"
        annual_remaining_text.value = f"남은연차: {annual_remaining}"

        calendar_grid.controls.clear()
        cal = calendar.Calendar(firstweekday=6)
        weeks = cal.monthdayscalendar(current['year'], current['month'])
        # 📐 화면 높이에 맞춰 날짜칸 크기 자동 계산 (기기/글자크기 상관없이 화면에 맞게 조정)
        # ⚠️ 모바일 크롬은 주소창이 접히고 펴지는 순간 page.height가 비정상적으로 작은 값(예: 100~200)을
        # 순간적으로 보고할 때가 있음 → 이 이상값을 걸러내고 마지막 정상값을 재사용
        raw_h = page.height or 700
        if raw_h < 400:
            screen_h = rebuild_interface._last_good_h if hasattr(rebuild_interface, "_last_good_h") else 700
        else:
            screen_h = raw_h
            rebuild_interface._last_good_h = raw_h
        # 155는 기존 page.padding=4 기준으로 튜닝된 값. top_inset이 4보다 크면(안드로이드 네이티브)
        # 그 차이만큼 빼주는 것 외에, 실기기 테스트 결과 추가 여유 버퍼가 더 필요해서 +30 추가
        # (top_inset=30 반영 시 chrome_overhead=181로는 하단이 화면 밖으로 밀려남 → 211로 증가 테스트)
        # 하단 메뉴는 이제 별도 고정 영역이므로 그 높이를 명시적으로 제외한다.
        # Android에서는 상태바/내비게이션바 오차가 있어 약간의 안전 여유도 둔다.
        native_safety = 18 if is_native_android else 0
        chrome_overhead = 125 + max(0, top_inset - 4) + BOTTOM_BAR_HEIGHT + native_safety
        available_h = max(screen_h - chrome_overhead, 60 * len(weeks))
        # ⚠️ 예전엔 cell_h를 100px로 상한을 씌워서, 주(week) 수가 적은 달이나 화면이 큰 기기에서는
        # 달력이 남는 공간을 다 못 채우고 하단 메뉴 사이에 빈 공간이 크게 남았음 → 상한 제거하고 화면을 꽉 채움
        cell_h = max(60, available_h / len(weeks))
        print(f"[DEBUG] raw_h={raw_h}, screen_h={screen_h}, weeks={len(weeks)}, chrome_overhead={chrome_overhead}, available_h={available_h}, cell_h={cell_h}, floor_hit={available_h == 60*len(weeks)}", flush=True)
        for week in weeks:
            week_row = ft.Row(alignment="spaceAround", spacing=0)
            for day in week:
                if day == 0: week_row.controls.append(ft.Container(expand=1, height=cell_h, bgcolor="#FFFFFF", border=ft.Border.all(0.5, CALENDAR_GRID_LINE_COLOR)))
                else:
                    weekday = datetime(current['year'], current['month'], day).weekday()
                    date_key = f"{current['year']}-{current['month']:02d}-{day:02d}"
                    day_info = get_effective_day_info(date_key)
                    status, start_time, order_no = day_info.get("status", ""), day_info.get("start_time", ""), day_info.get("order_no", "")
                    bg_color = "#F7F7F7"
                    text_color = status_color(status) if status else "#000000"
                    status_order = str(order_no) if status in ("오전", "오후", "전일", "근무") and order_no else ""
                    status_display = ft.Row([
                        ft.Text(status, size=10, weight="bold", color=text_color, no_wrap=True),
                    ] + ([ft.Text(status_order, size=7, weight="normal", color="#64748B", no_wrap=True)] if status_order else []), alignment="center", vertical_alignment="center", spacing=0, tight=True, height=14)
                    time_text = ft.Text(start_time, size=10, weight="normal", color=text_color, no_wrap=True) if start_time and status != "휴무" else None
                    time_display = ft.Row([time_text] if time_text else [], alignment="center", vertical_alignment="center", spacing=0, height=14)
                    departure = str(day_info.get("departure", "") or "").strip()
                    departure_display = ft.Row(
                        [ft.Text(departure, size=8, color="#475569", no_wrap=True,
                                 max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)] if departure else [],
                        alignment="center", vertical_alignment="center", spacing=0,
                        height=12 if departure else 0,
                    )
                    holiday_name = get_holiday_name(date_key)
                    lunar_marker = get_lunar_marker(current['year'], current['month'], day)
                    day_number_color = "#D93025" if (weekday == 6 or holiday_name) else ("#1A73E8" if weekday == 5 else "#000000")
                    has_date_alarm = day_info.get("alarm_mode", "") in ("relative", "direct")
                    memo_text = DATE_MEMOS.get(date_key, "")
                    memo_control = ft.Text(memo_text, size=9, color="black", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, text_align="center", expand=True) if memo_text else None
                    memo_display = ft.Row([memo_control] if memo_control else [], alignment="center", vertical_alignment="center", spacing=0, height=12)
                    is_today = (current['year'] == today_y and current['month'] == today_m and day == today_d)
                    date_labels = []
                    if holiday_name:
                        date_labels.append(ft.Text(holiday_name, size=7, weight="normal", color="white" if is_today else "#D93025", no_wrap=True, overflow=ft.TextOverflow.VISIBLE))
                    if lunar_marker and not holiday_name:  # 공휴일과 겹치면 공휴일 이름만 표시
                        date_labels.append(ft.Text(lunar_marker, size=7, color="white" if is_today else "#64748B", no_wrap=True, overflow=ft.TextOverflow.VISIBLE))
                    # ==========================================================
                    # [UI 개선]
                    # 오늘 날짜 강조 방식을
                    # 파란 테두리 → 숫자 강조 방식으로 변경
                    # ==========================================================
                    day_number_display = ft.Text(f"{day}", size=10, weight="normal", italic=False, color="white" if is_today else day_number_color, offset=ft.Offset(0, -0.08))
                    day_number_row = ft.Row(
                        [day_number_display] +
                        # 알람 아이콘이 날짜숫자에 바짝 붙어 보이던 것을 살짝 띄우기 위해 spacing을 3→6으로 확대
                        ([ft.Container(content=ft.Icon(ft.Icons.ALARM, size=10, color="white" if is_today else "#2563EB", tooltip="날짜별 알람 설정됨"), padding=ft.Padding.only(top=2))] if has_date_alarm else []) +
                        ([ft.Container(content=ft.Column(date_labels, spacing=0, tight=True), padding=ft.Padding.only(top=2))] if date_labels else []),
                        alignment="start", vertical_alignment="start", spacing=4, height=14,
                    )
                    # 오늘 날짜 셀만 폭이 좁아져 "오후(6)" 같은 상태문구가 줄바꿈되던 버그 →
                    # 굵은 파란 테두리(2px)를 없애고 모든 셀과 동일한 얇은 회색 테두리로 통일하면서 함께 해결됨
                    day_header = ft.Container(content=day_number_row, left=1, right=1, top=1, height=14)
                    body_controls = [status_display, time_display]
                    if departure:
                        body_controls.append(departure_display)
                    body_controls.append(memo_display)
                    day_body = ft.Container(
                        content=ft.Column(body_controls, alignment="start", horizontal_alignment="center", spacing=1, tight=True),
                        left=1, right=1, top=16, bottom=0,
                        padding=ft.Padding.only(top=5), alignment=ft.Alignment.TOP_CENTER,
                    )
                    day_box = ft.Container(content=ft.Stack([
                        ft.Container(bgcolor="#2563EB", height=16, left=0, right=0, top=0) if is_today else ft.Container(),
                        day_header,
                        day_body,
                    ]), bgcolor="#FFF8D6" if is_today else "#FFFFFF", padding=0, border=ft.Border.all(0.5, CALENDAR_GRID_LINE_COLOR), border_radius=0, height=cell_h, expand=1, on_click=lambda e, dk=date_key: open_input_popup(dk))
                    week_row.controls.append(day_box)
            calendar_grid.controls.append(week_row)
        if current_tab == "근무현황": refresh_input_tab_view()
        page.update()

    # 날짜 다이얼로그 호출 및 휠 스크롤 시간 초기화 매칭 함수
    # 🔧 근무변경 메뉴에서 고를 수 있는 상태 목록
    STATUS_OPTIONS = ["변경없음", "직접입력", "월차", "연차", "휴무", "오전", "오후", "교육", "휴가", "조퇴", "병가", "대체근무"]
    pending_status_state = {"value": ""}
    current_status_display = ft.Text("미설정", size=16, weight="bold", color="grey")
    custom_status_field = ft.TextField(cursor_width=1, label="근무 상태 직접입력", height=44, text_size=14)

    def close_status_picker(e=None):
        status_picker_popup_layer.visible = False
        page.update()

    def apply_status_selection(value):
        pending_status_state["value"] = value
        current_status_display.value = f"현재설정: {value}" if value else "현재설정: 미설정"
        current_status_display.color = status_color(value) if value else "grey"
        refresh_date_first_trip()
        status_picker_popup_layer.visible = False
        page.update()

    def confirm_custom_status(e):
        if custom_status_field.value and custom_status_field.value.strip():
            apply_status_selection(custom_status_field.value.strip())
        else:
            close_status_picker()

    def show_status_list(e=None):
        rows = []
        for opt in STATUS_OPTIONS:
            if opt == "변경없음":
                rows.append(ft.Container(content=ft.Text(opt, size=15, color="grey"), alignment=ft.Alignment.CENTER_LEFT, padding=ft.Padding.symmetric(vertical=10, horizontal=14), border_radius=6, bgcolor="#F1F5F9", on_click=lambda e: close_status_picker()))
            elif opt == "직접입력":
                rows.append(ft.Container(content=ft.Text(opt, size=15, weight="bold", color="black"), alignment=ft.Alignment.CENTER_LEFT, padding=ft.Padding.symmetric(vertical=10, horizontal=14), border_radius=6, bgcolor="#F1F5F9", on_click=show_custom_input))
            else:
                rows.append(ft.Container(content=ft.Text(opt, size=15, weight="bold", color=status_color(opt)), alignment=ft.Alignment.CENTER_LEFT, padding=ft.Padding.symmetric(vertical=10, horizontal=14), border_radius=6, bgcolor="#F1F5F9", on_click=lambda e, v=opt: apply_status_selection(v)))
        status_picker_popup_layer.content = make_full_width_sheet(ft.Column([
                ft.Text("근무변경", size=16, weight="bold", color="black"),
                ft.Column(rows, spacing=6, scroll=ft.ScrollMode.AUTO, height=min(380, len(STATUS_OPTIONS) * 48), horizontal_alignment="stretch"),
                ft.Divider(height=1),
                ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="grey", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=close_status_picker)], spacing=8),
            ], spacing=10, tight=True, horizontal_alignment="stretch"))
        page.update()

    def show_custom_input(e):
        custom_status_field.value = ""
        status_picker_popup_layer.content = make_full_width_sheet(ft.Column([
                ft.Text("근무 상태 직접입력", size=16, weight="bold", color="black"),
                custom_status_field,
                ft.Row([
                    ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#2563EB", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=confirm_custom_status),
                    ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="grey", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=show_status_list),
                ], spacing=8),
            ], spacing=12, tight=True, horizontal_alignment="stretch"))
        page.update()

    def open_status_picker(e):
        show_status_list()
        status_picker_popup_layer.visible = True
        page.update()

    def open_input_popup(date_key):
        current["selected_date"] = date_key
        if clear_expired_date_alarms():
            page.run_task(save_all_to_client_storage)
        popup_date_title.value = date_key
        day_info = get_effective_day_info(date_key)
        current_time, current_order = day_info.get("start_time", ""), day_info.get("order_no", "")
        stored_route_id = str(day_info.get("route_id", "") or "")
        stored_route_number = str(day_info.get("route_number", "") or "").strip()
        resolved_route = find_route(routes_state, stored_route_id)
        if resolved_route is None:
            resolved_route = find_route_by_number(routes_state, stored_route_number)

        fallback_route = (
            default_route(routes_state)
            if resolved_route is None
            and not stored_route_id
            and not stored_route_number
            else None
        )
        active_route = resolved_route or fallback_route
        date_route_state["route_id"] = active_route["id"] if active_route else stored_route_id
        date_route_state["route_number"] = (
            active_route["route_number"] if active_route else stored_route_number
        )

        # 예전 route_id가 저장된 일정은 동일한 노선번호의 현재 노선으로 연결만 복구한다.
        # 상태·순번·시간·출발지·메모·알람 등 나머지 날짜 정보는 변경하지 않는다.
        stored_schedule = USER_SCHEDULES.get(date_key)
        if (
            resolved_route is not None
            and isinstance(stored_schedule, dict)
            and (
                stored_schedule.get("route_id") != resolved_route["id"]
                or str(stored_schedule.get("route_number", "") or "").strip()
                != str(resolved_route["route_number"])
            )
        ):
            stored_schedule["route_id"] = resolved_route["id"]
            stored_schedule["route_number"] = resolved_route["route_number"]
            page.run_task(save_all_to_client_storage)

        date_route_state["service_type"] = str(day_info.get("service_type", "") or "")
        date_route_state["departure"] = str(day_info.get("departure", "") or "")
        date_route_state["override"] = (
            day_info.get("start_time_override", False) is True
            or (bool(current_time) and resolved_route is None)
        )
        existing_status = day_info.get("status", "")
        pending_status_state["value"] = existing_status
        current_status_display.value = f"현재설정: {existing_status}" if existing_status else "현재설정: 미설정"
        current_status_display.color = status_color(existing_status) if existing_status else "grey"
        order_value_state["value"] = str(current_order) if current_order else ""
        order_display_box.content.value = f"{current_order}번" if current_order else "순번"
        order_display_box.content.color = "black" if current_order else "grey"
        if current_time and ":" in current_time:
            h, m = map(int, current_time.split(":"))
            selected_time_state["hour"], selected_time_state["minute"] = h, m
            hour_display_box.content.value, minute_display_box.content.value = f"{h:02d}", f"{m:02d}"
            hour_display_box.content.color, minute_display_box.content.color = "black", "black"
        else:
            selected_time_state["hour"], selected_time_state["minute"] = None, None
            hour_display_box.content.value, minute_display_box.content.value = "시간", "분"
            hour_display_box.content.color, minute_display_box.content.color = "grey", "grey"
        memo_field.value = DATE_MEMOS.get(date_key, "")
        alarm_mode = day_info.get("alarm_mode", "")
        if alarm_mode == "relative":
            date_alarm_dropdown.value = f"relative_{day_info.get('alarm_offset_minutes', 0)}"
        elif alarm_mode in ("off", "direct"):
            date_alarm_dropdown.value = alarm_mode
        else:
            date_alarm_dropdown.value = "default"
        date_alarm_direct_time.value = day_info.get("alarm_time", "")
        date_alarm_display_state["selected"] = alarm_mode in ("relative", "direct", "off")
        refresh_date_first_trip(reset_override=False)
        update_date_alarm_ui()
        popup_layer.content, popup_layer.visible = popup_card, True; page.update()

    # 근무 저장 및 삭제 처리 함수
    def select_status_and_save(action):
        target_date = current["selected_date"]
        if action == "선택취소":
            USER_SCHEDULES.pop(target_date, None); DATE_MEMOS.pop(target_date, None); page.run_task(save_all_to_client_storage); page.run_task(reconcile_alarms, "schedule_deleted"); popup_layer.visible = False; rebuild_interface(); return
        memo_value = memo_field.value.strip() if memo_field.value else ""
        if memo_value:
            DATE_MEMOS[target_date] = memo_value
        else:
            DATE_MEMOS.pop(target_date, None)
        status_value = pending_status_state["value"]
        if not status_value:
            page.run_task(save_all_to_client_storage); page.run_task(reconcile_alarms, "schedule_saved"); popup_layer.visible = False; rebuild_interface(); return
        h, m = selected_time_state["hour"], selected_time_state["minute"]
        final_time = f"{h:02d}:{m:02d}" if (status_value != "휴무" and h is not None and m is not None) else ""
        selection = date_alarm_dropdown.value or "default"
        alarm_mode, alarm_offset, alarm_time = "", 0, ""
        if selection.startswith("relative_"):
            if not final_time:
                date_alarm_dropdown.error_text = "첫탕 시간을 먼저 선택하거나 직접 시간을 입력하세요."
                page.update(); return
            alarm_mode, alarm_offset = "relative", int(selection.split("_", 1)[1])
        elif selection == "direct":
            candidate = (date_alarm_direct_time.value or "").strip()
            try:
                alarm_time = parse_direct_alarm_time(candidate)
            except ValueError:
                date_alarm_dropdown.error_text = "직접 알람 시간을 숫자 4자리로 입력하세요. 예: 0530"
                page.update(); return
            alarm_mode = "direct"
        elif selection == "off":
            alarm_mode = "off"
        selected_route = selected_date_route()
        USER_SCHEDULES[target_date] = {
            "status": status_value, "start_time": final_time,
            "order_no": "" if status_value == "휴무" else order_value_state["value"],
            "route_id": selected_route["id"] if selected_route else date_route_state["route_id"],
            "route_number": selected_route["route_number"] if selected_route else date_route_state["route_number"],
            "start_time_override": date_route_state["override"],
            "service_type": date_route_state.get("service_type", ""),
            "departure": "" if date_route_state["override"] else date_route_state.get("departure", ""),
            "alarm_mode": alarm_mode, "alarm_offset_minutes": alarm_offset,
            "alarm_time": alarm_time,
        }
        page.run_task(save_all_to_client_storage); page.run_task(reconcile_alarms, "schedule_saved"); popup_layer.visible = False; rebuild_interface()

    # [UI 개선] 키보드 표시 시 메모 입력란 가시성 및 알람 정보 배치 개선
    # 팝업 내부 스크롤뷰 레이아웃 구조체
    popup_card = make_full_width_sheet(ft.Column([
            ft.Row([popup_date_title], alignment="center"),
            ft.Row([current_status_display, ft.ElevatedButton(content=ft.Container(ft.Text("근무변경", size=13, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#374151", height=36, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.Padding.symmetric(horizontal=14)), on_click=open_status_picker)], alignment="spaceBetween"),
            ft.Divider(height=1),
            date_route_row,
            date_first_trip_row,
            ft.Row([
                hour_display_box,
                ft.Container(content=ft.Text(":", size=18, weight="bold", color="black"), width=24, alignment=ft.Alignment.CENTER),
                minute_display_box,
                ft.Container(width=24),
                order_display_box,
            ], alignment="center", spacing=0),
            ft.Column(
                [
                    ft.Column(
                        [
                            ft.Row([date_alarm_dropdown], spacing=0),
                            ft.Row([date_alarm_direct_time], spacing=0),
                        ],
                        spacing=1,
                        horizontal_alignment="stretch",
                    ),
                    ft.Row([memo_field], spacing=0),
                ],
                spacing=4,
                horizontal_alignment="stretch",
            ),
            ft.Row([ft.Container(content=ft.Text("저장", size=14, weight="bold", color="white"), bgcolor="#2563EB", alignment=ft.Alignment(0, 0), width=145, height=36, border_radius=6, on_click=lambda e: select_status_and_save("저장"))], alignment="center"), ft.Divider(height=1, color="transparent"),
            ft.Row([ft.TextButton("선택취소(삭제)", on_click=lambda e: select_status_and_save("선택취소"), style=ft.ButtonStyle(color="red")), ft.TextButton("닫기", on_click=lambda e: setattr(popup_layer, "visible", False) or page.update())], alignment="spaceBetween"),
            # 메모 키보드가 열린 상태에서도 입력 내용과 저장 버튼을
            # 키보드 위까지 올릴 수 있는 스크롤 여백.
            ft.Container(height=180),
        ], spacing=4, tight=True, scroll=ft.ScrollMode.AUTO, height=330), top=12)

    # 상단 내비게이션 바 (이전달 / 다음달 이동) 버튼 컴포넌트
    today_month_button = ft.TextButton(
        "오늘", visible=False, on_click=lambda e: go_today_month(e),
        style=ft.ButtonStyle(color="#2563EB", padding=2),
    )
    header_nav = ft.Row([
        ft.TextButton("◀ 이전", on_click=lambda e: move_prev(e), style=ft.ButtonStyle(color="black", padding=0)),
        ft.Row([month_title, today_month_button], spacing=2, tight=True),
        ft.TextButton("다음 ▶", on_click=lambda e: move_next(e), style=ft.ButtonStyle(color="black", padding=0)),
    ], alignment="spaceBetween", height=32)
    topbar_title = ft.Text("", size=17, weight="bold", color="black")
    topbar_back_row = ft.Row([
        ft.TextButton(content=ft.Text("🏠 달력으로 가기", size=14, weight="bold", color="#2563EB"), on_click=lambda e: page.go("/")),
        topbar_title,
    ], alignment="start", spacing=14, visible=False)
    # 하단 '달력으로 가기' 버튼은 제거됨 (상단 버튼으로 통일)
    mangeun_setting_row = ft.Row([mangeun_value_text, ft.ElevatedButton("변경", on_click=lambda e: setattr(mangeun_popup_layer, "visible", True) or page.update(), bgcolor="#2563EB", color="white", width=68, height=22, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), text_style=ft.TextStyle(size=11, weight="bold"), padding=0))], alignment="start", vertical_alignment="center", spacing=6, height=22)

    mangeun_popup_layer.content = make_full_width_sheet(ft.Column([
            ft.Text("만근 기준 변경", size=16, weight="bold", color="black"),
            ft.Text("탭해서 숫자를 선택하면 바로 적용돼요.", size=12, color="grey"),
            ft.Row([ft.Text("만근:", size=13, weight="bold", color="black"), mangeun_display_box], alignment="center", spacing=10),
            ft.Row([ft.TextButton("닫기", on_click=lambda e: setattr(mangeun_popup_layer, "visible", False) or page.update())], alignment="center"),
        ], spacing=10, tight=True))

    def move_prev(e):
        current["month"] -= 1
        if current["month"] == 0: current["month"] = 12; current["year"] -= 1
        rebuild_interface()

    def move_next(e):
        current["month"] += 1
        if current["month"] == 13: current["month"] = 1; current["year"] += 1
        rebuild_interface()

    def go_today_month(e):
        today = datetime.now(KST)
        current["year"], current["month"] = today.year, today.month
        current["selected_date"] = today.strftime("%Y-%m-%d")
        rebuild_interface()

    def summary_cell(text_control, expand=1):
        return ft.Container(content=text_control, expand=expand, padding=ft.Padding.symmetric(horizontal=12, vertical=8), alignment=ft.Alignment.CENTER_LEFT)

    morning_afternoon_cell = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=morning_count_text,
                    height=16,
                    padding=ft.Padding.symmetric(horizontal=10),
                    alignment=ft.Alignment.CENTER_LEFT,
                ),
                ft.Divider(height=1, color="#93C5FD"),
                ft.Container(
                    content=afternoon_count_text,
                    height=16,
                    padding=ft.Padding.symmetric(horizontal=10),
                    alignment=ft.Alignment.CENTER_LEFT,
                ),
            ],
            spacing=0,
            tight=True,
        ),
        expand=1,
        alignment=ft.Alignment.CENTER_LEFT,
    )

    summary_area = ft.Container(
        content=ft.Column([
            ft.Row([
                summary_cell(stats_text),
                ft.Container(width=1, height=32, bgcolor="#93C5FD"),
                morning_afternoon_cell,
                ft.Container(width=1, height=32, bgcolor="#93C5FD"),
                summary_cell(annual_used_text, expand=2),
            ], spacing=0),
            ft.Divider(height=1, color="#93C5FD"),
            ft.Row([
                summary_cell(mangeun_text, expand=2),
                ft.Container(width=1, height=32, bgcolor="#93C5FD"),
                summary_cell(annual_remaining_text, expand=2),
            ], spacing=0),
        ], spacing=0, tight=True),
        border=ft.Border.all(1, "#93C5FD"), border_radius=10,
        margin=ft.Margin.only(bottom=8),
    )
    summary_area_holder = ft.Column([], spacing=0, tight=True)

    # 🗑️ 리셋 관련: 확인 팝업 + 실제 초기화 로직
    reset_confirm_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)

    def close_reset_popup(e):
        reset_confirm_popup_layer.visible = False
        page.update()

    def do_reset(e):
        USER_SCHEDULES.clear()
        pattern_state["name"], pattern_state["anchor_date"], pattern_state["anchor_index"] = None, None, 0
        pattern_state["history"] = []
        page.run_task(save_all_to_client_storage)
        page.run_task(reconcile_alarms, "schedule_reset")
        reset_confirm_popup_layer.visible = False
        rebuild_interface()

    reset_confirm_popup_layer.content = make_full_width_sheet(ft.Column([
            ft.Text("⚠️ 근무 기록 초기화", size=16, weight="bold", color="#D93025"),
            ft.Text("입력하신 모든 날짜의 근무 기록과 반복 근무 패턴이 삭제됩니다.\n이 작업은 되돌릴 수 없습니다. 정말 초기화하시겠습니까?", size=13, color="black"),
            ft.Row([
                ft.ElevatedButton(content=ft.Container(ft.Text("초기화", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#D93025", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=do_reset),
                ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="grey", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=close_reset_popup),
            ], spacing=8),
        ], spacing=12, tight=True))

    def open_reset_popup(e):
        reset_confirm_popup_layer.visible = True
        page.update()

    guide_text = ft.Row([
        ft.Container(content=ft.Text("💡 날짜를 터치하여 근무를 입력 또는 수정하세요.", size=10, color="#666666"), padding=ft.Padding.only(left=8, bottom=0), expand=1),
        ft.TextButton(content=ft.Text("🗑️ 리셋", size=11, weight="bold", color="#D93025"), on_click=open_reset_popup, style=ft.ButtonStyle(padding=0)),
    ], alignment="spaceBetween", height=28)

    # 긴급연락처 신규 등록 폼 컴포넌트
    emergency_form_container = ft.Container(padding=ft.Padding.only(top=8), content=ft.Column([ft.Row([ft.Text("🚨 긴급연락처", size=16, weight="bold", color="#1E3A8A")]), ft.Divider(height=1), ft.Row([em_name := ft.TextField(cursor_width=1, label="이름/서비스명", label_style=ft.TextStyle(size=11), width=100, height=38, text_size=13, content_padding=8), em_phone := ft.TextField(cursor_width=1, label="전화번호(숫자만)", label_style=ft.TextStyle(size=11), expand=True, height=38, text_size=13, content_padding=8, keyboard_type=ft.KeyboardType.PHONE), ft.ElevatedButton(content=ft.Text("등록", size=12, weight="bold", color="white"), bgcolor="#2563EB", width=60, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e: add_emergency_item())], spacing=4), ft.Divider(height=1, color="#E2E8F0")]))

    contacts_content_host = ft.Container(visible=False)

    # 화면 스크롤 가능 구역 및 전체 인터페이스 초기 배치
    # Android APK에서는 Stack의 bottom=0 절대배치가 시스템 내비게이션 영역과 겹치거나
    # 화면 바깥으로 밀리는 기종이 있어, 하단 메뉴를 일반 Column의 고정 높이 영역으로 분리한다.
    # 이렇게 하면 본문이 길어져도 하단 메뉴는 항상 화면에 남는다.
    BOTTOM_BAR_HEIGHT = 58

    scrollable_content = ft.Column(
        [
            topbar_back_row,
            header_nav,
            summary_area_holder,
            guide_text,
            calendar_table,
            input_zone_container,
            contacts_subtab_bar,
            contacts_content_host,
            settings_zone_container,
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
    )

    bottom_bar = ft.Container(
        content=ft.Column(
            [
                ft.Divider(height=1),
                ft.Row(
                    [btn_status, btn_setting, btn_config],
                    alignment="spaceAround",
                    spacing=4,
                ),
            ],
            spacing=0,
        ),
        bgcolor="#FFFFFF",
        height=BOTTOM_BAR_HEIGHT,
        padding=ft.Padding.only(bottom=4),
    )

    # ==========================================================
    # [UI 개선]
    # 달력 좌우 스와이프 지원
    # 버튼과 동시에 사용 가능
    # ==========================================================
    calendar_swipe_state = {"dx": 0.0}

    def start_calendar_swipe(e):
        calendar_swipe_state["dx"] = 0.0

    def update_calendar_swipe(e):
        primary_delta = getattr(e, "primary_delta", None)
        if primary_delta is not None:
            calendar_swipe_state["dx"] += primary_delta
        else:
            local_delta = getattr(e, "local_delta", None)
            calendar_swipe_state["dx"] = getattr(local_delta, "x", 0.0) or 0.0

    def finish_calendar_swipe(e):
        dx = calendar_swipe_state["dx"]
        calendar_swipe_state["dx"] = 0.0
        if dx <= -35:
            move_next(e)  # 왼쪽 스와이프 → 다음달 (기존 "다음 ▶" 버튼과 동일 동작)
        elif dx >= 35:
            move_prev(e)  # 오른쪽 스와이프 → 이전달 (기존 "◀ 이전" 버튼과 동일 동작)

    # 본문과 하단 메뉴를 세로로 분리한 뒤, 팝업 레이어만 전체 화면 위에 올린다.
    def start_main_swipe(e):
        if current_tab == "긴급연락처":
            start_contacts_swipe(e)
        elif current_tab == "근무현황":
            start_driving_swipe(e)
        elif current_tab == "달력":
            start_calendar_swipe(e)

    def update_main_swipe(e):
        if current_tab == "긴급연락처":
            update_contacts_swipe(e)
        elif current_tab == "근무현황":
            update_driving_swipe(e)
        elif current_tab == "달력":
            update_calendar_swipe(e)

    def finish_main_swipe(e):
        if current_tab == "긴급연락처":
            finish_contacts_swipe(e)
        elif current_tab == "근무현황":
            finish_driving_swipe(e)
        elif current_tab == "달력":
            finish_calendar_swipe(e)

    swipeable_scroll_area = ft.GestureDetector(
        content=ft.Container(content=scrollable_content, expand=True),
        on_horizontal_drag_start=start_main_swipe,
        on_horizontal_drag_update=update_main_swipe,
        on_horizontal_drag_end=finish_main_swipe,
        drag_interval=10,
        expand=True,
    )

    main_layout = ft.Column(
        [
            swipeable_scroll_area,
            bottom_bar,
        ],
        expand=True,
        spacing=0,
    )

    # Android 시스템 내비게이션 바/제스처 영역을 피해 하단 메뉴 전체가 보이도록 한다.
    # 상단은 기존 top_inset 계산을 그대로 사용하므로 SafeArea의 상단 보정은 끈다.
    safe_main_layout = ft.SafeArea(
        content=main_layout,
        expand=True,
        avoid_intrusions_top=False,
        avoid_intrusions_left=False,
        avoid_intrusions_right=False,
        avoid_intrusions_bottom=True,
        maintain_bottom_view_padding=True,
        minimum_padding=ft.Padding.only(bottom=8),
    )

    page.add(
        ft.Stack(
            [
                safe_main_layout,
                popup_layer,
                value_picker_popup_layer,
                mangeun_popup_layer,
                pattern_popup_layer,
                pattern_name_popup_layer,
                reset_confirm_popup_layer,
                status_picker_popup_layer,
                exit_confirm_popup_layer,
                driver_list_popup_layer,
                alarm_settings_popup_layer,
                route_settings_popup_layer,
            ],
            expand=True,
        )
    )

    # 📱 Android 뒤로가기 처리
    # Flet의 root View pop을 막고, 현재 화면에 따라 직접 처리한다.
    # - 하위 화면: pop 취소 후 달력으로 이동
    # - 달력 화면: pop을 보류하고 종료 확인 팝업 표시
    async def on_root_view_confirm_pop(e):
        root_view = e.control

        # 노선 시간 편집에서는 휴대폰 뒤로가기도 화면의 뒤로가기와
        # 동일하게 동작시켜 저장 전 입력값을 잃지 않는다.
        if route_settings_popup_layer.visible:
            if route_editor_state.get("view") == "times":
                back_from_route_times()
            elif route_editor_state.get("view") == "basic":
                show_route_list()
            else:
                route_settings_popup_layer.visible = False
                page.update()
            await root_view.confirm_pop(False)
            return

        # 🔧 날짜 편집/피커 등 모달 팝업이 열려있으면, 뒤로가기는 "그 팝업을 닫는 것"이 최우선.
        # 이걸 안 하면 팝업이 떠 있어도 current_tab이 여전히 "달력"이라서
        # 종료 확인 팝업이 잘못 뜨는 버그가 생김.
        open_popups = [
            popup_layer, value_picker_popup_layer, mangeun_popup_layer,
            pattern_popup_layer, pattern_name_popup_layer, reset_confirm_popup_layer,
            status_picker_popup_layer, driver_list_popup_layer,
            alarm_settings_popup_layer,
        ]
        for layer in open_popups:
            if layer.visible:
                layer.visible = False
                page.update()
                await root_view.confirm_pop(False)
                return

        if current_tab != "달력":
            await root_view.confirm_pop(False)
            # 🔧 navigate_to("/")는 현재 탭이 홈이 아닐 때 page.route를 직접 대입만 하고
            # 실제 라우터(page.go)를 안 거쳐서, 이후 같은 탭 버튼을 다시 눌러도
            # 라우터 내부 상태와 어긋나 반응이 없는 버그가 있었음 → 실제 네비게이션으로 복귀
            page.go("/")
            return

        if exit_confirm_popup_layer.visible:
            # 🔧 팝업이 떠 있는 상태에서 뒤로가기를 또 누르면 "취소"를 누른 것과 동일하게 처리
            # (기존엔 이번 pop 요청만 조용히 무시해서 팝업이 그대로 남아있는 버그가 있었음)
            await root_view.confirm_pop(False)
            await close_exit_confirm()
            return

        pending_pop_view["view"] = root_view
        show_exit_confirm()

    if is_native_android and page.views:
        root_view = page.views[0]
        root_view.can_pop = False
        root_view.on_confirm_pop = on_root_view_confirm_pop
        page.update()

    page.on_resize = lambda e: rebuild_interface()
    await reconcile_alarms("app_start")
    async def handle_app_lifecycle(e):
        if e.state not in (ft.AppLifecycleState.SHOW, ft.AppLifecycleState.RESUME):
            return
        await reconcile_alarms("app_resumed")
        rebuild_interface()

    change_tab("달력"); rebuild_interface()
    page.run_task(sync_online_holidays)
    page.on_app_lifecycle_state_change = lambda e: page.run_task(handle_app_lifecycle, e)

if os.environ.get("PORT"):
    import uvicorn
    import flet.fastapi as flet_fastapi
    from fastapi import FastAPI, HTTPException
    from holiday_sync import build_holiday_payload, fetch_official_holidays

    web_app = FastAPI()
    _server_holiday_cache = {}

    @web_app.get("/api/holidays")
    async def holiday_api(years: str):
        try:
            requested_years = tuple(sorted({int(value) for value in years.split(",") if value.strip()}))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="잘못된 연도입니다.") from exc
        if not requested_years or len(requested_years) > 3:
            raise HTTPException(status_code=400, detail="연도는 1~3개만 요청할 수 있습니다.")
        if requested_years not in _server_holiday_cache:
            try:
                official = await asyncio.to_thread(fetch_official_holidays, requested_years)
                _server_holiday_cache[requested_years] = build_holiday_payload(official)
            except Exception as exc:
                fallback = {date_key: name for date_key, name in HOLIDAYS.items() if int(date_key[:4]) in requested_years}
                print(f"[HolidayAPI] fallback: {exc}", flush=True)
                _server_holiday_cache[requested_years] = build_holiday_payload(fallback, source="bundled")
        return _server_holiday_cache[requested_years]

    web_app.mount("/", flet_fastapi.app(main, assets_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")))
    uvicorn.run(web_app, host="0.0.0.0", port=int(os.environ["PORT"]))
else:
    # 📱 APK/네이티브 빌드 또는 로컬 실행 시에는 포트/브라우저 강제 지정 없이 기본 방식으로 실행
    ft.app(target=main)
