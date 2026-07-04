import os  # Render 배포 환경의 PORT 값을 읽기 위해 사용
import json  # 브라우저 저장소에 딕셔너리 데이터를 저장하기 위해 사용
import calendar
from datetime import datetime, timedelta, timezone

import flet as ft


# --- [기본 설정값] ---
KST = timezone(timedelta(hours=9))  # 대한민국 표준시(GMT+9)

# 브라우저/폰 저장소 키
STORAGE_SCHEDULES_KEY = "bus_helper_schedules"
STORAGE_MANGEUN_KEY = "bus_helper_mangeun_targets"
STORAGE_WORK_TYPE_KEY = "bus_helper_work_type"

# 근무 형태
WORK_TYPE_SHIFT = "교대제"
WORK_TYPE_ALT_DAY = "격일제"

# 근무 상태
STATUS_AM = "오전"
STATUS_PM = "오후"
STATUS_FULL = "전일"
STATUS_OFF = "휴무"
STATUS_AUTO = "자동"
STATUS_CANCEL = "선택취소"

# 공통 색상
COLOR_PRIMARY = "#2563EB"
COLOR_DARK_BLUE = "#1E3A8A"
COLOR_AM_BG = "#D2E3FC"
COLOR_AM_TEXT = "#1A73E8"
COLOR_PM_BG = "#E9D5FF"
COLOR_PM_TEXT = "#7E22CE"
COLOR_FULL_BG = "#FEF3C7"
COLOR_FULL_TEXT = "#D97706"
COLOR_OFF_BG = "#FCE8E6"
COLOR_OFF_TEXT = "#D93025"
COLOR_SUCCESS = "#10B981"
COLOR_BORDER = "#E2E8F0"
COLOR_WHITE = "#FFFFFF"
COLOR_BLACK = "#000000"
COLOR_GREY = "grey"
COLOR_OVERLAY = "#AA000000"
COLOR_TRANSPARENT = "transparent"


