# ==========================================
# [앱 이름: 버스캘린더]
# 현재 배포 버전: 빌드 0005 (주석 및 이모지 완벽 복구본)
# ==========================================

import os
import calendar
from datetime import datetime, timedelta, timezone
import flet as ft
import json

from data_utils import format_phone, normalize_contacts, normalize_input_data, normalize_schedules

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
    "2025-03-01": "삼일절", "2025-03-03": "대체휴일", "2025-05-01": "노동절", "2025-05-05": "어린이날/부처님",
    "2025-06-03": "대선", "2025-06-06": "현충일", "2025-08-15": "광복절", "2025-10-03": "개천절",
    "2025-10-05": "추석연휴", "2025-10-06": "추석", "2025-10-07": "추석연휴", "2025-10-08": "대체휴일",
    "2025-10-09": "한글날", "2025-12-25": "성탄절",
    "2026-01-01": "신정", "2026-02-16": "설연휴", "2026-02-17": "설날", "2026-02-18": "설연휴",
    "2026-03-01": "삼일절", "2026-03-02": "대체휴일", "2026-05-01": "노동절", "2026-05-05": "어린이날",
    "2026-05-24": "부처님", "2026-05-25": "대체휴일", "2026-06-03": "지방선거", "2026-06-06": "현충일",
    "2026-07-17": "제헌절", "2026-08-15": "광복절", "2026-08-17": "대체휴일", "2026-09-24": "추석연휴",
    "2026-09-25": "추석", "2026-09-26": "추석연휴", "2026-10-03": "개천절", "2026-10-05": "대체휴일",
    "2026-10-09": "한글날", "2026-12-25": "성탄절",
    "2027-01-01": "신정", "2027-02-06": "설연휴", "2027-02-07": "설날", "2027-02-08": "설연휴", "2027-02-09": "대체휴일",
    "2027-03-01": "삼일절", "2027-05-01": "노동절", "2027-05-05": "어린이날", "2027-05-13": "부처님",
    "2027-06-06": "현충일", "2027-07-17": "제헌절", "2027-08-15": "광복절", "2027-08-16": "대체휴일",
    "2027-09-14": "추석연휴", "2027-09-15": "추석", "2027-09-16": "추석연휴", "2027-10-03": "개천절",
    "2027-10-04": "대체휴일", "2027-10-09": "한글날", "2027-10-11": "대체휴일", "2027-12-25": "성탄절", "2027-12-27": "대체휴일",
}

_HOLIDAY_YEAR_CACHE = {}


