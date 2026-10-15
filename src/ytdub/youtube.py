"""طبقة yt-dlp المعزولة — كل منطق الاستخراج وبناء الفورمات هنا فقط.

حسب docs/02 + docs/05: fetch_info / group_dubs / group_qualities / build_format
"""

from __future__ import annotations

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from .models import DubTrack, Quality, VideoInfo
from .utils import classify_dub_kind, lang_display


def _base_opts(verbose: bool = False) -> dict:
    return {"quiet": not verbose, "no_warnings": not verbose, "skip_download": True}


def fetch_info(
    url: str,
    player_client: str | None = None,
    cookies_file: str | None = None,
    cookies_from_browser: str | None = None,
    verbose: bool = False,
) -> VideoInfo:
    opts = _base_opts(verbose)
    if player_client:
        opts["extractor_args"] = {"youtube": {"player_client": [player_client]}}
    if cookies_file:
        opts["cookiefile"] = cookies_file
    if cookies_from_browser:
        # صيغة: chrome أو chrome:/path — نمرر الاسم فقط غالبًا
        opts["cookiesfrombrowser"] = (cookies_from_browser,)
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        raise _friendly_error(e) from e
    if info is None:
        raise RuntimeError("تعذّر استخراج بيانات الفيديو (معلومات فارغة).")
    if "entries" in info:  # قائمة تشغيل بالخطأ
        raise RuntimeError("الرابط يشير إلى قائمة تشغيل وليس فيديو واحدًا. حمّل فيديو واحدًا.")
    return VideoInfo(
        video_id=str(info.get("id") or ""),
        title=str(info.get("title") or "بدون عنوان"),
        uploader=str(info.get("uploader") or info.get("channel") or ""),
        duration=info.get("duration"),
        view_count=info.get("view_count"),
        formats=list(info.get("formats") or []),
        raw=info,
    )


def _friendly_error(e: Exception) -> RuntimeError:
    msg = str(e)
    low = msg.lower()
    if "private" in low or "login" in low or "age" in low:
        return RuntimeError("الفيديو خاص أو محذوف أو يحتاج تسجيل دخول/تحقق عمر.")
    if "429" in msg or "too many requests" in low or "confirm you're not a bot" in low:
        return RuntimeError(
            "يوتيوب قيّد الوصول مؤقتًا (429/bot-check). جرّب لاحقًا أو استخدم "
            "--cookies-from-browser أو --player-client android."
        )
    if "drm" in low:
        return RuntimeError("هذا المحتوى محمي بـ DRM ولا يمكن تحميله.")
    if "po token" in low or "sabr" in low:
        return RuntimeError(
            "يوتيوب طلب PO Token. حدّث yt-dlp إلى nightly وثبّت deno ثم جرّب --player-client android."
        )
    return RuntimeError(f"فشل استخراج البيانات: {msg[:300]}")


def _is_audio_only(f: dict) -> bool:
    return f.get("acodec") not in (None, "none") and (f.get("vcodec") in (None, "none"))


def _is_video_only(f: dict) -> bool:
    return f.get("vcodec") not in (None, "none") and (f.get("acodec") in (None, "none"))


def group_dubs(formats: list[dict]) -> list[DubTrack]:
    """يجمع المسارات الصوتية حسب language — الترتيب: أصلي > مدبلج > تلقائي > وصفي."""
    by_lang: dict[str, list[dict]] = {}
    for f in formats:
        if not _is_audio_only(f):
            continue
        lang = (f.get("language") or "und").split(".")[0].strip() or "und"
        by_lang.setdefault(lang, []).append(f)

    tracks: list[DubTrack] = []
    for lang, items in by_lang.items():
        notes = " ".join(str(x.get("format_note") or "") for x in items)
        raw_ids = " ".join(str(x.get("language") or "") for x in formats if x in items)
        kind = classify_dub_kind(notes, raw_ids)
        # أصلي إذا وجدت كلمة original في أي ملاحظة
        is_default = any("original" in str(x.get("format_note") or "").lower() for x in items)
        best = max(items, key=lambda x: float(x.get("abr") or x.get("tbr") or 0))
        abr = best.get("abr") or best.get("tbr")
        tracks.append(
            DubTrack(
                index=0,
                lang=lang,
                display=lang_display(lang),
                kind=kind if kind != "unknown" else ("original" if is_default else "dubbed"),
                is_default=is_default,
                abr=float(abr) if abr else None,
                sample_format_id=str(best.get("format_id") or ""),
            )
        )

    order = {"original": 0, "dubbed": 1, "auto-dub": 2, "unknown": 3, "descriptive": 4}
    tracks.sort(key=lambda t: (order.get(t.kind, 3), not t.is_default, t.lang))
    # إن كانت لغة واحدة فقط وغير موسومة original نعتبرها الأصلية
    if len(tracks) == 1 and not tracks[0].is_default:
        tracks[0].is_default = True
        if tracks[0].kind == "dubbed":
            tracks[0].kind = "original"
    for i, t in enumerate(tracks, 1):
        t.index = i
    return tracks


