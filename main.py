import os
import flet as ft
import calendar
import sqlite3
from datetime import datetime

# 1. 데이터베이스 연결
conn = sqlite3.connect('bus_helper.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        date TEXT PRIMARY KEY,
        status TEXT,
        route TEXT,
        start_time TEXT,
        vehicle TEXT,
        memo TEXT
    )
''')
conn.commit()

def main(page: ft.Page):
    # 모바일 브라우저 가독성을 위해 패딩 최소화
    page.title = "버스기사도우미"
    page.theme_mode = "light"
    page.padding = 6

    current = {"year": 2026, "month": 7, "selected_date": ""}

    # UI 컴포넌트 선언
    month_title = ft.Text("", size=22, weight="bold", text_align="center")
    stats_text = ft.Text("", size=14, weight="bold", color="#1E3A8A")
    mangeun_text = ft.Text("", size=14, weight="bold", color="#1E3A8A")
    calendar_grid = ft.Column(spacing=2)

    popup_date_title = ft.Text("", size=18, weight="bold", color="black", text_align="center")
    
    start_time_input = ft.TextField(
        label="24시간제 숫자 4자리 입력",
        hint_text="예: 0535 또는 1420",
        text_size=16,
        text_align="center",
        content_padding=10
    )

    popup_layer = ft.Container(
        visible=False,
        bgcolor="#AA000000",  
        alignment=ft.Alignment(0, 0),
        expand=True
    )

    def rebuild_interface():
        month_title.value = f"{current['year']}년 {current['month']}월"
        
        month_prefix = f"{current['year']}-{current['month']:02d}"
        cursor.execute("SELECT date, status, start_time FROM schedules WHERE date LIKE ?", (f"{month_prefix}%",))
        month_data = {row[0]: {"status": row[1], "start_time": row[2] if row[2] else ""} for row in cursor.fetchall()}
        
        work_days = sum(1 for d in month_data.values() if d["status"] in ["오전", "오후"])
        off_days = sum(1 for d in month_data.values() if d["status"] == "휴무")
        
        days_in_month = calendar.monthrange(current['year'], current['month'])[1]
        m_target = 22 if days_in_month == 31 else (20 if current['month'] == 2 else 21)
        
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
                    # 좁은 화면을 위해 높이를 55로 압축
                    week_row.controls.append(ft.Container(expand=1, height=55))
                else:
                    date_key = f"{current['year']}-{current['month']:02d}-{day:02d}"
                    day_info = month_data.get(date_key, {"status": "", "start_time": ""})
                    
                    status = day_info["status"]
                    start_time = day_info["start_time"]
                    
                    bg_color = "#FFFFFF"
                    text_color = "#000000"
                    status_desc = ""
                    
                    if status == "오전":
                        bg_color = "#D2E3FC"; text_color = "#1A73E8"; status_desc = "오전"
                    elif status == "오후":
                        bg_color = "#FEEFC3"; text_color = "#E37400"; status_desc = "오후"
                    elif status == "휴무":
                        bg_color = "#FCE8E6"; text_color = "#D93025"; status_desc = "휴무"

                    time_display = ft.Text(start_time, size=10, weight="bold", color=text_color) if start_time and status != "휴무" else ft.Container()

                    # 세로 공간 다이어트 (height 68 -> 55, 자판 크기 및 여백 최적화)
                    day_box = ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(f"{day}", size=13, weight="bold", color=text_color),
                                ft.Text(status_desc, size=11, weight="bold", color=text_color),
                                time_display
                            ],
                            alignment="center",
                            horizontal_alignment="center",
                            spacing=0
                        ),
                        bgcolor=bg_color,
                        border_radius=4,
                        height=55,
                        expand=1,
                        on_click=lambda e, dk=date_key: open_input_popup(dk)
                    )
                    week_row.controls.append(day_box)
            calendar_grid.controls.append(week_row)
        page.update()

    def open_input_popup(date_key):
        current["selected_date"] = date_key
        popup_date_title.value = f"{date_key}\n시간을 적거나 근무를 누르세요"
        
        cursor.execute("SELECT start_time FROM schedules WHERE date = ?", (date_key,))
        row = cursor.fetchone()
        current_time = row[0] if row and row[0] else ""
        
        start_time_input.value = current_time.replace(":", "")
        popup_layer.visible = True
        page.update()

    def select_status_and_save(status_value):
        target_date = current["selected_date"]
        
        if status_value == "선택취소":
            cursor.execute("DELETE FROM schedules WHERE date = ?", (target_date,))
            conn.commit()
            popup_layer.visible = False  
            rebuild_interface()
            return

        input_time = start_time_input.value.strip()
        final_time = ""

        if input_time.isdigit() and len(input_time) in [3, 4]:
            if len(input_time) == 3:  
                input_time = f"0{input_time}"
            
            hour = int(input_time[:2])
            if hour >= 12:
                status_value = "오후"
            else:
                status_value = "오전"
                
            final_time = f"{input_time[:2]}:{input_time[2:]}"
        else:
            if status_value == "자동":
                return
            final_time = ""

        cursor.execute('''
            INSERT OR REPLACE INTO schedules (date, status, start_time) 
            VALUES (?, ?, ?)
        ''', (target_date, status_value, final_time))
        
        conn.commit()
        popup_layer.visible = False  
        rebuild_interface()          

    popup_card = ft.Container(
        content=ft.Column(
            [
                popup_date_title,
                ft.Divider(height=2, color="transparent"),
                start_time_input,  
                ft.Container(
                    content=ft.Text("입력한 시간으로 저장", size=16, weight="bold", color="white"),
                    bgcolor="#2563EB", alignment=ft.Alignment(0, 0), height=48, border_radius=6,
                    on_click=lambda e: select_status_and_save("자동")
                ),
                ft.Divider(height=5),
                ft.Text("시간 없이 근무만 등록할 때:", size=12, weight="bold", color="grey"),
                ft.Container(
                    content=ft.Text("휴무 지정", size=16, weight="bold", color="white"),
                    bgcolor="#D93025", alignment=ft.Alignment(0, 0), height=45, border_radius=6,
                    on_click=lambda e: select_status_and_save("휴무")
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("오전", size=15, weight="bold", color="white"),
                            bgcolor="#5C93E6", alignment=ft.Alignment(0, 0), height=42, border_radius=6, expand=1,
                            on_click=lambda e: select_status_and_save("오전")
                        ),
                        ft.Container(
                            content=ft.Text("오후", size=15, weight="bold", color="white"),
                            bgcolor="#E39430", alignment=ft.Alignment(0, 0), height=42, border_radius=6, expand=1,
                            on_click=lambda e: select_status_and_save("오후")
                        ),
                    ],
                    spacing=10
                ),
                ft.Divider(height=2, color="transparent"),
                ft.Row(
                    [
                        ft.TextButton("선택취소(삭제)", on_click=lambda e: select_status_and_save("선택취소"), style=ft.ButtonStyle(color="red")),
                        ft.TextButton("닫기", on_click=lambda e: setattr(popup_layer, "visible", False) or page.update()),
                    ],
                    alignment="spaceBetween"
                )
            ],
            spacing=8,
            tight=True
        ),
        bgcolor="white", padding=15, border_radius=12, width=310
    )
    popup_layer.content = popup_card

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
            ft.Text("만근 기준", size=14, color="black"),
            ft.Container(
                content=ft.TextField(value="22", text_size=13, content_padding=2, text_align="center"),
                width=40, height=26
            ),
            ft.FilledButton("저장", height=26, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)))
        ],
        alignment="spaceBetween"
    )

    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row(
        [
            ft.Container(
                content=ft.Text(d, size=14, weight="bold", color="#D93025" if d=="일" else ("#1A73E8" if d=="토" else "black")), 
                expand=1, alignment=ft.Alignment(0, 0)
            ) for d in days_letters
        ],
        alignment="spaceAround"
    )

    # 하단 탭 바 텍스트 버튼 정돈
    bottom_navigation_bar = ft.Row(
        [
            ft.TextButton("달력", style=ft.ButtonStyle(color="#2563EB"), expand=1, height=40),
            ft.TextButton("입력", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
            ft.TextButton("통계", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
            ft.TextButton("설정", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
        ],
        alignment="spaceAround"
    )

    # 스크롤이 가능하도록 메인 레이아웃에 scroll 옵션 추가하여 잘림 방지
    main_layout = ft.Column(
        [
            header_nav,
            stats_text,
            mangeun_text,
            mangeun_setting_row,
            ft.Divider(height=2),
            weeks_header,
            ft.Divider(height=2),
            calendar_grid,
            ft.Divider(height=5),
            bottom_navigation_bar
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO
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

# 외부 접속 허용 시동
# main.py 맨 아랫줄을 기존 것 대신 이걸로 덮어씌우세요!
ft.app(target=main, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)