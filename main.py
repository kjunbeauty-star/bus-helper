import os  # Render 배포 환경용 및 파일 확인 모듈
import sqlite3  # SQLite3 데이터베이스 모듈
import calendar
from datetime import datetime, timedelta, timezone
import flet as ft
import json

# 대한민국 표준시 (GMT +9:00) 설정
KST = timezone(timedelta(hours=9))

# 데이터베이스 파일 이름 정의
DB_FILE = "schedules.db"
STORAGE_SCHEDULES_KEY = "bus_helper_schedules"
STORAGE_MANGEUN_KEY = "bus_helper_mangeun_targets"

# --- [SQLite3 데이터베이스 제어 함수] ---
def init_db():
    """앱 시작 시 데이터베이스와 테이블을 생성하고 초기화합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # schedules 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            date_key TEXT PRIMARY KEY,
            status TEXT,
            start_time TEXT
        )
    """)
    
    # mangeun_targets 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mangeun_targets (
            month_key TEXT PRIMARY KEY,
            target INTEGER
        )
    """)
    
    conn.commit()
    conn.close()

def load_schedules_from_db():
    """데이터베이스에서 모든 근무 일정을 읽어와 딕셔너리로 반환합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT date_key, status, start_time FROM schedules")
    rows = cursor.fetchall()
    conn.close()
    
    schedules = {}
    for row in rows:
        schedules[row[0]] = {"status": row[1], "start_time": row[2], "order_no": ""}
    return schedules

def load_mangeun_targets_from_db():
    """데이터베이스에서 모든 월별 만근 기준을 읽어와 딕셔너리로 반환합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT month_key, target FROM mangeun_targets")
    rows = cursor.fetchall()
    conn.close()
    
    targets = {}
    for row in rows:
        targets[row[0]] = row[1]
    return targets

def save_schedule_to_db(date_key, status, start_time):
    """근무 일정을 데이터베이스에 즉시 저장하거나 수정합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO schedules (date_key, status, start_time)
        VALUES (?, ?, ?)
    """, (date_key, status, start_time))
    conn.commit()
    conn.close()

def delete_schedule_from_db(date_key):
    """선택 취소 시 데이터베이스에서 해당 일정을 즉시 삭제합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules WHERE date_key = ?", (date_key,))
    conn.commit()
    conn.close()

def save_mangeun_target_to_db(month_key, target):
    """만근 목표 기준 값을 데이터베이스에 즉시 저장하거나 수정합니다."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO mangeun_targets (month_key, target)
        VALUES (?, ?)
    """, (month_key, target))
    conn.commit()
    conn.close()

# --- [Flet 메인 어플리케이션 인터페이스] ---

