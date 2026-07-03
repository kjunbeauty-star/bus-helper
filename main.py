import flet as ft
import datetime
import calendar
import os  # [엔진 복원] Render 서버 구동에 필수적인 모듈

def main(page: ft.Page):
    page.title = "근무 달력"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    page.update()

    # 상단 바 및 배경 테마 상세 설정 복원
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    now = datetime.datetime.now()
    state = {
        "year": now.year,
        "month": now.month
    }

    calendar_container = ft.Column()

    # [핵심] 각자 핸드폰 브라우저 세션에서 장부를 안전하게 읽어오는 함수
    def load_user_data():
        try:
            data = page.session.get("my_bus_schedule")
            return data if data else {}
        except:
            return {}

    # [핵심] 각자 핸드폰 브라우저 세션에 장부를 안전하게 저장하는 함수
    def save_user_data(data):
        try:
            page.session.set("my_bus_schedule", data)
        except:
            pass

    def build_calendar():
        calendar_container.controls.clear()
        
        yr = state["year"]
        mo = state["month"]
        
        # 상단 내비게이션 바 디자인 디테일 설정
        nav_row = ft.Row(
            controls=[
                ft.TextButton("◀ 이전", on_click=prev_month, style=ft.ButtonStyle(color=ft.Colors.BLUE_700)),
                ft.Text(f"{yr}년 {mo}월", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ft.TextButton("다음 ▶", on_click=next_month, style=ft.ButtonStyle(color=ft.Colors.BLUE_700))
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            width=360
        )
        calendar_container.controls.append(nav_row)
        
        # 요일 헤더의 폰트 크기 및 색상 디테일 설정
        days_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(d, size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK54),
                    expand=1
                ) for d in ["일", "월", "화", "수", "목", "금", "토"]
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            width=360
        )
        calendar_container.controls.append(days_row)
        
        # 달력 날짜 생성 구조
        cal = calendar.TextCalendar(calendar.SUNDAY)
        month_days = cal.monthdayscalendar(yr, mo)
        
        # 이 핸드폰 사용자의 장부만 쏙 빼오기 (서로 절대 안 섞임)
        current_user_schedule = load_user_data()
        
        for week in month_days:
            week_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND, width=360)
            for day in week:
                if day == 0:
                    week_row.controls.append(ft.Container(expand=1))
                else:
                    date_key = f"{yr}-{mo:02d}-{day:02d}"
                    current_status = current_user_schedule.get(date_key, "")
                    
                    # 각 근무별 글자 색상과 부드러운 배경색 매칭 로직 완벽 복원
                    bg_color = ft.Colors.WHITE
                    text_color = ft.Colors.BLACK87
                    if current_status == "오전":
                        bg_color = ft.Colors.BLUE_50
                        text_color = ft.Colors.BLUE_700
                    elif current_status == "오후":
                        bg_color = ft.Colors.ORANGE_50
                        text_color = ft.Colors.ORANGE_700
                    elif current_status == "휴무":
                        bg_color = ft.Colors.RED_50
                        text_color = ft.Colors.RED_700
                        
                    day_card = ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(str(day), size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                                ft.Text(current_status, size=11, weight=ft.FontWeight.BOLD, color=text_color)
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4
                        ),
                        bgcolor=bg_color,
                        border=ft.border.all(0.5, ft.Colors.BLACK12),
                        border_radius=8,
                        aspect_ratio=1.0,
                        expand=1,
                        padding=4,
                        on_click=lambda e, dk=date_key: show_status_picker(dk)
                    )
                    week_row.controls.append(day_card)
            calendar_container.controls.append(week_row)
            
        page.update()

    def show_status_picker(date_key):
        def set_status(status_value):
            current_user_schedule = load_user_data()
            if status_value == "삭제":
                if date_key in current_user_schedule:
                    del current_user_schedule[date_key]
            else:
                current_user_schedule[date_key] = status_value
                
            save_user_data(current_user_schedule) # 이 폰 세션에만 저장
            dialog.open = False
            page.update()
            build_calendar()

        # 가로로 정렬된 입체적인 버튼(ElevatedButton) 구조 복원
        dialog = ft.AlertDialog(
            title=ft.Text("근무 상태 선택", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text(f"{date_key}의 근무를 선택하세요.", size=14),
            actions=[
                ft.Column([
                    ft.Row([
                        ft.ElevatedButton("오전", on_click=lambda e: set_status("오전"), bgcolor=ft.Colors.BLUE_50, color=ft.Colors.BLUE_700),
                        ft.ElevatedButton("오후", on_click=lambda e: set_status("오후"), bgcolor=ft.Colors.ORANGE_50, color=ft.Colors.ORANGE_700),
                        ft.ElevatedButton("휴무", on_click=lambda e: set_status("휴무"), bgcolor=ft.Colors.RED_50, color=ft.Colors.RED_700),
                        ft.ElevatedButton("삭제", on_click=lambda e: set_status("삭제"), bgcolor=ft.Colors.GREY_200, color=ft.Colors.BLACK54),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
                    ft.Row([
                        ft.TextButton("취소", on_click=lambda e: setattr(dialog, "open", False) or page.update())
                    ], alignment=ft.MainAxisAlignment.END)
                ], spacing=10)
            ]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def prev_month(e):
        if state["month"] == 1:
            state["year"] -= 1
            state["month"] = 12
        else:
            state["month"] -= 1
        build_calendar()

    def next_month(e):
        if state["month"] == 12:
            state["year"] += 1
            state["month"] = 1
        else:
            state["month"] += 1
        build_calendar()

    page.add(calendar_container)
    build_calendar()

# Render 서버 환경 및 개별 웹 브라우저 뷰 모드 완벽 연동
ft.app(target=main, port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)
