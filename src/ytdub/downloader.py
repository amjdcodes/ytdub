"""التحميل عبر yt-dlp + فحص ffmpeg + حلقة الاستئناف (حسب docs/03 و docs/05)."""

from __future__ import annotations

import platform
import shutil
import time

from yt_dlp import YoutubeDL

FFMPEG_INSTALL_HINT = {
    "Linux": "sudo apt install ffmpeg  (أو sudo dnf install ffmpeg)",
    "Darwin": "brew install ffmpeg",
    "Windows": "choco install ffmpeg  أو حمّله من https://www.gyan.dev/ffmpeg/builds/",
}


def ensure_ffmpeg(audio_only: bool = False) -> None:
    if shutil.which("ffmpeg"):
        return
    sys = platform.system()
    hint = FFMPEG_INSTALL_HINT.get(sys, "https://ffmpeg.org/download.html")
    raise RuntimeError(
        "تعذّر العثور على ffmpeg وهو إلزامي للدمج.\n"
        f"ثبّته ثم أعد التشغيل. ({sys}: {hint})"
        "\nملاحظة: لا تثبّت حزمة PyPI المسماة ffmpeg — المطلوب الثنائي الحقيقي."
    )


def _attempt(
    url: str,
    fmt: str,
    container: str,
    outtmpl: str,
    sort: list[str] | None,
    audio_multistreams: bool,
    cookies_file: str | None,
    cookies_from_browser: str | None,
    verbose: bool,
    net: dict,
    progress_hook,
) -> str:
    """محاولة تحميل واحدة — تستكمل ملفات .part تلقائيًا عبر continuedl."""
    opts: dict = {
        "format": fmt,
        "merge_output_format": container,
        "outtmpl": outtmpl,
        "quiet": not verbose,
        "no_warnings": not verbose,
        "continuedl": net.get("continuedl", True),
        "retries": net.get("retries", 10),
        "fragment_retries": net.get("fragment_retries", 10),
        "retry_sleep_functions": {"http": lambda n: net.get("retry_wait", 5)},
        "socket_timeout": net.get("socket_timeout", 30),
        "concurrent_fragment_downloads": net.get("concurrent_fragments", 4),
        "postprocessor_args": {"ffmpeg": ["-strict", "-2"]} if container == "mp4" else {},
    }
    if sort:
        opts["format_sort"] = sort
    if audio_multistreams:
        opts["audio_multistreams"] = True
    if cookies_file:
        opts["cookiefile"] = cookies_file
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser,)

    finished: dict = {}

    def _hook(d: dict) -> None:
        if d.get("status") == "finished":
            finished["path"] = d.get("filename", "")

    hooks = ([progress_hook] if progress_hook else []) + [_hook]
    opts["progress_hooks"] = hooks

    with YoutubeDL(opts) as ydl:
        ydl.download([url])
        try:
            info = ydl.extract_info(url, download=False)
            return finished.get("path") or ydl.prepare_filename(info)
        except Exception:
            return finished.get("path", "")


def download(
    url: str,
    fmt: str,
    container: str,
    outtmpl: str,
    sort: list[str] | None = None,
    audio_multistreams: bool = False,
    cookies_file: str | None = None,
    cookies_from_browser: str | None = None,
    verbose: bool = False,
    progress_hook=None,
    net: dict | None = None,
    max_retries: int = 0,
    retry_wait: int = 5,
    on_attempt=None,
) -> tuple[str, int, bool]:
    """تحميل مع حلقة إعادة محاولة خارجية واستكمال من .part.

    يرجع (المسار, عدد_المحاولات, هل_استؤنف).
    on_attempt(attempt_no, status, error) يُستدعى بعد كل محاولة لتسجيلها في DB.
    """
    net = dict(net or {})
    net.setdefault("retry_wait", retry_wait)
    total_tries = 1 + max(0, max_retries)
    last_error = ""
    for attempt in range(1, total_tries + 1):
        resumed = attempt > 1
        try:
            path = _attempt(url, fmt, container, outtmpl, sort, audio_multistreams, cookies_file, cookies_from_browser, verbose, net, progress_hook)
            if on_attempt:
                on_attempt(attempt, True, "")
            return path, attempt, resumed
        except Exception as e:
            last_error = str(e)[:300]
            if on_attempt:
                on_attempt(attempt, False, last_error)
            if attempt < total_tries:
                time.sleep(retry_wait)
    raise RuntimeError(f"فشل التنزيل بعد {total_tries} محاولات. آخر خطأ: {last_error}")
