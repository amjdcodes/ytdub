"""أدوات مساعدة: تحقق URL + تنسيق + أسماء اللغات."""

from __future__ import annotations

from urllib.parse import urlparse

LANG_NAMES = {
    "ar": "العربية",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "ru": "Русский",
    "tr": "Türkçe",
    "hi": "हिन्दी",
    "ur": "اردو",
    "ja": "日本語",
    "ko": "한국어",
    "zh": "中文",
    "nl": "Nederlands",
    "pl": "Polski",
    "id": "Bahasa Indonesia",
    "und": "غير محدد",
}

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "music.youtube.com",
    "www.music.youtube.com",
}


def is_youtube_url(url: str) -> bool:
    try:
        p = urlparse(url.strip())
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    host = (p.hostname or "").lower()
    if host not in YOUTUBE_HOSTS and not host.endswith(".youtube.com"):
        return False
    if host in ("youtu.be", "www.youtu.be"):
        return len(p.path.strip("/")) > 0
    return True


def format_bytes(n: int | float | None) -> str:
    if not n or n <= 0:
        return "—"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{int(n)}B"
        n /= 1024
    return f"{n:.1f}GB"


def format_duration(sec: int | None) -> str:
    if sec is None:
        return "—"
    sec = int(sec)
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def lang_display(lang: str) -> str:
    return LANG_NAMES.get(lang, lang)


def classify_dub_kind(format_note: str, language_raw: str = "") -> str:
    """يصنف المسار: original / dubbed / auto-dub / descriptive (حسب docs/01)."""
    note = (format_note or "").lower()
    raw = (language_raw or "").lower()
    if "descriptive" in note or "descriptive" in raw:
        return "descriptive"
    if "dubbed-auto" in note or "dubbed-auto" in raw or "auto-dub" in note:
        return "auto-dub"
    if "original" in note:
        return "original"
    if "dub" in note:
        return "dubbed"
    return "unknown"


KIND_AR = {
    "original": "أصلي ✅",
    "dubbed": "مدبلج",
    "auto-dub": "تلقائي 🤖",
    "descriptive": "وصفي",
    "unknown": "—",
}