def main(page: ft.Page):
    page.title = "버스기사도우미"
    page.theme_mode = "light"
    page.padding = 4

    # 폰/브라우저 저장소에서 기존 데이터 로드[cite: 2]
    saved_schedules = page.client_storage.get(STORAGE_SCHEDULES_KEY)
    saved_targets = page.client_storage.get(STORAGE_MANGEUN_KEY)

    USER_SCHEDULES = json.loads(saved_schedules) if saved_schedules else {}
    MANGEUN_TARGETS = json.loads(saved_targets) if saved_targets else {}
    
    def save_all_to_client_storage():
        """현재 근무표와 만근 기준을 폰/브라우저 저장소에 저장합니다."""
        page.client_storage.set(STORAGE_SCHEDULES_KEY, json.dumps(USER_SCHEDULES, ensure_ascii=False))
        page.client_storage.set(STORAGE_MANGEUN_KEY, json.dumps(MANGEUN_TARGETS, ensure_ascii=False))

    # 현재 시간 세팅
    now_kst = datetime.now(KST)
    current = {"year": now_kst.year, "month": now_kst.month, "selected_date": ""}
    selected_time_state = {"hour": 5, "minute": 0}

    # 1. 컴포넌트 선언
    month_title = ft.Text("", size=20, weight="bold", text_align="center")
    stats_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_value_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    calendar_grid = ft.Column(spacing=2)
    popup_date_title = ft.Text("", size=16, weight="bold", color="black", text_align="center")
    
    # [수정] 순번 입력을 TextField에서 Dropdown 방식으로 전환
    order_options = [ft.dropdown.Option("", "선택 안 함")] + [ft.dropdown.Option(str(i), f"{i}번") for i in range(1, 51)]
    order_dropdown = ft.Dropdown(
        options=order_options,
        width=140,
        height=40,
        text_size=13,
        content_padding=ft.padding.symmetric(vertical=4, horizontal=10),
    )
    
    # 만근 기준 저장 버튼 클릭 시 현재 월 기준값을 저장합니다.
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

    # 만근 기준 변경 팝업에서 사용하는 숫자 선택 드롭다운 (15일 ~ 26일)
    mangeun_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(str(i)) for i in range(15, 27)],
        width=62,
        height=36,
        text_size=12,
        content_padding=ft.padding.symmetric(vertical=4, horizontal=8),
    )

    # 24시간제 다이얼[cite: 2]
    hour_picker = ft.CupertinoPicker(
        controls=[ft.Text(f"{i:02d}", size=20) for i in range(24)],
        selected_index=5,
        on_change=lambda e: update_hour(int(e.control.selected_index)),
        height=100,
        expand=1,
        looping=True,
    )
    
    minute_picker = ft.CupertinoPicker(
        controls=[ft.Text(f"{i:02d}", size=20) for i in range(60)],
        selected_index=0,
        on_change=lambda e: update_minute(int(e.control.selected_index)),
        height=100,
        expand=1,
        looping=True,
    )

    def update_hour(val):
        selected_time_state["hour"] = val

    def update_minute(val):
        selected_time_state["minute"] = val

    dial_row = ft.Row(
        [
            hour_picker,
            ft.Text(":", size=20, weight="bold", color="black"),
            minute_picker,
        ],
        alignment="center",
        height=100
    )

    popup_layer = ft.Container(
        visible=False,
        bgcolor="#AA000000",  
        alignment=ft.Alignment(0, 0),  
        expand=True
    )

    mangeun_popup_layer = ft.Container(
        visible=False,
        bgcolor="#AA000000",
        alignment=ft.Alignment(0, 0),
        expand=True
    )

    # 2. 데이터 제어 함수[cite: 2]
    def get_mangeun_target():
        try:
            y, m = int(current['year']), int(current['month'])
            key = f"{y}_{m}"
            if key in MANGEUN_TARGETS:
                return int(MANGEUN_TARGETS[key])
            days_in_month = calendar.monthrange(y, m)[1]
            return 22 if days_in_month == 31 else (20 if m == 2 else 21)
        except:
            return 22

    # 3. 화면 리빌드 함수 (근무명 + 순번 결합 형태)[cite: 2]
    def rebuild_interface():
        nonlocal USER_SCHEDULES, MANGEUN_TARGETS

        today = datetime.now(KST)
        today_y = today.year
        today_m = today.month
        today_d = today.day

        month_title.value = f"{current['year']}년 {current['month']}월"
        month_prefix = f"{current['year']}-{current['month']:02d}"
        
        month_data = {k: v for k, v in USER_SCHEDULES.items() if k.startswith(month_prefix)}
        
        work_days = sum(1 for d in month_data.values() if d.get("status") in ["오전", "오후"])
        off_days = sum(1 for d in month_data.values() if d.get("status") == "휴무")
        
        m_target = get_mangeun_target()
        mangeun_dropdown.value = str(m_target)
        
        # 상단 요약은 항목명과 숫자만 간단히 표시합니다.
        diff = work_days - m_target
        if diff > 0:
            work_summary = f"근무: {work_days}(+{diff})"
        elif diff < 0:
            work_summary = f"근무: {work_days}({diff})"
        else:
            work_summary = f"근무: {work_days}"

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
                    date_obj = datetime(current['year'], current['month'], day)
                    weekday = date_obj.weekday()   # 월=0 ... 토=5, 일=6
                    date_key = f"{current['year']}-{current['month']:02d}-{day:02d}"
                    day_info = month_data.get(date_key, {"status": "", "start_time": "", "order_no": ""})
                    
                    status = day_info.get("status", "")
                    start_time = day_info.get("start_time", "")
                    order_no = day_info.get("order_no", "")
                    
                    bg_color = "#FFFFFF"
                    text_color = "#000000"
                    status_desc = ""
                    
                    if status == "오전":
                        bg_color = "#D2E3FC"; text_color = "#1A73E8"
                        status_desc = f"오전({order_no})" if order_no else "오전"
                    elif status == "오후":
                        bg_color = "#E9D5FF"; text_color = "#7E22CE"
                        status_desc = f"오후({order_no})" if order_no else "오후"
                    elif status == "휴무":
                        bg_color = "#FCE8E6"; text_color = "#D93025"
                        status_desc = "휴무"
                        
                    if weekday == 6:
                        day_number_color = "#D93025"
                    elif weekday == 5:
                        day_number_color = "#1A73E8"
                    else:
                        day_number_color = text_color

                    time_display = ft.Text(start_time, size=9, weight="bold", color=text_color) if start_time and status != "휴무" else ft.Container()

                    is_today = (current['year'] == today_y and current['month'] == today_m and day == today_d)
                    day_border = ft.border.all(2, "#2563EB") if is_today else None

                    day_box = ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(f"{day}", size=12, weight="bold", color=day_number_color),
                                ft.Text(status_desc, size=10, weight="bold", color=text_color),
                                time_display,
                            ],
                            alignment="center",
                            horizontal_alignment="center",
                            spacing=0
                        ),
                        bgcolor=bg_color,
                        border=day_border,
                        border_radius=4,
                        height=48,
                        expand=1,
                        on_click=lambda e, dk=date_key: open_input_popup(dk)
                    )
                    week_row.controls.append(day_box)
            calendar_grid.controls.append(week_row)
        page.update()

    # 4. 팝업창 제어 및 데이터 동기화 자동 저장 함수[cite: 2]
    def open_input_popup(date_key):
        current["selected_date"] = date_key
        popup_date_title.value = f"{date_key}\n근무를 선택하거나 시간을 맞추세요"
        
        day_info = USER_SCHEDULES.get(date_key, {})
        current_time = day_info.get("start_time", "")
        current_order = day_info.get("order_no", "")
        
        # [수정] 기존 데이터 매칭 루틴을 드롭다운 바인딩으로 전환
        order_dropdown.value = str(current_order) if current_order else ""
        
        if current_time and ":" in current_time:
            h, m = map(int, current_time.split(":"))
            selected_time_state["hour"] = h
            selected_time_state["minute"] = m
            hour_picker.selected_index = h
            minute_picker.selected_index = m
        else:
            selected_time_state["hour"] = 5
            selected_time_state["minute"] = 0
            hour_picker.selected_index = 5
            minute_picker.selected_index = 0
            
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
            h = selected_time_state["hour"]
            m = selected_time_state["minute"]
            if h >= 12:
                status_value = "오후"
            else:
                status_value = "오전"
            final_time = f"{h:02d}:{m:02d}"
        else:
            final_time = ""

        # [수정] 드롭다운 기반 순번 추출 및 휴무 예외 처리
        if status_value == "휴무":
            input_order = ""
        else:
            input_order = order_dropdown.value if order_dropdown.value else ""

        USER_SCHEDULES[target_date] = {
            "status": status_value, 
            "start_time": final_time,
            "order_no": input_order
        }
        save_all_to_client_storage()
        
        popup_layer.visible = False  
        rebuild_interface()          

    # 5. 팝업창 디자인 구성[cite: 2]
    popup_card = ft.Container(
        content=ft.Column(
            [
                ft.Row([popup_date_title], alignment="center"),
                ft.Divider(height=1, color="transparent"),
                dial_row, 
                ft.Container(
                    content=ft.Text("선택한 시간으로 저장", size=15, weight="bold", color="white"),
                    bgcolor="#2563EB", alignment=ft.Alignment(0, 0), height=44, border_radius=6,
                    on_click=lambda e: select_status_and_save("자동")
                ),
                ft.Divider(height=2),
                
                # [수정] 순번 드롭다운 배치 라인
                ft.Row(
                    [
                        ft.Text("근무 순번:", size=12, weight="bold", color="black"),
                        order_dropdown
                    ],
                    alignment="center",
                    spacing=10
                ),
                ft.Divider(height=2),
                
                ft.Text("시간 없이 근무만 등록할 때:", size=11, weight="bold", color="grey"),
                ft.Container(
                    content=ft.Text("휴무 지정", size=15, weight="bold", color="white"),
                    bgcolor="#D93025", alignment=ft.Alignment(0, 0), height=40, border_radius=6,
                    on_click=lambda e: select_status_and_save("휴무")
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("오전조 등록", size=14, weight="bold", color="white"),
                            bgcolor="#5C93E6", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1,
                            on_click=lambda e: select_status_and_save("오전")
                        ),
                        ft.Container(
                            content=ft.Text("오후조 등록", size=14, weight="bold", color="white"),
                            bgcolor="#7E22CE", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1,
                            on_click=lambda e: select_status_and_save("오후")
                        ),
                    ],
                    spacing=10
                ),
                ft.Divider(height=1, color="transparent"),
                ft.Row(
                    [
                        ft.TextButton("선택취소(삭제)", on_click=lambda e: select_status_and_save("선택취소"), style=ft.ButtonStyle(color="red")),
                        ft.TextButton("닫기", on_click=lambda e: setattr(popup_layer, "visible", False) or page.update()),
                    ],
                    alignment="spaceBetween"
                )
            ],
            spacing=6,
            tight=True
        ),
        bgcolor="white", padding=12, border_radius=12, width=300
    )
    popup_layer.content = popup_card

    def open_mangeun_popup(e):
        """현재 월의 만근 기준값을 팝업 드롭다운에 맞춘 뒤 엽니다."""
        mangeun_dropdown.value = str(get_mangeun_target())
        mangeun_popup_layer.visible = True
        page.update()

    mangeun_popup_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("만근 기준 변경", size=16, weight="bold", color="black"),
                ft.Row(
                    [
                        ft.Text("만근:", size=13, weight="bold", color="black"),
                        mangeun_dropdown,
                    ],
                    alignment="center",
                    spacing=10,
                ),
                ft.Row(
                    [
                        ft.TextButton("취소", on_click=lambda e: setattr(mangeun_popup_layer, "visible", False) or page.update()),
                        ft.TextButton("저장", on_click=on_mangeun_dropdown_changed, style=ft.ButtonStyle(color="#2563EB")),
                    ],
                    alignment="spaceBetween",
                ),
            ],
            spacing=10,
            tight=True,
        ),
        bgcolor="white",
        padding=14,
        border_radius=12,
        width=240,
    )
    mangeun_popup_layer.content = mangeun_popup_card

    # 상하단 레이아웃[cite: 2]
    def move_prev(e):
        current["month"] -= 1
        if current["month"] == 0: current["month"] = 12; current["year"] -= 1
        rebuild_interface()

    def move_next(e):
        current["month"] += 1
        if current["month"] == 13: current["month"] = 1; current["year"] += 1
        rebuild_interface()

    header_nav = ft.Row(
        [
            ft.TextButton("◀ 이전", on_click=move_prev, style=ft.ButtonStyle(color="black")),
            month_title,
            ft.TextButton("다음 ▶", on_click=move_next, style=ft.ButtonStyle(color="black")),
        ],
        alignment="spaceBetween"
    )

    mangeun_setting_row = ft.Row(
        [
            mangeun_value_text,
            ft.ElevatedButton(
                "변경",
                on_click=open_mangeun_popup,
                bgcolor="#2563EB",
                color="white",
                width=75,
                height=32,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
            ),
        ],
        alignment="start",
        vertical_alignment="center",
        spacing=6,
        height=32,
    )

    # 상단 요약 3줄만 촘촘하게 묶어 달력 구조에는 영향을 주지 않습니다.
    summary_group = ft.Column(
        [
            stats_text,
            mangeun_text,
            mangeun_setting_row,
        ],
        spacing=5,
        tight=True,
    )

    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row(
        [
            ft.Container(
                content=ft.Text(d, size=13, weight="bold", color="#D93025" if d=="일" else ("#1A73E8" if d=="토" else "black")), 
                expand=1, alignment=ft.Alignment(0, 0)
            ) for d in days_letters
        ],
        alignment="spaceAround"
    )

    # 하단 메뉴 컴포넌트 선언[cite: 2]
    bottom_navigation_bar = ft.Row(
        [
            ft.TextButton("달력", style=ft.ButtonStyle(color="#2563EB"), expand=1, height=36),
            ft.TextButton("입력", style=ft.ButtonStyle(color="grey"), expand=1, height=36),
            ft.TextButton("통계", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
            ft.TextButton("설정", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
        ],
        alignment="spaceAround"
    )

    # 상단 컨텐츠 전용 스크롤 레이아웃
    scrollable_content = ft.Column(
        [
            header_nav,
            summary_group,
            ft.Divider(height=1),
            weeks_header,        
            ft.Divider(height=1),
            calendar_grid
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )

    # 전체 화면 배치 구조 최적화[cite: 2]
    main_layout = ft.Column(
        [
            scrollable_content,       
            ft.Divider(height=1),     
            bottom_navigation_bar     
        ],
        expand=True
    )

    page.add(
        ft.Stack(
            [
                main_layout,
                popup_layer,
                mangeun_popup_layer
            ],
            expand=True
        )
    )

    rebuild_interface()

ft.app(target=main, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)
