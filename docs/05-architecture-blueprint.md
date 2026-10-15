# 05 — المخطط المعماري المقترح للأداة (Blueprint جاهز للبرمجة)

## 1. هيكل المجلدات المقترح

```
youtube_dub_downloader/
├── pyproject.toml
├── README.md
├── src/
│   └── ytdub/
│       ├── __init__.py
│       ├── __main__.py        # نقطة الدخول: python -m ytdub
│       ├── cli.py             # أوامر click + الوضع التفاعلي
│       ├── youtube.py         # تغليف yt-dlp: fetch_info + build_format
│       ├── models.py          # dataclasses: DubTrack, Quality, VideoInfo
│       ├── ui.py              # جداول rich + أسئلة questionary + تقدم
│       ├── downloader.py      # التحميل + progress_hooks + فحص ffmpeg
│       └── utils.py           # تحقق URL + أحجام + لغات ISO
└── tests/
    ├── test_format_builder.py
    └── test_lang_grouping.py
docs/  (هذه الوثائق)
```

## 2. نماذج البيانات

```python
from dataclasses import dataclass

@dataclass
class DubTrack:
    index: int
    lang: str            # "ar" — من audioTrack.id
    display: str         # "العربية" — للعرض
    kind: str            # "original" | "dubbed" | "auto-dub" | "descriptive"
    is_default: bool
    abr: float | None
    sample_format_id: str

@dataclass
class Quality:
    index: int
    height: int          # 720/1080/2160
    fps: int | None
    vcodec: str          # "avc1"/"vp09"/"av01"
    size_approx: int | None
    sample_format_id: str
    note: str            # "موصى به" / "يحتاج مشغلًا حديثًا"
```

## 3. الدوال الأساسية (pseudo-code ملزم)

```python
# youtube.py
def fetch_info(url: str, player_client: str | None = None) -> VideoInfo:
    """extract_info(download=False) → VideoInfo(formats, title, duration)."""
    ...

def group_dubs(formats) -> list[DubTrack]:
    """فلترة audio-only ثم تجميع حسب language، ترتيب: أصلي > بشري > تلقائي > وصفي."""
    ...

def group_qualities(formats) -> list[Quality]:
    """فلترة video-only ثم إبقاء أفضل bitrate لكل height."""
    ...

def build_format(dub: DubTrack | None, quality: Quality | None, prefer_h264=True) -> tuple[str, str]:
    """
    Returns (format_string, merge_container).
    مثال: ("bv*[height<=1080]+ba[language=es]/b[language=es]", "mp4")
    - quality=None → "b"/"ba" (أفضل شامل)
    - تعدد مسارات مطلوب → ("bv*+ba/b", "mkv") + --audio-multistreams
    """
    ...

# downloader.py
def ensure_ffmpeg() -> None:
    """shutil.which("ffmpeg") وإلا رسالة تثبيت حسب OS ثم خروج بكود 2."""
    ...

def download(url, fmt: str, container: str, outtmpl: str, progress_cb) -> str:
    """YoutubeDL({"format": fmt, "merge_output_format": container, "progress_hooks": [...]})"""
    ...
```

## 4. أمثلة `format` الجاهزة (انسخ والصق)

```python
# حالة المستخدم اختار دبلجة es + جودة 1080:
"fmt": "bv*[height<=1080]+ba[language=es]/b[language=es]/bv*[height<=1080]+ba/b"

# فرض h264 للتوافق + aac:
"format_sort": ["vcodec:h264", "lang", "quality", "res", "fps", "acodec:aac"]

# صوت فقط باللغة المختارة:
"fmt": "ba[language=ar]/ba/b"

# كل الدبلجات في ملف واحد:
{"format": "bv*+ba/b", "audio_multistreams": True, "merge_output_format": "mkv"}

# مع ترجمة مضمنة (اختياري):
{"subtitleslangs": ["ar", "en"], "embedsubtitles": True}
```

CLI المكافئ للاختبار اليدوي قبل البرمجة:

```bash
# 1) استكشاف:
yt-dlp -F "URL"
# 2) تجربة اختيار:
yt-dlp -f "bv*[height<=1080]+ba[language=es]" --merge-output-format mp4 -o "%(title)s [es][1080p].%(ext)s" "URL"
# 3) فرض التوافق:
yt-dlp -S "vcodec:h264,lang,quality,res,fps" -f "bv*[height<=720]+ba[language=ar]" -t mp4 "URL"
```

## 5. قالب اسم الملف `outtmpl`

```
%(title)s [%(language)s][%(height)sp].%(ext)s
# مثال: "رحلة إلى اليابان [ar][1080p].mp4"
# نظّف: restricted_filenames=True على ويندوز، وحد الطول بـ %(title).150B
```

## 6. معالجة الأخطاء (خريطة)

| الخطأ | رسالة المستخدم | إجراء تلقائي |
|---|---|---|
| رابط غير صالح | "الرابط غير مدعوم — الصق رابط watch/youtu.be صحيحًا" | إعادة السؤال |
| لا فورمات / فيديو خاص | "الفيديو خاص أو محذوف أو يحتاج تسجيل دخول" | اقترح `--cookies-from-browser` |
| `ffmpeg not found` | رابط التثبيت حسب OS | خروج 2 |
| `HTTP 429 / Sign in to confirm` | "يوتيوب قيّد IP مؤقتًا — جرّب لاحقًا أو مرّر cookies" | إعادة بانتظار متزايد |
| PO Token / SABR فقط | "جرّب --player-client android أو حدّث yt-dlp إلى nightly" | تبديل العميل تلقائيًا مرة واحدة |

## 7. قرارات معمارية ملزمة

1. **طبقة `youtube.py` معزولة**: كل منطق `yt-dlp` فيها — يسهل استبدالها أو تحديثها دون لمس الواجهة.
2. **لا منطق عرض داخل التحميل**: `downloader.py` يستقبل `progress_cb` فقط — `ui.py` يرسم.
3. **اختبارات بلا شبكة**: احفظ `info_dict` حقيقيًا (مجهولًا) كـ JSON في `tests/fixtures/` واختبر `group_dubs/build_format` عليه.
4. **الإصدارات مثبتة**: `yt-dlp>=2024.8.6`, `rich>=13`, `click>=8`, `questionary>=2`, `Python>=3.10`.

---
التالي: القيود القانونية والتقنية (ملف 06) قبل كتابة أي سطر كود.
