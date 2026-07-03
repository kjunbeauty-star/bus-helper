import os
import flet as ft
import calendar
import json  # 세션에 데이터를 안전하게 문자열로 저장하기 위해 추가
from datetime import datetime

def main(page: ft.Page):
    # 브라우저 바 공간 확보를 위해 전체 패딩을 최소화(4px)
    page.title = "버스기사도우미"
    page.theme_mode = "light"
    page.padding = 4

    current = {"year": 2026, "month": 7, "selected_date": ""}
    
    # 다이얼에서 선택된 시/분을 임시로 담아둘 공간 (기본값 오전 5시 0분)
    selected_time_state = {"hour": 5, "minute": 0}

    # UI 컴포넌트 슬림화 (글자 크기 및 높이 축소)
    month_title = ft.Text("", size=20, weight="bold", text_align="center")
    stats_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    calendar_grid = ft.Column(spacing=2)

    popup_date_title = ft.Text("", size=16, weight="bold", color="black", text_align="center")
    
    # [수정 완료] 복잡한 객체 대신 절대 에러 안 나는 안전한 문자열 "center" 적용
    time_label_header = ft.Row(
        [
            ft.Container(content=ft.Text("시", size=14, weight="bold", color="#1E3A8A"), expand=1, alignment="center"),
            ft.Container(content=ft.Text("분", size=14, weight="bold", color="#1E3A8A"), expand=1, alignment="center"),
        ],
        alignment="spaceAround"
    )

    # 다이얼이 굴러갈 때 실시간으로 정수형 초 단위를 시/분 변수에 정확히 각인
    def on_picker_change(e):
        total_seconds = int(e.control.value) if e.control.value is not None else (5 * 3600)
        total_minutes = total_seconds // 60
        selected_time_state["hour"] = total_minutes // 60
        selected_time_state["minute"] = total_minutes % 60

    # 영문 라벨 오류 옵션을 완전히 제거한 24시간제 위아래 회전식 토글 다이얼
    time_picker_dial = ft.CupertinoTimerPicker(
        mode=ft.CupertinoTimerPickerMode.HOUR_MINUTE,
        on_change=on_picker_change,
        value=5 * 3600,         # 기본 시작 위치를 5시간(새벽 5시)으로 세팅
        height=120,             # 팝업창 크기에 맞게 높이 최적화
    )

    # [수정 완료] 안전한 문자열 "center" 적용
    popup_layer = ft.Container(
        visible=False,
        bgcolor="#AA000000",  
        alignment="center",  
        expand=True
    )

    # [수정] 공용 DB 대신 이 기사님 핸드폰 세션에서만 장부를 읽어오는 함수
    def load_user_schedules():
        try:
            raw_data = page.session.get("user_schedules")
            if raw_data:
                return json.loads(raw_data)
            return {}
        except:
            return {}

    # [수정] 공용 DB 대신 이 기사님 핸드폰 세션에만 장부를 저장하는 함수
    def save_user_schedules(data):
        try:
            page.session.set("user_schedules", json.dumps(data))
        except:
            pass

    def rebuild_interface():
        month_title.value = f"{current['year']}년 {current['month']}월"
        
        month_prefix = f"{current['year']}-{current['month']:02d}"
        
        # [수정] DB 조회 대신 기사님 개인 세션 장부에서 이번 달 데이터만 필터링
        all_data = load_user_schedules()
        month_data = {
            k: v for k, v in all_data.items() 
            if k.startswith(month_prefix)
        }
        
        work_days = sum(1 for d in month_data.values() if d.get("status") in ["오전", "오후"])
        off_days = sum(1 for d in month_data.values() if d.get("status") == "휴무")
        
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
                    # 날짜 박스 높이를 46으로 대폭 압축하여 세로 공간 확보
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

                    # 세로 공간 확보를 위한 핵심 다이어트 (height 55 -> 46)
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
                        border_radius=4,
                        height=46,
                        expand=1,
                        on_click=lambda e, dk=date_key: open_input_popup(dk)
                    )
                    week_row.controls.append(day_box)
            calendar_grid.controls.append(week_row)
        page.update()

    def open_input_popup(date_key):
        current["selected_date"] = date_key
        popup_date_title.value = f"{date_key}\n시간을 맞추거나 근무를 누르세요"
        
        all_data = load_user_schedules()
        day_info = all_data.get(date_key, {})
        current_time = day_info.get("start_time", "")
        
        if current_time and ":" in current_time:
            h, m = map(int, current_time.split(":"))
            selected_time_state["hour"] = h
            selected_time_state["minute"] = m
            time_picker_dial.value = (h * 3600) + (m * 60)
        else:
            selected_time_state["hour"] = 5
            selected_time_state["minute"] = 0
            time_picker_dial.value = 5 * 3600
            
        popup_layer.visible = True
        page.update()

    def select_status_and_save(status_value):
        target_date = current["selected_date"]
        all_data = load_user_schedules()
        
        if status_value == "선택취소":
            if target_date in all_data:
                del all_data[target_date]
            save_user_schedules(all_data)
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

        all_data[target_date] = {"status": status_value, "start_time": final_time}
        save_user_schedules(all_data)
        
        popup_layer.visible = False  
        rebuild_interface()          

    # [원상복구 완료] 팝업 카드 레이아웃 정렬 속성 전부 문자열 "center"로 안전하게 정정
    popup_card = ft.Container(
        content=ft.Column(
            [
                popup_date_title,
                ft.Divider(height=1, color="transparent"),
                time_label_header,  
                time_picker_dial,   
                ft.Container(
                    content=ft.Text("선택한 시간으로 저장", size=15, weight="bold", color="white"),
                    bgcolor="#2563EB", alignment="center", height=44, border_radius=6,
                    on_click=lambda e: select_status_and_save("자동")
                ),
                ft.Divider(height=2),
                ft.Text("시간 없이 근무만 등록할 때:", size=11, weight="bold", color="grey"),
                ft.Container(
                    content=ft.Text("휴무 지정", size=15, weight="bold", color="white"),
                    bgcolor="#D93025", alignment="center", height=40, border_radius=6,
                    on_click=lambda e: select_status_and_save("휴무")
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("오전", size=14, weight="bold", color="white"),
                            bgcolor="#5C93E6", alignment="center", height=38, border_radius=6, expand=1,
                            on_click=lambda e: select_status_and_save("오전")
                        ),
                        ft.Container(
                            content=ft.Text("오후", size=14, weight="bold", color="white"),
                            bgcolor="#E39430", alignment="center", height=38, border_radius=6, expand=1,
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
            ft.Text("만근 기준", size=13, color="black"),
            ft.Container(
                content=ft.TextField(value="22", text_size=12, content_padding=2, text_align="center"),
                width=38, height=24
            ),
            ft.FilledButton("저장", height=24, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)))
        ],
        alignment="spaceBetween"
    )

    # [원상복구 완료] 요일 헤더의 alignment "center" 문자열 적용
    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row(
        [
            ft.Container(
                content=ft.Text(d, size=13, weight=ft.FontWeight.BOLD, color="#D93025" if d=="일" else ("#1A73E8" if d=="토" else "black")), 
                expand=1, alignment="center"
            ) for d in days_letters
        ],
        alignment="spaceAround"
    )

    # [원상복구 완료] 삭제되었던 하단 메뉴 탭 바 완벽 복원
    bottom_navigation_bar = ft.Row(
        [
            ft.TextButton("달력", style=ft.ButtonStyle(color="#2563EB"), expand=1, height=36),
            ft.TextButton("입력", style=ft.ButtonStyle(color="grey"), expand=1, height=36),
            ft.TextButton("통계", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
            ft.TextButton("설정", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
        ],
        alignment="spaceAround"
    )

    # [원상복구 완료] 메인 레이아웃의 완전한 원래 뼈대 구조로 복구
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
            bottom_navigation_bar  # 빼먹었던 메뉴바 복구 안착
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

ft.app(target=main, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)
