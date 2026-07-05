import os  # Render 배포 환경의 PORT 값을 읽기 위해 사용
import json  # 브라우저 저장소에 딕셔너리 데이터를 저장하기 위해 사용
import calendar
import re  # 전화번호 숫자 추출 및 정규식 활용을 위해 사용
from datetime import datetime, timedelta, timezone

import flet as ft


# --- [기본 설정값] ---
KST = timezone(timedelta(hours=9))  # 대한민국 표준시(GMT+9)

# 브라우저/폰 저장소 키
STORAGE_SCHEDULES_KEY = "bus_helper_schedules"
STORAGE_MANGEUN_KEY = "bus_helper_mangeun_targets"
STORAGE_WORK_TYPE_KEY = "bus_helper_work_type"

# --- [v2.1 입력용 전용 스토리지 키 정의] ---
STORAGE_ROUTE_NUMBER = "bus_helper_route_number"
STORAGE_PHONEBOOK_OFFICE = "bus_helper_phonebook_office"
STORAGE_DRIVER_CONTACTS = "bus_helper_driver_contacts"
STORAGE_TODAY_VEHICLE = "bus_helper_today_vehicle"
STORAGE_NEIGHBOR_VEHICLES = "bus_helper_neighbor_vehicles"

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

    # 입력 메뉴 내부에서 공유할 선택 날짜 상태 변수 (기본값 오늘)
    selected_input_date = now_kst.strftime("%Y-%m-%d")

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

    # --- [전화번호 자동 하이픈 포맷 함수] ---
    def format_phone_number(raw_string):
        """숫자가 아닌 문자를 제거하고 한국 유선/무선 전화번호 체계에 맞춰 하이픈을 넣어줍니다."""
        try:
            clean_num = re.sub(r"[^\d]", "", raw_string)
            length = len(clean_num)
            
            if length == 0:
                return ""
            
            # 서울 지역 번호 (02) 기준 처리
            if clean_num.startswith("02"):
                if length < 3:
                    return clean_num
                elif length <= 5:
                    return f"{clean_num[:2]}-{clean_num[2:]}"
                elif length <= 9:
                    return f"{clean_num[:2]}-{clean_num[2:5]}-{clean_num[5:]}"
                else:
                    return f"{clean_num[:2]}-{clean_num[2:6]}-{clean_num[6:10]}"
            
            # 일반 휴대폰 및 타 지역 번호 체계 처리
            if length < 4:
                return clean_num
            elif length <= 6:
                return f"{clean_num[:3]}-{clean_num[3:]}"
            elif length <= 10:
                return f"{clean_num[:3]}-{clean_num[3:6]}-{clean_num[6:]}"
            else:
                return f"{clean_num[:3]}-{clean_num[3:7]}-{clean_num[7:11]}"
        except Exception:
            return raw_string

    # --- [공통 전화번호부 관리 팝업 레이어 선언 구역] ---
    popup_phonebook_layer = ft.Container(
        visible=False,
        bgcolor=COLOR_OVERLAY,
        alignment=ft.Alignment(0, 0),
        expand=True,
    )

    pb_name_input = ft.TextField(label="이름", hint_text="예: 홍길동")
    pb_phone_input = ft.TextField(label="전화번호", hint_text="하이픈 없이 입력 가능")
    pb_memo_input = ft.TextField(label="메모 (선택)", hint_text="예: 오전조")
    pb_feedback_text = ft.Text("", size=12, color=COLOR_SUCCESS, weight="bold")
    pb_list_layout = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)

    def open_phonebook_popup(e):
        """버튼 클릭 시 통합 전화번호부 팝업창을 엽니다."""
        try:
            pb_name_input.value = ""
            pb_phone_input.value = ""
            pb_memo_input.value = ""
            pb_feedback_text.value = ""
            redraw_popup_driver_list()
            popup_phonebook_layer.visible = True
            page.update()
        except Exception as ex:
            print(f"전화번호부 팝업 오픈 에러: {ex}")

    def close_phonebook_popup(e):
        """전화번호부 팝업창을 닫습니다."""
        popup_phonebook_layer.visible = False
        page.update()

    def redraw_popup_driver_list():
        """팝업창 내에 동료 기사 명단을 새로 고침합니다."""
        try:
            pb_list_layout.controls.clear()
            current_items = load_json_from_storage(STORAGE_DRIVER_CONTACTS, [])
            for idx, item in enumerate(current_items):
                def create_pb_delete_handler(target_idx):
                    return lambda e: remove_pb_driver_item(target_idx)
                
                memo_info = f" ({item['memo']})" if item['memo'] else ""
                pb_list_layout.controls.append(
                    ft.Row([
                        ft.Text(f"👤 {item['name']} | {item['phone']}{memo_info}", size=13, expand=True),
                        ft.IconButton(icon=ft.icons.DELETE, icon_color=COLOR_OFF_TEXT, icon_size=16, on_click=create_pb_delete_handler(idx))
                    ], alignment="spaceBetween")
                )
        except Exception as ex:
            pb_feedback_text.value = f"목록 갱신 실패: {ex}"
            pb_feedback_text.color = COLOR_OFF_TEXT

    def add_pb_driver_item(e):
        """팝업창에서 신규 동료를 검증 및 포맷 완료 후 스토리지에 저장합니다."""
        try:
            n_val = pb_name_input.value.strip()
            p_val = pb_phone_input.value.strip()
            m_val = pb_memo_input.value.strip()

            if not n_val or not p_val:
                pb_feedback_text.value = "이름과 전화번호를 입력해주세요."
                pb_feedback_text.color = COLOR_OFF_TEXT
                page.update()
                return

            formatted_phone = format_phone_number(p_val)

            current_items = load_json_from_storage(STORAGE_DRIVER_CONTACTS, [])
            current_items.append({"name": n_val, "phone": formatted_phone, "memo": m_val})
            page.client_storage.set(STORAGE_DRIVER_CONTACTS, json.dumps(current_items, ensure_ascii=False))

            pb_name_input.value = ""
            pb_phone_input.value = ""
            pb_memo_input.value = ""

            redraw_popup_driver_list()
            pb_feedback_text.value = "동료가 추가되었습니다."
            pb_feedback_text.color = COLOR_SUCCESS
            page.update()
        except Exception as ex:
            pb_feedback_text.value = f"추가 실패 오류: {ex}"
            pb_feedback_text.color = COLOR_OFF_TEXT
            page.update()

    def remove_pb_driver_item(index):
        """팝업창 내에서 특정 동료 데이터를 삭제합니다."""
        try:
            current_items = load_json_from_storage(STORAGE_DRIVER_CONTACTS, [])
            if 0 <= index < len(current_items):
                current_items.pop(index)
            page.client_storage.set(STORAGE_DRIVER_CONTACTS, json.dumps(current_items, ensure_ascii=False))
            redraw_popup_driver_list()
            pb_feedback_text.value = "선택한 동료가 삭제되었습니다."
            pb_feedback_text.color = COLOR_SUCCESS
            page.update()
        except Exception as ex:
            pb_feedback_text.value = f"삭제 실패 오류: {ex}"
            pb_feedback_text.color = COLOR_OFF_TEXT
            page.update()

    popup_phonebook_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("📞 전화번호부 통합 관리", size=16, weight="bold", color=COLOR_DARK_BLUE),
                ft.Divider(height=1),
                pb_name_input,
                pb_phone_input,
                pb_memo_input,
                ft.ElevatedButton("동료 저장하기", bgcolor=COLOR_SUCCESS, color="white", on_click=add_pb_driver_item, width=280),
                pb_feedback_text,
                ft.Divider(height=2),
                ft.Text("📋 등록된 동료 명단", size=12, color=COLOR_GREY, weight="bold"),
                ft.Container(content=pb_list_layout, height=200),
                ft.Divider(height=1),
                ft.Row([ft.TextButton("팝업 닫기", on_click=close_phonebook_popup)], alignment="end")
            ],
            spacing=6,
            tight=True,
        ),
        bgcolor="white",
        padding=14,
        border_radius=12,
        width=300,
    )
    popup_phonebook_layer.content = popup_phonebook_card

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
        
        # [수정 반영] 중복값 표현 제거 및 초과/부족/충족 상태 명확화
        diff = work_days - m_target
        if diff > 0:
            mangeun_text.value = f"만근기준 {diff}일 초과"
        elif diff < 0:
            mangeun_text.value = f"만근기준 {abs(diff)}일 부족"
        else:
            mangeun_text.value = "만근기준 충족"

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

    # [수정 반영] 하단 설정 영역의 라벨 기재 형식 맞춤 ('만근 기준 설정' ➔ '만근 설정')
    mangeun_setting_row = ft.Row(
        [
            ft.Text("만근 설정", size=13, weight="bold", color=COLOR_BLACK),
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

    btn_phonebook_trigger = ft.TextButton(
        "📞 전화번호부", 
        on_click=open_phonebook_popup, 
        style=ft.ButtonStyle(color=COLOR_PRIMARY, text_style=ft.TextStyle(size=12, weight="bold"))
    )

    stats_and_button_row = ft.Row(
        [
            stats_text,
            btn_phonebook_trigger
        ],
        alignment="spaceBetween",
        vertical_alignment="center"
    )

    def get_calendar_view():
        return ft.Column(
            [
                header_nav,
                stats_and_button_row,
                mangeun_text,
                mangeun_setting_row,
                ft.Divider(height=1),
                weeks_header,
                ft.Divider(height=1),
                calendar_grid,
            ],
            expand=True,
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

    # =========================================================================
    # --- [v2.1 신규 활성화 및 안정화: 운행 정보 입력 화면 관리 구역] ---
    # =========================================================================

    feedback_labels = {
        "route": ft.Text("", size=12, color=COLOR_SUCCESS, weight="bold"),
        "vehicle": ft.Text("", size=12, color=COLOR_SUCCESS, weight="bold"),
        "neighbors": ft.Text("", size=12, color=COLOR_SUCCESS, weight="bold"),
        "office": ft.Text("", size=12, color=COLOR_SUCCESS, weight="bold"),
    }

    summary_text = ft.Text("", size=13, color=COLOR_BLACK)
    
    def update_summary_box():
        route_num = page.client_storage.get(STORAGE_ROUTE_NUMBER) or "미입력"
        vehicle_map = load_json_from_storage(STORAGE_TODAY_VEHICLE, {})
        neighbors_map = load_json_from_storage(STORAGE_NEIGHBOR_VEHICLES, {})
        
        today_vehicle = vehicle_map.get(selected_input_date, "미입력")
        today_neighbors = neighbors_map.get(selected_input_date, {})
        
        f_car = today_neighbors.get("front_car") or "미입력"
        f_name = today_neighbors.get("front_driver_name") or "미입력"
        f_phone = today_neighbors.get("front_driver_phone") or "미입력"
        
        b_car = today_neighbors.get("back_car") or "미입력"
        b_name = today_neighbors.get("back_driver_name") or "미입력"
        b_phone = today_neighbors.get("back_driver_phone") or "미입력"
        
        summary_text.value = (
            f"📅 {selected_input_date} 운행 정보\n"
            f"노선: {route_num}\n"
            f"내 차량: {today_vehicle + '호' if today_vehicle != '미입력' and not today_vehicle.endswith('호') else today_vehicle}\n"
            f"앞차: {f_car} / {f_name} / {f_phone}\n"
            f"뒷차: {b_car} / {b_name} / {b_phone}"
        )

    def trigger_feedback(target_key):
        feedback_labels[target_key].value = "저장되었습니다."
        update_summary_box()
        page.update()

    def get_input_view():
        nonlocal selected_input_date
        
        route_num = page.client_storage.get(STORAGE_ROUTE_NUMBER) or ""
        office_list = load_json_from_storage(STORAGE_PHONEBOOK_OFFICE, [])
        vehicle_map = load_json_from_storage(STORAGE_TODAY_VEHICLE, {})
        neighbors_map = load_json_from_storage(STORAGE_NEIGHBOR_VEHICLES, {})
        
        today_vehicle = vehicle_map.get(selected_input_date, "")
        today_neighbors = neighbors_map.get(selected_input_date, {
            "front_car": "", "front_driver_name": "", "front_driver_phone": "",
            "back_car": "", "back_driver_name": "", "back_driver_phone": ""
        })

        for lbl in feedback_labels.values():
            lbl.value = ""

        update_summary_box()

        summary_box_container = ft.Container(
            content=summary_text,
            bgcolor="#EFF6FF",
            border=ft.border.all(1, "#BFDBFE"),
            border_radius=8,
            padding=12,
            margin=ft.margin.only(bottom=10)
        )

        date_display_field = ft.TextField(
            label="선택된 기준 날짜",
            value=selected_input_date,
            read_only=True,
            width=180,
            height=45,
            text_size=14,
            content_padding=10
        )

        def handle_date_picked(e):
            nonlocal selected_input_date
            if date_picker.value:
                selected_input_date = date_picker.value.strftime("%Y-%m-%d")
                content_area.content = get_input_view()
                page.update()

        date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31),
            on_change=handle_date_picked
        )
        if date_picker not in page.overlay:
            page.overlay.append(date_picker)

        def open_date_picker(e):
            date_picker.open = True
            page.update()

        route_field = ft.TextField(label="노선번호 입력", value=route_num, hint_text="예: 143")
        
        def save_route(e):
            page.client_storage.set(STORAGE_ROUTE_NUMBER, route_field.value.strip())
            trigger_feedback("route")

        vehicle_field = ft.TextField(label="오늘 운행 차량 번호", value=today_vehicle, hint_text="예: 1234호")
        
        def save_today_vehicle(e):
            v_map = load_json_from_storage(STORAGE_TODAY_VEHICLE, {})
            v_map[selected_input_date] = vehicle_field.value.strip()
            page.client_storage.set(STORAGE_TODAY_VEHICLE, json.dumps(v_map, ensure_ascii=False))
            trigger_feedback("vehicle")

        def make_driver_dropdown_options():
            try:
                current_drivers = load_json_from_storage(STORAGE_DRIVER_CONTACTS, [])
                if not current_drivers:
                    return [ft.dropdown.Option("", "전화번호부에 등록된 동료가 없습니다.")]
                
                opts = [ft.dropdown.Option("", "직접 입력 (목록에서 선택)")]
                for d in current_drivers:
                    display_label = f"{d['name']} ({d['phone']} / {d['memo']})" if d.get('memo') else f"{d['name']} ({d['phone']})"
                    opts.append(ft.dropdown.Option(f"{d['name']}/{d['phone']}", display_label))
                return opts
            except Exception:
                return [ft.dropdown.Option("", "직접 입력 (목록에서 선택)")]

        front_car_field = ft.TextField(label="차량번호", value=today_neighbors.get("front_car", ""), hint_text="예: 2694")
        front_driver_name_field = ft.TextField(label="운전자 이름", value=today_neighbors.get("front_driver_name", ""), hint_text="예:선명구")
        front_driver_phone_field = ft.TextField(label="전화번호", value=today_neighbors.get("front_driver_phone", ""), hint_text="예: 010-0000-0000")
        
        back_car_field = ft.TextField(label="차량번호", value=today_neighbors.get("back_car", ""), hint_text="예: 2745")
        back_driver_name_field = ft.TextField(label="운전자 이름", value=today_neighbors.get("back_driver_name", ""), hint_text="예: 이청일")
        back_driver_phone_field = ft.TextField(label="전화번호", value=today_neighbors.get("back_driver_phone", ""), hint_text="예: 010-0000-0000")

        def handle_front_selection(e):
            try:
                if front_driver_dd.value:
                    name, phone = front_driver_dd.value.split("/")
                    front_driver_name_field.value = name
                    front_driver_phone_field.value = phone
                else:
                    front_driver_name_field.value = ""
                    front_driver_phone_field.value = ""
                page.update()
            except Exception:
                pass

        def handle_back_selection(e):
            try:
                if back_driver_dd.value:
                    name, phone = back_driver_dd.value.split("/")
                    back_driver_name_field.value = name
                    back_driver_phone_field.value = phone
                else:
                    back_driver_name_field.value = ""
                    back_driver_phone_field.value = ""
                page.update()
            except Exception:
                pass

        driver_dropdown_options = make_driver_dropdown_options()
        front_driver_dd = ft.Dropdown(label="등록된 동료 기사 선택 (앞차)", options=driver_dropdown_options, on_change=handle_front_selection, value="")
        back_driver_dd = ft.Dropdown(label="등록된 동료 기사 선택 (뒷차)", options=driver_dropdown_options, on_change=handle_back_selection, value="")

        def save_neighbors(e):
            try:
                n_map = load_json_from_storage(STORAGE_NEIGHBOR_VEHICLES, {})
                n_map[selected_input_date] = {
                    "front_car": front_car_field.value.strip(),
                    "front_driver_name": front_driver_name_field.value.strip(),
                    "front_driver_phone": front_driver_phone_field.value.strip(),
                    "back_car": back_car_field.value.strip(),
                    "back_driver_name": back_driver_name_field.value.strip(),
                    "back_driver_phone": back_driver_phone_field.value.strip()
                }
                page.client_storage.set(STORAGE_NEIGHBOR_VEHICLES, json.dumps(n_map, ensure_ascii=False))
                trigger_feedback("neighbors")
            except Exception:
                pass

        front_info_card = ft.Container(
            content=ft.Column([
                ft.Text("앞차 정보", size=14, weight="bold", color=COLOR_DARK_BLUE),
                ft.Divider(height=1, color=COLOR_BORDER),
                front_car_field,
                front_driver_name_field,
                front_driver_phone_field,
            ], spacing=8),
            padding=12,
            border=ft.border.all(1, COLOR_BORDER),
            border_radius=8,
            bgcolor="#F8FAFC"
        )

        back_info_card = ft.Container(
            content=ft.Column([
                ft.Text("뒷차 정보", size=14, weight="bold", color=COLOR_DARK_BLUE),
                ft.Divider(height=1, color=COLOR_BORDER),
                back_car_field,
                back_driver_name_field,
                back_driver_phone_field,
            ], spacing=8),
            padding=12,
            border=ft.border.all(1, COLOR_BORDER),
            border_radius=8,
            bgcolor="#F8FAFC"
        )

        office_list_layout = ft.Column(spacing=4)
        office_type_input = ft.TextField(label="구분", hint_text="예: 정비고")
        office_phone_input = ft.TextField(label="전화번호", hint_text="예: 02-1234-5678")

        def raise_confirm_dialog(message, on_confirm_click):
            def close_dialog(e):
                page.dialog.open = False
                page.update()

            def process_confirm(e):
                page.dialog.open = False
                on_confirm_click()
                page.update()

            page.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("삭제 확인"),
                content=ft.Text(message),
                actions=[
                    ft.TextButton("삭제", on_click=process_confirm, style=ft.ButtonStyle(color="red")),
                    ft.TextButton("취소", on_click=close_dialog),
                ],
                actions_alignment="end",
            )
            page.dialog.open = True
            page.update()

        def redraw_office_list(update_page=True):
            office_list_layout.controls.clear()
            current_items = load_json_from_storage(STORAGE_PHONEBOOK_OFFICE, [])
            for idx, item in enumerate(current_items):
                def create_delete_handler(target_idx):
                    return lambda e: raise_confirm_dialog(
                        "이 항목을 삭제하시겠습니까?", 
                        lambda: remove_office_item(target_idx)
                    )
                office_list_layout.controls.append(
                    ft.Row([
                        ft.Text(f"• {item['type']} : {item['phone']}", size=13, expand=True),
                        ft.IconButton(icon=ft.icons.DELETE, icon_color=COLOR_OFF_TEXT, icon_size=16, on_click=create_delete_handler(idx))
                    ], alignment="spaceBetween")
                )
            if update_page:
                page.update()

        def add_office_item(e):
            t_val = office_type_input.value.strip()
            p_val = office_phone_input.value.strip()
            if not t_val or not p_val: return
            
            formatted_office_phone = format_phone_number(p_val)

            current_items = load_json_from_storage(STORAGE_PHONEBOOK_OFFICE, [])
            current_items.append({"type": t_val, "phone": formatted_office_phone})
            page.client_storage.set(STORAGE_PHONEBOOK_OFFICE, json.dumps(current_items, ensure_ascii=False))
            office_type_input.value, office_phone_input.value = "", ""
            redraw_office_list(update_page=True)
            trigger_feedback("office")

        def remove_office_item(index):
            current_items = load_json_from_storage(STORAGE_PHONEBOOK_OFFICE, [])
            if 0 <= index < len(current_items):
                current_items.pop(index)
            page.client_storage.set(STORAGE_PHONEBOOK_OFFICE, json.dumps(current_items, ensure_ascii=False))
            redraw_office_list(update_page=True)

        redraw_office_list(update_page=False)

        return ft.Column([
            ft.Text("운행 정보 입력", size=22, weight="bold", color=COLOR_BLACK),
            
            ft.Row([
                date_display_field,
                ft.IconButton(
                    icon=ft.icons.CALENDAR_MONTH,
                    icon_color=COLOR_PRIMARY,
                    icon_size=28,
                    on_click=open_date_picker
                )
            ], alignment="start", vertical_alignment="center"),
            ft.Divider(height=10, color=COLOR_TRANSPARENT),
            
            summary_box_container,
            
            ft.Card(ft.Container(ft.Column([
                ft.Text("🚍 노선번호 관리", size=14, weight="bold", color=COLOR_DARK_BLUE),
                route_field,
                ft.ElevatedButton("노선번호 저장", width=280, height=42, bgcolor=COLOR_PRIMARY, color="white", on_click=save_route),
                feedback_labels["route"]
            ], spacing=8), padding=10)),

            ft.Card(ft.Container(ft.Column([
                ft.Text("🔑 해당 일자 운행 차량 번호 입력", size=14, weight="bold", color=COLOR_DARK_BLUE),
                vehicle_field,
                ft.ElevatedButton("차량 번호 저장", width=280, height=42, bgcolor=COLOR_PRIMARY, color="white", on_click=save_today_vehicle),
                feedback_labels["vehicle"]
            ], spacing=8), padding=10)),

            ft.Card(ft.Container(ft.Column([
                ft.Text("↔️ 앞차 / 뒷차 운행 정보 연계", size=14, weight="bold", color=COLOR_DARK_BLUE),
                front_driver_dd,
                front_info_card,
                ft.Divider(height=10, color=COLOR_TRANSPARENT),
                back_driver_dd,
                back_info_card,
                ft.ElevatedButton("연계 배차 정보 일괄 저장", width=280, height=44, bgcolor=COLOR_DARK_BLUE, color="white", on_click=save_neighbors),
                feedback_labels["neighbors"]
            ], spacing=8), padding=10)),

            ft.Card(ft.Container(ft.Column([
                ft.Text("☎️ 사무실 / 정비고 / AS 연락처 등록", size=14, weight="bold", color=COLOR_DARK_BLUE),
                office_type_input,
                office_phone_input,
                ft.ElevatedButton("연락처 등록추가", width=280, height=42, bgcolor=COLOR_SUCCESS, color="white", on_click=add_office_item),
                feedback_labels["office"],
                ft.Divider(height=1),
                office_list_layout
            ], spacing=8), padding=10)),
            
            ft.Container(height=30)
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    # --- [하단 탭 메뉴 전환 확장 분기 연동] ---
    def switch_tab(tab_name):
        btn_calendar.style.color = COLOR_PRIMARY if tab_name == "달력" else COLOR_GREY
        btn_input.style.color = COLOR_PRIMARY if tab_name == "입력" else COLOR_GREY
        btn_stats.style.color = COLOR_PRIMARY if tab_name == "통계" else COLOR_GREY
        btn_settings.style.color = COLOR_PRIMARY if tab_name == "설정" else COLOR_GREY

        if tab_name == "달력":
            content_area.content = get_calendar_view()
            rebuild_interface(update_page=False)
        elif tab_name == "입력":
            content_area.content = get_input_view()
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

    content_area.content = get_calendar_view()

    main_layout = ft.Column(
        [
            content_area,
            ft.Divider(height=1),
            bottom_navigation_bar,
        ],
        expand=True,
    )

    page.add(ft.Stack([main_layout, popup_layer, popup_phonebook_layer], expand=True))
    rebuild_interface()


ft.app(
    target=main,
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    view=ft.AppView.WEB_BROWSER,
)
