# 02 — النواة: لماذا `yt-dlp` وكيف نستخدمه من بايثون؟

## 1. الحكم النهائي: `yt-dlp` بلا منازع

| المكتبة | الحالة 2025-2026 | الحكم للأداة |
|---|---|---|
| **`yt-dlp`** | نشط جدًا (~198k نجمة، تحديثات شبه يومية عبر قنوات `stable/nightly/master`)، يدعم `audioTrack` و`PO Token` و`SABR` | **النواة الوحيدة** |
| `youtube-dl` | متوقف/شبه ميت، لا يدعم العملاء الجدد | مرفوض |
| `pytube` / `pytubefix` | سهل للمبتدئين لكن يفشل مع الدبلجات المتعددة، لا دمج، صيانة هشة | مرفوض كأساس (يصلح لتجارب فقط) |
| `youtube-transcript-api` | للترجمة النصية فقط، ليس للصوت المدبلج | مكمل اختياري للترجمة، ليس بديلًا |

> القاعدة: أي حل لا يقرأ `audioTrack.language` ولا يدمج بـ `ffmpeg` **لا يحقق طلبك**.

## 2. طريقتان لاستخدام `yt-dlp` — ماذا نختار؟

| الطريقة | متى؟ | ملاحظة |
|---|---|---|
| **A. تضمين كمكتبة Python** (`import yt_dlp`) | **الاختيار الأساسي للأداة** — نحتاج سردًا تفاعليًا + تقدمًا مخصصًا بـ `Rich` | `YoutubeDL(params).extract_info(url, download=False)` ثم `download=[url]` |
| **B. استدعاء الثنائي عبر `subprocess`** (`yt-dlp -F`, `yt-dlp -f ...`) | احتياطي/تبسيط أول نسخة MVP | أسهل لكن أبطأ وتحكم أقل في الجداول والتقدم |

**التوصية:** ابنِ الأداة على **A** من اليوم الأول. ملف التحويل الرسمي `devscripts/cli_to_api.py` يترجم أي سطر أوامر CLI إلى بارامترات `YoutubeDL` — استخدمه كمرجع.

التثبيت القياسي (من التوثيق الرسمي):

```bash
python3 -m pip install -U "yt-dlp[default]"
# القناة الليلية موصى بها للمستخدمين الدائمين (إصلاحات يوتيوب السريعة):
python3 -m pip install -U --pre "yt-dlp[default]"
```

متطلبات التشغيل: **Python ≥3.10 (CPython)**، ويفضل `deno` أو `node` + حزمة `yt-dlp-ejs` لدعم يوتيوب الكامل.

## 3. استخراج الدبلجات والجودات (بدون تحميل)

```python
from yt_dlp import YoutubeDL

ydl_opts = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
}
with YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)  # info_dict

formats = info.get("formats", [])       # كل الجودات والمسارات
# كل عنصر يحمل: format_id, ext, resolution/height/fps,
# vcodec/acodec, abr/tbr, filesize/approx, language, format_note
```

**اشتقاق جدول الدبلجات:**

```python
audios = [f for f in formats if f.get("acodec") != "none" and f.get("vcodec") == "none"]
# جمّع حسب f.get("language") — اعرض: اللغة، format_note، abr، audioIsDefault
langs = sorted({ (a.get("language") or "und", a.get("format_note") or "") for a in audios })
```

**اشتقاق جدول الجودات (فيديو فقط):**

```python
videos = [f for f in formats if f.get("vcodec") != "none" and f.get("acodec") == "none"]
# اعرض: format_id, ext, height (720/1080/2160), fps, vcodec (avc1/vp9/av01), filesize
videos_sorted = sorted(videos, key=lambda v: (v.get("height") or 0, v.get("fps") or 0))
```

أو ببساطة من CLI للفحص اليدوي:

```bash
yt-dlp -F "URL"              # كل الفورمات
yt-dlp -F --list-audios "URL" 2>/dev/null || yt-dlp -F "URL" | grep -i audio
yt-dlp -J "URL" | python3 -m json.tool | less   # فحص info_dict خام
```

