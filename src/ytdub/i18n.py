"""كتالوج رسائل الواجهة (عربي/إنجليزي) — وحدة leaf بلا استيرادات داخلية.

الاستخدام:
    from .i18n import set_lang, t
    set_lang("en")
    console.print(t("dub.selected", display="English", lang="en"))

المفاتيح مسطّحة ومتشابهة بين اللغتين (اختبار التكافؤ في tests/test_i18n.py).
"""

from __future__ import annotations

LANG_AR = "ar"
LANG_EN = "en"
_ALIASES_EN = ("en", "english", "eng")

_LANG = LANG_AR

# ── مفردات الرموز (عائلة نصية موجهة للمطورين — بلا إيموجي) ──────────────
SYM_SECTION = "◆"
SYM_PROMPT = "›"
SYM_DOT = "·"
SYM_ARROW = "→"
TAG_OK = "OK " + SYM_DOT
TAG_ERR = "ERR " + SYM_DOT
TAG_WARN = "WARN " + SYM_DOT
TAG_RETRY = "RETRY " + SYM_DOT
TAG_SKIP = "SKIP " + SYM_DOT
TAG_INFO = "INFO " + SYM_DOT

_MESSAGES: dict[str, dict[str, str]] = {
    "ar": {
        # ── أخطاء عامة ──────────────────────────────────────────────
        "error.input_cancelled": "أُلغي الإدخال.",
        "error.setup_cancelled": "أُلغي الإعداد.",
        "error.operation_cancelled": "أُلغيت العملية.",
        "error.url_unsupported": "الرابط غير مدعوم — الصق رابط watch/youtu.be/music.youtube صحيحًا.",
        "error.no_qualities": "لا توجد جودات فيديو متاحة لهذا الرابط (خاص/محذوف/DRM؟).",
        "error.dub_unavailable": "الدبلجة '{lang}' غير متوفرة. المتاح: {avail}",
        "error.quality_unavailable": "الدقة {height}p غير متوفرة. المتاح: {avail}",
        "error.retry_not_found_last": "لا يوجد آخر صف فاشل في السجل — راجع ytdub --history.",
        "error.retry_not_found_row": "لا يوجد الصف {id} في السجل — راجع ytdub --history.",
        "error.batch_empty": "ملف الدفعات فارغ — ضع رابطًا في كل سطر.",
        "error.batch_read": "تعذّر قراءة ملف الدفعات: {err}",
        "error.extract_empty": "تعذّر استخراج بيانات الفيديو (معلومات فارغة).",
        "error.playlist": "الرابط يشير إلى قائمة تشغيل وليس فيديو واحدًا. حمّل فيديو واحدًا.",
        "error.extract_failed": "فشل استخراج البيانات: {msg}",
        "error.private": "الفيديو خاص أو محذوف أو يحتاج تسجيل دخول/تحقق عمر.",
        "error.rate_limited": (
            "يوتيوب قيّد الوصول مؤقتًا (429/bot-check). جرّب لاحقًا أو استخدم "
            "--cookies-from-browser أو --player-client android."
        ),
        "error.drm": "هذا المحتوى محمي بـ DRM ولا يمكن تحميله.",
        "error.po_token": (
            "يوتيوب طلب PO Token. حدّث yt-dlp إلى nightly وثبّت deno ثم جرّب --player-client android."
        ),
        "error.ffmpeg_missing": (
            "تعذّر العثور على ffmpeg وهو إلزامي للدمج.\n"
            "ثبّته ثم أعد التشغيل. ({sys}: {hint})\n"
            "ملاحظة: لا تثبّت حزمة PyPI المسماة ffmpeg — المطلوب الثنائي الحقيقي."
        ),
        "error.download_failed": "فشل التنزيل بعد {tries} محاولات. آخر خطأ: {err}",
        # ── المعالج والإعدادات ──────────────────────────────────────
        "wizard.lang_header": SYM_SECTION + " اختر لغة الواجهة / Choose interface language:",
        "wizard.lang_invalid": TAG_ERR + " اختر 1 أو 2 / Choose 1 or 2",
        "wizard.intro": SYM_SECTION + " أول تشغيل — إعداد سريع (مرة واحدة فقط):",
        "wizard.retry_q": "عند فشل التنزيل، هل يعيد المحاولة مع الاستكمال من حيث توقف؟",
        "wizard.retry_max_q": "كم مرة يعيد المحاولة عند الفشل المتكرر؟",
        "wizard.retry_wait_q": "كم ثانية ينتظر بين المحاولات؟",
        "wizard.update_q": "هل يفحص تحديثات الأدوات (yt-dlp...) عند كل تشغيل ويثبتها؟",
        "wizard.output_q": "مجلد الحفظ الافتراضي (افتراضي downloads): ",
        "wizard.saved": TAG_OK + " حُفظت الإعدادات في: {path}",
        "wizard.invalid_yesno": "أجب بـ y أو n.",
        "wizard.invalid_int": "أدخل رقمًا صحيحًا.",
        "wizard.int_range": "الرقم يجب أن يكون بين {min} و {max}.",
        "config.header": "الإعدادات: {path}",
        "config.ui_lang_set": TAG_OK + " لغة الواجهة الآن: العربية — حُفظت في {path}",
        # ── التصاميم ────────────────────────────────────────────────
        "theme.classic.name": "كلاسيكي",
        "theme.classic.desc": "ألوان الطرفية الافتراضية — خفيف ومتوازن",
        "theme.midnight.name": "ليلي",
        "theme.midnight.desc": "أزرق هادئ لخلفيات داكنة — مريح للعين",
        "theme.sand.name": "رملي",
        "theme.sand.desc": "ألوان دافئة لخلفيات فاتحة — مريح نهارًا",
        "theme.header": SYM_SECTION + " اختر تصميم الواجهة:",
        "theme.prompt": SYM_PROMPT + " اختر التصميم [0-{max}] (افتراضي {default}، 0 = إلغاء): ",
        "theme.invalid": "اختر رقمًا من 0 إلى {max}.",
        "theme.saved": TAG_OK + " التصميم الآن: {name} — حُفظ في {path}",
        "theme.current": "الحالي",
        "theme.preview_video": "فيديو تجريبي — معاينة التصميم",
        "banner.tagline": "تحميل يوتيوب بالدبلجة والجودة التي تختارها",
        # ── السجل والحالات ──────────────────────────────────────────
        "history.empty": "لا يوجد سجل بعد — حمّل أول فيديو.",
        "history.title": SYM_SECTION + " سجل التنزيلات (آخر {count})",
        "history.col_id": "#",
        "history.col_title": "العنوان",
        "history.col_lang": "اللغة",
        "history.col_height": "الدقة",
        "history.col_status": "الحالة",
        "history.col_attempts": "محاولات",
        "status.pending": "قيد الانتظار",
        "status.success": "نجح",
        "status.failed": "فشل",
        "status.resumed": "استُؤنف",
        "status.retried": "أُعيدت محاولته",
        "status.skipped": "تم التخطي",
        # ── أنواع الدبلجة والقيم ────────────────────────────────────
        "kind.original": "أصلي",
        "kind.dubbed": "مدبلج",
        "kind.auto-dub": "تلقائي",
        "kind.descriptive": "وصفي",
        "kind.unknown": "—",
        "value.all_dubs": "كل الدبلجات",
        "value.audio_only": "صوت فقط",
        "value.best": "الأفضل",
        "value.unknown_lang": "غير محدد",
        # ── الجداول والعرض ──────────────────────────────────────────
        "video.subtitle": "{uploader} " + SYM_DOT + " المدة {duration}",
        "video.views": "{count:,} مشاهدة",
        "dubs.single": "لغة صوتية واحدة فقط (الأصلية: {lang}) — سيتم تخطي اختيار الدبلجة.",
        "dubs.title": SYM_SECTION + " الدبلجات المتوفرة ({count})",
        "dubs.col_num": "#",
        "dubs.col_lang": "اللغة",
        "dubs.col_code": "الكود",
        "dubs.col_kind": "النوع",
        "dubs.col_quality": "الجودة",
        "quals.title": SYM_SECTION + " الجودات المتوفرة ({count})",
        "quals.col_num": "#",
        "quals.col_res": "الدقة",
        "quals.col_fps": "FPS",
        "quals.col_codec": "الكودك",
        "quals.col_size": "الحجم",
        "quals.col_note": "ملاحظة",
        "quals.audio_row": "صوت فقط",
        "quals.note_recommended": "موصى به",
        "quals.note_modern": "يحتاج مشغلًا حديثًا",
        "estimate.line": "الحجم المتوقع تقريبًا: {size} ({container})",
        "confirm.overwrite": "الملف موجود مسبقًا: {path}\n" + SYM_PROMPT + " إعادة التنزيل؟ [y/N]: ",
        # ── الأسئلة ─────────────────────────────────────────────────
        "ask.choose": "اختر:",
        "ask.url_prompt": "رابط الفيديو: ",
        "ask.number_prompt": "{prompt} [{min}-{max}] (افتراضي {default}): ",
        "ask.dub_prompt": SYM_PROMPT + " اختر الدبلجة",
        "ask.quality_prompt": SYM_PROMPT + " اختر الجودة (0 = صوت فقط)",
        "ask.invalid_int": "أدخل رقمًا صحيحًا.",
        "ask.out_of_range": "الرقم يجب أن يكون بين {min} و {max}.",
        # ── التدفق ─────────────────────────────────────────────────
        "scan.status": "جارٍ فحص الدبلجات والجودات...",
        "scan.android_extra": "تم العثور على دبلجات إضافية عبر android player.",
        "dub.selected": "الدبلجة: {display} ({lang})",
        "dub.default": "الدبلجة (افتراضي): {display}",
        "quality.selected": "الجودة: {height}p",
        "progress.downloading": "جارٍ التحميل [{lang}|{quality}]",
        "download.retry_warning": TAG_WARN + " فشلت المحاولة {attempt} — إعادة بعد {wait}s (استكمال من حيث توقف)...",
        "download.done": TAG_OK + " تم (محاولات: {attempts}): ./{dir}/{file}   {tags}",
        "download.skipped": TAG_SKIP + " موجود مسبقًا — تم التخطي: {path}",
        "retry.starting": TAG_RETRY + " إعادة محاولة: {title} (المعرّف {id})",
        "batch.started": "دفعات: {count} رابط من {file}",
        "batch.item_failed": TAG_ERR + " فشل: {err}",
        "batch.summary": "الملخص: نجح {ok} " + SYM_DOT + " فشل {failed} من {total}",
        # ── التحديثات ──────────────────────────────────────────────
        "update.upgrading": "تحديث {pkg}: {old} " + SYM_ARROW + " {new} ...",
        "update.ok": TAG_OK + " تم تحديث {pkg}",
        "update.fail": TAG_ERR + " فشل تحديث {pkg}",
        "update.available": TAG_INFO + " تحديثات متاحة: {names}",
    },
    "en": {
        # ── General errors ─────────────────────────────────────────
        "error.input_cancelled": "Input cancelled.",
        "error.setup_cancelled": "Setup cancelled.",
        "error.operation_cancelled": "Operation cancelled.",
        "error.url_unsupported": "Unsupported URL — paste a valid watch/youtu.be/music.youtube link.",
        "error.no_qualities": "No video qualities available for this link (private/deleted/DRM?).",
        "error.dub_unavailable": "Dub '{lang}' is unavailable. Available: {avail}",
        "error.quality_unavailable": "Resolution {height}p is unavailable. Available: {avail}",
        "error.retry_not_found_last": "No failed row found in history — see ytdub --history.",
        "error.retry_not_found_row": "Row {id} was not found in history — see ytdub --history.",
        "error.batch_empty": "Batch file is empty — put one URL per line.",
        "error.batch_read": "Could not read the batch file: {err}",
        "error.extract_empty": "Could not extract video info (empty metadata).",
        "error.playlist": "The link points to a playlist, not a single video. Download one video.",
        "error.extract_failed": "Failed to extract info: {msg}",
        "error.private": "The video is private, deleted, or requires sign-in/age verification.",
        "error.rate_limited": (
            "YouTube temporarily rate-limited access (429/bot check). Try later or use "
            "--cookies-from-browser / --player-client android."
        ),
        "error.drm": "This content is DRM-protected and cannot be downloaded.",
        "error.po_token": (
            "YouTube requires a PO Token. Update yt-dlp to nightly, install deno, then try --player-client android."
        ),
        "error.ffmpeg_missing": (
            "ffmpeg was not found and is required for merging.\n"
            "Install it, then retry. ({sys}: {hint})\n"
            "Note: do not install the PyPI package named ffmpeg — you need the real binary."
        ),
        "error.download_failed": "Download failed after {tries} attempts. Last error: {err}",
        # ── Wizard & config ────────────────────────────────────────
        "wizard.lang_header": SYM_SECTION + " Choose interface language / اختر لغة الواجهة:",
        "wizard.lang_invalid": TAG_ERR + " Choose 1 or 2 / اختر 1 أو 2",
        "wizard.intro": SYM_SECTION + " First run — quick setup (one time only):",
        "wizard.retry_q": "On a failed download, retry and resume where it stopped?",
        "wizard.retry_max_q": "How many retries on repeated failure?",
        "wizard.retry_wait_q": "Seconds to wait between attempts?",
        "wizard.update_q": "Check for tool updates (yt-dlp...) on each run and install them?",
        "wizard.output_q": "Default save folder (default downloads): ",
        "wizard.saved": TAG_OK + " Settings saved to: {path}",
        "wizard.invalid_yesno": "Answer y or n.",
        "wizard.invalid_int": "Enter a valid integer.",
        "wizard.int_range": "The number must be between {min} and {max}.",
        "config.header": "Config: {path}",
        "config.ui_lang_set": TAG_OK + " Interface language is now: English — saved to {path}",
        # ── Themes ──────────────────────────────────────────────────
        "theme.classic.name": "Classic",
        "theme.classic.desc": "Default terminal colors — light and balanced",
        "theme.midnight.name": "Midnight",
        "theme.midnight.desc": "Soft blue for dark backgrounds — easy on the eyes",
        "theme.sand.name": "Sand",
        "theme.sand.desc": "Warm tones for light backgrounds — comfortable by day",
        "theme.header": SYM_SECTION + " Choose the interface theme:",
        "theme.prompt": SYM_PROMPT + " Theme [0-{max}] (default {default}, 0 = cancel): ",
        "theme.invalid": "Choose a number from 0 to {max}.",
        "theme.saved": TAG_OK + " Theme is now: {name} — saved to {path}",
        "theme.current": "current",
        "theme.preview_video": "Sample video — theme preview",
        "banner.tagline": "Download YouTube with the dub and quality you choose",
        # ── History & statuses ─────────────────────────────────────
        "history.empty": "No history yet — download your first video.",
        "history.title": SYM_SECTION + " Download history (last {count})",
        "history.col_id": "#",
        "history.col_title": "Title",
        "history.col_lang": "Language",
        "history.col_height": "Resolution",
        "history.col_status": "Status",
        "history.col_attempts": "Attempts",
        "status.pending": "Pending",
        "status.success": "Succeeded",
        "status.failed": "Failed",
        "status.resumed": "Resumed",
        "status.retried": "Retried",
        "status.skipped": "Already present",
        # ── Dub kinds & values ─────────────────────────────────────
        "kind.original": "Original",
        "kind.dubbed": "Dubbed",
        "kind.auto-dub": "Auto",
        "kind.descriptive": "Descriptive",
        "kind.unknown": "—",
        "value.all_dubs": "all dubs",
        "value.audio_only": "audio only",
        "value.best": "best",
        "value.unknown_lang": "Unknown",
        # ── Tables & display ───────────────────────────────────────
        "video.subtitle": "{uploader} " + SYM_DOT + " Duration {duration}",
        "video.views": "{count:,} views",
        "dubs.single": "Only one audio language (original: {lang}) — dub selection will be skipped.",
        "dubs.title": SYM_SECTION + " Available dubs ({count})",
        "dubs.col_num": "#",
        "dubs.col_lang": "Language",
        "dubs.col_code": "Code",
        "dubs.col_kind": "Type",
        "dubs.col_quality": "Quality",
        "quals.title": SYM_SECTION + " Available qualities ({count})",
        "quals.col_num": "#",
        "quals.col_res": "Resolution",
        "quals.col_fps": "FPS",
        "quals.col_codec": "Codec",
        "quals.col_size": "Size",
        "quals.col_note": "Note",
        "quals.audio_row": "Audio only",
        "quals.note_recommended": "Recommended",
        "quals.note_modern": "Needs a modern player",
        "estimate.line": "Estimated size: {size} ({container})",
        "confirm.overwrite": "File already exists: {path}\n" + SYM_PROMPT + " Re-download? [y/N]: ",
        # ── Prompts ────────────────────────────────────────────────
        "ask.choose": "Choose:",
        "ask.url_prompt": "Video URL: ",
        "ask.number_prompt": "{prompt} [{min}-{max}] (default {default}): ",
        "ask.dub_prompt": SYM_PROMPT + " Choose the dub",
        "ask.quality_prompt": SYM_PROMPT + " Choose quality (0 = audio only)",
        "ask.invalid_int": "Enter a valid integer.",
        "ask.out_of_range": "The number must be between {min} and {max}.",
        # ── Flow ───────────────────────────────────────────────────
        "scan.status": "Scanning dubs and qualities...",
        "scan.android_extra": "Found extra dubs via the android player.",
        "dub.selected": "Dub: {display} ({lang})",
        "dub.default": "Dub (default): {display}",
        "quality.selected": "Quality: {height}p",
        "progress.downloading": "Downloading [{lang}|{quality}]",
        "download.retry_warning": TAG_WARN + " Attempt {attempt} failed — retrying in {wait}s (resuming)...",
        "download.done": TAG_OK + " Done (attempts: {attempts}): ./{dir}/{file}   {tags}",
        "download.skipped": TAG_SKIP + " Already downloaded — skipped: {path}",
        "retry.starting": TAG_RETRY + " Retrying: {title} (id {id})",
        "batch.started": "Batch: {count} URLs from {file}",
        "batch.item_failed": TAG_ERR + " Failed: {err}",
        "batch.summary": "Summary: {ok} succeeded " + SYM_DOT + " {failed} failed of {total}",
        # ── Updates ────────────────────────────────────────────────
        "update.upgrading": "Updating {pkg}: {old} " + SYM_ARROW + " {new} ...",
        "update.ok": TAG_OK + " Updated {pkg}",
        "update.fail": TAG_ERR + " Failed to update {pkg}",
        "update.available": TAG_INFO + " Updates available: {names}",
    },
}


def set_lang(lang: str | None) -> str:
    """يضبط لغة الواجهة. أي قيمة غير إنجليزية ترجع للعربية."""
    global _LANG
    _LANG = LANG_EN if str(lang or "").strip().lower().startswith(_ALIASES_EN) else LANG_AR
    return _LANG


def get_lang() -> str:
    return _LANG


def t(key: str, **fmt) -> str:
    """يرجع رسالة بالمفتاح واللغة الحالية، مع سقوط آمن للعربية ثم للمفتاح."""
    table = _MESSAGES.get(_LANG, _MESSAGES[LANG_AR])
    text = table.get(key)
    if text is None:
        text = _MESSAGES[LANG_AR].get(key, key)
    return text.format(**fmt) if fmt else text
