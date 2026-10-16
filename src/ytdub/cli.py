"""نقطة الأوامر — التدفق: إعداد → تحديث → رابط → دبلجة → جودة → تحميل باستئناف."""

from __future__ import annotations

import os
import sys

import click
from rich.table import Table
from rich.traceback import install as rich_traceback

from . import __version__
from . import config as app_config
from . import store
from . import updater
from .downloader import download, ensure_ffmpeg
from .ui import ask_dub, ask_quality, console, make_progress, show_dubs_table, show_qualities_table, show_video_info
from .utils import is_youtube_url
from .youtube import build_format, fetch_info, group_dubs, group_qualities

HELP_NOTE = (
    "حمّل فيديوهات يوتيوب بالدبلجة والجودة التي تختارها.\n\n"
    "⚠️ تنبيه: المطوّر غير مسؤول عن أي استخدام سيئ للأداة."
)


@click.command(help=HELP_NOTE)
@click.argument("url", required=False)
@click.option("--url", "url_opt", default=None, help="رابط الفيديو (بديل للوسيط).")
@click.option("--lang", default=None, help="كود الدبلجة مباشرة (ar/en/es) لتجاوز السؤال.")
@click.option("--height", type=int, default=None, help="الدقة مباشرة (720/1080/2160) لتجاوز السؤال.")
@click.option("--yes", "-y", is_flag=True, help="تجاوز كل الأسئلة بالافتراضيات (أصلي + 1080p).")
@click.option("--output-dir", "-o", default=None, help="مجلد الحفظ (افتراضي config.json).")
@click.option("--player-client", default=None, help="عميل يوتيوب (android/mweb/ios/web_safari) عند غياب الدبلجات.")
@click.option("--keep-all-dubs", is_flag=True, help="الاحتفاظ بكل الدبلجات في ملف mkv واحد.")
@click.option("--prefer-av1", is_flag=True, help="تفضيل AV1/VP9 بدل h264 (جودة أعلى، توافق أقل).")
@click.option("--audio-only", is_flag=True, help="تحميل الصوت فقط.")
@click.option("--cookies", "cookies_file", default=None, help="ملف كوكيز Netscape (اختياري).")
@click.option("--cookies-from-browser", default=None, help="مثال: chrome / firefox (اختياري).")
@click.option("--history", is_flag=True, help="عرض سجل التنزيلات (ناجح/فاشل/مستأنف/معاد) ثم خروج.")
@click.option("--history-limit", type=int, default=20, show_default=True, help="عدد صفوف السجل.")
@click.option("--show-config", is_flag=True, help="عرض الإعدادات الحالية ومسارها ثم خروج.")
@click.option("--reset-config", is_flag=True, help="إعادة معالج الإعداد من جديد ثم خروج.")
@click.option("--verbose", is_flag=True, help="إظهار تفاصيل تقنية للأخطاء.")
@click.version_option(__version__, "--version", "-V")
def main(url, url_opt, lang, height, yes, output_dir, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, history, history_limit, show_config, reset_config, verbose):
    if verbose:
        rich_traceback(show_locals=False)
    try:
        if history:
            _show_history(history_limit)
            return
        if show_config:
            cfg, _ = app_config.load()
            console.print(f"[bold]الإعدادات:[/bold] {app_config.config_path()}")
            for k, v in cfg.items():
                console.print(f"  {k} = {v}")
            return
        if reset_config:
            app_config.first_run_wizard(console)
            return
        _run(url or url_opt, lang, height, yes, output_dir, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, verbose)
    except RuntimeError as e:
        console.print(f"[red]❌ {e}[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]أُلغيت العملية.[/yellow]")
        sys.exit(130)


def _show_history(limit: int) -> None:
    rows = store.recent(limit)
    if not rows:
        console.print("[yellow]لا يوجد سجل بعد — حمّل أول فيديو.[/yellow]")
        return
    t = Table(title=f"📜 سجل التنزيلات (آخر {len(rows)})")
    t.add_column("#", justify="center")
    t.add_column("العنوان")
    t.add_column("اللغة", justify="center")
    t.add_column("الدقة", justify="center")
    t.add_column("الحالة")
    t.add_column("محاولات", justify="center")
    for r in rows:
        t.add_row(
            str(r["id"]),
            (r["title"] or r["url"])[:45],
            r["lang"] or "—",
            str(r["height"]) + "p" if r["height"] else "—",
            store.STATUS_AR.get(r["status"], r["status"]),
            str(r["attempts"]),
        )
    console.print(t)


