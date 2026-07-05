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

    USER_SCHEDULES = json.loads(saved_schedules) if saved_schedules else {}
    MANGEUN_TARGETS = json.loads(saved_targets) if saved_targets else {}
    
    def save_all_to_client_storage():
        page.client_storage.set(STORAGE_SCHEDULES_KEY, json.dumps(USER_SCHEDULES, ensure_ascii=False))
        page.client_storage.set(STORAGE_MANGEUN_KEY, json.dumps(MANGEUN_TARGETS, ensure_ascii=False))

    now_kst = datetime.now(KST)
    current = {"year": now_kst.year, "month": now_kst.month, "selected_date": "2026-07-04"}
    selected_time_state = {"hour": 5, "minute": 0}

    # 입력창 제어를 위한 임시 메모리 변수
    input_data_state = {
        "route": "미입력",
        "bus_no": "미입력"
    }

    current_tab = "달력"

    month_title = ft.Text("", size=20, weight="bold", text_align="center")
    stats_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_value_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    
    calendar_grid = ft.Column(spacing=2)
    input_zone_container = ft.Column(spacing=2, visible=False)
    
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

    # 1구역 운행 요약 카드 UI 생성 함수 (상태 변수값을 반영하도록 개선)
    def build_driving_summary_zone():
        day_data = {
            "route": input_data_state["route"],
            "bus_no": input_data_state["bus_no"],
            "front_bus": "미입력", "front_driver": "미입력", "front_phone": "미입력",
            "back_bus": "미입력", "back_driver": "미입력", "back_phone": "미입력"
        }
        main_info_col = ft.Column([
            ft.Text(f"노선: {day_data['route']}", size=16, weight="bold", color="black"),
            ft.Text(f"내차: {day_data['bus_no']}", size=16, weight="bold", color="black")
        ], spacing=4)

        front_card = ft.Container(
            content=ft.Column([
                ft.Text("앞차 정보", size=11, color="grey", weight="bold"),
                ft.Text(day_data['front_bus'], size=14, weight="bold", color="black"),
                ft.Text(day_data['front_driver'], size=14, weight="bold", color="black"),
                ft.Text(day_data['front_phone'], size=13, color="#1E3A8A", weight="bold")
            ], spacing=2, tight=True),
            bgcolor="#F8FAFC", border=ft.border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1
        )

        back_card = ft.Container(
            content=ft.Column([
                ft.Text("뒷차 정보", size=11, color="grey", weight="bold"),
                ft.Text(day_data['back_bus'], size=14, weight="bold", color="black"),
                ft.Text(day_data['back_driver'], size=14, weight="bold", color="black"),
                ft.Text(day_data['back_phone'], size=13, color="#1E3A8A", weight="bold")
            ], spacing=2, tight=True),
            bgcolor="#F8FAFC", border=ft.border.all(1, "#E2E8F0"), border_radius=8, padding=10, expand=1
        )
        helpers_row = ft.Row([front_card, back_card], spacing=8, alignment="spaceAround")
        return ft.Container(
            content=ft.Column([
                ft.Text("📅 운행 정보 요약", size=14, weight="bold", color="#1E3A8A"),
                main_info_col, ft.Divider(height=1, color="#E2E8F0"), helpers_row
            ], spacing=8),
            padding=12, border=ft.border.all(1, "#2563EB"), border_radius=10, margin=ft.margin.only(bottom=10)
        )

    # ⭐ [추가] 2구역: 노선번호 및 내차번호 입력 컴포넌트 생성 함수
    # 수정된 2구역: 내차 / 앞차 / 뒷차 분리형 입력창 함수
    def build_input_fields_zone():
        # --- [1. 내 정보 입력 구역] ---
        tf_route = ft.TextField(label="노선번호", hint_text="67", keyboard_type=ft.KeyboardType.NUMBER, expand=2, height=38, text_size=12, content_padding=ft.padding.symmetric(vertical=4, horizontal=6))
        tf_bus_no = ft.TextField(label="내차번호", hint_text="2743", keyboard_type=ft.KeyboardType.NUMBER, expand=2, height=38, text_size=12, content_padding=ft.padding.symmetric(vertical=4, horizontal=6))
        
        def on_my_confirm(e):
            input_data_state["route"] = tf_route.value if tf_route.value else "미입력"
            input_data_state["bus_no"] = f"{tf_bus_no.value}호" if tf_bus_no.value else "미입력"
            refresh_input_tab_view()

        btn_my_confirm = ft.ElevatedButton("확인", on_click=on_my_confirm, bgcolor="#2563EB", color="white", height=36, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0))
        
        my_zone = ft.Container(
            content=ft.Column([
                ft.Text("👤 내 차량 설정", size=11, weight="bold", color="grey"),
                ft.Row([tf_route, tf_bus_no, btn_my_confirm], spacing=6)
            ], spacing=4),
            padding=8, border=ft.border.all(1, "#E2E8F0"), border_radius=6, margin=ft.margin.only(bottom=6)
        )

        # --- [2. 앞차 정보 입력 구역] ---
        tf_f_bus = ft.TextField(label="앞차번호", hint_text="1234", keyboard_type=ft.KeyboardType.NUMBER, expand=3, height=38, text_size=12, content_padding=ft.padding.symmetric(vertical=4, horizontal=6))
        tf_f_driver = ft.TextField(label="기사성함", hint_text="홍길동", expand=3, height=38, text_size=12, content_padding=ft.padding.symmetric(vertical=4, horizontal=6))
        tf_f_phone = ft.TextField(label="전화번호", hint_text="01012345678", keyboard_type=ft.KeyboardType.PHONE, expand=4, height=38, text_size=12, content_padding=ft.padding.symmetric(vertical=4, horizontal=6))
        
        def on_front_confirm(e):
            input_data_state["front_bus"] = f"{tf_f_bus.value}호" if tf_f_bus.value else "미입력"
            input_data_state["front_driver"] = tf_f_driver.value if tf_f_driver.value else "미입력"
            input_data_state["front_phone"] = tf_f_phone.value if tf_f_phone.value else "미입력"
            refresh_input_tab_view()

        btn_front_confirm = ft.ElevatedButton("확인", on_click=on_front_confirm, bgcolor="#1E3A8A", color="white", height=36, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0))

        front_zone = ft.Container(
            content=ft.Column([
                ft.Text("◀ 앞차 정보 입력", size=11, weight="bold", color="grey"),
                ft.Row([tf_f_bus, tf_f_driver, tf_f_phone, btn_front_confirm], spacing=4)
            ], spacing=4),
            padding=8, border=ft.border.all(1, "#E2E8F0"), border_radius=6, margin=ft.margin.only(bottom=6)
        )

        # --- [3. 뒷차 정보 입력 구역] ---
        tf_b_bus = ft.TextField(label="뒷차번호", hint_text="5678", keyboard_type=ft.KeyboardType.NUMBER, expand=3, height=38, text_size=12, content_padding=ft.padding.symmetric(vertical=4, horizontal=6))
        tf_b_driver = ft.TextField(label="기사성함", hint_text="김철수", expand=3, height=38, text_size=12, content_padding=ft.padding.symmetric(vertical=4, horizontal=6))
        tf_b_phone = ft.TextField(label="전화번호", hint_text="01087654321", keyboard_type=ft.KeyboardType.PHONE, expand=4, height=38, text_size=12, content_padding=ft.padding.symmetric(vertical=4, horizontal=6))

        def on_back_confirm(e):
            input_data_state["back_bus"] = f"{tf_b_bus.value}호" if tf_b_bus.value else "미입력"
            input_data_state["back_driver"] = tf_b_driver.value if tf_b_driver.value else "미입력"
            input_data_state["back_phone"] = tf_b_phone.value if tf_b_phone.value else "미입력"
            refresh_input_tab_view()

        btn_back_confirm = ft.ElevatedButton("확인", on_click=on_back_confirm, bgcolor="#1E3A8A", color="white", height=36, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0))

        back_zone = ft.Container(
            content=ft.Column([
                ft.Text("▶ 뒷차 정보 입력", size=11, weight="bold", color="grey"),
                ft.Row([tf_b_bus, tf_b_driver, tf_b_phone, btn_back_confirm], spacing=4)
            ], spacing=4),
            padding=8, border=ft.border.all(1, "#E2E8F0"), border_radius=6, margin=ft.margin.only(bottom=10)
        )

        # 기존 입력값 복원 세팅
        if input_data_state["route"] != "미입력": tf_route.value = input_data_state["route"]
        if input_data_state["bus_no"] != "미입력": tf_bus_no.value = input_data_state["bus_no"].replace("호", "")
        if input_data_state["front_bus"] != "미입력": tf_f_bus.value = input_data_state["front_bus"].replace("호", "")
        if input_data_state["front_driver"] != "미입력": tf_f_driver.value = input_data_state["front_driver"]
        if input_data_state["front_phone"] != "미입력": tf_f_phone.value = input_data_state["front_phone"]
        if input_data_state["back_bus"] != "미입력": tf_b_bus.value = input_data_state["back_bus"].replace("호", "")
        if input_data_state["back_driver"] != "미입력": tf_b_driver.value = input_data_state["back_driver"]
        if input_data_state["back_phone"] != "미입력": tf_b_phone.value = input_data_state["back_phone"]

        # 최종적으로 세 개의 독립된 구역을 세로로 쌓아서 반환
        return ft.Column([my_zone, front_zone, back_zone], spacing=2)

    # 입력 탭의 화면 구성품을 갱신하는 헬퍼 함수
    def refresh_input_tab_view():
        input_zone_container.controls.clear()
        # 1구역 요약 카드와 2구역 입력창을 차례대로 결합
        input_zone_container.controls.append(build_driving_summary_zone())
        input_zone_container.controls.append(build_input_fields_zone())
        page.update()

    def change_tab(tab_name):
        nonlocal current_tab
        current_tab = tab_name
        
        btn_calendar.style.color = "#2563EB" if tab_name == "달력" else "grey"
        btn_input.style.color = "#2563EB" if tab_name == "입력" else "grey"
        btn_setting.style.color = "#2563EB" if tab_name == "설정" else "grey"
        
        if tab_name == "달력":
            calendar_grid.visible = True
            input_zone_container.visible = False
            weeks_header.visible = True
            div_line1.visible = True
            div_line2.visible = True
        elif tab_name == "입력":
            calendar_grid.visible = False
            input_zone_container.visible = True
            weeks_header.visible = False
            div_line1.visible = False
            div_line2.visible = False
            
            # 입력 탭 진입 시 1구역+2구역 통합 빌드
            refresh_input_tab_view()
        # 이 부분이 change_tab 함수의 맨 아래쪽입니다.
        elif tab_name == "설정":
            calendar_grid.visible = False
            input_zone_container.visible = False
            weeks_header.visible = False
            div_line1.visible = False
            div_line2.visible = False

        # ⭐ [이 줄을 추가해 주세요!] 겉껍질 박스도 화면 갱신 대상에 포함시킵니다.
        scrollable_content.update() 
        
        page.update()

    def rebuild_interface():
        nonlocal USER_SCHEDULES, MANGEUN_TARGETS
        today = datetime.now(KST)
        today_y, today_m, today_d = today.year, today.month, today.day
        month_title.value = f"{current['year']}년 {current['month']}월"
        month_prefix = f"{current['year']}-{current['month']:02d}"
        month_data = {k: v for k, v in USER_SCHEDULES.items() if k.startswith(month_prefix)}
        work_days = sum(1 for d in month_data.values() if d.get("status") in ["오전", "오후"])
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
                    week_row.controls.append(ft.Container(expand=1, height=48))
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
                    elif status == "휴무":
                        bg_color, text_color = "#FCE8E6", "#D93025"
                        status_desc = "휴무"
                    day_number_color = "#D93025" if weekday == 6 else ("#1A73E8" if weekday == 5 else text_color)
                    time_display = ft.Text(start_time, size=9, weight="bold", color=text_color) if start_time and status != "휴무" else ft.Container()
                    is_today = (current['year'] == today_y and current['month'] == today_m and day == today_d)
                    day_border = ft.border.all(2, "#2563EB") if is_today else ft.border.all(0.5, "#E2E8F0")

                    day_box = ft.Container(
                        content=ft.Column([ft.Text(f"{day}", size=12, weight="bold", color=day_number_color), ft.Text(status_desc, size=10, weight="bold", color=text_color), time_display], alignment="center", horizontal_alignment="center", spacing=0),
                        bgcolor=bg_color, border=day_border, border_radius=4, height=48, expand=1, on_click=lambda e, dk=date_key: open_input_popup(dk)
                    )
                    week_row.controls.append(day_box)
            calendar_grid.controls.append(week_row)
        
        if current_tab == "입력":
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
            status_value = "오후" if h >= 12 else "오전"
            final_time = f"{h:02d}:{m:02d}"
        input_order = "" if status_value == "휴무" else (order_dropdown.value if order_dropdown.value else "")
        USER_SCHEDULES[target_date] = {"status": status_value, "start_time": final_time, "order_no": input_order}
        save_all_to_client_storage()
        popup_layer.visible = False
        rebuild_interface()

    popup_card = ft.Container(
        content=ft.Column([
            ft.Row([popup_date_title], alignment="center"), ft.Divider(height=1, color="transparent"), dial_row,
            ft.Row([ft.Container(content=ft.Text("저장", size=14, weight="bold", color="white"), bgcolor="#2563EB", alignment=ft.Alignment(0, 0), width=160, height=38, border_radius=6, on_click=lambda e: select_status_and_save("자동"))], alignment="center"),
            ft.Divider(height=2),
            ft.Row([ft.Text("근무 순번:", size=12, weight="bold", color="black"), order_dropdown], alignment="center", spacing=10),
            ft.Divider(height=2), ft.Text("시간 없이 근무만 등록할 때:", size=11, weight="bold", color="grey"),
            ft.Row([
                ft.Container(content=ft.Text("휴무", size=14, weight="bold", color="white"), bgcolor="#D93025", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("휴무")),
                ft.Container(content=ft.Text("오전근무", size=14, weight="bold", color="white"), bgcolor="#5C93E6", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("오전")),
                ft.Container(content=ft.Text("오후근무", size=14, weight="bold", color="white"), bgcolor="#7E22CE", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1, on_click=lambda e: select_status_and_save("오후"))
            ], spacing=6),
            ft.Divider(height=1, color="transparent"),
            ft.Row([ft.TextButton("선택취소(삭제)", on_click=lambda e: select_status_and_save("선택취소"), style=ft.ButtonStyle(color="red")), ft.TextButton("닫기", on_click=lambda e: setattr(popup_layer, "visible", False) or page.update())], alignment="spaceBetween")
        ], spacing=6, tight=True),
        bgcolor="white", padding=12, border_radius=12, width=300
    )
    popup_layer.content = popup_card

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
    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row([ft.Container(content=ft.Text(d, size=13, weight="bold", color="#D93025" if d=="일" else ("#1A73E8" if d=="토" else "black")), expand=1, alignment=ft.Alignment(0, 0)) for d in days_letters], alignment="spaceAround")

    div_line1 = ft.Divider(height=1)
    div_line2 = ft.Divider(height=1)

    # 하단 내비게이션 바 버튼에 탭 전환 기능(on_click) 확실하게 연결
    btn_calendar = ft.TextButton("달력", style=ft.ButtonStyle(color="#2563EB"), expand=1, height=40, on_click=lambda e: change_tab("달력"))
    btn_input = ft.TextButton("입력", style=ft.ButtonStyle(color="grey"), expand=1, height=40, on_click=lambda e: change_tab("입력"))
    btn_setting = ft.TextButton("설정", style=ft.ButtonStyle(color="grey"), expand=1, height=40, on_click=lambda e: change_tab("설정"))    
    
    bottom_navigation_bar = ft.Row([btn_calendar, btn_input, btn_setting], alignment="spaceAround")

    scrollable_content = ft.Column(
        [
            header_nav, summary_group, div_line1,
            weeks_header, div_line2,
            calendar_grid,
            input_zone_container
        ],
        expand=True, scroll=ft.ScrollMode.AUTO
    )

    main_layout = ft.Column([scrollable_content, ft.Divider(height=1), bottom_navigation_bar], expand=True)
    page.add(ft.Stack([main_layout, popup_layer, mangeun_popup_layer], expand=True))
    
    change_tab("달력")
    rebuild_interface()

init_db()
ft.app(target=main, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)
