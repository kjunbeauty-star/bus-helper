import os  # Render 배포 환경용 및 파일 확인 모듈
import sqlite3  # SQLite3 데이터베이스 모듈
import calendar
from datetime import datetime, timedelta, timezone
import flet as ft

# 대한민국 표준시 (GMT +9:00) 설정
KST = timezone(timedelta(hours=9))

# 데이터베이스 파일 이름 정의
DB_FILE = "schedules.db"

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
        schedules[row[0]] = {"status": row[1], "start_time": row[2]}
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

    # 데이터베이스 및 테이블 초기화 고정
    init_db()

    # 앱 시작 시 SQLite DB에서 기존 데이터 로드
    USER_SCHEDULES = load_schedules_from_db()
    MANGEUN_TARGETS = load_mangeun_targets_from_db()

    # 클립보드 알림 바 기능
    def on_copy_success(e):
        page.snack_bar = ft.SnackBar(ft.Text("백업 데이터가 클립보드에 복사되었습니다."))
        page.snack_bar.open = True
        page.update()

    # 현재 시간 세팅
    now_kst = datetime.now(KST)
    current = {"year": now_kst.year, "month": now_kst.month, "selected_date": ""}
    selected_time_state = {"hour": 5, "minute": 0}

    # 1. 컴포넌트 선언
    month_title = ft.Text("", size=20, weight="bold", text_align="center")
    stats_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    calendar_grid = ft.Column(spacing=2)
    popup_date_title = ft.Text("", size=16, weight="bold", color="black", text_align="center")
    
    # 만근 기준 드롭다운 값 변경 시 SQLite 실시간 저장
    def on_mangeun_dropdown_changed(e):
        try:
            val = int(mangeun_dropdown.value)
            key = f"{current['year']}_{current['month']}"
            MANGEUN_TARGETS[key] = val
            save_mangeun_target_to_db(key, val)
            rebuild_interface()
        except (ValueError, TypeError):
            pass

    # "만근" 옆 숫자 선택 드롭다운 (15일 ~ 26일)
    mangeun_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(str(i)) for i in range(15, 27)],
        width=80,
        height=40,
        text_size=12,
        content_padding=ft.Padding(left=8, top=0, right=8, bottom=0),
        on_change=on_mangeun_dropdown_changed
    )

    # --- 백업 및 복원 로직 ---
    backup_input_field = ft.TextField(
        label="복원할 백업 텍스트를 여기에 붙여넣으세요",
        text_size=11,
        multiline=True,
        min_lines=2,
        max_lines=4,
        expand=True
    )

    def trigger_backup_copy(e):
        """현재 데이터를 하나의 JSON 문자열로 변환하여 클립보드에 복사합니다."""
        backup_data = {
            "schedules": USER_SCHEDULES,
            "mangeun_targets": MANGEUN_TARGETS
        }
        json_str = json.dumps(backup_data, ensure_ascii=False)
        page.set_clipboard(json_str)
        on_copy_success(None)

    def trigger_restore_data(e):
        """붙여넣은 텍스트를 해독하여 데이터를 복원하고 전체 DB를 동기화 갱신합니다."""
        global USER_SCHEDULES, MANGEUN_TARGETS
        raw_text = backup_input_field.value.strip()
        if not raw_text:
            page.snack_bar = ft.SnackBar(ft.Text("복원할 텍스트가 비어 있습니다."))
            page.snack_bar.open = True
            page.update()
            return
        
        try:
            parsed_data = json.loads(raw_text)
            if "schedules" in parsed_data and "mangeun_targets" in parsed_data:
                USER_SCHEDULES = parsed_data["schedules"]
                MANGEUN_TARGETS = parsed_data["mangeun_targets"]
                
                # 복원된 전체 내역을 SQLite DB로 전체 이전 및 덮어쓰기
                for d_key, val in USER_SCHEDULES.items():
                    save_schedule_to_db(d_key, val.get("status", ""), val.get("start_time", ""))
                for m_key, val in MANGEUN_TARGETS.items():
                    save_mangeun_target_to_db(m_key, int(val))
                
                rebuild_interface()
                backup_input_field.value = ""
                page.snack_bar = ft.SnackBar(ft.Text("데이터가 데이터베이스에 성공적으로 복원되었습니다!"))
                page.snack_bar.open = True
            else:
                page.snack_bar = ft.SnackBar(ft.Text("올바른 백업 양식이 아닙니다."))
                page.snack_bar.open = True
        except Exception:
            page.snack_bar = ft.SnackBar(ft.Text("복원에 실패했습니다. 텍스트를 확인해주세요."))
            page.snack_bar.open = True
        page.update()

    # 24시간제 다이얼
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

    # 2. 데이터 제어 함수
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

    # 3. 화면 리빌드 함수 (GMT+9 서울 시간 고정 및 DB 캐시 매칭)
    def rebuild_interface():
        nonlocal USER_SCHEDULES, MANGEUN_TARGETS
        USER_SCHEDULES = load_schedules_from_db()
        MANGEUN_TARGETS = load_mangeun_targets_from_db()

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
        
        stats_text.value = f"근무 {work_days}일   휴무 {off_days}일"
        
        diff = work_days - m_target
        if diff >= 0:
            mangeun_text.value = f"만근 {m_target}일 · 기준보다 {diff}일 초과"
        else:
            mangeun_text.value = f"만근 {m_target}일 · 기준보다 {abs(diff)}일 부족"

        calendar_grid.controls.clear()
        cal = calendar.Calendar(firstweekday=6)
        month_weeks = cal.monthdayscalendar(current['year'], current['month'])
        
        for week in month_weeks:
            week_row = ft.Row(alignment="spaceAround", spacing=2)
            for day in week:
                if day == 0:
                    week_row.controls.append(ft.Container(expand=1, height=46))
                else:
                    date_key = f"{current['year']}-{current['month']:02d}-{day:02d}"
                    day_info = month_data.get(date_key, {"status": "", "start_time": ""})
                    
                    status = day_info.get("status", "")
                    start_time = day_info.get("start_time", "")
                    
                    bg_color = "#FFFFFF"
                    text_color = "#000000"
                    status_desc = ""
                    
                    if status == "오전":
                        bg_color = "#D2E3FC"; text_color = "#1A73E8"; status_desc = "오전"
                    elif status == "오후":
                        bg_color = "#FEEFC3"; text_color = "#E37400"; status_desc = "오후"
                    elif status == "휴무":
                        bg_color = "#FCE8E6"; text_color = "#D93025"; status_desc = "휴무"

                    time_display = ft.Text(start_time, size=9, weight="bold", color=text_color) if start_time and status != "휴무" else ft.Container()

                    is_today = (current['year'] == today_y and current['month'] == today_m and day == today_d)
                    day_border = ft.border.all(2, "#2563EB") if is_today else None

                    day_box = ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(f"{day}", size=12, weight="bold", color=text_color),
                                ft.Text(status_desc, size=10, weight="bold", color=text_color),
                                time_display
                            ],
                            alignment="center",
                            horizontal_alignment="center",
                            spacing=0
                        ),
                        bgcolor=bg_color,
                        border=day_border,
                        border_radius=4,
                        height=46,
                        expand=1,
                        on_click=lambda e, dk=date_key: open_input_popup(dk)
                    )
                    week_row.controls.append(day_box)
            calendar_grid.controls.append(week_row)
        page.update()

    # 4. 팝업창 제어 및 SQLite 실시간 동기화 자동 저장 함수
    def open_input_popup(date_key):
        current["selected_date"] = date_key
        popup_date_title.value = f"{date_key}\n근무를 선택하거나 시간을 맞추세요"
        
        day_info = USER_SCHEDULES.get(date_key, {})
        current_time = day_info.get("start_time", "")
        
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
            delete_schedule_from_db(target_date)
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

        save_schedule_to_db(target_date, status_value, final_time)
        
        popup_layer.visible = False  
        rebuild_interface()          

    # 5. 팝업창 디자인 구성
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
                            bgcolor="#E39430", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1,
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

    # 상하단 레이아웃 네비게이션
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
            ft.Text("만근", size=13, weight="bold", color="black"),
            mangeun_dropdown
        ],
        alignment="start",
        spacing=10
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

    # 📌 [수정 사항 4] 이전에는 화면에 바로 배치되었던 백업/복원 레이아웃 정의 (동일 기능 분리 보존)
    backup_restore_view = ft.Container(
        content=ft.Column(
            [
                ft.Text("데이터 백업 및 복원 설정", size=18, weight="bold"),
                ft.Divider(height=2),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "내 근무 데이터 백업 복사", 
                            icon=ft.icons.COPY,
                            on_click=trigger_backup_copy,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))
                        ),
                    ],
                    alignment="center"
                ),
                ft.Divider(height=1),
                backup_input_field,
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "복원하기", 
                            icon=ft.icons.RESTORE,
                            on_click=trigger_restore_data,
                            style=ft.ButtonStyle(bgcolor="#10B981", color="white", shape=ft.RoundedRectangleBorder(radius=6))
                        )
                    ],
                    alignment="center"
                )
            ],
            spacing=10
        ),
        content_padding=ft.Padding(left=10, top=16, right=10, bottom=16),
        visible=False  # 📌 초기에는 보이지 않음 (설정 선택 시에만 전환됨)
    )

    # 📌 [수정 사항 3] 달력 화면 전용 레이아웃 정의 (백업/복원 컴포넌트 완전 제외)
    calendar_main_view = ft.Column(
        [
            header_nav,
            stats_text,
            mangeun_text,
            mangeun_setting_row,
            ft.Divider(height=1),
            weeks_header,        
            ft.Divider(height=1),
            calendar_grid
        ],
        visible=True
    )

    # 📌 [수정 사항 2] 하단 탭 클릭 제어 함수 추가 (화면 분기 제어)
    def switch_tab(e):
        selected_text = e.control.text
        if selected_text == "달력":
            calendar_main_view.visible = True
            backup_restore_view.visible = False
            # 버튼 색상 하이라이트 제어
            btn_calendar.style.color = "#2563EB"
            btn_settings.style.color = "grey"
            rebuild_interface()
        elif selected_text == "설정":
            calendar_main_view.visible = False
            backup_restore_view.visible = True
            # 버튼 색상 하이라이트 제어
            btn_calendar.style.color = "grey"
            btn_settings.style.color = "#2563EB"
        page.update()

    # 하단 탭 내비게이션 버튼들 선언
    btn_calendar = ft.TextButton("달력", style=ft.ButtonStyle(color="#2563EB"), expand=1, height=36, on_click=switch_tab)
    btn_settings = ft.TextButton("설정", style=ft.ButtonStyle(color="grey"), expand=1, height=40, on_click=switch_tab)

    bottom_navigation_bar = ft.Row(
        [
            btn_calendar,
            ft.TextButton("입력", style=ft.ButtonStyle(color="grey"), expand=1, height=36),
            ft.TextButton("통계", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
            btn_settings,
        ],
        alignment="spaceAround"
    )

    # 전체 컨텐츠 영역 묶음 구조 정의
    content_container = ft.Column(
        [
            calendar_main_view,
            backup_restore_view
        ],
        expand=True
    )

    main_layout = ft.Column(
        [
            content_container,
            ft.Divider(height=2),
            bottom_navigation_bar 
        ],
        expand=True
    )

    page.add(
        ft.Stack(
            [
                main_layout,
                popup_layer
            ],
            expand=True
        )
    )

    rebuild_interface()

import json  # 백업 구조 파싱 모듈 고정
ft.app(target=main, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)