def _run(url, lang, height, yes, output_dir, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, verbose):
    # 0) الإعدادات + فحص التحديثات (المعالج يظهر فقط بأول تشغيل تفاعلي)
    cfg, cfg_path = app_config.ensure(console, non_interactive=bool(yes))
    updater.run_startup_check(console, cfg)

    output_dir = output_dir or cfg.get("output_dir") or "downloads"
    lang = lang or cfg.get("default_lang")
    height = height if height is not None else cfg.get("default_height")
    player_client = player_client or cfg.get("player_client")

    # 1) الرابط
    if not url:
        try:
            url = console.input("🔗 [bold]رابط الفيديو:[/bold] ").strip()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError("أُلغي الإدخال.")
    if not url or not is_youtube_url(url):
        raise RuntimeError("الرابط غير مدعوم — الصق رابط watch/youtu.be/music.youtube صحيحًا.")

    # 2) ffmpeg إلزامي
    ensure_ffmpeg(audio_only=audio_only or False)

    # 3) جلب البيانات
    with console.status("🔍 جارٍ فحص الدبلجات والجودات...", spinner="dots"):
        info = fetch_info(url, player_client=player_client, cookies_file=cookies_file, cookies_from_browser=cookies_from_browser, verbose=verbose)
        dubs = group_dubs(info.formats)
        quals = group_qualities(info.formats)
        if len(dubs) <= 1 and not player_client and (lang or not yes):
            try:
                alt = fetch_info(url, player_client="android", cookies_file=cookies_file, cookies_from_browser=cookies_from_browser, verbose=False)
                alt_dubs = group_dubs(alt.formats)
                if len(alt_dubs) > len(dubs):
                    info, dubs = alt, alt_dubs
                    quals = group_qualities(alt.formats)
                    console.print("[yellow]تم العثور على دبلجات إضافية عبر android player.[/yellow]")
            except Exception:
                pass

    if not quals and not audio_only:
        raise RuntimeError("لا توجد جودات فيديو متاحة لهذا الرابط (خاص/محذوف/DRM؟).")

    show_video_info(info)
    show_dubs_table(dubs)
    if quals:
        show_qualities_table(quals)

    # 4) اختيار الدبلجة
    if keep_all_dubs:
        dub = None
    elif lang:
        dub = next((d for d in dubs if d.lang.lower() == lang.lower()), None)
        if dub is None:
            avail = ", ".join(d.lang for d in dubs)
            raise RuntimeError(f"الدبلجة '{lang}' غير متوفرة. المتاح: {avail}")
        console.print(f"🎧 الدبلجة: [bold]{dub.display} ({dub.lang})[/bold]")
    elif yes:
        dub = next((d for d in dubs if d.is_default), dubs[0])
        console.print(f"🎧 الدبلجة (افتراضي): [bold]{dub.display}[/bold]")
    else:
        dub = ask_dub(dubs)

    # 5) اختيار الجودة
    want_audio_only = bool(audio_only)
    quality = None
    if keep_all_dubs:
        quality = None
    elif height is not None:
        quality = next((q for q in quals if q.height == height), None)
        if quality is None and not (height == 0 or want_audio_only):
            avail = ", ".join(str(q.height) for q in quals)
            raise RuntimeError(f"الدقة {height}p غير متوفرة. المتاح: {avail}")
        if quality:
            console.print(f"🎞️ الجودة: [bold]{quality.height}p[/bold]")
    elif yes:
        quality = next((q for q in quals if q.height == 1080), quals[0] if quals else None)
    else:
        if quals:
            quality, want_audio_only = ask_quality(quals)
        else:
            want_audio_only = True

    # 6) بناء الفورمات + سجل DB
    fmt, container, extra = build_format(dub, quality, keep_all_dubs=keep_all_dubs, prefer_h264=not prefer_av1, audio_only=want_audio_only)
    os.makedirs(output_dir, exist_ok=True)
    outtmpl = os.path.join(output_dir, "%(title).150B [%(id)s].%(ext)s")

    if verbose:
        console.print(f"[dim]format={fmt} container={container} sort={extra.get('format_sort')}[/dim]")

    row_id = store.record_start(
        url, video_id=info.video_id, title=info.title,
        lang=(dub.lang if dub else "all"), height=(quality.height if quality else None), container=container,
    )

    resume_on = bool(cfg.get("resume_on_failure", True))
    max_retries = int(cfg.get("max_retries", 5)) if resume_on else 0
    retry_wait = int(cfg.get("retry_wait_seconds", 5))
    net = {
        "continuedl": True,
        "retries": 10,
        "fragment_retries": 10,
        "retry_wait": retry_wait,
        "socket_timeout": int(cfg.get("socket_timeout", 30)),
        "concurrent_fragments": int(cfg.get("concurrent_fragments", 4)),
    }

    desc = f"⬇️ جارٍ التحميل [{dub.lang if dub else 'all'}|{(str(quality.height) + 'p') if quality else ('audio' if want_audio_only else 'best')}]"
    progress = make_progress()
    task = None

    def hook(d: dict):
        nonlocal task
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            if task is None:
                task = progress.add_task(desc, total=total or 100)
            progress.update(task, total=total or 100, completed=done)
        elif d.get("status") == "finished":
            if task is not None:
                progress.update(task, completed=progress.tasks[task].total)

    def on_attempt(attempt_no: int, ok: bool, error: str):
        if ok:
            return
        store.record_attempt(row_id, store.STATUS_RETRIED, error=error)
        console.print(f"[yellow]⚠️ فشلت المحاولة {attempt_no} — إعادة بعد {retry_wait}s (استكمال من حيث توقف)...[/yellow]")

    try:
        with progress:
            final, attempts, resumed = download(
                url, fmt, container, outtmpl, sort=extra.get("format_sort"),
                audio_multistreams=extra.get("audio_multistreams", False),
                cookies_file=cookies_file, cookies_from_browser=cookies_from_browser,
                verbose=verbose, progress_hook=hook, net=net,
                max_retries=max_retries, retry_wait=retry_wait, on_attempt=on_attempt,
            )
    except RuntimeError as e:
        store.record_attempt(row_id, store.STATUS_FAILED, error=str(e)[:300])
        raise

    final_status = store.STATUS_RESUMED if (resumed or attempts > 1) else store.STATUS_SUCCESS
    store.record_attempt(row_id, final_status, filepath=final)
    fname = os.path.basename(final) if final else "—"
    qtxt = f"{quality.height}p" if quality else ("صوت فقط" if want_audio_only else "الأفضل")
    ltxt = dub.display if dub else "كل الدبلجات"
    console.print(f"✅ [green]تم (محاولات: {attempts}):[/green] ./{output_dir}/{fname}   [{ltxt}][{qtxt}][{container}]")


if __name__ == "__main__":
    main()
