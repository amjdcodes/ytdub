# 07 — المتطلبات النهائية وخارطة الطريق (من البحث إلى الكود)

## 1. قائمة المكتبات النهائية (المثبتة بالدليل)

### إلزامي

```toml
# pyproject.toml (مقترح)
[project]
name = "ytdub"
requires-python = ">=3.10"
dependencies = [
  "yt-dlp[default]>=2024.8.6",
  "rich>=13.7.0",
  "click>=8.1.0",
  "questionary>=2.0.0",
]
```

| المكوّن | التثبيت | التحقق |
|---|---|---|
| Python 3.10+ | `python3 --version` | `yt-dlp` لا يدعم أقل رسميًا |
| `yt-dlp` | `pip install -U "yt-dlp[default]"` | `yt-dlp --version` |
| `ffmpeg` + `ffprobe` (ثنائي!) | Ubuntu: `sudo apt install ffmpeg` / macOS: `brew install ffmpeg` / Windows: `choco install ffmpeg` أو builds `yt-dlp/FFmpeg-Builds` | `ffmpeg -version` |
| JS runtime | `deno` (موصى) أو `node` | `deno --version` |
| `yt-dlp-ejs` | يأتي مع `[default]` غالبًا | يظهر أعلى `--verbose` بلا تحذير |

### اختياري (مرحلة ثانية)

- `rich-click` بدل `click` لمظهر أجمل تلقائيًا.
- `youtube-transcript-api` لعرض/تحميل الترجمة كنص (ليست دبلجة).
- `pyinstaller` لبناء `exe` standalone للتوزيع.

### مستبعد بقرار موثق

- `pytube`, `youtube-dl` الأصلي — لا دعم موثوق للدبلجات المتعددة.
- حزمة PyPI المسماة `ffmpeg` — ليست الثنائي الحقيقي.
- `argparse` وحده للعرض — يُقبل للمنطق، لكن العرض يجب أن يكون `rich`.

## 2. خارطة الطريق — 4 مراحل

### المرحلة 0: تحقق يدوي (30 دقيقة، بدون كود)

```bash
yt-dlp -F "رابط_تجريبي_فيه_دبلجة"
yt-dlp -f "bv*[height<=720]+ba[language=en]" --merge-output-format mp4 -o "%(title)s.%(ext)s" "URL"
ffprobe -show_entries stream=index,codec_type,codec_name:stream_tags=language "الملف.mp4"
```

نجاح المرحلة = ملف يعمل وفيه اللغة الصحيحة.

### المرحلة 1: MVP تفاعلي (الأساس)

- [ ] `cli.py`: سؤال الرابط + تحقق.
- [ ] `youtube.py`: `fetch_info` + `group_dubs` + `group_qualities` + `build_format`.
- [ ] `ui.py`: جدولان `rich` + اختيار برقم (حتى قبل `questionary`).
- [ ] `downloader.py`: تحميل + `progress_hooks` + فحص `ffmpeg`.
- [ ] اختبار على 3 فيديوهات: (أ) بلا دبلجة، (ب) بدبلجة بشرية، (ج) بدبلجة تلقائية.

### المرحلة 2: احترافية UX

- [ ] `questionary` بالأسهم + افتراضيات Enter.
- [ ] وضع `--url/--lang/--height/--yes` غير التفاعلي.
- [ ] `--keep-all-dubs` (mkv متعدد المسارات) + `--prefer-av1` + `--player-client`.
- [ ] رسائل خطأ عربية لكل حالة في ملف 05/06 + `--verbose`.

### المرحلة 3: توزيع

- [ ] `pyproject.toml` + `README` استخدام + تنبيه قانوني.
- [ ] اختبارات `pytest` على fixtures محفوظة (بلا شبكة).
- [ ] `pyinstaller --onefile` لويندوز/لينكس + فحص `ffmpeg` بجانب الثنائي.

## 3. معايير القبول (متى نقول "الأداة جاهزة"؟)

| # | المعيار | كيف نتحقق؟ |
|---|---|---|
| 1 | رابط → جدولا دبلجة وجودة مرتبين | تجربة يدوية على فيديو مدبلج حقيقي |
| 2 | اختيار دبلجة غير افتراضية يعطي صوتًا مختلفًا فعلًا | `ffprobe language=` + استماع عينة |
| 3 | 1080p h264 يعمل على جوال قديم وتلفاز | تشغيل الملف على جهازين |
| 4 | غياب `ffmpeg` يعطي تعليمات تثبيت لا `traceback` | حذف `ffmpeg` من PATH والتجربة |
| 5 | فيديو بلا دبلجة يتجاوز خطوة الدبلجة بسلاسة | فيديو لغة واحدة |
| 6 | `--help` عربي/إنجليزي واضح + تنبيه مسؤولية | مراجعة نصية |

## 4. أول 5 أوامر للبدء الفعلي بعد اعتماد البحث

```bash
python3 -m pip install -U "yt-dlp[default]" rich click questionary pytest
ffmpeg -version || echo ">>> ثبّت ffmpeg أولًا"
yt-dlp -F "URL_تجريبي"
mkdir -p src/ytdub tests/fixtures
yt-dlp -J "URL_تجريبي" > tests/fixtures/sample_info.json
```

---
**الحالة بعد هذا الملف:** البحث مغلق. الخطوة التالية هي برمجة المرحلة 1 — لا حاجة لمزيد من البحث إلا عند ظهور خطأ غير موثق هنا.
