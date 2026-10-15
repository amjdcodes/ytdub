# 08 — المصادر الموثقة (كل معلومة أعلاه لها أصل)

> منهجية البحث: تعذّر الوصول إلى محرك بحث SearXNG أثناء الجلسة، فاعتُمد **التوثيق الرسمي المباشر** (أعلى موثوقية) عبر Context7 + الجلب المباشر للصفحات الرسمية. لا توجد معلومة جوهرية من مدونات أو فيديوهات — كلها من المصدر الأول.

## المصادر الأولية (رُجعت فعلًا أثناء البحث)

### 1. `yt-dlp` — المستودع والتوثيق الرسمي

- **README الرئيسي** — `https://github.com/yt-dlp/yt-dlp`
  - أقسام: `INSTALLATION`, `DEPENDENCIES` (Python ≥3.10 + ffmpeg + deno/node + yt-dlp-ejs)، `FORMAT SELECTION` (صيغة `bv*+ba/b` وقاعدة تجاهل التكرار بدون `--audio-multistreams`)، `Preset Aliases` (`-t mp4/mkv/mp3`)، `EMBEDDING YT-DLP` (التضمين عبر `YoutubeDL` + أداة `devscripts/cli_to_api.py`)، `Sorting Formats` (`-S`).
  - استُخدمت منه: كل أوامر `-f` و`-S` و`-t` والتحذير من حزمة `ffmpeg` على PyPI.
- **الكود المصدري للمستخرج** — `yt_dlp/extractor/youtube/_video.py`
  - دالة `get_language_code_and_preference(fmt_stream)` — استخراج `language` من `audioTrack.id` ومعالجة `descriptive/original/audioIsDefault`.
  - استُخدمت منه: جدول `audioTrack` في ملف 01.
- **Wiki الرسمي**
  - `FAQ` — `https://github.com/yt-dlp/yt-dlp/wiki/FAQ`: "Do I need any other programs؟" (الجودات العالية منفصلة وتحتاج ffmpeg)، "incorrect codec parameters" (Opus في mp4 → حدّث ffmpeg أو `-strict -2`)، الكوكيز، Cloudflare 403.
  - `PO Token Guide` + `Extractors` (عبر Context7): مصفوفة `player_client` (web/web_safari/mweb/android/ios/tv) ومتطلبات PO Token لكل عميل، ووسائط `player_skip`, `visitor_data`, `po_token`.
  - استُخدمت منه: ملف 06 بالكامل وخيار `--player-client` في 02/05.

### 2. `FFmpeg` — التوثيق الرسمي

- **الدليل الرئيسي** — `https://ffmpeg.org/ffmpeg.html`
  - أقسام: `Stream selection` (الاختيار التلقائي مقابل `-map`)، `Stream specifiers` (`a:0`, `m:language:`)، `-metadata:s:a:0 language=eng`، `Streamcopy` (`-c copy`) مقابل Transcoding.
  - **أمثلة معتمدة**: `-map 0:m:language:eng`، `-metadata:s:a:0 language=eng`، `-i INPUT -map 0:1 -c copy OUTPUT.mp4`.
  - استُخدمت منه: كل أوامر الدمج والوسم في ملف 03.
- **Builds الموصى بها** — `https://github.com/yt-dlp/FFmpeg-Builds` (مذكورة في README كبديل مكافئ للمنبع حاليًا).

### 3. `Rich` — مكتبة الواجهة

- **المستودع** — `https://github.com/Textualize/rich` (57k+ نجمة): الجداول (`Table`)، التقدم (`Progress/track`)، الحالة (`Console.status`)، الأعمدة والماركداون.
- **التوثيق** (عبر Context7 — `/textualize/rich`): `Progress.get_renderables/make_tasks_table`، `Console.input` للأسئلة، تخصيص أعمدة السرعة والحجم والوقت المتبقي.
- **مكملات**: `click` (`/websites/click_palletsprojects_en_stable`) و`rich-click` (`/ewels/rich-click`) للأوامر بمظهر Rich.
- استُخدمت منه: ملف 04 بالكامل.

## ما لم يُعتمد عليه (بقرار واعٍ)

- شروحات يوتيوب/مدونات الطرف الثالث حول "تحميل الدبلجة" — أغلبها يستخدم `pytube` أو طرقًا مكسورة ولا يغطي `audioTrack`.
- حزمة PyPI المسماة `ffmpeg` — حذّر منها `yt-dlp` صراحةً (ليست الثنائي).
- `youtube-dl` الأصلي — متوقف ولا يدعم العملاء الجدد.

## كيف تتحقق بنفسك (إعادة إنتاج البحث في 10 دقائق)

```bash
# 1) تأكيد آلية audioTrack:
# افتح yt_dlp/extractor/youtube/_video.py وابحث عن audioTrack
# 2) تأكيد صيغ الاختيار:
grep -A5 "audio-multistreams" README.md  # في مستنسخ yt-dlp
# 3) تأكيد دور ffmpeg:
yt-dlp --verbose "URL"  # لاحظ سطر merging + تحذير ffmpeg عند غيابه
# 4) تأكيد وسم اللغة:
ffmpeg -h muxer=matroska | grep -i language
```

## سجل الجلسة

- التاريخ: 2026-10-15 — اللغة: العربية.
- الأدوات: Context7 (للتوثيق الرسمي) + WebFetch مباشر (GitHub/ffmpeg.org). محرك SearXNG كان غير متاح (`ConnectError`) فوُثّق ذلك بدل إخفائه.
- المخرجات: 8 ملفات في `docs/` — من `README.md` إلى هذا الملف.

---
انتهى البحث. أي معلومة في الملفات 01–07 غير مذكورة هنا تُعد رأيًا هندسيًا مبنيًا على المصادر أعلاه، لا حقيقة منقولة.
