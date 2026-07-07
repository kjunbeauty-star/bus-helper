import os
import sqlite3
import calendar
from datetime import datetime, timedelta, timezone
import flet as ft
import json

KST = timezone(timedelta(hours=9))
DB_FILE = "schedules.db"
STORAGE_SCHEDULES_KEY = "bus_helper_schedules"
STORAGE_MANGEUN_KEY = "bus_helper_mangeun_targets"
STORAGE_INPUT_DATA_KEY = "bus_helper_input_data"
# 💡 전화번호부 저장용 키 신설
STORAGE_PHONEBOOK_KEY = "bus_helper_phonebook"

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

    saved_schedules = page.client_storage.get(STORAGE_SCHEDULES_KEY)
    saved_targets = page.client_storage.get(STORAGE_MANGEUN_KEY)
    saved_input_data = page.client_storage.get(STORAGE_INPUT_DATA_KEY)
    # 💡 저장된 전화번호부 데이터 불러오기
    saved_phonebook = page.client_storage.get(STORAGE_PHONEBOOK_KEY)
    # 🌟 [빌드 0002 추가] 저장된 긴급 연락처 데이터 불러오기
    saved_emergency = page.client_storage.get(STORAGE_EMERGENCY_KEY)
    if saved_emergency:
        EMERGENCY_LIST = json.loads(saved_emergency)

    USER_SCHEDULES = json.loads(saved_schedules) if saved_schedules else {}
    MANGEUN_TARGETS = json.loads(saved_targets) if saved_targets else {}
    PHONEBOOK_LIST = json.loads(saved_phonebook) if saved_phonebook else []
    # 🌟 [빌드 0002 추가] 긴급 연락처 리스트 (사무실, 정비실은 고정 값으로 기본 세팅)
    EMERGENCY_LIST = [
    {"name": "사무실", "phone": "", "is_fixed": True},
    {"name": "정비실", "phone": "", "is_fixed": True}
    ]
    STORAGE_EMERGENCY_KEY = "bus_helper_emergency" # 저장용 키 신설
    
    if saved_input_data:
        input_data_state = json.loads(saved_input_data)
    else:
        input_data_state = {
            "route": "미입력",
            "bus_no": "미입력",
            "front_bus": "미입력", "front_driver": "미입력", "front_phone": "미입력",
            "back_bus": "미입력", "back_driver": "미입력", "back_phone": "미입력"
        }

    def save_all_to_client_storage():
        page.client_storage.set(STORAGE_SCHEDULES_KEY, json.dumps(USER_SCHEDULES, ensure_ascii=False))
        page.client_storage.set(STORAGE_MANGEUN_KEY, json.dumps(MANGEUN_TARGETS, ensure_ascii=False))
        page.client_storage.set(STORAGE_INPUT_DATA_KEY, json.dumps(input_data_state, ensure_ascii=False))
        # 💡 전화번호부도 함께 스토리지에 저장
        page.client_storage.set(STORAGE_PHONEBOOK_KEY, json.dumps(PHONEBOOK_LIST, ensure_ascii=False))
        # 🌟 [빌드 0002 추가] 긴급 연락처도 함께 저장
        page.client_storage.set(STORAGE_EMERGENCY_KEY, json.dumps(EMERGENCY_LIST))

    now_kst = datetime.now(KST)
    current = {"year": now_kst.year, "month": now_kst.month, "selected_date": "2026-07-05"}
    selected_time_state = {"hour": 5, "minute": 0}

    current_tab = "달력"

    month_title = ft.Text("", size=20, weight="bold", text_align="center")
    stats_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_value_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    
    calendar_grid = ft.Column(spacing=2)
    input_zone_container = ft.Column(spacing=2, visible=False)
    
    # 💡 전화번호부 리스트가 담길 내부 컴포넌트 선언
    phonebook_items_column = ft.Column(spacing=6)
    
    # 💡 전화번호부 탭 UI 전면 개편
    phonebook_zone_container = ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📞 전화번호부관리", size=16, weight="bold", color="#1E3A8A"),
                ], alignment="spaceBetween"),
                ft.Divider(height=1),
                
                # 연락처 입력창 폼
                ft.Row([
                    pb_name := ft.TextField(label="이름/직책", label_style=ft.TextStyle(size=11), width=100, height=38, text_size=13, content_padding=8), # 💡 label_style 추가
                    pb_phone := ft.TextField(label="전화번호(숫자만)", label_style=ft.TextStyle(size=11), expand=True, height=38, text_size=13, content_padding=8, keyboard_type=ft.KeyboardType.PHONE), # 💡 label_style 추가

                    ft.ElevatedButton(
                        content=ft.Text("추가", size=12, weight="bold", color="white"),
                        bgcolor="#2563EB", width=60, height=38,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0),
                        on_click=lambda e: add_phonebook_item()
                    )
                ], spacing=4),
                ft.Divider(height=1, color="#E2E8F0"),
                
                # 연락처가 출력되는 리스트 공간
                phonebook_items_column
            ]),
            padding=12, border=ft.border.all(1, "#2563EB"), border_radius=10
        )
    ], spacing=2, visible=False)
    
    # 상단 전화번호부 큰 버튼 (글자 크기 20, 완벽한 직사각형 스타일 유지)
    phonebook_big_button = ft.ElevatedButton(
        content=ft.Container(ft.Text("전화번호부", color="white", size=20, weight="bold"), alignment=ft.alignment.center), 
        width=150, height=70, bgcolor="#2563EB", color="white", 
        on_click=lambda e: change_tab("전화번호"),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.all(0)
        )
    )

    btn_calendar = ft.ElevatedButton(
        content=ft.Container(ft.Text("달력", color="white", size=11, weight="bold"), alignment=ft.alignment.center),
        expand=1, height=40, 
        style=ft.ButtonStyle(bgcolor="#2563EB", shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(vertical=0, horizontal=0)), 
        on_click=lambda e: change_tab("달력")
    )
    btn_input = ft.ElevatedButton(
        content=ft.Container(ft.Text("운행정보", color="white", size=11, weight="bold"), alignment=ft.alignment.center),
        expand=1, height=40, 
        style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(vertical=0, horizontal=0)), 
        on_click=lambda e: change_tab("운행정보")
    )
    btn_setting = ft.ElevatedButton(
        content=ft.Container(ft.Text("긴급연락처", color="white", size=11, weight="bold"), alignment=ft.alignment.center),
        expand=1, height=40, 
        style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(vertical=0, horizontal=0)), 
        on_click=lambda e: change_tab("긴급연락처")
    )

    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row([ft.Container(content=ft.Text(d, size=13, weight="bold", color="#D93025" if d=="일" else ("#1A73E8" if d=="토" else "black")), expand=1, alignment=ft.Alignment(0, 0)) for d in days_letters], alignment="spaceAround")

    div_line1 = ft.Divider(height=1)
    div_line2 = ft.Divider(height=1)

    # 💡 [주석 자리] 전화번호부 리스트를 화면에 새롭게 그려주는 기능 (한글 수정/삭제 버튼 적용)
    def rebuild_phonebook_view():
        phonebook_items_column.controls.clear()
        if not PHONEBOOK_LIST:
            phonebook_items_column.controls.append(
                ft.Container(
                    content=ft.Text("등록된 연락처가 없습니다.\n자주 쓰는 번호를 상단에 등록해 보세요!", size=13, color="grey", text_align="center"),
                    padding=20, alignment=ft.alignment.center
                )
            )
        else:
            for index, item in enumerate(PHONEBOOK_LIST):
                name = item.get("name", "")
                phone = item.get("phone", "")
                is_edit = item.get("is_edit", False) # 현재 수정 중인 상태인지 확인하는 값
                
                if is_edit:
                    # ✏️ [수정 모드] 입력창 및 [저장] / [취소] 한글 버튼
                    edit_name = ft.TextField(value=name, width=90, height=34, text_size=13, content_padding=6)
                    edit_phone = ft.TextField(value=phone.replace("-",""), expand=True, height=34, text_size=13, content_padding=6, keyboard_type=ft.KeyboardType.PHONE)
                    
                    def save_edit(idx, en, ep):
                        if en.value and ep.value:
                            PHONEBOOK_LIST[idx] = {"name": en.value, "phone": final_format_phone(ep.value), "is_edit": False}
                            
                            # 🌟 [여기에 추가] 이름(name)을 기준으로 가나다순 정렬
                            PHONEBOOK_LIST.sort(key=lambda x: x.get("name", ""))
                            
                            save_all_to_client_storage()
                            rebuild_phonebook_view()

                    row_content = ft.Row([
                        edit_name,
                        edit_phone,
                        ft.ElevatedButton(
                            content=ft.Container(ft.Text("저장", size=11, weight="bold", color="white"), alignment=ft.alignment.center),
                            bgcolor="green", width=50, height=34,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0),
                            on_click=lambda e, idx=index, en=edit_name, ep=edit_phone: save_edit(idx, en, ep)
                        ),
                        ft.ElevatedButton(
                            content=ft.Container(ft.Text("취소", size=11, weight="bold", color="white"), alignment=ft.alignment.center),
                            bgcolor="grey", width=50, height=34,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0),
                            on_click=lambda e, idx=index: toggle_edit_mode(idx, False)
                        )
                    ], spacing=4)
                else:
                    # 📱 [일반 모드] 연락처 정보 및 [수정] / [삭제] 한글 파란색 버튼
                    row_content = ft.Row([
                        ft.GestureDetector(
                            content=ft.Row([
                                ft.Text(f"{name}", size=14, weight="bold", color="black", width=70), # 너비를 70으로 확보
                                ft.Text(f"{phone}", size=13, weight="bold", color="#1E3A8A", expand=True), # expand=True로 남은 공간 다 쓰기, 글자 13으로 조절
                                ft.Text("☎️", size=12, color="red")
                            ], spacing=4, alignment="start"),
                            on_tap=lambda e, p=phone: make_call(p),
                            expand=True
                        ),
                        ft.Row([
                            ft.ElevatedButton(
                                content=ft.Container(ft.Text("수정", size=11, weight="bold", color="white"), alignment=ft.alignment.center),
                                bgcolor="#2563EB", width=46, height=30, # 버튼 크기를 더 콤팩트하게 조절
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0),
                                on_click=lambda e, idx=index: toggle_edit_mode(idx, True)
                            ),
                            ft.ElevatedButton(
                                content=ft.Container(ft.Text("삭제", size=11, weight="bold", color="white"), alignment=ft.alignment.center),
                                bgcolor="#1E3A8A", width=46, height=30, # 버튼 크기를 더 콤팩트하게 조절
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0),
                                on_click=lambda e, idx=index: delete_phonebook_item(idx)
                            )
                        ], spacing=3)
                    ], alignment="spaceBetween")

                    # 📱 [일반 모드] 연락처 정보 및 [수정] / [삭제] 슬림 한글 버튼
                    row_content = ft.Row([
                        ft.GestureDetector(
                            content=ft.Row([
                                ft.Text(f"{name}", size=14, weight="bold", color="black", width=65), 
                                ft.Text(f"{phone}", size=13, weight="bold", color="#1E3A8A", no_wrap=True), 
                                ft.Text("☎️", size=11, color="red")
                            ], spacing=4, alignment="start"),
                            on_tap=lambda e, p=phone: make_call(p),
                            expand=True
                        ),
                        ft.Row([
                            ft.ElevatedButton(
                                content=ft.Container(ft.Text("수정", size=10, weight="bold", color="white"), alignment=ft.alignment.center),
                                bgcolor="#2563EB", width=40, height=28, # 💡 가로 40, 높이 28로 더 슬림하게 조절
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0),
                                on_click=lambda e, idx=index: toggle_edit_mode(idx, True)
                            ),
                            ft.ElevatedButton(
                                content=ft.Container(ft.Text("삭제", size=10, weight="bold", color="white"), alignment=ft.alignment.center),
                                bgcolor="#1E3A8A", width=40, height=28, # 💡 가로 40, 높이 28로 더 슬림하게 조절
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0),
                                on_click=lambda e, idx=index: delete_phonebook_item(idx)
                            )
                        ], spacing=3)
                    ], alignment="spaceBetween")

                # 💡 이 부분이 박스를 없애고 아래쪽 라인(밑줄)으로 넒게 정의하는 핵심 코드입니다!
                phonebook_items_column.controls.append(
                    ft.Container(
                        content=row_content,
                        padding=ft.padding.only(left=4, right=4, top=8, bottom=8), # 좌우 여백을 줄여 가로를 넓게 씀
                        border=ft.border.Border(bottom=ft.border.BorderSide(0.5, "#E2E8F0")) # 💡 사방 박스 대신 하단 밑줄만 적용!
                    )
                )

        page.update()

    # 🌟 [교정] 함수 괄호 안에 target_column을 넣어서 안전하게 상자를 전달받습니다.
    def rebuild_emergency_view(target_column):
        # 이제 외부에서 넘겨받은 상자를 깨끗이 비웁니다. 노란 줄이 사라집니다!
        target_column.controls.clear()
        
        for index, item in enumerate(EMERGENCY_LIST):
            is_fixed = item.get("is_fixed", False)
            
            display_text = f"{item['name']}: {item['phone']}" if item['phone'] else f"{item['name']}: (번호 없음)"
            
            action_buttons = [
                ft.IconButton(
                    icon=ft.icons.PHONE,
                    icon_color="green",
                    on_click=lambda e, ph=item["phone"]: page.launch_url(f"tel:{ph}") if ph else None
                )
            ]
            
            if not is_fixed:
                action_buttons.append(
                    ft.ElevatedButton(
                        content=ft.Container(ft.Text("삭제", size=10, weight="bold", color="white"), alignment=ft.alignment.center),
                        bgcolor="#1E3A8A", width=40, height=28,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0),
                        on_click=lambda e, idx=index: delete_emergency_item(idx, target_column) # 삭제할 때도 상자 전달
                    )
                )
            
            row_content = ft.Row([
                ft.Text(display_text, size=14, weight="bold" if is_fixed else "normal", color="black"),
                ft.Row(action_buttons, spacing=3)
            ], alignment="spaceBetween")
            
            # 전달받은 상자에 차곡차곡 추가
            target_column.controls.append(
                ft.Container(
                    content=row_content,
                    padding=ft.padding.only(left=4, right=4, top=8, bottom=8),
                    border=ft.border.Border(bottom=ft.border.BorderSide(0.5, "#E2E8F0"))
                )
            )
            
        page.update()

    # 🌟 [교정] 삭제 함수도 상자를 같이 넘겨받도록 수정
    def delete_emergency_item(index, target_column):
        EMERGENCY_LIST.pop(index)
        save_all_to_client_storage()
        rebuild_emergency_view(target_column) # 삭제 후 새로고침할 때 상자 전달

    # 💡 전화번호 추가 로직
    def add_phonebook_item():
        tf_name = pb_name
        tf_phone = pb_phone
        
        if tf_name.value and tf_phone.value:
            formatted_num = final_format_phone(tf_phone.value)
            PHONEBOOK_LIST.append({"name": tf_name.value, "phone": formatted_num})
            
            # 🌟 [여기에 추가] 이름(name)을 기준으로 가나다순 정렬
            PHONEBOOK_LIST.sort(key=lambda x: x.get("name", ""))
            
            save_all_to_client_storage()
            tf_name.value = ""
            tf_phone.value = ""
            rebuild_phonebook_view()

    # 💡 전화번호 삭제 로직
    def delete_phonebook_item(index):
        if 0 <= index < len(PHONEBOOK_LIST):
            PHONEBOOK_LIST.pop(index)
            save_all_to_client_storage()
            rebuild_phonebook_view()
    # 💡 전화번호 수정 모드 전환 함수
    def toggle_edit_mode(index, status):
        if 0 <= index < len(PHONEBOOK_LIST):
            PHONEBOOK_LIST[index]["is_edit"] = status
            rebuild_phonebook_view()

    def change_tab(tab_name):
        nonlocal current_tab
        current_tab = tab_name
        
        # 💡 배경색과 글자색은 그대로 부드럽게 제어합니다.
        btn_calendar.style = ft.ButtonStyle(
            color="white" if tab_name == "달력" else "#94A3B8",
            bgcolor="#2563EB" if tab_name == "달력" else "transparent", # 활성화될 때만 배경색을 은은하게 주거나 투명하게 제어
            shape=ft.RoundedRectangleBorder(radius=6)
        )
        btn_input.style = ft.ButtonStyle(
            color="white" if tab_name == "운행정보" else "#94A3B8",
            bgcolor="#2563EB" if tab_name == "운행정보" else "transparent",
            shape=ft.RoundedRectangleBorder(radius=6)
        )
        btn_setting.style = ft.ButtonStyle(
            color="white" if tab_name == "긴급연락처" else "#94A3B8",
            bgcolor="#2563EB" if tab_name == "긴급연락처" else "transparent",
            shape=ft.RoundedRectangleBorder(radius=6)
        )

        # 📱 [추가] 기사님이 원하셨던 전화번호부 타이틀/버튼 색상 제어! 
        # 전화번호부 탭("전화번호")이 열렸을 때만 파란색, 달력이나 운행정보일 때는 그레이로 자동 전환됩니다.
        # (※ 만약 전화번호부 버튼 변수명이 다르면 그 이름으로 바꿔주세요)
        # phonebook_title.color = "#2563EB" if tab_name == "전화번호" else "grey"

        btn_calendar.update()
        btn_input.update()
        btn_setting.update()
        
        if tab_name == "달력":
            calendar_grid.visible = True
            input_zone_container.visible = False
            phonebook_zone_container.visible = False
            weeks_header.visible = True
            div_line1.visible = True
            div_line2.visible = True
        elif tab_name == "운행정보":
            calendar_grid.visible = False
            input_zone_container.visible = True
            phonebook_zone_container.visible = False
            weeks_header.visible = False
            div_line1.visible = False
            div_line2.visible = False
            refresh_input_tab_view()
        elif tab_name == "전화번호":
            calendar_grid.visible = False
            input_zone_container.visible = False
            phonebook_zone_container.visible = True
            weeks_header.visible = False
            div_line1.visible = False
            div_line2.visible = False
            # 💡 기존 전화번호부 데이터도 탭을 열 때 가나다순으로 자동 정렬
            PHONEBOOK_LIST.sort(key=lambda x: x.get("name", ""))
            rebuild_phonebook_view() # 전화번호부 탭 열릴 때 새로고침
        elif tab_name == "긴급연락처":
            calendar_grid.visible = False
            input_zone_container.visible = False
            phonebook_zone_container.visible = False
            weeks_header.visible = False
            div_line1.visible = False
            div_line2.visible = False

        page.update()

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
        except (ValueError, TypeError):
            pass

    mangeun_dropdown = ft.Dropdown(options=[ft.dropdown.Option(str(i)) for i in range(15, 27)], width=62, height=36, text_size=12, content_padding=ft.padding.symmetric(vertical=4, horizontal=8))

    hour_picker = ft.CupertinoPicker(controls=[ft.Text(f"{i:02d}", size=20) for i in range(24)], selected_index=5, on_change=lambda e: update_hour(int(e.control.selected_index)), height=100, expand=1, looping=True)
    minute_picker = ft.CupertinoPicker(controls=[ft.Text(f"{i:02d}", size=20) for i in range(60)], selected_index=0, on_change=lambda e: update_minute(int(e.control.selected_index)), height=100, expand=1, looping=True)

    def update_hour(val): selected_time_state["hour"] = val
    def update_minute(val): selected_time_state["minute"] = val

    dial_row = ft.Row([hour_picker, ft.Text(":", size=20, weight="bold", color="black"), minute_picker], alignment="center", height=100)
    
    popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)
    mangeun_popup_layer = ft.Container(visible=False, bgcolor="#AA000000", alignment=ft.Alignment(0, 0), expand=True)

    def get_mangeun_target():
        try:
            y, m = int(current['year']), int(current['month'])
            key = f"{y}_{m}"
            if key in MANGEUN_TARGETS: return int(MANGEUN_TARGETS[key])
            days_in_month = calendar.monthrange(y, m)[1]
            return 22 if days_in_month == 31 else (20 if m == 2 else 21)
        except: return 22

    def make_call(phone_number):
        if phone_number and phone_number != "미입력":
            page.launch_url(f"tel:{phone_number}")

    def build_driving_summary_zone():
        my_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("내차 정보", size=11, color="grey", weight="bold"),
                    ft.ElevatedButton(
                        content=ft.Container(ft.Text("입력", size=10, weight="bold", color="white"), alignment=ft.alignment.center),
                        on_click=lambda e: open_info_input_popup("내차"), bgcolor="#2563EB", width=55, height=22, 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=ft.padding.symmetric(vertical=0, horizontal=0))
                    )
                ], alignment="spaceBetween"),
                ft.Text(f"노선: {input_data_state['route']}", size=14, weight="bold", color="black"),
                ft.Text(f"내차: {input_data_state['bus_no']}", size=14, weight="bold", color="black"),
                ft.Container(height=15)
            ], spacing=2, tight=True),
            bgcolor="#F8FAFC", border=ft.border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1
        )

        front_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("앞차 정보", size=11, color="grey", weight="bold"),
                    ft.ElevatedButton(
                        content=ft.Container(ft.Text("입력", size=10, weight="bold", color="white"), alignment=ft.alignment.center),
                        on_click=lambda e: open_info_input_popup("앞차"), bgcolor="#1E3A8A", width=55, height=22, 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=ft.padding.symmetric(vertical=0, horizontal=0))
                    )
                ], alignment="spaceBetween"),
                ft.Text(input_data_state['front_bus'], size=14, weight="bold", color="black"),
                ft.Text(input_data_state['front_driver'], size=14, weight="bold", color="black"),
                ft.GestureDetector(
                    content=ft.Row([
                        ft.Text(input_data_state['front_phone'], size=13, color="#1E3A8A", weight="bold"),
                        ft.Text("☎️", size=13, color="red") if input_data_state['front_phone'] != "미입력" else ft.Container()
                    ], spacing=4, alignment="start"),
                    on_tap=lambda e: make_call(input_data_state['front_phone'])
                )
            ], spacing=2, tight=True),
            bgcolor="#F8FAFC", border=ft.border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1
        )

        back_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("뒷차 정보", size=11, color="grey", weight="bold"),
                    ft.ElevatedButton(
                        content=ft.Container(ft.Text("입력", size=10, weight="bold", color="white"), alignment=ft.alignment.center),
                        on_click=lambda e: open_info_input_popup("뒷차"), bgcolor="#1E3A8A", width=55, height=22, 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=ft.padding.symmetric(vertical=0, horizontal=0))
                    )
                ], alignment="spaceBetween"),
                ft.Text(input_data_state['back_bus'], size=14, weight="bold", color="black"),
                ft.Text(input_data_state['back_driver'], size=14, weight="bold", color="black"),
                ft.GestureDetector(
                    content=ft.Row([
                        ft.Text(input_data_state['back_phone'], size=13, color="#1E3A8A", weight="bold"),
                        ft.Text("☎️", size=13, color="red") if input_data_state['back_phone'] != "미입력" else ft.Container()
                    ], spacing=4, alignment="start"),
                    on_tap=lambda e: make_call(input_data_state['back_phone'])
                )
            ], spacing=2, tight=True),
            bgcolor="#F8FAFC", border=ft.border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("🚍 운행 정보 요약", size=14, weight="bold", color="#1E3A8A"),
                my_card, 
                ft.Row([front_card, back_card], spacing=8, alignment="spaceAround")
            ], spacing=8),
            padding=12, border=ft.border.all(1, "#2563EB"), border_radius=10, margin=ft.margin.only(bottom=10)
        )

    def final_format_phone(raw_value):
        clean = "".join(filter(str.isdigit, raw_value))
        if len(clean) <= 3:
            return clean
        elif len(clean) <= 7:
            return f"{clean[:3]}-{clean[3:]}"
        elif len(clean) <= 10:
            return f"{clean[:3]}-{clean[3:6]}-{clean[6:]}"
        else:
            return f"{clean[:3]}-{clean[3:7]}-{clean[7:11]}"

    def open_info_input_popup(target_type):
        if target_type == "내차":
            tf_route = ft.TextField(label="노선번호", value=input_data_state["route"].replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38)
            tf_bus_no = ft.TextField(label="내차번호", value=input_data_state["bus_no"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38)
            
            def save_my(e):
                input_data_state["route"] = tf_route.value if tf_route.value else "미입력"
                input_data_state["bus_no"] = f"{tf_bus_no.value}호" if tf_bus_no.value else "미입력"
                save_all_to_client_storage()
                info_dialog.open = False  
                page.update()
                rebuild_interface()

            box_content = ft.Container(
                content=ft.Column([
                    ft.Text("👤 내 차량 설정", size=14, weight="bold"),
                    ft.Row([tf_route, tf_bus_no]),
                    ft.Row([
                        ft.ElevatedButton(
                            content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white"), alignment=ft.alignment.center),
                            on_click=save_my, expand=1, height=38,
                            style=ft.ButtonStyle(bgcolor="#2563EB", shape=ft.RoundedRectangleBorder(radius=0), padding=ft.padding.symmetric(vertical=0, horizontal=0)),
                        ),
                        ft.ElevatedButton(
                            content=ft.Container(ft.Text("뒤로가기", size=13, weight="bold", color="white"), alignment=ft.alignment.center),
                            on_click=lambda e: setattr(info_dialog, "open", False) or page.update(), expand=1, height=38,
                            style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=0), padding=ft.padding.symmetric(vertical=0, horizontal=0)),
                        )
                    ], alignment="center", spacing=8)
                ], spacing=10, tight=True),
                width=260, padding=4
            )

        elif target_type == "앞차":
            tf_f_bus = ft.TextField(label="앞차번호", value=input_data_state["front_bus"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38)
            tf_f_driver = ft.TextField(label="기사성함", value=input_data_state["front_driver"].replace("미입력",""), expand=True, height=38)
            tf_f_phone = ft.TextField(label="전화번호(숫자만)", value=input_data_state["front_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, expand=True, height=38)
            
            def save_front(e):
                input_data_state["front_bus"] = f"{tf_f_bus.value}호" if tf_f_bus.value else "미입력"
                input_data_state["front_driver"] = tf_f_driver.value if tf_f_driver.value else "미입력"
                input_data_state["front_phone"] = final_format_phone(tf_f_phone.value) if tf_f_phone.value else "미입력"
                save_all_to_client_storage()
                info_dialog.open = False  
                page.update()
                rebuild_interface()

            box_content = ft.Container(
                content=ft.Column([
                    ft.Text("◀ 앞차 정보 입력", size=14, weight="bold"),
                    tf_f_bus, tf_f_driver, tf_f_phone,
                    ft.Row([
                        ft.ElevatedButton(
                            content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white"), alignment=ft.alignment.center),
                            on_click=save_front, expand=1, height=38,
                            style=ft.ButtonStyle(bgcolor="#1E3A8A", shape=ft.RoundedRectangleBorder(radius=0), padding=ft.padding.symmetric(vertical=0, horizontal=0)),
                        ),
                        ft.ElevatedButton(
                            content=ft.Container(ft.Text("뒤로가기", size=13, weight="bold", color="white"), alignment=ft.alignment.center),
                            on_click=lambda e: setattr(info_dialog, "open", False) or page.update(), expand=1, height=38,
                            style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=0), padding=ft.padding.symmetric(vertical=0, horizontal=0)),
                        )
                    ], alignment="center", spacing=8)
                ], spacing=10, tight=True),
                width=260, padding=4
            )

        elif target_type == "뒷차":
            tf_b_bus = ft.TextField(label="뒷차번호", value=input_data_state["back_bus"].replace("호","").replace("미입력",""), keyboard_type=ft.KeyboardType.NUMBER, expand=True, height=38)
            tf_b_driver = ft.TextField(label="기사성함", value=input_data_state["back_driver"].replace("미입력",""), expand=True, height=38)
            tf_b_phone = ft.TextField(label="전화번호 (숫자만)", value=input_data_state["back_phone"].replace("-","").replace("미입력",""), keyboard_type=ft.KeyboardType.PHONE, expand=True, height=38)
            
            def save_back(e):
                input_data_state["back_bus"] = f"{tf_b_bus.value}호" if tf_b_bus.value else "미입력"
                input_data_state["back_driver"] = tf_b_driver.value if tf_b_driver.value else "미입력"
                input_data_state["back_phone"] = final_format_phone(tf_b_phone.value) if tf_b_phone.value else "미입력"
                save_all_to_client_storage()
                info_dialog.open = False  
                page.update()
                rebuild_interface()

            box_content = ft.Container(
                content=ft.Column([
                    ft.Text("▶ 뒷차 정보 입력", size=14, weight="bold"),
                    tf_b_bus, tf_b_driver, tf_b_phone,
                    ft.Row([
                        ft.ElevatedButton(
                            content=ft.Container(ft.Text("확인", size=13, weight="bold", color="white"), alignment=ft.alignment.center),
                            on_click=save_back, expand=1, height=38,
                            style=ft.ButtonStyle(bgcolor="#1E3A8A", shape=ft.RoundedRectangleBorder(radius=0), padding=ft.padding.symmetric(vertical=0, horizontal=0)),
                        ),
                        ft.ElevatedButton(
                            content=ft.Container(ft.Text("뒤로가기", size=13, weight="bold", color="white"), alignment=ft.alignment.center),
                            on_click=lambda e: setattr(info_dialog, "open", False) or page.update(), expand=1, height=38,
                            style=ft.ButtonStyle(bgcolor="grey", shape=ft.RoundedRectangleBorder(radius=0), padding=ft.padding.symmetric(vertical=0, horizontal=0)),
                        )
                    ], alignment="center", spacing=8)
                ], spacing=10, tight=True),
                width=260, padding=4
            )

        info_dialog.content = box_content
        info_dialog.open = True
        page.update()

    info_dialog = ft.AlertDialog(modal=False, content=ft.Container())
    page.dialog = info_dialog

    def refresh_input_tab_view():
        input_zone_container.controls.clear()
        input_zone_container.controls.append(build_driving_summary_zone())
        page.update()

    def rebuild_interface():
        nonlocal USER_SCHEDULES, MANGEUN_TARGETS
        today = datetime.now(KST)
        today_y, today_m, today_d = today.year, today.month, today.day
        month_title.value = f"{current['year']}년 {current['month']}월"
        month_prefix = f"{current['year']}-{current['month']:02d}"
        month_data = {k: v for k, v in USER_SCHEDULES.items() if k.startswith(month_prefix)}
        # 🌟 [수정] 근무 일수 계산할 때 "전일"도 근무 날짜에 포함시킵니다.
        work_days = sum(1 for d in month_data.values() if d.get("status") in ["오전", "오후", "전일"])
        off_days = sum(1 for d in month_data.values() if d.get("status") == "휴무")
        m_target = get_mangeun_target()
        mangeun_dropdown.value = str(m_target)
        diff = work_days - m_target
        work_summary = f"근무: {work_days}(+{diff})" if diff > 0 else (f"근무: {work_days}({diff})" if diff < 0 else f"근무: {work_days}")
        stats_text.value = work_summary
        mangeun_text.value = f"휴무: {off_days}"
        mangeun_value_text.value = f"만근: {m_target}"

        calendar_grid.controls.clear()
        cal = calendar.Calendar(firstweekday=6)
        month_weeks = cal.monthdayscalendar(current['year'], current['month'])
        for week in month_weeks:
            week_row = ft.Row(alignment="spaceAround", spacing=2)
            for day in week:
                if day == 0:
                    week_row.controls.append(ft.Container(expand=1, height=52))
                else:
                    weekday = datetime(current['year'], current['month'], day).weekday()
                    date_key = f"{current['year']}-{current['month']:02d}-{day:02d}"
                    day_info = month_data.get(date_key, {"status": "", "start_time": "", "order_no": ""})
                    status, start_time, order_no = day_info.get("status", ""), day_info.get("start_time", ""), day_info.get("order_no", "")
                    bg_color, text_color, status_desc = "#FFFFFF", "#000000", ""
                    if status == "오전":
                        bg_color, text_color = "#D2E3FC", "#1A73E8"
                        status_desc = f"오전({order_no})" if order_no else "오전"
                    elif status == "오후":
                        bg_color, text_color = "#E9D5FF", "#7E22CE"
                        status_desc = f"오후({order_no})" if order_no else "오후"
                    # 🌟 [추가] '전일' 근무일 때 달력 칸을 연한 녹색 바탕에 진한 녹색 글씨로 표시
                    elif status == "전일":
                        bg_color, text_color = "#E6F4EA", "#137333"
                        status_desc = f"전일({order_no})" if order_no else "전일"
                    elif status == "휴무":
                        bg_color, text_color = "#FCE8E6", "#D93025"
                        status_desc = "휴무"
                    day_number_color = "#D93025" if weekday == 6 else ("#1A73E8" if weekday == 5 else "#000000")
                    time_display = ft.Text(start_time, size=9, weight="bold", color=text_color) if start_time and status != "휴무" else ft.Container()
                    is_today = (current['year'] == today_y and current['month'] == today_m and day == today_d)
                    day_border = ft.border.all(2, "#2563EB") if is_today else ft.border.all(0.5, "#E2E8F0")

                    day_box = ft.Container(
                        content=ft.Column([ft.Text(f"{day}", size=12, weight="bold", color=day_number_color), ft.Text(status_desc, size=10, weight="bold", color=text_color), time_display], alignment="center", horizontal_alignment="center", spacing=0),
                        bgcolor=bg_color, border=day_border, border_radius=4, height=52, expand=1, on_click=lambda e, dk=date_key: open_input_popup(dk)
                    )
                    week_row.controls.append(day_box)
            calendar_grid.controls.append(week_row)
        
        if current_tab == "운행정보":
            refresh_input_tab_view()

        page.update()

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
            selected_time_state["hour"], selected_time_state["minute"] = 5, 0
            hour_picker.selected_index, minute_picker.selected_index = 5, 0
        
        popup_layer.content = popup_card
        popup_layer.visible = True
        page.update()

    def select_status_and_save(status_value):
        target_date = current["selected_date"]
        if status_value == "선택취소":
            USER_SCHEDULES.pop(target_date, None)
            save_all_to_client_storage()
            popup_layer.visible = False
            rebuild_interface()
            return
            
        final_time = ""
        if status_value == "자동":
            h, m = selected_time_state["hour"], selected_time_state["minute"]
            
            # 🌟 [로직 수정] 기존 상태가 '전일'인 상태에서 시간만 바꾼 거라면, 오전/오후로 분류하지 않고 '전일' 유지!
            existing_info = USER_SCHEDULES.get(target_date, {})
            if existing_info.get("status") == "전일":
                status_value = "전일"
            else:
                status_value = "오후" if h >= 12 else "오전"
                
            final_time = f"{h:02d}:{m:02d}"
            
        input_order = "" if status_value == "휴무" else (order_dropdown.value if order_dropdown.value else "")
        USER_SCHEDULES[target_date] = {"status": status_value, "start_time": final_time, "order_no": input_order}
        save_all_to_client_storage()
        popup_layer.visible = False
        rebuild_interface()

    popup_card = ft.Container(
        content=ft.Column([
            # 1️⃣ 날짜 타이틀 (맨 위)
            ft.Row([popup_date_title], alignment="center"), 
            ft.Divider(height=1, color="transparent"),
            
            # 2️⃣ [상단 배치] 시간 없이 근무만 등록하는 버튼들
            # 3️⃣ 시간 없이 근무만 등록하는 버튼들 (전일근무 버튼 신설!)
            ft.Text("시간 없이 근무만 등록할 때:", size=11, weight="bold", color="grey"),
            ft.Row([
                ft.Container(content=ft.Text("휴무", size=14, weight="bold", color="white"), bgcolor="#D93025", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("휴무")),
                ft.Container(content=ft.Text("오전", size=14, weight="bold", color="white"), bgcolor="#5C93E6", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("오전")),
                ft.Container(content=ft.Text("오후", size=14, weight="bold", color="white"), bgcolor="#7E22CE", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("오후")),
                # 🌟 [추가] 전일근무 버튼 (녹색으로 깔끔하게 구별)
                ft.Container(content=ft.Text("전일", size=14, weight="bold", color="white"), bgcolor="#10B981", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("전일"))
            ], spacing=4), # 💡 버튼이 4개가 되므로 여백을 4로 살짝 줄여서 한 줄에 쏙 넣습니다.
            # 3️⃣ 첫탕 시간을 정하는 시계 바퀴 (CupertinoPicker)
            dial_row,
            
            # 4️⃣ [위치 교정] 시계 바퀴 바로 아래로 내려온 근무 순번 선택 영역
            ft.Row([ft.Text("근무 순번:", size=12, weight="bold", color="black"), order_dropdown], alignment="center", spacing=10),
            ft.Divider(height=2), 
            
            # 5️⃣ 파란색 저장 버튼 (순번 바로 밑으로)
            ft.Row([ft.Container(content=ft.Text("저장", size=14, weight="bold", color="white"), bgcolor="#2563EB", alignment=ft.Alignment(0, 0), width=160, height=38, border_radius=6, on_click=lambda e: select_status_and_save("자동"))], alignment="center"),
            
            # 6️⃣ 맨 아래 취소/닫기 영역
            ft.Divider(height=1, color="transparent"),
            ft.Row([ft.TextButton("선택취소(삭제)", on_click=lambda e: select_status_and_save("선택취소"), style=ft.ButtonStyle(color="red")), ft.TextButton("닫기", on_click=lambda e: setattr(popup_layer, "visible", False) or page.update())], alignment="spaceBetween")
        ], spacing=6, tight=True),
        bgcolor="white", padding=12, border_radius=12, width=300
    )

    def open_mangeun_popup(e):
        mangeun_dropdown.value = str(get_mangeun_target())
        mangeun_popup_layer.visible = True
        page.update()

    mangeun_popup_card = ft.Container(
        content=ft.Column([
            ft.Text("만근 기준 변경", size=16, weight="bold", color="black"),
            ft.Row([ft.Text("만근:", size=13, weight="bold", color="black"), mangeun_dropdown], alignment="center", spacing=10),
            ft.Row([ft.TextButton("취소", on_click=lambda e: setattr(mangeun_popup_layer, "visible", False) or page.update()), ft.TextButton("저장", on_click=on_mangeun_dropdown_changed, style=ft.ButtonStyle(color="#2563EB"))], alignment="spaceBetween")
        ], spacing=10, tight=True),
        bgcolor="white", padding=14, border_radius=12, width=240
    )
    mangeun_popup_layer.content = mangeun_popup_card

    def move_prev(e):
        current["month"] -= 1
        if current["month"] == 0: current["month"] = 12; current["year"] -= 1
        rebuild_interface()

    def move_next(e):
        current["month"] += 1
        if current["month"] == 13: current["month"] = 1; current["year"] += 1
        rebuild_interface()

    header_nav = ft.Row([ft.TextButton("◀ 이전", on_click=move_prev, style=ft.ButtonStyle(color="black")), month_title, ft.TextButton("다음 ▶", on_click=move_next, style=ft.ButtonStyle(color="black"))], alignment="spaceBetween")
    mangeun_setting_row = ft.Row([mangeun_value_text, ft.ElevatedButton("변경", on_click=open_mangeun_popup, bgcolor="#2563EB", color="white", width=68, height=22, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), text_style=ft.TextStyle(size=11, weight="bold"), padding=0))], alignment="start", vertical_alignment="center", spacing=6, height=22)
    
    summary_group = ft.Column([stats_text, mangeun_text, mangeun_setting_row], spacing=6, tight=True)
    summary_area = ft.Row([summary_group, phonebook_big_button], alignment="spaceBetween")
    # ↓↓↓ 안내문구 추가 날짜를 터치하여 근무를 입력 또는 수정하세요 ↓↓↓
    guide_text = ft.Container(content=ft.Text("💡 날짜를 터치하여 근무를 입력 또는 수정하세요.", size=10, color="#666666"), padding=ft.padding.only(left=8, bottom=4))
    bottom_navigation_bar = ft.Row([btn_calendar, btn_input, btn_setting], alignment="spaceAround", spacing=4)

    scrollable_content = ft.Column(
        [
            header_nav, summary_area, guide_text, div_line1,
            weeks_header, div_line2,
            calendar_grid,
            input_zone_container,
            phonebook_zone_container 
        ],
        expand=True, scroll=ft.ScrollMode.AUTO
    )

    main_layout = ft.Column([scrollable_content, ft.Divider(height=1), bottom_navigation_bar], expand=True)
    
    page.add(ft.Stack([main_layout, popup_layer, mangeun_popup_layer], expand=True))
    
    change_tab("달력")
    rebuild_interface()

init_db()
ft.app(target=main, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)
