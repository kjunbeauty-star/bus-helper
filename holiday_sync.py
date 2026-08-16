import hashlib
import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

OFFICIAL_API_URL = "https://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo"

def normalize_holiday_name(name):
    text = str(name or "").strip()
    return "대체휴" if "대체공휴일" in text else text

def parse_official_holiday_xml(payload):
    root = ET.fromstring(payload)
    result_code = root.findtext(".//resultCode")
    if result_code not in (None, "00"):
        raise ValueError(f"{result_code}: {root.findtext('.//resultMsg') or '공휴일 API 오류'}")
    holidays = {}
    for item in root.findall(".//item"):
        if (item.findtext("isHoliday") or "Y").upper() != "Y":
            continue
        raw_date = (item.findtext("locdate") or "").strip()
        name = normalize_holiday_name(item.findtext("dateName"))
        if len(raw_date) == 8 and raw_date.isdigit() and name:
            holidays[f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"] = name
    return holidays

def fetch_official_holidays(years, service_key=None, timeout=10):
    key = service_key or os.environ.get("KASI_HOLIDAY_API_KEY", "")
    if not key:
        raise RuntimeError("KASI_HOLIDAY_API_KEY가 설정되지 않았습니다.")
    holidays = {}
    for year in sorted({int(year) for year in years}):
        query = urllib.parse.urlencode({"serviceKey": key, "solYear": str(year), "numOfRows": "100", "pageNo": "1"}, safe="%")
        request = urllib.request.Request(f"{OFFICIAL_API_URL}?{query}", headers={"User-Agent": "BusCalendar/1.1"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            holidays.update(parse_official_holiday_xml(response.read()))
    return holidays

def build_holiday_payload(holidays, source="kasi"):
    normalized = {str(k): normalize_holiday_name(v) for k, v in holidays.items()}
    canonical = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
    return {"updated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "version": hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16], "source": source, "holidays": normalized}

def should_check_holidays(last_checked_month, now=None):
    current = now or datetime.now().astimezone()
    return last_checked_month != current.strftime("%Y-%m")

def download_holidays(url, years, timeout=8):
    query = urllib.parse.urlencode({"years": ",".join(str(int(y)) for y in years)})
    separator = "&" if "?" in url else "?"
    request = urllib.request.Request(f"{url}{separator}{query}", headers={"User-Agent": "BusCalendar/1.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    holidays = payload.get("holidays", {}) if isinstance(payload, dict) else {}
    if not isinstance(holidays, dict):
        raise ValueError("잘못된 공휴일 응답입니다.")
    return {str(k): normalize_holiday_name(v) for k, v in holidays.items()}