def main(page: ft.Page):
    page.title = "버스기사도우미"
    page.theme_mode = "light"
    page.padding = 4

    def load_json_from_storage(storage_key, default_value):
        """브라우저 저장소에서 JSON 문자열을 읽고, 문제가 있으면 기본값을 반환합니다."""
        saved_value = page.client_storage.get(storage_key)
        if not saved_value:
            return default_value
        try:
            return json.loads(saved_value)
        except (json.JSONDecodeError, TypeError):
            return default_value

    # 브라우저/폰 저장소에서 기존 데이터 로드
    USER_SCHEDULES = load_json_from_storage(STORAGE_SCHEDULES_KEY, {})
    MANGEUN_TARGETS = load_json_from_storage(STORAGE_MANGEUN_KEY, {})
    saved_work_type = page.client_storage.get(STORAGE_WORK_TYPE_KEY)
    CURRENT_WORK_TYPE = saved_work_type if saved_work_type else WORK_TYPE_SHIFT

    def save_all_to_client_storage():
        """현재 근무표와 만근 기준을 브라우저/폰 저장소에 저장합니다."""
        page.client_storage.set(STORAGE_SCHEDULES_KEY, json.dumps(USER_SCHEDULES, ensure_ascii=False))
        page.client_storage.set(STORAGE_MANGEUN_KEY, json.dumps(MANGEUN_TARGETS, ensure_ascii=False))

    # 현재 시간 세팅
    now_kst = datetime.now(KST)
    current = {"year": now_kst.year, "month": now_kst.month, "selected_date": ""}
    selected_time_state = {"hour": 5, "minute": 0}

    # 중앙 화면 제어용 컨테이너
    content_area = ft.Container(expand=True)

    # --- [컴포넌트 선언] ---
    month_title = ft.Text("", size=20, weight="bold", text_align="center")
    stats_text = ft.Text("", size=13, weight="bold", color=COLOR_DARK_BLUE)
    mangeun_text = ft.Text("", size=13, weight="bold", color=COLOR_DARK_BLUE)
    calendar_grid = ft.Column(spacing=2)
    popup_date_title = ft.Text("", size=16, weight="bold", color=COLOR_BLACK, text_align="center")
    save_status_text = ft.Text("", size=14, weight="bold", color=COLOR_SUCCESS)

    # 순번 입력 Dropdown (1~50 및 선택 안 함)
    order_options = [ft.dropdown.Option("", "선택 안 함")] + [ft.dropdown.Option(str(i), f"{i}번") for i in range(1, 51)]
    order_dropdown = ft.Dropdown(
        options=order_options,
        width=140,
        height=40,
        text_size=13,
        content_padding=ft.padding.symmetric(vertical=4, horizontal=10),
    )

    def on_mangeun_dropdown_changed(e):
        """만근 기준 드롭다운 값 변경 시 즉시 저장하고 달력을 갱신합니다."""
        try:
            val = int(mangeun_dropdown.value)
            key = f"{current['year']}_{current['month']}"
            MANGEUN_TARGETS[key] = val
            save_all_to_client_storage()
            rebuild_interface()
        except (ValueError, TypeError):
            pass

    mangeun_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(str(i)) for i in range(10, 27)],
        width=80,
        height=40,
        text_size=12,
        content_padding=8,
        on_change=on_mangeun_dropdown_changed,
    )

    def update_hour(val):
        selected_time_state["hour"] = val

    def update_minute(val):
        selected_time_state["minute"] = val

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

    dial_row = ft.Row(
        [hour_picker, ft.Text(":", size=20, weight="bold", color=COLOR_BLACK), minute_picker],
        alignment="center",
        height=100,
    )

    popup_layer = ft.Container(
        visible=False,
        bgcolor=COLOR_OVERLAY,
        alignment=ft.Alignment(0, 0),
        expand=True,
    )

    def close_popup():
        """입력 팝업을 닫습니다."""
        popup_layer.visible = False
        page.update()

    # --- [데이터 계산 함수] ---
    def get_mangeun_target():
        """저장된 월별 만근 기준이 있으면 사용하고, 없으면 기본 기준을 반환합니다."""
        try:
            y, m = int(current["year"]), int(current["month"])
            key = f"{y}_{m}"
            if key in MANGEUN_TARGETS:
                return int(MANGEUN_TARGETS[key])

            days_in_month = calendar.monthrange(y, m)[1]
            if days_in_month == 31:
                return 22
            if m == 2:
                return 20
            return 21
        except (ValueError, TypeError):
            return 22

    def rebuild_interface(update_page=True):
        """달력, 통계, 만근 표시를 현재 데이터 기준으로 다시 그립니다."""
        today = datetime.now(KST)
        today_y, today_m, today_d = today.year, today.month, today.day

        month_title.value = f"{current['year']}년 {current['month']}월"
        month_prefix = f"{current['year']}-{current['month']:02d}"
        month_data = {k: v for k, v in USER_SCHEDULES.items() if k.startswith(month_prefix)}

        # 만근 근무일 계산: 오전/오후/전일은 근무일, 휴무는 휴무일로 계산
        work_days = sum(1 for d in month_data.values() if d.get("status") in [STATUS_AM, STATUS_PM, STATUS_FULL])
        off_days = sum(1 for d in month_data.values() if d.get("status") == STATUS_OFF)

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
        month_weeks = cal.monthdayscalendar(current["year"], current["month"])

        for week in month_weeks:
            week_row = ft.Row(alignment="spaceAround", spacing=2)
            for day in week:
                if day == 0:
                    week_row.controls.append(ft.Container(expand=1, height=48))
                    continue

                date_obj = datetime(current["year"], current["month"], day)
                weekday = date_obj.weekday()
                date_key = f"{current['year']}-{current['month']:02d}-{day:02d}"
                day_info = month_data.get(date_key, {"status": "", "start_time": "", "order_no": ""})

                status = day_info.get("status", "")
                start_time = day_info.get("start_time", "")
                order_no = day_info.get("order_no", "")

                bg_color = COLOR_WHITE
                text_color = COLOR_BLACK
                status_desc = ""

                if status == STATUS_AM:
                    bg_color, text_color = COLOR_AM_BG, COLOR_AM_TEXT
                    status_desc = f"{STATUS_AM}({order_no})" if order_no else STATUS_AM
                elif status == STATUS_PM:
                    bg_color, text_color = COLOR_PM_BG, COLOR_PM_TEXT
                    status_desc = f"{STATUS_PM}({order_no})" if order_no else STATUS_PM
                elif status == STATUS_FULL:
                    bg_color, text_color = COLOR_FULL_BG, COLOR_FULL_TEXT
                    status_desc = f"{STATUS_FULL}({order_no})" if order_no else STATUS_FULL
                elif status == STATUS_OFF:
                    bg_color, text_color = COLOR_OFF_BG, COLOR_OFF_TEXT
                    status_desc = STATUS_OFF

                day_number_color = COLOR_OFF_TEXT if weekday == 6 else (COLOR_AM_TEXT if weekday == 5 else text_color)
                time_display = ft.Text(start_time, size=9, weight="bold", color=text_color) if start_time and status != STATUS_OFF else ft.Container()

                is_today = current["year"] == today_y and current["month"] == today_m and day == today_d
                day_border = ft.border.all(2, COLOR_PRIMARY) if is_today else None

                day_box = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(f"{day}", size=12, weight="bold", color=day_number_color),
                            ft.Text(status_desc, size=10, weight="bold", color=text_color),
                            time_display,
                        ],
                        alignment="center",
                        horizontal_alignment="center",
                        spacing=0,
                    ),
                    bgcolor=bg_color,
                    border=day_border,
                    border_radius=4,
                    height=48,
                    expand=1,
                    on_click=lambda e, dk=date_key: open_input_popup(dk),
                )
                week_row.controls.append(day_box)
            calendar_grid.controls.append(week_row)

        if update_page:
            page.update()

    # --- [팝업창 제어 및 데이터 저장 함수] ---
    def open_input_popup(date_key):
        current["selected_date"] = date_key
        popup_date_title.value = f"{date_key}\n근무를 선택하거나 시간을 맞추세요"

        day_info = USER_SCHEDULES.get(date_key, {})
        current_time = day_info.get("start_time", "")
        current_order = day_info.get("order_no", "")
        order_dropdown.value = str(current_order) if current_order else ""

        if current_time and ":" in current_time:
            h, m = map(int, current_time.split(":"))
            selected_time_state["hour"], selected_time_state["minute"] = h, m
            hour_picker.selected_index, minute_picker.selected_index = h, m
        else:
            selected_time_state["hour"], selected_time_state["minute"] = 5, 0
            hour_picker.selected_index, minute_picker.selected_index = 5, 0

        current_work_mode = page.client_storage.get(STORAGE_WORK_TYPE_KEY) or WORK_TYPE_SHIFT
        if current_work_mode == WORK_TYPE_SHIFT:
            shift_buttons_row.visible = True
            full_day_button_container.visible = False
        else:
            shift_buttons_row.visible = False
            full_day_button_container.visible = True

        popup_layer.visible = True
        page.update()

    def select_status_and_save(status_value):
        target_date = current["selected_date"]

        if status_value == STATUS_CANCEL:
            USER_SCHEDULES.pop(target_date, None)
            save_all_to_client_storage()
            popup_layer.visible = False
            rebuild_interface()
            return

        final_time = ""
        if status_value == STATUS_AUTO:
            h, m = selected_time_state["hour"], selected_time_state["minute"]
            current_work_mode = page.client_storage.get(STORAGE_WORK_TYPE_KEY) or WORK_TYPE_SHIFT
            status_value = STATUS_FULL if current_work_mode == WORK_TYPE_ALT_DAY else (STATUS_PM if h >= 12 else STATUS_AM)
            final_time = f"{h:02d}:{m:02d}"

        input_order = "" if status_value == STATUS_OFF else (order_dropdown.value if order_dropdown.value else "")

        USER_SCHEDULES[target_date] = {
            "status": status_value,
            "start_time": final_time,
            "order_no": input_order,
        }
        save_all_to_client_storage()
        popup_layer.visible = False
        rebuild_interface()

    # --- [팝업창 버튼 구성] ---
    shift_buttons_row = ft.Row(
        [
            ft.Container(
                content=ft.Text("오전조 등록", size=14, weight="bold", color="white"),
                bgcolor=COLOR_AM_TEXT,
                alignment=ft.Alignment(0, 0),
                height=38,
                border_radius=6,
                expand=1,
                on_click=lambda e: select_status_and_save(STATUS_AM),
            ),
            ft.Container(
                content=ft.Text("오후조 등록", size=14, weight="bold", color="white"),
                bgcolor=COLOR_PM_TEXT,
                alignment=ft.Alignment(0, 0),
                height=38,
                border_radius=6,
                expand=1,
                on_click=lambda e: select_status_and_save(STATUS_PM),
            ),
        ],
        spacing=10,
    )

    full_day_button_container = ft.Container(
        content=ft.Text("전일근무 등록", size=14, weight="bold", color="white"),
        bgcolor=COLOR_FULL_TEXT,
        alignment=ft.Alignment(0, 0),
        height=38,
        border_radius=6,
        on_click=lambda e: select_status_and_save(STATUS_FULL),
        visible=False,
    )

    popup_card = ft.Container(
        content=ft.Column(
            [
                ft.Row([popup_date_title], alignment="center"),
                ft.Divider(height=1, color=COLOR_TRANSPARENT),
                dial_row,
                ft.Container(
                    content=ft.Text("선택한 시간으로 저장", size=15, weight="bold", color="white"),
                    bgcolor=COLOR_PRIMARY,
                    alignment=ft.Alignment(0, 0),
                    height=44,
                    border_radius=6,
                    on_click=lambda e: select_status_and_save(STATUS_AUTO),
                ),
                ft.Divider(height=2),
                ft.Row(
                    [ft.Text("근무 순번:", size=12, weight="bold", color=COLOR_BLACK), order_dropdown],
                    alignment="center",
                    spacing=10,
                ),
                ft.Divider(height=2),
                ft.Text("시간 없이 근무만 등록할 때:", size=11, weight="bold", color=COLOR_GREY),
                ft.Container(
                    content=ft.Text("휴무 지정", size=15, weight="bold", color="white"),
                    bgcolor=COLOR_OFF_TEXT,
                    alignment=ft.Alignment(0, 0),
                    height=40,
                    border_radius=6,
                    on_click=lambda e: select_status_and_save(STATUS_OFF),
                ),
                shift_buttons_row,
                full_day_button_container,
                ft.Divider(height=1, color=COLOR_TRANSPARENT),
                ft.Row(
                    [
                        ft.TextButton(
                            "선택취소(삭제)",
                            on_click=lambda e: select_status_and_save(STATUS_CANCEL),
                            style=ft.ButtonStyle(color="red"),
                        ),
                        ft.TextButton("닫기", on_click=lambda e: close_popup()),
                    ],
                    alignment="spaceBetween",
                ),
            ],
            spacing=6,
            tight=True,
        ),
        bgcolor="white",
        padding=12,
        border_radius=12,
        width=300,
    )
    popup_layer.content = popup_card

    # --- [달력 화면 구성] ---
    def move_prev(e):
        current["month"] -= 1
        if current["month"] == 0:
            current["month"] = 12
            current["year"] -= 1
        rebuild_interface()

    def move_next(e):
        current["month"] += 1
        if current["month"] == 13:
            current["month"] = 1
            current["year"] += 1
        rebuild_interface()

    header_nav = ft.Row(
        [
            ft.TextButton("◀ 이전", on_click=move_prev, style=ft.ButtonStyle(color=COLOR_BLACK)),
            month_title,
            ft.TextButton("다음 ▶", on_click=move_next, style=ft.ButtonStyle(color=COLOR_BLACK)),
        ],
        alignment="spaceBetween",
    )

    mangeun_setting_row = ft.Row(
        [
            ft.Text("만근 기준 설정", size=13, weight="bold", color=COLOR_BLACK),
            mangeun_dropdown,
        ],
        alignment="start",
        spacing=10,
    )

    days_letters = ["일", "월", "화", "수", "목", "금", "토"]
    weeks_header = ft.Row(
        [
            ft.Container(
                content=ft.Text(
                    d,
                    size=13,
                    weight="bold",
                    color=COLOR_OFF_TEXT if d == "일" else (COLOR_AM_TEXT if d == "토" else COLOR_BLACK),
                ),
                expand=1,
                alignment=ft.Alignment(0, 0),
            )
            for d in days_letters
        ],
        alignment="spaceAround",
    )

    def get_calendar_view():
        return ft.Column(
            [
                header_nav,
                stats_text,
                mangeun_text,
                mangeun_setting_row,
                ft.Divider(height=1),
                weeks_header,
                ft.Divider(height=1),
                calendar_grid,
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    # --- [설정 화면 구성] ---
    def on_work_type_radio_changed(e):
        page.client_storage.set(STORAGE_WORK_TYPE_KEY, work_type_radio.value)
        save_status_text.value = f"“{work_type_radio.value}로 저장되었습니다.”"
        page.update()

    work_type_radio = ft.RadioGroup(
        content=ft.Column(
            [
                ft.Radio(value=WORK_TYPE_SHIFT, label="교대제 (오전/오후 분할 근무)"),
                ft.Radio(value=WORK_TYPE_ALT_DAY, label="격일제 (하루 전일 근무 형태)"),
            ],
            spacing=12,
        ),
        value=CURRENT_WORK_TYPE,
        on_change=on_work_type_radio_changed,
    )

    def get_settings_view():
        # 설정 화면을 열 때마다 현재 저장된 근무 형태와 저장 문구 상태를 맞춥니다.
        work_type_radio.value = page.client_storage.get(STORAGE_WORK_TYPE_KEY) or WORK_TYPE_SHIFT
        save_status_text.value = ""
        return ft.Column(
            [
                ft.Text("앱 설정", size=20, weight="bold", color=COLOR_BLACK),
                ft.Divider(height=10, color=COLOR_TRANSPARENT),
                ft.Text("근무 형태 선택", size=14, weight="bold", color=COLOR_DARK_BLUE),
                ft.Text("형태 변경 시 달력 및 일정 입력 양식이 자동 전환됩니다.", size=11, color=COLOR_GREY),
                ft.Container(
                    content=work_type_radio,
                    padding=10,
                    border=ft.border.all(1, COLOR_BORDER),
                    border_radius=8,
                ),
                ft.Divider(height=10, color=COLOR_TRANSPARENT),
                save_status_text,
                ft.Divider(height=5, color=COLOR_TRANSPARENT),
                ft.Container(
                    content=ft.Text("달력으로 돌아가기", size=14, weight="bold", color="white"),
                    bgcolor=COLOR_PRIMARY,
                    alignment=ft.Alignment(0, 0),
                    height=42,
                    border_radius=6,
                    on_click=lambda e: switch_tab("달력"),
                ),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    # --- [하단 탭 메뉴 전환] ---
    def switch_tab(tab_name):
        btn_calendar.style.color = COLOR_PRIMARY if tab_name == "달력" else COLOR_GREY
        btn_input.style.color = COLOR_PRIMARY if tab_name == "입력" else COLOR_GREY
        btn_stats.style.color = COLOR_PRIMARY if tab_name == "통계" else COLOR_GREY
        btn_settings.style.color = COLOR_PRIMARY if tab_name == "설정" else COLOR_GREY

        if tab_name == "달력":
            content_area.content = get_calendar_view()
            rebuild_interface(update_page=False)
        elif tab_name == "설정":
            content_area.content = get_settings_view()
        else:
            content_area.content = ft.Column(
                [
                    ft.Text(f"{tab_name} 화면", size=18, weight="bold"),
                    ft.Text("해당 기능은 다음 개발 단계에서 추가될 예정입니다.", color=COLOR_GREY),
                ],
                expand=True,
            )

        page.update()

    btn_calendar = ft.TextButton(
        "달력",
        style=ft.ButtonStyle(color=COLOR_PRIMARY),
        expand=1,
        height=40,
        on_click=lambda e: switch_tab("달력"),
    )
    btn_input = ft.TextButton(
        "입력",
        style=ft.ButtonStyle(color=COLOR_GREY),
        expand=1,
        height=40,
        on_click=lambda e: switch_tab("입력"),
    )
    btn_stats = ft.TextButton(
        "통계",
        style=ft.ButtonStyle(color=COLOR_GREY),
        expand=1,
        height=40,
        on_click=lambda e: switch_tab("통계"),
    )
    btn_settings = ft.TextButton(
        "설정",
        style=ft.ButtonStyle(color=COLOR_GREY),
        expand=1,
        height=40,
        on_click=lambda e: switch_tab("설정"),
    )

    bottom_navigation_bar = ft.Row(
        [btn_calendar, btn_input, btn_stats, btn_settings],
        alignment="spaceAround",
    )

    # 최초 실행 진입점은 달력 화면입니다.
    content_area.content = get_calendar_view()

    main_layout = ft.Column(
        [
            content_area,
            ft.Divider(height=1),
            bottom_navigation_bar,
        ],
        expand=True,
    )

    page.add(ft.Stack([main_layout, popup_layer], expand=True))
    rebuild_interface()


ft.app(
    target=main,
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    view=ft.AppView.WEB_BROWSER,
)