def group_qualities(formats: list[dict]) -> list[Quality]:
    """يبقي أفضل bitrate لكل height من الفيديو المنفصل."""
    best_by_h: dict[int, dict] = {}
    for f in formats:
        if not _is_video_only(f):
            continue
        h = f.get("height")
        if not isinstance(h, int) or h <= 0:
            continue
        score = float(f.get("tbr") or f.get("vbr") or 0)
        size = f.get("filesize") or f.get("filesize_approx") or 0
        cur = best_by_h.get(h)
        cur_score = float(cur.get("tbr") or cur.get("vbr") or 0) if cur else -1
        if cur is None or score > cur_score:
            best_by_h[h] = f
        elif score == cur_score and size > (cur.get("filesize") or cur.get("filesize_approx") or 0):
            best_by_h[h] = f

    quals: list[Quality] = []
    for h in sorted(best_by_h, reverse=True):
        f = best_by_h[h]
        vc = str(f.get("vcodec") or "").split(".")[0]
        note = ""
        if h == 1080 and vc.startswith("avc"):
            note = "موصى به ✅"
        elif h >= 2160 or vc.startswith(("av01", "vp09")):
            note = "يحتاج مشغلًا حديثًا"
        quals.append(
            Quality(
                index=0,
                height=h,
                fps=f.get("fps"),
                vcodec=vc,
                size_approx=f.get("filesize") or f.get("filesize_approx"),
                sample_format_id=str(f.get("format_id") or ""),
                note=note,
            )
        )
    for i, q in enumerate(quals, 1):
        q.index = i
    return quals


def build_format(
    dub: DubTrack | None,
    quality: Quality | None,
    keep_all_dubs: bool = False,
    prefer_h264: bool = True,
    audio_only: bool = False,
) -> tuple[str, str, dict]:
    """يبني (format_string, container, extra_opts) حسب docs/05.

    - audio_only → صوت فقط باللغة المختارة.
    - keep_all_dubs → كل المسارات في mkv.
    - quality=None → أفضل شامل.
    """
    extra: dict = {}
    if audio_only:
        lang = dub.lang if dub else None
        fmt = f"ba[language={lang}]/ba/b" if lang and lang != "und" else "ba/b"
        return fmt, "m4a", extra
    if keep_all_dubs:
        extra["audio_multistreams"] = True
        return "bv*+ba/b", "mkv", extra

    lang = dub.lang if dub else None
    lang_sel = f"[language={lang}]" if lang and lang != "und" else ""
    if quality is None:
        fmt = f"bv*+ba{lang_sel}/b{lang_sel}/bv*+ba/b" if lang_sel else "bv*+ba/b"
    else:
        h = quality.height
        if prefer_h264:
            fmt = (
                f"bv*[vcodec^=avc1][height<={h}]+ba{lang_sel}/"
                f"b{lang_sel}/bv*[height<={h}]+ba{lang_sel}/b{lang_sel}"
                if lang_sel
                else f"bv*[vcodec^=avc1][height<={h}]+ba/b[height<={h}]/bv*[height<={h}]+ba/b"
            )
        else:
            fmt = (
                f"bv*[height<={h}]+ba{lang_sel}/b{lang_sel}/bv*+ba/b"
                if lang_sel
                else f"bv*[height<={h}]+ba/b"
            )
    extra["format_sort"] = ["vcodec:h264", "lang", "quality", "res", "fps", "acodec:aac"] if prefer_h264 else []
    return fmt, "mp4", extra
