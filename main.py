# ==========================================
# [앱 이름: 버스캘린더]
# 현재 배포 버전: 빌드 0005 (주석 및 이모지 완벽 복구본)
# ==========================================

import os
import calendar
from datetime import datetime, timedelta, timezone
import flet as ft
import json

# 한국 표준시(KST) 및 데이터베이스/저장소 키 설정
KST = timezone(timedelta(hours=9))
STORAGE_SCHEDULES_KEY = "bus_helper_schedules"
STORAGE_MANGEUN_KEY = "bus_helper_mangeun_targets"
STORAGE_INPUT_DATA_KEY = "bus_helper_input_data"
STORAGE_PHONEBOOK_KEY = "bus_helper_phonebook"
STORAGE_EMERGENCY_KEY = "bus_helper_emergency"
STORAGE_PATTERN_KEY = "bus_helper_work_pattern"

# 🔁 반복 근무 패턴 정의 (버스종사자 근무 유형별 순환 사이클)
WORK_PATTERNS = {
    "4일오전 4일오후": ["오전", "오전", "오전", "오전", "휴무", "오후", "오후", "오후", "오후", "휴무"],
    "5일오전 5일오후": ["오전", "오전", "오전", "오전", "오전", "휴무", "오후", "오후", "오후", "오후", "오후", "휴무"],
    "격일제": ["근무", "휴무"],
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

def main(page: ft.Page):
    page.title = "버스캘린더"
    page.theme_mode = "light"
    page.padding = 4

    # 긴급연락처 화면을 담을 메인 기둥 레이아웃
    setting_column = ft.Column(spacing=2, visible=False)

    # 메모리 상의 긴급연락처 리스트 변수
    EMERGENCY_LIST = []

    # 스마트폰 내부 저장소(Client Storage)에서 기존 데이터 불러오기
    saved_schedules = page.client_storage.get(STORAGE_SCHEDULES_KEY)
    saved_targets = page.client_storage.get(STORAGE_MANGEUN_KEY)
    saved_input_data = page.client_storage.get(STORAGE_INPUT_DATA_KEY)
    saved_phonebook = page.client_storage.get(STORAGE_PHONEBOOK_KEY)
    
    saved_emergency = page.client_storage.get(STORAGE_EMERGENCY_KEY)
    if saved_emergency:
        EMERGENCY_LIST = json.loads(saved_emergency)

    saved_pattern = page.client_storage.get(STORAGE_PATTERN_KEY)
    # pattern_state: name(패턴명) / anchor_date(기준일 YYYY-MM-DD) / anchor_index(그날이 패턴의 몇 번째인지)
    pattern_state = json.loads(saved_pattern) if saved_pattern else {"name": None, "anchor_date": None, "anchor_index": 0}

    USER_SCHEDULES = json.loads(saved_schedules) if saved_schedules else {}
    MANGEUN_TARGETS = json.loads(saved_targets) if saved_targets else {}
    PHONEBOOK_LIST = json.loads(saved_phonebook) if saved_phonebook else []
    
    # 운행정보(내차/앞차/뒷차) 초기값 세팅
    if saved_input_data:
        input_data_state = json.loads(saved_input_data)
    else:
        input_data_state = {
            "route": "미입력",
            "bus_no": "미입력",
            "front_bus": "미입력", "front_driver": "미입력", "front_phone": "미입력",
            "back_bus": "미입력", "back_driver": "미입력", "back_phone": "미입력"
        }

    # 데이터 변경 시 스마트폰 저장소에 즉시 통합 저장하는 함수
    def save_all_to_client_storage():
        page.client_storage.set(STORAGE_SCHEDULES_KEY, json.dumps(USER_SCHEDULES, ensure_ascii=False))
        page.client_storage.set(STORAGE_MANGEUN_KEY, json.dumps(MANGEUN_TARGETS, ensure_ascii=False))
        page.client_storage.set(STORAGE_INPUT_DATA_KEY, json.dumps(input_data_state, ensure_ascii=False))
        page.client_storage.set(STORAGE_PHONEBOOK_KEY, json.dumps(PHONEBOOK_LIST, ensure_ascii=False))
        page.client_storage.set(STORAGE_EMERGENCY_KEY, json.dumps(EMERGENCY_LIST, ensure_ascii=False))
        page.client_storage.set(STORAGE_PATTERN_KEY, json.dumps(pattern_state, ensure_ascii=False))

    # 앱 켜질 때 오늘 날짜 및 시간 제어용 초기값 설정
    now_kst = datetime.now(KST)
    current = {"year": now_kst.year, "month": now_kst.month, "selected_date": f"{now_kst.year}-{now_kst.month:02d}-{now_kst.day:02d}"}
    selected_time_state = {"hour": 5, "minute": 0}

    current_tab = "달력"

    # 메인 상단 텍스트 레이블 선언
    month_title = ft.Text("", size=20, weight="bold", text_align="center")
    stats_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_value_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    
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
        padding=12, border=ft.border.all(1, "#2563EB"), border_radius=10, visible=False
    )
    
    # 📇 전화번호부는 이제 하단 '연락처' 탭 안에 통합되어 있음 (별도 큰 버튼 제거됨)

    # [하단 탭 메뉴 버튼] 기사님 디자인 피드백 반영 (텍스트 이모지 장착 및 한여름의 패딩 제거 버전)
    btn_status = ft.ElevatedButton(content=ft.Container(content=ft.Text("📊 근무현황", color="white", size=11, weight="bold"), alignment=ft.alignment.center), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: navigate_to("/status"))
    btn_setting = ft.ElevatedButton(content=ft.Container(content=ft.Text("📇 연락처", color="white", size=11, weight="bold"), alignment=ft.alignment.center), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: navigate_to("/emergency"))
    btn_config = ft.ElevatedButton(content=ft.Container(content=ft.Text("⚙️ 설정", color="white", size=11, weight="bold"), alignment=ft.alignment.center), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: navigate_to("/settings"))

    # 달력 최상단 요일 표시줄 (일~토)
    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row([ft.Container(content=ft.Text(d, size=13, weight="bold", color="#D93025" if d=="일" else ("#1A73E8" if d=="토" else "black")), expand=1, alignment=ft.Alignment(0, 0), padding=ft.padding.symmetric(vertical=2), bgcolor="#E5E7EB", border=ft.border.all(0.5, "black")) for d in days_letters], alignment="spaceAround", spacing=0)
    calendar_table = ft.Column([weeks_header, calendar_grid], spacing=0)


    # 📞 전화번호부 목록을 화면에 다시 그려주는 함수 (일반연락처용)
    def rebuild_phonebook_view():
        phonebook_items_column.controls.clear()
        if not PHONEBOOK_LIST:
            phonebook_items_column.controls.append(ft.Container(content=ft.Text("등록된 연락처가 없습니다.\n자주 쓰는 번호를 상단에 등록해 보세요!", size=13, color="grey", text_align="center"), padding=20, alignment=ft.alignment.center))
        else:
            for index, item in enumerate(PHONEBOOK_LIST):
                name = item.get("name", "")
                phone = item.get("phone", "")
                is_edit = item.get("is_edit", False)
        
                if is_edit:
                    edit_name = ft.TextField(cursor_width=1, value=name, width=90, height=34, text_size=13, content_padding=6)
                    edit_phone = ft.TextField(cursor_width=1, value=phone.replace("-",""), expand=True, height=34, text_size=13, content_padding=6, keyboard_type=ft.KeyboardType.PHONE)
                    
                    def save_edit(idx, en, ep):
                        if en.value and ep.value:
                            PHONEBOOK_LIST[idx] = {"name": en.value, "phone": final_format_phone(ep.value), "is_edit": False}
                            PHONEBOOK_LIST.sort(key=lambda x: x.get("name", ""))
                            save_all_to_client_storage()
                            rebuild_phonebook_view()

                    row_content = ft.Row([
                        edit_name, edit_phone,
                        ft.ElevatedButton(content=ft.Container(ft.Text("저장", size=11, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="green", width=50, height=34, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e, idx=index, en=edit_name, ep=edit_phone: save_edit(idx, en, ep)),
                        ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=11, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="grey", width=50, height=34, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e, idx=index: toggle_edit_mode(idx, False))
                    ], spacing=4)
                else:
                    row_content = ft.Row([
                        ft.GestureDetector(content=ft.Row([ft.Text(f"{name}", size=14, weight="bold", color="black", width=65), ft.Text(f"{phone}", size=13, weight="bold", color="#1E3A8A", no_wrap=True), ft.Icon(ft.icons.PHONE, color="green", size=14)], spacing=4, alignment="start"), on_tap=lambda e, p=phone: make_call(p), expand=True),
                        ft.Row([
                            ft.ElevatedButton(content=ft.Container(ft.Text("수정", size=10, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="#2563EB", width=40, height=28, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e, idx=index: toggle_edit_mode(idx, True)),
                            ft.ElevatedButton(content=ft.Container(ft.Text("삭제", size=10, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="#1E3A8A", width=40, height=28, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e, idx=index: delete_phonebook_item(idx))
                        ], spacing=3)
                    ], alignment="spaceBetween")

                phonebook_items_column.controls.append(ft.Container(content=row_content, padding=ft.padding.only(left=4, right=4, top=8, bottom=8), border=ft.border.Border(bottom=ft.border.BorderSide(0.5, "#E2E8F0"))))
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
            target_column.controls.append(ft.Container(content=ft.Text("등록된 긴급 연락처가 없습니다.\n사무실, 정비실 번호를 등록해 보세요!", size=13, color="grey", text_align="center"), padding=20, alignment=ft.alignment.center))
        else:
            for index, item in enumerate(EMERGENCY_LIST):
                name = item.get("name", "")
                phone = item.get("phone", "")
                is_edit = item.get("is_edit", False)
                is_special = name in ["사무실", "정비실"]
                name_color = "#E65100" if is_special else "black"
                
                if is_edit:
                    edit_em_name = ft.TextField(cursor_width=1, value=name, width=90, height=34, text_size=13, content_padding=6)
                    edit_em_phone = ft.TextField(cursor_width=1, value=phone.replace("-",""), expand=True, height=34, text_size=13, content_padding=6, keyboard_type=ft.KeyboardType.PHONE)
                    
                    def save_em_edit(idx, en, ep):
                        if en.value and ep.value:
                            EMERGENCY_LIST[idx] = {"name": en.value.strip(), "phone": final_format_phone(ep.value), "is_edit": False}
                            save_all_to_client_storage()
                            rebuild_emergency_view(setting_column)

                    row_content = ft.Row([
                        edit_em_name, edit_em_phone,
                        ft.ElevatedButton(content=ft.Container(ft.Text("저장", size=11, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="green", width=50, height=34, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e, idx=index, en=edit_em_name, ep=edit_em_phone: save_em_edit(idx, en, ep)),
                        ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=11, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="grey", width=50, height=34, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e, idx=index: toggle_em_edit_mode(idx, False))
                    ], spacing=4)
                else:
                    display_text = f"{name}: {phone}" if phone else f"{name}: (번호 없음)"
                    action_buttons = [
                        ft.IconButton(ft.icons.PHONE, icon_color="green", on_click=lambda e, ph=phone: page.launch_url(f"tel:{ph}") if ph else None),
                        ft.ElevatedButton(content=ft.Container(ft.Text("수정", size=10, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="#2563EB", width=40, height=28, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e, idx=index: toggle_em_edit_mode(idx, True)),
                        ft.ElevatedButton(content=ft.Container(ft.Text("삭제", size=10, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="#1E3A8A", width=40, height=28, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e, idx=index: delete_emergency_item(idx, target_column))
                    ]
                    row_content = ft.Row([ft.Text(display_text, size=14, weight="bold" if is_special else "normal", color=name_color), ft.Row(action_buttons, spacing=3)], alignment="spaceBetween")
                
                target_column.controls.append(ft.Container(content=row_content, padding=ft.padding.only(left=4, right=4, top=8, bottom=8), border=ft.border.Border(bottom=ft.border.BorderSide(0.5, "#E2E8F0"))))
        page.update()

    # ⚙️ 설정 화면 - 반복 근무 패턴 선택 (예: 4일오전 4일오후 등 순환근무 자동 채우기)
    pattern_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    pending_pattern_name = {"value": None}
    popup_view_mode = {"mode": "list", "confirm_idx": None}

    def pattern_slot_color(slot_status):
        return {"오전": "#1A73E8", "오후": "#7E22CE", "휴무": "#D93025", "전일": "#137333", "근무": "#137333"}.get(slot_status, "black")

    def close_pattern_popup(e):
        pattern_popup_layer.visible = False
        pattern_dropdown.value = None
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

    def confirm_apply_pattern(e):
        today_str = datetime.now(KST).strftime("%Y-%m-%d")
        pattern_state["name"] = pending_pattern_name["value"]
        pattern_state["anchor_date"] = today_str
        pattern_state["anchor_index"] = popup_view_mode["confirm_idx"]
        save_all_to_client_storage()
        pattern_popup_layer.visible = False
        pattern_dropdown.value = None
        rebuild_settings_view(); rebuild_interface()

    def clear_pattern(e):
        pattern_state["name"], pattern_state["anchor_date"], pattern_state["anchor_index"] = None, None, 0
        save_all_to_client_storage()
        rebuild_settings_view(); rebuild_interface()

    def build_pattern_popup():
        pat = WORK_PATTERNS.get(pending_pattern_name["value"], [])
        if popup_view_mode["mode"] == "confirm" and popup_view_mode["confirm_idx"] is not None:
            idx = popup_view_mode["confirm_idx"]
            slot_status = pat[idx] if idx < len(pat) else ""
            pattern_popup_layer.content = ft.Container(
                content=ft.Column([
                    ft.Text(f"{pending_pattern_name['value']}", size=15, weight="bold", color="black"),
                    ft.Text(f"오늘을 {idx+1}번째 근무({slot_status})로\n적용하시겠습니까?", size=14, color="black", text_align="center"),
                    ft.Row([
                        ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=14, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="#2563EB", expand=1, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=confirm_apply_pattern),
                        ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="grey", expand=1, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=back_to_slot_list),
                    ], spacing=8),
                ], spacing=14, tight=True, horizontal_alignment="center"),
                bgcolor="white", padding=16, border_radius=12, width=280,
            )
        else:
            slot_rows = []
            for i, slot_status in enumerate(pat):
                slot_rows.append(
                    ft.Container(
                        content=ft.Text(f"{i+1}. {slot_status}", size=14, weight="bold", color=pattern_slot_color(slot_status)),
                        bgcolor="#F1F5F9",
                        padding=ft.padding.symmetric(vertical=10, horizontal=14), border_radius=6,
                        on_click=lambda e, idx=i: select_pattern_slot(idx),
                    )
                )
            pattern_popup_layer.content = ft.Container(
                content=ft.Column([
                    ft.Text(f"오늘 근무선택 ({pending_pattern_name['value']})", size=15, weight="bold", color="black"),
                    ft.Text("오늘이 몇 번째 근무인지 선택하세요.", size=12, color="grey"),
                    ft.Column(slot_rows, spacing=6, scroll=ft.ScrollMode.AUTO, height=min(360, len(pat) * 48)),
                    ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("닫기", size=14, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="grey", expand=1, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=close_pattern_popup)], spacing=8),
                ], spacing=10, tight=True),
                bgcolor="white", padding=16, border_radius=12, width=280,
            )

    def open_pattern_popup(pattern_name):
        pending_pattern_name["value"] = pattern_name
        popup_view_mode["mode"], popup_view_mode["confirm_idx"] = "list", None
        build_pattern_popup()
        pattern_popup_layer.visible = True
        page.update()

    def on_pattern_dropdown_change(e):
        val = e.control.value
        if val and val in WORK_PATTERNS:
            open_pattern_popup(val)

    pattern_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(k) for k in WORK_PATTERNS.keys()],
        value=None, hint_text="눌러서 선택하세요", width=260, height=44, text_size=13, content_padding=ft.padding.symmetric(vertical=8, horizontal=10), on_change=on_pattern_dropdown_change,
    )
    pattern_status_text = ft.Text("", size=12, color="grey")

    def rebuild_settings_view():
        if pattern_state.get("name"):
            pattern_status_text.value = f"✅ 현재 적용중: {pattern_state['name']} (기준일 {pattern_state['anchor_date']})"
        else:
            pattern_status_text.value = "적용된 반복 근무 패턴이 없습니다."
        pattern_dropdown.value = None
        settings_zone_container.controls.clear()
        settings_zone_container.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("⚙️ 설정", size=16, weight="bold", color="#1E3A8A"),
                    ft.Divider(height=1),
                    ft.Text("근무형태 (반복 근무 패턴)", size=13, weight="bold", color="black"),
                    pattern_status_text,
                    ft.Text("패턴 선택:", size=12, color="grey"),
                    pattern_dropdown,
                    ft.Row([
                        ft.ElevatedButton(content=ft.Container(ft.Text("패턴 해제", size=14, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="grey", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=clear_pattern),
                    ], spacing=8),
                ], spacing=8, tight=True),
                padding=12, bgcolor="#F8FAFC", border_radius=8, border=ft.border.all(1, "#E2E8F0"),
            )
        )
        page.update()

    # 연락처 관리 관련 내부 기능 함수들 (삭제/토글/추가 등)
    def delete_emergency_item(index, target_column):
        if 0 <= index < len(EMERGENCY_LIST):
            EMERGENCY_LIST.pop(index)
            save_all_to_client_storage()
            rebuild_emergency_view(target_column)

    def toggle_em_edit_mode(index, status):
        if 0 <= index < len(EMERGENCY_LIST):
            EMERGENCY_LIST[index]["is_edit"] = status
            rebuild_emergency_view(setting_column)

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
            save_all_to_client_storage()
            em_name.value = ""
            em_phone.value = ""
            rebuild_emergency_view(setting_column)

    def add_phonebook_item():
        if pb_name.value and pb_phone.value:
            formatted_num = final_format_phone(pb_phone.value)
            PHONEBOOK_LIST.append({"name": pb_name.value, "phone": formatted_num, "is_edit": False})
            PHONEBOOK_LIST.sort(key=lambda x: x.get("name", ""))
            save_all_to_client_storage()
            pb_name.value = ""
            pb_phone.value = ""
            rebuild_phonebook_view()

    def delete_phonebook_item(index):
        if 0 <= index < len(PHONEBOOK_LIST):
            PHONEBOOK_LIST.pop(index)
            save_all_to_client_storage()
            rebuild_phonebook_view()

    def toggle_edit_mode(index, status):
        if 0 <= index < len(PHONEBOOK_LIST):
            PHONEBOOK_LIST[index]["is_edit"] = status
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

        if tab_name == "달력":
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, settings_zone_container.visible, weeks_header.visible = True, False, True, True, False, False, False, False, True
        elif tab_name == "근무현황":
            topbar_title.value = "📊 근무현황"
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, settings_zone_container.visible, weeks_header.visible = False, True, False, False, True, False, False, False, False
            refresh_input_tab_view()
        elif tab_name == "긴급연락처":
            topbar_title.value = "📇 연락처"
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, settings_zone_container.visible, weeks_header.visible = False, False, False, False, False, True, True, False, False
            rebuild_emergency_view(setting_column)
            PHONEBOOK_LIST.sort(key=lambda x: x.get("name", ""))
            rebuild_phonebook_view()
        elif tab_name == "설정":
            topbar_title.value = "⚙️ 설정"
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, settings_zone_container.visible, weeks_header.visible = False, False, False, False, False, False, False, True, False
            rebuild_settings_view()
        page.update()

    # 🧭 URL 라우팅: 브라우저/안드로이드 "뒤로가기"가 각 화면 → 달력(홈)으로 자연스럽게 이어지도록 연결
    ROUTE_TO_TAB = {"/": "달력", "/home": "달력", "/status": "근무현황", "/emergency": "긴급연락처", "/settings": "설정"}

    def on_route_change(e):
        change_tab(ROUTE_TO_TAB.get(page.route, "달력"))
        # 🚫 달력(홈) 화면에서 뒤로가기를 눌러도 앱이 꺼지지 않도록,
        # "/"와 "/home"을 번갈아 다시 쌓아서 항상 뒤로 갈 곳이 남아있게 만듦
        if page.route == "/":
            page.go("/home")
        elif page.route == "/home":
            page.go("/")

    page.on_route_change = on_route_change

    # 🧭 탭 이동 헬퍼: 달력(홈)에서 이동할 때만 새 히스토리를 쌓고, 하위화면끼리 이동할 땐 히스토리를 안 쌓아서
    # "뒤로가기 한 번 = 무조건 달력으로" 동작이 되도록 함
    def navigate_to(route):
        if page.route in ("/", "/home"):
            page.go(route)
        else:
            page.route = route
            change_tab(ROUTE_TO_TAB.get(route, "달력"))

    # 달력 날짜 클릭 시 튀어나오는 첫탕 근무등록 팝업창 세팅들
    popup_date_title = ft.Text("", size=16, weight="bold", color="black", text_align="center")
    order_options = [ft.dropdown.Option("", "선택 안 함")] + [ft.dropdown.Option(str(i), f"{i}번") for i in range(1, 51)]
    order_dropdown = ft.Dropdown(options=order_options, width=140, height=40, text_size=13, content_padding=ft.padding.symmetric(vertical=4, horizontal=10))
    
    def on_mangeun_dropdown_changed(e):
        try:
            val = int(mangeun_dropdown.value)
            key = f"{current['year']}_{current['month']}"
            MANGEUN_TARGETS[key] = val
            save_all_to_client_storage()
            mangeun_popup_layer.visible = False
            rebuild_interface()
        except: pass

    mangeun_dropdown = ft.Dropdown(options=[ft.dropdown.Option(str(i)) for i in range(15, 27)], width=62, height=36, text_size=12, content_padding=ft.padding.symmetric(vertical=4, horizontal=8))
    hour_picker = ft.Dropdown(options=[ft.dropdown.Option(f"{i:02d}") for i in range(24)], value="05", width=100, height=48, text_size=18, content_padding=ft.padding.symmetric(vertical=8, horizontal=10), on_change=lambda e: update_hour(int(e.control.value)))
    minute_picker = ft.Dropdown(options=[ft.dropdown.Option(f"{i:02d}") for i in range(60)], value="00", width=100, height=48, text_size=18, content_padding=ft.padding.symmetric(vertical=8, horizontal=10), on_change=lambda e: update_minute(int(e.control.value)))

    def update_hour(val): selected_time_state["hour"] = val
    def update_minute(val): selected_time_state["minute"] = val

    dial_row = ft.Row([hour_picker, ft.Text(":", size=20, weight="bold", color="black"), minute_picker], alignment="center")
    popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    mangeun_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    status_picker_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    # 매월 유동적으로 변하는 자동 만근 일수 계산 로직
    def get_mangeun_target():
        try:
            y, m = int(current['year']), int(current['month'])
            key = f"{y}_{m}"
            if key in MANGEUN_TARGETS: return int(MANGEUN_TARGETS[key])
            return 22 if calendar.monthrange(y, m)[1] == 31 else (20 if m == 2 else 21)
        except: return 22

    # 번호 터치 시 스마트폰 기본 전화 다이얼로 즉시 토스해 주는 함수
    def make_call(phone_number):
        if phone_number and phone_number != "미입력": page.launch_url(f"tel:{phone_number}")

    # 🚍 운행정보 탭 내부의 내차/앞차/뒷차 요약 카드뷰 빌드
    def build_driving_summary_zone():
        my_card = ft.Container(content=ft.Column([ft.Row([ft.Text("내차 정보", size=11, color="grey", weight="bold"), ft.ElevatedButton(content=ft.Container(ft.Text("입력", size=10, weight="bold", color="white"), alignment=ft.alignment.center), on_click=lambda e: open_info_input_popup("내차"), bgcolor="#2563EB", width=55, height=22, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0))], alignment="spaceBetween"), ft.Text(f"노선: {input_data_state['route']}", size=14, weight="bold", color="black"), ft.Text(f"내차: {input_data_state['bus_no']}", size=14, weight="bold", color="black"), ft.Container(height=15)], spacing=2, tight=True), bgcolor="#F8FAFC", border=ft.border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1)
        front_card = ft.Container(content=ft.Column([ft.Row([ft.Text("앞차 정보", size=11, color="grey", weight="bold"), ft.ElevatedButton(content=ft.Container(ft.Text("입력", size=10, weight="bold", color="white"), alignment=ft.alignment.center), on_click=lambda e: open_info_input_popup("앞차"), bgcolor="#1E3A8A", width=55, height=22, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0))], alignment="spaceBetween"), ft.Text(input_data_state['front_bus'], size=14, weight="bold", color="black"), ft.Text(input_data_state['front_driver'], size=14, weight="bold", color="black"), ft.GestureDetector(content=ft.Row([ft.Text(input_data_state['front_phone'], size=13, color="#1E3A8A", weight="bold"), ft.Icon(ft.icons.PHONE, color="green", size=16) if input_data_state['front_phone'] != "미입력" else ft.Container()], spacing=4, alignment="start"), on_tap=lambda e: make_call(input_data_state['front_phone']))], spacing=2, tight=True), bgcolor="#F8FAFC", border=ft.border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1)
        back_card = ft.Container(content=ft.Column([ft.Row([ft.Text("뒷차 정보", size=11, color="grey", weight="bold"), ft.ElevatedButton(content=ft.Container(ft.Text("입력", size=10, weight="bold", color="white"), alignment=ft.alignment.center), on_click=lambda e: open_info_input_popup("뒷차"), bgcolor="#1E3A8A", width=55, height=22, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0))], alignment="spaceBetween"), ft.Text(input_data_state['back_bus'], size=14, weight="bold", color="black"), ft.Text(input_data_state['back_driver'], size=14, weight="bold", color="black"), ft.GestureDetector(content=ft.Row([ft.Text(input_data_state['back_phone'], size=13, color="#1E3A8A", weight="bold"), ft.Icon(ft.icons.PHONE, color="green", size=16) if input_data_state['back_phone'] != "미입력" else ft.Container()], spacing=4, alignment="start"), on_tap=lambda e: make_call(input_data_state['back_phone']))], spacing=2, tight=True), bgcolor="#F8FAFC", border=ft.border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1)
        return ft.Container(content=ft.Column([ft.Text("🚍 운행 정보 요약", size=14, weight="bold", color="#1E3A8A"), my_card, ft.Row([front_card, back_card], spacing=8, alignment="spaceAround")], spacing=8), padding=12, border=ft.border.all(1, "#2563EB"), border_radius=10, margin=ft.margin.only(bottom=10))

    # 하이픈(-) 자동 정렬 마법의 번호 교정 포맷 함수
    def final_format_phone(raw_value):
        clean = "".join(filter(str.isdigit, raw_value))
        if len(clean) <= 3: return clean
        elif len(clean) <= 7: return f"{clean[:3]}-{clean[3:]}"
        elif len(clean) <= 10: return f"{clean[:3]}-{clean[3:6]}-{clean[6:]}"
        else: return f"{clean[:3]}-{clean[3:7]}-{clean[7:11]}"

    # 앞차/뒷차/내차 세부 입력용 팝업 조립 레이아웃 구역
    # 📇 앞차/뒷차 기사성함 입력 시, 기사연락처(전화번호부)에서 선택하면 전화번호가 자동으로 채워지는 드롭다운
    def build_driver_picker(name_field, phone_field):
        def on_driver_pick(e):
            val = e.control.value
            if val and val != "직접입력":
                match = next((p for p in PHONEBOOK_LIST if p.get("name") == val), None)
                if match:
                    name_field.value = match.get("name", "")
                    phone_field.value = match.get("phone", "").replace("-", "")
                    page.update()
        options = [ft.dropdown.Option("직접입력")] + [ft.dropdown.Option(p["name"]) for p in PHONEBOOK_LIST if p.get("name")]
        return ft.Dropdown(options=options, value="직접입력", label="기사연락처에서 선택", label_style=ft.TextStyle(size=11), height=44, text_size=13, content_padding=ft.padding.symmetric(vertical=8, horizontal=10), on_change=on_driver_pick)

    def open_info_input_popup(target_type):
        if target_type == "내차":
            tf_route, tf_bus_no = ft.TextField(cursor_width=1, label="노선번호", value=input_data_state["route"].replace("미입력",""), keyboard_type=ft.KeyboardType.TEXT, expand=True, height=38), ft.TextField(cursor_width=1, label="내차번호", value=input_data_state["bus_no"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38)
            def save_my(e):
                input_data_state["route"], input_data_state["bus_no"] = tf_route.value if tf_route.value else "미입력", f"{tf_bus_no.value}호" if tf_bus_no.value else "미입력"
                save_all_to_client_storage(); info_dialog.open = False; page.update(); rebuild_interface()
            box_content = ft.Container(content=ft.Column([ft.Text("👤 내 차량 설정", size=14, weight="bold"), ft.Row([tf_route, tf_bus_no]), ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=save_my, expand=1, height=38, bgcolor="#2563EB"), ft.ElevatedButton(content=ft.Container(ft.Text("뒤로가기", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=lambda e: setattr(info_dialog, "open", False) or page.update(), expand=1, height=38, bgcolor="grey")], alignment="center", spacing=8)], spacing=10, tight=True, scroll=ft.ScrollMode.AUTO, height=210), width=260, padding=4)
        elif target_type == "앞차":
            tf_f_bus, tf_f_driver, tf_f_phone = ft.TextField(cursor_width=1, label="앞차번호", value=input_data_state["front_bus"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38), ft.TextField(cursor_width=1, label="기사성함", value=input_data_state["front_driver"].replace("미입력",""), expand=True, height=38), ft.TextField(cursor_width=1, label="전화번호(숫자만)", value=input_data_state["front_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, expand=True, height=38)
            def save_front(e):
                input_data_state["front_bus"], input_data_state["front_driver"], input_data_state["front_phone"] = f"{tf_f_bus.value}호" if tf_f_bus.value else "미입력", tf_f_driver.value if tf_f_driver.value else "미입력", final_format_phone(tf_f_phone.value) if tf_f_phone.value else "미입력"
                save_all_to_client_storage(); info_dialog.open = False; page.update(); rebuild_interface()
            box_content = ft.Container(content=ft.Column([ft.Text("◀ 앞차 정보 입력", size=14, weight="bold"), tf_f_bus, build_driver_picker(tf_f_driver, tf_f_phone), tf_f_driver, tf_f_phone, ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=save_front, expand=1, height=38, bgcolor="#1E3A8A"), ft.ElevatedButton(content=ft.Container(ft.Text("뒤로가기", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=lambda e: setattr(info_dialog, "open", False) or page.update(), expand=1, height=38, bgcolor="grey")], alignment="center", spacing=8)], spacing=10, tight=True, scroll=ft.ScrollMode.AUTO, height=340), width=260, padding=4)
        elif target_type == "뒷차":
            tf_b_bus, tf_b_driver, tf_b_phone = ft.TextField(cursor_width=1, label="뒷차번호", value=input_data_state["back_bus"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38), ft.TextField(cursor_width=1, label="기사성함", value=input_data_state["back_driver"].replace("미입력",""), expand=True, height=38), ft.TextField(cursor_width=1, label="전화번호 (숫자만)", value=input_data_state["back_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, expand=True, height=38)
            def save_back(e):
                input_data_state["back_bus"], input_data_state["back_driver"], input_data_state["back_phone"] = f"{tf_b_bus.value}호" if tf_b_bus.value else "미입력", tf_b_driver.value if tf_b_driver.value else "미입력", final_format_phone(tf_b_phone.value) if tf_b_phone.value else "미입력"
                save_all_to_client_storage(); info_dialog.open = False; page.update(); rebuild_interface()
            box_content = ft.Container(content=ft.Column([ft.Text("▶ 뒷차 정보 입력", size=14, weight="bold"), tf_b_bus, build_driver_picker(tf_b_driver, tf_b_phone), tf_b_driver, tf_b_phone, ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=save_back, expand=1, height=38, bgcolor="#1E3A8A"), ft.ElevatedButton(content=ft.Container(ft.Text("뒤로가기", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=lambda e: setattr(info_dialog, "open", False) or page.update(), expand=1, height=38, bgcolor="grey")], alignment="center", spacing=8)], spacing=10, tight=True, scroll=ft.ScrollMode.AUTO, height=340), width=260, padding=4)
        info_dialog.content = box_content; info_dialog.open = True; page.update()

    info_dialog = ft.AlertDialog(modal=False, content=ft.Container()); page.dialog = info_dialog
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
        m_target = get_mangeun_target(); mangeun_dropdown.value = str(m_target)
        diff = work_days - m_target
        stats_text.value = f"근무: {work_days}(+{diff})" if diff > 0 else (f"근무: {work_days}({diff})" if diff < 0 else f"근무: {work_days}")
        mangeun_text.value, mangeun_value_text.value = f"휴무: {off_days}", f"만근: {m_target}"

        calendar_grid.controls.clear()
        cal = calendar.Calendar(firstweekday=6)
        weeks = cal.monthdayscalendar(current['year'], current['month'])
        # 📐 화면 높이에 맞춰 날짜칸 크기 자동 계산 (기기/글자크기 상관없이 화면에 맞게 조정)
        screen_h = page.height or 700
        chrome_overhead = 230  # 상단바+안내문구+요일줄+구분선+하단탭 등이 차지하는 대략적 높이
        available_h = max(screen_h - chrome_overhead, 60 * len(weeks))
        cell_h = max(60, min(100, available_h / len(weeks)))
        for week in weeks:
            week_row = ft.Row(alignment="spaceAround", spacing=0)
            for day in week:
                if day == 0: week_row.controls.append(ft.Container(expand=1, height=cell_h, bgcolor="#FFFFFF", border=ft.border.all(0.5, "black")))
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
                    holiday_name = HOLIDAYS.get(date_key)
                    day_number_color = "#D93025" if (weekday == 6 or holiday_name) else ("#1A73E8" if weekday == 5 else "#000000")
                    time_display = ft.Text(start_time, size=10, weight="bold", color=text_color) if start_time and status != "휴무" else ft.Container()
                    day_number_row = ft.Row(
                        [ft.Text(f"{day}", size=15, weight="normal", italic=True, color=day_number_color)] +
                        ([ft.Text(holiday_name, size=8, weight="bold", color="#D93025")] if holiday_name else []),
                        alignment="center", spacing=3, tight=True,
                    )
                    day_box = ft.Container(content=ft.Column([day_number_row, ft.Text(status_desc, size=12, weight="bold", color=text_color), time_display], alignment="start", horizontal_alignment="center", spacing=2), bgcolor="#FFFFFF", padding=ft.padding.only(top=0), border=ft.border.all(2, "#2563EB") if (current['year'] == today_y and current['month'] == today_m and day == today_d) else ft.border.all(0.5, "black"), border_radius=0, height=cell_h, expand=1, on_click=lambda e, dk=date_key: open_input_popup(dk))
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
        current_status_display.value = value if value else "미설정"
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
                rows.append(ft.Container(content=ft.Text(opt, size=15, color="grey"), padding=ft.padding.symmetric(vertical=10, horizontal=14), border_radius=6, bgcolor="#F1F5F9", on_click=lambda e: close_status_picker()))
            elif opt == "직접입력":
                rows.append(ft.Container(content=ft.Text(opt, size=15, weight="bold", color="black"), padding=ft.padding.symmetric(vertical=10, horizontal=14), border_radius=6, bgcolor="#F1F5F9", on_click=show_custom_input))
            else:
                rows.append(ft.Container(content=ft.Text(opt, size=15, weight="bold", color=status_color(opt)), padding=ft.padding.symmetric(vertical=10, horizontal=14), border_radius=6, bgcolor="#F1F5F9", on_click=lambda e, v=opt: apply_status_selection(v)))
        status_picker_popup_layer.content = ft.Container(
            content=ft.Column([
                ft.Text("근무변경", size=16, weight="bold", color="black"),
                ft.Column(rows, spacing=6, scroll=ft.ScrollMode.AUTO, height=min(380, len(STATUS_OPTIONS) * 48)),
                ft.Divider(height=1),
                ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="grey", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=close_status_picker)], spacing=8),
            ], spacing=10, tight=True),
            bgcolor="white", padding=16, border_radius=12, width=280,
        )
        page.update()

    def show_custom_input(e):
        custom_status_field.value = ""
        status_picker_popup_layer.content = ft.Container(
            content=ft.Column([
                ft.Text("근무 상태 직접입력", size=16, weight="bold", color="black"),
                custom_status_field,
                ft.Row([
                    ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=14, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="#2563EB", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=confirm_custom_status),
                    ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="grey", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=show_status_list),
                ], spacing=8),
            ], spacing=12, tight=True),
            bgcolor="white", padding=16, border_radius=12, width=280,
        )
        page.update()

    def open_status_picker(e):
        show_status_list()
        status_picker_popup_layer.visible = True
        page.update()

    def open_input_popup(date_key):
        current["selected_date"] = date_key
        popup_date_title.value = f"{date_key}\n첫탕 시간을 선택하세요"
        day_info = get_effective_day_info(date_key)
        current_time, current_order = day_info.get("start_time", ""), day_info.get("order_no", "")
        existing_status = day_info.get("status", "")
        pending_status_state["value"] = existing_status
        current_status_display.value = existing_status if existing_status else "미설정"
        current_status_display.color = status_color(existing_status) if existing_status else "grey"
        order_dropdown.value = str(current_order) if current_order else ""
        if current_time and ":" in current_time:
            h, m = map(int, current_time.split(":"))
            selected_time_state["hour"], selected_time_state["minute"] = h, m
            hour_picker.value, minute_picker.value = f"{h:02d}", f"{m:02d}"
        else:
            selected_time_state["hour"], selected_time_state["minute"], hour_picker.value, minute_picker.value = 5, 0, "05", "00"
        popup_layer.content, popup_layer.visible = popup_card, True; page.update()

    # 근무 저장 및 삭제 처리 함수
    def select_status_and_save(action):
        target_date = current["selected_date"]
        if action == "선택취소":
            USER_SCHEDULES.pop(target_date, None); save_all_to_client_storage(); popup_layer.visible = False; rebuild_interface(); return
        status_value = pending_status_state["value"]
        if not status_value:
            popup_layer.visible = False; page.update(); return
        h, m = selected_time_state["hour"], selected_time_state["minute"]
        final_time = f"{h:02d}:{m:02d}" if status_value != "휴무" else ""
        USER_SCHEDULES[target_date] = {"status": status_value, "start_time": final_time, "order_no": "" if status_value == "휴무" else (order_dropdown.value if order_dropdown.value else "")}
        save_all_to_client_storage(); popup_layer.visible = False; rebuild_interface()

    # 팝업 내부 스크롤뷰 레이아웃 구조체
    popup_card = ft.Container(
        content=ft.Column([
            ft.Row([popup_date_title], alignment="center"), ft.Divider(height=1, color="transparent"),
            ft.Row([current_status_display, ft.ElevatedButton(content=ft.Container(ft.Text("근무변경", size=13, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="#374151", height=36, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(horizontal=14)), on_click=open_status_picker)], alignment="spaceBetween"),
            dial_row, ft.Row([ft.Text("근무 순번:", size=12, weight="bold", color="black"), order_dropdown], alignment="center", spacing=10), ft.Divider(height=2),
            ft.Row([ft.Container(content=ft.Text("저장", size=14, weight="bold", color="white"), bgcolor="#2563EB", alignment=ft.Alignment(0, 0), width=160, height=38, border_radius=6, on_click=lambda e: select_status_and_save("저장"))], alignment="center"), ft.Divider(height=1, color="transparent"),
            ft.Row([ft.TextButton("선택취소(삭제)", on_click=lambda e: select_status_and_save("선택취소"), style=ft.ButtonStyle(color="red")), ft.TextButton("닫기", on_click=lambda e: setattr(popup_layer, "visible", False) or page.update())], alignment="spaceBetween")
        ], spacing=6, tight=True), bgcolor="white", padding=12, border_radius=12, width=300
    )

    # 상단 내비게이션 바 (이전달 / 다음달 이동) 버튼 컴포넌트
    header_nav = ft.Row([ft.TextButton("◀ 이전", on_click=lambda e: move_prev(e), style=ft.ButtonStyle(color="black")), month_title, ft.TextButton("다음 ▶", on_click=lambda e: move_next(e), style=ft.ButtonStyle(color="black"))], alignment="spaceBetween")
    topbar_title = ft.Text("", size=17, weight="bold", color="black")
    topbar_back_row = ft.Row([
        ft.TextButton(content=ft.Text("🏠 달력으로 가기", size=14, weight="bold", color="#2563EB"), on_click=lambda e: page.go("/")),
        topbar_title,
    ], alignment="start", spacing=14, visible=False)
    # 하단 '달력으로 가기' 버튼은 제거됨 (상단 버튼으로 통일)
    mangeun_setting_row = ft.Row([mangeun_value_text, ft.ElevatedButton("변경", on_click=lambda e: setattr(mangeun_popup_layer, "visible", True) or page.update(), bgcolor="#2563EB", color="white", width=68, height=22, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), text_style=ft.TextStyle(size=11, weight="bold"), padding=0))], alignment="start", vertical_alignment="center", spacing=6, height=22)
    
    mangeun_popup_layer.content = ft.Container(content=ft.Column([ft.Text("만근 기준 변경", size=16, weight="bold", color="black"), ft.Row([ft.Text("만근:", size=13, weight="bold", color="black"), mangeun_dropdown], alignment="center", spacing=10), ft.Row([ft.TextButton("취소", on_click=lambda e: setattr(mangeun_popup_layer, "visible", False) or page.update()), ft.TextButton("저장", on_click=on_mangeun_dropdown_changed, style=ft.ButtonStyle(color="#2563EB"))], alignment="spaceBetween")], spacing=10, tight=True), bgcolor="white", padding=14, border_radius=12, width=240)

    def move_prev(e):
        current["month"] -= 1
        if current["month"] == 0: current["month"] = 12; current["year"] -= 1
        rebuild_interface()

    def move_next(e):
        current["month"] += 1
        if current["month"] == 13: current["month"] = 1; current["year"] += 1
        rebuild_interface()

    summary_area = ft.Row([ft.Column([stats_text, mangeun_text, mangeun_setting_row], spacing=6, tight=True)], alignment="start")

    # 🗑️ 리셋 관련: 확인 팝업 + 실제 초기화 로직
    reset_confirm_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)

    def close_reset_popup(e):
        reset_confirm_popup_layer.visible = False
        page.update()

    def do_reset(e):
        USER_SCHEDULES.clear()
        pattern_state["name"], pattern_state["anchor_date"], pattern_state["anchor_index"] = None, None, 0
        save_all_to_client_storage()
        reset_confirm_popup_layer.visible = False
        rebuild_interface()

    reset_confirm_popup_layer.content = ft.Container(
        content=ft.Column([
            ft.Text("⚠️ 근무 기록 초기화", size=16, weight="bold", color="#D93025"),
            ft.Text("입력하신 모든 날짜의 근무 기록과 반복 근무 패턴이 삭제됩니다.\n이 작업은 되돌릴 수 없습니다. 정말 초기화하시겠습니까?", size=13, color="black"),
            ft.Row([
                ft.ElevatedButton(content=ft.Container(ft.Text("초기화", size=14, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="#D93025", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=do_reset),
                ft.ElevatedButton(content=ft.Container(ft.Text("취소", size=14, weight="bold", color="white"), alignment=ft.alignment.center), bgcolor="grey", expand=1, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=close_reset_popup),
            ], spacing=8),
        ], spacing=12, tight=True),
        bgcolor="white", padding=16, border_radius=12, width=280,
    )

    def open_reset_popup(e):
        reset_confirm_popup_layer.visible = True
        page.update()

    guide_text = ft.Row([
        ft.Container(content=ft.Text("💡 날짜를 터치하여 근무를 입력 또는 수정하세요.", size=10, color="#666666"), padding=ft.padding.only(left=8, bottom=4), expand=1),
        ft.TextButton(content=ft.Text("🗑️ 리셋", size=11, weight="bold", color="#D93025"), on_click=open_reset_popup),
    ], alignment="spaceBetween")
   
    # 긴급연락처 신규 등록 폼 컴포넌트
    emergency_form_container = ft.Container(content=ft.Column([ft.Row([ft.Text("🚨 긴급연락처", size=16, weight="bold", color="#1E3A8A")]), ft.Divider(height=1), ft.Row([em_name := ft.TextField(cursor_width=1, label="이름/서비스명", label_style=ft.TextStyle(size=11), width=100, height=38, text_size=13, content_padding=8), em_phone := ft.TextField(cursor_width=1, label="전화번호(숫자만)", label_style=ft.TextStyle(size=11), expand=True, height=38, text_size=13, content_padding=8, keyboard_type=ft.KeyboardType.PHONE), ft.ElevatedButton(content=ft.Text("등록", size=12, weight="bold", color="white"), bgcolor="#2563EB", width=60, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e: add_emergency_item())], spacing=4), ft.Divider(height=1, color="#E2E8F0")]))

    # 화면 스크롤 가능 구역 및 전체 인터페이스 초기 패치 주입 구역
    scrollable_content = ft.Column([topbar_back_row, header_nav, summary_area, guide_text, calendar_table, input_zone_container, setting_column, phonebook_zone_container, settings_zone_container], expand=True, scroll=ft.ScrollMode.AUTO)
    page.add(ft.Stack([ft.Column([scrollable_content, ft.Divider(height=1), ft.Row([btn_status, btn_setting, btn_config], alignment="spaceAround", spacing=4)], expand=True), popup_layer, mangeun_popup_layer, pattern_popup_layer, reset_confirm_popup_layer, status_picker_popup_layer], expand=True))
    
    page.on_resize = lambda e: rebuild_interface()
    change_tab("달력"); rebuild_interface()

ft.app(target=main, port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)
