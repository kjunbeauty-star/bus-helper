"""공개 GitHub Release 기반 APK 업데이트 안내. 저장 데이터/설치 권한을 변경하지 않는다."""
import asyncio
from dataclasses import dataclass
import json
from pathlib import Path
import re
import tomllib
from urllib.parse import urlparse
from urllib.request import Request, urlopen

REPOSITORY = "kjunbeauty-star/bus-helper"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"


def version_parts(value):
    if not isinstance(value, str) or not re.fullmatch(r"v?\d+(?:\.\d+)*", value.strip()):
        raise ValueError("Unsupported version")
    return tuple(int(part) for part in value.strip().removeprefix("v").split("."))


def compare_versions(current_version, latest_version):
    """최신이 더 높으면 1, 같으면 0, 더 낮으면 -1."""
    current, latest = version_parts(current_version), version_parts(latest_version)
    size = max(len(current), len(latest))
    current += (0,) * (size - len(current))
    latest += (0,) * (size - len(latest))
    return (latest > current) - (latest < current)


def get_current_app_version():
    # Flet 빌드의 project.version과 동일한 파일을 사용한다. 버전 문자열 복제 없음.
    try:
        with Path(__file__).with_name("pyproject.toml").open("rb") as stream:
            version = tomllib.load(stream)["project"]["version"]
        version_parts(version)
        return version
    except (OSError, ValueError, KeyError, TypeError):
        return None


@dataclass(frozen=True)
class Release:
    tag_name: str
    name: str
    body: str
    apk_url: str
    page_url: str

    @property
    def download_url(self):
        return self.apk_url or self.page_url


def github_release_url(value):
    if not isinstance(value, str):
        return ""
    url = urlparse(value)
    return value if (url.scheme == "https" and url.netloc == "github.com"
                     and url.path.startswith(f"/{REPOSITORY}/releases/")) else ""


def parse_release(payload):
    if not isinstance(payload, dict) or payload.get("draft") or payload.get("prerelease"):
        return None
    tag = payload.get("tag_name")
    version_parts(tag)
    page_url = github_release_url(payload.get("html_url"))
    apk_url = ""
    for asset in payload.get("assets", []) or []:
        if isinstance(asset, dict) and str(asset.get("name", "")).lower().endswith(".apk"):
            apk_url = github_release_url(asset.get("browser_download_url"))
            if apk_url:
                break
    if not (apk_url or page_url):
        return None
    return Release(tag, str(payload.get("name") or tag)[:200],
                   str(payload.get("body") or "새 버전이 출시되었습니다.")[:3000],
                   apk_url, page_url)


def fetch_latest_release():
    try:
        request = Request(LATEST_RELEASE_API, headers={
            "Accept": "application/vnd.github+json", "User-Agent": "BusCalendar-update",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        with urlopen(request, timeout=6) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return None
        return parse_release(json.loads(raw))
    except Exception:
        # 오프라인, 404/403/500, timeout, 잘못된 JSON 모두 조용히 건너뛴다.
        return None


async def open_update_url(launcher, release):
    import flet as ft
    await launcher.launch_url(release.download_url, mode=ft.LaunchMode.EXTERNAL_APPLICATION)


def show_update_dialog(page, launcher, release):
    import flet as ft

    def later(e):
        page.pop_dialog()

    async def update(e):
        try:
            await open_update_url(launcher, release)
        except Exception:
            return  # 실행 불가 시 팝업을 남겨 나중에 닫거나 재시도할 수 있다.
        page.pop_dialog()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("새 버전이 있습니다", size=16, weight="bold", color="#1E3A8A"),
        content=ft.Column([
            ft.Text(f"버스캘린더 {release.tag_name} 업데이트가 있습니다.", size=13),
            ft.Text(release.name, size=12, weight="bold"),
            ft.Text("주요 변경사항", size=12, weight="bold"),
            ft.Text(release.body, size=12),
        ], tight=True, spacing=8),
        scrollable=True,
        actions=[ft.TextButton("나중에", on_click=later),
                 ft.ElevatedButton("업데이트", bgcolor="#2563EB", color="white", on_click=update)],
    )
    page.show_dialog(dialog)


async def check_for_update(page, launcher):
    try:
        current = get_current_app_version()
        if current is None:
            return
        release = await asyncio.wait_for(asyncio.to_thread(fetch_latest_release), timeout=8)
        if release and compare_versions(current, release.tag_name) > 0:
            show_update_dialog(page, launcher, release)
    except Exception:
        return
