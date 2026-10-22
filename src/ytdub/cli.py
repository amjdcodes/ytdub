"""نقطة الأوامر — التدفق: إعداد → تحديث → رابط → دبلجة → جودة → تقدير → تخطي/تحميل.

يدعم رابطًا واحدًا، دفعات (`--batch`)، وإعادة من السجل (`--retry`/`--retry-last`).
"""

from __future__ import annotations

import os
import sys

import click
from rich.markup import escape
from rich.table import Table
from rich.traceback import install as rich_traceback

from . import __version__
from . import config as app_config
from . import preferences
from . import store
from . import updater
from .autopick import PICK_CAPPED, PICK_EXACT, PICK_UPGRADED, find_dub, pick_quality
from .downloader import download, ensure_ffmpeg
from .i18n import TAG_ERR, TAG_WARN, set_lang, t
from .themes import THEME_NAMES, theme_label
from .ui import (
    ask_dub,
    ask_quality,
    ask_theme,
    confirm_overwrite,
    console,
    make_progress,
    set_theme,
    show_banner,
    show_dubs_table,
    show_estimate,
    show_qualities_table,
    show_theme_preview,
    show_video_info,
)
from .utils import existing_output, is_youtube_url, read_batch_file, retry_selection
from .youtube import build_format, estimate_size, fetch_info, group_dubs, group_qualities

HELP_NOTE = (
    "حمّل فيديوهات يوتيوب بالدبلجة والجودة التي تختارها.\n"
    "Download YouTube videos with the dub language and quality you choose.\n\n"
    + TAG_WARN + " تنبيه: المطوّر غير مسؤول عن أي استخدام سيئ للأداة.\n"
    + TAG_WARN + " Disclaimer: the developer is not responsible for any misuse of this tool."
)