## 4. صيغ اختيار الفورمات التي ستحتاجها الأداة

القاعدة الذهبية من README الرسمي:

```bash
# الأفضل تلقائيًا (فيديو+صوت، ويدمج عند الحاجة):
yt-dlp "URL"
# صريحًا:
yt-dlp -f "bv*+ba/b" "URL"
```

**للدبلجة والجودة المختارة من المستخدم:**

```bash
# مثال: فيديو ≤1080p + صوت إسباني، والدمج إلى mp4
yt-dlp -f "bv*[height<=1080]+ba[language=es]/b[language=es]" --merge-output-format mp4 "URL"

# مثال: أفضل فيديو h264 حتى 720p + أفضل صوت عربي
yt-dlp -f "bv*[vcodec^=avc1][height<=720]+ba[language=ar]" --merge-output-format mp4 "URL"

# الاحتفاظ بكل الدبلجات في ملف واحد (متقدم - mkv):
yt-dlp -f "bv*+ba/b" --audio-multistreams --merge-output-format mkv "URL"
```

**فرز ذكي بدل كتابة شروط معقدة (`-S`):**

```bash
# فضّل h264 ثم اللغة ثم الجودة ثم fps — ثم الصوت aac
yt-dlp -S "vcodec:h264,lang,quality,res,fps,hdr:12,acodec:aac" "URL"
# بريسِت جاهز لضمان mp4:
yt-dlp -t mp4 "URL"
```

| الخيار | ماذا يفعل؟ | متى نستخدمه؟ |
|---|---|---|
| `-f` / `--format` | اختيار دقيق بالشروط (`[height<=1080]`, `[language=ar]`) | **دائمًا** بعد اختيار المستخدم |
| `-S` / `--format-sort` | ترتيب التفضيلات بدل الشروط الصارمة | لتفضيل `h264/aac` للتوافق |
| `--merge-output-format mp4/mkv` | الحاوية النهائية بعد الدمج | `mp4` لمسار واحد، `mkv` لتعدد المسارات |
| `--audio-multistreams` | الاحتفاظ بكل المسارات الصوتية | وضع "حمّل كل الدبلجات" الاختياري |
| `--list-subs` / `--sub-langs` | سرد/تحميل الترجمة (مكمل) | إذا أضفت خيار ترجمة لاحقًا |

مقابلها في Python (`YoutubeDL` params):

```python
ydl_opts = {
  "format": "bv*[height<=1080]+ba[language=es]/b[language=es]",
  "merge_output_format": "mp4",
  "format_sort": ["vcodec:h264", "lang", "quality", "res", "fps"],
}
```

## 5. عميل المشغّل `player_client` — متى تتدخل؟

يوتيوب يقدّم فورمات مختلفة حسب العميل. إن غابت الدبلجات أو فشل التحميل:

```bash
--extractor-args "youtube:player_client=android"
# بدائل: mweb, ios, web, tv, web_safari (الأخير يعطي HLS يتجاوز PO Token أحيانًا)
```

للأداة: اجعل `player_client` **قابلًا للضبط** (افتراضي `None` = تلقائي)، وجرّب `android,mweb` كخطة بديلة عند صفر دبلجات. راجع دليل PO Token الرسمي عند أخطاء `GVS/Player`.

## 6. ما الذي لا يفعله `yt-dlp` (ونحتاج `ffmpeg` له)؟

- دمج الفيديو المنفصل مع الصوت المختار → `ffmpeg` (ملف 03).
- عرض جداول عربية جميلة وتقدم حي → `Rich` (ملف 04).
- لا يعتمد عليه وحده للتحقق من وجود `ffmpeg` — الأداة يجب أن تفحص `shutil.which("ffmpeg")` وتوجه المستخدم للتثبيت.

---
**المصادر:** قسم `FORMAT SELECTION` و`Preset Aliases` و`EMBEDDING YT-DLP` في README الرسمي + `FAQ: Do I need any other programs?` (يؤكد أن جودات يوتيوب العالية ملفات منفصلة وتحتاج `ffmpeg`).
