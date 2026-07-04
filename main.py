import os
import flet as ft
import calendar
from datetime import datetime, timedelta, timezone
import json

# --- [개인화] 서울 표준시 (GMT +9) 설정 ---
KST = timezone(timedelta(hours=9))

def main(page: ft.Page):
    page.title = "버스기사도우미"
    page.theme_mode = "light"
    page.padding = 4

    # 현재 날짜 기준 설정 (서울 시각 기준)
    now_kst = datetime.now(KST)
    current = {"year": now_kst.year, "month": now_kst.month, "selected_date": ""}
    selected_time_state = {"hour": 5, "minute": 0}

# --- [새로 붙여넣을 코드] 서버 리셋 방지용 브라우저 스토리지 로직 ---
    def load_data():
        global USER_SCHEDULES, MANGEUN_TARGETS
        try:
            schedules_raw = page.run_javascript_return("localStorage.getItem('user_schedules')")
            mangeun_raw = page.run_javascript_return("localStorage.getItem('mangeun_targets')")
            
            USER_SCHEDULES = json.loads(schedules_raw) if schedules_raw else {}
            MANGEUN_TARGETS = json.loads(mangeun_raw) if mangeun_raw else {}
        except Exception:
            USER_SCHEDULES = {}
            MANGEUN_TARGETS = {}

    def save_data_to_storage():
        try:
            schedules_json = json.dumps(USER_SCHEDULES, ensure_ascii=False)
            mangeun_json = json.dumps(MANGEUN_TARGETS, ensure_ascii=False)
            
            page.run_javascript(f"localStorage.setItem('user_schedules', '{schedules_json}');")
            page.run_javascript(f"localStorage.setItem('mangeun_targets', '{mangeun_json}');")
        except Exception as e:
            print(f"저장 실패: {e}")

    # 최초 실행 시 데이터 불러오기
    load_data()

    # 컴포넌트 선언
    month_title = ft.Text("", size=20, weight="bold", text_align="center")
    stats_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    calendar_grid = ft.Column(spacing=2)

    popup_date_title = ft.Text("", size=16, weight="bold", color="black", text_align="center")
    
    mangeun_setting_field = ft.TextField(
        value=str(MANGEUN_TARGETS.get(f"{current['year']}-{current['month']}", 22)), 
        text_size=12, 
        content_padding=2, 
        text_align="center"
    )

    # 대화상자(Confirm) 닫기용
    def close_confirm_dialog(e):
        confirm_dialog.open = False
        page.update()

    # 실제 저장 로직 수행 (확인 버튼 클릭 시)
    def handle_save_confirmed(e):
        confirm_dialog.open = False
        save_data_to_storage()
        page.show_snack_bar(ft.SnackBar(ft.Text("근무 상태가 기기에 안전하게 저장되었습니다!"), open=True))
        page.update()

    # 저장 확인 팝업창 (AlertDialog)
    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("변경사항 저장"),
        content=ft.Text("현재까지 입력된 근무 상태와 만근 설정을 저장하시겠습니까?\n저장 후에는 서버가 리셋되어도 유지됩니다."),
        actions=[
            ft.TextButton("취소", on_click=close_confirm_dialog),
            ft.TextButton("확인", on_click=handle_save_confirmed, style=ft.ButtonStyle(color="blue")),
        ],
        actions_alignment="end",
    )
    page.dialog = confirm_dialog

    # 메인창 저장 버튼 클릭 이벤트
    def on_main_save_click(e):
        # 현재 만근 기준일 수도 딕셔너리에 실시간 반영 후 팝업 띄움
        month_key = f"{current['year']}-{current['month']}"
        try:
            MANGEUN_TARGETS[month_key] = int(mangeun_setting_field.value)
        except ValueError:
            MANGEUN_TARGETS[month_key] = 22
        
        confirm_dialog.open = True
        page.update()

    # 일정 입력용 팝업 다이얼로그 선언
    schedule_dialog = ft.AlertDialog(title=ft.Text("근무 설정"))

    def open_schedule_popup(date_str):
        current["selected_date"] = date_str
        popup_date_title.value = f"{date_str} 근무 선택"
        
        current_status = USER_SCHEDULES.get(date_str, {}).get("status", "미설정")
        current_time = USER_SCHEDULES.get(date_str, {}).get("time", "05:00")
        
        try:
            h, m = map(int, current_time.split(":"))
        except:
            h, m = 5, 0
        selected_time_state["hour"] = h
        selected_time_state["minute"] = m

        def set_status(status_name):
            if date_str not in USER_SCHEDULES:
                USER_SCHEDULES[date_str] = {}
            USER_SCHEDULES[date_str]["status"] = status_name
            USER_SCHEDULES[date_str]["time"] = f"{selected_time_state['hour']:02d}:{selected_time_state['minute']:02d}"
            schedule_dialog.open = False
            update_calendar()

        def delete_status(e):
            if date_str in USER_SCHEDULES:
                del USER_SCHEDULES[date_str]
            schedule_dialog.open = False
            update_calendar()

        def on_time_change(hour_delta, minute_delta):
            selected_time_state["hour"] = (selected_time_state["hour"] + hour_delta) % 24
            selected_time_state["minute"] = (selected_time_state["minute"] + minute_delta) % 60
            time_text.value = f"{selected_time_state['hour']:02d}:{selected_time_state['minute']:02d}"
            if date_str in USER_SCHEDULES:
                USER_SCHEDULES[date_str]["time"] = time_text.value
            page.update()

        time_text = ft.Text(f"{selected_time_state['hour']:02d}:{selected_time_state['minute']:02d}", size=20, weight="bold")

        schedule_dialog.content = ft.Container(
            content=ft.Column(
                [
                    popup_date_title,
                    ft.Divider(),
                    ft.Text("근무 종류 선택", weight="bold"),
                    ft.Row([
                        ft.ElevatedButton("오전", bgcolor="#E3F2FD", color="#1E88E5", on_click=lambda _: set_status("오전"), expand=1),
                        ft.ElevatedButton("오후", bgcolor="#FFF3E0", color="#F4511E", on_click=lambda _: set_status("오후"), expand=1),
                        ft.ElevatedButton("휴무", bgcolor="#E8F5E9", color="#43A047", on_click=lambda _: set_status("휴무"), expand=1),
                    ], alignment="center"),
                    ft.Divider(),
                    ft.Text("출근 시간 설정", weight="bold"),
                    ft.Row([
                        ft.IconButton(ft.icons.REMOVE, on_click=lambda _: on_time_change(-1, 0)),
                        ft.IconButton(ft.icons.KEYBOARD_ARROW_DOWN, on_click=lambda _: on_time_change(0, -10)),
                        time_text,
                        ft.IconButton(ft.icons.KEYBOARD_ARROW_UP, on_click=lambda _: on_time_change(0, 10)),
                        ft.IconButton(ft.icons.ADD, on_click=lambda _: on_time_change(1, 0)),
                    ], alignment="center"),
                    ft.Divider(),
                    ft.ElevatedButton("근무 삭제", bgcolor="#FFEBEE", color="#E53935", on_click=delete_status, width=200),
                ],
                tight=True,
                horizontal_alignment="center",
                spacing=10
            ),
            width=300,
            padding=10
        )
        schedule_dialog.open = True
        page.update()

    def update_calendar():
        year = current["year"]
        month = current["month"]
        
        month_title.value = f"{year}년 {month}월"
        month_key = f"{year}-{month}"
        
        # 만근 기준일 가져오기
        target_mangeun = MANGEUN_TARGETS.get(month_key, 22)
        mangeun_setting_field.value = str(target_mangeun)

        # 달력 날짜 계산
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(year, month)

        # 통계 계산
        work_days = 0
        off_days = 0
        for d in range(1, 32):
            date_key = f"{year}-{month:02d}-{d:02d}"
            if date_key in USER_SCHEDULES:
                status = USER_SCHEDULES[date_key].get("status", "")
                if status in ["오전", "오후"]:
                    work_days += 1
                elif status == "휴무":
                    off_days += 1

        stats_text.value = f"📊 이번 달 근무 현황: 총 {work_days}일 출근 / 휴무 {off_days}일"
        
        diff = work_days - target_mangeun
        if diff >= 0:
            mangeun_text.value = f"🎉 만근 달성! 기준({target_mangeun}일)보다 {diff}일 더 근무하셨습니다."
            mangeun_text.color = "green"
        else:
            mangeun_text.value = f"⚠️ 만근까지 {abs(diff)}일 부족합니다. (기준: {target_mangeun}일)"
            mangeun_text.color = "red"

        # 그리드 초기화 후 다시 그리기
        calendar_grid.controls.clear()
        
        # 오늘 날짜 하이라이트용 (서울시각 기준)
        today_str = datetime.now(KST).strftime("%Y-%m-%d")

        for week in month_days:
            week_row = ft.Row(alignment="spaceAround", spacing=2)
            for day in week:
                if day == 0:
                    week_row.controls.append(ft.Container(expand=1, height=55))
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    schedule = USER_SCHEDULES.get(date_str, {})
                    status = schedule.get("status", "")
                    time_str = schedule.get("time", "")

                    # 상태별 색상 테마
                    bg_color = "white"
                    text_color = "black"
                    border_style = None
                    display_text = f"{day}"

                    if status == "오전":
                        bg_color = "#E3F2FD"
                        text_color = "#1E88E5"
                        display_text = f"{day}\n오전\n{time_str}"
                    elif status == "오후":
                        bg_color = "#FFF3E0"
                        text_color = "#F4511E"
                        display_text = f"{day}\n오후\n{time_str}"
                    elif status == "휴무":
                        bg_color = "#E8F5E9"
                        text_color = "#43A047"
                        display_text = f"{day}\n휴무"

                    # 오늘 날짜 강조 표시 테두리
                    if date_str == today_str:
                        border_style = ft.border.all(2, "#6200EE")

                    day_box = ft.Container(
                        content=ft.Text(display_text, size=11, weight="bold", color=text_color, text_align="center"),
                        alignment=ft.alignment.center,
                        expand=1,
                        height=55,
                        bgcolor=bg_color,
                        border=border_style,
                        border_radius=4,
                        on_click=lambda e, d_str=date_str: open_schedule_popup(d_str)
                    )
                    week_row.controls.append(day_box)
            calendar_grid.controls.add(week_row)
        
        page.update()

    def change_month(delta):
        current["month"] += delta
        if current["month"] > 12:
            current["month"] = 1
            current["year"] += 1
        elif current["month"] < 1:
            current["month"] = 12
            current["year"] -= 1
        update_calendar()