def get_holiday_name(date_key):
    """Return a Korean holiday name, including years outside the bundled table."""
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
    page.title = "버스캘린더"
    page.theme_mode = "light"

    # 외부 앱(전화 다이얼러 등)을 여는 Flet 서비스
    # Service는 화면 레이어(overlay)가 아니라 page.services에 등록해야 한다.
    url_launcher = ft.UrlLauncher()
    page.services.append(url_launcher)

    # 안드로이드 네이티브 앱에서만 상태바(시간/배터리/신호) 침범 방지용 상단 여백 추가
    # 웹(Render) 배포는 브라우저가 자체적으로 상태바를 처리하므로 영향 없어야 함
    is_native_android = (page.platform == ft.PagePlatform.ANDROID) and not page.web
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
    
    saved_emergency = await page.shared_preferences.get(STORAGE_EMERGENCY_KEY)
    EMERGENCY_LIST = safe_json_load(saved_emergency, list, [])

    saved_pattern = await page.shared_preferences.get(STORAGE_PATTERN_KEY)
    # pattern_state: name(패턴명) / anchor_date(기준일 YYYY-MM-DD) / anchor_index(그날이 패턴의 몇 번째인지)
    pattern_state = safe_json_load(saved_pattern, dict, {"name": None, "anchor_date": None, "anchor_index": 0})

    saved_memos = await page.shared_preferences.get(STORAGE_MEMO_KEY)
    DATE_MEMOS = safe_json_load(saved_memos, dict, {})

    USER_SCHEDULES = normalize_schedules(safe_json_load(saved_schedules, dict, {}))
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


    # 앱 켜질 때 오늘 날짜 및 시간 제어용 초기값 설정
    now_kst = datetime.now(KST)
    current = {"year": now_kst.year, "month": now_kst.month, "selected_date": f"{now_kst.year}-{now_kst.month:02d}-{now_kst.day:02d}"}
    selected_time_state = {"hour": None, "minute": None}

    current_tab = "달력"

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
    mangeun_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_value_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    annual_used_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    annual_remaining_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    
    calendar_grid = ft.Column(spacing=0)
    input_zone_container = ft.Column(spacing=2, visible=False)
    settings_zone_container = ft.Column(spacing=2, visible=False)
    
    phonebook_items_column = ft.Column(spacing=6)
    
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
            ft.Divider(height=1, color="#E2E8F0"),
            phonebook_items_column
        ]),
        padding=ft.Padding.symmetric(horizontal=4, vertical=8), visible=False
    )
    
    # 📇 전화번호부는 이제 하단 '연락처' 탭 안에 통합되어 있음 (별도 큰 버튼 제거됨)

    # [하단 탭 메뉴 버튼] 기사님 디자인 피드백 반영 (텍스트 이모지 장착 및 한여름의 패딩 제거 버전)
    btn_status = ft.ElevatedButton(content=ft.Container(content=ft.Text("📊 근무현황", color="white", size=11, weight="bold"), alignment=ft.Alignment.CENTER), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: navigate_to("/status"))
    btn_setting = ft.ElevatedButton(content=ft.Container(content=ft.Text("📇 연락처", color="white", size=11, weight="bold"), alignment=ft.Alignment.CENTER), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: navigate_to("/emergency"))
    btn_config = ft.ElevatedButton(content=ft.Container(content=ft.Text("⚙️ 설정", color="white", size=11, weight="bold"), alignment=ft.Alignment.CENTER), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: navigate_to("/settings"))

    # 달력 최상단 요일 표시줄 (일~토)
    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row([ft.Container(content=ft.Text(d, size=13, weight="bold", color="#D93025" if d=="일" else ("#1A73E8" if d=="토" else "black")), expand=1, alignment=ft.Alignment(0, 0), padding=ft.Padding.symmetric(vertical=2), bgcolor="#E5E7EB", border=ft.Border.all(0.5, "black")) for d in days_letters], alignment="spaceAround", spacing=0)
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

                phonebook_items_column.controls.append(ft.Container(content=row_content, padding=ft.Padding.only(left=4, right=4, top=8, bottom=8), border=ft.border.Border(bottom=ft.border.BorderSide(0.5, "#E2E8F0"))))
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
                
                target_column.controls.append(ft.Container(content=row_content, padding=ft.Padding.only(left=4, right=4, top=8, bottom=8), border=ft.border.Border(bottom=ft.border.BorderSide(0.5, "#E2E8F0"))))
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

    def apply_pattern(idx):
        today_str = datetime.now(KST).strftime("%Y-%m-%d")
        pattern_state["name"] = pending_pattern_name["value"]
        pattern_state["anchor_date"] = today_str
        pattern_state["anchor_index"] = idx
        page.run_task(save_all_to_client_storage)
        rebuild_settings_view(); rebuild_interface()
        popup_view_mode["mode"] = "done"
        popup_view_mode["applied_idx"] = idx
        popup_view_mode["applied_date"] = today_str
        build_pattern_popup()
        page.update()

    def confirm_apply_pattern(e):
        apply_pattern(popup_view_mode["confirm_idx"])

    def clear_pattern(e):
        pattern_state["name"], pattern_state["anchor_date"], pattern_state["anchor_index"] = None, None, 0
        page.run_task(save_all_to_client_storage)
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
                    ft.Row(slot_chips, wrap=True, spacing=6, run_spacing=6),
                    ft.Text("이후 날짜는 이 기준으로 자동 반복 적용됩니다.", size=12, color="grey"),
                    ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#2563EB", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=finish_pattern_apply)], spacing=8),
                ], spacing=10, tight=True, horizontal_alignment="stretch"))
            return
        if pending_pattern_name["value"] == "격일제":
            # 🔁 격일제는 근무/휴무 2가지뿐이라 "몇 번째 근무"를 물어볼 필요가 없음
            # → 오늘이 근무인지 휴무인지만 고르면 그 기준으로 이후 날짜가 하루씩 번갈아 자동 채워짐
            pattern_popup_layer.content = make_full_width_sheet(ft.Column([
                    ft.Text("오늘 격일제 근무를 선택하세요", size=15, weight="bold", color="black"),
                    ft.Text("선택한 상태를 기준으로 이후 근무/휴무가 하루씩 번갈아 자동 설정됩니다.", size=12, color="grey"),
                    ft.Row([
                        ft.ElevatedButton(content=ft.Container(ft.Text("오늘 근무", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#137333", expand=1, height=44, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: apply_pattern(0)),
                        ft.ElevatedButton(content=ft.Container(ft.Text("오늘 휴무", size=14, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#D93025", expand=1, height=44, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: apply_pattern(1)),
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

    def rebuild_settings_view():
        if pattern_state.get("name"):
            pattern_status_text.value = f"✅ 현재 적용중: {pattern_state['name']} (기준일 {pattern_state['anchor_date']})"
        else:
            pattern_status_text.value = "적용된 반복 근무 패턴이 없습니다."
        pattern_select_box.content.value, pattern_select_box.content.color = "눌러서 선택하세요", "grey"
        settings_zone_container.controls.clear()
        settings_zone_container.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("⚙️ 설정", size=16, weight="bold", color="#1E3A8A"),
                    ft.Divider(height=1),
                    ft.Text("근무형태 (반복 근무 패턴)", size=13, weight="bold", color="black"),
                    pattern_status_text,
                    ft.Text("패턴 선택:", size=12, color="grey"),
                    pattern_select_box,
                ], spacing=8, tight=True, horizontal_alignment="stretch"),
                padding=12, bgcolor="#F8FAFC", border_radius=8, border=ft.Border.all(1, "#E2E8F0"),
            )
        )
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
    contacts_subtab_state = {"value": "긴급"}
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
        if dx <= -35 and contacts_subtab_state["value"] == "긴급":
            switch_contacts_subtab("기사")
        elif dx >= 35 and contacts_subtab_state["value"] == "기사":
            switch_contacts_subtab("긴급")

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
        content=ft.Row([btn_contacts_emergency, btn_contacts_driver], spacing=6),
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
    memo_field = ft.TextField(cursor_width=1, label="메모 (선택 입력)", hint_text="예: 미용실, 병원 예약 등", height=44, text_size=13, content_padding=ft.Padding.symmetric(vertical=8, horizontal=10))
    order_value_state = {"value": ""}

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
        value_picker_popup_layer.visible = False
        page.update()

    def open_value_picker(field):
        if field == "hour":
            title, items = "시간 선택", [(f"{i:02d}", f"{i:02d}") for i in range(24)]
        elif field == "minute":
            title, items = "분 선택", [(f"{i:02d}", f"{i:02d}") for i in range(60)]
        elif field == "mangeun":
            title, items = "만근 기준 선택", [(str(i), str(i)) for i in range(15, 27)]
        else:
            title, items = "순번 선택", [(str(i), f"{i}번") for i in range(1, 51)]
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

    hour_display_box = ft.Container(content=ft.Text("시간", size=16, color="grey"), width=72, height=48, border=ft.Border.all(1, "#94A3B8"), border_radius=6, alignment=ft.Alignment.CENTER, on_click=lambda e: open_value_picker("hour"))
    minute_display_box = ft.Container(content=ft.Text("분", size=16, color="grey"), width=72, height=48, border=ft.Border.all(1, "#94A3B8"), border_radius=6, alignment=ft.Alignment.CENTER, on_click=lambda e: open_value_picker("minute"))
    order_display_box = ft.Container(content=ft.Text("순번", size=14, color="grey"), width=76, height=48, border=ft.Border.all(1, "#94A3B8"), border_radius=6, alignment=ft.Alignment.CENTER, on_click=lambda e: open_value_picker("order"))

    mangeun_display_box = ft.Container(content=ft.Text("22", size=14, weight="bold", color="black"), width=62, height=36, border=ft.Border.all(1, "#94A3B8"), border_radius=6, alignment=ft.Alignment.CENTER, on_click=lambda e: open_value_picker("mangeun"))

    # dial_row는 더 이상 쓰지 않음 (시/분/순번이 popup_card에서 한 줄로 직접 배치됨)
    popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    value_picker_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    mangeun_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    status_picker_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    driver_list_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
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
            tf_route = ft.TextField(cursor_width=1, label="노선번호", value=input_data_state["route"].replace("미입력",""), keyboard_type=ft.KeyboardType.TEXT, width=260, height=38, text_size=13, content_padding=8)
            tf_bus_no = ft.TextField(cursor_width=1, label="내차번호", value=input_data_state["bus_no"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, width=260, height=38, text_size=13, content_padding=8)
            tf_relief_driver = ft.TextField(cursor_width=1, label="교대자 성함", value=input_data_state["relief_driver"].replace("미입력",""), width=260, height=38, text_size=13, content_padding=8)
            tf_relief_phone = ft.TextField(cursor_width=1, label="교대자 전화번호(숫자만)", value=input_data_state["relief_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, width=260, height=38, text_size=13, content_padding=8)
            def save_my(e):
                input_data_state["route"], input_data_state["bus_no"] = tf_route.value if tf_route.value else "미입력", f"{tf_bus_no.value}호" if tf_bus_no.value else "미입력"
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
            tf_f_bus, tf_f_driver, tf_f_phone = ft.TextField(cursor_width=1, label="앞차번호", value=input_data_state["front_bus"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38, text_size=13, content_padding=8), ft.TextField(cursor_width=1, label="기사성함", value=input_data_state["front_driver"].replace("미입력",""), expand=True, height=38, text_size=13, content_padding=8), ft.TextField(cursor_width=1, label="전화번호(숫자만)", value=input_data_state["front_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, expand=True, height=38, text_size=13, content_padding=8)
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
            tf_b_bus, tf_b_driver, tf_b_phone = ft.TextField(cursor_width=1, label="뒷차번호", value=input_data_state["back_bus"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38, text_size=13, content_padding=8), ft.TextField(cursor_width=1, label="기사성함", value=input_data_state["back_driver"].replace("미입력",""), expand=True, height=38, text_size=13, content_padding=8), ft.TextField(cursor_width=1, label="전화번호 (숫자만)", value=input_data_state["back_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, expand=True, height=38, text_size=13, content_padding=8)
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

    info_dialog = ft.AlertDialog(modal=False, content=ft.Container())
    def refresh_input_tab_view(): input_zone_container.controls.clear(); input_zone_container.controls.append(build_driving_summary_zone()); page.update()

    # 📅 [캘린더 렌더러] 매달 달력 날짜 그리드 및 실시간 만근 카운트 일체 갱신 함수
    # 🔁 특정 날짜가 반복패턴상 몇 번째 슬롯인지 계산해서 상태를 돌려줌 (패턴 미설정 시 None)
    def get_pattern_status(date_key):
        if not pattern_state.get("name") or not pattern_state.get("anchor_date"):
            return None
        pattern = WORK_PATTERNS.get(pattern_state["name"])
        if not pattern:
            return None
        try:
            anchor = datetime.strptime(pattern_state["anchor_date"], "%Y-%m-%d")
            target = datetime.strptime(date_key, "%Y-%m-%d")
        except ValueError:
            return None
        delta_days = (target - anchor).days
        idx = (pattern_state.get("anchor_index", 0) + delta_days) % len(pattern)
        return pattern[idx]

    # 📌 해당 날짜의 실제 표시용 근무정보: 수동입력 있으면 그걸 우선, 없으면 반복패턴으로 자동 채움
    def get_effective_day_info(date_key):
        manual = USER_SCHEDULES.get(date_key)
        if manual:
            return manual
        p_status = get_pattern_status(date_key)
        if p_status:
            return {"status": p_status, "start_time": "", "order_no": ""}
        return {"status": "", "start_time": "", "order_no": ""}

    def rebuild_interface():
        nonlocal USER_SCHEDULES, MANGEUN_TARGETS
        today = datetime.now(KST)
        today_y, today_m, today_d = today.year, today.month, today.day
        month_title.value = f"{current['year']}년 {current['month']}월"
        month_prefix = f"{current['year']}-{current['month']:02d}"
        month_data = {k: v for k, v in USER_SCHEDULES.items() if k.startswith(month_prefix)}
        days_in_month = calendar.monthrange(current['year'], current['month'])[1]
        month_effective_statuses = [get_effective_day_info(f"{month_prefix}-{d:02d}").get("status", "") for d in range(1, days_in_month + 1)]
        work_days, off_days = sum(1 for s in month_effective_statuses if s in WORK_STATUSES), sum(1 for s in month_effective_statuses if s in OFF_STATUSES)
        m_target = get_mangeun_target(); mangeun_display_box.content.value = str(m_target)
        annual_used = sum(1 for date_key, info in USER_SCHEDULES.items() if date_key.startswith(f"{current['year']}-") and isinstance(info, dict) and info.get("status") == "연차")
        annual_remaining = max(0, 15 - annual_used)
        stats_text.value = f"근무: {work_days}"
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
                if day == 0: week_row.controls.append(ft.Container(expand=1, height=cell_h, bgcolor="#FFFFFF", border=ft.Border.all(0.5, "black")))
                else:
                    weekday = datetime(current['year'], current['month'], day).weekday()
                    date_key = f"{current['year']}-{current['month']:02d}-{day:02d}"
                    day_info = get_effective_day_info(date_key)
                    status, start_time, order_no = day_info.get("status", ""), day_info.get("start_time", ""), day_info.get("order_no", "")
                    bg_color = "#F7F7F7"
                    text_color = status_color(status) if status else "#000000"
                    if status in ("오전", "오후", "전일", "근무") and order_no:
                        status_desc = f"{status}({order_no})"
                    else:
                        status_desc = status
                    holiday_name = get_holiday_name(date_key)
                    day_number_color = "#D93025" if (weekday == 6 or holiday_name) else ("#1A73E8" if weekday == 5 else "#000000")
                    time_display = ft.Text(start_time, size=10, weight="bold", color=text_color) if start_time and status != "휴무" else ft.Container()
                    memo_text = DATE_MEMOS.get(date_key, "")
                    memo_display = ft.Text(memo_text, size=9, color="#7E22CE", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS) if memo_text else ft.Container()
                    day_number_row = ft.Row(
                        [ft.Text(f"{day}", size=12, weight="normal", italic=True, color=day_number_color)] +
                        ([ft.Text(holiday_name, size=8, weight="bold", color="#D93025")] if holiday_name else []),
                        alignment="center", spacing=3, tight=True,
                    )
                    day_box = ft.Container(content=ft.Column([day_number_row, ft.Text(status_desc, size=10, weight="bold", color=text_color), time_display, memo_display], alignment="start", horizontal_alignment="center", spacing=1), bgcolor="#FFFFFF", padding=ft.Padding.only(top=0), border=ft.Border.all(2, "#2563EB") if (current['year'] == today_y and current['month'] == today_m and day == today_d) else ft.Border.all(0.5, "black"), border_radius=0, height=cell_h, expand=1, on_click=lambda e, dk=date_key: open_input_popup(dk))
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
        popup_date_title.value = date_key
        day_info = get_effective_day_info(date_key)
        current_time, current_order = day_info.get("start_time", ""), day_info.get("order_no", "")
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
        popup_layer.content, popup_layer.visible = popup_card, True; page.update()

    # 근무 저장 및 삭제 처리 함수
    def select_status_and_save(action):
        target_date = current["selected_date"]
        if action == "선택취소":
            USER_SCHEDULES.pop(target_date, None); DATE_MEMOS.pop(target_date, None); page.run_task(save_all_to_client_storage); popup_layer.visible = False; rebuild_interface(); return
        memo_value = memo_field.value.strip() if memo_field.value else ""
        if memo_value:
            DATE_MEMOS[target_date] = memo_value
        else:
            DATE_MEMOS.pop(target_date, None)
        status_value = pending_status_state["value"]
        if not status_value:
            page.run_task(save_all_to_client_storage); popup_layer.visible = False; rebuild_interface(); return
        h, m = selected_time_state["hour"], selected_time_state["minute"]
        final_time = f"{h:02d}:{m:02d}" if (status_value != "휴무" and h is not None and m is not None) else ""
        USER_SCHEDULES[target_date] = {"status": status_value, "start_time": final_time, "order_no": "" if status_value == "휴무" else order_value_state["value"]}
        page.run_task(save_all_to_client_storage); popup_layer.visible = False; rebuild_interface()

    # 팝업 내부 스크롤뷰 레이아웃 구조체
    popup_card = make_full_width_sheet(ft.Column([
            ft.Row([popup_date_title], alignment="center"),
            ft.Row([current_status_display, ft.ElevatedButton(content=ft.Container(ft.Text("근무변경", size=13, weight="bold", color="white"), alignment=ft.Alignment.CENTER), bgcolor="#374151", height=36, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.Padding.symmetric(horizontal=14)), on_click=open_status_picker)], alignment="spaceBetween"),
            ft.Divider(height=1),
            ft.Text("첫탕 시간을 선택하세요", size=12, weight="bold", color="grey"),
            ft.Row([
                hour_display_box,
                ft.Container(content=ft.Text(":", size=18, weight="bold", color="black"), width=24, alignment=ft.Alignment.CENTER),
                minute_display_box,
                ft.Container(width=24),
                order_display_box,
            ], alignment="center", spacing=0),
            ft.Divider(height=2, color="transparent"),
            memo_field,
            ft.Row([ft.Container(content=ft.Text("저장", size=14, weight="bold", color="white"), bgcolor="#2563EB", alignment=ft.Alignment(0, 0), width=160, height=38, border_radius=6, on_click=lambda e: select_status_and_save("저장"))], alignment="center"), ft.Divider(height=1, color="transparent"),
            ft.Row([ft.TextButton("선택취소(삭제)", on_click=lambda e: select_status_and_save("선택취소"), style=ft.ButtonStyle(color="red")), ft.TextButton("닫기", on_click=lambda e: setattr(popup_layer, "visible", False) or page.update())], alignment="spaceBetween")
        ], spacing=6, tight=True))

    # 상단 내비게이션 바 (이전달 / 다음달 이동) 버튼 컴포넌트
    header_nav = ft.Row([
        ft.TextButton("◀ 이전", on_click=lambda e: move_prev(e), style=ft.ButtonStyle(color="black", padding=0)),
        month_title,
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

    def summary_cell(text_control):
        return ft.Container(content=text_control, expand=1, padding=ft.Padding.symmetric(horizontal=12, vertical=8), alignment=ft.Alignment.CENTER_LEFT)

    summary_area = ft.Container(
        content=ft.Column([
            ft.Row([summary_cell(stats_text), ft.Container(width=1, height=32, bgcolor="#93C5FD"), summary_cell(annual_used_text)], spacing=0),
            ft.Divider(height=1, color="#93C5FD"),
            ft.Row([summary_cell(mangeun_text), ft.Container(width=1, height=32, bgcolor="#93C5FD"), summary_cell(annual_remaining_text)], spacing=0),
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
        page.run_task(save_all_to_client_storage)
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
    emergency_form_container = ft.Container(content=ft.Column([ft.Row([ft.Text("🚨 긴급연락처", size=16, weight="bold", color="#1E3A8A")]), ft.Divider(height=1), ft.Row([em_name := ft.TextField(cursor_width=1, label="이름/서비스명", label_style=ft.TextStyle(size=11), width=100, height=38, text_size=13, content_padding=8), em_phone := ft.TextField(cursor_width=1, label="전화번호(숫자만)", label_style=ft.TextStyle(size=11), expand=True, height=38, text_size=13, content_padding=8, keyboard_type=ft.KeyboardType.PHONE), ft.ElevatedButton(content=ft.Text("등록", size=12, weight="bold", color="white"), bgcolor="#2563EB", width=60, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e: add_emergency_item())], spacing=4), ft.Divider(height=1, color="#E2E8F0")]))

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

    # 본문과 하단 메뉴를 세로로 분리한 뒤, 팝업 레이어만 전체 화면 위에 올린다.
    def start_main_swipe(e):
        if current_tab == "긴급연락처":
            start_contacts_swipe(e)
        elif current_tab == "근무현황":
            start_driving_swipe(e)

    def update_main_swipe(e):
        if current_tab == "긴급연락처":
            update_contacts_swipe(e)
        elif current_tab == "근무현황":
            update_driving_swipe(e)

    def finish_main_swipe(e):
        if current_tab == "긴급연락처":
            finish_contacts_swipe(e)
        elif current_tab == "근무현황":
            finish_driving_swipe(e)

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

        # 🔧 날짜 편집/피커 등 모달 팝업이 열려있으면, 뒤로가기는 "그 팝업을 닫는 것"이 최우선.
        # 이걸 안 하면 팝업이 떠 있어도 current_tab이 여전히 "달력"이라서
        # 종료 확인 팝업이 잘못 뜨는 버그가 생김.
        open_popups = [
            popup_layer, value_picker_popup_layer, mangeun_popup_layer,
            pattern_popup_layer, pattern_name_popup_layer, reset_confirm_popup_layer,
            status_picker_popup_layer, driver_list_popup_layer,
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
    change_tab("달력"); rebuild_interface()

if os.environ.get("PORT"):
    # 🌐 Render 등 웹 서버로 배포될 때 (PORT 환경변수가 있을 때만) 브라우저/포트 지정 방식으로 실행
    ft.app(target=main, port=int(os.environ.get("PORT")), view=ft.AppView.WEB_BROWSER)
else:
    # 📱 APK/네이티브 빌드 또는 로컬 실행 시에는 포트/브라우저 강제 지정 없이 기본 방식으로 실행
    ft.app(target=main)