@click.command(help=HELP_NOTE)
@click.argument("url", required=False)
@click.option("--url", "url_opt", default=None, help="رابط الفيديو (بديل للوسيط) / Video URL (alternative to the argument).")
@click.option("--lang", default=None, help="كود الدبلجة مباشرة (ar/en/es) لتجاوز السؤال / Dub code, skips the prompt.")
@click.option("--height", type=int, default=None, help="الدقة مباشرة (720/1080/2160) / Resolution, skips the prompt.")
@click.option("--yes", "-y", is_flag=True, help="تجاوز كل الأسئلة بالافتراضيات / Skip all prompts with defaults.")
@click.option("--output-dir", "-o", default=None, help="مجلد الحفظ (افتراضي config.json) / Save folder (default from config).")
@click.option("--player-client", default=None, help="عميل يوتيوب عند غياب الدبلجات / YouTube client fallback (android/mweb/ios/web_safari).")
@click.option("--keep-all-dubs", is_flag=True, help="الاحتفاظ بكل الدبلجات في ملف mkv واحد / Keep every dub in one mkv.")
@click.option("--prefer-av1", is_flag=True, help="تفضيل AV1/VP9 بدل h264 / Prefer AV1/VP9 over h264.")
@click.option("--audio-only", is_flag=True, help="تحميل الصوت فقط / Audio only.")
@click.option("--cookies", "cookies_file", default=None, help="ملف كوكيز Netscape (اختياري) / Netscape cookies file (optional).")
@click.option("--cookies-from-browser", default=None, help="مثال: chrome / firefox (اختياري) / e.g. chrome / firefox (optional).")
@click.option("--history", is_flag=True, help="عرض سجل التنزيلات ثم خروج / Show download history, then exit.")
@click.option("--history-limit", type=int, default=20, show_default=True, help="عدد صفوف السجل / History rows to show.")
@click.option("--retry", "retry_id", type=int, default=None, help="إعادة محاولة صف معيّن من السجل / Retry a specific history row by id.")
@click.option("--retry-last", is_flag=True, help="إعادة محاولة آخر صف فاشل / Retry the most recent failed row.")
@click.option("--batch", "batch_file", default=None, help="ملف روابط (سطر لكل رابط) / File of URLs, one per line.")
@click.option("--overwrite", is_flag=True, help="إعادة التنزيل حتى لو كان الملف موجودًا / Redownload even if the file exists.")
@click.option("--show-config", is_flag=True, help="عرض الإعدادات ومسارها ثم خروج / Show settings and path, then exit.")
@click.option("--ui-lang", type=click.Choice(["ar", "en"]), default=None, help="تغيير لغة الواجهة وحفظها ثم خروج / Set and save the interface language, then exit.")
@click.option("--theme", "theme_name", type=click.Choice(list(THEME_NAMES)), default=None, help="تعيين تصميم الواجهة وحفظه: classic/midnight/sand / Set and save the interface theme.")
@click.option("--theme-menu", is_flag=True, help="قائمة تفاعلية لمعاينة واختيار التصميم / Interactive theme picker with live preview.")
@click.option("--smart/--no-smart", "smart_flag", default=None, help="تفعيل/تعطيل الاختيار الذكي من تفضيلاتك / Enable or disable smart picks from learned preferences.")
@click.option("--reset-config", is_flag=True, help="إعادة معالج الإعداد من جديد / Re-run the setup wizard.")
@click.option("--verbose", is_flag=True, help="إظهار تفاصيل تقنية للأخطاء / Technical error details.")
@click.version_option(__version__, "--version", "-V")
def main(url, url_opt, lang, height, yes, output_dir, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, history, history_limit, retry_id, retry_last, batch_file, overwrite, show_config, ui_lang, theme_name, theme_menu, smart_flag, reset_config, verbose):
    if verbose:
        rich_traceback(show_locals=False)
    try:
        keeps_going = any((url, url_opt, batch_file, retry_id is not None, retry_last, history, show_config, ui_lang, theme_menu, reset_config))
        if theme_name:
            cfg, _ = app_config.ensure(console, non_interactive=True)
            chosen = set_theme(theme_name)
            _save_theme_choice(cfg, chosen)
            if not keeps_going and smart_flag is None:
                show_theme_preview()
                return
        if smart_flag is not None:
            cfg, _ = app_config.ensure(console, non_interactive=True)
            set_theme(cfg.get("ui_theme"))
            cfg["smart_picks"] = bool(smart_flag)
            path = app_config.save(cfg)
            console.print(t("smart.enabled" if smart_flag else "smart.disabled", path=escape(path)))
            if smart_flag:
                _seed_smart_preferences()
                pref_lang = preferences.preferred_lang()
                pref_height = preferences.preferred_height()
                if pref_lang or pref_height is not None:
                    console.print(
                        t(
                            "smart.current",
                            lang=pref_lang or "—",
                            height=f"{pref_height}p" if pref_height else "—",
                        )
                    )
                else:
                    console.print(t("smart.no_preference"))
            if not keeps_going:
                return
        if theme_menu:
            cfg, _ = app_config.ensure(console, non_interactive=True)
            set_theme(cfg.get("ui_theme"))
            chosen = ask_theme()
            if chosen:
                _save_theme_choice(cfg, chosen)
                show_theme_preview()
            return
        if history:
            cfg, _ = app_config.ensure(console, non_interactive=True)
            set_theme(cfg.get("ui_theme"))
            _show_history(history_limit)
            return
        if show_config:
            cfg, _ = app_config.ensure(console, non_interactive=True)
            set_theme(cfg.get("ui_theme"))
            console.print(f"[bold]{t('config.header', path=escape(app_config.config_path()))}[/bold]")
            for k, v in cfg.items():
                console.print(f"  [text]{k}[/text] = [accent]{v}[/accent]")
            return
        if ui_lang:
            cfg, _ = app_config.load()
            cfg["ui_lang"] = ui_lang
            path = app_config.save(cfg)
            set_lang(ui_lang)
            set_theme(cfg.get("ui_theme"))
            console.print(t("config.ui_lang_set", path=escape(path)))
            return
        if reset_config:
            cfg = app_config.first_run_wizard(console)
            set_theme(cfg.get("ui_theme"))
            return
        if retry_id is not None or retry_last:
            _retry_from_history(retry_id, retry_last, output_dir, player_client, prefer_av1, cookies_file, cookies_from_browser, verbose, overwrite)
            return
        if batch_file:
            _run_batch(batch_file, lang, height, yes, output_dir, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, verbose, overwrite)
            return
        _run(url or url_opt, lang, height, yes, output_dir, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, verbose, overwrite)
    except RuntimeError as e:
        console.print(f"[error]{TAG_ERR} {e}[/error]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print(f"\n[warning]{t('error.operation_cancelled')}[/warning]")
        sys.exit(130)


def _save_theme_choice(cfg, chosen: str) -> str:
    cfg["ui_theme"] = chosen
    path = app_config.save(cfg)
    console.print(t("theme.saved", name=f"[bold]{theme_label(chosen)}[/bold]", path=escape(path)))
    return path


def _seed_smart_preferences() -> None:
    """يهيّئ التفضيلات من السجل القديم مرة واحدة فقط."""
    if not preferences.is_empty():
        return
    langs, heights, last_lang, last_height = store.selection_counts()
    preferences.seed(langs, heights, last_lang, last_height)


def _retry_from_history(retry_id, retry_last, output_dir, player_client, prefer_av1, cookies_file, cookies_from_browser, verbose, overwrite) -> None:
    row = store.last_failed() if retry_last else store.get(int(retry_id))
    if row is None:
        if retry_last:
            raise RuntimeError(t("error.retry_not_found_last"))
        raise RuntimeError(t("error.retry_not_found_row", id=retry_id))
    sel = retry_selection(row)
    title = escape((row.get("title") or row["url"])[:60])
    console.print(t("retry.starting", title=f"[bold]{title}[/bold]", id=row["id"]))
    _run(row["url"], sel["lang"], sel["height"], True, output_dir, player_client, sel["keep_all_dubs"], prefer_av1, sel["audio_only"], cookies_file, cookies_from_browser, verbose, overwrite)


def _run_batch(batch_file, lang, height, yes, output_dir, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, verbose, overwrite) -> None:
    urls = read_batch_file(batch_file)
    if not urls:
        raise RuntimeError(t("error.batch_empty"))
    cfg, output_dir = _setup(yes, output_dir)
    lang = lang or cfg.get("default_lang")
    height = height if height is not None else cfg.get("default_height")
    player_client = player_client or cfg.get("player_client")
    ensure_ffmpeg(audio_only=bool(audio_only))
    console.print(f"[heading]{t('batch.started', count=len(urls), file=batch_file)}[/heading]")

    ok = failed = 0
    for i, u in enumerate(urls, 1):
        console.rule(f"[{i}/{len(urls)}] {u}")
        try:
            _process_url(u, cfg, output_dir, lang, height, yes, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, verbose, overwrite)
            ok += 1
        except RuntimeError as e:
            failed += 1
            console.print(f"[error]{t('batch.item_failed', err=e)}[/error]")
    console.print(f"[bold]{t('batch.summary', ok=ok, failed=failed, total=len(urls))}[/bold]")
    if failed:
        sys.exit(1)


def _show_history(limit: int) -> None:
    rows = store.recent(limit)
    if not rows:
        console.print(f"[warning]{t('history.empty')}[/warning]")
        return
    t_obj = Table(title=t("history.title", count=len(rows)))
    t_obj.add_column(t("history.col_id"), justify="center")
    t_obj.add_column(t("history.col_title"))
    t_obj.add_column(t("history.col_lang"), justify="center")
    t_obj.add_column(t("history.col_height"), justify="center")
    t_obj.add_column(t("history.col_status"))
    t_obj.add_column(t("history.col_attempts"), justify="center")
    for r in rows:
        t_obj.add_row(
            str(r["id"]),
            escape((r["title"] or r["url"])[:45]),
            r["lang"] or "—",
            str(r["height"]) + "p" if r["height"] else "—",
            store.status_label(r["status"]),
            str(r["attempts"]),
        )
    console.print(t_obj)


def _setup(yes, output_dir):
    """إعداد مشترك: التصميم + الإعدادات + فحص التحديثات (بختم زمني) + مجلد الإخراج."""
    cfg, cfg_path = app_config.ensure(console, non_interactive=bool(yes))
    set_theme(cfg.get("ui_theme"))
    if not yes:
        show_banner()
    updater.run_startup_check(console, cfg, state_dir=os.path.dirname(cfg_path))
    output_dir = output_dir or cfg.get("output_dir") or "downloads"
    return cfg, output_dir


def _run(url, lang, height, yes, output_dir, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, verbose, overwrite=False):
    cfg, output_dir = _setup(yes, output_dir)
    lang = lang or cfg.get("default_lang")
    height = height if height is not None else cfg.get("default_height")
    player_client = player_client or cfg.get("player_client")

    # 1) الرابط
    if not url:
        try:
            url = console.input(t("ask.url_prompt")).strip()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError(t("error.input_cancelled"))

    # 2) ffmpeg إلزامي
    ensure_ffmpeg(audio_only=audio_only or False)

    _process_url(url, cfg, output_dir, lang, height, yes, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, verbose, overwrite)


def _process_url(url, cfg, output_dir, lang, height, yes, player_client, keep_all_dubs, prefer_av1, audio_only, cookies_file, cookies_from_browser, verbose, overwrite=False):
    """معالجة رابط واحد: جلب → جداول → اختيار → بناء الفورمات → تخطي/تحميل."""
    if not url or not is_youtube_url(url):
        raise RuntimeError(t("error.url_unsupported"))

    # 3) جلب البيانات
    with console.status(t("scan.status"), spinner="dots"):
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
                    console.print(f"[warning]{t('scan.android_extra')}[/warning]")
            except Exception:
                pass

    if not quals and not audio_only:
        raise RuntimeError(t("error.no_qualities"))

    show_video_info(info)
    show_dubs_table(dubs)
    if quals:
        show_qualities_table(quals)

    smart_enabled = bool(cfg.get("smart_picks")) and not keep_all_dubs
    favorite_lang = None
    favorite_height = None
    if smart_enabled:
        _seed_smart_preferences()
        favorite_lang = preferences.preferred_lang()
        favorite_height = preferences.preferred_height()
        if not favorite_lang and favorite_height is None:
            console.print(t("smart.no_preference"))

    # 4) اختيار الدبلجة
    dub = None
    dub_from_user = False
    if keep_all_dubs:
        dub = None
    elif lang:
        dub = next((d for d in dubs if d.lang.lower() == lang.lower()), None)
        if dub is None:
            avail = ", ".join(d.lang for d in dubs)
            raise RuntimeError(t("error.dub_unavailable", lang=lang, avail=avail))
        dub_from_user = True
        console.print(t("dub.selected", display=f"[bold]{escape(dub.display)}[/bold]", lang=dub.lang))
    elif smart_enabled and favorite_lang:
        dub = find_dub(dubs, favorite_lang)
        if dub is None:
            avail = ", ".join(d.lang for d in dubs) or "—"
            raise RuntimeError(t("smart.dub_missing", lang=favorite_lang, avail=avail))
        console.print(t("smart.dub_selected", display=f"[bold]{escape(dub.display)}[/bold]", lang=dub.lang))
    elif yes:
        dub = next((d for d in dubs if d.is_default), dubs[0])
        console.print(t("dub.default", display=f"[bold]{escape(dub.display)}[/bold]"))
    else:
        dub = ask_dub(dubs)
        dub_from_user = len(dubs) > 1

    # 5) اختيار الجودة (الصوت فقط يتجاوز الاختيار تمامًا)
    want_audio_only = bool(audio_only)
    quality = None
    quality_from_user = False
    if keep_all_dubs or want_audio_only:
        quality = None
    elif height is not None:
        quality = next((q for q in quals if q.height == height), None)
        if quality is None and height != 0:
            avail = ", ".join(str(q.height) for q in quals)
            raise RuntimeError(t("error.quality_unavailable", height=height, avail=avail))
        quality_from_user = quality is not None
        if quality:
            console.print(t("quality.selected", height=f"[bold]{quality.height}[/bold]"))
    elif smart_enabled and favorite_height is not None:
        quality, pick_kind = pick_quality(quals, favorite_height)
        if quality is not None and pick_kind == PICK_EXACT:
            console.print(t("smart.quality_selected", height=f"[bold]{quality.height}[/bold]"))
        elif quality is not None and pick_kind == PICK_UPGRADED:
            console.print(t("smart.quality_upgraded", requested=favorite_height, height=quality.height))
        elif quality is not None and pick_kind == PICK_CAPPED:
            console.print(t("smart.quality_capped", requested=favorite_height, height=quality.height))
    elif yes:
        quality = next((q for q in quals if q.height == 1080), quals[0] if quals else None)
    else:
        if quals:
            quality, want_audio_only = ask_quality(quals)
            quality_from_user = quality is not None
        else:
            want_audio_only = True

    record_lang = dub.lang if (dub_from_user and dub) else None
    record_height = quality.height if (quality_from_user and quality) else None
    if record_lang or record_height:
        preferences.record_choice(lang=record_lang, height=record_height)

    # 6) بناء الفورمات + تقدير الحجم
    fmt, container, extra = build_format(dub, quality, keep_all_dubs=keep_all_dubs, prefer_h264=not prefer_av1, audio_only=want_audio_only)
    os.makedirs(output_dir, exist_ok=True)
    outtmpl = os.path.join(output_dir, "%(title).150B [%(id)s].%(ext)s")

    if verbose:
        console.print(f"[muted]format={fmt} container={container} sort={extra.get('format_sort')}[/muted]")

    show_estimate(estimate_size(dub, quality, keep_all_dubs=keep_all_dubs, audio_only=want_audio_only), container)

    # 7) تخطي الموجود مسبقًا (إلا مع --overwrite)
    existing = existing_output(output_dir, info.video_id, container=container)
    if existing and not overwrite and cfg.get("skip_existing", True):
        redo = (not yes) and confirm_overwrite(existing)
        if not redo:
            store.record_skip(
                url, video_id=info.video_id, title=info.title,
                lang=(dub.lang if dub else "all"), height=(quality.height if quality else None),
                container=container, filepath=existing,
            )
            console.print(f"[warning]{t('download.skipped', path=escape(existing))}[/warning]")
            return

    # 8) سجل DB + التنزيل
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

    qlabel = f"{quality.height}p" if quality else ("audio" if want_audio_only else "best")
    desc = t("progress.downloading", lang=(dub.lang if dub else "all"), quality=qlabel)
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
        console.print(f"[warning]{t('download.retry_warning', attempt=attempt_no, wait=retry_wait)}[/warning]")

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
    qtxt = f"{quality.height}p" if quality else (t("value.audio_only") if want_audio_only else t("value.best"))
    ltxt = dub.display if dub else t("value.all_dubs")
    tags = escape(f"[{ltxt}][{qtxt}][{container}]")
    console.print(f"[success]{t('download.done', attempts=attempts, dir=escape(output_dir), file=escape(fname), tags=tags)}[/success]")


if __name__ == "__main__":
    main()
