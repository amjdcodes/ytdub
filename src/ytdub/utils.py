"""أدوات مساعدة: تحقق URL + تنسيق + أسماء اللغات."""

from __future__ import annotations

import os

from urllib.parse import urlparse

from .i18n import t

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
    if lang == "und":
        return t("value.unknown_lang")
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


def kind_label(kind: str) -> str:
    """اسم نوع المسار بلغة الواجهة الحالية."""
    return t(f"kind.{kind}") if kind in ("original", "dubbed", "auto-dub", "descriptive") else t("kind.unknown")


def existing_output(output_dir: str, video_id: str, container: str = "") -> str | None:
    """يبحث عن ملف منزَّل سابقًا لنفس المعرّف في مجلد الإخراج.

    القالب الافتراضي يضمّن «[video_id]» في الاسم؛ نتجاهل ملفات .part الجزئية.
    """
    if not video_id or not os.path.isdir(output_dir):
        return None
    needle = f"[{video_id}]"
    for name in os.listdir(output_dir):
        if name.endswith(".part"):
            continue
        if container:
            if not name.endswith(f"{needle}.{container}"):
                continue
        elif needle not in name:
            continue
        elif name.rsplit(needle, 1)[-1].startswith(".f"):
            continue  # شظية وسيطة مثل .f299.mp4 وليست الملف المدمج
        return os.path.join(output_dir, name)
    return None


def read_batch_file(path: str) -> list[str]:
    """يقرأ ملف روابط: سطر لكل رابط، ويتجاهل الفارغ والتعليقات (#)."""
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.readlines()
    except OSError as e:
        raise RuntimeError(f"تعذّر قراءة ملف الدفعات: {e}")
    urls: list[str] = []
    for line in raw:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        urls.append(s)
    return urls


def retry_selection(row: dict) -> dict:
    """يحوّل صف سجل إلى وسائط تشغيل: (lang, height, keep_all_dubs, audio_only)."""
    keep_all = (row.get("lang") or "") == "all"
    return {
        "lang": None if keep_all else (row.get("lang") or None),
        "height": row.get("height"),
        "keep_all_dubs": keep_all,
        "audio_only": (row.get("container") or "") == "m4a",
    }
