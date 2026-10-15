# ytdub — تحميل فيديوهات يوتيوب مع الدبلجة 🎧

أداة CLI بلغة Python: تُدخل رابط يوتيوب → تعرض الدبلجات والجودات بشكل مرتب → تختار → تُحمّل بالدبلجة والجودة المختارة.

> استخدم الأداة بمسؤولية وللمحتوى المسموح فقط (ملكك / Creative Commons / مسموح بتنزيله).

## التثبيت

```bash
# 1) ffmpeg (إلزامي — الثنائي الحقيقي وليس حزمة PyPI)
# Ubuntu/Debian:
sudo apt install ffmpeg
# macOS:
brew install ffmpeg

# 2) الأداة نفسها
pip install -e .
# أو مباشرة:
pip install "yt-dlp[default]" rich click questionary
```

يفضل أيضًا `deno` لدعم يوتيوب الكامل (PO Token):
```bash
# https://deno.land — ثم:
deno --version
```

## الاستخدام

```bash
# تفاعلي (يطلب الرابط ثم يعرض الجداول):
ytdub
python -m ytdub

# مباشر:
ytdub "https://www.youtube.com/watch?v=XXXX"

# غير تفاعلي بالكامل:
ytdub --url "URL" --lang ar --height 1080 --yes

# صوت فقط / كل الدبلجات / عميل بديل:
ytdub --url "URL" --audio-only
ytdub --url "URL" --keep-all-dubs
ytdub --url "URL" --player-client android --verbose
```

## الخيارات

```
ytdub --help
```

| الخيار | الوظيفة |
|---|---|
| `--lang ar` | اختيار الدبلجة مباشرة |
| `--height 1080` | اختيار الدقة مباشرة |
| `--yes` | افتراضيات: أصلي + 1080p |
| `--keep-all-dubs` | كل الدبلجات في `mkv` واحد |
| `--prefer-av1` | تفضيل AV1/VP9 بدل h264 |
| `--audio-only` | صوت فقط |
| `--output-dir` | مجلد الحفظ (افتراضي `downloads`) |
| `--player-client` | عميل بديل عند غياب الدبلجات |
| `--cookies-from-browser chrome` | حل مشاكل التقييد (اختياري) |

## التطوير

```bash
pip install -e . pytest
pytest -q
```

## البنية

- `src/ytdub/youtube.py` — كل منطق `yt-dlp` (معزول)
- `src/ytdub/downloader.py` — التحميل + فحص `ffmpeg`
- `src/ytdub/ui.py` — جداول `rich` + أسئلة
- `src/ytdub/cli.py` — التدفق الرئيسي
- `docs/` — البحث الاحترافي الكامل (8 ملفات)
