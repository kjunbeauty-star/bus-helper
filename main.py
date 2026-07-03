import os
import flet as ft
import calendar
import json  # 세션에 데이터를 안전하게 문자열로 저장하기 위해 추가
from datetime import datetime, time

def main(page: ft.Page):
    # 브라우저 바 공간 확보를 위해 전체 패딩을 최소화(4px)
    page.title = "버스기사도우미"
    page.theme_mode = "light"
    page.padding = 4

    current = {"year": 2026, "month": 7, "selected_date": ""}
    
    # 선택된 시/분을 안전하게 담아둘 공간 (기본값 오전 5시 0분)
    selected_time_state = {"hour": 5, "minute": 0}

    # UI 컴포넌트 슬림화 (글자 크기 및 높이 축소)
    month_title = ft.Text("", size=20, weight="bold", text_align="center")
    stats_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    mangeun_text = ft.Text("", size=13, weight="bold", color="#1E3A8A")
    calendar_grid = ft.Column(spacing=2)

    popup_date_title = ft.Text("", size=16, weight="bold", color="black", text_align="center")
    
    # [새 기능 장착] 기사님이 고른 시간을 에러 없이 완벽하게 메모리에 가두는 함수
    def on_time_picked(e):
        if time_picker.value:
            selected_time_state["hour"] = time_picker.value.hour
            selected_time_state["minute"] = time_picker.value.minute
            # 기사님이 시간을 고르면 화면 안내 텍스트를 실시간으로 업데이트
            popup_time_display.value = f"선택된 시간: {time_picker.value.hour:02d}시 {time_picker.value.minute:02d}분"
            page.update()

    # 데이터 유실 버그가 전혀 없는 Flet 표준 24시간제 타임피커 장착
    time_picker = ft.TimePicker(
        confirm_text="확인",
        cancel_text="취소",
        error_invalid_text="올바른 시간을 입력하세요",
        hour_label="시",
        minute_label="분",
        time_picker_entry_mode=ft.TimePickerEntryMode.DIAL, # 둥근 다이얼 토글 방식 지정
        value=time(5, 0),
        on_change=on_time_picked
    )
    # 페이지 전역 오버레이에 타임피커 부품 등록
    page.overlay.append(time_picker)

    # 팝업창 안에서 현재 선택된 시간을 보여줄 텍스트 상자
    popup_time_display = ft.Text("시간을 선택해 주세요 (기본값 05:00)", size=13, weight="bold", color="blue")

    popup_layer = ft.Container(
        visible=False,
        bgcolor="#AA000000",  
        alignment=ft.Alignment(0, 0),
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
        popup_date_title.value = f"{date_key}\n근무를 등록하거나 시간을 바꾸세요"
        
        all_data = load_user_schedules()
        day_info = all_data.get(date_key, {})
        current_time = day_info.get("start_time", "")
        
        if current_time and ":" in current_time:
            h, m = map(int, current_time.split(":"))
            selected_time_state["hour"] = h
            selected_time_state["minute"] = m
            time_picker.value = time(h, m)
            popup_time_display.value = f"선택된 시간: {h:02d}시 {m:02d}분"
        else:
            selected_time_state["hour"] = 5
            selected_time_state["minute"] = 0
            time_picker.value = time(5, 0)
            popup_time_display.value = "시간을 선택해 주세요 (기본값 05:00)"
            
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

    popup_card = ft.Container(
        content=ft.Column(
            [
                popup_date_title,
                ft.Divider(height=1, color="transparent"),
                
                # [부품 대수리] 시간 선택을 위한 원터치 알람창 호출 버튼 및 안내판 배치
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.ACCESS_TIME, color="white", size=16),
                            ft.Text("시·분 알람창 열기", size=14, weight="bold", color="white")
                        ],
                        alignment="center",
                        spacing=6
                    ),
                    bgcolor="#10B981", alignment=ft.Alignment(0, 0), height=40, border_radius=6,
                    on_click=lambda e: time_picker.pick_time()
                ),
                ft.Container(content=popup_time_display, alignment=ft.Alignment(0, 0), padding=4),
                
                ft.Container(
                    content=ft.Text("위 선택한 시간으로 저장", size=15, weight="bold", color="white"),
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
                            content=ft.Text("오전", size=14, weight="bold", color="white"),
                            bgcolor="#5C93E6", alignment=ft.Alignment(0, 0), height=38, border_radius=6, expand=1,
                            on_click=lambda e: select_status_and_save("오전")
                        ),
                        ft.Container(
                            content=ft.Text("오후", size=14, weight="bold", color="white"),
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

    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row(
        [
            ft.Container(
                content=ft.Text(d, size=13, weight=ft.FontWeight.BOLD, color="#D93025" if d=="일" else ("#1A73E8" if d=="토" else "black")), 
                expand=1, alignment=ft.Alignment(0, 0)
            ) for d in days_letters
        ],
        alignment="spaceAround"
    )

    bottom_navigation_bar = ft.Row(
        [
            ft.TextButton("달력", style=ft.ButtonStyle(color="#2563EB"), expand=1, height=36),
            ft.TextButton("입력", style=ft.ButtonStyle(color="grey"), expand=1, height=36),
            ft.TextButton("통계", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
            ft.TextButton("설정", style=ft.ButtonStyle(color="grey"), expand=1, height=40),
        ],
        alignment="spaceAround"
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

ft.app(target=main, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)
