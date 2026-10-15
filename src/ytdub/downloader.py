"""التحميل عبر yt-dlp + فحص ffmpeg (حسب docs/03 و docs/05)."""

from __future__ import annotations

import platform
import shutil

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
        + ("\nملاحظة: لا تثبّت حزمة PyPI المسماة ffmpeg — المطلوب الثنائي الحقيقي." if True else "")
    )


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
) -> str:
    opts: dict = {
        "format": fmt,
        "merge_output_format": container,
        "outtmpl": outtmpl,
        "quiet": not verbose,
        "no_warnings": not verbose,
        "progress_hooks": [progress_hook] if progress_hook else [],
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

    final_path = ""
    finished: dict = {}

    def _hook(d: dict) -> None:
        if d.get("status") == "finished":
            finished["path"] = d.get("filename", "")
        if progress_hook:
            pass  # progress_hook الخارجي عولج قبله عبر نفس السلسلة

    # نجمع hook الداخلي + الخارجي
    hooks = []
    if progress_hook:
        hooks.append(progress_hook)
    hooks.append(_hook)
    opts["progress_hooks"] = hooks

    with YoutubeDL(opts) as ydl:
        ydl.download([url])
        # أفضل اسم متوقع:
        try:
            info = ydl.extract_info(url, download=False)
            final_path = finished.get("path") or ydl.prepare_filename(info)
        except Exception:
            final_path = finished.get("path", "")
    return final_path