# ▼▼▼ [수정 후 코드] 들여쓰기 공백을 맞춰서 그대로 붙여넣어 주세요 ▼▼▼
    # 상단 네비게이션 바 (호환성 100% 문자열 아이콘으로 최종 교체)
    header_nav = ft.Row(
        [
            ft.IconButton(icon="arrow_back", on_click=lambda _: change_month(-1), icon_size=24),
            month_title,
            ft.IconButton(icon="arrow_forward", on_click=lambda _: change_month(1), icon_size=24),
        ],
        alignment="center"
    )

    # 만근일수 수동 설정 영역
    mangeun_setting_row = ft.Row(
        [
            ft.Text("이번 달 만근 기준일수 직접 설정:", size=11, color="grey"),
            ft.Container(content=mangeun_setting_field, width=40, height=25),
            ft.Text("일", size=11, color="grey"),
            ft.TextButton("반영", on_click=lambda _: update_calendar(), style=ft.ButtonStyle(padding=2))
        ],
        alignment="center"
    )

    # 요일 헤더
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

    # 하단 탭 내비게이션 바
    bottom_navigation_bar = ft.Row(
        [
            ft.TextButton("달력", style=ft.ButtonStyle(color="#2563EB"), expand=1, height=36),
            ft.TextButton("입력", style=ft.ButtonStyle(color="grey"), expand=1, height=36),
            ft.TextButton("통계", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
            ft.TextButton("설정", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
        ],
        alignment="spaceAround"
    )

 # 신규 추가된 메인 저장 버튼 (호환성 100% 문자열 아이콘으로 최종 교체)
    save_main_button = ft.ElevatedButton(
        text="현재 설정 및 근무 저장하기",
        icon="save",  # <- 대문자 ft.icons.SAVE를 소문자 "save"로 확실하게 고쳤습니다!
        bgcolor="#2563EB",
        color="white",
        on_click=on_main_save_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
        height=40
    )

    main_layout = ft.Column(
        [
            header_nav,
            stats_text,
            mangeun_text,
            mangeun_setting_row,
            ft.Divider(height=1),
            weeks_header,        
            ft.Divider(height=1),
            calendar_grid,       
            ft.Divider(height=2),
            ft.Row([save_main_button], alignment="center"),  # 저장 버튼 추가 위치
            ft.Divider(height=1),
            bottom_navigation_bar
        ],
        scroll="auto"
    )

    page.add(main_layout)
    page.overlay.append(schedule_dialog)
    update_calendar()

if __name__ == "__main__":
    # 웹서버 형태로 구동되도록 설정 유지
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
