import flet as ft
import datetime
import calendar

def main(page: ft.Page):
    page.title = "근무 달력"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    user_schedule = {}
    now = datetime.datetime.now()
    state = {"year": now.year, "month": now.month}
    calendar_container = ft.Column()

    def build_calendar():
        calendar_container.controls.clear()
        yr, mo = state["year"], state["month"]
        
        nav_row = ft.Row(
            controls=[
                ft.TextButton("◀ 이전", on_click=prev_month),
                ft.Text(f"{yr}년 {mo}월", size=24, weight=ft.FontWeight.BOLD),
                ft.TextButton("다음 ▶", on_click=next_month)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        calendar_container.controls.append(nav_row)
        
        days_row = ft.Row(
            controls=[ft.Container(ft.Text(d, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER), expand=1) for d in ["일", "월", "화", "수", "목", "금", "토"]],
            alignment=ft.MainAxisAlignment.SPACE_AROUND
        )
        calendar_container.controls.append(days_row)
        
        cal = calendar.TextCalendar(calendar.SUNDAY)
        month_days = cal.monthdayscalendar(yr, mo)
        
        for week in month_days:
            week_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND)
            for day in week:
                if day == 0:
                    week_row.controls.append(ft.Container(expand=1))
                else:
                    date_key = f"{yr}-{mo:02d}-{day:02d}"
                    current_status = user_schedule.get(date_key, "")
                    
                    bg_color = ft.Colors.WHITE
                    if current_status == "오전": bg_color = ft.Colors.BLUE_50
                    elif current_status == "오후": bg_color = ft.Colors.ORANGE_50
                    elif current_status == "휴무": bg_color = ft.Colors.RED_50
                        
                    day_card = ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(str(day), weight=ft.FontWeight.BOLD),
                                ft.Text(current_status, size=10)
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        bgcolor=bg_color,
                        border_radius=5,
                        aspect_ratio=1.0,
                        expand=1,
                        on_click=lambda e, dk=date_key: show_status_picker(dk)
                    )
                    week_row.controls.append(day_card)
            calendar_container.controls.append(week_row)
        page.update()

    def show_status_picker(date_key):
        def set_status(status_value):
            if status_value == "삭제":
                if date_key in user_schedule: del user_schedule[date_key]
            else: user_schedule[date_key] = status_value
            dialog.open = False
            build_calendar()

        dialog = ft.AlertDialog(
            title=ft.Text("근무 상태 선택"),
            content=ft.Text(f"{date_key}의 근무를 선택하세요."),
            actions=[
                ft.TextButton("오전", on_click=lambda e: set_status("오전")),
                ft.TextButton("오후", on_click=lambda e: set_status("오후")),
                ft.TextButton("휴무", on_click=lambda e: set_status("휴무")),
                ft.TextButton("삭제", on_click=lambda e: set_status("삭제")),
                ft.TextButton("취소", on_click=lambda e: setattr(dialog, "open", False) or page.update())
            ]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def prev_month(e):
        if state["month"] == 1: state["year"] -= 1; state["month"] = 12
        else: state["month"] -= 1
        build_calendar()

    def next_month(e):
        if state["month"] == 12: state["year"] += 1; state["month"] = 1
        else: state["month"] += 1
        build_calendar()

    page.add(calendar_container)
    build_calendar()

ft.app(target=main)
