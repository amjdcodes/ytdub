# 03 — `ffmpeg`: الدمج، اللغة، والحاوية الصحيحة

## 1. لماذا `ffmpeg` إلزامي؟ (وليس اختياريًا)

- يوتيوب يقدّم الجودات العالية **ملفين منفصلين**: فيديو بلا صوت + صوت بلا فيديو (DASH).
- `yt-dlp` يحمّلهما ثم ينادي `ffmpeg` تلقائيًا للدمج. **بدون `ffmpeg` ستحصل على ملفات منفصلة أو جودة ≤720p فقط.**
- التوثيق الرسمي (`FAQ`) ينص على ذلك حرفيًا.

> **تحذير شهير:** لا تثبّت حزمة `ffmpeg` من PyPI — تلك ليست `ffmpeg` الحقيقي. المطلوب **الثنائي** من `ffmpeg.org` أو عبر مدير الحزم (`apt/dnf/brew/choco`) أو builds الخاصة بـ `yt-dlp/FFmpeg-Builds`.

التحقق:

```bash
ffmpeg -version
ffprobe -version
```

## 2. المفاهيم الثلاثة التي يجب إتقانها

### أ) `stream copy` مقابل إعادة الترميز

| الوضع | الأمر | السرعة/الجودة |
|---|---|---|
| نسخ بدون ترميز (الأصل) | `-c copy` | سريع جدًا، صفر فقدان — **الافتراضي للدمج** |
| إعادة ترميز | `-c:v libx264 -c:a aac` | بطيء، فقدان محتمل — فقط عند قصّ دقيق أو تغيير كودك غير متوافق |

الأداة يجب أن تستخدم **نسخًا دائمًا** إلا لسبب صريح (مثل Opus في `mp4` قديم → الأفضل التحويل إلى `mkv` أو `aac`).

### ب) `-map`: من يدخل في الملف النهائي؟

بدون `-map` يختار `ffmpeg` تلقائيًا (أعلى دقة + أكثر قنوات صوتية) — **وهذا قد يتجاهل الدبلجة المختارة!**

```bash
# دمج فيديو + صوت مختار فقط (الحالة الشائعة للأداة):
ffmpeg -i video.mp4 -i audio_es.m4a -map 0:v:0 -map 1:a:0 -c copy -metadata:s:a:0 language=spa output.mp4

# الاحتفاظ بكل الدبلجات (وضع متقدم):
ffmpeg -i video.mp4 -i audio_en.m4a -i audio_ar.m4a \
  -map 0:v:0 -map 1:a:0 -map 2:a:0 -c copy \
  -metadata:s:a:0 language=eng -metadata:s:a:1 language=ara output.mkv
```

`yt-dlp` يفعل هذا نيابة عنك عندما تمرر `-f` صحيحًا + `--merge-output-format` — **لا تنادِ `ffmpeg` يدويًا إلا لحالات خاصة** (إعادة تسمية لغات، استخراج مسار، إصلاح حاوية).

### ج) وسم اللغة `language=...`

```bash
# وسم المسار الصوتي الأول كإسباني (ISO 639-2: spa/es)
-metadata:s:a:0 language=spa
# إنجليزي eng/en، عربي ara/ar، فرنسي fra/fr، ألماني ger/de
```

بدون الوسم تظهر المسارات في المشغلات باسم "Track 1/2" — تجربة سيئة. `yt-dlp` يوسم تلقائيًا عند الدمج، لكن تحقق بـ:

```bash
ffprobe -v error -show_entries stream=index,codec_name,codec_type:stream_tags=language -of table "output.mkv"
```

## 3. `mp4` أم `mkv`؟ — قرار الحاوية

| الحالة | الحاوية | السبب |
|---|---|---|
| مسار صوتي **واحد** (دبلجة واحدة مختارة) | **`mp4`** | توافق شامل (جوال/تلفاز/ويب)، `h264+aac` مثالي |
| **عدة** مسارات صوتية | **`mkv`** | `mp4` محدود مع Opus/تعدد المسارات؛ `mkv` مرن ويحفظ كل اللغات والترجمات |
| المستخدم طلب `mp3` (صوت فقط) | `mp3/m4a/opus` | عبر `-x --audio-format mp3` |

بريسِت `yt-dlp` الجاهز يختصر القرار:

```bash
-t mp4   # = --merge-output-format mp4 --remux-video mp4 -S vcodec:h264,...,acodec:aac
-t mkv   # = --merge-output-format mkv --remux-video mkv
-t mp3   # استخراج صوت
```

**توصية الأداة:** افتراضي `mp4` للوضع العادي، وانتقل تلقائيًا إلى `mkv` إذا فعّل المستخدم "تضمين كل الدبلجات" أو كان الكودك `opus/vp9` غير متوافق.

## 4. أخطاء شائعة وحلولها (من FAQ الرسمي)

| العرض | السبب | الحل |
|---|---|---|
| `incorrect codec parameters / Could not write header` | Opus في `mp4` بنسخة `ffmpeg` قديمة | حدّث `ffmpeg` من `yt-dlp/FFmpeg-Builds`، أو أضف `--postprocessor-args "ffmpeg:-strict -2"`، أو اخرج `mkv` |
| ملفان منفصلان بدل ملف واحد | `ffmpeg` غير موجود في `PATH` | ثبّته وضعه بجانب `yt-dlp` أو في `PATH` |
| القصّ غير دقيق عند الأجزاء | القصّ بدون إعادة ترميز يقف عند keyframes | `--force-keyframes-at-cuts` (بطيء) — تجنبه إلا للضرورة |
| لا صوت/لا فيديو في مشغّل قديم | كودك `AV1/VP9` غير مدعوم | افرض `-S vcodec:h264,acodec:aac` |

## 5. ماذا تفعل الأداة عمليًا؟

1. لا تُضمّن `ffmpeg` — **افحص وجوده** عند بدء التشغيل (`shutil.which`) واعرض رابط التثبيت حسب OS.
2. مرّر `--merge-output-format` و`--remux-video` و`--postprocessor-args` عبر `yt-dlp` بدل استدعاء `ffmpeg` يدويًا.
3. بعد التحميل، تحقق اختياريًا بـ `ffprobe` أن الملف يحوي المسار الصحيح ولغته موسومة، واعرض النتيجة للمستخدم.
4. للترجمة (اختياري لاحقًا): `--sub-langs ar,en --embed-subs` — تُضمّن في `mkv` بسلاسة، وفي `mp4` بقيود `mov_text`.

---
**المصادر:** `ffmpeg.org/ffmpeg.html` (أقسام Stream selection و`-map` و`-metadata`) + `FAQ: incorrect codec parameters` و`Do I need any other programs?` في Wiki الرسمي.
