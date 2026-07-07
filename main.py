# ==========================================
# [앱 이름: 버스헬퍼 스케줄러]
# 현재 배포 버전: 빌드 0005 (주석 및 이모지 완벽 복구본)
# ==========================================

import os
import sqlite3
import calendar
from datetime import datetime, timedelta, timezone
import flet as ft
import json

# 한국 표준시(KST) 및 데이터베이스/저장소 키 설정
KST = timezone(timedelta(hours=9))
DB_FILE = "schedules.db"
STORAGE_SCHEDULES_KEY = "bus_helper_schedules"
STORAGE_MANGEUN_KEY = "bus_helper_mangeun_targets"
STORAGE_INPUT_DATA_KEY = "bus_helper_input_data"
STORAGE_PHONEBOOK_KEY = "bus_helper_phonebook"
STORAGE_EMERGENCY_KEY = "bus_helper_emergency" 

# 구버전 호환용 SQLite 초기화 (현재는 클라이언트 스토리지를 주력으로 사용)
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS schedules (date_key TEXT PRIMARY KEY, status TEXT, start_time TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS mangeun_targets (month_key TEXT PRIMARY KEY, target INTEGER)")
    conn.commit()
    conn.close()

def main(page: ft.Page):
    page.title = "버스기사도우미"
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
    
    calendar_grid = ft.Column(spacing=2)
    input_zone_container = ft.Column(spacing=2, visible=False)
    
    phonebook_items_column = ft.Column(spacing=6)
    
    # [화면 구역] 📞 전화번호부 관리 페이지 레이아웃
    phonebook_zone_container = ft.Container(
        content=ft.Column([
            ft.Row([ft.Text("📞 전화번호부관리", size=16, weight="bold", color="#1E3A8A")]),
            ft.Divider(height=1),
            ft.Row([
                pb_name := ft.TextField(label="이름/직책", label_style=ft.TextStyle(size=11), width=100, height=38, text_size=13, content_padding=8),
                pb_phone := ft.TextField(label="전화번호(숫자만)", label_style=ft.TextStyle(size=11), expand=True, height=38, text_size=13, content_padding=8, keyboard_type=ft.KeyboardType.PHONE),
                ft.ElevatedButton(content=ft.Text("추가", size=12, weight="bold", color="white"), bgcolor="#2563EB", width=60, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e: add_phonebook_item())
            ], spacing=4),
            ft.Divider(height=1, color="#E2E8F0"),
            phonebook_items_column
        ]),
        padding=12, border=ft.border.all(1, "#2563EB"), border_radius=10, visible=False
    )
    
    # [버튼] 달력 화면 우측 상단에 배치되는 거대한 '📞 전화번호부' 바로가기 버튼 (복구 완료!)
    phonebook_big_button = ft.ElevatedButton(
        content=ft.Container(ft.Text("📞 전화번호부", color="white", size=20, weight="bold"), alignment=ft.alignment.center), 
        width=150, height=70, bgcolor="#2563EB", color="white", 
        on_click=lambda e: change_tab("전화번호"),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=ft.padding.all(0))
    )

    # [하단 탭 메뉴 버튼] 기사님 디자인 피드백 반영 (텍스트 이모지 장착 및 한여름의 패딩 제거 버전)
    btn_calendar = ft.ElevatedButton(content=ft.Container(content=ft.Text("📅 달력", color="white", size=11, weight="bold"), alignment=ft.alignment.center), expand=1, height=40, style=ft.ButtonStyle(bgcolor="#2563EB", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: change_tab("달력"))
    btn_input = ft.ElevatedButton(content=ft.Container(content=ft.Text("🚌 운행정보", color="white", size=11, weight="bold"), alignment=ft.alignment.center), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: change_tab("운행정보"))
    btn_setting = ft.ElevatedButton(content=ft.Container(content=ft.Text("🚨 긴급연락처", color="white", size=11, weight="bold"), alignment=ft.alignment.center), expand=1, height=40, style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=0), on_click=lambda e: change_tab("긴급연락처"))

    # 달력 최상단 요일 표시줄 (일~토)
    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row([ft.Container(content=ft.Text(d, size=13, weight="bold", color="#D93025" if d=="일" else ("#1A73E8" if d=="토" else "black")), expand=1, alignment=ft.Alignment(0, 0)) for d in days_letters], alignment="spaceAround")

    div_line1 = ft.Divider(height=1)
    div_line2 = ft.Divider(height=1)

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
                    edit_name = ft.TextField(value=name, width=90, height=34, text_size=13, content_padding=6)
                    edit_phone = ft.TextField(value=phone.replace("-",""), expand=True, height=34, text_size=13, content_padding=6, keyboard_type=ft.KeyboardType.PHONE)
                    
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
                    edit_em_name = ft.TextField(value=name, width=90, height=34, text_size=13, content_padding=6)
                    edit_em_phone = ft.TextField(value=phone.replace("-",""), expand=True, height=34, text_size=13, content_padding=6, keyboard_type=ft.KeyboardType.PHONE)
                    
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

    # 🔄 [메인 함수] 하단 메뉴 탭 전환 마스터 제어 함수 (여백 패딩 제로 깔끔 동기화 버전)
    def change_tab(tab_name):
        nonlocal current_tab
        current_tab = tab_name
        
        btn_calendar.style = ft.ButtonStyle(color="white" if tab_name == "달력" else "#94A3B8", bgcolor="#2563EB" if tab_name == "달력" else "transparent", shape=ft.RoundedRectangleBorder(radius=6), padding=0)
        btn_input.style = ft.ButtonStyle(color="white" if tab_name == "운행정보" else "#94A3B8", bgcolor="#2563EB" if tab_name == "운행정보" else "transparent", shape=ft.RoundedRectangleBorder(radius=6), padding=0)
        btn_setting.style = ft.ButtonStyle(color="white" if tab_name == "긴급연락처" else "#94A3B8", bgcolor="#2563EB" if tab_name == "긴급연락처" else "transparent", shape=ft.RoundedRectangleBorder(radius=6), padding=0)

        btn_calendar.update()
        btn_input.update()
        btn_setting.update()
        
        if tab_name == "달력":
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, weeks_header.visible, div_line1.visible, div_line2.visible = True, True, True, True, False, False, False, True, True, True
        elif tab_name == "운행정보":
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, weeks_header.visible, div_line1.visible, div_line2.visible = True, False, False, False, True, False, False, False, False, False
            refresh_input_tab_view()
        elif tab_name == "전화번호":
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, weeks_header.visible, div_line1.visible, div_line2.visible = True, False, False, False, False, True, False, False, False, False
            PHONEBOOK_LIST.sort(key=lambda x: x.get("name", ""))
            rebuild_phonebook_view()
        elif tab_name == "긴급연락처":
            header_nav.visible, summary_area.visible, guide_text.visible, calendar_grid.visible, input_zone_container.visible, phonebook_zone_container.visible, setting_column.visible, weeks_header.visible, div_line1.visible, div_line2.visible = True, False, False, False, False, False, True, False, False, False
            rebuild_emergency_view(setting_column)
        page.update()

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
    hour_picker = ft.CupertinoPicker(controls=[ft.Text(f"{i:02d}", size=20) for i in range(24)], selected_index=5, on_change=lambda e: update_hour(int(e.control.selected_index)), height=100, expand=1, looping=True)
    minute_picker = ft.CupertinoPicker(controls=[ft.Text(f"{i:02d}", size=20) for i in range(60)], selected_index=0, on_change=lambda e: update_minute(int(e.control.selected_index)), height=100, expand=1, looping=True)

    def update_hour(val): selected_time_state["hour"] = val
    def update_minute(val): selected_time_state["minute"] = val

    dial_row = ft.Row([hour_picker, ft.Text(":", size=20, weight="bold", color="black"), minute_picker], alignment="center", height=100)
    popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    mangeun_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)

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
    def open_info_input_popup(target_type):
        if target_type == "내차":
            tf_route, tf_bus_no = ft.TextField(label="노선번호", value=input_data_state["route"].replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38), ft.TextField(label="내차번호", value=input_data_state["bus_no"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38)
            def save_my(e):
                input_data_state["route"], input_data_state["bus_no"] = tf_route.value if tf_route.value else "미입력", f"{tf_bus_no.value}호" if tf_bus_no.value else "미입력"
                save_all_to_client_storage(); info_dialog.open = False; page.update(); rebuild_interface()
            box_content = ft.Container(content=ft.Column([ft.Text("👤 내 차량 설정", size=14, weight="bold"), ft.Row([tf_route, tf_bus_no]), ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=save_my, expand=1, height=38, bgcolor="#2563EB"), ft.ElevatedButton(content=ft.Container(ft.Text("뒤로가기", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=lambda e: setattr(info_dialog, "open", False) or page.update(), expand=1, height=38, bgcolor="grey")], alignment="center", spacing=8)], spacing=10, tight=True), width=260, padding=4)
        elif target_type == "앞차":
            tf_f_bus, tf_f_driver, tf_f_phone = ft.TextField(label="앞차번호", value=input_data_state["front_bus"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38), ft.TextField(label="기사성함", value=input_data_state["front_driver"].replace("미입력",""), expand=True, height=38), ft.TextField(label="전화번호(숫자만)", value=input_data_state["front_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, expand=True, height=38)
            def save_front(e):
                input_data_state["front_bus"], input_data_state["front_driver"], input_data_state["front_phone"] = f"{tf_f_bus.value}호" if tf_f_bus.value else "미입력", tf_f_driver.value if tf_f_driver.value else "미입력", final_format_phone(tf_f_phone.value) if tf_f_phone.value else "미입력"
                save_all_to_client_storage(); info_dialog.open = False; page.update(); rebuild_interface()
            box_content = ft.Container(content=ft.Column([ft.Text("◀ 앞차 정보 입력", size=14, weight="bold"), tf_f_bus, tf_f_driver, tf_f_phone, ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=save_front, expand=1, height=38, bgcolor="#1E3A8A"), ft.ElevatedButton(content=ft.Container(ft.Text("뒤로가기", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=lambda e: setattr(info_dialog, "open", False) or page.update(), expand=1, height=38, bgcolor="grey")], alignment="center", spacing=8)], spacing=10, tight=True), width=260, padding=4)
        elif target_type == "뒷차":
            tf_b_bus, tf_b_driver, tf_b_phone = ft.TextField(label="뒷차번호", value=input_data_state["back_bus"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38), ft.TextField(label="기사성함", value=input_data_state["back_driver"].replace("미입력",""), expand=True, height=38), ft.TextField(label="전화번호 (숫자만)", value=input_data_state["back_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, expand=True, height=38)
            def save_back(e):
                input_data_state["back_bus"], input_data_state["back_driver"], input_data_state["back_phone"] = f"{tf_b_bus.value}호" if tf_b_bus.value else "미입력", tf_b_driver.value if tf_b_driver.value else "미입력", final_format_phone(tf_b_phone.value) if tf_b_phone.value else "미입력"
                save_all_to_client_storage(); info_dialog.open = False; page.update(); rebuild_interface()
            box_content = ft.Container(content=ft.Column([ft.Text("▶ 뒷차 정보 입력", size=14, weight="bold"), tf_b_bus, tf_b_driver, tf_b_phone, ft.Row([ft.ElevatedButton(content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=save_back, expand=1, height=38, bgcolor="#1E3A8A"), ft.ElevatedButton(content=ft.Container(ft.Text("뒤로가기", size=13, weight="bold", color="white"), alignment=ft.alignment.center), on_click=lambda e: setattr(info_dialog, "open", False) or page.update(), expand=1, height=38, bgcolor="grey")], alignment="center", spacing=8)], spacing=10, tight=True), width=260, padding=4)
        info_dialog.content = box_content; info_dialog.open = True; page.update()

    info_dialog = ft.AlertDialog(modal=False, content=ft.Container()); page.dialog = info_dialog
    def refresh_input_tab_view(): input_zone_container.controls.clear(); input_zone_container.controls.append(build_driving_summary_zone()); page.update()

    # 📅 [캘린더 렌더러] 매달 달력 날짜 그리드 및 실시간 만근 카운트 일체 갱신 함수
    def rebuild_interface():
        nonlocal USER_SCHEDULES, MANGEUN_TARGETS
        today = datetime.now(KST)
        today_y, today_m, today_d = today.year, today.month, today.day
        month_title.value = f"{current['year']}년 {current['month']}월"
        month_prefix = f"{current['year']}-{current['month']:02d}"
        month_data = {k: v for k, v in USER_SCHEDULES.items() if k.startswith(month_prefix)}
        work_days, off_days = sum(1 for d in month_data.values() if d.get("status") in ["오전", "오후", "전일"]), sum(1 for d in month_data.values() if d.get("status") == "휴무")
        m_target = get_mangeun_target(); mangeun_dropdown.value = str(m_target)
        diff = work_days - m_target
        stats_text.value = f"근무: {work_days}(+{diff})" if diff > 0 else (f"근무: {work_days}({diff})" if diff < 0 else f"근무: {work_days}")
        mangeun_text.value, mangeun_value_text.value = f"휴무: {off_days}", f"만근: {m_target}"

        calendar_grid.controls.clear()
        cal = calendar.Calendar(firstweekday=6)
        for week in cal.monthdayscalendar(current['year'], current['month']):
            week_row = ft.Row(alignment="spaceAround", spacing=2)
            for day in week:
                if day == 0: week_row.controls.append(ft.Container(expand=1, height=52))
                else:
                    weekday = datetime(current['year'], current['month'], day).weekday()
                    date_key = f"{current['year']}-{current['month']:02d}-{day:02d}"
                    day_info = month_data.get(date_key, {"status": "", "start_time": "", "order_no": ""})
                    status, start_time, order_no = day_info.get("status", ""), day_info.get("start_time", ""), day_info.get("order_no", "")
                    bg_color, text_color, status_desc = "#FFFFFF", "#000000", ""
                    if status == "오전": bg_color, text_color, status_desc = "#D2E3FC", "#1A73E8", f"오전({order_no})" if order_no else "오전"
                    elif status == "오후": bg_color, text_color, status_desc = "#E9D5FF", "#7E22CE", f"오후({order_no})" if order_no else "오후"
                    elif status == "전일": bg_color, text_color, status_desc = "#E6F4EA", "#137333", f"전일({order_no})" if order_no else "전일"
                    elif status == "휴무": bg_color, text_color, status_desc = "#FCE8E6", "#D93025", "휴무"
                    day_number_color = "#D93025" if weekday == 6 else ("#1A73E8" if weekday == 5 else "#000000")
                    time_display = ft.Text(start_time, size=9, weight="bold", color=text_color) if start_time and status != "휴무" else ft.Container()
                    day_box = ft.Container(content=ft.Column([ft.Text(f"{day}", size=12, weight="bold", color=day_number_color), ft.Text(status_desc, size=10, weight="bold", color=text_color), time_display], alignment="center", horizontal_alignment="center", spacing=0), bgcolor=bg_color, border=ft.border.all(2, "#2563EB") if (current['year'] == today_y and current['month'] == today_m and day == today_d) else ft.border.all(0.5, "#E2E8F0"), border_radius=4, height=52, expand=1, on_click=lambda e, dk=date_key: open_input_popup(dk))
                    week_row.controls.append(day_box)
            calendar_grid.controls.append(week_row)
        if current_tab == "운행정보": refresh_input_tab_view()
        page.update()

    # 날짜 다이얼로그 호출 및 휠 스크롤 시간 초기화 매칭 함수
    def open_input_popup(date_key):
        current["selected_date"] = date_key
        popup_date_title.value = f"{date_key}\n첫탕 시간을 선택하세요"
        day_info = USER_SCHEDULES.get(date_key, {})
        current_time, current_order = day_info.get("start_time", ""), day_info.get("order_no", "")
        order_dropdown.value = str(current_order) if current_order else ""
        if current_time and ":" in current_time:
            h, m = map(int, current_time.split(":"))
            selected_time_state["hour"], selected_time_state["minute"] = h, m
            hour_picker.selected_index, minute_picker.selected_index = h, m
        else:
            selected_time_state["hour"], selected_time_state["minute"], hour_picker.selected_index, minute_picker.selected_index = 5, 0, 5, 0
        popup_layer.content, popup_layer.visible = popup_card, True; page.update()

    # 근무 선택 및 저장/삭제 공통 로직 처리 함수
    def select_status_and_save(status_value):
        target_date = current["selected_date"]
        if status_value == "선택취소":
            USER_SCHEDULES.pop(target_date, None); save_all_to_client_storage(); popup_layer.visible = False; rebuild_interface(); return
        final_time = ""
        if status_value == "자동":
            h, m = selected_time_state["hour"], selected_time_state["minute"]
            status_value = "전일" if USER_SCHEDULES.get(target_date, {}).get("status") == "전일" else ("오후" if h >= 12 else "오전")
            final_time = f"{h:02d}:{m:02d}"
        USER_SCHEDULES[target_date] = {"status": status_value, "start_time": final_time, "order_no": "" if status_value == "휴무" else (order_dropdown.value if order_dropdown.value else "")}
        save_all_to_client_storage(); popup_layer.visible = False; rebuild_interface()

    # 팝업 내부 스크롤뷰 레이아웃 구조체
    popup_card = ft.Container(
        content=ft.Column([
            ft.Row([popup_date_title], alignment="center"), ft.Divider(height=1, color="transparent"), ft.Text("시간 없이 근무만 등록할 때:", size=11, weight="bold", color="grey"),
            ft.Row([ft.Container(content=ft.Text("휴무", size=14, weight="bold", color="white"), bgcolor="#D93025", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("휴무")), ft.Container(content=ft.Text("오전", size=14, weight="bold", color="white"), bgcolor="#5C93E6", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("오전")), ft.Container(content=ft.Text("오후", size=14, weight="bold", color="white"), bgcolor="#7E22CE", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("오후")), ft.Container(content=ft.Text("전일", size=14, weight="bold", color="white"), bgcolor="#10B981", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("전일"))], spacing=4),
            dial_row, ft.Row([ft.Text("근무 순번:", size=12, weight="bold", color="black"), order_dropdown], alignment="center", spacing=10), ft.Divider(height=2),
            ft.Row([ft.Container(content=ft.Text("저장", size=14, weight="bold", color="white"), bgcolor="#2563EB", alignment=ft.Alignment(0, 0), width=160, height=38, border_radius=6, on_click=lambda e: select_status_and_save("자동"))], alignment="center"), ft.Divider(height=1, color="transparent"),
            ft.Row([ft.TextButton("선택취소(삭제)", on_click=lambda e: select_status_and_save("선택취소"), style=ft.ButtonStyle(color="red")), ft.TextButton("닫기", on_click=lambda e: setattr(popup_layer, "visible", False) or page.update())], alignment="spaceBetween")
        ], spacing=6, tight=True), bgcolor="white", padding=12, border_radius=12, width=300
    )

    # 상단 내비게이션 바 (이전달 / 다음달 이동) 버튼 컴포넌트
    header_nav = ft.Row([ft.TextButton("◀ 이전", on_click=lambda e: move_prev(e), style=ft.ButtonStyle(color="black")), month_title, ft.TextButton("다음 ▶", on_click=lambda e: move_next(e), style=ft.ButtonStyle(color="black"))], alignment="spaceBetween")
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

    summary_area = ft.Row([ft.Column([stats_text, mangeun_text, mangeun_setting_row], spacing=6, tight=True), phonebook_big_button], alignment="spaceBetween")
    guide_text = ft.Container(content=ft.Text("💡 날짜를 터치하여 근무를 입력 또는 수정하세요.", size=10, color="#666666"), padding=ft.padding.only(left=8, bottom=4))
   
    # 긴급연락처 신규 등록 폼 컴포넌트
    emergency_form_container = ft.Container(content=ft.Column([ft.Row([ft.Text("🚨 긴급 연락처 관리", size=16, weight="bold", color="#1E3A8A")]), ft.Divider(height=1), ft.Row([em_name := ft.TextField(label="이름/서비스명", label_style=ft.TextStyle(size=11), width=100, height=38, text_size=13, content_padding=8), em_phone := ft.TextField(label="전화번호(숫자만)", label_style=ft.TextStyle(size=11), expand=True, height=38, text_size=13, content_padding=8, keyboard_type=ft.KeyboardType.PHONE), ft.ElevatedButton(content=ft.Text("등록", size=12, weight="bold", color="white"), bgcolor="#2563EB", width=60, height=38, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0), on_click=lambda e: add_emergency_item())], spacing=4), ft.Divider(height=1, color="#E2E8F0")]))

    # 화면 스크롤 가능 구역 및 전체 인터페이스 초기 패치 주입 구역
    scrollable_content = ft.Column([header_nav, summary_area, guide_text, div_line1, weeks_header, div_line2, calendar_grid, input_zone_container, phonebook_zone_container, setting_column], expand=True, scroll=ft.ScrollMode.AUTO)
    page.add(ft.Stack([ft.Column([scrollable_content, ft.Divider(height=1), ft.Row([btn_calendar, btn_input, btn_setting], alignment="spaceAround", spacing=4)], expand=True), popup_layer, mangeun_popup_layer], expand=True))
    
    change_tab("달력"); rebuild_interface()

init_db()
ft.app(target=main, port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)
